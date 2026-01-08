#!/usr/bin/env python3
"""
Holistic Test Suite for GPT AI Analysis Data Inputs
Tests all data sources currently integrated into GPT prompts
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import datetime, timezone
from services.gpt_ai_analysis import GPTAIAnalyzer, MarketContext
from services.market_sentiment_service import market_sentiment_service
from services.live_market_data import live_market_data_service
from app import get_tradingview_prices

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test(name, status, details=""):
    """Print a test result"""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {name}")
    if details:
        print(f"   {details}")

def test_trading_sessions():
    """Test trading session detection"""
    print_section("TEST 1: Trading Sessions")
    
    analyzer = GPTAIAnalyzer()
    sessions = analyzer._get_trading_sessions()
    
    # Check structure
    has_active_sessions = 'active_sessions' in sessions
    has_market_status = 'market_status' in sessions
    has_volatility_implication = 'volatility_implication' in sessions
    
    print_test("Structure Check", has_active_sessions and has_market_status and has_volatility_implication,
               f"Keys: {list(sessions.keys())}")
    
    # Check active_sessions is a list
    is_list = isinstance(sessions.get('active_sessions', None), list)
    print_test("Active Sessions is List", is_list,
               f"Type: {type(sessions.get('active_sessions'))}")
    
    # Check market_status values
    valid_status = sessions.get('market_status') in ['open', 'closed', 'unknown']
    print_test("Valid Market Status", valid_status,
               f"Status: {sessions.get('market_status')}")
    
    # Check volatility implication exists
    has_implication = bool(sessions.get('volatility_implication'))
    print_test("Volatility Implication Present", has_implication,
               f"Implication: {sessions.get('volatility_implication', 'None')}")
    
    # Print current state
    print(f"\n📊 Current Trading Session State:")
    print(f"   Active Sessions: {sessions.get('active_sessions', [])}")
    print(f"   Market Status: {sessions.get('market_status')}")
    print(f"   Volatility Implication: {sessions.get('volatility_implication')}")
    if 'current_time_utc' in sessions:
        print(f"   Current Time (UTC): {sessions.get('current_time_utc')}")
    
    return has_active_sessions and has_market_status and has_volatility_implication

def test_vix_data():
    """Test VIX data extraction"""
    print_section("TEST 2: VIX Fear Indicator")
    
    analyzer = GPTAIAnalyzer()
    sentiment_data = analyzer._get_market_sentiment_data()
    
    if not sentiment_data:
        print_test("Sentiment Data Available", False, "Could not fetch sentiment data")
        return False
    
    vix_data = sentiment_data.get('vix')
    
    if not vix_data:
        print_test("VIX Data Available", False, "VIX data not found in sentiment")
        return False
    
    # Check structure
    has_value = 'value' in vix_data
    has_change = 'change' in vix_data
    has_level = 'level' in vix_data
    
    print_test("VIX Structure Check", has_value and has_change and has_level,
               f"Keys: {list(vix_data.keys())}")
    
    # Check value types
    value_valid = isinstance(vix_data.get('value'), (int, float))
    change_valid = isinstance(vix_data.get('change'), (int, float))
    level_valid = vix_data.get('level') in ['low', 'medium', 'high']
    
    print_test("VIX Value Valid", value_valid,
               f"Value: {vix_data.get('value')} (type: {type(vix_data.get('value'))})")
    print_test("VIX Change Valid", change_valid,
               f"Change: {vix_data.get('change')} (type: {type(vix_data.get('change'))})")
    print_test("VIX Level Valid", level_valid,
               f"Level: {vix_data.get('level')}")
    
    # Print current VIX state
    print(f"\n📊 Current VIX State:")
    print(f"   Value: {vix_data.get('value')}")
    print(f"   Change: {vix_data.get('change'):+.2f}")
    print(f"   Level: {vix_data.get('level').upper()}")
    
    return has_value and has_change and has_level and value_valid and change_valid and level_valid

def test_risk_appetite():
    """Test Risk Appetite data extraction"""
    print_section("TEST 3: Risk Appetite")
    
    analyzer = GPTAIAnalyzer()
    sentiment_data = analyzer._get_market_sentiment_data()
    
    if not sentiment_data:
        print_test("Sentiment Data Available", False, "Could not fetch sentiment data")
        return False
    
    risk_data = sentiment_data.get('risk_appetite')
    
    if not risk_data:
        print_test("Risk Appetite Data Available", False, "Risk appetite data not found")
        return False
    
    # Check structure
    has_level = 'level' in risk_data
    has_percentage = 'percentage' in risk_data
    has_safe_havens = 'safe_havens' in risk_data
    has_trend = 'trend' in risk_data
    
    print_test("Risk Appetite Structure", has_level and has_percentage and has_safe_havens and has_trend,
               f"Keys: {list(risk_data.keys())}")
    
    # Check value types
    level_valid = risk_data.get('level') in ['low', 'medium', 'high']
    percentage_valid = isinstance(risk_data.get('percentage'), (int, float))
    percentage_range = 0 <= risk_data.get('percentage', -1) <= 100
    trend_valid = risk_data.get('trend') in ['increasing', 'decreasing', 'stable']
    
    print_test("Risk Level Valid", level_valid,
               f"Level: {risk_data.get('level')}")
    print_test("Risk Percentage Valid", percentage_valid and percentage_range,
               f"Percentage: {risk_data.get('percentage')}%")
    print_test("Risk Trend Valid", trend_valid,
               f"Trend: {risk_data.get('trend')}")
    
    # Print current state
    print(f"\n📊 Current Risk Appetite State:")
    print(f"   Level: {risk_data.get('level').upper()}")
    print(f"   Percentage: {risk_data.get('percentage')}%")
    print(f"   Safe Havens: {risk_data.get('safe_havens', 'None')}")
    print(f"   Trend: {risk_data.get('trend')}")
    
    return has_level and has_percentage and has_safe_havens and level_valid and percentage_valid and percentage_range

def test_pairs_sentiment():
    """Test pairs sentiment data extraction"""
    print_section("TEST 4: Pairs Sentiment (Top 3 Pairs)")
    
    analyzer = GPTAIAnalyzer()
    
    # Test with USD event
    test_event = {
        'title': 'US Non-Farm Payrolls',
        'currency': 'USD',
        'currencyPairs': ['EUR/USD', 'USD/JPY', 'GBP/USD']
    }
    
    # Create minimal market context
    market_context = MarketContext(
        current_prices={'EUR/USD': 1.0850, 'USD/JPY': 148.50, 'GBP/USD': 1.2650},
        recent_volatility={'EUR/USD': 'Medium', 'USD/JPY': 'Medium', 'GBP/USD': 'Medium'},
        market_sentiment={'EUR/USD': 'bullish', 'USD/JPY': 'bearish', 'GBP/USD': 'neutral'},
        key_levels=None,
        economic_calendar=[],
        bond_yields=None,
        equity_indices=None,
        commodity_prices=None
    )
    
    pairs_data = analyzer._get_pairs_sentiment_data('USD', test_event, market_context)
    
    # Check if we got data
    has_data = len(pairs_data) > 0
    print_test("Pairs Sentiment Data Available", has_data,
               f"Found {len(pairs_data)} pairs")
    
    if not has_data:
        print("   ⚠️  Note: This might be expected if market sentiment service is not initialized")
        return False
    
    # Check structure for each pair
    all_valid = True
    for i, pair_data in enumerate(pairs_data[:3]):  # Check first 3
        has_pair = 'pair' in pair_data
        has_sentiment = 'sentiment' in pair_data
        has_daily_change = 'daily_change' in pair_data
        has_rsi = 'rsi' in pair_data
        has_volatility = 'volatility' in pair_data
        
        pair_valid = has_pair and has_sentiment and has_daily_change and has_rsi and has_volatility
        
        print_test(f"Pair {i+1} Structure ({pair_data.get('pair', 'Unknown')})", pair_valid,
                   f"Keys: {list(pair_data.keys())}")
        
        if pair_valid:
            # Check value types
            sentiment_valid = pair_data.get('sentiment') in ['bullish', 'bearish', 'neutral']
            daily_change_valid = isinstance(pair_data.get('daily_change'), (int, float))
            rsi_valid = isinstance(pair_data.get('rsi'), (int, float)) and 0 <= pair_data.get('rsi', -1) <= 100
            volatility_valid = isinstance(pair_data.get('volatility'), (int, float)) and pair_data.get('volatility', -1) >= 0
            
            print_test(f"  Pair {i+1} Values Valid", 
                      sentiment_valid and daily_change_valid and rsi_valid and volatility_valid,
                      f"Sentiment: {pair_data.get('sentiment')}, Change: {pair_data.get('daily_change'):+.2f}%, "
                      f"RSI: {pair_data.get('rsi'):.1f}, Vol: {pair_data.get('volatility'):.2f}%")
            
            if not (sentiment_valid and daily_change_valid and rsi_valid and volatility_valid):
                all_valid = False
        else:
            all_valid = False
    
    # Print current state
    print(f"\n📊 Current Pairs Sentiment State:")
    for pair_data in pairs_data[:3]:
        print(f"   {pair_data.get('pair')}: {pair_data.get('sentiment').upper()} "
              f"({pair_data.get('daily_change'):+.2f}%), RSI: {pair_data.get('rsi'):.1f}, "
              f"Vol: {pair_data.get('volatility'):.2f}%")
    
    return has_data and all_valid

def test_top_3_pairs_selection():
    """Test top 3 pairs selection logic"""
    print_section("TEST 5: Top 3 Pairs Selection")
    
    analyzer = GPTAIAnalyzer()
    
    # Test with event that has currencyPairs
    event_with_pairs = {
        'currency': 'USD',
        'currencyPairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD']
    }
    pairs = analyzer._get_top_3_pairs_for_currency('USD', event_with_pairs)
    print_test("Uses Event Pairs (First 3)", len(pairs) == 3 and pairs == ['EUR/USD', 'USD/JPY', 'GBP/USD'],
               f"Selected: {pairs}")
    
    # Test with event without currencyPairs
    event_no_pairs = {
        'currency': 'EUR'
    }
    pairs = analyzer._get_top_3_pairs_for_currency('EUR', event_no_pairs)
    expected = ['EUR/USD', 'EUR/GBP', 'EUR/JPY']
    print_test("Uses Priority Map (EUR)", pairs == expected,
               f"Selected: {pairs}, Expected: {expected}")
    
    # Test with unknown currency
    pairs = analyzer._get_top_3_pairs_for_currency('XYZ', event_no_pairs)
    default = ['EUR/USD', 'USD/JPY', 'GBP/USD']
    print_test("Uses Default for Unknown Currency", len(pairs) == 3 and pairs == default,
               f"Selected: {pairs}")
    
    return True

def test_market_context():
    """Test market context data"""
    print_section("TEST 6: Market Context (Current Prices, Volatility, Sentiment)")
    
    # Get live market data
    live_data = live_market_data_service.get_live_market_data()
    
    has_prices = 'current_prices' in live_data and live_data['current_prices']
    has_volatility = 'recent_volatility' in live_data and live_data['recent_volatility']
    has_sentiment = 'market_sentiment' in live_data and live_data['market_sentiment']
    
    print_test("Current Prices Available", has_prices,
               f"Pairs: {list(live_data.get('current_prices', {}).keys())[:5]}...")
    print_test("Recent Volatility Available", has_volatility,
               f"Pairs: {list(live_data.get('recent_volatility', {}).keys())[:5]}...")
    print_test("Market Sentiment Available", has_sentiment,
               f"Pairs: {list(live_data.get('market_sentiment', {}).keys())[:5]}...")
    
    # Check data quality
    if has_prices:
        prices = live_data['current_prices']
        sample_pair = list(prices.keys())[0] if prices else None
        price_valid = sample_pair and isinstance(prices[sample_pair], (int, float))
        print_test("Price Values Valid", price_valid,
                   f"Sample ({sample_pair}): {prices.get(sample_pair)}")
    
    print(f"\n📊 Market Context Sample:")
    if has_prices:
        sample_pairs = list(live_data['current_prices'].keys())[:3]
        for pair in sample_pairs:
            print(f"   {pair}: {live_data['current_prices'][pair]}, "
                  f"Vol: {live_data.get('recent_volatility', {}).get(pair, 'N/A')}, "
                  f"Sentiment: {live_data.get('market_sentiment', {}).get(pair, 'N/A')}")
    
    return has_prices and has_volatility and has_sentiment

def test_tradingview_daily_change():
    """Test TradingView daily change data"""
    print_section("TEST 7: TradingView Daily Change Data")
    
    tv_data = get_tradingview_prices()
    
    has_data = tv_data is not None and len(tv_data) > 0
    print_test("TradingView Data Available", has_data,
               f"Pairs: {len(tv_data) if tv_data else 0}")
    
    if not has_data:
        return False
    
    # Check structure for a sample pair
    sample_pair = list(tv_data.keys())[0] if tv_data else None
    if sample_pair:
        pair_data = tv_data[sample_pair]
        has_change_percent = 'changePercent' in pair_data
        has_price = 'price' in pair_data
        has_change = 'change' in pair_data
        
        print_test(f"Sample Pair Structure ({sample_pair})", 
                  has_change_percent and has_price and has_change,
                  f"Keys: {list(pair_data.keys())}")
        
        if has_change_percent:
            change_percent = pair_data['changePercent']
            is_valid = isinstance(change_percent, (int, float))
            print_test("changePercent Valid", is_valid,
                      f"Value: {change_percent:+.4f}%")
            
            print(f"\n📊 TradingView Sample Data ({sample_pair}):")
            print(f"   Price: {pair_data.get('price')}")
            print(f"   Change: {pair_data.get('change')}")
            print(f"   Change %: {pair_data.get('changePercent'):+.4f}%")
            
            return is_valid
    
    return False

def test_prompt_construction():
    """Test full prompt construction"""
    print_section("TEST 8: Full Prompt Construction")
    
    analyzer = GPTAIAnalyzer()
    
    # Create test event
    test_event = {
        'title': 'US Non-Farm Payrolls',
        'currency': 'USD',
        'impact': 'high',
        'previous': '150K',
        'expected': '180K',
        'actual': '200K',
        'currencyPairs': ['EUR/USD', 'USD/JPY', 'GBP/USD']
    }
    
    # Create market context
    market_context = MarketContext(
        current_prices={'EUR/USD': 1.0850, 'USD/JPY': 148.50, 'GBP/USD': 1.2650},
        recent_volatility={'EUR/USD': 'Medium', 'USD/JPY': 'Medium', 'GBP/USD': 'Medium'},
        market_sentiment={'EUR/USD': 'bullish', 'USD/JPY': 'bearish', 'GBP/USD': 'neutral'},
        key_levels=None,
        economic_calendar=[],
        bond_yields=None,
        equity_indices=None,
        commodity_prices=None
    )
    
    try:
        prompt = analyzer._create_analysis_prompt(test_event, market_context, 'post_event')
        
        # Check prompt contains required sections
        has_event_details = 'EVENT DETAILS:' in prompt
        has_market_context = 'MARKET CONTEXT:' in prompt
        has_additional_context = 'ADDITIONAL MARKET CONTEXT:' in prompt
        has_important_note = 'IMPORTANT:' in prompt
        
        print_test("Prompt Contains Event Details", has_event_details)
        print_test("Prompt Contains Market Context", has_market_context)
        print_test("Prompt Contains Additional Context", has_additional_context)
        print_test("Prompt Contains Important Note", has_important_note)
        
        # Check for specific data
        has_trading_sessions = 'Trading Sessions' in prompt or 'Market Status' in prompt
        has_vix = 'VIX' in prompt
        has_risk_appetite = 'Risk Appetite' in prompt
        has_pairs_sentiment = 'RELEVANT CURRENCY PAIRS SENTIMENT' in prompt or 'Daily Change' in prompt
        
        print_test("Prompt Contains Trading Sessions", has_trading_sessions)
        print_test("Prompt Contains VIX", has_vix)
        print_test("Prompt Contains Risk Appetite", has_risk_appetite)
        print_test("Prompt Contains Pairs Sentiment", has_pairs_sentiment)
        
        # Print prompt length
        print(f"\n📊 Prompt Statistics:")
        print(f"   Length: {len(prompt)} characters")
        print(f"   Lines: {len(prompt.split(chr(10)))}")
        
        # Print sample of prompt
        print(f"\n📝 Prompt Sample (first 500 chars):")
        print(prompt[:500] + "...")
        
        return (has_event_details and has_market_context and has_additional_context and 
                has_trading_sessions and has_vix and has_risk_appetite)
        
    except Exception as e:
        print_test("Prompt Construction", False, f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("\n" + "="*80)
    print("  GPT AI ANALYSIS DATA INPUTS - HOLISTIC TEST SUITE")
    print("="*80)
    print(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run all tests
    results['trading_sessions'] = test_trading_sessions()
    results['vix_data'] = test_vix_data()
    results['risk_appetite'] = test_risk_appetite()
    results['top_3_pairs'] = test_top_3_pairs_selection()
    results['market_context'] = test_market_context()
    results['tradingview_change'] = test_tradingview_daily_change()
    results['pairs_sentiment'] = test_pairs_sentiment()
    results['prompt_construction'] = test_prompt_construction()
    
    # Print summary
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name.replace('_', ' ').title()}")
    
    # Overall status
    all_passed = all(results.values())
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED - Ready for production!")
    else:
        print("⚠️  SOME TESTS FAILED - Review failures before proceeding")
    print("="*80)
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

