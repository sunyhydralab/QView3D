#!/bin/bash
mode=$1
# Starts the docker image and gives it access to the current working directory 
# (Ensure the current working directory is the root of the project!)
# TODO add a check for that

# Ensure the correct mode is set
if [ "$mode" != "dev" ] && [ "$mode" != "prod" ]; then
    echo -e "There are only two supported modes: dev and prod.\n $mode is not valid"
    exit 1
fi

# Builds the docker image
sudo docker build \
    -t qview3d/ubuntu:24.04 \
    -f .docker/Dockerfile \
    .

# Run the docker container
sudo docker run \
    -e MODE=$mode \
    -e UPDATE=yes \
    -v "$(pwd)":/qview3d/working_dir \
    -it qview3d/ubuntu:24.04 /bin/bash