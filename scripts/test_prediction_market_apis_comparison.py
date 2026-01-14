#!/usr/bin/env python3
"""
Comprehensive comparison of prediction market APIs:
1. DOME API (current approach)
2. Polymarket CLOB API (direct)
3. Polymarket Gamma API (direct)
4. Kalshi API (direct - public endpoints)

Tests rate limits, data quality, and forex-relevant market availability.
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
TEST_KEYWORDS = [
    "fed", "federal reserve", "fomc", "interest rate",
    "inflation", "cpi", "gdp", "employment", "nfp",
    "ecb", "boe", "boj", "eur/usd", "gbp/usd", "usd/jpy"
]

class APITester:
    def __init__(self):
        self.results = {
            "dome_api": {},
            "polymarket_clob": {},
            "polymarket_gamma": {},
            "kalshi": {}
        }
        self.dome_api_key = os.getenv('DOME_API_KEY', '')
    
    def test_dome_api(self) -> Dict[str, Any]:
        """Test DOME API (current approach)"""
        print("\n" + "="*80)
        print("TESTING DOME API")
        print("="*80)
        
        result = {
            "accessible": False,
            "requires_auth": True,
            "rate_limit": "1 req/sec, 10 req/10sec (free tier)",
            "markets_fetched": 0,
            "forex_relevant": 0,
            "response_time_ms": 0,
            "errors": [],
            "sample_market": None,
            "data_structure": {}
        }
        
        if not self.dome_api_key:
            result["errors"].append("DOME_API_KEY not set")
            print("⚠️  DOME_API_KEY not set - skipping DOME API test")
            return result
        
        try:
            url = "https://api.domeapi.io/v1/polymarket/markets"
            headers = {"Authorization": f"Bearer {self.dome_api_key}"}
            params = {"limit": 10, "offset": 0}
            
            start_time = time.time()
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response_time = (time.time() - start_time) * 1000
            
            result["response_time_ms"] = round(response_time, 2)
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get("markets", [])
                result["accessible"] = True
                result["markets_fetched"] = len(markets)
                result["data_structure"] = {
                    "top_level_keys": list(data.keys()),
                    "market_keys": list(markets[0].keys()) if markets else []
                }
                
                # Check for forex-relevant markets
                forex_count = 0
                for market in markets:
                    title = str(market.get("title", "")).lower()
                    if any(keyword.lower() in title for keyword in TEST_KEYWORDS):
                        forex_count += 1
                        if result["sample_market"] is None:
                            result["sample_market"] = {
                                "title": market.get("title", ""),
                                "platform": market.get("platform", ""),
                                "status": market.get("status", ""),
                                "volume": market.get("volume_total") or market.get("volume", 0)
                            }
                
                result["forex_relevant"] = forex_count
                print(f"✅ DOME API accessible")
                print(f"   Markets fetched: {len(markets)}")
                print(f"   Forex-relevant: {forex_count}")
                print(f"   Response time: {response_time:.2f}ms")
                
            elif response.status_code == 429:
                result["errors"].append("Rate limit hit (429)")
                print("⚠️  Rate limit hit")
            else:
                result["errors"].append(f"HTTP {response.status_code}: {response.text[:200]}")
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            result["errors"].append(str(e))
            print(f"❌ Exception: {e}")
        
        return result
    
    def test_polymarket_clob(self) -> Dict[str, Any]:
        """Test Polymarket CLOB API (direct)"""
        print("\n" + "="*80)
        print("TESTING POLYMARKET CLOB API (DIRECT)")
        print("="*80)
        
        result = {
            "accessible": False,
            "requires_auth": False,
            "rate_limit": "Unknown (no official docs)",
            "markets_fetched": 0,
            "forex_relevant": 0,
            "response_time_ms": 0,
            "errors": [],
            "sample_market": None,
            "data_structure": {},
            "pagination_available": False
        }
        
        try:
            url = "https://clob.polymarket.com/markets"
            params = {"limit": 100}  # Test with 100 markets
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=15)
            response_time = (time.time() - start_time) * 1000
            
            result["response_time_ms"] = round(response_time, 2)
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get("data", [])
                result["accessible"] = True
                result["markets_fetched"] = len(markets)
                result["pagination_available"] = "next_cursor" in data
                result["data_structure"] = {
                    "top_level_keys": list(data.keys()),
                    "market_keys": list(markets[0].keys()) if markets else []
                }
                
                # Check for forex-relevant markets
                forex_count = 0
                for market in markets:
                    question = str(market.get("question", "")).lower()
                    description = str(market.get("description", "")).lower()
                    text = f"{question} {description}"
                    
                    if any(keyword.lower() in text for keyword in TEST_KEYWORDS):
                        forex_count += 1
                        if result["sample_market"] is None:
                            result["sample_market"] = {
                                "question": market.get("question", "")[:100],
                                "active": market.get("active", False),
                                "closed": market.get("closed", False),
                                "tokens": len(market.get("tokens", []))
                            }
                
                result["forex_relevant"] = forex_count
                print(f"✅ Polymarket CLOB API accessible")
                print(f"   Markets fetched: {len(markets)}")
                print(f"   Forex-relevant: {forex_count}")
                print(f"   Response time: {response_time:.2f}ms")
                print(f"   Pagination: {'Yes' if result['pagination_available'] else 'No'}")
                
            elif response.status_code == 429:
                result["errors"].append("Rate limit hit (429)")
                print("⚠️  Rate limit hit")
            else:
                result["errors"].append(f"HTTP {response.status_code}: {response.text[:200]}")
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            result["errors"].append(str(e))
            print(f"❌ Exception: {e}")
        
        return result
    
    def test_polymarket_gamma(self) -> Dict[str, Any]:
        """Test Polymarket Gamma API (direct)"""
        print("\n" + "="*80)
        print("TESTING POLYMARKET GAMMA API (DIRECT)")
        print("="*80)
        
        result = {
            "accessible": False,
            "requires_auth": False,
            "rate_limit": "Unknown (no official docs)",
            "markets_fetched": 0,
            "forex_relevant": 0,
            "response_time_ms": 0,
            "errors": [],
            "sample_market": None,
            "data_structure": {}
        }
        
        try:
            url = "https://gamma-api.polymarket.com/markets"
            params = {"limit": 100}
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=15)
            response_time = (time.time() - start_time) * 1000
            
            result["response_time_ms"] = round(response_time, 2)
            
            if response.status_code == 200:
                data = response.json()
                # Gamma API might return array directly or wrapped
                if isinstance(data, list):
                    markets = data
                elif isinstance(data, dict):
                    markets = data.get("data", data.get("markets", []))
                else:
                    markets = []
                
                result["accessible"] = True
                result["markets_fetched"] = len(markets)
                result["data_structure"] = {
                    "response_type": type(data).__name__,
                    "market_keys": list(markets[0].keys()) if markets else []
                }
                
                # Check for forex-relevant markets
                forex_count = 0
                for market in markets:
                    question = str(market.get("question", "")).lower()
                    title = str(market.get("title", "")).lower()
                    text = f"{question} {title}"
                    
                    if any(keyword.lower() in text for keyword in TEST_KEYWORDS):
                        forex_count += 1
                        if result["sample_market"] is None:
                            result["sample_market"] = {
                                "question": (market.get("question") or market.get("title", ""))[:100],
                                "active": market.get("active", False),
                                "liquidity": market.get("liquidity", 0)
                            }
                
                result["forex_relevant"] = forex_count
                print(f"✅ Polymarket Gamma API accessible")
                print(f"   Markets fetched: {len(markets)}")
                print(f"   Forex-relevant: {forex_count}")
                print(f"   Response time: {response_time:.2f}ms")
                
            elif response.status_code == 429:
                result["errors"].append("Rate limit hit (429)")
                print("⚠️  Rate limit hit")
            else:
                result["errors"].append(f"HTTP {response.status_code}: {response.text[:200]}")
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            result["errors"].append(str(e))
            print(f"❌ Exception: {e}")
        
        return result
    
    def test_kalshi_public(self) -> Dict[str, Any]:
        """Test Kalshi public endpoints (no auth required)"""
        print("\n" + "="*80)
        print("TESTING KALSHI PUBLIC API (DIRECT)")
        print("="*80)
        
        result = {
            "accessible": False,
            "requires_auth": False,
            "rate_limit": "Unknown",
            "markets_fetched": 0,
            "forex_relevant": 0,
            "response_time_ms": 0,
            "errors": [],
            "sample_market": None,
            "data_structure": {},
            "endpoints_tested": []
        }
        
        # Test public endpoints according to Kalshi docs
        endpoints = [
            "https://api.kalshi.com/trade-api/v2/events",
            "https://api.kalshi.com/trade-api/v2/markets",
            "https://api.kalshi.com/trade-api/v2/exchange/status"
        ]
        
        for endpoint in endpoints:
            try:
                print(f"\nTesting: {endpoint}")
                start_time = time.time()
                response = requests.get(endpoint, timeout=15)
                response_time = (time.time() - start_time) * 1000
                
                endpoint_result = {
                    "url": endpoint,
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2),
                    "accessible": response.status_code == 200
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        endpoint_result["data_structure"] = {
                            "top_level_keys": list(data.keys()) if isinstance(data, dict) else "array",
                            "response_type": type(data).__name__
                        }
                        
                        # Try to extract markets/events
                        if isinstance(data, dict):
                            markets = data.get("markets", data.get("events", []))
                        elif isinstance(data, list):
                            markets = data
                        else:
                            markets = []
                        
                        if markets:
                            endpoint_result["markets_fetched"] = len(markets)
                            result["markets_fetched"] += len(markets)
                            
                            # Check for forex-relevant
                            forex_count = 0
                            for market in markets[:50]:  # Sample first 50
                                title = str(market.get("title", market.get("event_ticker", ""))).lower()
                                if any(keyword.lower() in title for keyword in TEST_KEYWORDS):
                                    forex_count += 1
                                    if result["sample_market"] is None:
                                        result["sample_market"] = {
                                            "title": market.get("title", market.get("event_ticker", ""))[:100],
                                            "status": market.get("status", "")
                                        }
                            
                            endpoint_result["forex_relevant"] = forex_count
                            result["forex_relevant"] += forex_count
                        
                        result["accessible"] = True
                        print(f"   ✅ Accessible - {len(markets) if 'markets' in locals() else 0} items")
                        
                    except json.JSONDecodeError:
                        endpoint_result["error"] = "Invalid JSON response"
                        print(f"   ⚠️  Invalid JSON")
                        
                elif response.status_code == 401:
                    endpoint_result["error"] = "Authentication required"
                    print(f"   ⚠️  Requires authentication")
                elif response.status_code == 403:
                    endpoint_result["error"] = "Forbidden"
                    print(f"   ⚠️  Forbidden (403)")
                else:
                    endpoint_result["error"] = f"HTTP {response.status_code}"
                    print(f"   ❌ Error: {response.status_code}")
                
                result["endpoints_tested"].append(endpoint_result)
                
            except requests.exceptions.Timeout:
                result["errors"].append(f"Timeout: {endpoint}")
                print(f"   ❌ Timeout")
            except requests.exceptions.ConnectionError as e:
                result["errors"].append(f"Connection error: {endpoint} - {str(e)}")
                print(f"   ❌ Connection error: {e}")
            except Exception as e:
                result["errors"].append(f"Exception: {endpoint} - {str(e)}")
                print(f"   ❌ Exception: {e}")
        
        if result["accessible"]:
            result["response_time_ms"] = sum(e.get("response_time_ms", 0) for e in result["endpoints_tested"]) / len(result["endpoints_tested"])
            print(f"\n✅ Kalshi API accessible from your location")
        else:
            print(f"\n❌ Kalshi API not accessible (may be geo-blocked or require auth)")
        
        return result
    
    def test_rate_limits(self):
        """Test rate limits by making multiple rapid requests"""
        print("\n" + "="*80)
        print("TESTING RATE LIMITS")
        print("="*80)
        
        # Test Polymarket CLOB rate limits
        print("\nTesting Polymarket CLOB rate limits (5 rapid requests)...")
        clob_times = []
        for i in range(5):
            try:
                start = time.time()
                response = requests.get("https://clob.polymarket.com/markets", params={"limit": 10}, timeout=10)
                elapsed = (time.time() - start) * 1000
                clob_times.append(elapsed)
                print(f"  Request {i+1}: {response.status_code} ({elapsed:.0f}ms)")
                if response.status_code == 429:
                    print("  ⚠️  Rate limit hit!")
                    break
                time.sleep(0.2)  # Small delay
            except Exception as e:
                print(f"  Request {i+1}: Error - {e}")
        
        return {
            "polymarket_clob": {
                "avg_response_time_ms": sum(clob_times) / len(clob_times) if clob_times else 0,
                "rate_limit_hit": any(t > 1000 for t in clob_times)  # Heuristic
            }
        }
    
    def run_all_tests(self):
        """Run all API tests"""
        print("\n" + "="*80)
        print("PREDICTION MARKET API COMPARISON TEST")
        print("="*80)
        print(f"Test started: {datetime.now().isoformat()}")
        print(f"Testing keywords: {', '.join(TEST_KEYWORDS[:5])}...")
        
        # Run tests
        self.results["dome_api"] = self.test_dome_api()
        time.sleep(1)  # Rate limit consideration
        
        self.results["polymarket_clob"] = self.test_polymarket_clob()
        time.sleep(1)
        
        self.results["polymarket_gamma"] = self.test_polymarket_gamma()
        time.sleep(1)
        
        self.results["kalshi"] = self.test_kalshi_public()
        
        # Test rate limits
        rate_limit_results = self.test_rate_limits()
        
        # Generate summary
        self.print_summary()
        
        # Save results
        output_file = "data/prediction_market_api_comparison_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results,
                "rate_limit_tests": rate_limit_results
            }, f, indent=2)
        
        print(f"\n✅ Results saved to: {output_file}")
    
    def print_summary(self):
        """Print comparison summary"""
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        
        summary_data = []
        for api_name, result in self.results.items():
            summary_data.append({
                "api": api_name.replace("_", " ").title(),
                "accessible": result.get("accessible", False),
                "auth_required": result.get("requires_auth", False),
                "markets": result.get("markets_fetched", 0),
                "forex_relevant": result.get("forex_relevant", 0),
                "response_time_ms": result.get("response_time_ms", 0),
                "rate_limit": result.get("rate_limit", "Unknown")
            })
        
        # Print table
        print(f"\n{'API':<25} {'Accessible':<12} {'Auth':<8} {'Markets':<10} {'Forex':<10} {'Time(ms)':<12} {'Rate Limit':<20}")
        print("-" * 100)
        for data in summary_data:
            accessible = "✅ Yes" if data["accessible"] else "❌ No"
            auth = "Yes" if data["auth_required"] else "No"
            print(f"{data['api']:<25} {accessible:<12} {auth:<8} {data['markets']:<10} {data['forex_relevant']:<10} {data['response_time_ms']:<12.1f} {data['rate_limit']:<20}")
        
        # Recommendations
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        
        accessible_apis = [d for d in summary_data if d["accessible"]]
        
        if not accessible_apis:
            print("❌ No APIs are currently accessible. Check network/authentication.")
            return
        
        # Find best option
        best = max(accessible_apis, key=lambda x: (x["forex_relevant"], -x["response_time_ms"]))
        
        print(f"\n🏆 Best Option: {best['api']}")
        print(f"   - Forex-relevant markets: {best['forex_relevant']}")
        print(f"   - Response time: {best['response_time_ms']:.1f}ms")
        print(f"   - Auth required: {best['auth_required']}")
        
        if best["api"] == "Polymarket Clob":
            print("\n💡 Recommendation: Use Polymarket CLOB API directly")
            print("   - No authentication required")
            print("   - Good forex market coverage")
            print("   - Faster than DOME API")
            print("   - No rate limit restrictions (within reason)")
        elif best["api"] == "Dome Api":
            print("\n💡 Recommendation: Continue using DOME API")
            print("   - Already integrated")
            print("   - Unified interface for multiple platforms")
            print("   - Consider upgrading to paid tier for better limits")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()

