#!/bin/sh

sudo apt update
sudo apt upgrade -y
sudo apt install ros-noetic-kobuki-* -y
sudo apt install ros-noetic-ecl-streams -y
sudo apt install ros-noetic-joy -y
sudo apt install ros-noetic-joint-state-publisher* -y
sudo apt install ros-noetic-depthimage-to-laserscan -y

sudo apt install ros-noetic-usb-cam -y
sudo apt install ros-noetic-rosbridge-server -y

sudo apt install ros-noetic-web-video-server -y

sudo apt install ros-noetic-depthimage-to-laserscan -y

sudo apt install python-zbar -y

sudo apt install google-chrome-stable -y

sudo apt install ros-noetic-visp-auto-tracker -y
sudo cp ~/catkin_ws/src/prost_common/libgazebo_ros_kobuki.so /opt/ros/noetic/lib

#!/bin/bash


# echo "╔══╣ Install: Sobit Common (STARTING) ╠══╗"


# sudo apt-get update
# sudo apt-get install -y \
#     ros-${ROS_DISTRO}-kobuki-* \
#     ros-${ROS_DISTRO}-ecl-streams \
#     ros-${ROS_DISTRO}-joy \
#     ros-${ROS_DISTRO}-joint-state-publisher*

sudo cp ~/catkin_ws/src/sobit_common/turtlebot2/turtlebot_simulator/turtlebot_gazebo/libgazebo_ros_kobuki.so /opt/ros/noetic/lib

# # 関係ない
# sudo apt-get install -y \
#     ros-${ROS_DISTRO}-pcl-* \
#     ros-${ROS_DISTRO}-openni2-*


# echo "╚══╣ Install: Sobit Common (FINISHED) ╠══╝"
