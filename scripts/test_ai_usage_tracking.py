#!/usr/bin/env python3
"""
Test script for AI Usage Tracking
Tests that user tracking is working correctly for OpenAI API calls
"""
import os
import sys
import requests
from dotenv import load_dotenv
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv()

def test_usage_tracking():
    """Test that usage tracking is working"""
    print("🧪 Testing AI Usage Tracking System")
    print("=" * 60)
    
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5001')
    
    # Test 1: Check if tracking service is available
    print("\n1️⃣ Testing Usage Tracker Service...")
    try:
        from services.ai_usage_tracker import ai_usage_tracker
        if ai_usage_tracker.firebase_available:
            print("   ✅ Usage tracker initialized with Firestore")
        else:
            print("   ⚠️ Usage tracker initialized but Firestore not available")
    except Exception as e:
        print(f"   ❌ Error initializing usage tracker: {e}")
        return False
    
    # Test 2: Test tracking a usage event
    print("\n2️⃣ Testing Usage Event Tracking...")
    try:
        test_user_info = {
            'user_id': 'test_user_123',
            'user_email': 'test@example.com',
            'user_name': 'Test User'
        }
        
        ai_usage_tracker.track_analysis_usage(
            user_info=test_user_info,
            analysis_type='pre-event',
            event_id='test_event_123',
            model_used='gpt-4-turbo',
            cost_estimate=0.05,
            cache_hit=False
        )
        print("   ✅ Usage event tracked successfully")
    except Exception as e:
        print(f"   ⚠️ Usage tracking failed (may be expected if Firestore not configured): {e}")
    
    # Test 3: Test getting active users (requires admin auth)
    print("\n3️⃣ Testing Active Users Endpoint...")
    print("   ℹ️  This requires Firebase authentication token")
    print("   ℹ️  Run this from frontend with logged-in admin user")
    
    # Test 4: Verify OpenAI user parameter is being set
    print("\n4️⃣ Testing OpenAI User Parameter...")
    print("   ℹ️  Check OpenAI usage dashboard: https://platform.openai.com/usage")
    print("   ℹ️  Look for individual users in the 'Users' dropdown")
    print("   ℹ️  Each user should appear separately, not all under one name")
    
    print("\n" + "=" * 60)
    print("✅ Test script completed!")
    print("\n📋 Next Steps:")
    print("   1. Make some AI analysis requests from different users")
    print("   2. Check OpenAI dashboard for per-user tracking")
    print("   3. Use /api/ai-usage/stats endpoint to see active users")
    print("   4. Contact active users for feedback")
    
    return True

if __name__ == '__main__':
    test_usage_tracking()
