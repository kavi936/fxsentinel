#!/usr/bin/env python3
"""
Detailed test of Polymarket REST API endpoints to see what data is available
"""

import requests
import json
from datetime import datetime

def test_endpoint(url, params=None):
    """Test an endpoint and return results"""
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"\n{'='*80}")
        print(f"Testing: {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Success! Response type: {type(data)}")
                
                # Try to understand the structure
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())[:10]}")
                    # Look for markets or events
                    if 'data' in data:
                        print(f"Data structure found: {type(data['data'])}")
                        if isinstance(data['data'], list) and len(data['data']) > 0:
                            print(f"Sample item keys: {list(data['data'][0].keys())[:10]}")
                            print(f"\nSample item:")
                            print(json.dumps(data['data'][0], indent=2)[:500])
                    elif 'markets' in data:
                        print(f"Markets found: {len(data['markets'])}")
                        if len(data['markets']) > 0:
                            print(f"\nSample market:")
                            print(json.dumps(data['markets'][0], indent=2)[:500])
                    elif 'events' in data:
                        print(f"Events found: {len(data['events'])}")
                        if len(data['events']) > 0:
                            print(f"\nSample event:")
                            print(json.dumps(data['events'][0], indent=2)[:500])
                    else:
                        print(f"\nFull response (first 1000 chars):")
                        print(json.dumps(data, indent=2)[:1000])
                elif isinstance(data, list):
                    print(f"List with {len(data)} items")
                    if len(data) > 0:
                        print(f"\nSample item:")
                        print(json.dumps(data[0], indent=2)[:500])
                else:
                    print(f"Response: {str(data)[:500]}")
                    
            except json.JSONDecodeError:
                print(f"Response is not JSON. First 500 chars:")
                print(response.text[:500])
        else:
            print(f"❌ Failed: {response.text[:500]}")
            
        return response.status_code == 200, response
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

# Test Polymarket endpoints
print("="*80)
print("POLYMARKET API ENDPOINT TESTING")
print("="*80)

# Test CLOB API
print("\n\n🔵 TESTING CLOB API (clob.polymarket.com)")
test_endpoint("https://clob.polymarket.com/markets")
test_endpoint("https://clob.polymarket.com/markets", params={"limit": 10})
test_endpoint("https://clob.polymarket.com/events")

# Test Gamma API
print("\n\n🔵 TESTING GAMMA API (gamma-api.polymarket.com)")
test_endpoint("https://gamma-api.polymarket.com/markets")
test_endpoint("https://gamma-api.polymarket.com/events")
test_endpoint("https://gamma-api.polymarket.com/markets", params={"limit": 10})
test_endpoint("https://gamma-api.polymarket.com/markets", params={"active": "true"})

# Try to find currency-related markets
print("\n\n🔵 SEARCHING FOR CURRENCY/FOREX MARKETS")
currency_terms = ["EUR", "USD", "GBP", "JPY", "forex", "currency", "dollar", "euro"]

for term in currency_terms:
    print(f"\nSearching for: {term}")
    test_endpoint("https://gamma-api.polymarket.com/markets", params={"search": term})
    test_endpoint("https://gamma-api.polymarket.com/events", params={"search": term})

print("\n\n" + "="*80)
print("TESTING COMPLETE")
print("="*80)

