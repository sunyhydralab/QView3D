#!/bin/bash

# Change directory to the server
cd server

# Start the Flask server in the background. Log the errors.
flask run >> server.log 2>&1 &

# Change directory to the client.
cd ../client

# Set the NODE_ENV environment variable to production
export NODE_ENV=production

# Start the Vue.js frontend in production mode
npm run start >> server.log 2>&1

# Start the flask server & run the node frontend. 
