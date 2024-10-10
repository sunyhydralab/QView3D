#!/bin/bash

setup_python() {
    pip install -r requirements.txt 
}

setup_flask() {
    rm -rf migrations
    
    flask db init 

    flask db migrate 

    flask db upgrade    
}

setup_client() {
    npm install --save-dev
}

build_client() {
    npm run build-only
}

echo "Installing dependencies for QView3D"

setup_python

cd server

setup_flask

cd ../client

setup_client

build_client

echo "Finished installed dependencies!"