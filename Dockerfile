# Using Ubuntu 24.04 to match the production server
FROM ubuntu:24.04

# Install dependencies that will be used
RUN apt update -y && apt upgrade -y && apt install git nodejs npm python3-pip python3-venv -y

# Update npm to the latest version that's compatible with the version of node offered (Ubuntu 24.04 comes with NodeJS 18.x.x, npm 10.x.x is supported by this runtime)
RUN npm i -g npm@^10.x.x

# Create the project folder
RUN mkdir qview3d

# Copy the repository's files into the container
RUN git clone https://github.com/sunyhydralab/QView3D.git /qview3d

# Use the current working directory instead
# COPY . /qview3d

# Set the working directory
WORKDIR /qview3d

# Change to the docker branch (TODO: Temporary)
RUN git checkout docker-setup

# Build the python virtual environment
RUN python3 -m venv .python-venv

# Activate the venv
ENV PATH=".python-venv/bin:$PATH"

# Install Python dependencies
RUN pip install -r requirements.txt

# Install NodeJS dependencies
RUN cd client && npm install