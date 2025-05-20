# robotont-supervisor
## Prerequisites:
    * Connection to Robotont mainboard via serial
    * Connection to internet
    * Connection to local network if SSH is used.
## Changing SSH ports
Modify the SSH port on the host to allow connection to container using default SSH port 22. You may skip this step if SSH connection into container is not needed.
    * **If you are connected via SSH, you will need to reconnect after changing the port and restarting SSH server.**
    * Open following file with a text editor:
        ```
        sudo nano /etc/ssh/sshd_config
        ```
    * Find and modify the port line from `#Port 22` to `Port 22222`. This frees up port 22 on host to be used by container ssh server.
    * You may need to modify firewall settings to allow SSH connections to host machine using port 22222.
    * Restart the SSH server.
        ```
        sudo systemctl restart ssh.service
        ```
## Building images
Navigate to each directory where Dockerfile is present and build the images.
    ```
    docker build -t <name> .
    ```
## Starting supervisor from scratch:
Before staring the superivisor, make sure that port 5000 is open, otherwise it is impossible to access the web interface.
1) Install the [Docker engine using the apt repository](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository).

2) Allow non-privileged users (including supervisor) to run Docker commands. [Linux post-installation steps for Docker Engine](https://docs.docker.com/engine/install/linux-postinstall/)

3) Download robotont-supervisor repository on the robot.
    ```
    git clone https://github.com/robotont/robotont-supervisor.git
    ```
4) Robotont service should be disabled on host to avoid conflicts.
    ```
    sudo systemctl disable robotont.service
    ```
5) Create a Python virtual environment for the supervisor.
    ```
    python3 -m venv supervisor-venv
    ```
6) Activate the created virtual environment.
    ```
    source supervisor-venv/bin/activate
    ```
7) Navigate into previosly downloaded repository and install the requirements from "requirements.txt".
    ```
    pip install -r requirements.txt
    ```
8) Run supervisor.py (from virtual environment):
    ```
    python3 supervisor.py
    ```
    Optionally, you may use .env files for setting variables. The default values also work.
    


## Troubleshooting:
* If there are issues with paths, absolute paths in .env file could be a fix.
* Serial device names can change.
    #### Useful commands
    * sourcing ROS
        ```
        source /opt/ros/$ROS_DISTRO/setup.bash
        source /root/ros2_ws/install/local_setup.bash
        ```
    * odometry test
        ```
        ros2 topic echo /odom
        ```
    * open container bash
        ```
        docker exec -it <container-name> bash
        ```
