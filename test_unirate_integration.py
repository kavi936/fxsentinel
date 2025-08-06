#!/usr/bin/env python3
"""
Test script for UniRateAPI integration
Run this to verify your API key and data fetching works correctly
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_unirate_api_key():
    """Test if the UniRateAPI key is working"""
    api_key = os.getenv('UNIRATE_API_KEY', 'demo')
    
    if api_key == 'demo':
        print("❌ No UniRateAPI key found in environment variables")
        print("Please set UNIRATE_API_KEY in your .env file")
        return False
    
    print(f"🔑 Testing UniRateAPI key: {api_key[:8]}...")
    
    # Test with EUR/USD conversion
    url = "https://api.unirateapi.com/api/convert"
    params = {
        'api_key': api_key,
        'from': 'USD',
        'to': 'EUR',
        'amount': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'result' in data and data['result']:
            print("✅ UniRateAPI key is working!")
            rate = data['result']
            print(f"📊 USD/EUR Rate: {rate}")
            return True
        else:
            print(f"❌ API returned unexpected data: {data}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return False

def test_backend_endpoint():
    """Test the backend forex-prices endpoint"""
    print("\n🌐 Testing backend endpoint...")
    
    try:
        response = requests.get('http://localhost:8000/api/forex-prices', timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'prices' in data:
            print("✅ Backend endpoint is working!")
            print(f"📊 Data source: {data.get('dataSource', 'unknown')}")
            
            prices = data['prices']
            for pair, info in prices.items():
                price = info.get('price', 'N/A')
                change = info.get('change', 'N/A')
                print(f"   {pair}: {price} (change: {change})")
            
            return True
        else:
            print("❌ No prices in response")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not running or error: {e}")
        print("Make sure your Flask backend is running on http://localhost:8000")
        return False

def test_api_status():
    """Test the API status endpoint"""
    print("\n📊 Testing API status endpoint...")
    
    try:
        response = requests.get('http://localhost:8000/api/api-status', timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        print("✅ API status endpoint is working!")
        print(f"Provider: {data.get('provider', 'unknown')}")
        print(f"Plan: {data.get('plan', 'unknown')}")
        print(f"Daily requests used: {data.get('daily_requests_used', 0)}")
        print(f"Daily requests remaining: {data.get('daily_requests_remaining', 0)}")
        print(f"Minute requests used: {data.get('minute_requests_used', 0)}")
        print(f"Minute requests remaining: {data.get('minute_requests_remaining', 0)}")
        print(f"Status: {data.get('status', 'unknown')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API status endpoint error: {e}")
        return False

def test_multiple_currencies():
    """Test multiple currency pairs"""
    print("\n💱 Testing multiple currency pairs...")
    
    api_key = os.getenv('UNIRATE_API_KEY', 'demo')
    if api_key == 'demo':
        print("❌ No API key available for currency testing")
        return False
    
    pairs = [
        ('USD', 'EUR', 'USD/EUR'),
        ('USD', 'JPY', 'USD/JPY'),
        ('GBP', 'USD', 'GBP/USD')
    ]
    
    success_count = 0
    
    for from_curr, to_curr, pair_name in pairs:
        try:
            url = "https://api.unirateapi.com/api/convert"
            params = {
                'api_key': api_key,
                'from': from_curr,
                'to': to_curr,
                'amount': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'result' in data and data['result']:
                rate = data['result']
                print(f"✅ {pair_name}: {rate}")
                success_count += 1
            else:
                print(f"❌ {pair_name}: No data")
                
        except Exception as e:
            print(f"❌ {pair_name}: Error - {e}")
    
    print(f"\n📈 Successfully fetched {success_count}/{len(pairs)} currency pairs")
    return success_count == len(pairs)

def main():
    """Run all tests"""
    print("🧪 Testing UniRateAPI Integration")
    print("=" * 40)
    
    # Test 1: API Key
    api_key_works = test_unirate_api_key()
    
    # Test 2: Multiple currencies
    currencies_work = test_multiple_currencies()
    
    # Test 3: Backend endpoint
    backend_works = test_backend_endpoint()
    
    # Test 4: API status
    status_works = test_api_status()
    
    print("\n" + "=" * 40)
    print("📋 Test Results Summary:")
    print(f"   API Key: {'✅ Working' if api_key_works else '❌ Failed'}")
    print(f"   Currencies: {'✅ Working' if currencies_work else '❌ Failed'}")
    print(f"   Backend: {'✅ Working' if backend_works else '❌ Failed'}")
    print(f"   Status: {'✅ Working' if status_works else '❌ Failed'}")
    
    if api_key_works and currencies_work and backend_works and status_works:
        print("\n🎉 All tests passed! UniRateAPI integration is working correctly.")
        print("\n💰 Budget Impact:")
        print("   - Monthly data cost: $0 (was $50 with Polygon.io)")
        print("   - Break-even users: 2 (was 4 with Polygon.io)")
        print("   - Profit at 10 users: $224 (was $174 with Polygon.io)")
    else:
        print("\n⚠️ Some tests failed. Check the errors above and fix them.")
        
        if not api_key_works:
            print("\n💡 To fix API key issues:")
            print("1. Get a free UniRateAPI key from https://unirateapi.com/")
            print("2. Add UNIRATE_API_KEY=your_key to your .env file")
            
        if not backend_works:
            print("\n💡 To fix backend issues:")
            print("1. Make sure your Flask backend is running")
            print("2. Run: cd backend && python app.py")
    
    print("\n📝 Next Steps:")
    print("1. Add attribution link to your website:")
    print('   <a href="https://unirateapi.com">Exchange Rates By UniRateAPI</a>')
    print("2. Monitor usage via /api/api-status endpoint")
    print("3. Focus on user acquisition with your lower break-even point!")

if __name__ == "__main__":
    main() 