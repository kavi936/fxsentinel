#!/usr/bin/env python3
"""
Simple API test - just call the APIs and see what we get
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
backend_env = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
if os.path.exists(backend_env):
    load_dotenv(backend_env)

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def test_propheseer():
    """Test PropheSeer API directly"""
    print_header("TESTING PROPHESEER API")
    
    api_key = os.getenv('PROPHESEER_API_KEY')
    if not api_key:
        print_error("PROPHESEER_API_KEY not found in environment")
        return
    
    print_info(f"API Key: {api_key[:20]}...")
    
    # Test basic endpoint
    url = "https://api.propheseer.com/v1/markets"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = {
        "limit": 10
    }
    
    print_info(f"Requesting: {url}")
    print_info(f"Params: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Request successful!")
            data = response.json()
            print_info(f"Response keys: {list(data.keys())}")
            
            if "data" in data:
                markets = data["data"]
                print_success(f"Found {len(markets)} markets")
                
                if markets:
                    print_info("\nFirst market:")
                    print(json.dumps(markets[0], indent=2, default=str))
                    
                    print_info("\nAll market titles:")
                    for i, m in enumerate(markets, 1):
                        title = m.get("question") or m.get("title", "N/A")
                        category = m.get("category", "N/A")
                        status = m.get("status", "N/A")
                        print(f"  {i}. [{category}] {status}: {title[:70]}")
            else:
                print_info("Full response:")
                print(json.dumps(data, indent=2, default=str)[:1000])
        else:
            print_error(f"Request failed: {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_polyrouter():
    """Test PolyRouter API directly"""
    print_header("TESTING POLYROUTER API")
    
    api_key = os.getenv('POLYROUTER_API_KEY')
    if not api_key:
        print_error("POLYROUTER_API_KEY not found in environment")
        return
    
    print_info(f"API Key: {api_key[:20]}...")
    
    # Test basic endpoint
    url = "https://api-v2.polyrouter.io/markets"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    params = {
        "limit": 10,
        "platform": "polymarket"
    }
    
    print_info(f"Requesting: {url}")
    print_info(f"Params: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Request successful!")
            data = response.json()
            print_info(f"Response keys: {list(data.keys())}")
            
            if "markets" in data:
                markets = data["markets"]
                print_success(f"Found {len(markets)} markets")
                
                if markets:
                    print_info("\nFirst market:")
                    print(json.dumps(markets[0], indent=2, default=str))
                    
                    print_info("\nAll market titles:")
                    for i, m in enumerate(markets, 1):
                        title = m.get("title") or m.get("question", "N/A")
                        platform = m.get("platform", "N/A")
                        status = m.get("status", "N/A")
                        print(f"  {i}. [{platform}] {status}: {title[:70]}")
            else:
                print_info("Full response:")
                print(json.dumps(data, indent=2, default=str)[:1000])
        else:
            print_error(f"Request failed: {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print_header("SIMPLE API TEST")
    
    # Test PropheSeer
    test_propheseer()
    
    # Test PolyRouter
    test_polyrouter()
    
    print_header("TEST COMPLETE")

if __name__ == "__main__":
    main()

