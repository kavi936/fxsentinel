#!/usr/bin/env python3
"""
Test Enhanced Forex Filtering System
"""

from services.enhanced_forex_filter import enhanced_forex_filter

def test_enhanced_filtering():
    """Test the enhanced forex filtering system"""
    
    print("🧪 TESTING ENHANCED FOREX FILTERING")
    print("=" * 60)
    
    test_cases = [
        {
            "title": "Fed Chair Powell Testifies on Monetary Policy",
            "summary": "Federal Reserve Chairman Jerome Powell addresses Congress on interest rate outlook",
            "expected": True,
            "description": "High impact forex news"
        },
        {
            "title": "Bitcoin Reaches New High as Institutional Adoption Grows",
            "summary": "Cryptocurrency market sees increased institutional investment",
            "expected": False,
            "description": "Crypto news (should be excluded)"
        },
        {
            "title": "EUR/USD Breaks Key Resistance Level",
            "summary": "Euro dollar pair reaches 1.1000 as ECB policy uncertainty continues",
            "expected": True,
            "description": "Direct forex pair news"
        },
        {
            "title": "Apple Stock Surges on Strong Earnings Report",
            "summary": "Tech giant beats analyst expectations with record iPhone sales",
            "expected": False,
            "description": "Stock news (should be excluded)"
        },
        {
            "title": "Oil Prices Impact Currency Markets",
            "summary": "Crude oil volatility affects USD/CAD and other commodity currencies",
            "expected": False,
            "description": "Commodity news (should be excluded)"
        },
        {
            "title": "ECB Maintains Interest Rates at 4.5%",
            "summary": "European Central Bank holds rates steady as inflation concerns persist",
            "expected": True,
            "description": "Central bank decision"
        },
        {
            "title": "US CPI Data Shows Inflation Cooling",
            "summary": "Consumer price index fell to 3.1% in December, below expectations",
            "expected": True,
            "description": "Economic indicator"
        },
        {
            "title": "Non-Farm Payrolls Beat Expectations",
            "summary": "US economy adds 216,000 jobs in December, unemployment rate at 3.7%",
            "expected": True,
            "description": "Employment data"
        },
        {
            "title": "Gold Prices Surge on Safe Haven Demand",
            "summary": "Precious metal reaches new highs as investors seek safety",
            "expected": False,
            "description": "Commodity news"
        },
        {
            "title": "Tesla Stock Plunges on Earnings Miss",
            "summary": "Electric vehicle maker reports disappointing quarterly results",
            "expected": False,
            "description": "Stock news"
        }
    ]
    
    correct_matches = 0
    total_tests = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        # Get detailed scoring
        score = enhanced_forex_filter.get_forex_score(case['title'], case['summary'])
        
        # Check if result matches expectation
        is_correct = score['is_forex'] == case['expected']
        if is_correct:
            correct_matches += 1
        
        status = "✅" if is_correct else "❌"
        result = "FOREX" if score['is_forex'] else "NOT FOREX"
        expected = "FOREX" if case['expected'] else "NOT FOREX"
        
        print(f"{i}. {status} {case['title']}")
        print(f"   Result: {result} | Expected: {expected}")
        print(f"   Confidence: {score['confidence']}% | Impact: {score['impact_level']}")
        print(f"   Positive Score: {score['positive_score']} | Negative Score: {score['negative_score']}")
        print(f"   Positive Keywords: {score['positive_keywords_found'][:3]}...")
        print(f"   Negative Keywords: {score['negative_keywords_found'][:3]}...")
        print(f"   Description: {case['description']}")
        print()
    
    accuracy = (correct_matches / total_tests) * 100
    print(f"📈 ENHANCED FILTERING ACCURACY: {accuracy:.1f}% ({correct_matches}/{total_tests})")
    print()

def test_currency_pair_extraction():
    """Test currency pair extraction"""
    
    print("💱 TESTING CURRENCY PAIR EXTRACTION")
    print("=" * 60)
    
    test_texts = [
        "EUR/USD breaks above 1.1000 resistance level",
        "USD/JPY falls to 150.50 as BOJ intervenes",
        "GBP/USD volatile ahead of BOE rate decision",
        "AUD/USD and NZD/USD both decline on risk-off sentiment",
        "EUR/GBP consolidates around 0.8600 level"
    ]
    
    for i, text in enumerate(test_texts, 1):
        pairs = enhanced_forex_filter.extract_currency_pairs(text)
        print(f"{i}. {text}")
        print(f"   Extracted Pairs: {pairs}")
        print()

def test_impact_scoring():
    """Test impact level scoring"""
    
    print("📊 TESTING IMPACT LEVEL SCORING")
    print("=" * 60)
    
    test_cases = [
        {
            "title": "Fed Raises Interest Rates by 25 Basis Points",
            "summary": "Federal Reserve increases target rate to 5.25-5.50%",
            "expected_impact": "high"
        },
        {
            "title": "US CPI Data Shows Inflation at 3.1%",
            "summary": "Consumer price index remains above target",
            "expected_impact": "high"
        },
        {
            "title": "Retail Sales Increase by 0.3%",
            "summary": "Consumer spending shows modest growth",
            "expected_impact": "medium"
        },
        {
            "title": "EUR/USD Technical Analysis",
            "summary": "Pair approaches key support level",
            "expected_impact": "low"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        score = enhanced_forex_filter.get_forex_score(case['title'], case['summary'])
        
        status = "✅" if score['impact_level'] == case['expected_impact'] else "❌"
        
        print(f"{i}. {status} {case['title']}")
        print(f"   Impact: {score['impact_level']} | Expected: {case['expected_impact']}")
        print(f"   High Impact Keywords: {score['high_impact_matches']}")
        print(f"   Medium Impact Keywords: {score['medium_impact_matches']}")
        print()

if __name__ == "__main__":
    test_enhanced_filtering()
    test_currency_pair_extraction()
    test_impact_scoring()
