#!/usr/bin/env python3
"""
Test fetching specific Kalshi market by URL
"""

import os
import sys
import re
import requests
import json
from dotenv import load_dotenv

# Load environment
backend_env = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
if os.path.exists(backend_env):
    load_dotenv(backend_env)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.polyrouter_api_client import PolyRouterAPIClient

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

def parse_kalshi_url(url):
    """Extract identifiers from Kalshi URL"""
    # Pattern: https://kalshi.com/markets/{event_ticker}/{optional_path}/{market_ticker}
    # Example: https://kalshi.com/markets/kxfeddecision/fed-meeting/kxfeddecision-26jan
    # event_ticker: kxfeddecision
    # market_ticker: kxfeddecision-26jan (last segment)
    pattern = r'kalshi\.com/markets/([^/]+)/(?:[^/]+/)?([^/?]+)'
    match = re.search(pattern, url)
    if match:
        return {
            "event_ticker": match.group(1),
            "market_ticker": match.group(2)  # Last segment is the actual market ticker
        }
    return None

def test_dome_api(event_ticker, market_ticker):
    """Test fetching via DOME API"""
    print_header("TESTING DOME API")
    
    dome_api_key = os.getenv('DOME_API_KEY')
    if not dome_api_key:
        print_error("DOME_API_KEY not set")
        return None
    
    try:
        # Try DOME API endpoint
        url = "https://api.domeapi.io/v1/kalshi/markets"
        headers = {"X-API-Key": dome_api_key}
        params = {
            "limit": 100,  # DOME API max is 100
            "offset": 0
        }
        
        print_info(f"Fetching markets from DOME API...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            markets = data.get("markets", [])
            print_success(f"Fetched {len(markets)} markets from DOME API")
            
            # Search for matching market (try multiple pagination pages)
            found = None
            offset = 0
            max_pages = 10  # Search up to 10 pages (1000 markets)
            
            print_info(f"Searching through up to {max_pages} pages (1000 markets)...")
            
            for page in range(max_pages):
                params = {
                    "limit": 100,
                    "offset": offset
                }
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    print_error(f"DOME API returned status {response.status_code} at page {page + 1}")
                    break
                
                data = response.json()
                markets = data.get("markets", [])
                
                if not markets:
                    print_info(f"No more markets at page {page + 1}")
                    break
                
                print_info(f"Searching page {page + 1} ({len(markets)} markets)...")
                
                # Search in this page
                for market in markets:
                    mt = market.get("market_ticker") or market.get("ticker")
                    et = market.get("event_ticker") or market.get("series_ticker")
                    
                    # Check exact match
                    if mt == market_ticker:
                        found = market
                        print_success(f"Found exact match on page {page + 1}!")
                        break
                    # Check partial match
                    elif market_ticker in str(mt) and event_ticker in str(et):
                        found = market
                        print_success(f"Found partial match on page {page + 1}!")
                        break
                
                if found:
                    break
                
                offset += 100
                if len(markets) < 100:  # Last page
                    break
            
            if found:
                market = found
                print_success(f"Found matching market!")
                print(f"\n{CYAN}Market Data:{RESET}")
                print(f"  Title: {market.get('title', 'N/A')}")
                print(f"  Event Ticker: {market.get('event_ticker', 'N/A')}")
                print(f"  Market Ticker: {market.get('market_ticker', 'N/A')}")
                print(f"  Status: {market.get('status', 'N/A')}")
                print(f"  Last Price: {market.get('last_price', 'N/A')}")
                print(f"  Volume: {market.get('volume', 'N/A')}")
                print(f"  Volume 24h: {market.get('volume_24h', 'N/A')}")
                print(f"  Close Time: {market.get('close_time', 'N/A')}")
                
                # Show side_a and side_b if available
                if "side_a" in market:
                    side_a = market["side_a"]
                    print(f"\n  Side A:")
                    if isinstance(side_a, dict):
                        for k, v in side_a.items():
                            print(f"    {k}: {v}")
                    else:
                        print(f"    {side_a}")
                
                if "side_b" in market:
                    side_b = market["side_b"]
                    print(f"\n  Side B:")
                    if isinstance(side_b, dict):
                        for k, v in side_b.items():
                            print(f"    {k}: {v}")
                    else:
                        print(f"    {side_b}")
                
                return market
        else:
            print_error(f"DOME API returned status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print_error(f"DOME API error: {e}")
        import traceback
        traceback.print_exc()
    
    print_error("Market not found in DOME API results")
    return None

def test_polyrouter_api(event_ticker, market_ticker):
    """Test fetching via PolyRouter API"""
    print_header("TESTING POLYROUTER API")
    
    polyrouter_api_key = os.getenv('POLYROUTER_API_KEY')
    if not polyrouter_api_key:
        print_error("POLYROUTER_API_KEY not set")
        return None
    
    try:
        client = PolyRouterAPIClient(polyrouter_api_key)
        
        if not client.available:
            print_error("PolyRouter client not available")
            return None
        
        print_info(f"Fetching Kalshi markets from PolyRouter...")
        markets = client.get_markets(platform="kalshi", limit=100)  # Start with smaller limit
        
        print_success(f"Fetched {len(markets)} markets from PolyRouter")
        
        # Search for matching market
        for market in markets:
            normalized = client.normalize_market(market)
            market_id = normalized.get("id")
            url = normalized.get("url", "")
            
            # Check if ticker matches
            if market_ticker in str(market_id) or market_ticker in url or event_ticker in url:
                print_success(f"Found potential match!")
                print(f"\n{CYAN}Market Data:{RESET}")
                print(f"  Question: {normalized.get('question', 'N/A')}")
                print(f"  Platform: {normalized.get('platform', 'N/A')}")
                print(f"  ID: {normalized.get('id', 'N/A')}")
                print(f"  Status: {normalized.get('status', 'N/A')}")
                print(f"  Yes Price: {normalized.get('yes_price', 'N/A')}")
                print(f"  No Price: {normalized.get('no_price', 'N/A')}")
                print(f"  Volume: {normalized.get('volume', 'N/A')}")
                print(f"  URL: {normalized.get('url', 'N/A')}")
                
                # Show raw market data
                raw = normalized.get("raw_data", {})
                if raw:
                    print(f"\n  Raw Data Keys: {list(raw.keys())[:20]}")
                    if "current_prices" in raw:
                        print(f"  Current Prices: {json.dumps(raw['current_prices'], indent=4)}")
                
                return normalized
        
        print_error("Market not found in PolyRouter results")
        return None
        
    except Exception as e:
        print_error(f"PolyRouter API error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_kalshi_public_api(event_ticker, market_ticker):
    """Test fetching via Kalshi Public API (no auth required)"""
    print_header("TESTING KALSHI PUBLIC API")
    
    try:
        # Kalshi public API endpoint - try different formats
        # Format 1: By market ticker
        url1 = f"https://api.kalshi.com/trade-api/v2/markets/{market_ticker}"
        # Format 2: By event ticker and market ticker
        url2 = f"https://api.kalshi.com/trade-api/v2/events/{event_ticker}/markets/{market_ticker}"
        
        print_info(f"Trying Format 1: {url1}")
        try:
            response = requests.get(url1, timeout=30)
            if response.status_code == 200:
                data = response.json()
                print_success("Market found via Kalshi Public API (Format 1)!")
                print(f"\n{CYAN}Market Data:{RESET}")
                print(json.dumps(data, indent=2))
                return data
        except requests.exceptions.RequestException as e:
            print_info(f"Format 1 failed: {e}")
        
        print_info(f"Trying Format 2: {url2}")
        try:
            response = requests.get(url2, timeout=30)
            if response.status_code == 200:
                data = response.json()
                print_success("Market found via Kalshi Public API (Format 2)!")
                print(f"\n{CYAN}Market Data:{RESET}")
                print(json.dumps(data, indent=2))
                return data
        except requests.exceptions.RequestException as e:
            print_info(f"Format 2 failed: {e}")
        
        # If both fail, show error
        print_error("Kalshi Public API endpoints not accessible (may require authentication or different endpoint)")
        return None
            
    except Exception as e:
        print_error(f"Kalshi Public API error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    url = "https://kalshi.com/markets/kxfeddecision/fed-meeting/kxfeddecision-26jan"
    
    print_header("FETCHING KALSHI MARKET BY URL")
    print_info(f"URL: {url}")
    
    # Parse URL
    parsed = parse_kalshi_url(url)
    if not parsed:
        print_error("Could not parse URL")
        return
    
    event_ticker = parsed["event_ticker"]
    market_ticker = parsed["market_ticker"]
    
    print_success(f"Parsed identifiers:")
    print(f"  Event Ticker: {event_ticker}")
    print(f"  Market Ticker: {market_ticker}")
    
    # Try different APIs
    results = {}
    
    # Try DOME API
    results["dome"] = test_dome_api(event_ticker, market_ticker)
    
    # Try PolyRouter
    results["polyrouter"] = test_polyrouter_api(event_ticker, market_ticker)
    
    # Try Kalshi Public API
    results["kalshi_public"] = test_kalshi_public_api(event_ticker, market_ticker)
    
    # Summary
    print_header("SUMMARY")
    for api_name, result in results.items():
        if result:
            print_success(f"{api_name.upper()}: Found market data")
        else:
            print_error(f"{api_name.upper()}: No data found")

if __name__ == "__main__":
    main()

