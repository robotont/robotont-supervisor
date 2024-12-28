#Ubuntu 24.04 (Noble Numbat) base image
FROM ubuntu:24.04

#ARG to define build-time variables
ARG LANG=en_US.UTF-8
ARG LC_ALL=en_US.UTF-8
ARG ROS_DISTRO=jazzy
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
    build-essential \
    python3-pip \
    python3-venv \
    git \
    openssh-server \
    nano \
    vim \
    && locale-gen en_US.UTF-8 \
    && update-locale LC_ALL=$LC_ALL LANG=$LANG

#universe repository
RUN add-apt-repository universe

#add ROS 2 GPG key and repository
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null

#dev tools
RUN apt update && apt install -y ros-dev-tools

#update system and install ROS 2 Jazzy desktop and required packages
RUN apt update && apt upgrade -y && \
    apt install -y ros-$ROS_DISTRO-desktop \
    ros-$ROS_DISTRO-io-context \
    ros-$ROS_DISTRO-serial-driver \
    ros-$ROS_DISTRO-asio-cmake-module \
    python3-rosdep

#initialize rosdep
RUN rosdep init && rosdep update

#set up ROS workspace
RUN mkdir -p /root/ros2_ws/src

WORKDIR /root/ros2_ws/src

#clone the jazzy-devel branch of robotont_driver repository
RUN git clone --branch jazzy-devel https://github.com/robotont/robotont_driver.git

#clone the jazzy-devel branch of robotont_msgs repository
RUN git clone --branch jazzy-devel https://github.com/robotont/robotont_msgs.git

#install dependencies using rosdep
WORKDIR /root/ros2_ws
RUN rosdep install --from-paths src -y --ignore-src

#build the workspace
RUN /bin/bash -c "source /opt/ros/$ROS_DISTRO/setup.bash && colcon build"

#source ROS setup files for runtime
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /root/.bashrc && \
    echo "source /root/ros2_ws/install/local_setup.bash" >> /root/.bashrc

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
