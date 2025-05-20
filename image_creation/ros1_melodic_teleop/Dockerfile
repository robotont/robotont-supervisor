#Ubuntu 18.04 base image
FROM ubuntu:18.04

#ARG to define build-time variables
ARG LANG=en_US.UTF-8
ARG LC_ALL=en_US.UTF-8
ARG ROS_DISTRO=melodic
ARG DEBIAN_FRONTEND=noninteractive
ARG ROOT_PASSWORD=defaultpassword

#set ENV variables based on ARG
ENV LANG=$LANG
ENV LC_ALL=$LC_ALL
ENV ROS_DISTRO=$ROS_DISTRO
ENV DEBIAN_FRONTEND=$DEBIAN_FRONTEND

#required packages and dependencies
RUN apt update && apt install -y \
    locales \
    curl \
    gnupg \
    software-properties-common \
    git \
    openssh-server \
    nano \
    vim \
    && locale-gen en_US.UTF-8 \
    && update-locale LC_ALL=$LC_ALL LANG=$LANG

#universe repository
RUN add-apt-repository universe

#add ROS GPG key and repository
RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
RUN curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add -

#update system and install ROS Melodic desktop and required packages
RUN apt update && apt upgrade -y && \
    apt install -y ros-$ROS_DISTRO-desktop \
    python-rosdep \
    python-rosinstall \
    python-rosinstall-generator \
    python-wstool \
    build-essential

#initialize rosdep
RUN rosdep init && rosdep update

#set up ROS workspace
RUN mkdir -p /root/ros_ws/src

WORKDIR /root/ros_ws/src

#clone the branch of robotont_driver repository
RUN git clone --branch melodic-devel https://github.com/robotont/robotont_driver.git

#clone the branch of robotont_msgs repository
RUN git clone --branch melodic-devel https://github.com/robotont/robotont_msgs.git

#clone ar steering demo
#RUN git clone --branch main https://github.com/robotont-demos/demo_ar_steering.git

#install teleop demo
RUN apt-get install ros-melodic-teleop-twist-keyboard

# install dependencies using rosdep
WORKDIR /root/ros_ws
RUN /bin/bash -c "\
    source /opt/ros/$ROS_DISTRO/setup.bash && \
    rosdep update --include-eol-distros && \
    rosdep install --from-paths src \
                    --rosdistro=$ROS_DISTRO \
                    --ignore-src -y"

RUN apt-get update && apt-get install -y ros-melodic-serial

#build the workspace
RUN /bin/bash -c "\
    source /opt/ros/$ROS_DISTRO/setup.bash && \
    catkin_make -j1 -l1"

#source ROS setup files for runtime
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /root/.bashrc && \
    echo "source /root/ros_ws/devel/setup.bash" >> /root/.bashrc

#setup SSH
RUN mkdir /var/run/sshd \
    && echo "root:$ROOT_PASSWORD" | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

#allow container to use pseudo-terminal for SSH
RUN echo "export TERM=xterm" >> /root/.bashrc

#copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

#default command
ENTRYPOINT ["/entrypoint.sh"]
