#!/bin/bash

# FXSentinel Simple Alert Check Script
# This script runs the simplified alert check that works correctly

echo "🚨 FXSentinel Simple Alert Check Started"
echo "========================================="
echo "Time: $(date)"
echo ""

# Change to the project directory
cd "$(dirname "$0")"

# Run the simplified alert check
python3 simple_alert_check.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Simple alert check completed successfully"
else
    echo ""
    echo "❌ Simple alert check failed"
    exit 1
fi
