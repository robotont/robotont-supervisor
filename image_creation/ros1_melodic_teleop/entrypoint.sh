#!/bin/bash

#start SSH server
service ssh start

#source ROS setup files
source /opt/ros/$ROS_DISTRO/setup.bash
source /root/ros_ws/devel/setup.bash

#rosrun teleop_twist_keyboard teleop_twist_keyboard.py

#execute the provided command
exec "$@"