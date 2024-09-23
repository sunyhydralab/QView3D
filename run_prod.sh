#!/bin/bash

# Function to run the production server
run_prod() {
    echo "Starting the production server..."
    cd server
    #uvicorn asgi:flask_app --host 0.0.0.0 --port 8000
    #waitress-serve --call --port=8000 'app:create_app'
    # restful webservice 
    #hypercorn 'app:create_app' --bind 0.0.0.0:8000 --workers 4
    gunicorn --worker-class eventlet -w 1 app:app
}

# Run the production server
run_prod