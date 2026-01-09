#!/usr/bin/env python3
"""
Test script to evaluate prediction market APIs:
- Polymarket (GraphQL Subgraph)
- Kalshi (REST API)
- Unified APIs (Predexon, PolyRouter)

This script tests what data is available and helps decide which API to use.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# ANSI colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text: str):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(text: str):
    print(f"{GREEN}✅ {text}{RESET}")

def print_warning(text: str):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_error(text: str):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text: str):
    print(f"{BLUE}ℹ️  {text}{RESET}")

# ============================================================================
# POLYMARKET API TESTS
# ============================================================================

def test_polymarket_graphql():
    """Test Polymarket GraphQL Subgraph API"""
    print_header("TESTING POLYMARKET GRAPHQL SUBGRAPH")
    
    # Polymarket subgraph endpoint (public)
    subgraph_url = "https://api.thegraph.com/subgraphs/name/polymarket/polymarket"
    
    # Query to get markets related to currencies/forex
    currency_keywords = ["EUR", "USD", "GBP", "JPY", "forex", "currency", "dollar", "euro", "pound"]
    
    queries = [
        {
            "name": "Recent Markets",
            "query": """
            {
                markets(first: 10, orderBy: volume, orderDirection: desc) {
                    id
                    question
                    volume
                    liquidity
                    endDate
                    outcomes {
                        id
                        title
                        price
                    }
                }
            }
            """
        },
        {
            "name": "Currency-Related Markets",
            "query": """
            {
                markets(
                    first: 20,
                    where: {
                        question_contains_nocase: "EUR"
                    },
                    orderBy: volume,
                    orderDirection: desc
                ) {
                    id
                    question
                    volume
                    liquidity
                    endDate
                    outcomes {
                        id
                        title
                        price
                    }
                }
            }
            """
        },
        {
            "name": "USD-Related Markets",
            "query": """
            {
                markets(
                    first: 20,
                    where: {
                        question_contains_nocase: "USD"
                    },
                    orderBy: volume,
                    orderDirection: desc
                ) {
                    id
                    question
                    volume
                    liquidity
                    endDate
                    outcomes {
                        id
                        title
                        price
                    }
                }
            }
            """
        }
    ]
    
    results = {
        "api_name": "Polymarket GraphQL Subgraph",
        "endpoint": subgraph_url,
        "authentication_required": False,
        "tests_passed": 0,
        "tests_failed": 0,
        "markets_found": [],
        "currency_markets": [],
        "errors": []
    }
    
    try:
        for query_info in queries:
            print_info(f"Testing: {query_info['name']}")
            try:
                response = requests.post(
                    subgraph_url,
                    json={"query": query_info["query"]},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "errors" in data:
                        print_error(f"GraphQL errors: {data['errors']}")
                        results["errors"].extend(data["errors"])
                    elif "data" in data and "markets" in data["data"]:
                        markets = data["data"]["markets"]
                        print_success(f"Found {len(markets)} markets")
                        results["tests_passed"] += 1
                        
                        if "Currency" in query_info["name"] or "USD" in query_info["name"]:
                            results["currency_markets"].extend(markets)
                        else:
                            results["markets_found"].extend(markets)
                        
                        # Print sample markets
                        for i, market in enumerate(markets[:3], 1):
                            print(f"  {i}. {market.get('question', 'N/A')[:80]}")
                            print(f"     Volume: {market.get('volume', 'N/A')}, Liquidity: {market.get('liquidity', 'N/A')}")
                    else:
                        print_warning(f"Unexpected response structure: {data}")
                        results["tests_failed"] += 1
                else:
                    print_error(f"HTTP {response.status_code}: {response.text[:200]}")
                    results["tests_failed"] += 1
                    results["errors"].append(f"HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print_error(f"Request failed: {str(e)}")
                results["tests_failed"] += 1
                results["errors"].append(str(e))
            
            print()
    
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        results["errors"].append(str(e))
    
    return results

def test_polymarket_rest_api():
    """Test Polymarket REST API (if available)"""
    print_header("TESTING POLYMARKET REST API")
    
    # Polymarket may have REST endpoints - testing common patterns
    base_urls = [
        "https://api.polymarket.com",
        "https://clob.polymarket.com",
        "https://gamma-api.polymarket.com"
    ]
    
    results = {
        "api_name": "Polymarket REST API",
        "endpoints_tested": [],
        "authentication_required": None,
        "accessible": False,
        "errors": []
    }
    
    for base_url in base_urls:
        print_info(f"Testing: {base_url}")
        try:
            # Try common endpoints
            endpoints = ["/markets", "/events", "/health", "/v1/markets"]
            
            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"
                try:
                    response = requests.get(url, timeout=5)
                    results["endpoints_tested"].append({
                        "url": url,
                        "status": response.status_code,
                        "requires_auth": response.status_code == 401
                    })
                    
                    if response.status_code == 200:
                        print_success(f"  {endpoint}: Accessible (200)")
                        results["accessible"] = True
                    elif response.status_code == 401:
                        print_warning(f"  {endpoint}: Requires authentication (401)")
                        results["authentication_required"] = True
                    elif response.status_code == 404:
                        print_info(f"  {endpoint}: Not found (404)")
                    else:
                        print_info(f"  {endpoint}: Status {response.status_code}")
                        
                except requests.exceptions.RequestException:
                    pass
                    
        except Exception as e:
            results["errors"].append(str(e))
    
    return results

# ============================================================================
# KALSHI API TESTS
# ============================================================================

def test_kalshi_api():
    """Test Kalshi API (will likely require authentication)"""
    print_header("TESTING KALSHI API")
    
    base_url = "https://api.kalshi.com/trade-api/v2"
    
    results = {
        "api_name": "Kalshi REST API",
        "base_url": base_url,
        "authentication_required": None,
        "public_endpoints": [],
        "errors": []
    }
    
    # Test public endpoints (if any)
    endpoints = [
        "/events",
        "/markets",
        "/exchange/status",
        "/portfolio/balance"  # This will definitely require auth
    ]
    
    print_info("Testing public endpoints (may require authentication)...")
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print_success(f"{endpoint}: Accessible without authentication")
                results["public_endpoints"].append(endpoint)
                try:
                    data = response.json()
                    print(f"  Response sample: {json.dumps(data, indent=2)[:200]}")
                except:
                    pass
            elif response.status_code == 401:
                print_warning(f"{endpoint}: Requires authentication (401)")
                results["authentication_required"] = True
            elif response.status_code == 403:
                print_warning(f"{endpoint}: Forbidden (403) - likely requires authentication")
                results["authentication_required"] = True
            else:
                print_info(f"{endpoint}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print_error(f"{endpoint}: Request failed - {str(e)}")
            results["errors"].append(f"{endpoint}: {str(e)}")
    
    return results

# ============================================================================
# UNIFIED API TESTS
# ============================================================================

def test_predexon_api():
    """Test Predexon unified API"""
    print_header("TESTING PREDEXON UNIFIED API")
    
    results = {
        "api_name": "Predexon",
        "accessible": False,
        "authentication_required": None,
        "errors": []
    }
    
    # Predexon API endpoint (need to check actual endpoint)
    base_urls = [
        "https://api.predexon.com",
        "https://predexon.com/api"
    ]
    
    for base_url in base_urls:
        print_info(f"Testing: {base_url}")
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print_success("Predexon API accessible")
                results["accessible"] = True
            elif response.status_code == 401:
                print_warning("Predexon API requires authentication")
                results["authentication_required"] = True
        except:
            pass
    
    return results

def test_polyrouter_api():
    """Test PolyRouter unified API"""
    print_header("TESTING POLYROUTER UNIFIED API")
    
    results = {
        "api_name": "PolyRouter",
        "accessible": False,
        "authentication_required": None,
        "errors": []
    }
    
    # PolyRouter API endpoint
    base_urls = [
        "https://api.polyrouter.io",
        "https://polyrouter.io/api"
    ]
    
    for base_url in base_urls:
        print_info(f"Testing: {base_url}")
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print_success("PolyRouter API accessible")
                results["accessible"] = True
            elif response.status_code == 401:
                print_warning("PolyRouter API requires authentication")
                results["authentication_required"] = True
        except:
            pass
    
    return results

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all API tests and generate summary"""
    print_header("PREDICTION MARKETS API EVALUATION")
    print_info("Testing available APIs to determine best option for FXSentinel")
    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    all_results = {}
    
    # Test Polymarket GraphQL (most likely to work)
    polymarket_graphql_results = test_polymarket_graphql()
    all_results["polymarket_graphql"] = polymarket_graphql_results
    
    # Test Polymarket REST
    polymarket_rest_results = test_polymarket_rest_api()
    all_results["polymarket_rest"] = polymarket_rest_results
    
    # Test Kalshi
    kalshi_results = test_kalshi_api()
    all_results["kalshi"] = kalshi_results
    
    # Test Unified APIs
    predexon_results = test_predexon_api()
    all_results["predexon"] = predexon_results
    
    polyrouter_results = test_polyrouter_api()
    all_results["polyrouter"] = polyrouter_results
    
    # Generate summary
    print_header("TEST SUMMARY & RECOMMENDATIONS")
    
    # Polymarket GraphQL Summary
    print(f"\n{BLUE}POLYMARKET GRAPHQL SUBGRAPH{RESET}")
    print(f"  Status: {'✅ Accessible' if polymarket_graphql_results['tests_passed'] > 0 else '❌ Not accessible'}")
    print(f"  Authentication Required: {'No' if not polymarket_graphql_results['authentication_required'] else 'Yes'}")
    print(f"  Currency Markets Found: {len(polymarket_graphql_results['currency_markets'])}")
    print(f"  Total Markets Found: {len(polymarket_graphql_results['markets_found']) + len(polymarket_graphql_results['currency_markets'])}")
    
    # Kalshi Summary
    print(f"\n{BLUE}KALSHI API{RESET}")
    print(f"  Status: {'✅ Some endpoints accessible' if kalshi_results['public_endpoints'] else '⚠️ Requires authentication'}")
    print(f"  Authentication Required: {'Yes' if kalshi_results['authentication_required'] else 'Unknown'}")
    print(f"  Public Endpoints: {len(kalshi_results['public_endpoints'])}")
    
    # Unified APIs Summary
    print(f"\n{BLUE}UNIFIED APIs{RESET}")
    print(f"  Predexon: {'✅ Accessible' if predexon_results['accessible'] else '❌ Not tested/accessible'}")
    print(f"  PolyRouter: {'✅ Accessible' if polyrouter_results['accessible'] else '❌ Not tested/accessible'}")
    
    # Recommendations
    print_header("RECOMMENDATIONS")
    
    if polymarket_graphql_results['tests_passed'] > 0:
        print_success("RECOMMENDED: Start with Polymarket GraphQL Subgraph")
        print("  Reasons:")
        print("  - No authentication required for public data")
        print("  - GraphQL provides flexible queries")
        print("  - Found currency-related markets")
        print("  - Easy to integrate")
        print("\n  Next Steps:")
        print("  1. Test filtering for EUR/USD/GBP/JPY markets")
        print("  2. Implement backend service using GraphQL queries")
        print("  3. Add caching layer (5-10 min intervals)")
        print("  4. Create frontend card component")
    
    if kalshi_results['authentication_required']:
        print_warning("KALSHI: Requires setup but offers official support")
        print("  Reasons:")
        print("  - Official Python SDK available")
        print("  - Well-documented REST API")
        print("  - US-regulated platform")
        print("\n  Next Steps:")
        print("  1. Sign up for Kalshi account")
        print("  2. Generate API keys")
        print("  3. Set up RSA-PSS authentication")
        print("  4. Test market data endpoints")
    
    # Save results to file
    output_file = "data/prediction_markets_api_test_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print_success(f"\nResults saved to: {output_file}")
    except Exception as e:
        print_error(f"Failed to save results: {e}")
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Testing complete!{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

if __name__ == "__main__":
    main()

