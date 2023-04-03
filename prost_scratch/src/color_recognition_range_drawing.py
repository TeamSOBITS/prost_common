#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import cv2
import pyzbar
import PIL.Image
import numpy as np
import tf
import math
from std_msgs.msg import String,UInt8,Empty,Bool
from geometry_msgs.msg import Twist,Quaternion,PoseStamped
from sensor_msgs.msg import LaserScan,Image
from kobuki_msgs.msg import *
from nav_msgs.msg import Odometry
from cv_bridge import CvBridge, CvBridgeError


class ColorDrawing:

	def __init__(self):
		rospy.init_node('color_recognition_range_drawing')
		rospy.loginfo("color_recognition_range_drawing Started")

		self.bridge_range_drawing = CvBridge()

		self.height_min_range = 275
		self.height_max_range = 355
		self.width_min_range = 320#275
		self.width_max_range = 360#315

		self.b_drawing = []
		self.g_drawing = []
		self.r_drawing = []


		self.pub_ros_scratch = rospy.Publisher('/ros_scratch', String, queue_size = 10)#scratchへ送るメッセージ
		self.image_sub_range_drawing = rospy.Subscriber("/usb_cam/image_raw",Image,self.range_drawing)
		self.pub_specified_range_drawing = rospy.Publisher('/specified_range_drawing', Image, queue_size = 10)

	def range_drawing(self, image):
		try:
			cv_image = self.bridge_range_drawing.imgmsg_to_cv2(image, "bgr8")
			(width,height,channels) = cv_image.shape
			image_size = width * height
			copy_cv_image = cv_image.copy()

			for i in range(self.height_min_range, self.height_max_range):
				for j in range(self.width_min_range, self.width_max_range):
					self.b_drawing.append(cv_image[i][j][0])
					self.g_drawing.append(cv_image[i][j][1])
					self.r_drawing.append(cv_image[i][j][2])

			cv2.rectangle(copy_cv_image,(self.width_min_range,self.height_min_range),(self.width_max_range,self.height_max_range),(0,255,255),2)
			specified_range_image = self.bridge_range_drawing.cv2_to_imgmsg(copy_cv_image, "bgr8")
			self.pub_specified_range_drawing.publish(specified_range_image)

			#initialization
			self.b_drawing = []
			self.g_drawing = []
			self.r_drawing = []

		except CvBridgeError as e:
			print(e)

if __name__ == '__main__':
	cd = ColorDrawing()
	rospy.spin()
