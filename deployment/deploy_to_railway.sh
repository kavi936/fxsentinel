#!/bin/bash

# FXSentinel Railway Deployment Script
# This script deploys both the main Flask app and background worker to Railway

set -e  # Exit on any error

echo "🚀 FXSentinel Railway Deployment Script"
echo "======================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
else
    echo "✅ Railway CLI found"
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged into Railway. Please login first:"
    echo "   railway login"
    exit 1
fi

echo "✅ Logged into Railway as: $(railway whoami)"

# Function to deploy service
deploy_service() {
    local service_name=$1
    local service_dir=$2
    local start_command=$3
    
    echo ""
    echo "🔧 Deploying $service_name..."
    echo "   Directory: $service_dir"
    echo "   Start Command: $start_command"
    
    # Create Railway project if it doesn't exist
    if [ ! -f "$service_dir/railway.json" ]; then
        echo "   Creating Railway project..."
        cd "$service_dir"
        railway init --name "fxsentinel-$service_name"
        cd ..
    fi
    
    # Deploy the service
    echo "   Deploying to Railway..."
    cd "$service_dir"
    railway up
    cd ..
    
    echo "✅ $service_name deployed successfully!"
}

# Deploy main Flask app
deploy_service "main-app" "backend" "python3 app.py"

# Deploy background worker
deploy_service "background-worker" "backend" "python3 -c \"from services.background_alert_worker import start_background_worker; start_background_worker(); import time; time.sleep(86400)\""

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Set environment variables in Railway dashboard:"
echo "   - Go to each service in Railway"
echo "   - Add environment variables from 'railway.env.example'"
echo "   - Update API_BASE_URL to point to your main app URL"
echo ""
echo "2. Test the services:"
echo "   - Main app health: https://your-main-app.up.railway.app/api/health"
echo "   - Background worker: Check Railway logs"
echo ""
echo "3. Verify alerts are working:"
echo "   - Check Railway logs for background worker activity"
echo "   - Test with a manual alert trigger"
echo ""
echo "🔗 Railway Dashboard: https://railway.app/dashboard"
