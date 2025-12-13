#!/bin/bash
# Deploy to Railway Background Worker Service

echo "🚂 Railway Background Worker Deployment"
echo "========================================"
echo ""

# Check if logged in
echo "Checking Railway authentication..."
railway whoami > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Not logged in to Railway"
    echo ""
    echo "Please run: railway login"
    echo "Then run this script again."
    exit 1
fi

echo "✅ Logged in to Railway"
echo ""

# List projects
echo "Available Railway projects:"
railway list

echo ""
echo "To deploy to background worker:"
echo "1. Link to your worker service:"
echo "   railway link"
echo ""
echo "2. Select your FXSentinel project"
echo "3. Select the WORKER service (not main app)"
echo ""
echo "4. Deploy with:"
echo "   railway up"
echo ""
echo "OR if already linked, just run:"
echo "   railway up"

