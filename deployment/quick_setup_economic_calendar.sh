#!/bin/bash

echo "🚀 FXSentinel Economic Calendar - Quick Setup"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "backend/services/hybrid_economic_calendar.py" ]; then
    echo "❌ Please run this script from the FXSentinel root directory"
    exit 1
fi

echo "✅ Found hybrid economic calendar service"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi

# Check if API keys are set
echo ""
echo "🔑 Checking API keys..."

FMP_KEY=$(grep "FMP_API_KEY=" .env | cut -d'=' -f2)
FRED_KEY=$(grep "FRED_API_KEY=" .env | cut -d'=' -f2)

if [ "$FMP_KEY" = "your_fmp_api_key_here" ] || [ -z "$FMP_KEY" ]; then
    echo "❌ FMP API key not set"
    echo "   Get it from: https://site.financialmodelingprep.com/developer"
else
    echo "✅ FMP API key is set"
fi

if [ "$FRED_KEY" = "your_fred_api_key_here" ] || [ -z "$FRED_KEY" ]; then
    echo "❌ FRED API key not set"
    echo "   Get it from: https://fred.stlouisfed.org/docs/api/api_key.html"
else
    echo "✅ FRED API key is set"
fi

echo ""
echo "🧪 Testing the hybrid economic calendar..."

# Test if Python can import the service
python3 -c "
import sys
import os
sys.path.append('backend')
try:
    from backend.services.hybrid_economic_calendar import hybrid_economic_calendar
    print('✅ Hybrid service imports successfully')
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 Running full test..."
    python3 test_hybrid_economic_calendar.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 SUCCESS! Your economic calendar is working!"
        echo ""
        echo "📋 Next steps:"
        echo "1. Set up your API keys in .env file if not done already"
        echo "2. Start your Flask server: cd backend && python3 app.py"
        echo "3. Test the endpoint: curl http://localhost:5001/api/economic-calendar"
        echo "4. Deploy to Railway with your API keys"
        echo ""
        echo "💰 Cost savings: $300/month → $0/month"
    else
        echo ""
        echo "⚠️  Test completed with some issues. Check the output above."
        echo "   Make sure to set up your API keys in the .env file."
    fi
else
    echo ""
    echo "❌ Setup failed. Please check the error messages above."
fi

echo ""
echo "📚 For detailed setup instructions, see: SETUP_FREE_ECONOMIC_CALENDAR.md"
