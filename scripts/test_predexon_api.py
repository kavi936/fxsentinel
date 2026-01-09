#!/usr/bin/env python3
"""
Test Predexon unified API to see what's available
"""

import requests
import json

print("="*80)
print("TESTING PREDEXON UNIFIED API")
print("="*80)

# Test Predexon endpoints
endpoints = [
    "https://api.predexon.com",
    "https://predexon.com/api",
    "https://api.predexon.com/v1",
    "https://api.predexon.com/markets",
    "https://api.predexon.com/health"
]

for endpoint in endpoints:
    print(f"\nTesting: {endpoint}")
    try:
        response = requests.get(endpoint, timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ JSON Response:")
                print(f"  {json.dumps(data, indent=2)[:500]}")
            except:
                print(f"  Response: {response.text[:200]}")
        elif response.status_code == 401:
            print(f"  ⚠️  Requires authentication")
        elif response.status_code == 404:
            print(f"  ℹ️  Not found")
        else:
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*80)
print("If Predexon requires authentication, check their documentation:")
print("https://docs.predexon.com")
print("="*80)

