#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search for a specific wifi ip and connect to it.
written by kasramvd.
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
# 切断検知後、次のチェックまでのクールダウン秒数
DISCONNECT_COOLDOWN_SEC = 3.0


class WifiConnectNode(Node):
    def __init__(self):
        super().__init__('wifi_connect')

        self.declare_parameter('ip_prefix', '192.168.1.')  # 接続を確認したいIP設定
        self.declare_parameter('check_period_sec', 1.0)
        self.declare_parameter('rosbridge_launch_pkg', 'rosbridge_server')
        self.declare_parameter('rosbridge_launch_file', 'rosbridge_websocket_launch.xml')

        self.ip_prefix = self.get_parameter('ip_prefix').get_parameter_value().string_value
        self.check_period_sec = self.get_parameter('check_period_sec').get_parameter_value().double_value
        self.rosbridge_launch_pkg = self.get_parameter('rosbridge_launch_pkg').get_parameter_value().string_value
        self.rosbridge_launch_file = self.get_parameter('rosbridge_launch_file').get_parameter_value().string_value

        self.pub = self.create_publisher(Bool, '/wifi_connect', QUEUE_SIZE)

        self.node_kill_flag = False
        self.rosbridge_proc = None

        self.prev_connected = None  # type: bool | None

        self.get_logger().info("wifi connect check Started")
        self.timer = self.create_timer(self.check_period_sec, self.on_timer)

    def get_host_ips(self) -> str:
        try:
            out = subprocess.check_output(['hostname', '-I'], stderr=subprocess.STDOUT).decode().strip()
            return out
        except Exception as e:
            self.get_logger().warn(f"Failed to run hostname -I: {e}")
            return ""

    def is_connected(self) -> tuple[bool, str]:
        ips = self.get_host_ips()
        return (self.ip_prefix in ips), ips

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

    def publish_state(self, connected: bool):
        msg = Bool()
        msg.data = connected
        self.pub.publish(msg)

    def on_timer(self):
        connected, ips = self.is_connected()

        if self.prev_connected is None:
            if connected:
                self.get_logger().info(f"Wi-Fi CONNECTED (matched '{self.ip_prefix}') | IPs: {ips}")
            else:
                self.get_logger().warn(f"Wi-Fi DISCONNECTED (no match '{self.ip_prefix}') | IPs: {ips}")
        elif connected != self.prev_connected:
            if connected:
                self.get_logger().info(f"Wi-Fi CONNECTED (matched '{self.ip_prefix}') | IPs: {ips}")
            else:
                self.get_logger().warn(f"Wi-Fi DISCONNECTED (no match '{self.ip_prefix}') | IPs: {ips}")

        self.prev_connected = connected

        if connected:
            if self.node_kill_flag is True:
                self.start_rosbridge()
                self.node_kill_flag = False
            self.publish_state(True)
        else:
            self.publish_state(False)
            self.node_kill_flag = True
            self.stop_rosbridge()
            time.sleep(DISCONNECT_COOLDOWN_SEC)


def main():
    rclpy.init()
    node = WifiConnectNode()
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
