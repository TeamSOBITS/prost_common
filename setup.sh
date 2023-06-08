#!/bin/sh


echo "╔══╣ Install: Prost Common (STARTING) ╠══╗"
sudo apt update
# sudo apt upgrade -y

sudo apt-get update

sudo apt-get install -y \
    software-properties-common

sudo add-apt-repository -y \
    ppa:ubuntuhandbook1/ppa

sudo apt install -y \
    libusb-dev \
    libftdi-dev \
    libavahi-client-dev \
    pyqt5-dev-tools
    mongodb \
    mongodb-dev \
    python3-pip \
    git \
    libqt4-dev \
    libavahi-common-dev


python3 -m pip install -U \
    pip

python3 -m pip install \
    pymongo \
    pycryptodome \
    console \
    utils \
    ansible

sudo apt -y install ros-${ROS_DISTRO}-cmake-modules \
    ros-${ROS_DISTRO}-kobuki-msgs \
    ros-${ROS_DISTRO}-image-geometry \
    ros-${ROS_DISTRO}-common-msgs \
    ros-${ROS_DISTRO}-depthimage-to-laserscan \
    ros-${ROS_DISTRO}-sensor-msgs \
    ros-${ROS_DISTRO}-ecl-* \
    ros-${ROS_DISTRO}-geometry* \
    ros-${ROS_DISTRO}-linux-peripheral-interfaces \
    ros-${ROS_DISTRO}-navigation \
    ros-${ROS_DISTRO}-nav-msgs \
    ros-${ROS_DISTRO}-openslam-gmapping \
    ros-${ROS_DISTRO}-robot-pose-ekf\
    ros-${ROS_DISTRO}-rospy-message-converter \
    ros-${ROS_DISTRO}-gmapping \
    ros-${ROS_DISTRO}-std-msgs \
    ros-${ROS_DISTRO}-unique-identifier \
    ros-${ROS_DISTRO}-warehouse-ros \
    ros-${ROS_DISTRO}-capabilities \
    ros-${ROS_DISTRO}-urdf \
    ros-${ROS_DISTRO}-roslint \
    ros-${ROS_DISTRO}-rqt-robot-dashboard \
    ros-${ROS_DISTRO}-kdl-conversions \
    ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-gazebo-ros \
    ros-${ROS_DISTRO}-gazebo-plugins \
    ros-${ROS_DISTRO}-resource-retriever \
    ros-${ROS_DISTRO}-qt-* \
    ros-${ROS_DISTRO}-interactive-markers \
    ros-${ROS_DISTRO}-depth-image-proc \
    ros-${ROS_DISTRO}-joy \
    ros-${ROS_DISTRO}-xacro \
    ros-${ROS_DISTRO}-rqt* \
    ros-${ROS_DISTRO}-robot-state-publisher \
    ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-openni2-* \
    ros-${ROS_DISTRO}-usb-cam \
    ros-${ROS_DISTRO}-rosbridge-server  \
    ros-${ROS_DISTRO}-web-video-server  \
    ros-${ROS_DISTRO}-visp-auto-tracker
    # ros-${ROS_DISTRO}-pcl-* \

sudo apt install python3-zbar -y
sudo pip3 install pyzbar

sudo apt install google-chrome-stable -y


echo 'export TURTLEBOT_GAZEBO_WORLD_FILE="$HOME/catkin_ws/src/prost_common/turtlebot2/turtlebot2_on_noetic/turtlebot_simulator/turtlebot_gazebo/worlds/competition.world"' >> ~/.bashrc
echo 'export TURTLEBOT_STAGE_MAP_FILE="$HOME/catkin_ws/src/prost_common/prostbot_gazebo/maps/playground.yaml"' >> ~/.bashrc
echo 'export TURTLEBOT_STAGE_WORLD_FILE="$HOME/catkin_ws/src/prost_common/prostbot_gazebo/worlds/empty.world"' >> ~/.bashrc
echo 'export TURTLEBOT_3D_SENSOR="asus_xtion_pro"' >> ~/.bashrc

source ~/.bashrc
cd ~/catkin_ws
catkin_make

echo "╚══╣ Install: Prost Common (FINISHED) ╠══╝"
