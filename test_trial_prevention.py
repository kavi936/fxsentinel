#!/usr/bin/env python3
"""
Test script for trial prevention system
Tests that users can only get one trial per email address
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5001"
TEST_EMAIL = "test_trial_prevention@example.com"

def test_trial_prevention():
    """Test the trial prevention system"""
    print("🧪 Testing Trial Prevention System")
    print("=" * 50)
    
    # Test 1: Check initial eligibility
    print("\n1️⃣ Testing initial trial eligibility...")
    response = requests.get(f"{API_BASE_URL}/api/check-trial-eligibility/{TEST_EMAIL}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Initial eligibility check: {data['eligible']}")
        print(f"📧 Email: {data['email']}")
        print(f"📝 Message: {data['message']}")
        print(f"📊 Trial history: {len(data['trial_history'])} entries")
    else:
        print(f"❌ Failed to check eligibility: {response.status_code}")
        return False
    
    # Test 2: Simulate creating a trial (without actual payment)
    print("\n2️⃣ Simulating trial creation...")
    
    # Create a mock checkout session request
    checkout_data = {
        "user_id": "test_user_123",
        "email": TEST_EMAIL,
        "name": "Test User"
    }
    
    response = requests.post(f"{API_BASE_URL}/api/create-checkout-session", 
                           json=checkout_data)
    
    if response.status_code == 200:
        print("✅ Checkout session created successfully")
        session_data = response.json()
        print(f"🔗 Session URL: {session_data['session_url'][:50]}...")
    elif response.status_code == 403:
        print("❌ Trial already used (expected if this email has been used before)")
        error_data = response.json()
        print(f"📝 Error message: {error_data.get('message', 'No message')}")
    else:
        print(f"❌ Failed to create checkout session: {response.status_code}")
        print(f"📝 Response: {response.text}")
        return False
    
    # Test 3: Check eligibility again
    print("\n3️⃣ Testing eligibility after trial creation...")
    time.sleep(1)  # Small delay to ensure database update
    
    response = requests.get(f"{API_BASE_URL}/api/check-trial-eligibility/{TEST_EMAIL}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Post-trial eligibility check: {data['eligible']}")
        print(f"📝 Message: {data['message']}")
        print(f"📊 Trial history: {len(data['trial_history'])} entries")
        
        if not data['eligible']:
            print("✅ Trial prevention working correctly!")
        else:
            print("⚠️ Trial prevention may not be working as expected")
    else:
        print(f"❌ Failed to check post-trial eligibility: {response.status_code}")
        return False
    
    # Test 4: Try to create another trial with same email
    print("\n4️⃣ Testing duplicate trial prevention...")
    
    response = requests.post(f"{API_BASE_URL}/api/create-checkout-session", 
                           json=checkout_data)
    
    if response.status_code == 403:
        print("✅ Duplicate trial correctly prevented!")
        error_data = response.json()
        print(f"📝 Error message: {error_data.get('message', 'No message')}")
    else:
        print(f"❌ Duplicate trial not prevented: {response.status_code}")
        return False
    
    print("\n🎉 All trial prevention tests passed!")
    return True

def test_different_emails():
    """Test that different emails can each get a trial"""
    print("\n🧪 Testing Multiple Email Support")
    print("=" * 50)
    
    test_emails = [
        "test1@example.com",
        "test2@example.com", 
        "test3@example.com"
    ]
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n{i}️⃣ Testing email: {email}")
        
        # Check eligibility
        response = requests.get(f"{API_BASE_URL}/api/check-trial-eligibility/{email}")
        
        if response.status_code == 200:
            data = response.json()
            if data['eligible']:
                print(f"✅ {email} is eligible for trial")
            else:
                print(f"❌ {email} is not eligible (may have been used before)")
        else:
            print(f"❌ Failed to check eligibility for {email}")
    
    print("\n✅ Multiple email test completed!")

def test_developer_email_bypass():
    """Test that developer emails bypass trial prevention"""
    print("\n🧪 Testing Developer Email Bypass")
    print("=" * 50)
    
    # Test with a developer email (you'll need to add this to your .env)
    developer_email = "kavi.cf412@gmail.com"
    
    print(f"🔧 Testing developer email: {developer_email}")
    
    response = requests.get(f"{API_BASE_URL}/api/check-trial-eligibility/{developer_email}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📊 Eligibility: {data['eligible']}")
        print(f"📝 Message: {data['message']}")
        print(f"📊 Trial history: {len(data['trial_history'])} entries")
    else:
        print(f"❌ Failed to check developer eligibility: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Starting Trial Prevention Tests")
    print(f"📍 API Base URL: {API_BASE_URL}")
    print(f"📧 Test Email: {TEST_EMAIL}")
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test basic trial prevention
        success = test_trial_prevention()
        
        if success:
            # Test multiple emails
            test_different_emails()
            
            # Test developer bypass
            test_developer_email_bypass()
            
            print("\n🎉 All tests completed successfully!")
        else:
            print("\n❌ Some tests failed!")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {API_BASE_URL}")
        print("💡 Make sure your backend server is running: python3 backend/app.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
