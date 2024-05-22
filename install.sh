#!/bin/bash

# Change directory to the server 
cd server

# Install Python dependencies. Requirements was created with pipreqs.
pip install -r requirements.txt >> install.log 2>&1

# Initialize the database. Log the errors.
flask db init >> install.log 2>&1

# Generate a migration script. Log the errors.
flask db migrate >> install.log 2>&1

# Apply the migration. Log the errors. 
flask db upgrade >> install.log 2>&1

# Change directory to the client.
cd ../client

# Install Node.js dependencies. Log the errors.
npm install >> install.log 2>&1


# Script to install all the python requirements. 
# Install and start the flask database.
# Install node.