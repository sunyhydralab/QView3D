@echo off

echo Building the client...
cd client
npm run build-only

cd ..

echo Starting the production server...
cd server
gunicorn --worker-class eventlet -w 1 app:app