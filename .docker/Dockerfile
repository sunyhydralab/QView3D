### This container has two modes: production mode and development mode. 
## In development mode, the contents contained in the current directory will be assumed to 
# be the latest version of the software and executed.
## In production mode, the main branch will be used by default. [This can be changed temporarily by adding a branch keyword afterwards TODO ADD]

# Using Ubuntu 24.04 to match the production server
FROM ubuntu:24.04

# Install dependencies that will be used
RUN apt update -y && apt upgrade -y && apt install -y git nodejs npm wget

# Set the working directory
WORKDIR /qview3d

# Copy the repository's files into the container [All branches are added]
RUN git clone https://github.com/sunyhydralab/QView3D.git /qview3d

# By default, the development branch is used to ensure the most up to date requirements.txt file is included
# [This will be automatically updated when in development mode]
RUN git checkout development

### uv is a very fast package manager; however, it's only 1 year old at the time of writing
### It can be easily replaced with pip if need be with the code below

# Runs the installer for getting uv, a much faster Python package manager
RUN wget -qO- https://astral.sh/uv/install.sh | sh

# uv installs itself to this directory, so we must add it to the PATH to use it
ENV PATH="/root/.local/bin/:$PATH"

# Create the venv
RUN uv venv .uv-venv

# Activate the venv
ENV PATH="/qview3d/.uv-venv/bin:$PATH"

# Install the python dependencies
RUN uv pip install -r requirements.txt

### In the event that uv breaks, uncomment the below code to use pip instead ###
# # Install pip and venv
# RUN apt install -y python3-pip python3-venv

# # Build the python virtual environment
# RUN python3 -m venv .pip-venv

# # Activate the venv
# ENV PATH="/qview3d/.pip-venv/bin:$PATH"

# # Install Python dependencies
# RUN pip install -r requirements.txt

# Update npm to the latest version that's compatible with the version of node offered 
# (Ubuntu 24.04 comes with NodeJS 18.x.x, npm 10.x.x is supported by this runtime)
RUN npm i -g npm@^10.x.x

# Install NodeJS dependencies
RUN cd client && npm install

# Create the .docker directory
RUN mkdir /qview3d/.docker/

# Copy the existing start_docker.sh file [TODO: TEMP]
COPY ./.docker/start_docker.sh /qview3d/.docker/

# Make this file executable
RUN chmod +x /qview3d/.docker/start_docker.sh

# The start_docker script will start the project
CMD ["/qview3d/.docker/start_docker.sh"]

# ENTRYPOINT exec /qview3d/.docker/start_docker.sh