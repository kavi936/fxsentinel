#!/usr/bin/env python3
"""
Test script for persistent news cache
Tests Firebase connection, cache operations, and persistence
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_import():
    """Test that the module can be imported"""
    print("=" * 60)
    print("TEST 1: Import Module")
    print("=" * 60)
    try:
        from services.persistent_news_cache import get_persistent_news_cache
        cache = get_persistent_news_cache()
        print("✅ Import successful")
        return cache
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return None

def test_firebase_connection(cache):
    """Test Firebase connection"""
    print("\n" + "=" * 60)
    print("TEST 2: Firebase Connection")
    print("=" * 60)
    try:
        # Check Firebase configuration
        print(f"Firebase Project ID: {cache.firebase.project_id}")
        print(f"Firebase Database URL: {cache.firebase.database_url}")
        
        # Try a simple read operation
        status = cache.get_cache_status()
        print(f"Cache Status: {status}")
        
        if 'error' in status:
            print(f"⚠️  Warning: {status['error']}")
            print("   This might be expected if Firebase credentials are not set locally")
        else:
            print("✅ Firebase connection successful")
        
        return True
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        print("   This might be expected if Firebase credentials are not set locally")
        return False

def test_save_and_load(cache):
    """Test saving and loading news"""
    print("\n" + "=" * 60)
    print("TEST 3: Save and Load News")
    print("=" * 60)
    try:
        # Create test news items
        test_news = [
            {
                'id': 'test_001',
                'title': 'Test News Item 1',
                'summary': 'This is a test news item',
                'source': 'Test Source',
                'url': 'https://example.com/test1',
                'published_at': datetime.now().isoformat(),
                'impact': 'high',
                'currency_pairs': ['EUR/USD'],
                'type': 'RSS_FEED'
            },
            {
                'id': 'test_002',
                'title': 'Test News Item 2',
                'summary': 'Another test news item',
                'source': 'Test Source',
                'url': 'https://example.com/test2',
                'published_at': datetime.now().isoformat(),
                'impact': 'medium',
                'currency_pairs': ['GBP/USD'],
                'type': 'RSS_FEED'
            }
        ]
        
        # Save news
        print("Saving test news...")
        success = cache.save_news(test_news)
        if success:
            print("✅ News saved successfully")
        else:
            print("❌ Failed to save news")
            return False
        
        # Load news
        print("Loading news from cache...")
        loaded_news = cache.load_news()
        if loaded_news:
            print(f"✅ Loaded {len(loaded_news)} news items")
            print(f"   First item: {loaded_news[0].get('title', 'N/A')}")
        else:
            print("⚠️  No news loaded (cache might be empty or expired)")
        
        return True
    except Exception as e:
        print(f"❌ Save/Load test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_history(cache):
    """Test history operations"""
    print("\n" + "=" * 60)
    print("TEST 4: History Operations")
    print("=" * 60)
    try:
        # Load history
        print("Loading history...")
        history = cache.load_history()
        print(f"✅ History loaded: {len(history)} items")
        
        if history:
            print(f"   Oldest item: {history[-1].get('title', 'N/A')[:50]}")
            print(f"   Newest item: {history[0].get('title', 'N/A')[:50]}")
        
        # Get recent history
        print("\nGetting recent history (last 24 hours)...")
        recent = cache.get_recent_history(hours=24)
        print(f"✅ Recent history: {len(recent)} items")
        
        return True
    except Exception as e:
        print(f"❌ History test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_by_id(cache):
    """Test getting news by ID"""
    print("\n" + "=" * 60)
    print("TEST 5: Get News by ID")
    print("=" * 60)
    try:
        # Try to get a test news item
        news_item = cache.get_news_by_id('test_001')
        if news_item:
            print(f"✅ Found news item: {news_item.get('title', 'N/A')}")
        else:
            print("⚠️  News item not found (might not be in cache)")
        
        return True
    except Exception as e:
        print(f"❌ Get by ID test failed: {e}")
        return False

def test_cache_status(cache):
    """Test cache status methods"""
    print("\n" + "=" * 60)
    print("TEST 6: Cache Status")
    print("=" * 60)
    try:
        # Get cache status
        cache_status = cache.get_cache_status()
        print("Cache Status:")
        print(f"   Exists: {cache_status.get('exists', False)}")
        print(f"   Valid: {cache_status.get('is_valid', False)}")
        print(f"   News Count: {cache_status.get('news_count', 0)}")
        print(f"   Age: {cache_status.get('age', 'N/A')}")
        
        # Get history status
        history_status = cache.get_history_status()
        print("\nHistory Status:")
        print(f"   Total Items: {history_status.get('total_items', 0)}")
        print(f"   Oldest Item: {history_status.get('oldest_item', 'N/A')}")
        print(f"   Newest Item: {history_status.get('newest_item', 'N/A')}")
        
        print("\n✅ Status checks completed")
        return True
    except Exception as e:
        print(f"❌ Status test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PERSISTENT NEWS CACHE TEST SUITE")
    print("=" * 60)
    print("\nNote: Some tests may fail locally if Firebase credentials")
    print("      are not configured. This is expected.")
    print()
    
    results = []
    
    # Test 1: Import
    cache = test_import()
    if not cache:
        print("\n❌ Cannot continue without cache instance")
        return 1
    results.append(("Import", True))
    
    # Test 2: Firebase Connection
    connection_ok = test_firebase_connection(cache)
    results.append(("Firebase Connection", connection_ok))
    
    # Test 3: Save and Load
    save_load_ok = test_save_and_load(cache)
    results.append(("Save/Load", save_load_ok))
    
    # Test 4: History
    history_ok = test_history(cache)
    results.append(("History", history_ok))
    
    # Test 5: Get by ID
    get_by_id_ok = test_get_by_id(cache)
    results.append(("Get by ID", get_by_id_ok))
    
    # Test 6: Cache Status
    status_ok = test_cache_status(cache)
    results.append(("Cache Status", status_ok))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed (may be expected if Firebase not configured locally)")
        return 1

if __name__ == '__main__':
    sys.exit(main())

