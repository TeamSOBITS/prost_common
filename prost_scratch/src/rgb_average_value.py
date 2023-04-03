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


class RGBAverage:

	def __init__(self):
		rospy.init_node('rgb_average_value')
		rospy.loginfo("rgb_average_value Started")


		self.bridge_image_rgb_ave = CvBridge()

		self.height_min_range = 275
		self.height_max_range = 355
		self.width_min_range = 320#275
		self.width_max_range = 360#315

		self.b = []
		self.g = []
		self.r = []

		self.pub_ros_scratch = rospy.Publisher('/ros_scratch', String, queue_size = 10)#scratchへ送るメッセージ
		self.image_sub_rgb = rospy.Subscriber("/usb_cam/image_raw",Image,self.image_rgb_ave)

	def image_rgb_ave(self, ros_image):
		try:
			frame = self.bridge_image_rgb_ave.imgmsg_to_cv2(ros_image, "bgr8")
			(width,height,channels) = frame.shape
			image_size = width * height
			#debug
			#copy_image = frame.copy()
			#print("image_size")
			#print(image_size)
			#print("height")
			#print(len(frame))#480
			#print("width")
			#print(len(frame[0]))#680
			#print("channels")
			#print(len(frame[0][0]))
			#print(" ")

			#rgb Average 物体が映る範囲
			for i in range(self.height_min_range, self.height_max_range):
				for j in range(self.width_min_range, self.width_max_range):
					self.b.append(frame[i][j][0])
					self.b.append(frame[i][j][0])
					self.g.append(frame[i][j][1])
					self.r.append(frame[i][j][2])
					#debug
					#copy_image[i][j][0] = 0
					#copy_image[i][j][1] = 0
					#copy_image[i][j][2] = 0
			#debug
			#cv2.namedWindow("image")
			#cv2.imshow("image", copy_image)
			#cv2.waitKey(10)

			b_ave = sum(self.b) / len(self.b)
			g_ave = sum(self.g) / len(self.g)
			r_ave = sum(self.r) / len(self.r)
			#rospy.loginfo("Average r:%d  g:%d b:%d", r_ave, g_ave ,b_ave)



			b_ave_word = "image_b_ave:" + str(b_ave)
			g_ave_word = "image_g_ave:" + str(g_ave)
			r_ave_word = "image_r_ave:" + str(r_ave)
			self.pub_ros_scratch.publish(b_ave_word)
			self.pub_ros_scratch.publish(g_ave_word)
			self.pub_ros_scratch.publish(r_ave_word)

			#Most common color
			if 50 > b_ave and 50 > g_ave and 50 > r_ave:
				word = "image_common_color:黒"
				self.pub_ros_scratch.publish(word)
			elif b_ave > 150 and g_ave > 150 and r_ave > 150 and 200 > b_ave and 200 > g_ave and 200 > r_ave:
				word = "image_common_color:白"
				self.pub_ros_scratch.publish(word)
			elif r_ave > g_ave and r_ave > b_ave and 100 > b_ave and 100 > g_ave :
				word = "image_common_color:赤"
				self.pub_ros_scratch.publish(word)
			elif b_ave > g_ave and b_ave > r_ave and 50 > r_ave:
				word = "image_common_color:青"
				self.pub_ros_scratch.publish(word)
			elif g_ave > b_ave and g_ave > r_ave and 50 > r_ave:
				word = "image_common_color:緑"
				self.pub_ros_scratch.publish(word)
			elif r_ave > g_ave and b_ave > g_ave:
				word = "image_common_color:紫"
				self.pub_ros_scratch.publish(word)
			elif r_ave > b_ave and g_ave > b_ave and r_ave > 150 and g_ave > 150:
				word = "image_common_color:黃"
				self.pub_ros_scratch.publish(word)
			elif g_ave > r_ave and b_ave > r_ave:
				word = "image_common_color:水色"
				self.pub_ros_scratch.publish(word)


			#initialization
			self.b = []
			self.g = []
			self.r = []

		except CvBridgeError as e:
			print(e)
		input_image = np.array(frame, dtype=np.uint8)



if __name__ == '__main__':
	rgb_a = RGBAverage()
	rospy.spin()
