#!/usr/bin/env python3
# coding: utf-8

import os
import math
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, Point, Quaternion, Twist
from std_msgs.msg import String, Empty
from nav_msgs.msg import Odometry

from tf2_ros import Buffer, TransformListener, TransformException


def euler_from_quaternion(q):
    """
    クォータニオン [x, y, z, w] からオイラー角 (roll, pitch, yaw) を計算する関数
    """
    x, y, z, w = q
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    return 0.0, 0.0, yaw


class OdomBaseController(Node):
    def __init__(self):
        super().__init__('odom_base_controller')

        # TF2 の設定
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # 回転制御パラメータ
        self.turn_acs = 1.0            # 加速度
        self.turn_speed_max = 150.0    # 最高速度
        self.turn_speed_min = 0.0
        self.turn_ki = 0.15

        # 直進制御パラメータ
        self.stlight_acs = 0.01        # 加速度
        self.stlight_speed_max = 0.4    # 最高速度
        self.stlight_speed_min = 0.0   # 最低速度
        self.stlight_ki = 0.1          # 積分係数

        # ループ周期設定 (秒)
        self.sleep_vale = 0.030

        # 台形制御のグラフ描画用
        self.graph_x = []
        self.graph_y = []

        # 速度更新時間計測
        self.start_measurement_time = 0.0
        self.speed_update_time = 0.0
        self.period_time = 0.0
        self.speed_start_flag = False

        # 初期化
        self.speed = 0.0
        self.speed_max = 0.0
        self.speed_min = 0.0
        self.before_speed = 0.0
        self.current_speed = 0.0
        self.current_pose_x = 0.0
        self.current_pose_y = 0.0
        self.current_angle = 0.0
        self.before_pose_x = 0.0
        self.before_pose_y = 0.0
        self.before_angle = 0.0
        self.order_vale = 0.0
        self.moved_vale = 0.0
        self.error_P = 0.0
        self.error_I = 0.0
        self.move_order_T = False
        self.move_order_S = False
        self.stop_flag = False

        # パブリッシャーとサブスクライバーの設定
        self.pub_twist = self.create_publisher(Twist, '/mobile_base/commands/velocity', 10)
        self.pub_output_log = self.create_publisher(String, '/odom_base/output_log', 10)
        self.pub_reset_odometry = self.create_publisher(Empty, '/mobile_base/commands/reset_odometry', 10)
        self.pub_retrun_arrive = self.create_publisher(String, '/retrun_arrive', 10)

        self.sub_motion_stop = self.create_subscription(String, '/motion_stop', self.motion_stop, 10)
        self.sub_odom_base_ctrl = self.create_subscription(String, '/odom_base_ctrl', self.odom_base_ctrl, 10)

        # ROS 2 ではコールバック内で無限ループを回すと通信がブロックされるため、タイマー駆動に変更
        self.timer = self.create_timer(self.sleep_vale, self.control_loop)

        self.get_logger().info("odom_base_controller is OK.")

    def Check_Command(self, line):
        cmd_line = line.data[0:2]
        value_line = line.data[2:len(line.data)]
        for key in cmd_line:
            if key not in ['T', 'S', ':']:
                self.get_logger().info(f"check_command cmd error: {line.data}")
                return False
        for key in value_line:
            if not (('0' <= key <= '9') or key == '-' or key == '.'):
                self.get_logger().info(f"check_command cmd error: {line.data}")
                return False
        return True

    def Read_Value(self, line):
        value_str = line.data[2:len(line.data)]
        return float(value_str)

    def motion_stop(self, data):
        self.stop_flag = True

    def get_current_tf(self):
        """odom -> base_link の TF を取得するヘルパー関数"""
        try:
            # ROS 2 ではフレーム名の先頭スラッシュ ('/') は含めません
            trans = self.tf_buffer.lookup_transform('odom', 'base_link', rclpy.time.Time())
            x = trans.transform.translation.x * 100.0  # [cm]
            y = trans.transform.translation.y * 100.0  # [cm]
            rot = trans.transform.rotation
            _, _, yaw = euler_from_quaternion([rot.x, rot.y, rot.z, rot.w])
            angle = math.degrees(yaw)  # [deg]
            return x, y, angle
        except TransformException as ex:
            self.get_logger().warn(f"Could not transform odom to base_link: {ex}")
            return None, None, None

    def odom_base_ctrl(self, motion):
        if self.move_order_T or self.move_order_S:
            self.get_logger().info("Sorry, the action is not registered.")
            return

        check = self.Check_Command(motion)
        if not check:
            self.get_logger().info("The command cannot be carried out.")
            return

        if "T" in motion.data:
            self.order_vale = self.Read_Value(motion)
            self.move_order_T = True
            self.get_logger().info(f"order: Turn: {self.order_vale:f}(deg)")
        elif "S" in motion.data:
            self.order_vale = self.Read_Value(motion)  # cm
            self.move_order_S = True
            self.get_logger().info(f"order: Straight: {self.order_vale:f}(cm)")

        if self.move_order_T and not self.move_order_S:
            self.speed_acs = self.turn_acs
            self.speed_max = self.turn_speed_max
            self.speed_min = self.turn_speed_min
            self.ki = self.turn_ki
        elif not self.move_order_T and self.move_order_S:
            self.speed_acs = self.stlight_acs
            self.speed_max = self.stlight_speed_max
            self.speed_min = self.stlight_speed_min
            self.ki = self.stlight_ki

        # 開始地点の TF 値を取得
        x, y, angle = self.get_current_tf()
        if x is not None:
            self.before_pose_x = x
            self.before_pose_y = y
            self.before_angle = angle
            self.get_logger().info(
                f"--開始地点のエンコーダ値: x:{self.before_pose_x:f} y:{self.before_pose_y:f} angle:{self.before_angle:f}"
            )

    def reset_state(self):
        """ステートの初期化処理"""
        self.speed = 0.0
        self.current_speed = 0.0
        self.order_vale = 0.0
        self.moved_vale = 0.0
        self.error_P = 0.0
        self.error_I = 0.0
        self.move_order_T = False
        self.move_order_S = False
        self.speed_start_flag = False
        self.graph_x = []
        self.graph_y = []

    def control_loop(self):
        """タイマーで 0.03秒毎に定期実行される制御メインループ"""
        # 移動命令が出ていないときは何もしない
        if not self.move_order_T and not self.move_order_S:
            return

        send_cmd = Twist()

        # 動作中止判定
        if self.stop_flag:
            self.stop_flag = False
            self.reset_state()
            self.pub_twist.publish(Twist())  # 停止
            self.get_logger().info("stop flag True")
            return

        # 加減速計算 (台形制御)
        if self.moved_vale < abs(self.order_vale) / 5.0:
            # 加速区間
            self.speed += self.speed_acs
            self.current_speed = self.speed
        elif self.moved_vale > abs(self.order_vale) * 4.0 / 5.0:
            # 減速区間
            self.before_speed = self.speed
            if self.speed > self.error_I:
                self.error_P = (abs(self.order_vale) - self.moved_vale) / (abs(self.order_vale) / 5.0)
                self.speed = self.current_speed * self.error_P + self.error_I
                self.error_I += (self.before_speed - self.speed) * self.ki
            elif self.speed <= self.error_I:
                self.speed = self.error_I
        else:
            # 等速区間
            pass

        # 速度上限・下限補正
        if self.speed >= self.speed_max:
            self.speed = self.speed_max
        if self.speed < self.speed_min:
            self.speed = self.speed_min

        # --- 回転制御 ---
        if self.move_order_T and not self.move_order_S:
            if self.order_vale > 0:
                send_cmd.angular.z = math.radians(-self.speed)
            else:
                send_cmd.angular.z = math.radians(self.speed)

            if self.speed_start_flag:
                self.period_time = time.time() - self.speed_update_time

            if self.moved_vale < abs(self.order_vale):
                self.pub_twist.publish(send_cmd)
                self.speed_update_time = time.time()
                if not self.speed_start_flag:
                    self.start_measurement_time = time.time()
                    self.speed_start_flag = True

                # 現在値のTF更新
                x, y, angle = self.get_current_tf()
                if x is not None:
                    self.current_pose_x = x
                    self.current_pose_y = y
                    self.current_angle = angle

                    sub_point = abs(self.current_angle - self.before_angle)
                    if sub_point > 180:
                        sub_point = abs(sub_point - 360)
                    self.moved_vale += sub_point
                    self.get_logger().info(f"現在の回転角度:{self.moved_vale:f}[deg]")

                    self.before_pose_x = self.current_pose_x
                    self.before_pose_y = self.current_pose_y
                    self.before_angle = self.current_angle
            else:
                self.pub_twist.publish(Twist())  # 停止
                all_time = time.time() - self.start_measurement_time
                print(f"総回転時間 :{all_time}[sec]")

                saved_order_vale = self.order_vale
                self.reset_state()

                output_log = f"{saved_order_vale}_finished"
                msg_log = String()
                msg_log.data = output_log
                self.pub_output_log.publish(msg_log)

                end = String()
                end.data = "move end"
                self.pub_retrun_arrive.publish(end)

        # --- 直進制御 ---
        elif not self.move_order_T and self.move_order_S:
            if self.order_vale > 0:
                send_cmd.linear.x = float(self.speed)
            else:
                send_cmd.linear.x = -float(self.speed)

            if self.moved_vale < abs(self.order_vale):
                if self.speed_start_flag:
                    self.period_time = time.time() - self.speed_update_time

                self.pub_twist.publish(send_cmd)
                self.speed_update_time = time.time()
                if not self.speed_start_flag:
                    self.start_measurement_time = time.time()
                    self.speed_start_flag = True

                # 現在値のTF更新
                x, y, angle = self.get_current_tf()
                if x is not None:
                    self.current_pose_x = x
                    self.current_pose_y = y
                    self.current_angle = angle

                    sub_x = self.before_pose_x - self.current_pose_x
                    sub_y = self.before_pose_y - self.current_pose_y
                    self.moved_vale = math.hypot(sub_x, sub_y)
                    self.get_logger().info(f"現在の移動距離: {self.moved_vale:f}[cm]")
            else:
                self.pub_twist.publish(Twist())  # 停止
                all_time = time.time() - self.start_measurement_time
                print(f"総移動時間:{all_time}[sec]")

                self.reset_state()

                end = String()
                end.data = "move end"
                self.pub_retrun_arrive.publish(end)


def main(args=None):
    rclpy.init(args=args)
    node = OdomBaseController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()