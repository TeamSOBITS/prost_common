#!/usr/bin/env python3
# coding: utf-8
import rospy
import tf
import math
import time
from tf.transformations import euler_from_quaternion
from geometry_msgs.msg import Pose, Point, Quaternion, Twist
from std_msgs.msg import String, Empty
from nav_msgs.msg import Odometry

import os
import numpy as np
import matplotlib.pyplot as plt
import datetime


#indent = 1 tabs
# S:1000	(1000cm直進)
# T:90		(90度回転、反時計回り正回転)

###############################################################################

class OdomBaseController:
	def __init__(self):
		self.listener = tf.TransformListener()

		#回転制御パラメータ//各自調整
		self.turn_acs = 1	#加速度(初期：0.5)
		self.turn_speed_max = 150	#最高速度(初期：20)
		self.turn_speed_min = 0
		self.turn_ki = 0.15
		#直進制御パラメータ//各自調整
		self.stlight_acs = 0.01 		#加速度(デフォルト：0.01)
		self.stlight_speed_max = 0.4 	#最高速度(デフォルト：0.2m/s)
		self.stlight_speed_min = 0		#最低速度(デフォルト:0m/s)
		self.stlight_ki = 0.1			#積分係数

		#ループ周期設定
		self.sleep_vale = 0.030

		#台形制御のグラフ描画用
		self.graph_x = []
		self.graph_y = []

		#速度更新時間計測
		self.start_measurement_time = 0
		self.speed_update_time = 0
		self.period_time = 0
		self.speed_start_flag = False

		#初期化
		self.speed = 0
		self.speed_max = 0
		self.speed_min = 0
		self.before_speed = 0
		self.current_speed = 0
		self.current_pose_x = 0
		self.current_pose_y = 0
		self.current_angle = 0
		self.before_pose_x = 0
		self.before_pose_y = 0
		self.before_angle = 0
		self.order_vale = 0
		self.moved_vale = 0
		self.error_P = 0
		self.error_I = 0
		self.move_order_T = False
		self.move_order_S = False
		self.stop_flag = False


		self.pub_twist = rospy.Publisher('/mobile_base/commands/velocity', Twist, queue_size=10)
		self.pub_output_log = rospy.Publisher('/odom_base/output_log', String, queue_size=10)
		self.pub_reset_odometry = rospy.Publisher('/mobile_base/commands/reset_odometry', Empty, queue_size=10)
		self.pub_retrun_arrive = rospy.Publisher('/retrun_arrive', String, queue_size=10)

		self.sub_motion_stop = rospy.Subscriber('/motion_stop',String, self.motion_stop)
		self.sub_odom_base_ctrl = rospy.Subscriber('/odom_base_ctrl',String, self.odom_base_ctrl)

		rospy.loginfo("odom_base_controller is OK.")


	def Check_Command(self, line):
		#print("チェックコマンド!!!")
		cmd_line = line.data[0:2]
		value_line = line.data[2:len(line.data)]
		for i in range(len(cmd_line)):
			key = cmd_line[i]
			if key == 'T' or key == 'S' or key == ':':
				#print "Check ok-1"
				pass
			else:
				rospy.loginfo("check_command cmd error")
				rospy.loginfo(line.data)
				return False
		for i in range(len(value_line)):
			key = value_line[i]
			if key >= '0' and key <= '9' or key == '-' or key == '.':
				#print "Check ok-2"
				pass
			else:
				rospy.loginfo("check_command cmd error")
				rospy.loginfo(line.data)
				return False
		return True

	def Read_Value(self, line):
		#print("値の読み込み！！！")
		value_str = line.data[2:len(line.data)]
		value = float(value_str)
		return value

	def motion_stop(self,data):
		#print("-- get stop flag")
		self.stop_flag = True

	def odom_base_ctrl(self,motion):
		#rospy.loginfo("move_order_T: %s" % (self.move_order_T))
		#rospy.loginfo("move_order_S: %s" % (self.move_order_S))
		if self.move_order_T == True or self.move_order_S == True:
			rospy.loginfo("Sorry, the action is not registered.")
			return "False"
		check = self.Check_Command(motion)
		if check == False:
			rospy.loginfo("The command cannot be carried out.")
			return "False"
		else:
			if "T" in motion.data:
				self.order_vale = self.Read_Value(motion)
				self.move_order_T = True
				rospy.loginfo("order: Turn: %f(deg)" % (self.order_vale))
				#注意：描画するとループ周期が長くなる
				#グラフ描画準備①
				"""
				title = str(self.order_vale)
				fig = plt.figure()
				print("---ここでセグメントフォルス---")
				plt.title("order_vale: " + title + " (deg)")
				plt.ylabel("speed[rad/sec]")
				"""
			elif "S" in motion.data:
				self.order_vale = self.Read_Value(motion)#cm
				self.move_order_S = True
				rospy.loginfo("order: Straight: %f(cm)" % (self.order_vale))
				#グラフ描画準備①
				"""
				title = str(self.order_vale)
				fig = plt.figure()
				plt.title("order_vale: " + title + " (cm)")
				plt.ylabel("speed[m/sec]")
				"""
		if self.move_order_T == True and self.move_order_S == False:
			#回転制御パラメータ
			self.speed_acs = self.turn_acs
			self.speed_max = self.turn_speed_max
			self.speed_min = self.turn_speed_min
			self.ki = self.turn_ki
		elif self.move_order_T == False and self.move_order_S == True:
			#直進制御パラメータ
			self.speed_acs = self.stlight_acs
			self.speed_max = self.stlight_speed_max
			self.speed_min = self.stlight_speed_min
			self.ki = self.stlight_ki

		#現在のエンコーダ値を保存//プログラム内に保存していたエンコーダ値を更新（学生が素手でロボットを動かす時があるため、エンコーダ値が変化するため）
		(trans,rot) = self.listener.lookupTransform('/base_link', '/odom', rospy.Time(0))
		euler = tf.transformations.euler_from_quaternion((rot[0],rot[1],rot[2],rot[3]))
		#現在位置代入
		self.before_pose_x = trans[0] * 100#[cm]
		self.before_pose_y = trans[1] * 100#[cm]
		self.before_angle = math.degrees(euler[2])#[deg]
		rospy.loginfo("--開始地点のエンコーダ値: x:%f y:%f angle:%f", self.before_pose_x, self.before_pose_y, self.before_angle)

		#グラフ描画準備②
		"""
		plt.xlabel("time[sec]")
		self.graph_x.append(0)
		self.graph_y.append(0)
		ax = fig.add_subplot(1, 1, 1)
		ax.plot(self.graph_x, self.graph_y)
		"""

		while True:
			time.sleep(self.sleep_vale)
			send_cmd = Twist()#メッセージ変数の宣言
			#rospy.loginfo("move_order_T: %s" % (self.move_order_T))
			#rospy.loginfo("move_order_S: %s" % (self.move_order_S))


##########################################################################################################################################
			if self.move_order_T == False and self.move_order_S == False:
				#rospy.loginfo("move order flag False")
				self.pub_twist.publish(Twist())#停止
				break
			elif self.stop_flag == True:#動作中止判定
				self.stop_flag = False#初期化
				self.speed = 0
				self.current_speed = 0
				self.order_vale = 0
				self.moved_vale = 0
				self.error_P = 0
				self.error_I = 0
				self.move_order_S = False
				self.move_order_T = False
				self.pub_twist.publish(Twist())#停止
				rospy.loginfo("stop flag True")
				break
			else:
				#加速区間
				if self.moved_vale < abs(self.order_vale) / 5:
					self.speed += self.speed_acs
					self.current_speed = self.speed
					#rospy.loginfo("加速区間 %f"%(self.speed))
				#減速区間
				elif self.moved_vale > abs(self.order_vale) * 4 / 5:
						#PI制御
						self.before_speed = self.speed	#前回パブリッシュした速度を保存
						if self.speed > self.error_I:    #現在のスピードが積分係数より小さい時
							self.error_P = (abs(self.order_vale) - self.moved_vale) / (abs(self.order_vale) / 5)#小さくなる
							self.speed = self.current_speed * self.error_P + self.error_I#小さくなる
							self.error_I += (self.before_speed - self.speed)*self.ki#小さくなる
							#print "error_T_I=%f" % self.error_T_I
						elif self.speed <= self.error_I:
							self.speed = self.error_I
						else:
							pass
						#rospy.loginfo("減速区間 %f"%(self.speed))
				#等速区間
				else:
					#rospy.loginfo("等速区間 %f"%(self.speed))
					pass

				#最高速度補正
				if self.speed >= self.speed_max:
					self.speed = self.speed_max
					#rospy.loginfo("最高速度補正 %f"%(self.speed))
				#逆走防止
				if self.speed < self.speed_min:
					self.speed = self.speed_min
					#rospy.loginfo("逆走防止 %f"%(self.speed))


				#print('speed:' + str(self.speed))


##########################################################################################################################################
				if self.move_order_T == True and self.move_order_S == False:
					if self.order_vale > 0:
						send_cmd.angular.z = math.radians(-self.speed)
					else:#時計回り
						send_cmd.angular.z = math.radians(self.speed)
					#rospy.loginfo("Turn send_cmd: %f"%(send_cmd.angular.z))

					if self.speed_start_flag == True:
						#速度更新周期算出
						self.period_time = time.time() - self.speed_update_time
						#rospy.loginfo("速度更新周期: %f[sec]"%(self.period_time))
					if self.moved_vale < abs(self.order_vale):
						self.pub_twist.publish(send_cmd)
						#速度更新時間計測開始
						self.speed_update_time = time.time()
						if self.speed_start_flag == False:
							self.start_measurement_time = time.time()
							self.speed_start_flag = True
						#グラフを表示
						"""
						elapsed_time = time.time() - self.start
						#rospy.loginfo("現在時間:%f[sec]",time.time())
						#rospy.loginfo("time:%f[sec]",elapsed_time)
						#rospy.loginfo("speed:%f[rad/sec]",abs(send_cmd.angular.z))
						#rospy.loginfo("speed_2:%f",self.speed)
						self.graph_x.append(elapsed_time)
						self.graph_y.append(abs(send_cmd.angular.z))
						ax.plot(self.graph_x, self.graph_y, marker="o", color = "red", linestyle = "--")
						plt.pause(.01)
						"""
						#現在位置代入
						(trans,rot) = self.listener.lookupTransform('/base_link', '/odom', rospy.Time(0))
						euler = tf.transformations.euler_from_quaternion((rot[0],rot[1],rot[2],rot[3]))
						self.current_pose_x = trans[0] * 100#[cm]
						self.current_pose_y = trans[1] * 100#[cm]
						self.current_angle = math.degrees(euler[2])#[deg]
						#rospy.loginfo("-エンコーダ値- x: %f[cm] y: %f[cm] angle: %f[deg]",self.current_pose_x, self.current_pose_y, self.current_angle )
						#rospy.loginfo("          order_vale: %f moved_vale: %f",self.order_vale , self.moved_vale)
						#移動角度算出
						sub_point = abs(self.current_angle - self.before_angle)#例：開始角度350 終了角度10→移動角度20を算出する際使用//この処理がないと340が移動角度になる  ☆最後の測定量(before_angle)が間違っていた!//外乱（生徒がロボットを素手で動かす）
						if sub_point > 180:
							sub_point = abs(sub_point - 360)
						self.moved_vale += sub_point#加算 ☆移動量が間違っていた
						rospy.loginfo("現在の回転角度:%f[deg]", self.moved_vale)
						rospy.loginfo(" ")
						#開始地点保存
						self.before_pose_x = self.current_pose_x
						self.before_pose_y = self.current_pose_y
						self.before_angle = self.current_angle
					else:
						self.period_time = time.time() - self.speed_update_time
						#rospy.loginfo("速度更新周期: %f[sec]"%(self.period_time))
						self.pub_twist.publish(Twist())#停止
						all_time = time.time() - self.start_measurement_time
						#print(" ")
						print ("総回転時間 :"+ str(all_time) + "[sec]")
						#print(" ")
						#台形制御のグラフの保存
						"""
						elapsed_time = time.time() - self.start_time
						print ("処理終了時間:"+ format(elapsed_time) + "[sec]")
						self.graph_x.append(elapsed_time)
						self.graph_y.append(0)
						ax.plot(self.graph_x, self.graph_y, marker="o", color = "red", linestyle = "--")
						dt_now = datetime.datetime.now()
						file_name = str(dt_now)
						plt.savefig(os.path.join(os.path.abspath(".") + "/catkin_ws/src/prost_scratch/png/", "figure_" + file_name + ".png"))
						plt.close(fig)
						"""
						#rospy.loginfo("finished")
						self.speed = 0
						self.current_speed = 0
						self.order_vale = 0
						self.moved_vale = 0
						self.error_P = 0
						self.error_I = 0
						self.move_order_T = False
						self.speed_start_flag =  False
						self.graph_x = []
						self.graph_y = []
						output_log = str(self.order_vale) + "_finished"
						self.pub_output_log.publish(output_log)
						#到着合図
						end = String()
						end.data = "move end"
						self.pub_retrun_arrive.publish(end)


##########################################################################################################################################
				elif self.move_order_T == False and self.move_order_S == True:
					if self.order_vale > 0:
						send_cmd.linear.x = self.speed #m/sec
					else:
						send_cmd.linear.x = -self.speed #m/sec
					#rospy.loginfo("stlight send_cmd: %f"%(send_cmd.linear.x))

					if self.moved_vale < abs(self.order_vale):
						if self.speed_start_flag == True:
							#速度更新周期算出
							self.period_time = time.time() - self.speed_update_time
							#rospy.loginfo("速度更新周期: %f[sec]"%(self.period_time))
						#☆速度更新時間計測開始
						self.pub_twist.publish(send_cmd)
						self.speed_update_time = time.time()
						if self.speed_start_flag == False:
							self.start_measurement_time = time.time()
							self.speed_start_flag = True

						#グラフを表示
						"""
						elapsed_time = time.time() - self.start
						rospy.loginfo("現在時間:%f[sec]",time.time())
						rospy.loginfo("time:%f[sec]",elapsed_time)
						rospy.loginfo("speed:%f[m/sec]",abs(send_cmd.linear.x))
						#rospy.loginfo("speed_2:%f",self.speed)
						self.graph_x.append(elapsed_time)
						self.graph_y.append(abs(send_cmd.linear.x))
						ax.plot(self.graph_x, self.graph_y, marker="o", color = "blue", linestyle = "--")
						plt.pause(.01)
						"""

						#現在位置代入
						(trans,rot) = self.listener.lookupTransform('/base_link', '/odom', rospy.Time(0))
						euler = tf.transformations.euler_from_quaternion((rot[0],rot[1],rot[2],rot[3]))
						self.current_pose_x = trans[0] * 100#[cm]
						self.current_pose_y = trans[1] * 100#[cm]
						self.current_angle = math.degrees(euler[2])#[deg]
						#rospy.loginfo("-エンコーダ値- x: %f[cm] y: %f[cm] angle: %f[deg]",self.current_pose_x, self.current_pose_y, self.current_angle )
						#rospy.loginfo("          order_vale: %f moved_vale: %f",self.order_vale , self.moved_vale)
						#移動距離算出
						sub_x = self.before_pose_x - self.current_pose_x
						sub_y = self.before_pose_y - self.current_pose_y
						self.moved_vale = math.hypot(sub_x,sub_y)
						rospy.loginfo("現在の移動距離: %f[cm]", self.moved_vale)
						rospy.loginfo(" ")
					else:
						self.period_time = time.time() - self.speed_update_time
						#rospy.loginfo("速度更新周期: %f[sec]"%(self.period_time))
						self.pub_twist.publish(Twist())#停止
						#rospy.loginfo("速度更新周期: %f[sec]"%(self.period_time))
						all_time = time.time() - self.start_measurement_time
						#print(" ")
						print ("総移動時間:"+ str(all_time) + "[sec]")
						#print(" ")
						#台形制御のグラフの保存
						"""
						elapsed_time = time.time() - self.start
						print ("処理終了時間:"+ format(elapsed_time) + "[sec]")
						#台形制御のグラフの保存
						self.graph_x.append(elapsed_time)
						self.graph_y.append(0)
						ax.plot(self.graph_x, self.graph_y, marker="o", color = "blue", linestyle = "--")
						dt_now = datetime.datetime.now()
						file_name = str(dt_now)
						plt.savefig(os.path.join(os.path.abspath(".") + "/catkin_ws/src/prost_scratch/png/", "figure_" + file_name + ".png"))
						plt.close(fig)
						"""
						self.speed = 0
						self.current_speed = 0
						self.order_vale = 0
						self.moved_vale = 0
						self.error_P = 0
						self.error_I = 0
						self.graph_x = []
						self.graph_y = []
						self.move_order_S = False
						self.speed_start_flag = False
						output_log = str(self.order_vale) + "_finished"
						#到着合図
						end = String()
						end.data = "move end"
						self.pub_retrun_arrive.publish(end)
		#/odom初期化#確認
		reset_val = Empty()
		#self.pub_reset_odometry.publish(reset_val)
		rospy.sleep(0.1)
		rospy.loginfo("Moving Finished")
		#ラズパイ側自動git pull確認用コメント--最終確認
		#rospy.loginfo("---- %s" % motion.data)









if __name__ == '__main__':

	rospy.init_node('odom_base_controller')

	obc = OdomBaseController()
	rospy.spin()
