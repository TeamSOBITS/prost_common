#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import cv2
import numpy as np
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError


#HSVでの色名判定しきい値 (H:度数0-360, S/V:0-255)
BLACK_V_MAX = 60
RED_H_MAX = 25
RED_H_MIN_WRAP = 330
YELLOW_H_MIN = 25
YELLOW_H_MAX = 90
YELLOW_S_MIN = 50
GREEN_H_MIN = 150
GREEN_H_MAX = 180
GREEN_S_MIN = 50
CYAN_H_MIN = 150
CYAN_H_MAX = 210
CYAN_S_MIN = 60
CYAN_V_MIN = 70
BLUE_H_MIN = 210
BLUE_H_MAX = 260
BLUE_S_MIN = 50
PURPLE_H_MIN = 210
PURPLE_H_MAX = 280

#OpenCVのH(0-179)を度数(0-360)に変換する係数
OPENCV_HUE_TO_DEGREES = 2

#色判定モード切り替え ("hsv" または "rgb" に書き換えて切り替える)
COLOR_MODE = "hsv"

#RGBでの色名判定しきい値 (0-255)
RGB_BLACK_MAX = 50
RGB_RED_OTHER_MAX = 100
RGB_BLUE_GREEN_R_MAX = 50
RGB_YELLOW_MIN = 150

ROI_HEIGHT_MIN = 220
ROI_HEIGHT_MAX = 260
ROI_WIDTH_MIN = 300
ROI_WIDTH_MAX = 340


PUBLISHER_QUEUE_SIZE = 10


def map_hsv_to_color_name(H, S, V):

	if V < BLACK_V_MAX:
		return "黒"
	if (0 <= H < RED_H_MAX) or (RED_H_MIN_WRAP <= H <= 360):
		return "赤"
	if YELLOW_H_MIN <= H < YELLOW_H_MAX and S > YELLOW_S_MIN:
		return "黄"
	if GREEN_H_MIN <= H < GREEN_H_MAX and S > GREEN_S_MIN:
		return "緑"
	if CYAN_H_MIN <= H < CYAN_H_MAX and S > CYAN_S_MIN and V > CYAN_V_MIN:
		return "水色"
	if BLUE_H_MIN <= H < BLUE_H_MAX and S > BLUE_S_MIN:
		return "青"
	if PURPLE_H_MIN <= H < PURPLE_H_MAX:
		return "紫"

	return "不明"


def map_rgb_to_color_name(r, g, b):
	""" 従来の RGB 判定ルール """
	if b < RGB_BLACK_MAX and g < RGB_BLACK_MAX and r < RGB_BLACK_MAX:
		return "黒"
	elif r > g and r > b and g < RGB_RED_OTHER_MAX and b < RGB_RED_OTHER_MAX:
		return "赤"
	elif b > g and b > r and r < RGB_BLUE_GREEN_R_MAX:
		return "青"
	elif g > b and g > r and r < RGB_BLUE_GREEN_R_MAX:
		return "緑"
	elif r > g and b > g:
		return "紫"
	elif r > b and g > b and r > RGB_YELLOW_MIN and g > RGB_YELLOW_MIN:
		return "黄"
	elif g > r and b > r:
		return "水色"

	return "不明"


class RGBAverage:

	def __init__(self):
		rospy.init_node('rgb_average_value')
		rospy.loginfo("rgb_average_value Started")
		rospy.loginfo("color_mode: %s", COLOR_MODE)

		self.bridge_image_rgb_ave = CvBridge()

		self.height_min_range = ROI_HEIGHT_MIN
		self.height_max_range = ROI_HEIGHT_MAX
		self.width_min_range = ROI_WIDTH_MIN
		self.width_max_range = ROI_WIDTH_MAX

		self.b = []
		self.g = []
		self.r = []

		self.pub_ros_scratch = rospy.Publisher('/ros_scratch', String, queue_size = PUBLISHER_QUEUE_SIZE)#scratchへ送るメッセージ
		self.pub_roi_drawing = rospy.Publisher('/rgb_average_value/roi_image', Image, queue_size = PUBLISHER_QUEUE_SIZE)#参照範囲を可視化した画像
		self.image_sub_rgb = rospy.Subscriber("/usb_cam/image_raw",Image,self.image_rgb_ave)

	def image_rgb_ave(self, ros_image):
		try:
			frame = self.bridge_image_rgb_ave.imgmsg_to_cv2(ros_image, "bgr8")

			#rgb Average 物体が映る範囲
			for i in range(self.height_min_range, self.height_max_range):
				for j in range(self.width_min_range, self.width_max_range):
					self.b.append(frame[i][j][0])
					self.g.append(frame[i][j][1])
					self.r.append(frame[i][j][2])

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

			#rgb average -> hsv変換 (OpenCVのH:0-179, S/V:0-255)
			bgr_ave = np.uint8([[[b_ave, g_ave, r_ave]]])
			hsv_ave = cv2.cvtColor(bgr_ave, cv2.COLOR_BGR2HSV)
			h_ave, s_ave, v_ave = hsv_ave[0][0]

			h_ave_word = "image_h_ave:" + str(h_ave)
			s_ave_word = "image_s_ave:" + str(s_ave)
			v_ave_word = "image_v_ave:" + str(v_ave)
			self.pub_ros_scratch.publish(h_ave_word)
			self.pub_ros_scratch.publish(s_ave_word)
			self.pub_ros_scratch.publish(v_ave_word)

			#Most common color : ファイル先頭のCOLOR_MODE定数でHSV/RGB判定を切り替え (デフォルトはhsv)
			if COLOR_MODE == 'rgb':
				color_name = map_rgb_to_color_name(int(r_ave), int(g_ave), int(b_ave))
				word_color = "image_common_color:" + color_name
				#rospy.loginfo("R:%d G:%d B:%d -> %s", int(r_ave), int(g_ave), int(b_ave), color_name)
			else:
				H_deg = int(h_ave) * OPENCV_HUE_TO_DEGREES
				color_name = map_hsv_to_color_name(H_deg, int(s_ave), int(v_ave))
				word_color = "image_common_color_hsv:" + color_name
				rospy.loginfo("H_deg:%d S:%d V:%d -> %s", H_deg, int(s_ave), int(v_ave), color_name)
			self.pub_ros_scratch.publish(word_color)

			#参照しているROIを矩形で描いて可視化
			roi_drawing_image = frame.copy()
			cv2.rectangle(roi_drawing_image, (self.width_min_range, self.height_min_range), (self.width_max_range, self.height_max_range), (0, 255, 255), 2)
			self.pub_roi_drawing.publish(self.bridge_image_rgb_ave.cv2_to_imgmsg(roi_drawing_image, "bgr8"))

			#initialization
			self.b = []
			self.g = []
			self.r = []

		except CvBridgeError as e:
			print(e)



if __name__ == '__main__':
	rgb_a = RGBAverage()
	rospy.spin()
