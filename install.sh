#!/bin/bash

# Change directory to the server 
cd server

# Install Python dependencies. Requirements was created with pipreqs.
pip install -r requirements.txt 

# Initialize the database. Log the errors.
flask db init 

# Generate a migration script. Log the errors.
flask db migrate 

# Apply the migration. Log the errors. 
flask db upgrade 

# Change directory to the client.
cd ../client

# Install Node.js dependencies. Log the errors.
npm install 


# Script to install all the python requirements. 
# Install and start the flask database.
# Install node.