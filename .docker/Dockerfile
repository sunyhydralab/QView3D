### This file defines how the Docker image will be built

# Using Ubuntu 24.04 to match the production server
FROM ubuntu:24.04

# Install runtime dependencies
RUN apt update -y && apt upgrade -y && apt install --no-install-recommends --no-install-suggests python3-pip python3-venv nodejs npm -y

# Update NPM to the latest version that works with the version of NodeJS offered in Ubuntu
RUN npm install -g npm@^10.x.x

# The location of the project files
WORKDIR /usr/src/qview3d

# The location of the project in the Docker image
ENV DOCKER_APP_PATH=/usr/src/qview3d

# The location of the Docker scripts that will be used while in the Docker container
ENV PATH=$DOCKER_APP_PATH/.docker:$PATH

# Make the docker scripts executable
CMD ["/bin/sh", "-c", "chmod +x .docker/* && exec /bin/bash"]