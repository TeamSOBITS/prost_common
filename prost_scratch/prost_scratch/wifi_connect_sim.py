#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wi-Fi接続確認をスキップし、常に接続済みとして扱うシミュレーション用ノード。
実機のWi-Fi状態に関わらずrosbridgeを起動したい開発・シミュレーション環境向け。
"""
import subprocess
import signal
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

# ROSトピックのキューサイズ
QUEUE_SIZE = 10
# rosbridge起動後、安定するまでの待機秒数
ROSBRIDGE_STARTUP_WAIT_SEC = 3.0
# rosbridge停止時、SIGINTへの応答を待つ最大秒数
ROSBRIDGE_SHUTDOWN_TIMEOUT_SEC = 3.0


class WifiConnectSimNode(Node):
    def __init__(self):
        super().__init__('wifi_connect_sim')

        self.declare_parameter('publish_period_sec', 1.0)
        self.declare_parameter('rosbridge_launch_pkg', 'rosbridge_server')
        self.declare_parameter('rosbridge_launch_file', 'rosbridge_websocket_launch.xml')

        self.publish_period_sec = self.get_parameter('publish_period_sec').get_parameter_value().double_value
        self.rosbridge_launch_pkg = self.get_parameter('rosbridge_launch_pkg').get_parameter_value().string_value
        self.rosbridge_launch_file = self.get_parameter('rosbridge_launch_file').get_parameter_value().string_value

        self.pub = self.create_publisher(Bool, '/wifi_connect', QUEUE_SIZE)
        self.rosbridge_proc = None

        self.get_logger().info("wifi connect check Started (simulation mode: always connected)")

        self.start_rosbridge()
        self.timer = self.create_timer(self.publish_period_sec, self.on_timer)

    def start_rosbridge(self):
        if self.rosbridge_proc is not None:
            if self.rosbridge_proc.poll() is None:
                return
            self.rosbridge_proc = None

        cmd = ['ros2', 'launch', self.rosbridge_launch_pkg, self.rosbridge_launch_file]
        self.get_logger().info(f"Starting rosbridge: {' '.join(cmd)}")
        try:
            self.rosbridge_proc = subprocess.Popen(cmd)
            time.sleep(ROSBRIDGE_STARTUP_WAIT_SEC)
        except Exception as e:
            self.get_logger().error(f"Failed to start rosbridge: {e}")
            self.rosbridge_proc = None

    def stop_rosbridge(self):
        if self.rosbridge_proc is not None and self.rosbridge_proc.poll() is None:
            self.get_logger().info("Stopping rosbridge")
            try:
                self.rosbridge_proc.send_signal(signal.SIGINT)
                try:
                    self.rosbridge_proc.wait(timeout=ROSBRIDGE_SHUTDOWN_TIMEOUT_SEC)
                except subprocess.TimeoutExpired:
                    self.rosbridge_proc.kill()
            except Exception as e:
                self.get_logger().warn(f"Failed to stop rosbridge process: {e}")
        self.rosbridge_proc = None

    def on_timer(self):
        # シミュレーション用のため実際のWi-Fi状態は確認せず常に接続済みとして扱う
        msg = Bool()
        msg.data = True
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = WifiConnectSimNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_rosbridge()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
