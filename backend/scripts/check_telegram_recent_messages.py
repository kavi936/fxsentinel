#!/usr/bin/env python3
"""
Check what recent messages are actually in Telegram channels
"""

import sys
import os
from datetime import datetime, timedelta
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def check_telegram_messages():
    """Check recent messages in Telegram channels"""
    print("=" * 80)
    print("CHECKING TELEGRAM CHANNEL MESSAGES")
    print("=" * 80)
    print(f"Check time: {datetime.now().isoformat()}")
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Missing Telegram API credentials")
        return
    
    # Use production session
    session_name = 'telegram_session_production' if os.path.exists('telegram_session_production.session') else 'fxsentinel_user_session'
    
    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        await client.start(phone=phone)
        
        if not await client.is_user_authorized():
            print("❌ Not authorized")
            return
        
        print("✅ Connected to Telegram")
        
        # Check channels
        target_channels = ['WatcherGuru', '@WatcherGuru']
        now = datetime.now()
        cutoff_1h = now - timedelta(hours=1)
        cutoff_6h = now - timedelta(hours=6)
        cutoff_24h = now - timedelta(hours=24)
        
        for channel in target_channels:
            print(f"\n{'='*80}")
            print(f"Checking channel: {channel}")
            print(f"{'='*80}")
            
            try:
                # Try different formats
                channel_variants = [channel, channel.replace('@', ''), f"@{channel.replace('@', '')}"]
                
                channel_entity = None
                for variant in channel_variants:
                    try:
                        channel_entity = await client.get_entity(variant)
                        print(f"✅ Found channel: {variant}")
                        break
                    except Exception as e:
                        continue
                
                if not channel_entity:
                    print(f"❌ Could not find channel: {channel}")
                    continue
                
                # Get recent messages
                messages = []
                async for message in client.iter_messages(channel_entity, limit=20):
                    if hasattr(message, 'text') and message.text:
                        msg_date = message.date
                        age = now - msg_date.replace(tzinfo=None) if msg_date.tzinfo else now - msg_date
                        
                        messages.append({
                            'date': msg_date,
                            'text': message.text[:100],
                            'age': age
                        })
                
                print(f"   Total messages fetched: {len(messages)}")
                
                # Categorize by age
                recent_1h = [m for m in messages if m['age'] <= timedelta(hours=1)]
                recent_6h = [m for m in messages if timedelta(hours=1) < m['age'] <= timedelta(hours=6)]
                recent_24h = [m for m in messages if timedelta(hours=6) < m['age'] <= timedelta(hours=24)]
                older = [m for m in messages if m['age'] > timedelta(hours=24)]
                
                print(f"\n   📊 BREAKDOWN BY AGE:")
                print(f"      Last hour: {len(recent_1h)} messages")
                print(f"      Last 6 hours: {len(recent_6h)} messages")
                print(f"      Last 24 hours: {len(recent_24h)} messages")
                print(f"      Older than 24h: {len(older)} messages")
                
                # Show recent messages
                if recent_1h:
                    print(f"\n   🆕 MESSAGES FROM LAST HOUR:")
                    for i, msg in enumerate(recent_1h[:5], 1):
                        print(f"      {i}. {msg['text']}...")
                        print(f"         Age: {msg['age']}")
                
                if recent_6h:
                    print(f"\n   📰 MESSAGES FROM LAST 6 HOURS:")
                    for i, msg in enumerate(recent_6h[:5], 1):
                        print(f"      {i}. {msg['text']}...")
                        print(f"         Age: {msg['age']}")
                
                # Show oldest message
                if messages:
                    oldest = max(messages, key=lambda x: x['age'])
                    print(f"\n   ⏰ OLDEST MESSAGE:")
                    print(f"      {oldest['text']}...")
                    print(f"      Age: {oldest['age']}")
                
            except Exception as e:
                print(f"❌ Error checking channel {channel}: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_telegram_messages())

