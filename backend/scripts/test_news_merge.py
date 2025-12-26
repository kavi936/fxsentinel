#!/usr/bin/env python3
"""
Test script to simulate new news and verify merge/save logic works correctly
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_news_merge():
    """Test the news merge and save logic"""
    print("=" * 80)
    print("TESTING NEWS MERGE LOGIC")
    print("=" * 80)
    
    from services.persistent_news_cache import get_persistent_news_cache
    news_cache = get_persistent_news_cache()
    
    # Load current cache
    print("\n1. Loading current cache...")
    cached_news = news_cache.load_news() or []
    print(f"   ✅ Loaded {len(cached_news)} cached articles")
    
    # Create some fake "new" articles
    print("\n2. Creating test 'new' articles...")
    new_articles = []
    for i in range(3):
        new_article = {
            'id': f'test_new_{datetime.now().timestamp()}_{i}',
            'title': f'TEST NEW ARTICLE {i+1}: Breaking Forex News - Test {datetime.now().strftime("%H:%M:%S")}',
            'summary': f'This is a test article {i+1} to verify merge logic works',
            'source': 'Test Source',
            'url': f'https://test.com/article{i+1}',
            'published_at': datetime.now().isoformat(),
            'added_to_feed_at': datetime.now().isoformat(),
            'impact': 'high',
            'currency_pairs': ['EUR/USD', 'USD/JPY'],
            'type': 'TEST'
        }
        new_articles.append(new_article)
    
    print(f"   ✅ Created {len(new_articles)} test articles")
    for i, article in enumerate(new_articles, 1):
        print(f"      {i}. {article['title']}")
    
    # Simulate merge: new articles + cached articles
    print("\n3. Simulating merge (new articles + cached articles)...")
    all_news = new_articles + cached_news
    print(f"   ✅ Merged list: {len(all_news)} total ({len(new_articles)} new + {len(cached_news)} cached)")
    
    # Save merged list to cache
    print("\n4. Saving merged list to cache...")
    save_success = news_cache.save_news(all_news, append=False)
    if save_success:
        print(f"   ✅ Successfully saved {len(all_news)} articles to cache")
    else:
        print(f"   ❌ Failed to save to cache")
        return
    
    # Reload cache to verify
    print("\n5. Reloading cache to verify...")
    reloaded_news = news_cache.load_news() or []
    print(f"   ✅ Reloaded {len(reloaded_news)} articles from cache")
    
    # Check if new articles are at the top
    print("\n6. Verifying new articles are at the top...")
    test_articles_found = []
    for i, article in enumerate(reloaded_news[:10], 1):  # Check first 10
        if article.get('type') == 'TEST':
            test_articles_found.append((i, article))
            print(f"   ✅ Test article found at position {i}: {article.get('title', 'No title')[:60]}...")
    
    if len(test_articles_found) == len(new_articles):
        print(f"\n   ✅ SUCCESS: All {len(new_articles)} test articles are at the top of the cache!")
    else:
        print(f"\n   ⚠️  WARNING: Only found {len(test_articles_found)}/{len(new_articles)} test articles")
        print(f"      Expected them at positions 1-{len(new_articles)}, but found at: {[pos for pos, _ in test_articles_found]}")
    
    # Check sorting
    print("\n7. Verifying sorting by added_to_feed_at...")
    sorted_news = sorted(reloaded_news, key=lambda x: x.get('added_to_feed_at') or x.get('published_at') or '', reverse=True)
    is_sorted = reloaded_news == sorted_news
    if is_sorted:
        print(f"   ✅ Cache is properly sorted (newest first)")
    else:
        print(f"   ⚠️  Cache is NOT properly sorted")
        print(f"      First 3 articles:")
        for i, article in enumerate(reloaded_news[:3], 1):
            print(f"         {i}. {article.get('title', 'No title')[:50]}... (added: {article.get('added_to_feed_at', 'N/A')})")
    
    # Cleanup: Remove test articles
    print("\n8. Cleaning up test articles...")
    cleaned_news = [item for item in reloaded_news if item.get('type') != 'TEST']
    news_cache.save_news(cleaned_news, append=False)
    print(f"   ✅ Removed {len(new_articles)} test articles, saved {len(cleaned_news)} articles back to cache")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_news_merge()

