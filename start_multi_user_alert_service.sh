#!/bin/bash

# FXSentinel Multi-User Background Alert Service Startup Script

echo "🚀 Starting FXSentinel Multi-User Background Alert Service..."
echo "============================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if the Flask app is running
if ! curl -s http://localhost:5001/api/health > /dev/null; then
    echo "❌ Flask app is not running on port 5001"
    echo "   Please start the Flask app first:"
    echo "   cd backend && python3 app.py"
    exit 1
fi

echo "✅ Flask app is running"

# Start the multi-user background alert service
echo "📱 Starting multi-user background alert service..."
echo "   This will monitor for news and send alerts to ALL connected users"
echo "   Check interval: 5 minutes"
echo "   Press Ctrl+C to stop the service"
echo ""

# Run the multi-user background service
python3 background_alert_service_multi_user.py
