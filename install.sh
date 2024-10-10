#!/bin/bash

echo "Installing dependencies for QView3D"

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

# Build client so server can host it.
npm run build-only

echo "Finished installed dependencies!"