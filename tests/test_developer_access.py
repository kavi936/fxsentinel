#!/usr/bin/env python3
"""
Test Developer Access System
Tests the developer email whitelist functionality
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:5001"

def test_developer_access():
    """Test developer email access functionality"""
    print("🧪 Testing Developer Access System")
    print("=" * 50)
    
    # Get developer emails from environment
    developer_emails_str = os.getenv('DEVELOPER_EMAILS', '')
    developer_emails = [email.strip() for email in developer_emails_str.split(',') if email.strip()]
    
    print(f"🔧 Developer emails configured: {developer_emails}")
    
    if not developer_emails:
        print("❌ No developer emails configured in DEVELOPER_EMAILS environment variable")
        print("   Add your email to .env file: DEVELOPER_EMAILS=your_email@example.com")
        return False
    
    # Test each developer email
    for email in developer_emails:
        print(f"\n📧 Testing developer email: {email}")
        
        # Test subscription status
        try:
            response = requests.get(
                f"{BASE_URL}/api/subscription-status/test_user",
                params={'email': email},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Subscription status: {data.get('status')}")
                print(f"   Daily limit: {data.get('analysis_limit')}")
                print(f"   Is developer: {data.get('is_developer', False)}")
                
                if data.get('status') == 'developer':
                    print("✅ Developer access confirmed!")
                else:
                    print("❌ Developer access not working")
                    return False
            else:
                print(f"❌ Failed to get subscription status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing subscription status: {e}")
            return False
        
        # Test analysis permission
        try:
            response = requests.get(
                f"{BASE_URL}/api/check-analysis-permission/test_user",
                params={'email': email},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Analysis permission: {data.get('can_perform')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Daily limit: {data.get('daily_limit')}")
                
                if data.get('can_perform') and data.get('status') == 'developer':
                    print("✅ Developer analysis access confirmed!")
                else:
                    print("❌ Developer analysis access not working")
                    return False
            else:
                print(f"❌ Failed to check analysis permission: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing analysis permission: {e}")
            return False
    
    print("\n🎉 All developer access tests passed!")
    return True

def test_regular_user_access():
    """Test that regular users don't get developer access"""
    print("\n🧪 Testing Regular User Access")
    print("=" * 50)
    
    regular_email = "regular_user@example.com"
    print(f"📧 Testing regular email: {regular_email}")
    
    # Test subscription status
    try:
        response = requests.get(
            f"{BASE_URL}/api/subscription-status/test_user",
            params={'email': regular_email},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Subscription status: {data.get('status')}")
            print(f"   Daily limit: {data.get('analysis_limit')}")
            print(f"   Is developer: {data.get('is_developer', False)}")
            
            if data.get('status') != 'developer':
                print("✅ Regular user correctly not given developer access!")
            else:
                print("❌ Regular user incorrectly given developer access")
                return False
        else:
            print(f"❌ Failed to get subscription status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing subscription status: {e}")
        return False
    
    print("🎉 Regular user access test passed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Developer Access Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("   Make sure your backend server is running: python3 backend/app.py")
        exit(1)
    
    # Run tests
    developer_test = test_developer_access()
    regular_test = test_regular_user_access()
    
    if developer_test and regular_test:
        print("\n🎉 All tests passed! Developer access system is working correctly.")
        print("\n📋 Next steps:")
        print("   1. Add your email to DEVELOPER_EMAILS in .env file")
        print("   2. Restart your backend server")
        print("   3. Test the payment system with real users")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        exit(1)
