#!/usr/bin/env python3
"""
Test to identify Telegram connection issues
"""

import sys
import os
import asyncio
sys.path.append('backend')

async def test_telegram_connection():
    """Test Telegram connection issues"""
    
    print("🔍 Testing Telegram Connection Issues")
    print("=" * 50)
    
    from services.telegram_monitor_user import telegram_user_monitor
    
    # Test 1: First connection
    print("\n1️⃣ Testing first connection...")
    try:
        result1 = await telegram_user_monitor.get_recent_telegram_news(hours=24)
        print(f"✅ First connection: {len(result1)} articles")
    except Exception as e:
        print(f"❌ First connection error: {e}")
        return
    
    # Test 2: Check client state after first use
    print("\n2️⃣ Checking client state after first use...")
    print(f"Client connected: {telegram_user_monitor.client and telegram_user_monitor.client.is_connected()}")
    print(f"Is connected flag: {telegram_user_monitor.is_connected}")
    
    # Test 3: Second connection attempt
    print("\n3️⃣ Testing second connection...")
    try:
        result2 = await telegram_user_monitor.get_recent_telegram_news(hours=24)
        print(f"✅ Second connection: {len(result2)} articles")
    except Exception as e:
        print(f"❌ Second connection error: {e}")
    
    # Test 4: Check if we can manually reconnect
    print("\n4️⃣ Testing manual reconnection...")
    try:
        # Force disconnect
        await telegram_user_monitor.disconnect()
        print("✅ Disconnected")
        
        # Try to reconnect
        connected = await telegram_user_monitor.ensure_connected()
        print(f"✅ Reconnection: {connected}")
        
        if connected:
            result3 = await telegram_user_monitor.get_recent_telegram_news(hours=24)
            print(f"✅ After reconnection: {len(result3)} articles")
        else:
            print("❌ Reconnection failed")
            
    except Exception as e:
        print(f"❌ Reconnection error: {e}")
    
    # Test 5: Test with fresh instance
    print("\n5️⃣ Testing with fresh instance...")
    try:
        # Create a fresh instance
        from services.telegram_monitor_user import TelegramUserMonitor
        fresh_monitor = TelegramUserMonitor()
        
        result4 = await fresh_monitor.get_recent_telegram_news(hours=24)
        print(f"✅ Fresh instance: {len(result4)} articles")
        
        # Clean up
        await fresh_monitor.disconnect()
        
    except Exception as e:
        print(f"❌ Fresh instance error: {e}")

if __name__ == "__main__":
    asyncio.run(test_telegram_connection())
