#!/usr/bin/env python3
"""
Test Refund Request Functionality
Tests the new refund request endpoint to ensure it works properly
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')

def test_refund_request():
    """Test the refund request endpoint"""
    print("🧪 Testing Refund Request Functionality")
    print("=" * 50)
    
    # Test data
    test_data = {
        'email': 'test@example.com',
        'reason': 'not-satisfied',
        'details': 'This is a test refund request from the automated test script.'
    }
    
    print(f"📧 Testing refund request for: {test_data['email']}")
    print(f"📝 Reason: {test_data['reason']}")
    print(f"📄 Details: {test_data['details']}")
    print()
    
    try:
        # Make the request
        response = requests.post(
            f"{BASE_URL}/api/request-refund",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message', 'No message')}")
            print(f"📊 Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📊 Error Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Raw Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to the server")
        print(f"   Make sure the backend is running at: {BASE_URL}")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 What to check:")
    print("   1. Backend console should show refund request logs")
    print("   2. If email is configured, check fxsentinelapp@gmail.com")
    print("   3. If Firebase is configured, check refund_requests collection")
    print("   4. Frontend should show success message")

def test_refund_request_validation():
    """Test validation for refund request endpoint"""
    print("\n🧪 Testing Refund Request Validation")
    print("=" * 50)
    
    # Test missing email
    print("📧 Testing missing email...")
    test_data = {
        'reason': 'not-satisfied',
        'details': 'Test without email'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/request-refund",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ Validation working: Missing email rejected")
        else:
            print(f"❌ Validation failed: Expected 400, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    # Test missing reason
    print("\n📝 Testing missing reason...")
    test_data = {
        'email': 'test@example.com',
        'details': 'Test without reason'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/request-refund",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ Validation working: Missing reason rejected")
        else:
            print(f"❌ Validation failed: Expected 400, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 FXSentinel Refund Request Test")
    print(f"🌐 Testing against: {BASE_URL}")
    print()
    
    test_refund_request()
    test_refund_request_validation()
    
    print("\n✅ Test completed!")
    print("\n📋 Next Steps:")
    print("   1. Check backend logs for refund request processing")
    print("   2. Test the frontend refund form in the ProfilePopup")
    print("   3. Configure email settings in .env if you want actual emails")
    print("   4. Monitor Firebase refund_requests collection")
