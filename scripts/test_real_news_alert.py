#!/usr/bin/env python3
"""
Test Alert System with Real News Item
Sends a test alert using a real news item from the system
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def get_real_news_item():
    """Get a real high-impact news item from the system"""
    print_section("1. FETCHING REAL NEWS ITEM")
    try:
        # Try to get news from local backend
        try:
            response = requests.get('http://localhost:5001/api/news', timeout=10)
            if response.status_code == 200:
                data = response.json()
                news_items = data.get('news', [])
                
                if not news_items:
                    print("❌ No news items available")
                    return None
                
                # Find high-impact news
                from services.news_alert_trigger import news_alert_trigger
                
                high_impact = []
                for item in news_items:
                    if news_alert_trigger.is_forex_high_impact(item):
                        high_impact.append(item)
                
                if high_impact:
                    selected = high_impact[0]
                    print(f"✅ Found high-impact news item:")
                    print(f"   Title: {selected.get('title', 'No title')[:60]}...")
                    print(f"   Source: {selected.get('source', 'Unknown')}")
                    print(f"   Impact: {selected.get('impact', 'Unknown')}")
                    return selected
                else:
                    print("⚠️  No high-impact news found in current feed")
                    # Use first news item as fallback
                    if news_items:
                        selected = news_items[0]
                        print(f"   Using first news item as test:")
                        print(f"   Title: {selected.get('title', 'No title')[:60]}...")
                        return selected
                    return None
            else:
                print(f"❌ Failed to get news: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            print("⚠️  Backend not accessible at localhost:5001")
            print("   Creating synthetic test news item...")
            
            # Create synthetic news item for testing
            return {
                'id': f'test_real_{datetime.now().timestamp()}',
                'title': 'Test Real News Alert - Verification',
                'source': 'Test Source',
                'impact': 'high',
                'summary': 'This is a test alert using a real news item structure',
                'url': 'https://example.com',
                'published_at': datetime.now().isoformat(),
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"❌ Error fetching news: {e}")
        import traceback
        traceback.print_exc()
        return None

def trigger_alert(news_item):
    """Trigger alert using the /api/alerts/trigger endpoint"""
    print_section("2. TRIGGERING ALERT")
    try:
        alert_data = {
            'type': 'news',
            'data': news_item
        }
        
        # Try local backend first
        api_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        endpoint = f"{api_url}/api/alerts/trigger"
        
        print(f"Sending alert to: {endpoint}")
        print(f"News item: {news_item.get('title', 'No title')[:50]}...")
        
        response = requests.post(
            endpoint,
            json=alert_data,
            timeout=30
        )
        
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            alerts_sent = result.get('alerts_sent', 0)
            total_users = result.get('total_users', 0)
            message = result.get('message', '')
            
            print(f"✅ Alert trigger successful")
            print(f"   Alerts sent: {alerts_sent}")
            print(f"   Total users processed: {total_users}")
            if message:
                print(f"   Message: {message}")
            
            if alerts_sent > 0:
                print("\n✅ SUCCESS: Alert was sent to users!")
                return True
            else:
                print("\n⚠️  WARNING: No alerts were sent")
                print("   Possible reasons:")
                print("   - No users with Telegram enabled")
                print("   - Users have alerts disabled")
                print("   - Deduplication blocked (already sent)")
                print("   - Subscription validation failed")
                return False
        else:
            print(f"❌ Alert trigger failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {api_url}")
        print("   Make sure backend is running")
        return False
    except Exception as e:
        print(f"❌ Error triggering alert: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_alert_sent():
    """Verify that alert was actually sent"""
    print_section("3. VERIFYING ALERT DELIVERY")
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase = FirebaseRealtimeStorage()
        
        # Get all users
        users = firebase.get_all_users_with_alerts()
        
        if not users:
            print("⚠️  No users found - cannot verify delivery")
            return False
        
        print(f"Found {len(users)} users")
        print("\nTo verify delivery:")
        print("1. Check Telegram for received alerts")
        print("2. Check Firebase alert_history for logged alerts")
        print("3. Check backend logs for 'Successfully sent alert' messages")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Error verifying: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("  REAL NEWS ALERT TEST")
    print("=" * 70)
    print(f"Time: {datetime.now().isoformat()}")
    
    # Step 1: Get real news item
    news_item = get_real_news_item()
    if not news_item:
        print("\n❌ Cannot proceed without news item")
        return
    
    # Step 2: Trigger alert
    success = trigger_alert(news_item)
    
    # Step 3: Verify
    if success:
        verify_alert_sent()
    
    # Summary
    print_section("TEST SUMMARY")
    if success:
        print("✅ Test completed successfully!")
        print("   → Check Telegram to confirm alert was received")
        print("   → Monitor backend logs for any errors")
    else:
        print("⚠️  Test completed but no alerts were sent")
        print("   → Check user settings and Telegram configuration")
        print("   → Run diagnostic script to identify issues")

if __name__ == "__main__":
    main()

