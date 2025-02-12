#!/bin/bash

# Starts the docker image and gives it access to the current working directory
# (TODO: Ensure the current working directory is the root of the project!)

# Builds the docker image
# -t qview3d/ubuntu:24.04 \         ### Sets the tag/nickname of the Docker container
# -f .docker/Dockerfile .           ### Specifies the location of the Dockerfile (The Dockerfile is used to build the container)
sudo docker build \
    -t "qview3d/ubuntu:24.04" \
    -f ".docker/Dockerfile" .

# Run the docker container
# -v "$(pwd)":/usr/src/qview3d/ \   ### Gives the Docker container access to the current directory
# -u "$(id -u)" \                   ### Sets the user of the Docker container to the current user
# -p 127.0.0.1:8002:8002 \          ### Binds the address:port on the host to the :port on the client address:port:port
# -p 127.0.0.1:8001:8001 \          
# -p 127.0.0.1:8000:8000 \
# -v /dev/bus/usb:/dev/bus/usb \    ### Gives the container access to every usb device on the host (To connect to the printers)
# --privileged \                    ### Allows the Docker container to easily access the 3D printers
# -it qview3d/ubuntu:24.04          ### Runs the container in interactive mode so that we can use it in a terminal
sudo docker run \
    -v "$(pwd)":/usr/src/qview3d/ \
    -u "$(id -u)" \
    -p 127.0.0.1:8002:8002 \
    -p 127.0.0.1:8001:8001 \
    -p 127.0.0.1:8000:8000 \
    -v /dev/bus/usb:/dev/bus/usb \
    --privileged \
    -it qview3d/ubuntu:24.04