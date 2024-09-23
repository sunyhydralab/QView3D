#!/bin/bash

# Function to run the production server
run_prod() {
    echo "Starting the production server..."
    cd server
    gunicorn --worker-class eventlet -w 1 app:app
}

# Run the production server
run_prod