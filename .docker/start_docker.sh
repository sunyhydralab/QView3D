#!/bin/bash

# This script handles starting the Docker container in development or production mode
# sudo docker run qview3d/ubuntu:24.04 [dev | prod] [yes | no : default true]

which flask

# Update packages if nothing is provided or true
if [ -z "$UPDATE" ] || [ "$UPDATE" = "yes" ]; then
    # uv is currently used, comment below and uncomment pip to switch

    # update python dependencies
    echo "Updating Python dependencies"
    uv pip install -r requirements.txt
    # pip install -r requirements.txt
    echo "Update complete"
    
    # update NPM dependencies
    cd client

    echo "Updating Node dependencies"
    # npm update
    echo "Update complete"

    cd ..
fi

# If dev or prod
if [ "$MODE" = "dev" ]; then
    # Utlize the current users working directory
    # It should be mounted to /qview3d/working_dir
    cd /qview3d/working_dir

    echo "Rebuilding client"
    # client
    cd client
    npx vite build --watch & 
    VITE_SESSION=$!

    echo "Starting server"
    # server
    cd ../server
    flask run &
    FLASK_SESSION=$!
    
    echo $FLASK_SESSION $VITE_SESSION

    echo "Ready to develop!"
    # Wait for one process to terminate
    wait $FLASK_SESSION $VITE_SESSION

    # Kill both processes when one terminates
    kill $FLASK_SESSION $VITE_SESSION
elif [ "$MODE" = "prod" ]; then
    # server
    echo hello
    cd server
    flask run
elif [ "$MODE" = "type_check" ]; then # Type checking
    # client
    cd client
    npx vue-tsc --build --force && npx vite build
fi