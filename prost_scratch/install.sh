#!/bin/sh

cd ~/catkin_ws/src

echo "Install TurtleBot packages"
#sudo apt install ros-melodic-turtlebot ros-melodic-turtlebot-apps ros-melodic-turtlebot-interactions ros-melodic-turtlebot-simulator ros-melodic-kobuki-ftdi ros-melodic-ar-track-alvar-msgs

sudo apt install ros-melodic-usb-cam -y

sudo apt install ros-melodic-visp-auto-tracker -y

#sudo pip install zbar

sudo apt install ros-melodic-rosbridge-server -y

sudo apt install ros-melodic-web-video-server -y

sudo apt install ros-melodic-depthimage-to-laserscan -y

sudo apt install python-zbar

sudo apt install google-chrome-stable -y

echo "Install Finished"

