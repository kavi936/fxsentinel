#!/usr/bin/env python3
"""
Test Trump and Political News Filtering
Shows how political events affect forex markets
"""

from services.enhanced_forex_filter import enhanced_forex_filter

def test_trump_and_political_news():
    """Test filtering for Trump and political news that affects forex"""
    
    print("🗽 TESTING TRUMP & POLITICAL NEWS FILTERING")
    print("=" * 70)
    
    test_cases = [
        {
            "title": "Trump Threatens New Tariffs on China",
            "summary": "Former president proposes 60% tariffs on Chinese imports, markets react",
            "expected": True,
            "description": "Trade war threat - high impact on USD/CNY and risk sentiment"
        },
        {
            "title": "Biden Signs Executive Order on Trade Policy",
            "summary": "President Biden implements new trade restrictions affecting global markets",
            "expected": True,
            "description": "Trade policy change - affects USD and trade-dependent currencies"
        },
        {
            "title": "Trump Leads in Polls, Dollar Strengthens",
            "summary": "Republican candidate gains in election polls, USD gains against major pairs",
            "expected": True,
            "description": "Election uncertainty - affects USD strength and market sentiment"
        },
        {
            "title": "US-China Trade Relations Deteriorate",
            "summary": "Trade tensions escalate between Washington and Beijing",
            "expected": True,
            "description": "Geopolitical tension - impacts risk currencies and safe havens"
        },
        {
            "title": "Congress Passes New Tariff Bill",
            "summary": "House and Senate approve legislation affecting international trade",
            "expected": True,
            "description": "Legislation - affects trade flows and currency valuations"
        },
        {
            "title": "Brexit Uncertainty Weighs on GBP",
            "summary": "British pound falls as Brexit negotiations face new challenges",
            "expected": True,
            "description": "Political uncertainty - direct impact on GBP pairs"
        },
        {
            "title": "Market Volatility Spikes on Political News",
            "summary": "Forex markets experience increased volatility due to political uncertainty",
            "expected": True,
            "description": "Market sentiment - affects all major currency pairs"
        },
        {
            "title": "Trump Announces Economic Policy Platform",
            "summary": "Republican candidate outlines plans for trade and economic policy",
            "expected": True,
            "description": "Policy announcement - affects market expectations and USD"
        },
        {
            "title": "US Sanctions Impact Russian Ruble",
            "summary": "New sanctions against Russia cause RUB to weaken significantly",
            "expected": True,
            "description": "Geopolitical sanctions - affects emerging market currencies"
        },
        {
            "title": "Election Campaign Rhetoric Affects Markets",
            "summary": "Political speeches and campaign promises create market uncertainty",
            "expected": True,
            "description": "Campaign rhetoric - affects investor confidence and risk sentiment"
        },
        {
            "title": "Apple Stock Rises on Earnings Beat",
            "summary": "Tech company reports strong quarterly results",
            "expected": False,
            "description": "Stock news - not forex related"
        },
        {
            "title": "Bitcoin Surges on Institutional Adoption",
            "summary": "Cryptocurrency reaches new highs as more institutions invest",
            "expected": False,
            "description": "Crypto news - should be excluded"
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
        print(f"   Positive Keywords: {score['positive_keywords_found'][:5]}...")
        print(f"   Description: {case['description']}")
        print()
    
    accuracy = (correct_matches / total_tests) * 100
    print(f"📈 POLITICAL NEWS FILTERING ACCURACY: {accuracy:.1f}% ({correct_matches}/{total_tests})")
    print()

def test_country_specific_news():
    """Test filtering for country-specific economic news"""
    
    print("🌍 TESTING COUNTRY-SPECIFIC NEWS FILTERING")
    print("=" * 70)
    
    test_cases = [
        {
            "title": "US Economy Shows Strong Growth",
            "summary": "American GDP exceeds expectations, dollar strengthens",
            "expected": True,
            "description": "US economic data - affects USD pairs"
        },
        {
            "title": "UK Inflation Rises Above Target",
            "summary": "British consumer prices increase, BOE under pressure",
            "expected": True,
            "description": "UK inflation - affects GBP pairs"
        },
        {
            "title": "China Trade Data Disappoints",
            "summary": "Chinese exports fall, affecting global trade sentiment",
            "expected": True,
            "description": "China trade - affects commodity currencies"
        },
        {
            "title": "Japanese Yen Weakens on BOJ Policy",
            "summary": "Bank of Japan maintains dovish stance, JPY falls",
            "expected": True,
            "description": "Japan monetary policy - affects JPY pairs"
        },
        {
            "title": "Australian Dollar Rises on Strong Data",
            "summary": "Aussie gains on positive economic indicators",
            "expected": True,
            "description": "Australia data - affects AUD pairs"
        },
        {
            "title": "Canadian Dollar Falls on Oil Prices",
            "summary": "CAD weakens as crude oil prices decline",
            "expected": True,
            "description": "Canada commodity correlation - affects CAD"
        },
        {
            "title": "Swiss Franc Gains on Safe Haven Demand",
            "summary": "CHF strengthens as investors seek safety",
            "expected": True,
            "description": "Switzerland safe haven - affects CHF pairs"
        },
        {
            "title": "New Zealand Dollar Volatile on RBNZ",
            "summary": "Kiwi fluctuates on central bank policy uncertainty",
            "expected": True,
            "description": "New Zealand policy - affects NZD pairs"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        score = enhanced_forex_filter.get_forex_score(case['title'], case['summary'])
        
        status = "✅" if score['is_forex'] else "❌"
        result = "FOREX" if score['is_forex'] else "NOT FOREX"
        
        print(f"{i}. {status} {case['title']}")
        print(f"   Result: {result} | Confidence: {score['confidence']}% | Impact: {score['impact_level']}")
        print(f"   Keywords: {score['positive_keywords_found'][:3]}...")
        print(f"   Description: {case['description']}")
        print()

def test_trade_and_tariff_news():
    """Test filtering for trade and tariff related news"""
    
    print("📦 TESTING TRADE & TARIFF NEWS FILTERING")
    print("=" * 70)
    
    test_cases = [
        {
            "title": "US Imposes New Tariffs on European Goods",
            "summary": "Washington announces 25% tariffs on EU imports",
            "expected": True,
            "description": "Trade war escalation - affects EUR/USD"
        },
        {
            "title": "China Retaliates with Trade Restrictions",
            "summary": "Beijing responds to US tariffs with countermeasures",
            "expected": True,
            "description": "Trade retaliation - affects global risk sentiment"
        },
        {
            "title": "Trade Deficit Widens in United States",
            "summary": "US trade gap increases, affecting dollar sentiment",
            "expected": True,
            "description": "Trade data - affects USD valuation"
        },
        {
            "title": "EU and UK Reach Trade Agreement",
            "summary": "Post-Brexit trade deal boosts pound and euro",
            "expected": True,
            "description": "Trade agreement - affects GBP and EUR"
        },
        {
            "title": "Trade Negotiations Between US and China",
            "summary": "Washington and Beijing resume trade talks",
            "expected": True,
            "description": "Trade diplomacy - affects market sentiment"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        score = enhanced_forex_filter.get_forex_score(case['title'], case['summary'])
        
        status = "✅" if score['is_forex'] else "❌"
        result = "FOREX" if score['is_forex'] else "NOT FOREX"
        
        print(f"{i}. {status} {case['title']}")
        print(f"   Result: {result} | Confidence: {score['confidence']}% | Impact: {score['impact_level']}")
        print(f"   Keywords: {score['positive_keywords_found'][:3]}...")
        print(f"   Description: {case['description']}")
        print()

if __name__ == "__main__":
    test_trump_and_political_news()
    test_country_specific_news()
    test_trade_and_tariff_news()
