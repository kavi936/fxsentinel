#!/bin/bash

# FXSentinel Railway Deployment Script
# This script helps deploy both the main app and background worker

echo "🚀 FXSentinel Railway Deployment Script"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "worker.py" ]; then
    echo "❌ Error: Please run this script from the root directory of the FXSentinel project"
    exit 1
fi

echo "✅ Found deployment files"

# Check git status
echo ""
echo "📋 Checking git status..."
git status --porcelain

if [ $? -ne 0 ]; then
    echo "❌ Error: Not in a git repository or git not available"
    exit 1
fi

echo ""
echo "🔧 Deployment Configuration:"
echo "Main App: fxsentinel-production.up.railway.app"
echo "Background Worker: fxsentinel-background-worker"
echo ""

# Ask user which service to deploy
echo "Which service would you like to deploy?"
echo "1) Main App (Web Application)"
echo "2) Background Worker"
echo "3) Both Services"
echo "4) Exit"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Deploying Main App..."
        echo "Make sure to set the following in Railway:"
        echo "- Root Directory: backend"
        echo "- Start Command: gunicorn app:app --bind 0.0.0.0:\$PORT --workers 1 --timeout 120 --keep-alive 2"
        echo ""
        read -p "Press Enter to continue with git push..."
        git add .
        git commit -m "Deploy main app with proper Flask configuration"
        git push origin main
        echo "✅ Main app deployment initiated"
        ;;
    2)
        echo ""
        echo "🚀 Deploying Background Worker..."
        echo "Make sure to set the following in Railway:"
        echo "- Root Directory: backend"
        echo "- Start Command: python railway_worker.py"
        echo ""
        read -p "Press Enter to continue with git push..."
        git add .
        git commit -m "Deploy background worker with proper configuration"
        git push origin main
        echo "✅ Background worker deployment initiated"
        ;;
    3)
        echo ""
        echo "🚀 Deploying Both Services..."
        echo ""
        echo "For Main App (fxsentinel-production):"
        echo "- Root Directory: backend"
        echo "- Start Command: gunicorn app:app --bind 0.0.0.0:\$PORT --workers 1 --timeout 120 --keep-alive 2"
        echo ""
        echo "For Background Worker (fxsentinel-background-worker):"
        echo "- Root Directory: backend"
        echo "- Start Command: python railway_worker.py"
        echo ""
        read -p "Press Enter to continue with git push..."
        git add .
        git commit -m "Deploy both main app and background worker with proper configuration"
        git push origin main
        echo "✅ Both services deployment initiated"
        ;;
    4)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "📋 Next Steps:"
echo "1. Go to Railway dashboard"
echo "2. Update the start commands as shown above"
echo "3. Set environment variables (see DEPLOYMENT_FIX_GUIDE.md)"
echo "4. Monitor deployment logs"
echo "5. Test the services"
echo ""
echo "📖 For detailed instructions, see: DEPLOYMENT_FIX_GUIDE.md"
echo ""
echo "✅ Deployment script completed!"
