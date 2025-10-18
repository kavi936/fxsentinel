#!/usr/bin/env python3
"""
Test script to verify Tier 1 AI Analysis System
Simulates user clicking on economic calendar events
Tests both pre-event and post-event analysis
"""

import requests
import json
from datetime import datetime
from colorama import init, Fore, Style
import sys

# Initialize colorama for colored output
init(autoreset=True)

# Backend URL (adjust if needed)
BACKEND_URL = "http://localhost:5001"

def print_header(text):
    """Print formatted header"""
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{text:^80}")
    print(f"{Fore.CYAN}{'=' * 80}\n")

def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN}✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"{Fore.RED}❌ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠️  {text}")

def print_info(text):
    """Print info message"""
    print(f"{Fore.BLUE}ℹ️  {text}")

def print_field(field_name, value, indent=0):
    """Print a field with its value"""
    indent_str = "  " * indent
    if isinstance(value, dict):
        print(f"{indent_str}{Fore.MAGENTA}{field_name}:")
        for k, v in value.items():
            print_field(k, v, indent + 1)
    elif isinstance(value, list):
        print(f"{indent_str}{Fore.MAGENTA}{field_name}: {Fore.WHITE}[{len(value)} items]")
        for i, item in enumerate(value[:3]):  # Show first 3 items
            if isinstance(item, str):
                print(f"{indent_str}  - {item[:100]}...")
            else:
                print(f"{indent_str}  - {item}")
    elif isinstance(value, str) and len(value) > 100:
        print(f"{indent_str}{Fore.MAGENTA}{field_name}: {Fore.WHITE}{value[:100]}...")
    else:
        print(f"{indent_str}{Fore.MAGENTA}{field_name}: {Fore.WHITE}{value}")

# Test events
TEST_EVENTS = [
    {
        "name": "Pre-Event NFP (No actual data)",
        "event": {
            "id": "test_nfp_pre",
            "title": "US Non-Farm Payrolls",
            "currency": "USD",
            "date": "Fri, Nov 1",
            "time": "12:30 UTC",
            "impact": "high",
            "previous": "254K",
            "expected": "150K",
            "actual": "",  # No actual data yet
            "forecast": "150K"
        },
        "analysisType": "pre-event",
        "should_be": "pre-event"
    },
    {
        "name": "Post-Event NFP (With actual data)",
        "event": {
            "id": "test_nfp_post",
            "title": "US Non-Farm Payrolls",
            "currency": "USD",
            "date": "Fri, Nov 1",
            "time": "12:30 UTC",
            "impact": "high",
            "previous": "254K",
            "expected": "150K",
            "actual": "180K",  # Actual data available
            "forecast": "150K"
        },
        "analysisType": "post-event",
        "should_be": "post-event"
    },
    {
        "name": "Pre-Event CPI (No actual data)",
        "event": {
            "id": "test_cpi_pre",
            "title": "US Consumer Price Index (CPI)",
            "currency": "USD",
            "date": "Wed, Oct 30",
            "time": "12:30 UTC",
            "impact": "high",
            "previous": "3.2%",
            "expected": "3.1%",
            "actual": "",  # No actual data yet
            "forecast": "3.1%"
        },
        "analysisType": "pre-event",
        "should_be": "pre-event"
    },
    {
        "name": "Post-Event CPI (With actual data)",
        "event": {
            "id": "test_cpi_post",
            "title": "US Consumer Price Index (CPI)",
            "currency": "USD",
            "date": "Wed, Oct 30",
            "time": "12:30 UTC",
            "impact": "high",
            "previous": "3.2%",
            "expected": "3.1%",
            "actual": "3.0%",  # Actual data available
            "forecast": "3.1%"
        },
        "analysisType": "post-event",
        "should_be": "post-event"
    }
]

# Required fields in GPTAnalysisResult
REQUIRED_FIELDS = [
    'headline',
    'key_takeaway',
    'forward_scenarios',
    'event_summary',
    'market_reaction',
    'implications_takeaways',
    'trading_plan',
    'big_picture',
    'positioning_context',
    'next_catalysts',
    'confidence_score',
    'analysis_timestamp',
    'event_id',
    'analysis_type',
    'model_used',
    'cost_estimate',
    'cache_hit',
    'data_quality',
    'validation_status',
    'market_data_source'
]

# Required nested fields
REQUIRED_NESTED_FIELDS = {
    'forward_scenarios': ['bullish', 'bearish', 'neutral'],
    'event_summary': ['release', 'outcome'],
    'market_reaction': ['price_action', 'volatility'],
    'implications_takeaways': ['economic_context', 'policy_implications', 'market_bias'],
    'trading_plan': ['best_approach', 'key_levels'],
    'big_picture': ['economic_outlook', 'medium_term_direction'],
    'positioning_context': ['retail_sentiment', 'market_bias']
}

def check_backend_status():
    """Check if backend is running"""
    print_header("CHECKING BACKEND STATUS")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Backend is running at {BACKEND_URL}")
            return True
        else:
            print_error(f"Backend responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to backend at {BACKEND_URL}")
        print_warning("Make sure the backend is running:")
        print_info("cd backend && python3 app.py")
        return False
    except Exception as e:
        print_error(f"Error checking backend: {e}")
        return False

def validate_response_structure(response_data, event_name):
    """Validate that response has all required fields"""
    print(f"\n{Fore.YELLOW}📋 Validating Response Structure for: {event_name}")
    
    all_valid = True
    missing_fields = []
    
    # Check top-level required fields
    for field in REQUIRED_FIELDS:
        if field not in response_data:
            missing_fields.append(field)
            print_error(f"Missing required field: {field}")
            all_valid = False
        else:
            print_success(f"Found field: {field}")
    
    # Check nested required fields
    for parent_field, child_fields in REQUIRED_NESTED_FIELDS.items():
        if parent_field in response_data:
            parent_data = response_data[parent_field]
            if isinstance(parent_data, dict):
                for child_field in child_fields:
                    if child_field not in parent_data:
                        missing_fields.append(f"{parent_field}.{child_field}")
                        print_warning(f"Missing nested field: {parent_field}.{child_field}")
                    else:
                        print_success(f"Found nested field: {parent_field}.{child_field}")
    
    if all_valid:
        print_success(f"\n✅ ALL REQUIRED FIELDS PRESENT ({len(REQUIRED_FIELDS)} fields)")
    else:
        print_error(f"\n❌ MISSING {len(missing_fields)} REQUIRED FIELDS")
        print_error(f"Missing: {', '.join(missing_fields)}")
    
    return all_valid

def test_analysis_endpoint(test_case):
    """Test the enhanced analysis endpoint with a test event"""
    print_header(f"TEST: {test_case['name']}")
    
    event = test_case['event']
    analysis_type = test_case['analysisType']
    
    print_info(f"Event: {event['title']}")
    print_info(f"Currency: {event['currency']}")
    print_info(f"Impact: {event['impact']}")
    print_info(f"Expected: {event.get('expected', 'N/A')}")
    print_info(f"Actual: {event.get('actual', 'N/A') or 'Not available yet'}")
    print_info(f"Analysis Type: {analysis_type}")
    
    # Prepare request
    url = f"{BACKEND_URL}/api/enhanced-analysis/{event['id']}"
    request_data = {
        "event": event,
        "analysisType": analysis_type,
        "marketContext": {
            "currentTime": datetime.now().isoformat(),
            "eventTime": datetime.now().isoformat(),
            "isPostEvent": analysis_type == "post-event"
        }
    }
    
    print(f"\n{Fore.CYAN}🚀 Sending POST request to: {url}")
    
    try:
        # Make the request
        response = requests.post(
            url,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"{Fore.CYAN}📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Analysis generated successfully!")
            
            # Parse response
            analysis_data = response.json()
            
            # Validate structure
            is_valid = validate_response_structure(analysis_data, test_case['name'])
            
            # Print key analysis details
            print(f"\n{Fore.YELLOW}📊 ANALYSIS DETAILS:")
            print(f"{Fore.YELLOW}{'-' * 80}")
            
            # Core fields
            if 'headline' in analysis_data:
                print_field('headline', analysis_data['headline'])
            
            if 'key_takeaway' in analysis_data:
                print_field('key_takeaway', analysis_data['key_takeaway'])
            
            if 'model_used' in analysis_data:
                print_field('model_used', analysis_data['model_used'])
            
            if 'confidence_score' in analysis_data:
                print_field('confidence_score', analysis_data['confidence_score'])
            
            if 'analysis_type' in analysis_data:
                expected_type = test_case['should_be']
                actual_type = analysis_data['analysis_type']
                if actual_type == expected_type:
                    print_success(f"Analysis type correct: {actual_type}")
                else:
                    print_error(f"Analysis type mismatch: expected {expected_type}, got {actual_type}")
            
            if 'cache_hit' in analysis_data:
                cache_status = "✅ FROM CACHE" if analysis_data['cache_hit'] else "🆕 FRESH ANALYSIS"
                print_info(f"Cache Status: {cache_status}")
            
            if 'cost_estimate' in analysis_data:
                cost = analysis_data['cost_estimate']
                print_info(f"Cost Estimate: ${cost:.4f}")
            
            if 'data_quality' in analysis_data:
                print_info(f"Data Quality: {analysis_data['data_quality']}")
            
            if 'validation_status' in analysis_data:
                print_info(f"Validation Status: {analysis_data['validation_status']}")
            
            # Forward scenarios
            if 'forward_scenarios' in analysis_data:
                print(f"\n{Fore.YELLOW}🔮 FORWARD SCENARIOS:")
                scenarios = analysis_data['forward_scenarios']
                if 'bullish' in scenarios:
                    print(f"{Fore.GREEN}  📈 Bullish: {scenarios['bullish'][:100]}...")
                if 'bearish' in scenarios:
                    print(f"{Fore.RED}  📉 Bearish: {scenarios['bearish'][:100]}...")
                if 'neutral' in scenarios:
                    print(f"{Fore.YELLOW}  ➡️  Neutral: {scenarios['neutral'][:100]}...")
            
            # Market reaction
            if 'market_reaction' in analysis_data:
                print(f"\n{Fore.YELLOW}📊 MARKET REACTION:")
                reaction = analysis_data['market_reaction']
                if 'price_action' in reaction:
                    print(f"  {reaction['price_action'][:150]}...")
                if 'volatility' in reaction:
                    print(f"  Volatility: {reaction['volatility']}")
            
            # Trading plan
            if 'trading_plan' in analysis_data:
                print(f"\n{Fore.YELLOW}💼 TRADING PLAN:")
                plan = analysis_data['trading_plan']
                if 'best_approach' in plan:
                    print(f"  {plan['best_approach'][:150]}...")
                if 'key_levels' in plan:
                    print(f"  Key Levels: {plan['key_levels'][:150]}...")
            
            # Next catalysts
            if 'next_catalysts' in analysis_data:
                print(f"\n{Fore.YELLOW}🎯 NEXT CATALYSTS:")
                for i, catalyst in enumerate(analysis_data['next_catalysts'][:3], 1):
                    print(f"  {i}. {catalyst}")
            
            print(f"\n{Fore.YELLOW}{'-' * 80}")
            
            if is_valid:
                print_success(f"\n✅ TEST PASSED: {test_case['name']}")
                return True
            else:
                print_error(f"\n❌ TEST FAILED: Missing required fields")
                return False
            
        elif response.status_code == 503:
            print_error("Service Unavailable (503)")
            error_data = response.json()
            print_error(f"Error: {error_data.get('error', 'Unknown error')}")
            print_warning(f"Message: {error_data.get('message', 'No message')}")
            print_warning("This means GPT analyzer is not initialized. Check OpenAI API key.")
            return False
            
        elif response.status_code == 400:
            print_error("Bad Request (400)")
            error_data = response.json()
            print_error(f"Error: {error_data.get('error', 'Unknown error')}")
            if 'validation_errors' in error_data:
                print_error(f"Validation Errors: {error_data['validation_errors']}")
            return False
            
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return False
        
    except requests.exceptions.Timeout:
        print_error("Request timed out (>30 seconds)")
        print_warning("This might happen if OpenAI API is slow. Try again.")
        return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {url}")
        print_warning("Make sure the backend is running.")
        return False
    except Exception as e:
        print_error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print_header("TIER 1 AI ANALYSIS SYSTEM TEST")
    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Test Cases: {len(TEST_EVENTS)}")
    print_info(f"Required Fields: {len(REQUIRED_FIELDS)}")
    
    # Check backend is running
    if not check_backend_status():
        sys.exit(1)
    
    # Run tests
    results = []
    for i, test_case in enumerate(TEST_EVENTS, 1):
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}TEST {i}/{len(TEST_EVENTS)}")
        print(f"{Fore.CYAN}{'=' * 80}")
        
        result = test_analysis_endpoint(test_case)
        results.append({
            'name': test_case['name'],
            'passed': result
        })
        
        # Wait a bit between tests to avoid rate limiting
        if i < len(TEST_EVENTS):
            print(f"\n{Fore.YELLOW}⏳ Waiting 2 seconds before next test...")
            import time
            time.sleep(2)
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for r in results if r['passed'])
    failed = len(results) - passed
    
    print(f"\n{Fore.CYAN}Total Tests: {len(results)}")
    print(f"{Fore.GREEN}Passed: {passed}")
    print(f"{Fore.RED}Failed: {failed}")
    
    print(f"\n{Fore.YELLOW}Individual Results:")
    for r in results:
        status = f"{Fore.GREEN}✅ PASS" if r['passed'] else f"{Fore.RED}❌ FAIL"
        print(f"  {status} - {r['name']}")
    
    if failed == 0:
        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"{Fore.GREEN}🎉 ALL TESTS PASSED! Tier 1 AI Analysis System is working correctly!")
        print(f"{Fore.GREEN}{'=' * 80}\n")
        sys.exit(0)
    else:
        print(f"\n{Fore.RED}{'=' * 80}")
        print(f"{Fore.RED}⚠️  SOME TESTS FAILED. Please check the output above for details.")
        print(f"{Fore.RED}{'=' * 80}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

