#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search for a specific wifi ssid and connect to it.
written by kasramvd.
"""
import os
from subprocess import check_output, Popen
import rospy
from std_msgs.msg import Bool

if __name__ == "__main__":
    rospy.init_node('wifi_connect')
    rospy.loginfo("wifi connect check Started")
    IP = "1" #シミュレーション用万能設定
    connect_state = Bool()
    node_kill_flag = False
    pub_wifi_connect = rospy.Publisher('/wifi_connect', Bool, queue_size=10)

    while not rospy.is_shutdown():
        wifi_ip = check_output(['hostname', '-I']).decode('utf-8')
        if IP in wifi_ip:
            if node_kill_flag == True:
                node_run = Popen(["roslaunch","rosbridge_server","rosbridge_websocket.launch"])
                rospy.sleep(3)
                node_kill_flag = False
            connect_state.data = True
            pub_wifi_connect.publish(connect_state)
            rospy.sleep(1)
        else:
            connect_state.data = False
            pub_wifi_connect.publish(connect_state)
            node_kill_flag = True
            node_kill = Popen(["rosnode","kill","/rosbridge_websocket"])
            rospy.sleep(3)
