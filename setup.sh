#!/bin/sh

sudo apt update
sudo apt upgrade -y
sudo apt install ros-melodic-kobuki-* -y
sudo apt install ros-melodic-ecl-streams -y
sudo apt install ros-melodic-joy -y
sudo apt install ros-melodic-joint-state-publisher* -y
sudo apt install ros-melodic-depthimage-to-laserscan -y

sudo apt install ros-melodic-usb-cam -y
sudo apt install ros-melodic-rosbridge-server -y

sudo apt install ros-melodic-web-video-server -y

sudo apt install ros-melodic-depthimage-to-laserscan -y

sudo apt install python-zbar -y

sudo apt install google-chrome-stable -y

sudo apt install ros-melodic-visp-auto-tracker -y
sudo cp ~/catkin_ws/src/prost_common/libgazebo_ros_kobuki.so /opt/ros/melodic/lib

