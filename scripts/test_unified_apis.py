#!/usr/bin/env python3
"""
Test script for PropheSeer and PolyRouter unified APIs
Evaluates data quality and relevance for forex traders
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_env = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
if os.path.exists(backend_env):
    load_dotenv(backend_env)
    print(f"Loaded environment from: {backend_env}")
else:
    # Try root .env
    root_env = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(root_env):
        load_dotenv(root_env)
        print(f"Loaded environment from: {root_env}")

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.propheseer_api_client import PropheSeerAPIClient
from services.polyrouter_api_client import PolyRouterAPIClient

# ANSI colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
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

def print_data(text: str):
    print(f"{CYAN}{text}{RESET}")

def analyze_market_relevance(markets: List[Dict], source_name: str) -> Dict[str, Any]:
    """Analyze markets for forex/economic relevance"""
    
    # Keywords that indicate forex relevance
    forex_keywords = [
        "fed", "fomc", "federal reserve", "interest rate", "rate hike", "rate cut",
        "cpi", "inflation", "gdp", "nfp", "employment", "unemployment",
        "ecb", "european central bank", "boe", "bank of england",
        "boj", "bank of japan", "rba", "rbnz", "boc", "snb",
        "eur", "usd", "gbp", "jpy", "chf", "aud", "nzd", "cad",
        "forex", "currency", "exchange rate", "central bank", "monetary policy"
    ]
    
    total = len(markets)
    relevant = 0
    has_prices = 0
    open_markets = 0
    platforms = set()
    categories = set()
    
    sample_relevant = []
    
    for market in markets:
        question = (market.get("question") or market.get("title") or "").lower()
        status = market.get("status", "").lower()
        platform = market.get("platform") or market.get("source", "unknown")
        
        platforms.add(platform)
        if market.get("category"):
            categories.add(market.get("category"))
        
        if status == "open":
            open_markets += 1
        
        yes_price = market.get("yes_price")
        no_price = market.get("no_price")
        if yes_price is not None or no_price is not None:
            has_prices += 1
        
        # Check for forex relevance
        is_relevant = any(keyword in question for keyword in forex_keywords)
        if is_relevant:
            relevant += 1
            if len(sample_relevant) < 5:
                sample_relevant.append({
                    "question": market.get("question") or market.get("title", "N/A")[:80],
                    "platform": platform,
                    "yes_price": yes_price,
                    "no_price": no_price,
                    "status": status,
                    "volume": market.get("volume")
                })
    
    return {
        "total_markets": total,
        "relevant_markets": relevant,
        "relevance_percentage": (relevant / total * 100) if total > 0 else 0,
        "has_prices": has_prices,
        "price_coverage": (has_prices / total * 100) if total > 0 else 0,
        "open_markets": open_markets,
        "platforms": list(platforms),
        "categories": list(categories),
        "sample_relevant": sample_relevant
    }

def test_propheseer():
    """Test PropheSeer API"""
    print_header("TESTING PROPHESEER API")
    
    client = PropheSeerAPIClient()
    
    if not client.available:
        print_error("PropheSeer API not available (check PROPHESEER_API_KEY)")
        return None
    
    print_success("PropheSeer API client initialized")
    
    # Test fetching markets - focus on financial and political
    print_info("Fetching financial markets from PropheSeer...")
    try:
        financial_markets = client.get_markets(status="open", category="finance", limit=50)
        print_info("Fetching political markets from PropheSeer...")
        political_markets = client.get_markets(status="open", category="politics", limit=50)
        
        # Combine and deduplicate
        all_markets = financial_markets + political_markets
        # Simple deduplication by ID
        seen_ids = set()
        markets = []
        for m in all_markets:
            market_id = m.get("id")
            if market_id and market_id not in seen_ids:
                seen_ids.add(market_id)
                markets.append(m)
        
        if not markets:
            print_warning("No markets returned from PropheSeer")
            return None
        
        print_success(f"Fetched {len(markets)} markets from PropheSeer")
        
        # Show sample market structure
        if markets:
            print_info("\nSample market structure:")
            sample = markets[0]
            print_data(json.dumps(sample, indent=2, default=str)[:500])
        
        # Normalize a few markets
        print_info("\nNormalizing markets...")
        normalized = []
        for market in markets[:10]:  # Normalize first 10
            try:
                norm = client.normalize_market(market)
                normalized.append(norm)
            except Exception as e:
                print_warning(f"Failed to normalize market: {e}")
        
        if normalized:
            print_success(f"Successfully normalized {len(normalized)} markets")
            print_info("\nSample normalized market:")
            print_data(json.dumps(normalized[0], indent=2, default=str))
        
        # Analyze relevance
        print_info("\nAnalyzing market relevance for forex traders...")
        analysis = analyze_market_relevance(normalized if normalized else markets, "PropheSeer")
        
        print(f"\n{BLUE}Analysis Results:{RESET}")
        print(f"  Total Markets: {analysis['total_markets']}")
        print(f"  Forex/Economic Relevant: {analysis['relevant_markets']} ({analysis['relevance_percentage']:.1f}%)")
        print(f"  Markets with Prices: {analysis['has_prices']} ({analysis['price_coverage']:.1f}%)")
        print(f"  Open Markets: {analysis['open_markets']}")
        print(f"  Platforms: {', '.join(analysis['platforms'])}")
        if analysis['categories']:
            print(f"  Categories: {', '.join(list(analysis['categories'])[:10])}")
        
        if analysis['sample_relevant']:
            print(f"\n{CYAN}Sample Relevant Markets:{RESET}")
            for i, market in enumerate(analysis['sample_relevant'], 1):
                print(f"  {i}. {market['question']}")
                print(f"     Platform: {market['platform']}, Status: {market['status']}")
                if market['yes_price'] or market['no_price']:
                    print(f"     Prices: YES={market['yes_price']}, NO={market['no_price']}")
                if market.get('volume'):
                    print(f"     Volume: {market['volume']}")
        
        return {
            "success": True,
            "markets_fetched": len(markets),
            "markets_normalized": len(normalized),
            "analysis": analysis,
            "sample_market": markets[0] if markets else None,
            "sample_normalized": normalized[0] if normalized else None
        }
        
    except Exception as e:
        print_error(f"Error testing PropheSeer: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_polyrouter():
    """Test PolyRouter API"""
    print_header("TESTING POLYROUTER API")
    
    client = PolyRouterAPIClient()
    
    if not client.available:
        print_error("PolyRouter API not available (check POLYROUTER_API_KEY)")
        return None
    
    print_success("PolyRouter API client initialized")
    
    # Test fetching markets - filter for financial/political by searching
    print_info("Fetching markets from PolyRouter (Polymarket platform)...")
    try:
        # Try fetching from Polymarket first (most likely to have financial/political)
        polymarket_markets = client.get_markets(platform="polymarket", limit=100)
        print_info(f"Fetched {len(polymarket_markets)} markets from Polymarket")
        
        # Also try Kalshi (US-regulated, often has economic markets)
        print_info("Fetching markets from PolyRouter (Kalshi platform)...")
        kalshi_markets = client.get_markets(platform="kalshi", limit=100)
        print_info(f"Fetched {len(kalshi_markets)} markets from Kalshi")
        
        all_markets = polymarket_markets + kalshi_markets
        
        # Filter for financial/political keywords
        financial_keywords = ["fed", "fomc", "rate", "inflation", "cpi", "gdp", "economic", "finance", "bank", "dollar", "eur", "usd", "gbp", "jpy", "interest", "employment", "nfp", "unemployment", "central bank", "ecb", "boe", "boj"]
        political_keywords = ["election", "trump", "biden", "president", "congress", "senate", "vote", "politics", "policy", "republican", "democrat", "2024", "2025", "2026"]
        
        financial_markets = []
        political_markets = []
        
        for market in all_markets:
            title = (market.get("title") or market.get("question") or "").lower()
            description = (market.get("description") or "").lower()
            text = f"{title} {description}"
            
            is_financial = any(kw in text for kw in financial_keywords)
            is_political = any(kw in text for kw in political_keywords)
            
            if is_financial:
                financial_markets.append(market)
            if is_political:
                political_markets.append(market)
        
        # Combine and deduplicate
        all_relevant = financial_markets + political_markets
        seen_ids = set()
        markets = []
        for m in all_relevant:
            m_id = m.get("id")
            if m_id and m_id not in seen_ids:
                seen_ids.add(m_id)
                markets.append(m)
        
        print_info(f"Found {len(financial_markets)} financial markets, {len(political_markets)} political markets")
        print_info(f"Total unique financial/political markets: {len(markets)} from {len(all_markets)} total")
        
        if not markets:
            print_warning("No markets returned from PolyRouter")
            return None
        
        print_success(f"Fetched {len(markets)} markets from PolyRouter")
        
        # Show sample market structure
        if markets:
            print_info("\nSample market structure:")
            sample = markets[0]
            print_data(json.dumps(sample, indent=2, default=str)[:500])
        
        # Normalize a few markets
        print_info("\nNormalizing markets...")
        normalized = []
        for market in markets[:10]:  # Normalize first 10
            try:
                norm = client.normalize_market(market)
                normalized.append(norm)
            except Exception as e:
                print_warning(f"Failed to normalize market: {e}")
        
        if normalized:
            print_success(f"Successfully normalized {len(normalized)} markets")
            print_info("\nSample normalized market:")
            print_data(json.dumps(normalized[0], indent=2, default=str))
        
        # Analyze relevance
        print_info("\nAnalyzing market relevance for forex traders...")
        analysis = analyze_market_relevance(normalized if normalized else markets, "PolyRouter")
        
        print(f"\n{BLUE}Analysis Results:{RESET}")
        print(f"  Total Markets: {analysis['total_markets']}")
        print(f"  Forex/Economic Relevant: {analysis['relevant_markets']} ({analysis['relevance_percentage']:.1f}%)")
        print(f"  Markets with Prices: {analysis['has_prices']} ({analysis['price_coverage']:.1f}%)")
        print(f"  Open Markets: {analysis['open_markets']}")
        print(f"  Platforms: {', '.join(analysis['platforms'])}")
        if analysis['categories']:
            print(f"  Categories: {', '.join(list(analysis['categories'])[:10])}")
        
        if analysis['sample_relevant']:
            print(f"\n{CYAN}Sample Relevant Markets:{RESET}")
            for i, market in enumerate(analysis['sample_relevant'], 1):
                print(f"  {i}. {market['question']}")
                print(f"     Platform: {market['platform']}, Status: {market['status']}")
                if market['yes_price'] or market['no_price']:
                    print(f"     Prices: YES={market['yes_price']}, NO={market['no_price']}")
                if market.get('volume'):
                    print(f"     Volume: {market['volume']}")
        
        # Test price history if available
        if normalized:
            print_info("\nTesting price history endpoint...")
            market_ids = [m.get("id") for m in normalized[:3] if m.get("id")]
            if market_ids:
                try:
                    history = client.get_price_history(market_ids)
                    if history:
                        print_success(f"Price history available for {len(history)} markets")
                        for market_id, data_points in list(history.items())[:1]:
                            print_data(f"  Market {market_id}: {len(data_points)} data points")
                            if data_points:
                                print_data(f"    Sample: {json.dumps(data_points[0], indent=4, default=str)[:200]}")
                    else:
                        print_warning("Price history endpoint returned no data")
                except Exception as e:
                    print_warning(f"Price history test failed: {e}")
        
        return {
            "success": True,
            "markets_fetched": len(markets),
            "markets_normalized": len(normalized),
            "analysis": analysis,
            "sample_market": markets[0] if markets else None,
            "sample_normalized": normalized[0] if normalized else None
        }
        
    except Exception as e:
        print_error(f"Error testing PolyRouter: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_apis(propheseer_result: Dict, polyrouter_result: Dict):
    """Compare the two APIs"""
    print_header("API COMPARISON & RECOMMENDATIONS")
    
    if not propheseer_result and not polyrouter_result:
        print_error("Both APIs failed - cannot compare")
        return
    
    print(f"\n{CYAN}Data Quality Comparison:{RESET}\n")
    
    if propheseer_result:
        ps = propheseer_result['analysis']
        print(f"{BLUE}PropheSeer:{RESET}")
        print(f"  Markets: {ps['total_markets']}")
        print(f"  Relevance: {ps['relevance_percentage']:.1f}%")
        print(f"  Price Coverage: {ps['price_coverage']:.1f}%")
        print(f"  Platforms: {len(ps['platforms'])}")
    
    if polyrouter_result:
        pr = polyrouter_result['analysis']
        print(f"\n{BLUE}PolyRouter:{RESET}")
        print(f"  Markets: {pr['total_markets']}")
        print(f"  Relevance: {pr['relevance_percentage']:.1f}%")
        print(f"  Price Coverage: {pr['price_coverage']:.1f}%")
        print(f"  Platforms: {len(pr['platforms'])}")
    
    print(f"\n{CYAN}Recommendations for FXSentinel:{RESET}\n")
    
    recommendations = []
    
    if propheseer_result and polyrouter_result:
        ps_rel = propheseer_result['analysis']['relevance_percentage']
        pr_rel = polyrouter_result['analysis']['relevance_percentage']
        
        if ps_rel > pr_rel:
            recommendations.append(f"✅ PropheSeer has higher relevance ({ps_rel:.1f}% vs {pr_rel:.1f}%)")
        elif pr_rel > ps_rel:
            recommendations.append(f"✅ PolyRouter has higher relevance ({pr_rel:.1f}% vs {ps_rel:.1f}%)")
        else:
            recommendations.append("✅ Both APIs have similar relevance")
    
    if propheseer_result:
        ps_price = propheseer_result['analysis']['price_coverage']
        if ps_price > 80:
            recommendations.append(f"✅ PropheSeer: Excellent price coverage ({ps_price:.1f}%)")
        elif ps_price > 50:
            recommendations.append(f"⚠️ PropheSeer: Good price coverage ({ps_price:.1f}%)")
        else:
            recommendations.append(f"❌ PropheSeer: Low price coverage ({ps_price:.1f}%)")
    
    if polyrouter_result:
        pr_price = polyrouter_result['analysis']['price_coverage']
        if pr_price > 80:
            recommendations.append(f"✅ PolyRouter: Excellent price coverage ({pr_price:.1f}%)")
        elif pr_price > 50:
            recommendations.append(f"⚠️ PolyRouter: Good price coverage ({pr_price:.1f}%)")
        else:
            recommendations.append(f"❌ PolyRouter: Low price coverage ({pr_price:.1f}%)")
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print(f"\n{CYAN}Integration Strategy:{RESET}\n")
    print("  1. Use both APIs to maximize market coverage")
    print("  2. Deduplicate markets by question text similarity")
    print("  3. Prioritize markets with price data")
    print("  4. Filter for forex/economic relevance")
    print("  5. Combine with existing CLOB/DOME sources for redundancy")

def main():
    """Main test function"""
    print_header("UNIFIED PREDICTION MARKETS API TEST")
    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test PropheSeer
    propheseer_result = test_propheseer()
    
    # Test PolyRouter
    polyrouter_result = test_polyrouter()
    
    # Compare results
    if propheseer_result or polyrouter_result:
        compare_apis(propheseer_result, polyrouter_result)
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "propheseer": propheseer_result,
        "polyrouter": polyrouter_result
    }
    
    output_file = os.path.join(os.path.dirname(__file__), "..", "data", "unified_apis_test_results.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print_success(f"\nResults saved to: {output_file}")
    except Exception as e:
        print_warning(f"Failed to save results: {e}")
    
    print_header("TEST COMPLETE")

if __name__ == "__main__":
    main()

