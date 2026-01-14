#!/usr/bin/env python3
"""
Comprehensive DOME API Test
Tests all available endpoints and fetches maximum data while respecting rate limits:
- 1 query per second
- 10 queries per 10 seconds

Tests both Polymarket and Kalshi endpoints through DOME API.
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

DOME_API_KEY = "01555869c196b7ba95ead857def66789408b54f9"
DOME_BASE_URL = "https://api.domeapi.io/v1"

# Rate limit: 1 req/sec, 10 req/10sec
RATE_LIMIT_DELAY = 1.1  # Slightly more than 1 second to be safe
MAX_REQUESTS_PER_WINDOW = 10
WINDOW_SECONDS = 10

class RateLimiter:
    def __init__(self):
        self.request_times = []
        self.lock = False
    
    def wait_if_needed(self):
        """Wait if we need to respect rate limits"""
        now = time.time()
        
        # Remove requests older than 10 seconds
        self.request_times = [t for t in self.request_times if now - t < WINDOW_SECONDS]
        
        # Check if we've hit the 10-per-10-seconds limit
        if len(self.request_times) >= MAX_REQUESTS_PER_WINDOW:
            # Wait until oldest request expires
            oldest = min(self.request_times)
            wait_time = WINDOW_SECONDS - (now - oldest) + 0.1
            if wait_time > 0:
                print(f"  ⏳ Rate limit: Waiting {wait_time:.1f}s (10 requests in last 10s)")
                time.sleep(wait_time)
                # Clean up again
                now = time.time()
                self.request_times = [t for t in self.request_times if now - t < WINDOW_SECONDS]
        
        # Always wait at least 1 second between requests
        if self.request_times:
            last_request = max(self.request_times)
            elapsed = now - last_request
            if elapsed < RATE_LIMIT_DELAY:
                wait_time = RATE_LIMIT_DELAY - elapsed
                time.sleep(wait_time)
        
        # Record this request
        self.request_times.append(time.time())

rate_limiter = RateLimiter()

def make_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """Make a rate-limited request to DOME API"""
    rate_limiter.wait_if_needed()
    
    url = f"{DOME_BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {DOME_API_KEY}"}
    
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "status_code": 200,
                "response_time_ms": round(response_time, 2),
                "error": None
            }
        elif response.status_code == 429:
            return {
                "success": False,
                "data": None,
                "status_code": 429,
                "response_time_ms": round(response_time, 2),
                "error": "Rate limit exceeded"
            }
        else:
            return {
                "success": False,
                "data": None,
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2),
                "error": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "status_code": None,
            "response_time_ms": 0,
            "error": str(e)
        }

def test_polymarket_markets():
    """Test Polymarket markets endpoint"""
    print("\n" + "="*80)
    print("TESTING POLYMARKET MARKETS (via DOME API)")
    print("="*80)
    
    results = {
        "endpoint": "/polymarket/markets",
        "total_markets": 0,
        "pages_fetched": 0,
        "forex_relevant": 0,
        "sample_markets": [],
        "data_structure": {},
        "pagination_info": {},
        "errors": []
    }
    
    markets = []
    offset = 0
    limit = 100
    max_pages = 20  # Test up to 20 pages (2000 markets)
    
    for page in range(max_pages):
        print(f"\n📄 Fetching page {page + 1} (offset: {offset})...")
        
        result = make_request("/polymarket/markets", params={"limit": limit, "offset": offset})
        
        if not result["success"]:
            if result["status_code"] == 429:
                print(f"  ⚠️  Rate limit hit - stopping")
                results["errors"].append(f"Rate limit at page {page + 1}")
                break
            else:
                print(f"  ❌ Error: {result['error']}")
                results["errors"].append(f"Page {page + 1}: {result['error']}")
                break
        
        data = result["data"]
        page_markets = data.get("markets", [])
        
        if not page_markets:
            print(f"  ✅ No more markets (empty page)")
            break
        
        markets.extend(page_markets)
        results["pages_fetched"] = page + 1
        results["total_markets"] = len(markets)
        
        # Store pagination info
        if page == 0:
            results["pagination_info"] = {
                "has_pagination": "pagination" in data or "has_more" in data,
                "top_level_keys": list(data.keys())
            }
            if page_markets:
                results["data_structure"] = {
                    "market_keys": list(page_markets[0].keys()),
                    "sample_keys": {k: type(v).__name__ for k, v in list(page_markets[0].items())[:10]}
                }
        
        # Check for forex-relevant markets
        forex_count = 0
        forex_keywords = ["fed", "federal reserve", "fomc", "interest rate", "inflation", "cpi", 
                         "gdp", "employment", "nfp", "ecb", "boe", "boj", "eur/usd", "gbp/usd", "usd/jpy"]
        
        for market in page_markets:
            title = str(market.get("title", "")).lower()
            if any(keyword in title for keyword in forex_keywords):
                forex_count += 1
                if len(results["sample_markets"]) < 5:
                    results["sample_markets"].append({
                        "title": market.get("title", "")[:100],
                        "status": market.get("status", ""),
                        "platform": market.get("platform", ""),
                        "volume": market.get("volume_total") or market.get("volume", 0)
                    })
        
        results["forex_relevant"] += forex_count
        
        print(f"  ✅ Fetched {len(page_markets)} markets (Total: {len(markets)}, Forex-relevant: {results['forex_relevant']})")
        print(f"     Response time: {result['response_time_ms']:.0f}ms")
        
        # Check if there's more data
        pagination = data.get("pagination", {})
        has_more = pagination.get("has_more", False) if pagination else False
        
        if not has_more:
            print(f"  ✅ No more pages available")
            break
        
        offset += limit
    
    return results, markets

def test_kalshi_markets():
    """Test Kalshi markets endpoint"""
    print("\n" + "="*80)
    print("TESTING KALSHI MARKETS (via DOME API)")
    print("="*80)
    
    results = {
        "endpoint": "/kalshi/markets",
        "total_markets": 0,
        "pages_fetched": 0,
        "forex_relevant": 0,
        "sample_markets": [],
        "data_structure": {},
        "pagination_info": {},
        "errors": []
    }
    
    markets = []
    offset = 0
    limit = 100
    max_pages = 20  # Test up to 20 pages
    
    for page in range(max_pages):
        print(f"\n📄 Fetching page {page + 1} (offset: {offset})...")
        
        result = make_request("/kalshi/markets", params={"limit": limit, "offset": offset})
        
        if not result["success"]:
            if result["status_code"] == 429:
                print(f"  ⚠️  Rate limit hit - stopping")
                results["errors"].append(f"Rate limit at page {page + 1}")
                break
            else:
                print(f"  ❌ Error: {result['error']}")
                results["errors"].append(f"Page {page + 1}: {result['error']}")
                break
        
        data = result["data"]
        page_markets = data.get("markets", [])
        
        if not page_markets:
            print(f"  ✅ No more markets (empty page)")
            break
        
        markets.extend(page_markets)
        results["pages_fetched"] = page + 1
        results["total_markets"] = len(markets)
        
        # Store structure info
        if page == 0:
            results["pagination_info"] = {
                "has_pagination": "pagination" in data or "has_more" in data,
                "top_level_keys": list(data.keys())
            }
            if page_markets:
                results["data_structure"] = {
                    "market_keys": list(page_markets[0].keys()),
                    "sample_keys": {k: type(v).__name__ for k, v in list(page_markets[0].items())[:10]}
                }
        
        # Check for forex-relevant markets
        forex_count = 0
        forex_keywords = ["fed", "federal reserve", "fomc", "interest rate", "inflation", "cpi", 
                         "gdp", "employment", "nfp", "ecb", "boe", "boj", "eur/usd", "gbp/usd", "usd/jpy"]
        
        for market in page_markets:
            title = str(market.get("title", "")).lower()
            if any(keyword in title for keyword in forex_keywords):
                forex_count += 1
                if len(results["sample_markets"]) < 5:
                    results["sample_markets"].append({
                        "title": market.get("title", "")[:100],
                        "status": market.get("status", ""),
                        "platform": market.get("platform", "")
                    })
        
        results["forex_relevant"] += forex_count
        
        print(f"  ✅ Fetched {len(page_markets)} markets (Total: {len(markets)}, Forex-relevant: {results['forex_relevant']})")
        print(f"     Response time: {result['response_time_ms']:.0f}ms")
        
        # Check if there's more data
        pagination = data.get("pagination", {})
        has_more = pagination.get("has_more", False) if pagination else False
        
        if not has_more:
            print(f"  ✅ No more pages available")
            break
        
        offset += limit
    
    return results, markets

def test_other_endpoints():
    """Test other available DOME API endpoints"""
    print("\n" + "="*80)
    print("TESTING OTHER DOME API ENDPOINTS")
    print("="*80)
    
    endpoints_to_test = [
        "/polymarket/events",
        "/kalshi/events",
        "/polymarket/markets/market-price",  # Might need params
    ]
    
    results = {}
    
    for endpoint in endpoints_to_test:
        print(f"\n🔍 Testing: {endpoint}")
        result = make_request(endpoint)
        
        if result["success"]:
            data = result["data"]
            print(f"  ✅ Accessible")
            print(f"     Response time: {result['response_time_ms']:.0f}ms")
            print(f"     Top-level keys: {list(data.keys())[:10]}")
            results[endpoint] = {
                "accessible": True,
                "response_time_ms": result["response_time_ms"],
                "structure": list(data.keys())[:10] if isinstance(data, dict) else type(data).__name__
            }
        else:
            print(f"  ❌ Error: {result['error']}")
            results[endpoint] = {
                "accessible": False,
                "error": result["error"]
            }
    
    return results

def analyze_market_data(markets: List[Dict], platform: str):
    """Analyze fetched market data"""
    print("\n" + "="*80)
    print(f"ANALYZING {platform.upper()} MARKET DATA")
    print("="*80)
    
    if not markets:
        print("No markets to analyze")
        return {}
    
    analysis = {
        "total_markets": len(markets),
        "status_distribution": defaultdict(int),
        "platform_distribution": defaultdict(int),
        "has_volume": 0,
        "has_prices": 0,
        "has_dates": 0,
        "sample_market": markets[0] if markets else None
    }
    
    for market in markets:
        # Status distribution
        status = market.get("status", "unknown")
        analysis["status_distribution"][status] += 1
        
        # Platform
        platform_name = market.get("platform", "unknown")
        analysis["platform_distribution"][platform_name] += 1
        
        # Data availability
        if market.get("volume") or market.get("volume_total") or market.get("volume_24h"):
            analysis["has_volume"] += 1
        
        if market.get("side_a") or market.get("side_b") or market.get("last_price"):
            analysis["has_prices"] += 1
        
        if market.get("end_time") or market.get("end_date_iso") or market.get("close_time"):
            analysis["has_dates"] += 1
    
    print(f"\nTotal Markets: {analysis['total_markets']}")
    print(f"\nStatus Distribution:")
    for status, count in sorted(analysis["status_distribution"].items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")
    
    print(f"\nPlatform Distribution:")
    for platform_name, count in sorted(analysis["platform_distribution"].items(), key=lambda x: -x[1]):
        print(f"  {platform_name}: {count}")
    
    print(f"\nData Availability:")
    print(f"  Has Volume: {analysis['has_volume']} ({analysis['has_volume']/len(markets)*100:.1f}%)")
    print(f"  Has Prices: {analysis['has_prices']} ({analysis['has_prices']/len(markets)*100:.1f}%)")
    print(f"  Has Dates: {analysis['has_dates']} ({analysis['has_dates']/len(markets)*100:.1f}%)")
    
    return analysis

def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE DOME API TEST")
    print("="*80)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"API Key: {DOME_API_KEY[:20]}...")
    print(f"Rate Limit: 1 req/sec, 10 req/10sec")
    print(f"Estimated time: ~5-10 minutes for full test")
    
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "api_key_preview": DOME_API_KEY[:20] + "...",
        "polymarket": {},
        "kalshi": {},
        "other_endpoints": {},
        "summary": {}
    }
    
    # Test Polymarket
    polymarket_results, polymarket_markets = test_polymarket_markets()
    all_results["polymarket"] = polymarket_results
    polymarket_analysis = analyze_market_data(polymarket_markets, "Polymarket")
    all_results["polymarket"]["analysis"] = polymarket_analysis
    
    # Test Kalshi
    kalshi_results, kalshi_markets = test_kalshi_markets()
    all_results["kalshi"] = kalshi_results
    kalshi_analysis = analyze_market_data(kalshi_markets, "Kalshi")
    all_results["kalshi"]["analysis"] = kalshi_analysis
    
    # Test other endpoints
    other_results = test_other_endpoints()
    all_results["other_endpoints"] = other_results
    
    # Summary
    all_results["summary"] = {
        "total_polymarket_markets": len(polymarket_markets),
        "total_kalshi_markets": len(kalshi_markets),
        "total_forex_relevant": polymarket_results["forex_relevant"] + kalshi_results["forex_relevant"],
        "polymarket_forex_relevant": polymarket_results["forex_relevant"],
        "kalshi_forex_relevant": kalshi_results["forex_relevant"],
        "total_requests_made": len(rate_limiter.request_times)
    }
    
    # Print summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"\nPolymarket Markets:")
    print(f"  Total fetched: {len(polymarket_markets)}")
    print(f"  Forex-relevant: {polymarket_results['forex_relevant']}")
    print(f"  Pages fetched: {polymarket_results['pages_fetched']}")
    
    print(f"\nKalshi Markets:")
    print(f"  Total fetched: {len(kalshi_markets)}")
    print(f"  Forex-relevant: {kalshi_results['forex_relevant']}")
    print(f"  Pages fetched: {kalshi_results['pages_fetched']}")
    
    print(f"\nTotal:")
    print(f"  Markets: {len(polymarket_markets) + len(kalshi_markets)}")
    print(f"  Forex-relevant: {all_results['summary']['total_forex_relevant']}")
    print(f"  API Requests: {all_results['summary']['total_requests_made']}")
    
    # Save results
    output_file = "data/dome_api_comprehensive_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to: {output_file}")
    print(f"✅ Test completed: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()

