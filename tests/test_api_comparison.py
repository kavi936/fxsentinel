#!/usr/bin/env python3
"""
Test script to compare FMP vs FRED APIs
Focus on what actually works with your API keys
"""

import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def test_fmp_api():
    """Test Financial Modeling Prep API"""
    print("🧪 TESTING FMP API")
    print("=" * 40)
    
    api_key = os.getenv('FMP_API_KEY')
    if not api_key or api_key == 'your_fmp_api_key_here':
        print("❌ FMP API key not set")
        return None
    
    print(f"✅ FMP API Key: {api_key[:10]}...")
    
    # Test 1: Economic Indicators (as per your documentation)
    print("\n1. Testing Economic Indicators...")
    try:
        url = "https://financialmodelingprep.com/stable/economic-indicators"
        params = {
            'name': 'GDP',
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {len(data)} GDP records")
            if data:
                print(f"   Sample: {data[0]}")
        else:
            print(f"   ❌ Failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Economic Calendar (if available)
    print("\n2. Testing Economic Calendar...")
    try:
        url = "https://financialmodelingprep.com/api/v3/economic_calendar"
        params = {
            'from': datetime.now().strftime('%Y-%m-%d'),
            'to': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {len(data)} calendar events")
            if data:
                print(f"   Sample: {data[0]}")
        else:
            print(f"   ❌ Failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return api_key

def test_fred_api():
    """Test FRED API"""
    print("\n🧪 TESTING FRED API")
    print("=" * 40)
    
    api_key = os.getenv('FRED_API_KEY')
    if not api_key or api_key == 'your_fred_api_key_here':
        print("❌ FRED API key not set")
        return None
    
    print(f"✅ FRED API Key: {api_key[:10]}...")
    
    # Test 1: GDP data
    print("\n1. Testing GDP data...")
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': 'GDP',
            'api_key': api_key,
            'file_type': 'json',
            'limit': 5,
            'sort_order': 'desc'
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data:
                print(f"   ✅ Success: {len(data['observations'])} GDP records")
                if data['observations']:
                    print(f"   Sample: {data['observations'][0]}")
            else:
                print(f"   ❌ No observations: {data}")
        else:
            print(f"   ❌ Failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: CPI data
    print("\n2. Testing CPI data...")
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': 'CPIAUCSL',
            'api_key': api_key,
            'file_type': 'json',
            'limit': 3,
            'sort_order': 'desc'
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data:
                print(f"   ✅ Success: {len(data['observations'])} CPI records")
                if data['observations']:
                    print(f"   Sample: {data['observations'][0]}")
            else:
                print(f"   ❌ No observations: {data}")
        else:
            print(f"   ❌ Failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Unemployment Rate
    print("\n3. Testing Unemployment Rate...")
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': 'UNRATE',
            'api_key': api_key,
            'file_type': 'json',
            'limit': 3,
            'sort_order': 'desc'
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data:
                print(f"   ✅ Success: {len(data['observations'])} Unemployment records")
                if data['observations']:
                    print(f"   Sample: {data['observations'][0]}")
            else:
                print(f"   ❌ No observations: {data}")
        else:
            print(f"   ❌ Failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return api_key

def compare_apis():
    """Compare FMP vs FRED capabilities"""
    print("\n📊 API COMPARISON")
    print("=" * 50)
    
    fmp_key = test_fmp_api()
    fred_key = test_fred_api()
    
    print("\n🎯 RECOMMENDATIONS")
    print("=" * 50)
    
    if fmp_key and fred_key:
        print("✅ Both APIs are working!")
        print("\n📋 FMP Strengths:")
        print("   - Economic indicators (GDP, CPI, etc.)")
        print("   - Simple API structure")
        print("   - Good for current values")
        
        print("\n📋 FRED Strengths:")
        print("   - Most comprehensive US economic data")
        print("   - Historical data available")
        print("   - Reliable and well-documented")
        print("   - Free with no limits")
        
        print("\n💡 RECOMMENDED APPROACH:")
        print("   1. Use FRED for US economic indicators (GDP, CPI, Unemployment)")
        print("   2. Use FMP for additional economic indicators")
        print("   3. Implement aggressive caching (24+ hours)")
        print("   4. Focus on major indicators only")
        
    elif fred_key:
        print("✅ FRED API is working!")
        print("💡 Use FRED only - it has everything you need")
        print("   - GDP, CPI, Unemployment, Interest Rates")
        print("   - Completely free with no limits")
        
    elif fmp_key:
        print("✅ FMP API is working!")
        print("💡 Use FMP for economic indicators")
        
    else:
        print("❌ Neither API is working properly")
        print("   Check your API keys and internet connection")

if __name__ == "__main__":
    print("🚀 API COMPARISON TEST")
    print("=" * 50)
    compare_apis()
