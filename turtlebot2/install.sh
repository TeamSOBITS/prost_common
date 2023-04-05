#!/bin/bash
# Reference: https://github.com/gaunthan/Turtlebot2-On-Melodic/blob/master/install_all.sh
# Reference: https://github.com/yujinrobot/kobuki_desktop/issues/53

echo "╔══╣ Install: Turtlebot2 for ROS Noetic (STARTING) ╠══╗"

# Install dependencies
sudo apt-get update

sudo apt-get install -y \
    software-properties-common

sudo add-apt-repository -y \
    ppa:ubuntuhandbook1/ppa

sudo apt install -y \
    git \
    libqt4-dev \
    pyqt5-dev-tools \
    libavahi-client-dev \
    libavahi-common-dev \
    libusb-dev \
    libftdi-dev \
    mongodb \
    mongodb-dev \
    python3-pip


python3 -m pip install -U \
    pip

python3 -m pip install \
    pymongo \
    pycryptodome \
    console \
    utils \
    ansible


# Download repositories
# - Turtlebot-related
git clone https://github.com/TeamSOBITS/turtlebot.git
git clone https://github.com/TeamSOBITS/turtlebot_apps.git
git clone https://github.com/TeamSOBITS/turtlebot_interactions.git
git clone https://github.com/TeamSOBITS/turtlebot_msgs.git
git clone https://github.com/TeamSOBITS/turtlebot_simulator.git

# - Kobuki-related
git clone https://github.com/TeamSOBITS/kobuki.git
git clone https://github.com/TeamSOBITS/kobuki_desktop.git
git clone https://github.com/yujinrobot/kobuki_core
git clone https://github.com/TeamSOBITS/kobuki_msgs.git

# - Others
git clone https://github.com/TeamSOBITS/yocs_msgs
git clone https://github.com/TeamSOBITS/yujin_ocs.git

git clone https://github.com/TeamSOBITS/ar_track_alvar

git clone https://github.com/TeamSOBITS/capabilities
git clone https://github.com/osrf/std_capabilities

git clone https://github.com/TeamSOBITS/stdr_simulator

git clone https://github.com/GT-RAIL/robot_pose_publisher

# git clone -b noetic-devel https://github.com/ros-planning/warehouse_ros_mongo
# git clone https://github.com/ros-planning/warehouse_ros

git clone https://github.com/TeamSOBITS/rocon_app_platform
git clone https://github.com/TeamSOBITS/rocon_msgs
git clone https://github.com/TeamSOBITS/rocon_multimaster
git clone https://github.com/TeamSOBITS/rocon_tools

git clone https://github.com/TeamSOBITS/world_canvas
git clone https://github.com/TeamSOBITS/world_canvas_libs
git clone https://github.com/TeamSOBITS/world_canvas_msgs

git clone https://github.com/TeamSOBITS/zeroconf_avahi_suite
git clone https://github.com/TeamSOBITS/zeroconf_msgs

# Install ROS dependencies
sudo apt-get install -y \
    ros-${ROS_DISTRO}-common-msgs \
    ros-${ROS_DISTRO}-depthimage-to-laserscan \
    ros-${ROS_DISTRO}-sensor-msgs \
    ros-${ROS_DISTRO}-ecl-* \
    ros-${ROS_DISTRO}-geometry2 \
    ros-${ROS_DISTRO}-geometry-msgs \
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
    ros-${ROS_DISTRO}-pcl-* \
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
    ros-${ROS_DISTRO}-openni2-*


# Export variables
echo 'export TURTLEBOT_GAZEBO_WORLD_FILE="$HOME/catkin_ws/src/turtlebot2/turtlebot_simulator/turtlebot_gazebo/worlds/playground.world"' >> ~/.bashrc
echo 'export TURTLEBOT_STAGE_MAP_FILE="$HOME/catkin_ws/src/turtlebot2/turtlebot_simulator/turtlebot_stage/maps/maze.yaml"' >> ~/.bashrc
echo 'export TURTLEBOT_STAGE_WORLD_FILE="$HOME/catkin_ws/src/turtlebot2/turtlebot_simulator/turtlebot_stage/maps/stage/maze.world"' >> ~/.bashrc
echo 'export TURTLEBOT_3D_SENSOR="asus_xtion_pro"' >> ~/.bashrc


echo "╚══╣ Install: Turtlebot2 for ROS Noetic (FINISHED) ╠══╝"
