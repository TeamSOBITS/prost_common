cmake_minimum_required(VERSION 3.0.2)
project(world_canvas_utils)

find_package(catkin REQUIRED COMPONENTS
  rospy
  roslib
  world_canvas_msgs
)

catkin_package()
catkin_python_setup()
