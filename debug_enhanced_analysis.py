#!/usr/bin/env python3
"""
Debug script to test enhanced analysis endpoint
"""

import requests
import json

def test_enhanced_analysis_debug():
    """Test the enhanced analysis endpoint with detailed debugging"""
    
    print("🔍 Debugging Enhanced Analysis Endpoint")
    print("=" * 50)
    
    # Test event data
    test_event = {
        "id": "test_debug_001",
        "title": "US Consumer Price Index (CPI)",
        "currency": "USD",
        "date": "2024-01-15",
        "time": "13:30",
        "expected": "3.1%",
        "previous": "3.2%",
        "actual": "3.0%",
        "impact": "High"
    }
    
    # Test request
    try:
        print("📡 Making request to enhanced-analysis endpoint...")
        print(f"   URL: http://localhost:5001/api/enhanced-analysis/test_debug_001")
        print(f"   Event: {test_event['title']}")
        
        response = requests.post(
            "http://localhost:5001/api/enhanced-analysis/test_debug_001",
            json={
                "event": test_event,
                "analysisType": "post-event",
                "marketContext": {
                    "currentTime": "2024-01-15T13:30:00Z",
                    "eventTime": "2024-01-15T13:30:00Z",
                    "isPostEvent": True
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            analysis = response.json()
            print("✅ Success! Enhanced analysis received:")
            print(f"   Model Used: {analysis.get('model_used', 'Unknown')}")
            print(f"   Headline: {analysis.get('headline', 'No headline')}")
            print(f"   Key Takeaway: {analysis.get('key_takeaway', 'No takeaway')}")
            print(f"   Confidence Score: {analysis.get('confidence_score', 'Unknown')}")
            
            if analysis.get('forward_scenarios'):
                print("✅ Forward scenarios present")
            else:
                print("⚠️ Forward scenarios not present")
                
        else:
            print(f"❌ Error Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"❌ Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"❌ Raw Error Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend server not running")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_health_endpoint():
    """Test the health endpoint"""
    
    print("\n🏥 Testing Health Endpoint...")
    
    try:
        response = requests.get("http://localhost:5001/api/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health Check: {health}")
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check Error: {e}")

def test_simple_analysis():
    """Test a simpler analysis endpoint"""
    
    print("\n🧪 Testing Simple Analysis...")
    
    try:
        response = requests.get("http://localhost:5001/api/analysis/1")
        print(f"📊 Simple Analysis Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Simple analysis works")
        else:
            print(f"❌ Simple analysis failed: {response.text}")
    except Exception as e:
        print(f"❌ Simple analysis error: {e}")

if __name__ == "__main__":
    test_health_endpoint()
    test_simple_analysis()
    test_enhanced_analysis_debug()
