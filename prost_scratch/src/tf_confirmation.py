#!/usr/bin/env python3
# coding: utf-8
import rospy
import tf
import math
import time
from tf.transformations import euler_from_quaternion
from geometry_msgs.msg import Pose, Point, Quaternion, Twist
from std_msgs.msg import String
from nav_msgs.msg import Odometry

import os
import numpy as np
import matplotlib.pyplot as plt
import datetime



class TfConfirmation:
	def __init__(self):
		self.listener = tf.TransformListener()

		rospy.sleep(3)

		while not rospy.is_shutdown():
			(trans,rot) = self.listener.lookupTransform('/base_link', '/odom', rospy.Time(0))
			euler = tf.transformations.euler_from_quaternion((rot[0],rot[1],rot[2],rot[3]))
			#現在位置代入
			before_pose_x = trans[0] * 100#[cm]
			before_pose_y = trans[1] * 100#[cm]
			before_pose_z = trans[2] * 100#[cm]
			before_angle_1 = math.degrees(euler[0])#[deg]
			before_angle_2 = math.degrees(euler[1])#[deg]
			before_angle_3 = math.degrees(euler[2])#[deg]
			#print "-- trans"
			#print len(trans)
			#print "-- len"
			#print len(euler)
			rospy.loginfo("--エンコーダ値: x:%f y:%f z:%f | roll:%f pitch:%f yaw:%f", before_pose_x, before_pose_y, before_pose_z, before_angle_1, before_angle_2, before_angle_3)


		rospy.loginfo("break OK.")


if __name__ == '__main__':

	rospy.init_node('tf_confirmation')

	tc = TfConfirmation()
	rospy.spin()
