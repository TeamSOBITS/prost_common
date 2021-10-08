
#依存を満たす ros-kinetic-librealsense　のインストール方法
#参考リンク https://github.com/IntelRealSense/librealsense/issues/4781

# basic container setup
sudo apt-get update
sudo apt-get upgrade -y
sudo apt install ros-kinetic-librealsense -y
sudo apt install ros-kinetic-turtlebot-* -y
sudo apt install ros-kinetic-kobuki-* -y
sudo apt install ros-kinetic-rosbridge-server -y
sudo apt install ros-kinetic-visp-auto-tracker -y
sudo apt install ros-kinetic-web-video-server -y
sudo apt install ros-kinetic-usb-cam -y



cd ~/catkin_ws

sudo apt-get install -y lsb-release
sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list
sudo apt-get update

# dependencies needed by librealsense. `deb -i` will not resolve these
sudo apt-get install -y binutils cpp cpp-5 dkms fakeroot gcc gcc-5 kmod libasan2 libatomic1 libc-dev-bin libc6-dev libcc1-0 libcilkrts5 libfakeroot libgcc-5-dev libgmp10 libgomp1 libisl15 libitm1 liblsan0 libmpc3 libmpfr4 libmpx0 libquadmath0 libssl-dev libssl-doc libtsan0 libubsan0 libusb-1.0-0 libusb-1.0-0-dev libusb-1.0-doc linux-headers-4.4.0-159 linux-headers-4.4.0-159-generic linux-headers-generic linux-libc-dev make manpages manpages-dev menu patch zlib1g-dev
sudo apt-get install -y libssl-dev libssl-doc libusb-1.0-0 libusb-1.0-0-dev libusb-1.0-doc linux-headers-4.4.0-159 linux-headers-4.4.0-159-generic linux-headers-generic zlib1g-dev

# modify librealsense deb (unpack, replace script, repack)
sudo apt-get download ros-kinetic-librealsense
sudo dpkg-deb -R ros-kinetic-librealsense*.deb ros-rslib/

sudo wget https://gist.githubusercontent.com/dizz/404ef259a15e1410d692792da0c27a47/raw/3769e80a051b5f2ce2a08d4ee6f79c766724f495/postinst
chmod +x postinst
sudo cp postinst ros-rslib/DEBIAN
sudo dpkg-deb -b ./ros-rslib/ ros-kinetic-librealsense_1.12.1-0xenial-20190830_icrlab_amd64.deb

# install container friendly libsense
sudo dpkg -i ros-kinetic-librealsense_1.12.1-0xenial-20190830_icrlab_amd64.deb

# lock from updates
sudo apt-mark hold ros-kinetic-librealsense

sudo apt install ros-kinetic-turtlebot-bringup -y
sudo apt install ros-kinetic-rosbridge-server -y
sudo apt install ros-kinetic-visp-auto-tracker -y
sudo apt install ros-kinetic-web-video-server -y
sudo apt install ros-kinetic-usb-cam -y


sudo apt install python-pip -y
pip install zbar


cd ~/catkin_ws/src
catkin_make

################################################################################

#クラッシュしにくい gazebo　のインストール方法
#参考リンク https://github.com/uzh-rpg/rpg_quadrotor_control/issues/58

sudo sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list'

wget http://packages.osrfoundation.org/gazebo.key -O - | sudo apt-key add -

sudo apt-get update

sudo apt-get install gazebo7 -y

sudo apt autoremove -y

#webcam無効（ホスト依存）
sudo rmmod -f uvcvideo

#使用後はホスト側で以下のコマンドを実行
#sudo modprobe uvcvideo
