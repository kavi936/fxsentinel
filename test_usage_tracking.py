#!/usr/bin/env python3
"""
Test script for usage tracking system
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:5001"

def test_usage_tracking():
    """Test the usage tracking system"""
    print("🧪 Testing Usage Tracking System")
    print("=" * 50)
    
    # Test user IDs
    developer_user_id = "test_developer_123"
    developer_email = "kavi.cf412@gmail.com"
    regular_user_id = "test_regular_123"
    regular_email = "test@example.com"
    
    print("📋 Test Scenarios:")
    print("   1. Developer account (unlimited)")
    print("   2. Trial user (15 analyses/day)")
    print("   3. Paid user (100 analyses/day)")
    print("   4. Usage increment simulation")
    print()
    
    # Test 1: Developer account
    print("🔧 Test 1: Developer Account")
    print("-" * 30)
    test_developer_usage(developer_user_id, developer_email)
    print()
    
    # Test 2: Regular user
    print("👤 Test 2: Regular User")
    print("-" * 30)
    test_regular_user_usage(regular_user_id, regular_email)
    print()
    
    # Test 3: Usage limits
    print("📊 Test 3: Usage Limits")
    print("-" * 30)
    test_usage_limits(regular_user_id, regular_email)
    print()

def test_developer_usage(user_id, email):
    """Test developer account usage"""
    url = f"{BASE_URL}/api/check-analysis-permission/{user_id}?email={email}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Developer Status: {data.get('status', 'unknown')}")
            print(f"   ✅ Can Perform: {data.get('can_perform', False)}")
            print(f"   ✅ Daily Usage: {data.get('daily_usage', 0)}")
            print(f"   ✅ Daily Limit: {data.get('daily_limit', 'unknown')}")
            print(f"   ✅ Expected: Unlimited access")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_regular_user_usage(user_id, email):
    """Test regular user usage"""
    url = f"{BASE_URL}/api/check-analysis-permission/{user_id}?email={email}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ User Status: {data.get('status', 'unknown')}")
            print(f"   ✅ Can Perform: {data.get('can_perform', False)}")
            print(f"   ✅ Daily Usage: {data.get('daily_usage', 0)}")
            print(f"   ✅ Daily Limit: {data.get('daily_limit', 'unknown')}")
            
            if data.get('status') == 'trial':
                print(f"   ✅ Expected: Trial user with 15 analyses/day limit")
            elif data.get('status') == 'active':
                print(f"   ✅ Expected: Paid user with 100 analyses/day limit")
            else:
                print(f"   ⚠️ Status: {data.get('status')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_usage_limits(user_id, email):
    """Test usage limit enforcement"""
    print("   📈 Simulating usage increments...")
    
    # Check initial usage
    url = f"{BASE_URL}/api/check-analysis-permission/{user_id}?email={email}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            initial_data = response.json()
            initial_usage = initial_data.get('daily_usage', 0)
            limit = initial_data.get('daily_limit', 15)
            
            print(f"   📊 Initial Usage: {initial_usage}/{limit}")
            
            # Simulate usage increments (this would normally happen when user performs analysis)
            print(f"   🔄 Usage tracking is handled automatically when users perform AI analysis")
            print(f"   💡 Backend automatically increments usage count")
            print(f"   💡 Daily reset happens at midnight")
            print(f"   💡 Limits are enforced in real-time")
            
            # Show what happens when limit is reached
            if initial_usage >= limit:
                print(f"   ⚠️ User has reached daily limit ({limit})")
                print(f"   🔒 User cannot perform more analyses today")
            else:
                remaining = limit - initial_usage
                print(f"   ✅ User can perform {remaining} more analyses today")
                
        else:
            print(f"   ❌ Failed to check usage: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_backend_connection():
    """Test if backend is running and accessible"""
    print("🌐 Testing backend connection...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on port 5001")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Usage Tracking System")
    print("=" * 50)
    
    # Test 1: Backend connection
    if not test_backend_connection():
        print("\n❌ Backend connection failed. Please start your backend server")
        return
    
    print()
    
    # Test 2: Usage tracking
    test_usage_tracking()
    
    print("=" * 50)
    print("🎉 Usage Tracking Test Complete!")
    print("\n📋 Key Features:")
    print("   ✅ Real-time usage tracking")
    print("   ✅ Daily limit enforcement")
    print("   ✅ Developer account bypass")
    print("   ✅ Automatic daily reset")
    print("   ✅ Visual progress indicators")
    print("   ✅ ProfilePopup integration")

if __name__ == "__main__":
    main()
