#!/bin/sh

cd ~/colcon_ws/src

echo "Install TurtleBot packages"
#sudo apt install ros-melodic-turtlebot ros-melodic-turtlebot-apps ros-melodic-turtlebot-interactions ros-melodic-turtlebot-simulator ros-melodic-kobuki-ftdi ros-melodic-ar-track-alvar-msgs

sudo apt install ros-jazzy-usb-cam -y

sudo apt install ros-jazzy-rosbridge-server -y

sudo apt install ros-jazzy-web-video-server -y

sudo apt install ros-jazzy-depthimage-to-laserscan -y

sudo apt install python3-zbar -y

sudo apt install python3-matplotlib -y

wget -O /tmp/google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install /tmp/google-chrome-stable_current_amd64.deb -y

echo "Build visp_auto_tracker from source (no apt package for Jazzy)"

sudo apt install libvisp-dev libdmtx-dev -y

if [ ! -d vision_visp ]; then
  git clone -b jazzy https://github.com/lagadic/vision_visp.git
fi

echo "Install Finished"

