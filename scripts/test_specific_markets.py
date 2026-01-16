#!/usr/bin/env python3
"""
Test fetching specific markets from URLs provided by user
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment
backend_env = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
if os.path.exists(backend_env):
    load_dotenv(backend_env)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.polyrouter_api_client import PolyRouterAPIClient
from services.prediction_markets_service import prediction_markets_service

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

def test_specific_markets():
    """Test fetching the specific markets from URLs"""
    print_header("TESTING SPECIFIC MARKETS FROM URLs")
    
    # Market identifiers extracted from URLs
    markets_to_test = [
        {
            "name": "Kalshi Fed Decision",
            "url": "https://kalshi.com/markets/kxfeddecision/fed-meeting/kxfeddecision-26jan",
            "platform": "kalshi",
            "event_ticker": "kxfeddecision",
            "market_ticker": "kxfeddecision-26jan"
        },
        {
            "name": "Polymarket Fed Decision",
            "url": "https://polymarket.com/event/fed-decision-in-january/no-change-in-fed-interest-rates-after-january-2026-meeting",
            "platform": "polymarket",
            "event_slug": "fed-decision-in-january",
            "market_slug": "no-change-in-fed-interest-rates-after-january-2026-meeting"
        },
        {
            "name": "Kalshi Powell Leaving",
            "url": "https://kalshi.com/markets/kxleavepowell/powell-leaving/leavepowell-25",
            "platform": "kalshi",
            "event_ticker": "kxleavepowell",
            "market_ticker": "leavepowell-25"
        }
    ]
    
    client = PolyRouterAPIClient()
    
    if not client.available:
        print_error("PolyRouter API not available")
        return
    
    print_success("PolyRouter API client initialized")
    
    # Search for these markets
    for market_info in markets_to_test:
        print_info(f"\nSearching for: {market_info['name']}")
        print_info(f"URL: {market_info['url']}")
        
        # Search by fetching markets and filtering
        platform = market_info['platform']
        markets = client.get_markets(platform=platform, limit=200)
        
        found = None
        if platform == "kalshi":
            # Search by title containing keywords
            keywords = []
            if "fed" in market_info['name'].lower():
                keywords = ["fed", "federal reserve", "january", "interest rate"]
            elif "powell" in market_info['name'].lower():
                keywords = ["powell", "leaving", "leave"]
            
            for m in markets:
                title = (m.get("title") or "").lower()
                if all(kw in title for kw in keywords):
                    found = m
                    break
        else:
            # Polymarket: search by slug or title
            for m in markets:
                slug = (m.get("slug") or m.get("market_slug") or "").lower()
                title = (m.get("title") or "").lower()
                if "fed" in title and "january" in title:
                    found = m
                    break
        
        if found:
            print_success(f"Found market!")
            normalized = client.normalize_market(found)
            
            print(f"\n{CYAN}Market Data:{RESET}")
            print(f"  Title: {normalized.get('question', 'N/A')}")
            print(f"  Platform: {normalized.get('platform', 'N/A')}")
            print(f"  Status: {normalized.get('status', 'N/A')}")
            print(f"  Yes Price: {normalized.get('yes_price', 'N/A')}")
            print(f"  No Price: {normalized.get('no_price', 'N/A')}")
            print(f"  Volume: ${normalized.get('volume', 0):,.2f}" if normalized.get('volume') else "  Volume: N/A")
            print(f"  URL: {normalized.get('url', 'N/A')}")
            print(f"  Resolution Date: {normalized.get('resolution_date', 'N/A')}")
            
            # Show raw current_prices
            raw = found.get("current_prices", {})
            if raw:
                print(f"\n  Raw Prices from API:")
                for outcome, price_data in raw.items():
                    if isinstance(price_data, dict):
                        print(f"    {outcome}: price={price_data.get('price')}, bid={price_data.get('bid')}, ask={price_data.get('ask')}")
        else:
            print_error(f"Market not found in first 500 results")
            print_info("This market might be further down in the list or not currently active")

def test_price_extraction():
    """Test price extraction logic"""
    print_header("TESTING PRICE EXTRACTION LOGIC")
    
    # Test cases
    test_cases = [
        {
            "name": "Valid prices",
            "current_prices": {
                "yes": {"price": 0.65, "bid": 0.64, "ask": 0.66},
                "no": {"price": 0.35, "bid": 0.34, "ask": 0.36}
            },
            "volume": 10000,
            "expected": "Should extract 0.65/0.35"
        },
        {
            "name": "Zero prices with no volume (invalid)",
            "current_prices": {
                "yes": {"price": 0, "bid": 0, "ask": 0},
                "no": {"price": 1, "bid": 0, "ask": 0}
            },
            "volume": 0,
            "expected": "Should be filtered out (no real data)"
        },
        {
            "name": "Zero prices with volume (valid)",
            "current_prices": {
                "yes": {"price": 0, "bid": 0, "ask": 0},
                "no": {"price": 1, "bid": 0, "ask": 0}
            },
            "volume": 5000,
            "expected": "Should extract 0/1 (resolved or extreme probability)"
        }
    ]
    
    client = PolyRouterAPIClient()
    
    for test_case in test_cases:
        print_info(f"\nTest: {test_case['name']}")
        print_info(f"Expected: {test_case['expected']}")
        
        market = {
            "title": "Test Market",
            "current_prices": test_case["current_prices"],
            "volume_24h": test_case["volume"],
            "status": "open",
            "platform": "polymarket"
        }
        
        normalized = client.normalize_market(market)
        yes_price = normalized.get("yes_price")
        no_price = normalized.get("no_price")
        volume = normalized.get("volume")
        
        print(f"  Result: yes_price={yes_price}, no_price={no_price}, volume={volume}")
        
        if test_case["name"] == "Zero prices with no volume (invalid)":
            if yes_price is None and no_price is None:
                print_success("  ✅ Correctly marked as invalid (None)")
            else:
                print_error(f"  ❌ Should be None but got {yes_price}/{no_price}")
        else:
            if yes_price is not None or no_price is not None:
                print_success(f"  ✅ Prices extracted: {yes_price}/{no_price}")
            else:
                print_error("  ❌ Failed to extract prices")

def main():
    print_header("SPECIFIC MARKETS TEST")
    
    # Test price extraction logic
    test_price_extraction()
    
    # Test fetching specific markets
    test_specific_markets()
    
    print_header("TEST COMPLETE")

if __name__ == "__main__":
    main()

