#!/bin/bash

# Load nvm
source ~/.nvm/nvm.sh

# Add the execute permission to the script.
chmod +x run.sh

# Change directory to the server
cd server

# Start the Flask server in the background. Log the errors.
flask run &

# Change directory to the client.
cd ../client

# Start the Vue.js frontend in development mode
npm run dev

