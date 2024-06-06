#!/bin/bash

# Change directory to the server
cd server

# Start the Flask server in the background. Log the errors.
flask run 

# Change directory to the client.
cd ../client

# Start the Vue.js frontend in development mode
npm run dev 


