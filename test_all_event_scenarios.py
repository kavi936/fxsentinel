#!/usr/bin/env python3
"""
Comprehensive test for ALL event scenarios
Tests quantitative, qualitative, partial data, and edge cases
"""

import requests
import json
from datetime import datetime
import sys

BACKEND_URL = "http://localhost:5001"

# Test all possible event scenarios
TEST_SCENARIOS = [
    {
        "name": "Scenario 1: Full Quantitative Data (Post-Event)",
        "description": "Event with all numeric data - previous, expected, actual",
        "event": {
            "id": "full_data_post",
            "title": "US Consumer Price Index (CPI) Nov 2025",
            "currency": "USD",
            "date": "Wed, Nov 13, 2025",
            "time": "13:30",
            "impact": "high",
            "previous": "2.6%",
            "expected": "2.7%",
            "actual": "2.9%",
            "source": "ForexFactory"
        },
        "analysisType": "post-event",
        "should_pass": True
    },
    {
        "name": "Scenario 2: Partial Data - TBD Actual (Pre-Event)",
        "description": "Upcoming event with TBD for actual value",
        "event": {
            "id": "tbd_actual",
            "title": "US Core PPI m/m Nov 2025",
            "currency": "USD",
            "date": "Wed, Nov 16, 2025",
            "time": "12:30",
            "impact": "high",
            "previous": "-0.1%",
            "expected": "0.3%",
            "actual": "TBD",
            "source": "ForexFactory"
        },
        "analysisType": "pre-event",
        "should_pass": True
    },
    {
        "name": "Scenario 3: Partial Data - N/A Values",
        "description": "Event with some N/A values",
        "event": {
            "id": "partial_na",
            "title": "Eurozone GDP q/q Nov 2025",
            "currency": "EUR",
            "date": "Thu, Nov 14, 2025",
            "time": "10:00",
            "impact": "medium",
            "previous": "0.2%",
            "expected": "N/A",
            "actual": "",
            "source": "ForexFactory"
        },
        "analysisType": "pre-event",
        "should_pass": True
    },
    {
        "name": "Scenario 4: Qualitative Event - Speech (No Numbers)",
        "description": "Fed Chair speech with no quantitative data",
        "event": {
            "id": "powell_speech",
            "title": "Fed Chair Powell Speaks on Economic Outlook",
            "currency": "USD",
            "date": "Fri, Nov 15, 2025",
            "time": "14:00",
            "impact": "high",
            "previous": "",
            "expected": "",
            "actual": "",
            "source": "ForexFactory"
        },
        "analysisType": "pre-event",
        "should_pass": True
    },
    {
        "name": "Scenario 5: All Empty Values",
        "description": "Event with all values empty or N/A",
        "event": {
            "id": "all_empty",
            "title": "Bank of England Policy Announcement",
            "currency": "GBP",
            "date": "Thu, Nov 7, 2025",
            "time": "12:00",
            "impact": "high",
            "previous": "N/A",
            "expected": "N/A",
            "actual": "N/A",
            "source": "ForexFactory"
        },
        "analysisType": "pre-event",
        "should_pass": True
    },
    {
        "name": "Scenario 6: Empty String for Actual (Pre-Event)",
        "description": "Event with empty string for actual (common in upcoming events)",
        "event": {
            "id": "empty_actual",
            "title": "Australia Employment Change Nov 2025",
            "currency": "AUD",
            "date": "Thu, Nov 14, 2025",
            "time": "00:30",
            "impact": "medium",
            "previous": "64.1K",
            "expected": "25.0K",
            "actual": "",
            "source": "ForexFactory"
        },
        "analysisType": "pre-event",
        "should_pass": True
    }
]

def test_scenario(scenario):
    """Test a single scenario"""
    print(f"\n{'='*80}")
    print(f"TEST: {scenario['name']}")
    print(f"{'='*80}")
    print(f"Description: {scenario['description']}")
    
    event = scenario['event']
    print(f"\nEvent: {event['title']}")
    print(f"Currency: {event['currency']}")
    print(f"Previous: '{event.get('previous', 'N/A')}'")
    print(f"Expected: '{event.get('expected', 'N/A')}'")
    print(f"Actual: '{event.get('actual', 'N/A')}'")
    print(f"Analysis Type: {scenario['analysisType']}")
    
    url = f"{BACKEND_URL}/api/enhanced-analysis/{event['id']}"
    request_data = {
        "event": event,
        "analysisType": scenario['analysisType'],
        "marketContext": {
            "currentTime": datetime.now().isoformat(),
            "eventTime": datetime.now().isoformat(),
            "isPostEvent": scenario['analysisType'] == "post-event"
        }
    }
    
    print(f"\n🚀 Sending request...")
    
    try:
        response = requests.post(url, json=request_data, timeout=30)
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required = ['headline', 'key_takeaway', 'forward_scenarios', 'positioning_context']
            missing = [f for f in required if f not in data]
            
            if missing:
                print(f"\n❌ MISSING FIELDS: {', '.join(missing)}")
                return False
            else:
                print(f"\n✅ ALL REQUIRED FIELDS PRESENT")
            
            # Show key details
            print(f"\n📊 ANALYSIS:")
            print(f"  Headline: {data['headline'][:80]}...")
            print(f"  Model: {data.get('model_used', 'N/A')}")
            print(f"  Confidence: {data.get('confidence_score', 'N/A')}")
            print(f"  Type: {data.get('analysis_type', 'N/A')}")
            
            # Show scenarios
            if 'forward_scenarios' in data:
                scenarios = data['forward_scenarios']
                print(f"\n🔮 SCENARIOS:")
                for key, value in scenarios.items():
                    print(f"  {key}: {value[:60]}...")
            
            # Check positioning context
            if 'positioning_context' in data:
                print(f"\n📍 POSITIONING CONTEXT:")
                pos = data['positioning_context']
                print(f"  Market bias: {pos.get('market_bias', 'N/A')[:60]}...")
            
            print(f"\n✅ TEST PASSED")
            return True
            
        else:
            print(f"\n❌ HTTP Error {response.status_code}")
            error_data = response.json()
            print(f"Error: {error_data.get('error', 'Unknown')}")
            if 'validation_errors' in error_data:
                print(f"Validation: {error_data['validation_errors']}")
            
            if scenario['should_pass']:
                print(f"❌ UNEXPECTED: Should have passed!")
                return False
            else:
                print(f"✅ EXPECTED: Should have failed")
                return True
                
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        return False

def main():
    """Run all scenario tests"""
    print("="*80)
    print("COMPREHENSIVE AI ANALYSIS - ALL SCENARIOS TEST")
    print("="*80)
    print(f"Testing {len(TEST_SCENARIOS)} different event scenarios\n")
    
    # Check backend
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if health.status_code == 200:
            print(f"✅ Backend running at {BACKEND_URL}\n")
        else:
            print(f"❌ Backend unhealthy: {health.status_code}\n")
            sys.exit(1)
    except:
        print(f"❌ Cannot connect to backend at {BACKEND_URL}")
        print("Make sure backend is running: cd backend && python3 app.py\n")
        sys.exit(1)
    
    # Run tests
    results = []
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n{'#'*80}")
        print(f"# TEST {i}/{len(TEST_SCENARIOS)}")
        print(f"{'#'*80}")
        
        passed = test_scenario(scenario)
        results.append({
            'name': scenario['name'],
            'passed': passed
        })
        
        if i < len(TEST_SCENARIOS):
            print("\n⏳ Waiting 2 seconds...")
            import time
            time.sleep(2)
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    passed_count = sum(1 for r in results if r['passed'])
    failed_count = len(results) - passed_count
    
    print(f"\nTotal: {len(results)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}\n")
    
    for r in results:
        status = "✅" if r['passed'] else "❌"
        print(f"{status} {r['name']}")
    
    if failed_count == 0:
        print(f"\n{'='*80}")
        print("🎉 ALL SCENARIOS PASSED!")
        print(f"{'='*80}\n")
        print("✅ System handles:")
        print("  - Full quantitative data (with actual values)")
        print("  - Partial data (TBD, N/A, empty)")
        print("  - Qualitative events (speeches, no numbers)")
        print("  - All empty values (policy announcements)")
        print("  - Pre-event and post-event analysis")
        sys.exit(0)
    else:
        print(f"\n{'='*80}")
        print(f"❌ {failed_count} SCENARIO(S) FAILED")
        print(f"{'='*80}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

