#!/bin/bash

echo "=========================================="
echo "Starting Co-op Survival RTS (Full Stack)"
echo "=========================================="


# Find the PID of the python3 -m server.main process
PID=$(ps -fA | grep -E "python3 server/main.py|python3 -m server.main" | grep -v grep | awk '{print $2}')

# Check if PID was found
if [ -n "$PID" ]; then
    echo "Killing process with PID: $PID"
    kill $PID
else
    echo "No matching process found."
fi

# Initialize conda for bash
eval "$(conda shell.bash hook)"
conda activate your_env_name  # <<< Replace with your environment name

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis server..."
    redis-server --daemonize yes --port 6379
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis started successfully"
    else
        echo "❌ Failed to start Redis, using in-memory storage"
    fi
else
    echo "✅ Redis is already running"
fi

cd "$(dirname "$0")"
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo ""
echo "Starting game server..."
rm -f server.log
python3 -m server.main 2>&1 | tee server_output.log
