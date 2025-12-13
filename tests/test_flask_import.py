#!/usr/bin/env python3
"""
Test if Flask can import the sync wrapper
"""

import sys
import os
sys.path.append('backend')

def test_flask_import():
    """Test Flask-style import"""
    
    print("🔍 Testing Flask Import")
    print("=" * 50)
    
    # Test 1: Import the sync wrapper
    print("\n1️⃣ Testing sync wrapper import...")
    try:
        from services.telegram_sync_wrapper import telegram_sync
        print("✅ Successfully imported telegram_sync")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return
    
    # Test 2: Call the sync wrapper
    print("\n2️⃣ Testing sync wrapper call...")
    try:
        result = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Sync wrapper returned: {len(result)} articles")
        
        if result:
            print("📰 Sample articles:")
            for i, news in enumerate(result[:3]):
                print(f"   {i+1}. {news.get('title', 'No title')}")
                print(f"      Source: {news.get('source', 'Unknown')}")
        else:
            print("❌ No articles returned")
            
    except Exception as e:
        print(f"❌ Sync wrapper call error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flask_import()
