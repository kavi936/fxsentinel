#!/usr/bin/env python3
"""
Test Telegram news fetching to see if it's working
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_telegram_news():
    """Test Telegram news fetching"""
    print("=" * 80)
    print("TESTING TELEGRAM NEWS FETCHING")
    print("=" * 80)
    print(f"Test time: {datetime.now().isoformat()}")
    
    try:
        print("\n1. Importing telegram_sync_wrapper...")
        from services.telegram_sync_wrapper import telegram_sync
        print("   ✅ Successfully imported")
        
        print("\n2. Checking if Telegram service is enabled...")
        if not telegram_sync.enabled:
            print("   ❌ Telegram service is NOT enabled")
            print("   This could be because:")
            print("   - Missing TELEGRAM_API_ID environment variable")
            print("   - Missing TELEGRAM_API_HASH environment variable")
            print("   - Missing Telegram session file")
            return
        print("   ✅ Telegram service is enabled")
        
        print("\n3. Fetching recent Telegram news (last 24 hours)...")
        try:
            articles = telegram_sync.get_recent_telegram_news(hours=24)
            print(f"   ✅ Successfully fetched {len(articles)} articles")
            
            if articles:
                print(f"\n   Articles by source:")
                sources = {}
                for article in articles:
                    source = article.get('source', 'Unknown')
                    sources[source] = sources.get(source, 0) + 1
                for source, count in sorted(sources.items()):
                    print(f"      - {source}: {count} articles")
                
                print(f"\n   Sample articles (first 5):")
                for i, article in enumerate(articles[:5], 1):
                    title = article.get('title', 'No title')
                    source = article.get('source', 'Unknown')
                    pub_date = article.get('published_at', 'N/A')
                    impact = article.get('impact', 'N/A')
                    print(f"      {i}. [{source}] {title[:60]}...")
                    print(f"         Published: {pub_date}")
                    print(f"         Impact: {impact}")
            else:
                print(f"   ⚠️  No articles returned")
                print(f"   This could mean:")
                print(f"   - No recent messages in the monitored channels")
                print(f"   - All messages were filtered out (not forex-related)")
                print(f"   - Channels are not accessible")
                
        except Exception as e:
            print(f"   ❌ Error fetching Telegram news: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        print(f"   ❌ Error importing telegram_sync_wrapper: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_telegram_news()

