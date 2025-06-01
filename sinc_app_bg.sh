#!/bin/bash

echo "Starting sincerity app script..." >> ~/btf2/sinc_app.log

# Activate the correct virtual environment
source ~/btf2/venv_btf/bin/activate
echo "Activated venv_btf" >> ~/btf2/sinc_app.log

# Navigate to the project directory
cd ~/btf2 || exit 1
echo "Changed directory to $(pwd)" >> ~/btf2/sinc_app.log

# Run the Flask app in the background
nohup python app.py > flask.log 2>&1 &
echo "Flask app started with PID $!" >> ~/btf2/sinc_app.log
