#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import cv2
import pyzbar.pyzbar as pyzbar
import PIL.Image
import numpy as np
from std_msgs.msg import String, UInt8, Empty, Bool
from sensor_msgs.msg import LaserScan, Image
from cv_bridge import CvBridge, CvBridgeError


class QrRecode:

    def __init__(self):
        rospy.init_node('qr_recode')
        rospy.loginfo("qr_recode Started")

        self.bridge_qr = CvBridge()
        self.pub_ros_scratch = rospy.Publisher('/ros_scratch', String, queue_size=10)

        self.image_sub_qr = rospy.Subscriber("/usb_cam/image_raw", Image, self.qr_recode)

    def qr_recode(self, data):
        try:
            cv_image = self.bridge_qr.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            print(e)

        # input image
        img = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

        # grayscale
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Binarization
        tresh = 100
        max_pixel = 255
        ret, img = cv2.threshold(img, tresh, max_pixel, cv2.THRESH_BINARY)

        # picture change PIL
        pil_img = PIL.Image.fromarray(img)
        width, height = pil_img.size
        raw = pil_img.tobytes()

        # result
        decoded = pyzbar.decode(raw)

        word = ""
        for d in decoded:
            word = str(d.data)

        word = "qr_recode:" + word
        self.pub_ros_scratch.publish(String(word))


if __name__ == '__main__':
    qr = QrRecode()
    rospy.spin()