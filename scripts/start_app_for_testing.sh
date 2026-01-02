#!/bin/bash
# Start Flask app for testing unified alert system

cd "$(dirname "$0")/.."

echo "🚀 Starting Flask app for testing..."
echo "   This will start the app with unified alert processor"
echo ""
echo "⚠️  Make sure you have:"
echo "   - Firebase credentials configured"
echo "   - Telegram bot token configured (optional)"
echo "   - All environment variables set"
echo ""

# Set default port if not set
export PORT=${PORT:-5001}

# Start Flask app
python3 backend/app.py

