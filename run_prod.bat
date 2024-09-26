@echo off

echo Starting the production server...
cd server
gunicorn --worker-class eventlet -w 1 app:app