#!/bin/bash

# FXSentinel Railway Deployment Script
echo "🚀 FXSentinel Railway Deployment Script"
echo "========================================"

# Check if we're in the backend directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Test dependencies first
echo "🔍 Testing dependencies..."
python3 test_dependencies.py
if [ $? -ne 0 ]; then
    echo "❌ Dependency test failed. Please fix the issues before deploying."
    exit 1
fi

echo "✅ Dependencies test passed!"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
fi

# Check current git status
echo "📊 Checking git status..."
git status

echo ""
echo "🚂 Railway Deployment Instructions:"
echo "=================================="
echo "1. Push your code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Fix Railway deployment issues'"
echo "   git push origin main"
echo ""
echo "2. Deploy on Railway:"
echo "   - Go to https://railway.app"
echo "   - Sign up/Login with GitHub"
echo "   - Click 'New Project' → 'Deploy from GitHub repo'"
echo "   - Select your repository"
echo "   - Set root directory to 'backend'"
echo "   - Railway will auto-detect Python/Flask"
echo ""
echo "3. Set Environment Variables (if needed):"
echo "   - OPENAI_API_KEY (optional)"
echo "   - ALPHA_VANTAGE_API_KEY_1 (optional)"
echo "   - ALPHA_VANTAGE_API_KEY_2 (optional)"
echo "   - ALPHA_VANTAGE_API_KEY_3 (optional)"
echo "   - ALPHA_VANTAGE_API_KEY_4 (optional)"
echo "   - UNIRATE_API_KEY (optional)"
echo ""
echo "4. Test your deployment:"
echo "   - Visit your Railway URL"
echo "   - Test: https://your-app.railway.app/api/health"
echo "   - Test: https://your-app.railway.app/api/hello"
echo ""
echo "✅ Ready for deployment!"
