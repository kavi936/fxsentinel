#!/usr/bin/env python3
"""
Debug test to check Flask server's import path
"""

import sys
import os

def test_flask_debug():
    """Test Flask server's import path"""
    
    print("🔍 Testing Flask Server Import Path")
    print("=" * 50)
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # Test 1: Try to import the sync wrapper
    print("\n1️⃣ Testing sync wrapper import...")
    try:
        from services.telegram_sync_wrapper import telegram_sync
        print("✅ Successfully imported telegram_sync")
    except Exception as e:
        print(f"❌ Import error: {e}")
        
        # Try alternative import paths
        print("\n2️⃣ Trying alternative import paths...")
        try:
            sys.path.append('backend')
            from services.telegram_sync_wrapper import telegram_sync
            print("✅ Successfully imported with backend path")
        except Exception as e2:
            print(f"❌ Alternative import error: {e2}")
            
            try:
                sys.path.append('.')
                from backend.services.telegram_sync_wrapper import telegram_sync
                print("✅ Successfully imported with relative path")
            except Exception as e3:
                print(f"❌ Relative import error: {e3}")
                return
    
    # Test 2: Call the sync wrapper
    print("\n3️⃣ Testing sync wrapper call...")
    try:
        result = telegram_sync.get_recent_telegram_news(hours=24)
        print(f"✅ Sync wrapper returned: {len(result)} articles")
        
        if result:
            print("📰 Sample articles:")
            for i, news in enumerate(result[:3]):
                print(f"   {i+1}. {news.get('title', 'No title')}")
        else:
            print("❌ No articles returned")
            
    except Exception as e:
        print(f"❌ Sync wrapper call error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flask_debug()
