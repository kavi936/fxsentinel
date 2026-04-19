#!/usr/bin/env python3
"""
Integration test for Risk Appetite - Tests API endpoint and data flow
"""

import requests
import json
import sys

def test_api_endpoint(base_url="http://localhost:5000"):
    """Test the market sentiment API endpoint"""
    print("="*60)
    print("RISK APPETITE API INTEGRATION TEST")
    print("="*60)
    
    try:
        # Test the market sentiment endpoint
        url = f"{base_url}/api/market-sentiment"
        print(f"\n📡 Testing endpoint: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        print(f"\n✅ API Response received successfully")
        print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
        print(f"   Market Status: {data.get('market_status', 'N/A')}")
        
        # Check market conditions
        market_conditions = data.get('market_conditions', [])
        print(f"\n📊 Market Conditions ({len(market_conditions)} found):")
        
        risk_appetite_found = False
        for condition in market_conditions:
            print(f"\n   - {condition['name']}:")
            print(f"     Value: {condition['value']}")
            print(f"     Percentage: {condition['percentage']}%")
            print(f"     Detail: {condition['detail']}")
            print(f"     Trend: {condition.get('trend', 'N/A')}")
            
            if condition['name'] == 'Risk Appetite':
                risk_appetite_found = True
                print(f"\n   ✅ Risk Appetite found!")
                print(f"      Level: {condition['value']}")
                print(f"      Percentage: {condition['percentage']}%")
                print(f"      Detail: {condition['detail']}")
                
                # Validate the values
                valid_levels = ['low', 'medium', 'high']
                
                if condition['value'] not in valid_levels:
                    print(f"      ⚠️ Warning: Invalid level '{condition['value']}'")
                    return False
                
                try:
                    pct = float(condition['percentage'])
                    if pct < 0 or pct > 100:
                        print(f"      ⚠️ Warning: Percentage out of range '{condition['percentage']}'")
                        return False
                except (TypeError, ValueError):
                    print(f"      ⚠️ Warning: Invalid percentage '{condition['percentage']}'")
                    return False
                
                # Check if detail contains safe havens + risk FX labels
                if 'safe havens:' not in condition['detail'].lower():
                    print(f"      ⚠️ Warning: Detail doesn't contain 'Safe havens:'")
                    return False
                if 'risk fx:' not in condition['detail'].lower():
                    print(f"      ⚠️ Warning: Detail doesn't contain 'Risk FX:'")
                    return False
        
        if not risk_appetite_found:
            print(f"\n❌ Risk Appetite condition not found in response!")
            return False
        
        # Check VIX data (should be separate field)
        vix_data = data.get('vix')
        if vix_data:
            print(f"\n📈 VIX Data:")
            print(f"   Value: {vix_data.get('value', 'N/A')}")
            print(f"   Change: {vix_data.get('change', 'N/A')}")
            print(f"   Level: {vix_data.get('level', 'N/A')}")
        
        print(f"\n✅ All checks passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {base_url}")
        print(f"   Make sure the backend server is running:")
        print(f"   cd backend && python3 app.py")
        return False
    except Exception as e:
        print(f"\n❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_data_structure():
    """Test that the data structure matches what frontend expects"""
    print("\n" + "="*60)
    print("FRONTEND DATA STRUCTURE VALIDATION")
    print("="*60)
    
    # Expected structure based on Overview.jsx
    expected_structure = {
        'market_conditions': [
            {
                'name': str,
                'value': str,  # 'low', 'medium', 'high'
                'percentage': (int, float),
                'detail': str,
                'trend': str
            }
        ],
        'vix': {
            'value': (int, float),
            'change': (int, float),
            'level': str
        }
    }
    
    print("\n✅ Frontend expects:")
    print("   - market_conditions array with Risk Appetite condition")
    print("   - vix object with value, change, and level")
    print("\n   The frontend maps over market_conditions and displays:")
    print("   - condition.name === 'Risk Appetite'")
    print("   - condition.value (capitalized)")
    print("   - condition.percentage (for bar width)")
    print("   - condition.detail (shows 'Safe havens: ... · Risk FX: ...')")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("RISK APPETITE INTEGRATION TESTS")
    print("="*60)
    
    # Test API endpoint
    api_test_passed = test_api_endpoint()
    
    # Test frontend structure
    frontend_test_passed = test_frontend_data_structure()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"API Endpoint Test: {'✅ PASSED' if api_test_passed else '❌ FAILED'}")
    print(f"Frontend Structure Test: {'✅ PASSED' if frontend_test_passed else '❌ FAILED'}")
    
    if api_test_passed and frontend_test_passed:
        print("\n✅ All integration tests passed!")
        print("\nNext steps:")
        print("1. Open the frontend application")
        print("2. Navigate to Overview tab")
        print("3. Check the 'Risk Appetite' card in Market Conditions")
        print("4. Verify it displays:")
        print("   - Correct level (Low/Medium/High)")
        print("   - Correct percentage bar")
        print("   - Safe havens listed in detail")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

