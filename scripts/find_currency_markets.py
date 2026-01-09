#!/usr/bin/env python3
"""
Fetch Polymarket data and search for currency/forex related markets
"""

import requests
import json
from datetime import datetime

def fetch_all_markets():
    """Fetch markets from Polymarket and search for currency-related ones"""
    
    print("Fetching markets from Polymarket...")
    
    # Fetch from CLOB API (has pagination)
    clob_markets = []
    cursor = None
    max_pages = 5  # Limit to avoid too many requests
    
    print("\n📊 Fetching from CLOB API...")
    for page in range(max_pages):
        url = "https://clob.polymarket.com/markets"
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
            
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                markets = data.get("data", [])
                clob_markets.extend(markets)
                cursor = data.get("next_cursor")
                print(f"  Page {page + 1}: Fetched {len(markets)} markets (Total: {len(clob_markets)})")
                if not cursor:
                    break
            else:
                print(f"  Error: {response.status_code}")
                break
        except Exception as e:
            print(f"  Error: {e}")
            break
    
    # Fetch from Gamma API
    print("\n📊 Fetching from Gamma API...")
    gamma_markets = []
    try:
        response = requests.get("https://gamma-api.polymarket.com/markets", timeout=10)
        if response.status_code == 200:
            gamma_markets = response.json()
            print(f"  Fetched {len(gamma_markets)} markets")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Search for currency-related markets
    currency_keywords = [
        "EUR", "USD", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD",
        "euro", "dollar", "pound", "yen", "forex", "currency",
        "exchange rate", "FX", "EUR/USD", "GBP/USD", "USD/JPY",
        "Federal Reserve", "Fed", "ECB", "Bank of England", "BOJ",
        "interest rate", "inflation", "CPI", "GDP"
    ]
    
    print("\n🔍 Searching for currency/forex related markets...")
    
    currency_markets_clob = []
    for market in clob_markets:
        question = market.get("question", "").lower()
        description = market.get("description", "").lower()
        text = f"{question} {description}"
        
        for keyword in currency_keywords:
            if keyword.lower() in text:
                currency_markets_clob.append({
                    "source": "CLOB",
                    "question": market.get("question"),
                    "description": market.get("description", "")[:200],
                    "active": market.get("active"),
                    "closed": market.get("closed"),
                    "condition_id": market.get("condition_id"),
                    "matched_keyword": keyword
                })
                break
    
    currency_markets_gamma = []
    for market in gamma_markets:
        question = market.get("question", "").lower()
        title = market.get("title", "").lower() if isinstance(market.get("title"), str) else ""
        description = market.get("description", "").lower() if isinstance(market.get("description"), str) else ""
        text = f"{question} {title} {description}"
        
        for keyword in currency_keywords:
            if keyword.lower() in text:
                currency_markets_gamma.append({
                    "source": "Gamma",
                    "question": market.get("question") or market.get("title"),
                    "description": market.get("description", "")[:200] if isinstance(market.get("description"), str) else "",
                    "end_date": market.get("endDate"),
                    "category": market.get("category"),
                    "liquidity": market.get("liquidity"),
                    "id": market.get("id"),
                    "matched_keyword": keyword
                })
                break
    
    print(f"\n✅ Found {len(currency_markets_clob)} currency markets in CLOB API")
    print(f"✅ Found {len(currency_markets_gamma)} currency markets in Gamma API")
    
    # Display sample markets
    print("\n" + "="*80)
    print("SAMPLE CURRENCY MARKETS FROM CLOB API")
    print("="*80)
    for i, market in enumerate(currency_markets_clob[:10], 1):
        print(f"\n{i}. {market['question']}")
        print(f"   Keyword: {market['matched_keyword']}")
        print(f"   Active: {market['active']}, Closed: {market['closed']}")
        if market['description']:
            print(f"   Description: {market['description'][:150]}...")
    
    print("\n" + "="*80)
    print("SAMPLE CURRENCY MARKETS FROM GAMMA API")
    print("="*80)
    for i, market in enumerate(currency_markets_gamma[:10], 1):
        print(f"\n{i}. {market['question']}")
        print(f"   Keyword: {market['matched_keyword']}")
        print(f"   Category: {market.get('category', 'N/A')}")
        print(f"   Liquidity: {market.get('liquidity', 'N/A')}")
        if market['description']:
            print(f"   Description: {market['description'][:150]}...")
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_clob_markets": len(clob_markets),
        "total_gamma_markets": len(gamma_markets),
        "currency_markets_clob": currency_markets_clob,
        "currency_markets_gamma": currency_markets_gamma,
        "total_currency_markets": len(currency_markets_clob) + len(currency_markets_gamma)
    }
    
    with open("data/polymarket_currency_markets.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to: data/polymarket_currency_markets.json")
    
    return results

if __name__ == "__main__":
    fetch_all_markets()

