#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener, TransformException

# TF確認の周期 (秒)
CHECK_PERIOD_SEC = 0.1


def euler_from_quaternion(x, y, z, w):
    """
    クォータニオン (x, y, z, w) からオイラー角 (roll, pitch, yaw) [rad] を計算するヘルパー関数
    """
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch = math.asin(t2)

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)

    return roll, pitch, yaw


class TfConfirmation(Node):
    def __init__(self):
        super().__init__('tf_confirmation')

        # TF2 の設定
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # ROS 2 ではブロッキングの while ループの代わりにタイマーで定期実行する
        self.timer = self.create_timer(CHECK_PERIOD_SEC, self.check_tf)

    def check_tf(self):
        try:
            # ROS 2 ではフレーム名の先頭スラッシュ ('/') は含めない
            trans = self.tf_buffer.lookup_transform('odom', 'base_link', rclpy.time.Time())
        except TransformException as ex:
            self.get_logger().warn(f"Could not transform base_link to odom: {ex}")
            return

        pose_x = trans.transform.translation.x * 100  # [cm]
        pose_y = trans.transform.translation.y * 100  # [cm]
        pose_z = trans.transform.translation.z * 100  # [cm]

        rot = trans.transform.rotation
        roll, pitch, yaw = euler_from_quaternion(rot.x, rot.y, rot.z, rot.w)
        angle_1 = math.degrees(roll)
        angle_2 = math.degrees(pitch)
        angle_3 = math.degrees(yaw)

        self.get_logger().info(
            f"--エンコーダ値: x:{pose_x:f} y:{pose_y:f} z:{pose_z:f} "
            f"| roll:{angle_1:f} pitch:{angle_2:f} yaw:{angle_3:f}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = TfConfirmation()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
