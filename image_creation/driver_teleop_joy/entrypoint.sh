#!/bin/bash

#start SSH server
service ssh start

#source ROS setup files
source /opt/ros/$ROS_DISTRO/setup.bash
source /root/ros2_ws/install/local_setup.bash


#execute the provided command
exec "$@"