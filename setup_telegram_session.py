#!/usr/bin/env python3
"""
Setup Telegram Session for WatcherGuru Monitoring
This script will authenticate the Telegram session to monitor WatcherGuru channel
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

async def setup_telegram_session():
    """Setup and authenticate Telegram session for WatcherGuru monitoring"""
    try:
        print("🔧 Setting up Telegram session for WatcherGuru monitoring...")
        print("=" * 60)
        
        # Check environment variables
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        if not all([api_id, api_hash, phone]):
            print("❌ Missing Telegram API credentials in .env file")
            print("Please ensure you have:")
            print("  TELEGRAM_API_ID=your_api_id")
            print("  TELEGRAM_API_HASH=your_api_hash")
            print("  TELEGRAM_PHONE=your_phone_number")
            return False
        
        print(f"✅ API ID: {api_id}")
        print(f"✅ API Hash: {api_hash[:10]}...")
        print(f"✅ Phone: {phone}")
        print()
        
        # Import and initialize Telegram monitor
        from backend.services.telegram_monitor_user import telegram_user_monitor
        
        print("🔐 Initializing Telegram client...")
        success = await telegram_user_monitor.initialize_client()
        
        if not success:
            print("❌ Failed to initialize Telegram client")
            return False
        
        print("✅ Telegram client initialized successfully")
        print()
        
        # Test connection to WatcherGuru channel
        print("📡 Testing connection to WatcherGuru channel...")
        messages = await telegram_user_monitor.get_channel_messages('WatcherGuru', limit=3)
        
        if messages:
            print(f"✅ Successfully connected to WatcherGuru! Found {len(messages)} messages")
            print()
            print("📰 Sample messages:")
            for i, msg in enumerate(messages[:3], 1):
                print(f"  {i}. {msg['title'][:80]}...")
            print()
        else:
            print("⚠️ No messages found from WatcherGuru (this might be normal if no recent posts)")
            print()
        
        # Test getting recent news
        print("🔄 Testing recent news fetch...")
        recent_news = await telegram_user_monitor.get_recent_telegram_news(hours=24)
        
        if recent_news:
            print(f"✅ Successfully fetched {len(recent_news)} recent news items")
            print()
            print("📊 News breakdown:")
            sources = {}
            for news in recent_news:
                source = news.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            
            for source, count in sources.items():
                print(f"  {source}: {count} articles")
        else:
            print("⚠️ No recent news found (this might be normal)")
        
        print()
        print("🎯 Session setup completed!")
        print("The Telegram session is now ready to monitor WatcherGuru for the live news feed.")
        print()
        print("Next steps:")
        print("1. Start the backend server: cd backend && python3 app.py")
        print("2. Force refresh news: curl -X POST http://localhost:5001/api/force-refresh-news")
        print("3. Check live news feed for WatcherGuru alerts")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Telegram session: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Always disconnect to clean up
        try:
            await telegram_user_monitor.disconnect()
        except:
            pass

if __name__ == "__main__":
    print("🚀 FXSentinel Telegram Session Setup")
    print("This will authenticate your Telegram session to monitor WatcherGuru")
    print()
    
    # Run the setup
    success = asyncio.run(setup_telegram_session())
    
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)
