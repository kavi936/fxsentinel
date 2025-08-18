#!/bin/bash

# FXSentinel Flask Server Startup Script
# This script ensures clean startup by checking for port conflicts

PORT=${1:-5001}
echo "🚀 Starting FXSentinel Flask server on port $PORT..."

# Check if port is already in use
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "⚠️  Port $PORT is already in use. Checking for processes..."
    
    # Get PIDs using the port
    PIDS=$(lsof -i :$PORT | awk 'NR>1 {print $2}' | sort -u)
    
    if [ ! -z "$PIDS" ]; then
        echo "🔍 Found processes using port $PORT: $PIDS"
        echo "🛑 Killing existing processes..."
        echo $PIDS | xargs kill -9
        sleep 2
    fi
fi

# Double-check port is free
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "❌ Port $PORT is still in use. Please check manually."
    exit 1
else
    echo "✅ Port $PORT is free. Starting Flask server..."
fi

# Start the Flask server
echo "🔧 Starting Flask server with debug mode off..."
python3 app.py
