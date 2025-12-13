#!/bin/bash

# Force Fresh Railway Deployment Script
# This script forces Railway to deploy fresh code by clearing caches and redeploying

echo "🚀 Forcing fresh Railway deployment for FXSentinel Background Worker"
echo "================================================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check if we're logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run: railway login"
    exit 1
fi

echo "✅ Railway CLI is available and authenticated"

# Get current timestamp for cache busting
TIMESTAMP=$(date +%s)
echo "🕐 Deployment timestamp: $TIMESTAMP"

# Update version file with timestamp
echo "2.0.0-$TIMESTAMP" > backend/VERSION
echo "📝 Updated version file with timestamp: 2.0.0-$TIMESTAMP"

# Commit changes to git (if in a git repo)
if [ -d ".git" ]; then
    echo "📦 Committing changes to git..."
    git add .
    git commit -m "Force fresh deployment - cache bust v2.0.0-$TIMESTAMP" || echo "⚠️ No changes to commit or git commit failed"
    git push origin main || echo "⚠️ Git push failed or not on main branch"
    echo "✅ Git changes committed and pushed"
else
    echo "⚠️ Not in a git repository - skipping git operations"
fi

# Force redeploy the background worker service
echo "🔄 Forcing redeploy of background worker service..."

# Try to redeploy using Railway CLI
railway redeploy --service fxsentinel-background-worker || {
    echo "⚠️ Service-specific redeploy failed, trying general redeploy..."
    railway redeploy
}

echo "✅ Redeploy command sent to Railway"
echo ""
echo "🎯 Next steps:"
echo "1. Check Railway dashboard for deployment status"
echo "2. Monitor logs for 'FXSentinel Background Worker v2.0.0' message"
echo "3. Verify health check at /api/health endpoint"
echo "4. Look for 'BackgroundAlertWorker started' in logs"
echo ""
echo "🔍 If deployment still fails:"
echo "1. Delete the service in Railway dashboard"
echo "2. Recreate it with the same configuration"
echo "3. Or try the nuclear option: railway service delete fxsentinel-background-worker"
echo ""
echo "📊 Monitor deployment with: railway logs --service fxsentinel-background-worker"
