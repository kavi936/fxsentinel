#!/usr/bin/env python3
"""
Test script for Polygon.io API integration
Run this to verify your API key and data fetching works correctly
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_polygon_api_key():
    """Test if the Polygon.io API key is working"""
    api_key = os.getenv('POLYGON_API_KEY', 'demo')
    
    if api_key == 'demo':
        print("❌ No Polygon.io API key found in environment variables")
        print("Please set POLYGON_API_KEY in your .env file")
        return False
    
    print(f"🔑 Testing Polygon.io API key: {api_key[:8]}...")
    
    # Test with EUR/USD
    url = "https://api.polygon.io/v2/snapshot/locale/global/markets/forex/tickers/C:EURUSD"
    params = {'apikey': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'OK':
            print("✅ Polygon.io API key is working!")
            if 'results' in data and data['results']:
                result = data['results']
                if 'last' in result and result['last']:
                    price = result['last']['p']
                    print(f"📊 EUR/USD Price: {price}")
                    return True
                else:
                    print("⚠️ No price data in response")
                    return False
            else:
                print("⚠️ No results in response")
                return False
        else:
            print(f"❌ API returned error: {data}")
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

def main():
    """Run all tests"""
    print("🧪 Testing Polygon.io Integration")
    print("=" * 40)
    
    # Test 1: API Key
    api_key_works = test_polygon_api_key()
    
    # Test 2: Backend endpoint
    backend_works = test_backend_endpoint()
    
    # Test 3: API status
    status_works = test_api_status()
    
    print("\n" + "=" * 40)
    print("📋 Test Results Summary:")
    print(f"   API Key: {'✅ Working' if api_key_works else '❌ Failed'}")
    print(f"   Backend: {'✅ Working' if backend_works else '❌ Failed'}")
    print(f"   Status: {'✅ Working' if status_works else '❌ Failed'}")
    
    if api_key_works and backend_works and status_works:
        print("\n🎉 All tests passed! Polygon.io integration is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above and fix them.")
        
        if not api_key_works:
            print("\n💡 To fix API key issues:")
            print("1. Get a Polygon.io API key from https://polygon.io/")
            print("2. Add POLYGON_API_KEY=your_key to your .env file")
            
        if not backend_works:
            print("\n💡 To fix backend issues:")
            print("1. Make sure your Flask backend is running")
            print("2. Run: cd backend && python app.py")

if __name__ == "__main__":
    main() 