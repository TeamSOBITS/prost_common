#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import time
import numpy as np

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8, Empty, Bool
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan, Image
from cv_bridge import CvBridge, CvBridgeError
from rclpy.executors import MultiThreadedExecutor

# Kobuki メッセージの互換性インポート (kobuki_ros_interfaces または kobuki_msgs)
try:
    from kobuki_ros_interfaces.msg import BumperEvent, ButtonEvent, Led, Sound
except ImportError:
    try:
        from kobuki_msgs.msg import BumperEvent, ButtonEvent, Led, Sound
    except ImportError:
        pass


def euler_from_quaternion(x, y, z, w):
    """
    クォータニオン (x, y, z, w) からオイラー角 (roll, pitch, yaw) [rad] を計算するヘルパー関数
    """
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = math.atan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = math.asin(t2)

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = math.atan2(t3, t4)

    return roll_x, pitch_y, yaw_z


class Scratch3Connector(Node):

    def __init__(self):
        super().__init__('scratch3_connector')
        self.get_logger().info("Scratch3_Connector Started")

        self.save_qr_distance = 0
        self.save_qr_width = 0
        self.save_qr_angle = 0
        self.moving_speed = Twist()

        # Publishers
        self.pub_ros_scratch = self.create_publisher(String, '/ros_scratch', 10)
        self.pub_ros_scratch_debug = self.create_publisher(String, '/ros_scratch_debug', 10)
        self.pub_led1 = self.create_publisher(Led, '/mobile_base/commands/led1', 10)
        self.pub_led2 = self.create_publisher(Led, '/mobile_base/commands/led2', 10)
        self.pub_sound = self.create_publisher(Sound, '/mobile_base/commands/sound', 10)
        self.pub_twist = self.create_publisher(Twist, '/mobile_base/commands/velocity', 5)
        self.pub_reset_odometry = self.create_publisher(Empty, '/mobile_base/commands/reset_odometry', 10)
        self.pub_odom_base_ctrl = self.create_publisher(String, '/odom_base_ctrl', 10)
        self.pub_speech_word = self.create_publisher(String, '/speech_word', 10)

        # Subscribers
        self.sub_scratch_ros = self.create_subscription(String, '/scratch_ros', self.cb_scratch_ros, 10)
        self.sub_bumper = self.create_subscription(BumperEvent, '/mobile_base/events/bumper', self.bumper_state, 10)
        self.sub_button = self.create_subscription(ButtonEvent, '/mobile_base/events/button', self.button_state, 10)
        self.sub_wifi_connect = self.create_subscription(Bool, '/wifi_connect', self.cb_wifi_connect, 10)
        self.sub_odom = self.create_subscription(Odometry, '/odom', self.cb_odom, 10)
        self.sub_speech_recognition = self.create_subscription(String, '/speech_recognition/word', self.speech_recognition, 10)
        self.sub_qr_position = self.create_subscription(PoseStamped, '/visp_auto_tracker/object_position', self.qr_position, 10)

        # 起動時の案内メッセージをタイマーで3秒後に送信
        self.initial_timer = self.create_timer(3.0, self.send_initial_speech)

    def send_initial_speech(self):
        msg = String()
        msg.data = "みどりいろのUSBを接続した後に、接続ブロックを実行してください"
        self.pub_speech_word.publish(msg)
        self.initial_timer.cancel()  # 一度送信したらタイマー停止

    def send_scratch_msg(self, text, debug=False):
        """Scratch 送信用メッセージヘルパー"""
        msg = String()
        msg.data = text
        self.pub_ros_scratch.publish(msg)
        if debug:
            self.pub_ros_scratch_debug.publish(msg)

    def cb_wifi_connect(self, state):
        msg = Led()
        if state.data:
            msg.value = 1  # green
        else:
            msg.value = 3  # red
        self.pub_led1.publish(msg)

    def cb_scratch_ros(self, msg):
        self.get_msg = msg.data
        print(self.get_msg)

        if self.get_msg.find('LED:') >= 0:
            word = self.get_msg[4:len(self.get_msg)]
            led_msg = Led()
            if word == "off":
                led_msg.value = 0
            elif word == "green":
                led_msg.value = 1
            elif word == "yellow":
                led_msg.value = 2
            elif word == "red":
                led_msg.value = 3
            self.pub_led2.publish(led_msg)

        elif self.get_msg.find('sound:') >= 0:
            word = self.get_msg[6:len(self.get_msg)]
            sound_msg = Sound()
            sound_msg.value = int(word)
            self.pub_sound.publish(sound_msg)

        elif self.get_msg.find('S:') >= 0 or self.get_msg.find('T:') >= 0:
            out_msg = String()
            out_msg.data = self.get_msg
            self.pub_odom_base_ctrl.publish(out_msg)

        elif self.get_msg.find('move_speed:') >= 0:
            word = self.get_msg[11:self.get_msg.find(',')]
            val = float(word)
            val = max(-50.0, min(50.0, val))

            self.moving_speed.linear.x = val * 0.01
            self.moving_speed.angular.z = 0.0

            if self.get_msg.find('second:') >= 0:
                second = float(self.get_msg[self.get_msg.index(',') + 8:len(self.get_msg)])
            else:
                second = 1.0

            begin = time.time()
            while rclpy.ok():
                check = time.time() - begin
                if check >= second:
                    self.moving_speed.linear.x = 0.0
                    self.pub_twist.publish(self.moving_speed)
                    print(check)
                    break
                self.pub_twist.publish(self.moving_speed)
                time.sleep(0.01)

        elif self.get_msg.find('rotation_speed:') >= 0:
            word = self.get_msg[15:self.get_msg.find(',')]
            val = float(word)
            val = max(-120.0, min(120.0, val))

            self.moving_speed.linear.x = 0.0
            self.moving_speed.angular.z = math.radians(val)

            if self.get_msg.find('second:') >= 0:
                second = float(self.get_msg[self.get_msg.index(',') + 8:len(self.get_msg)])
            else:
                second = 1.0

            begin = time.time()
            while rclpy.ok():
                check = time.time() - begin
                if check >= second:
                    self.moving_speed.angular.z = 0.0
                    self.pub_twist.publish(self.moving_speed)
                    print(check)
                    break
                self.pub_twist.publish(self.moving_speed)
                time.sleep(0.01)

        elif self.get_msg.find('turtlebot_cmd_vel:') >= 0:
            word = self.get_msg[18:len(self.get_msg)]
            num = word.find(',')
            vel = word[0:num]
            rad = word[num + 1:len(word)]
            self.moving_speed.linear.x = float(vel) * 0.01
            self.moving_speed.angular.z = math.radians(float(rad))
            self.pub_twist.publish(self.moving_speed)

        elif self.get_msg.find('motion_stop:') >= 0:
            self.moving_speed.linear.x = 0.0
            self.moving_speed.angular.z = 0.0
            self.pub_twist.publish(self.moving_speed)

        elif self.get_msg.find('odome_initialize') >= 0:
            reset_val = Empty()
            self.pub_reset_odometry.publish(reset_val)

        elif self.get_msg.find('speech') >= 0:
            word = self.get_msg[7:len(self.get_msg)]
            out_msg = String()
            out_msg.data = word
            self.pub_speech_word.publish(out_msg)

    def cb_odom(self, data):
        robo_pose_x = data.pose.pose.position.x
        robo_pose_y = data.pose.pose.position.y
        
        _, _, robo_rad = euler_from_quaternion(
            data.pose.pose.orientation.x,
            data.pose.pose.orientation.y,
            data.pose.pose.orientation.z,
            data.pose.pose.orientation.w
        )
        robo_deg = math.degrees(robo_rad)

        self.send_scratch_msg("robot_pose_x:" + str(robo_pose_x))
        self.send_scratch_msg("robot_pose_y:" + str(robo_pose_y))
        self.send_scratch_msg("robot_angle:" + str(robo_deg))

    def qr_position(self, data):
        _, pitch, _ = euler_from_quaternion(
            data.pose.orientation.x,
            data.pose.orientation.y,
            data.pose.orientation.z,
            data.pose.orientation.w
        )

        temp_width = data.pose.position.x * -1
        temp_distance = data.pose.position.z

        get_qr_distance = temp_distance * 100
        get_qr_distance = (0.00999177789385630000 * get_qr_distance * get_qr_distance +
                           1.95235227648073000000 * get_qr_distance +
                           4.00275749637565000000)

        if self.save_qr_distance != get_qr_distance:
            qr_distance_word = "qr_distance:" + str(get_qr_distance)
            self.send_scratch_msg(qr_distance_word, debug=True)
            self.save_qr_distance = get_qr_distance

        get_qr_width = int(temp_width * 100)
        if self.save_qr_width != get_qr_width:
            qr_width_word = "qr_width:" + str(get_qr_width)
            self.send_scratch_msg(qr_width_word)
            self.save_qr_width = get_qr_width

        qr_angle = int(math.degrees(pitch))
        if qr_angle == 0:
            return

        if self.save_qr_angle != qr_angle:
            qr_angle_word = "qr_angle:" + str(qr_angle)
            self.send_scratch_msg(qr_angle_word)
            self.save_qr_angle = qr_angle

    def bumper_state(self, data):
        if data.state == 1:
            if data.bumper == 0:
                self.send_scratch_msg('left_bumper:true')
            elif data.bumper == 1:
                self.send_scratch_msg('front_bumper:true')
            elif data.bumper == 2:
                self.send_scratch_msg('right_bumper:true')
        elif data.state == 0:
            if data.bumper == 0:
                self.send_scratch_msg('left_bumper:false')
            elif data.bumper == 1:
                self.send_scratch_msg('front_bumper:false')
            elif data.bumper == 2:
                self.send_scratch_msg('right_bumper:false')

    def button_state(self, data):
        if data.state == 0:
            if data.button == 0:
                self.send_scratch_msg('button_0:false')
            elif data.button == 1:
                self.send_scratch_msg('button_1:false')
            elif data.button == 2:
                self.send_scratch_msg('button_2:false')
        elif data.state == 1:
            if data.button == 0:
                self.send_scratch_msg('button_0:true')
            elif data.button == 1:
                self.send_scratch_msg('button_1:true')
            elif data.button == 2:
                self.send_scratch_msg('button_2:true')

    def speech_recognition(self, data):
        word = 'recognition_word:' + str(data.data)
        self.send_scratch_msg(word)

def main(args=None):
    rclpy.init(args=args)
    sc = Scratch3Connector()

    # マルチスレッドで実行し、while ループ中も他のトピック受信を妨げないようにする
    executor = MultiThreadedExecutor()
    executor.add_node(sc)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        sc.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()