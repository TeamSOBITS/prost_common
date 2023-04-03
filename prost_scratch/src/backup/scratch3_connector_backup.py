#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import cv2
import zbar
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


class Scratch3Connector:

	def __init__(self):
		rospy.init_node('scratch3_connector')
		rospy.loginfo("Scratch3_Connector Started")

		self.scanner = zbar.ImageScanner()
		self.scanner.parse_config('enable')
		self.bridge_qr = CvBridge()
		self.bridge_image_rgb_ave = CvBridge()
		self.bridge_range_drawing = CvBridge()
		self.moving_speed = Twist()
		self.listener = tf.TransformListener()
		self.save_qr_distance = 0
		self.save_qr_width = 0
		self.save_qr_angle = 0
		self.height_min_range = 275
		self.height_max_range = 355
		self.width_min_range = 320#275
		self.width_max_range = 360#315

		self.b_drawing = []
		self.g_drawing = []
		self.r_drawing = []

		self.b = []
		self.g = []
		self.r = []

		self.sub_scratch_ros = rospy.Subscriber("/scratch_ros", String, self.cb_scratch_ros)#scratchから受け取るメッセージ
		self.pub_ros_scratch = rospy.Publisher('/ros_scratch', String, queue_size = 10)#scratchへ送るメッセージ
		self.pub_ros_scratch_debug = rospy.Publisher('/ros_scratch_debug', String, queue_size = 10)#scratchへ送るメッセージ
		self.sub_bumper = rospy.Subscriber("/mobile_base/events/bumper", BumperEvent, self.bumper_state)
		self.sub_button = rospy.Subscriber("/mobile_base/events/button", ButtonEvent, self.button_state)
		self.image_sub_qr = rospy.Subscriber("/usb_cam/image_raw",Image,self.qr_recode)
		self.image_sub_rgb = rospy.Subscriber("/usb_cam/image_raw",Image,self.image_rgb_ave)
		self.image_sub_range_drawing = rospy.Subscriber("/usb_cam/image_raw",Image,self.range_drawing)
		self.sub_wifi_connect = rospy.Subscriber("/wifi_connect", Bool, self.cb_wifi_connect)
		self.sub_odom = rospy.Subscriber('/odom',Odometry, self.cb_odom)
		self.sub_speech_recognition = rospy.Subscriber('/speech_recognition/word', String, self.speech_recognition)
		self.pub_led1 = rospy.Publisher('/mobile_base/commands/led1', Led, queue_size = 10)
		self.pub_led2 = rospy.Publisher('/mobile_base/commands/led2', Led, queue_size = 10)
		self.pub_sound = rospy.Publisher('/mobile_base/commands/sound', Sound, queue_size = 10)
		self.pub_twist = rospy.Publisher('/mobile_base/commands/velocity', Twist, queue_size = 10)
		self.pub_reset_odometry = rospy.Publisher('/mobile_base/commands/reset_odometry', Empty, queue_size=10)
		self.pub_odom_base_ctrl = rospy.Publisher('/odom_base_ctrl', String, queue_size = 10)
		self.pub_speech_word = rospy.Publisher('/speech_word', String, queue_size = 10)
		self.pub_specified_range_drawing = rospy.Publisher('/specified_range_drawing', Image, queue_size = 10)
		self.sub_qr_position = rospy.Subscriber("/visp_auto_tracker/object_position", PoseStamped, self.qr_position)

		time.sleep(3)
		connection_call = String()
		connection_call = "USBを接続した後に、接続ブロックを実行してください"
		self.pub_speech_word.publish(connection_call)


	def cb_wifi_connect(self, state):
		if state.data == True:
			self.pub_led1.publish(1)#on--green
		else:
			self.pub_led1.publish(3)#off--red

	def cb_scratch_ros(self, msg):
		self.get_msg = msg.data
		print(self.get_msg)
		if(self.get_msg.find('LED:') >= 0):
			word = self.get_msg[4:len(self.get_msg)]
			#rospy.loginfo(word)
			if word == "off":
				self.pub_led2.publish(0)
			elif word == "green":
				self.pub_led2.publish(1)
			elif word == "yellow":
				self.pub_led2.publish(2)
			elif word == "red":
				self.pub_led2.publish(3)
		elif(self.get_msg.find('sound:') >= 0):
			word = self.get_msg[6:len(self.get_msg)]
			self.pub_sound.publish(np.uint8(word))
		elif(self.get_msg.find('S:') >= 0):
			self.pub_odom_base_ctrl.publish(self.get_msg)
		elif(self.get_msg.find('T:') >= 0):
			self.pub_odom_base_ctrl.publish(self.get_msg)
		elif(self.get_msg.find('move_speed:') >= 0):
			word = self.get_msg[11:len(self.get_msg)]
			self.moving_speed.linear.x = float(word) * 0.01
			self.moving_speed.angular.z = 0.0
			self.pub_twist.publish(self.moving_speed)
		elif(self.get_msg.find('rotation_speed:') >= 0):
			word = self.get_msg[15:len(self.get_msg)]
			self.moving_speed.linear.x = 0.0
			self.moving_speed.angular.z = math.radians(float(word))
			self.pub_twist.publish(self.moving_speed)
		elif(self.get_msg.find('turtlebot_cmd_vel:') >= 0):
			word = self.get_msg[18:len(self.get_msg)]
			num = word.find(',')
			vel = word[0:num]
			rad = word[num+1:len(word)]
			self.moving_speed.linear.x = float(vel) * 0.01
			self.moving_speed.angular.z = math.radians(float(rad))
			self.pub_twist.publish(self.moving_speed)
		elif(self.get_msg.find('motion_stop:') >= 0):
			word = self.get_msg[12:len(self.get_msg)]
			self.moving_speed.linear.x = 0.0
			self.moving_speed.angular.z = 0.0
			self.pub_twist.publish(self.moving_speed)
		elif(self.get_msg.find('odome_initialize') >= 0):
			reset_val = Empty()
			self.pub_reset_odometry.publish(reset_val)
		elif(self.get_msg.find('speech') >= 0):
			word = self.get_msg[7:len(self.get_msg)]
			self.pub_speech_word.publish(word)

	def cb_odom(self, data):
		robo_pose_x = data.pose.pose.position.x
		robo_pose_y = data.pose.pose.position.y
		euler = tf.transformations.euler_from_quaternion((data.pose.pose.orientation.x, data.pose.pose.orientation.y, data.pose.pose.orientation.z, data.pose.pose.orientation.w))
		robo_rad = euler[2]
		robo_deg = math.degrees(robo_rad)

		robo_pose_x_word = "robot_pose_x:" + str(robo_pose_x)
		robo_pose_y_word = "robot_pose_y:" + str(robo_pose_y)
		robo_angle_word = "robot_angle:" + str(robo_deg)

		self.pub_ros_scratch.publish(robo_pose_x_word)
		self.pub_ros_scratch.publish(robo_pose_y_word)
		self.pub_ros_scratch.publish(robo_angle_word)


	def qr_position(self, data):
		euler = tf.transformations.euler_from_quaternion((data.pose.orientation.x, data.pose.orientation.y, data.pose.orientation.z, data.pose.orientation.w))

		temp_width = data.pose.position.x * -1
		temp_high = data.pose.position.y * -1
		temp_distance = data.pose.position.z

		get_qr_distance = temp_distance * 100

		get_qr_distance = 0.00999177789385630000 * get_qr_distance * get_qr_distance + 1.95235227648073000000 * get_qr_distance + 4.00275749637565000000	#distance_calibration

		if self.save_qr_distance != get_qr_distance:
			qr_distance_word = "qr_distance:" + str(get_qr_distance)
			self.pub_ros_scratch.publish(qr_distance_word)
			self.pub_ros_scratch_debug.publish(qr_distance_word)	#デバッグ用
			self.save_qr_distance = get_qr_distance

		get_qr_width = int(temp_width * 100)
		if self.save_qr_width != get_qr_width:
			qr_width_word = "qr_width:" + str(get_qr_width)
			self.pub_ros_scratch.publish(qr_width_word)
			self.save_qr_width = get_qr_width

		qr_angle = int(math.degrees(euler[1]))
		if qr_angle == 0:
			return

		if self.save_qr_angle != qr_angle:
			qr_angle_word = "qr_angle:" + str(qr_angle)
			self.pub_ros_scratch.publish(qr_angle_word)
			self.save_qr_angle = qr_angle



	def qr_recode(self,data):
		try:
		    cv_image = self.bridge_qr.imgmsg_to_cv2(data, "bgr8")
		except CvBridgeError as e:
		    print(e)
		#input image
		img = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

		#grayscale
		img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

		#Binarization
		tresh = 100
		max_pixel = 255
		ret, img = cv2.threshold(img, tresh, max_pixel, cv2.THRESH_BINARY)

		#picture change PIL
		pil_img = PIL.Image.fromarray(img)
		width, height = pil_img.size
		raw = pil_img.tobytes()
		image = zbar.Image(width, height, 'Y800', raw)

		#result
		self.scanner.scan(image)
		word = ""
		for symbol in image:
			word = str(symbol.data)

		word = "qr_recode:" + word
		self.pub_ros_scratch.publish(String(word))

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

		except CvBridgeError, e:
			print e

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

		except CvBridgeError, e:
			print e
		input_image = np.array(frame, dtype=np.uint8)


	def bumper_state(self, data):
		word = String()
		if(1 == data.state):
			if(0 == data.bumper):
				word.data = 'left_bumper:true'
				self.pub_ros_scratch.publish(word)
			elif(1 == data.bumper):
				word.data = 'front_bumper:true'
				self.pub_ros_scratch.publish(word)
			elif(2 == data.bumper):
				word.data = 'right_bumper:true'
				self.pub_ros_scratch.publish(word)
		elif(0 == data.state):
			if(0 == data.bumper):
				word.data = 'left_bumper:false'
				self.pub_ros_scratch.publish(word)
			elif(1 == data.bumper):
				word.data = 'front_bumper:false'
				self.pub_ros_scratch.publish(word)
			elif(2 == data.bumper):
				word.data = 'right_bumper:false'
				self.pub_ros_scratch.publish(word)

	def button_state(self, data):
		word = String()
		if(0 == data.state):
			if(0 == data.button):
				word.data = 'button_0:false'
				self.pub_ros_scratch.publish(word)
			elif(1 == data.button):
				word.data = 'button_1:false'
				self.pub_ros_scratch.publish(word)
			elif(2 == data.button):
				word.data = 'button_2:false'
				self.pub_ros_scratch.publish(word)
		elif(1 == data.state):
			if(0 == data.button):
				word.data = 'button_0:true'
				self.pub_ros_scratch.publish(word)
			elif(1 == data.button):
				word.data = 'button_1:true'
				self.pub_ros_scratch.publish(word)
			elif(2 == data.button):
				word.data = 'button_2:true'
				self.pub_ros_scratch.publish(word)

	def speech_recognition(self, data):
		word = 'recognition_word:' + str(data.data)
		self.pub_ros_scratch.publish(word)


if __name__ == '__main__':
	sc = Scratch3Connector()
	rospy.spin()
