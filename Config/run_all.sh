#!/bin/bash

# Activate the env.
echo "Environment activating..."
source /home/tzo/anaconda3/bin/activate 301_server
echo "Environment activation success."

# Boot the app service.
cd /home/tzo/301_24/backend
nohup python3 /home/tzo/301_24/backend/app.py 1>/home/tzo/301_24/backend/301_app.log 2>&1 &
echo "App service boot done."

# Boot the server.
cd /home/tzo/301_24/backend
nohup python3 /home/tzo/301_24/backend/server.py 1>/home/tzo/301_24/backend/301_server.log 2>&1 &
echo "Server boot done."

echo "All services boot success."