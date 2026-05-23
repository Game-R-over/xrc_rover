###########################################
# Xplore Recruitment image Build Docker
###########################################
FROM ghcr.io/epflxplore/docker_commons:humble-desktop

ARG DEBIAN_FRONTEND=noninteractive

RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" \
    > /etc/apt/sources.list.d/ros2.list

# Install Rover packages
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y curl
RUN apt-get install -y ros-humble-rosbridge-suite

# Install g++ 12 (for std::expected)
RUN apt-get install -y \
	g++-12 \

	ros-humble-navigation2 \
	ros-humble-nav2-bringup

RUN usermod -a -G dialout xplore
#RUN pip install opencv-python torch torchvision ultralytics

# Add USB rules
RUN echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666"' | sudo tee /etc/udev/rules.d/80-movidius.rules
RUN /etc/init.d/udev restart

# Clean up
RUN rm -rf /var/lib/apt/lists/*

# Remove all the confidential Xplore source code from the image
RUN rm -rf /home/$USERNAME/dev_ws/src/*

USER $USERNAME

# Set a diretory to store the project
WORKDIR /home/$USERNAME/dev_ws/src
COPY . .

# Set a directory to build the project
WORKDIR /home/$USERNAME/dev_ws
