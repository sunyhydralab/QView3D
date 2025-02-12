#!/bin/bash

# Starts the docker image and gives it access to the current working directory
# (Ensure the current working directory is the root of the project!)

# Builds the docker image
sudo docker build \
    -t qview3d/ubuntu:24.04 \
    -f .docker/Dockerfile .

# Run the docker container
sudo docker run \
    -v "$(pwd)":/usr/src/qview3d/ \
    -u $(id -u) \
    -p 127.0.0.1:8001:8001 \
    -p 127.0.0.1:8000:8000 \
    -it qview3d/ubuntu:24.04