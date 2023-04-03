#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import cv2
import pyzbar
import PIL.Image
import numpy as np
import tf
import math
import time
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

		self.save_qr_distance = 0
		self.save_qr_width = 0
		self.save_qr_angle = 0
		self.moving_speed = Twist()
		self.listener = tf.TransformListener()
		self.start = rospy.Timer
		self.end = rospy.Timer

		self.sub_scratch_ros = rospy.Subscriber("/scratch_ros", String, self.cb_scratch_ros)#scratchから受け取るメッセージ
		self.pub_ros_scratch = rospy.Publisher('/ros_scratch', String, queue_size = 10)#scratchへ送るメッセージ
		self.pub_ros_scratch_debug = rospy.Publisher('/ros_scratch_debug', String, queue_size = 10)#scratchへ送るメッセージ（デバッグ）
		self.sub_bumper = rospy.Subscriber("/mobile_base/events/bumper", BumperEvent, self.bumper_state)#for bumper
		self.sub_button = rospy.Subscriber("/mobile_base/events/button", ButtonEvent, self.button_state)#
		self.sub_wifi_connect = rospy.Subscriber("/wifi_connect", Bool, self.cb_wifi_connect)
		self.sub_odom = rospy.Subscriber('/odom',Odometry, self.cb_odom)#自己位置
		self.sub_speech_recognition = rospy.Subscriber('/speech_recognition/word', String, self.speech_recognition)#発話
		self.pub_led1 = rospy.Publisher('/mobile_base/commands/led1', Led, queue_size = 10)
		self.pub_led2 = rospy.Publisher('/mobile_base/commands/led2', Led, queue_size = 10)
		self.pub_sound = rospy.Publisher('/mobile_base/commands/sound', Sound, queue_size = 10)
		self.pub_twist = rospy.Publisher('/mobile_base/commands/velocity', Twist, queue_size = 5)
		self.pub_reset_odometry = rospy.Publisher('/mobile_base/commands/reset_odometry', Empty, queue_size=10)#自己位置初期化
		self.pub_odom_base_ctrl = rospy.Publisher('/odom_base_ctrl', String, queue_size = 10)
		self.pub_speech_word = rospy.Publisher('/speech_word', String, queue_size = 10)
		self.sub_qr_position = rospy.Subscriber("/visp_auto_tracker/object_position", PoseStamped, self.qr_position)#QRの読み取り

		time.sleep(3)
		connection_call = String()
		connection_call = "みどりいろのUSBを接続した後に、接続ブロックを実行してください"
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
			word = self.get_msg[11:self.get_msg.find(',')]
			if float(word) > 50:
				word = 50
			if float(word) < -50:
				word = -50
			self.moving_speed.linear.x = float(word) * 0.01
			self.moving_speed.angular.z = 0.0
			if(self.get_msg.find('second:') >= 0):
				second = self.get_msg[self.get_msg.index(',')+8:len(self.get_msg)]
			else:
				second = 1
			begin = rospy.get_time()
			while True:
				check = rospy.get_time() - begin
				if check >= float(second):
					self.moving_speed.linear.x = 0
					self.pub_twist.publish(self.moving_speed)
					print(check)
					break
				self.pub_twist.publish(self.moving_speed)
		elif(self.get_msg.find('rotation_speed:') >= 0):
			word = self.get_msg[15:self.get_msg.find(',')]
			if float(word) > 120:
				word = 120
			if float(word) < -120:
				word = -120
			self.moving_speed.linear.x = 0.0
			self.moving_speed.angular.z = math.radians(float(word))
			if(self.get_msg.find('second:') >= 0):
				second = self.get_msg[self.get_msg.index(',')+8:len(self.get_msg)]
			else:
				second = 1
			begin = rospy.get_time()
			while True:
				check = rospy.get_time() - begin
				if check >= float(second):
					self.moving_speed.angular.z = 0
					self.pub_twist.publish(self.moving_speed)
					print(check)
					break
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
