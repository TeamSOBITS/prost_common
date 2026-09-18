#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError


class ColorDrawing(Node):

    def __init__(self):
        # Node クラスの初期化（ノード名を指定）
        super().__init__('color_recognition_range_drawing')
        self.get_logger().info("color_recognition_range_drawing Started")

        self.bridge_range_drawing = CvBridge()

        # ROI (Region of Interest) の範囲設定
        self.height_min_range = 275
        self.height_max_range = 355
        self.width_min_range = 320
        self.width_max_range = 360

        # Publisher の作成
        self.pub_ros_scratch = self.create_publisher(String, '/ros_scratch', 10)
        self.pub_specified_range_drawing = self.create_publisher(Image, '/specified_range_drawing', 10)

        # Subscriber の作成
        self.image_sub_range_drawing = self.create_subscription(
            Image,
            '/usb_cam/image_raw',
            self.range_drawing,
            10
        )

    def range_drawing(self, msg):
        try:
            cv_image = self.bridge_range_drawing.imgmsg_to_cv2(msg, "bgr8")
            
            # 1. cv2.shape の正確なアンパック (height, width, channels)
            img_height, img_width, _ = cv_image.shape

            # 2. 配列の範囲外アクセス（IndexError）を防止するクリッピング処理
            h_min = max(0, min(self.height_min_range, img_height))
            h_max = max(0, min(self.height_max_range, img_height))
            w_min = max(0, min(self.width_min_range, img_width))
            w_max = max(0, min(self.width_max_range, img_width))

            # 3. NumPy スライスによる高速な指定領域 (ROI) の抽出
            roi = cv_image[h_min:h_max, w_min:w_max]

            # 抽出したピクセル値（配列型）
            # 必要に応じて利用してください（例: np.mean(roi, axis=(0, 1)) で平均RGBを取得など）
            b_drawing = roi[:, :, 0].ravel()
            g_drawing = roi[:, :, 1].ravel()
            r_drawing = roi[:, :, 2].ravel()

            # 4. 矩形を描画（元の画像を汚さないように copy を使用）
            copy_cv_image = cv_image.copy()
            cv2.rectangle(
                copy_cv_image,
                (w_min, h_min),
                (w_max, h_max),
                (0, 255, 255),
                2
            )

            # 5. 画像メッセージに変換して Publish
            specified_range_image = self.bridge_range_drawing.cv2_to_imgmsg(copy_cv_image, "bgr8")
            self.pub_specified_range_drawing.publish(specified_range_image)

        except CvBridgeError as e:
            self.get_logger().error(f"cv_bridge error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ColorDrawing()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()