#!/usr/bin/env python3
"""
Test Flask server's access to Telegram service
"""

import sys
import os
sys.path.append('backend')

def test_flask_telegram_access():
    """Test if Flask can access Telegram service"""
    
    print("🔍 Testing Flask Telegram Access")
    print("=" * 50)
    
    # Test 1: Check if we can import the Telegram service
    print("\n1️⃣ Testing Telegram service import...")
    try:
        from services.telegram_monitor_user import telegram_user_monitor
        print("✅ Successfully imported telegram_user_monitor")
        print(f"📱 Target channels: {telegram_user_monitor.target_channels}")
        print(f"🔑 API ID configured: {bool(telegram_user_monitor.api_id)}")
        print(f"🔑 API Hash configured: {bool(telegram_user_monitor.api_hash)}")
        print(f"📞 Phone configured: {bool(telegram_user_monitor.phone)}")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return
    
    # Test 2: Check if we can access the service directly
    print("\n2️⃣ Testing direct service access...")
    try:
        import asyncio
        
        # Test direct access
        result = asyncio.run(telegram_user_monitor.get_recent_telegram_news(hours=24))
        print(f"✅ Direct access: {len(result)} articles")
        
        if result:
            print("📰 Sample articles:")
            for i, news in enumerate(result[:3]):
                print(f"   {i+1}. {news.get('title', 'No title')}")
        else:
            print("❌ No articles from direct access")
            
    except Exception as e:
        print(f"❌ Direct access error: {e}")
    
    # Test 3: Check if there are any session lock issues
    print("\n3️⃣ Testing session lock...")
    try:
        import tempfile
        import fcntl
        
        # Check if there's a lock file
        lock_file_path = f"/tmp/telegram_session_fxsentinel_user_session.lock"
        if os.path.exists(lock_file_path):
            print(f"⚠️ Lock file exists: {lock_file_path}")
            
            # Try to acquire the lock
            try:
                with open(lock_file_path, 'w') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    print("✅ Can acquire lock (no other process using it)")
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except (IOError, OSError) as e:
                print(f"❌ Cannot acquire lock: {e}")
                print("   Another process may be using the session")
        else:
            print("✅ No lock file found")
            
    except Exception as e:
        print(f"❌ Lock test error: {e}")
    
    # Test 4: Check if the Flask app can access the service in a similar way
    print("\n4️⃣ Testing Flask-style access...")
    try:
        import asyncio
        
        # Simulate how Flask would call the service
        async def flask_style_call():
            try:
                # Create new event loop (like Flask does)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Call the service with timeout
                result = await asyncio.wait_for(
                    telegram_user_monitor.get_recent_telegram_news(hours=24),
                    timeout=15.0
                )
                
                loop.close()
                return result
            except asyncio.TimeoutError:
                print("⚠️ Flask-style call timed out")
                return []
            except Exception as e:
                print(f"❌ Flask-style call error: {e}")
                return []
            finally:
                try:
                    if 'loop' in locals() and not loop.is_closed():
                        loop.close()
                except:
                    pass
        
        result = asyncio.run(flask_style_call())
        print(f"✅ Flask-style access: {len(result)} articles")
        
        if result:
            print("📰 Sample articles:")
            for i, news in enumerate(result[:3]):
                print(f"   {i+1}. {news.get('title', 'No title')}")
        else:
            print("❌ No articles from Flask-style access")
            
    except Exception as e:
        print(f"❌ Flask-style access error: {e}")

if __name__ == "__main__":
    test_flask_telegram_access()
