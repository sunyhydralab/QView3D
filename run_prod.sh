#!/bin/bash

# Function to run the production server
run_prod() {
    echo "Starting the production server..."
    cd server
    waitress-serve --call 'app:create_app'
}

# Run the production server
run_prod