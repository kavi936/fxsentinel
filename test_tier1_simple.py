#!/usr/bin/env python3
"""
Simple test script to verify Tier 1 AI Analysis System
Simulates user clicking on economic calendar events
"""

import requests
import json
from datetime import datetime
import sys

# Backend URL
BACKEND_URL = "http://localhost:5001"

# Test events - using proper format for validation
TEST_EVENTS = [
    {
        "name": "Pre-Event CPI (No actual data)",
        "event": {
            "id": "cpi_nov_2025_pre",
            "title": "US Consumer Price Index (CPI) Nov 2025",
            "currency": "USD",
            "date": "Wed, Nov 13, 2025",
            "time": "13:30",
            "impact": "high",
            "previous": "2.6%",
            "expected": "2.7%",
            "actual": "",  # No actual data yet (pre-event)
            "forecast": "2.7%",
            "source": "ForexFactory"
        },
        "analysisType": "pre-event"
    },
    {
        "name": "Post-Event CPI (With actual data)",
        "event": {
            "id": "cpi_nov_2025_post",
            "title": "US Consumer Price Index (CPI) Nov 2025",
            "currency": "USD",
            "date": "Wed, Nov 13, 2025",
            "time": "13:30",
            "impact": "high",
            "previous": "2.6%",
            "expected": "2.7%",
            "actual": "2.9%",  # Actual data available (post-event)
            "forecast": "2.7%",
            "source": "ForexFactory"
        },
        "analysisType": "post-event"
    }
]

# Required fields
REQUIRED_FIELDS = [
    'headline', 'key_takeaway', 'forward_scenarios', 'event_summary',
    'market_reaction', 'implications_takeaways', 'trading_plan',
    'big_picture', 'positioning_context', 'next_catalysts',
    'confidence_score', 'analysis_type', 'model_used'
]

def check_backend():
    """Check if backend is running"""
    print("\n" + "="*80)
    print("CHECKING BACKEND STATUS")
    print("="*80 + "\n")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend is running at {BACKEND_URL}\n")
            return True
        else:
            print(f"❌ Backend responded with status {response.status_code}\n")
            return False
    except:
        print(f"❌ Cannot connect to backend at {BACKEND_URL}")
        print("⚠️  Make sure the backend is running: cd backend && python3 app.py\n")
        return False

def test_event(test_case):
    """Test analysis for one event"""
    print("\n" + "="*80)
    print(f"TEST: {test_case['name']}")
    print("="*80 + "\n")
    
    event = test_case['event']
    
    print(f"Event: {event['title']}")
    print(f"Currency: {event['currency']}")
    print(f"Impact: {event['impact']}")
    print(f"Expected: {event.get('expected', 'N/A')}")
    print(f"Actual: {event.get('actual') or 'Not available yet'}")
    print(f"Analysis Type: {test_case['analysisType']}\n")
    
    # Make request
    url = f"{BACKEND_URL}/api/enhanced-analysis/{event['id']}"
    request_data = {
        "event": event,
        "analysisType": test_case['analysisType'],
        "marketContext": {
            "currentTime": datetime.now().isoformat(),
            "eventTime": datetime.now().isoformat(),
            "isPostEvent": test_case['analysisType'] == "post-event"
        }
    }
    
    print(f"🚀 Sending POST request to: {url}\n")
    
    try:
        response = requests.post(url, json=request_data, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            print("📋 CHECKING REQUIRED FIELDS:")
            print("-" * 80)
            missing = []
            for field in REQUIRED_FIELDS:
                if field in data:
                    print(f"✅ {field}")
                else:
                    print(f"❌ MISSING: {field}")
                    missing.append(field)
            
            print()
            
            if not missing:
                print("✅ ALL REQUIRED FIELDS PRESENT\n")
            else:
                print(f"❌ MISSING {len(missing)} FIELDS: {', '.join(missing)}\n")
                return False
            
            # Print key details
            print("📊 ANALYSIS DETAILS:")
            print("-" * 80)
            print(f"Headline: {data.get('headline', 'N/A')}")
            print(f"Key Takeaway: {data.get('key_takeaway', 'N/A')[:150]}...")
            print(f"Model Used: {data.get('model_used', 'N/A')}")
            print(f"Confidence: {data.get('confidence_score', 'N/A')}")
            print(f"Analysis Type: {data.get('analysis_type', 'N/A')}")
            print(f"Cache Hit: {data.get('cache_hit', False)}")
            print(f"Cost: ${data.get('cost_estimate', 0):.4f}")
            print(f"Data Quality: {data.get('data_quality', 'N/A')}")
            print(f"Validation: {data.get('validation_status', 'N/A')}")
            print()
            
            # Forward scenarios
            if 'forward_scenarios' in data:
                print("🔮 FORWARD SCENARIOS:")
                scenarios = data['forward_scenarios']
                if 'bullish' in scenarios:
                    print(f"📈 Bullish: {scenarios['bullish'][:120]}...")
                if 'bearish' in scenarios:
                    print(f"📉 Bearish: {scenarios['bearish'][:120]}...")
                if 'neutral' in scenarios:
                    print(f"➡️  Neutral: {scenarios['neutral'][:120]}...")
                print()
            
            # Market reaction
            if 'market_reaction' in data and 'price_action' in data['market_reaction']:
                print("📊 MARKET REACTION:")
                print(f"{data['market_reaction']['price_action'][:200]}...")
                print()
            
            # Trading plan
            if 'trading_plan' in data:
                plan = data['trading_plan']
                if 'best_approach' in plan:
                    print("💼 TRADING PLAN:")
                    print(f"{plan['best_approach'][:200]}...")
                    if 'key_levels' in plan:
                        print(f"Key Levels: {plan['key_levels'][:150]}...")
                    print()
            
            # Next catalysts
            if 'next_catalysts' in data:
                print("🎯 NEXT CATALYSTS:")
                for i, catalyst in enumerate(data['next_catalysts'][:3], 1):
                    print(f"  {i}. {catalyst}")
                print()
            
            print("✅ TEST PASSED\n")
            return True
            
        elif response.status_code == 503:
            error = response.json()
            print(f"❌ Service Unavailable (503)")
            print(f"Error: {error.get('error', 'Unknown')}")
            print(f"Message: {error.get('message', 'Unknown')}")
            print("⚠️  GPT analyzer not initialized. Check OpenAI API key.\n")
            return False
            
        else:
            print(f"❌ Status {response.status_code}")
            print(f"Response: {response.text[:500]}\n")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out\n")
        return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("TIER 1 AI ANALYSIS SYSTEM TEST")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Cases: {len(TEST_EVENTS)}")
    print(f"Required Fields: {len(REQUIRED_FIELDS)}")
    
    # Check backend
    if not check_backend():
        sys.exit(1)
    
    # Run tests
    results = []
    for i, test_case in enumerate(TEST_EVENTS, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(TEST_EVENTS)}")
        print('='*80)
        
        result = test_event(test_case)
        results.append({'name': test_case['name'], 'passed': result})
        
        if i < len(TEST_EVENTS):
            print("⏳ Waiting 2 seconds...")
            import time
            time.sleep(2)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for r in results if r['passed'])
    failed = len(results) - passed
    
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}\n")
    
    for r in results:
        status = "✅ PASS" if r['passed'] else "❌ FAIL"
        print(f"{status} - {r['name']}")
    
    if failed == 0:
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("⚠️  SOME TESTS FAILED")
        print("="*80 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

