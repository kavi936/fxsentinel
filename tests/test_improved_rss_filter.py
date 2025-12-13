#!/usr/bin/env python3
"""
Test Improved RSS Feed Filtering
Demonstrates the enhanced filtering that excludes irrelevant news for forex traders
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.enhanced_forex_filter import EnhancedForexFilter

def test_improved_filtering():
    """Test the improved RSS feed filtering system"""
    
    print("🔍 TESTING IMPROVED RSS FEED FILTERING")
    print("=" * 70)
    print("This test demonstrates how the enhanced filter excludes irrelevant news")
    print("for forex traders while keeping truly relevant forex content.\n")
    
    # Initialize the enhanced filter
    forex_filter = EnhancedForexFilter()
    
    # Test cases with various news types
    test_cases = [
        # ✅ SHOULD BE INCLUDED - High-impact forex news
        {
            "title": "Federal Reserve Raises Interest Rates by 25 Basis Points",
            "summary": "The Fed announced a quarter-point rate hike, signaling continued monetary tightening.",
            "source": "Reuters",
            "expected": True,
            "category": "High-impact forex news"
        },
        {
            "title": "EUR/USD Breaks Key Resistance Level at 1.1000",
            "summary": "Euro dollar pair reaches significant technical level amid ECB policy uncertainty.",
            "source": "FXStreet",
            "expected": True,
            "category": "Direct forex pair news"
        },
        {
            "title": "US CPI Inflation Rises to 3.2% in August",
            "summary": "Consumer price index shows inflation remains above target, affecting USD strength.",
            "source": "Bloomberg",
            "expected": True,
            "category": "Economic indicator news"
        },
        {
            "title": "ECB President Lagarde Speaks on Monetary Policy",
            "summary": "European Central Bank head discusses inflation outlook and rate decisions.",
            "source": "CNBC",
            "expected": True,
            "category": "Central bank news"
        },
        {
            "title": "Non-Farm Payrolls Beat Expectations with 216K Jobs Added",
            "summary": "US economy adds more jobs than expected, unemployment rate at 3.7%.",
            "source": "MarketWatch",
            "expected": True,
            "category": "Employment data news"
        },
        
        # ❌ SHOULD BE EXCLUDED - Irrelevant news for forex traders
        {
            "title": "Bitcoin Surges to New All-Time High of $120,000",
            "summary": "Cryptocurrency market sees massive gains as Bitcoin reaches unprecedented levels.",
            "source": "CryptoNews",
            "expected": False,
            "category": "Cryptocurrency news"
        },
        {
            "title": "Apple Stock Rises 5% on Strong Q4 Earnings Report",
            "summary": "Tech giant beats analyst expectations with record iPhone sales and revenue.",
            "source": "MarketWatch",
            "expected": False,
            "category": "Stock market news"
        },
        {
            "title": "Tesla Announces New Electric Vehicle Model",
            "summary": "Automaker reveals innovative features and improved battery technology.",
            "source": "TechCrunch",
            "expected": False,
            "category": "Company-specific news"
        },
        {
            "title": "Real Estate Market Shows Signs of Recovery",
            "summary": "Housing prices increase as mortgage rates stabilize and inventory grows.",
            "source": "RealEstateNews",
            "expected": False,
            "category": "Real estate news"
        },
        {
            "title": "Netflix Announces New Original Series",
            "summary": "Streaming platform reveals upcoming content lineup and production details.",
            "source": "EntertainmentWeekly",
            "expected": False,
            "category": "Entertainment news"
        },
        {
            "title": "New Restaurant Chain Opens in Downtown",
            "summary": "Popular dining establishment expands with innovative menu and modern decor.",
            "source": "LocalNews",
            "expected": False,
            "category": "Local business news"
        },
        {
            "title": "Medical Breakthrough in Cancer Treatment",
            "summary": "Researchers discover promising new therapy with improved success rates.",
            "source": "HealthNews",
            "expected": False,
            "category": "Healthcare news"
        },
        
        # 🔍 EDGE CASES - Should be carefully evaluated
        {
            "title": "Oil Prices Impact Currency Markets",
            "summary": "Crude oil volatility affects USD/CAD and other commodity currencies.",
            "source": "Reuters",
            "expected": True,
            "category": "Commodity impact on forex"
        },
        {
            "title": "Tech Stocks Fall, Dollar Strengthens",
            "summary": "Nasdaq decline leads to safe-haven flows into US dollar.",
            "source": "Bloomberg",
            "expected": True,
            "category": "Stock market impact on forex"
        },
        {
            "title": "Earnings Season Affects Market Sentiment",
            "summary": "Corporate earnings reports influence investor confidence and currency flows.",
            "source": "CNBC",
            "expected": False,
            "category": "General market sentiment"
        }
    ]
    
    # Run tests
    correct_matches = 0
    total_tests = len(test_cases)
    
    print("📊 TEST RESULTS:")
    print("-" * 70)
    
    for i, case in enumerate(test_cases, 1):
        title = case["title"]
        summary = case["summary"]
        source = case["source"]
        expected = case["expected"]
        category = case["category"]
        
        # Test the filtering
        result = forex_filter.is_forex_related(title, summary, source)
        
        # Get detailed scoring
        score = forex_filter.get_forex_score(title, summary)
        
        # Determine status
        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result == expected:
            correct_matches += 1
        
        print(f"{i:2d}. {status} | {category}")
        print(f"    Title: {title}")
        print(f"    Source: {source}")
        print(f"    Expected: {expected} | Got: {result}")
        print(f"    Confidence: {score['confidence']}% | Impact: {score['impact_level']}")
        print(f"    Positive keywords: {len(score['positive_keywords_found'])}")
        print(f"    Negative keywords: {len(score['negative_keywords_found'])}")
        print()
    
    # Summary
    accuracy = (correct_matches / total_tests) * 100
    print("📈 SUMMARY:")
    print("-" * 70)
    print(f"Total tests: {total_tests}")
    print(f"Correct matches: {correct_matches}")
    print(f"Accuracy: {accuracy:.1f}%")
    print()
    
    if accuracy >= 90:
        print("🎉 EXCELLENT! The improved filter is working very well.")
    elif accuracy >= 80:
        print("👍 GOOD! The improved filter is working well with minor issues.")
    else:
        print("⚠️  NEEDS IMPROVEMENT! The filter needs further refinement.")
    
    print("\n💡 KEY IMPROVEMENTS:")
    print("- Enhanced negative keywords to exclude crypto, stocks, real estate, etc.")
    print("- Source-aware filtering (more lenient for forex-focused sources)")
    print("- Better context awareness for economic news")
    print("- Improved keyword weighting and scoring")
    print("- More specific exclusion criteria for irrelevant content")

def test_source_specific_filtering():
    """Test how different sources are handled"""
    
    print("\n🔍 TESTING SOURCE-SPECIFIC FILTERING")
    print("=" * 70)
    
    forex_filter = EnhancedForexFilter()
    
    # Test the same content with different sources
    test_content = {
        "title": "Market Analysis: Currency Trends",
        "summary": "Analysis of recent currency movements and market sentiment."
    }
    
    sources = [
        ("FXStreet", "Forex-focused source"),
        ("Reuters", "General financial source"),
        ("CryptoNews", "Cryptocurrency source"),
        ("TechCrunch", "Technology source")
    ]
    
    print("Testing the same content with different sources:\n")
    
    for source, description in sources:
        result = forex_filter.is_forex_related(
            test_content["title"], 
            test_content["summary"], 
            source
        )
        score = forex_filter.get_forex_score(test_content["title"], test_content["summary"])
        
        print(f"Source: {source} ({description})")
        print(f"Result: {result} | Confidence: {score['confidence']}%")
        print()

if __name__ == "__main__":
    test_improved_filtering()
    test_source_specific_filtering()
