#!/bin/bash

# Add the execute permission to the script.
chmod +x install.sh

# Install the required packages.
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash

# Source your bash profile to load changes made by nvm
source ~/.bashrc

# Install Node.js.
nvm install node

# Install Python dependencies. Requirements was created with pipreqs.
pip install -r requirements.txt 

# Change directory to the server.
cd server

# Initialize the database. 
flask db init 

# Generate a migration script. 
flask db migrate 

# Apply the migration. 
flask db upgrade 

# Change directory to the client.
cd ../client

# Install Node.js dependencies.
npm install

# Install npm-run-all as a dev dependency
npm install --save-dev npm-run-all