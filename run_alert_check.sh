#!/bin/bash

# FXSentinel Alert Check Script
# This script checks for new alerts and sends them to users
# Can be run manually or scheduled with cron

echo "🚨 FXSentinel Alert Check Started"
echo "=================================="
echo "Time: $(date)"
echo ""

# Change to the project directory
cd "$(dirname "$0")"

# Run the alert check
python3 check_and_send_alerts.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Alert check completed successfully"
else
    echo ""
    echo "❌ Alert check failed"
    exit 1
fi
