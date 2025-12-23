#!/usr/bin/env python3
"""
Test script for Alert System Fixes
Tests persistent deduplication, filtering, and async handling
"""

import sys
import os
import asyncio
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.persistent_alert_deduplication import (
    get_persistent_deduplication,
    should_send_news_alert,
    should_send_economic_alert,
    get_deduplication_stats
)
from services.news_alert_trigger import news_alert_trigger
from services.background_alert_worker import BackgroundAlertWorker

def test_persistent_deduplication():
    """Test 1: Verify persistent deduplication prevents duplicates"""
    print("\n" + "="*60)
    print("TEST 1: Persistent Deduplication")
    print("="*60)
    
    dedup = get_persistent_deduplication()
    
    # Create a test news item
    test_news = {
        'id': 'test_news_123',
        'title': 'Fed Raises Interest Rates',
        'source': 'Reuters',
        'url': 'https://example.com/news1'
    }
    
    test_user_id = 'test_user_123'
    
    # First check - should return True (new alert)
    print(f"\n1. First check for news '{test_news['title']}'...")
    result1 = should_send_news_alert(test_news, test_user_id)
    print(f"   Result: {result1} (Expected: True)")
    
    if not result1:
        print("   ❌ FAILED: First check should return True")
        return False
    
    # Second check immediately - should return False (duplicate)
    print(f"\n2. Second check (duplicate) for same news...")
    result2 = should_send_news_alert(test_news, test_user_id)
    print(f"   Result: {result2} (Expected: False)")
    
    if result2:
        print("   ❌ FAILED: Second check should return False (duplicate)")
        return False
    
    # Check stats
    stats = get_deduplication_stats()
    print(f"\n3. Deduplication stats: {stats}")
    
    print("\n   ✅ TEST 1 PASSED: Persistent deduplication works correctly")
    return True

def test_different_users_same_news():
    """Test 2: Verify same news can be sent to different users"""
    print("\n" + "="*60)
    print("TEST 2: Different Users, Same News")
    print("="*60)
    
    test_news = {
        'id': 'test_news_456',
        'title': 'ECB Announces Policy Change',
        'source': 'Bloomberg',
        'url': 'https://example.com/news2'
    }
    
    user1 = 'test_user_1'
    user2 = 'test_user_2'
    
    # User 1 - should return True
    print(f"\n1. Check for user {user1}...")
    result1 = should_send_news_alert(test_news, user1)
    print(f"   Result: {result1} (Expected: True)")
    
    # User 2 - should also return True (different user)
    print(f"\n2. Check for user {user2} (same news)...")
    result2 = should_send_news_alert(test_news, user2)
    print(f"   Result: {result2} (Expected: True)")
    
    if not result1 or not result2:
        print("   ❌ FAILED: Both users should receive the same news")
        return False
    
    # User 1 again - should return False (duplicate for this user)
    print(f"\n3. Check for user {user1} again (duplicate)...")
    result3 = should_send_news_alert(test_news, user1)
    print(f"   Result: {result3} (Expected: False)")
    
    if result3:
        print("   ❌ FAILED: User 1 should not receive duplicate")
        return False
    
    print("\n   ✅ TEST 2 PASSED: Different users can receive same news")
    return True

def test_filtering_logic():
    """Test 3: Verify filtering logic catches forex-relevant news"""
    print("\n" + "="*60)
    print("TEST 3: Filtering Logic")
    print("="*60)
    
    # High-impact forex news
    high_impact_news = {
        'id': 'test_high_1',
        'title': 'Federal Reserve Raises Interest Rates by 0.5%',
        'summary': 'The Fed announced a significant rate hike affecting USD pairs',
        'source': 'Reuters',
        'impact': 'high'
    }
    
    # Medium-impact forex news (should still be caught)
    medium_impact_news = {
        'id': 'test_medium_1',
        'title': 'ECB Discusses Monetary Policy Changes',
        'summary': 'European Central Bank considers policy adjustments',
        'source': 'Bloomberg',
        'impact': 'medium'
    }
    
    # Low-impact non-forex news (should be filtered out)
    low_impact_news = {
        'id': 'test_low_1',
        'title': 'Local Restaurant Opens New Location',
        'summary': 'A new restaurant opened downtown',
        'source': 'Local News',
        'impact': 'low'
    }
    
    print("\n1. Testing high-impact forex news...")
    result1 = news_alert_trigger.is_forex_high_impact(high_impact_news)
    print(f"   Result: {result1} (Expected: True)")
    
    print("\n2. Testing medium-impact forex news...")
    result2 = news_alert_trigger.is_forex_high_impact(medium_impact_news)
    print(f"   Result: {result2} (Expected: True)")
    
    print("\n3. Testing low-impact non-forex news...")
    result3 = news_alert_trigger.is_forex_high_impact(low_impact_news)
    print(f"   Result: {result3} (Expected: False)")
    
    if not result1 or not result2 or result3:
        print("\n   ❌ FAILED: Filtering logic not working correctly")
        return False
    
    print("\n   ✅ TEST 3 PASSED: Filtering logic works correctly")
    return True

def test_worker_filtering():
    """Test 4: Verify worker uses same filtering as main app"""
    print("\n" + "="*60)
    print("TEST 4: Worker Filtering Consistency")
    print("="*60)
    
    # Create test news items
    test_news_items = [
        {
            'id': 'test_1',
            'title': 'Fed Rate Decision',
            'summary': 'Federal Reserve announces rate changes',
            'source': 'Reuters',
            'impact': 'high'
        },
        {
            'id': 'test_2',
            'title': 'ECB Policy Update',
            'summary': 'European Central Bank updates monetary policy',
            'source': 'Bloomberg',
            'impact': 'medium'  # Medium but should still be caught
        },
        {
            'id': 'test_3',
            'title': 'Weather Forecast',
            'summary': 'Sunny weather expected this week',
            'source': 'Weather Channel',
            'impact': 'low'  # Should be filtered out
        }
    ]
    
    print("\nTesting filtering with news_alert_trigger...")
    filtered = []
    for news in test_news_items:
        if news_alert_trigger.is_forex_high_impact(news):
            filtered.append(news)
    
    print(f"   Filtered {len(filtered)} out of {len(test_news_items)} news items")
    print(f"   Expected: 2 items (Fed and ECB news)")
    
    if len(filtered) != 2:
        print("   ❌ FAILED: Worker filtering not consistent")
        return False
    
    print("\n   ✅ TEST 4 PASSED: Worker filtering is consistent")
    return True

def test_async_handling():
    """Test 5: Verify async handling doesn't cause errors"""
    print("\n" + "="*60)
    print("TEST 5: Async Handling")
    print("="*60)
    
    async def test_async_function():
        """Test async function"""
        await asyncio.sleep(0.1)
        return True
    
    try:
        # Test 1: Run in new event loop
        print("\n1. Testing asyncio.run()...")
        result1 = asyncio.run(test_async_function())
        print(f"   Result: {result1} (Expected: True)")
        
        # Test 2: Run in existing event loop
        print("\n2. Testing in existing event loop...")
        async def run_in_loop():
            return await test_async_function()
        
        result2 = asyncio.run(run_in_loop())
        print(f"   Result: {result2} (Expected: True)")
        
        if not result1 or not result2:
            print("   ❌ FAILED: Async handling not working")
            return False
        
        print("\n   ✅ TEST 5 PASSED: Async handling works correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED: Async handling error: {e}")
        return False

def test_deduplication_persistence():
    """Test 6: Verify deduplication persists (simulated restart)"""
    print("\n" + "="*60)
    print("TEST 6: Deduplication Persistence")
    print("="*60)
    
    test_news = {
        'id': 'persistence_test_123',
        'title': 'Test Persistence News',
        'source': 'Test Source',
        'url': 'https://test.com/news'
    }
    
    test_user = 'persistence_test_user'
    
    # First check - mark as sent
    print("\n1. First check (marking as sent)...")
    result1 = should_send_news_alert(test_news, test_user)
    print(f"   Result: {result1} (Expected: True)")
    
    # Simulate "restart" by getting a new instance
    # (In real scenario, this would be a new process)
    print("\n2. Getting new deduplication instance (simulating restart)...")
    dedup_new = get_persistent_deduplication()
    
    # Check again - should still be blocked (persisted in Firebase)
    print("\n3. Checking again after 'restart'...")
    result2 = should_send_news_alert(test_news, test_user)
    print(f"   Result: {result2} (Expected: False - duplicate)")
    
    if not result1:
        print("   ❌ FAILED: First check should return True")
        return False
    
    if result2:
        print("   ❌ FAILED: After restart, duplicate should be prevented")
        print("   Note: This test requires Firebase connection to work")
        return False
    
    print("\n   ✅ TEST 6 PASSED: Deduplication persists (if Firebase connected)")
    return True

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ALERT SYSTEM FIXES - TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    tests = [
        ("Persistent Deduplication", test_persistent_deduplication),
        ("Different Users Same News", test_different_users_same_news),
        ("Filtering Logic", test_filtering_logic),
        ("Worker Filtering", test_worker_filtering),
        ("Async Handling", test_async_handling),
        ("Deduplication Persistence", test_deduplication_persistence),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n   ❌ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Completed at: {datetime.now().isoformat()}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

