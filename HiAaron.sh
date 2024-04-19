#!/bin/bash
# Script name: HiAaronIly.sh
# Author: Lars, Jack, Olamide
# Date: March 7, 2024
# Description: This script installs the dependencies and runs the code. 

# may need to run chmod 755 HiAaron.sh

# install tmux  
sudo apt update
sudo apt install tmux
sudo apt-get install tmux

# start new session 
tmux new-session -d -s fila_forge
tmux split-window -h


# create .env, install dependencies 
tmux send-keys -t fila_forge:0.0 '
 cd server && 
  echo "FLASK_ENV=development" > .env &&
  echo "FLASK_APP=app.py" >> .env &&
  echo "FLASK_RUN_PORT=8000" >> .env &&
  echo "SQLALCHEMY_DATABASE_URI=hvamc.db" >> .env &&
  echo "BASE_URL=http://localhost:8000" >> .env && 
  pip3 freeze > requirements. txt && 
  pip3 install -r requirements.txt && 
  sudo apt install python3-flask &&
  pip3 install flask_cors &&
  pip3 install flask_sqlalchemy &&
  pip3 install serial && 
  sudo apt-get install python-pip &&
  pip3 install tzlocal &&
  pip3 install dotenv &&
  pip3 install flask_socketio && 
  flask db init &&
  flask db migrate &&# install tmux  
sudo apt update
sudo apt install tmux
sudo apt-get install tmux
  flask db upgrade &&
' C-m
# run flask 
tmux send-keys -t fila_forge:0.0 'flask run' C-m

# split window 
tmux split-window -v

# install dependencies & run frontend 
tmux send-keys -t fila_forge:0.1 '
  cd client && 
  echo "VITE_API_ROOT=http://localhost:8000" > .env &&
  sudo apt install npm &&
  npm i &&
  npm i vite@latest &&
  npm run dev 
' Enter

echo "Script completed"
