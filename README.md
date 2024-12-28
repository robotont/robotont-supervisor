# robotont-supervisor

### Some useful commands
#### build images:
docker build -t <image tag name> .
#### sourcing:
source /opt/ros/$ROS_DISTRO/setup.bash
source /root/ros2_ws/install/local_setup.bash
#### odometry test:
ros2 topic echo /odom
#### open container bash
docker exec -it <name> bash