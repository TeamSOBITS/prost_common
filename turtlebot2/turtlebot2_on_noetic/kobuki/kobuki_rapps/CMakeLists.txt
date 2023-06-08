cmake_minimum_required(VERSION 3.0.2)

project(kobuki_rapps)

find_package(catkin REQUIRED)

catkin_package()

install(DIRECTORY rapps DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
