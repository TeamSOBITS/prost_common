#!/usr/bin/env python3

from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['world_canvas_server'],
    package_dir={'': 'src'},
    requires=['roslib', 'rospy', 'world_canvas_msgs', 'world_canvas_libs']
)

setup(**d)
