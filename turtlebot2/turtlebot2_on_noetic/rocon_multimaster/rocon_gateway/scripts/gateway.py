#!/usr/bin/env python3
#
# License: BSD
#   https://raw.github.com/robotics-in-concert/rocon_multimaster/license/LICENSE
#

##############################################################################
# Imports
##############################################################################

import rospy
from rocon_gateway import GatewayNode

##############################################################################
# Launch point
##############################################################################

if __name__ == '__main__':

    rospy.init_node('gateway')
    gateway = GatewayNode()
    gateway.spin()
