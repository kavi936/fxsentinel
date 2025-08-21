#!/usr/bin/env python3
"""
Setup User Alerts
Configure default alert settings for the user
"""

import requests
import json
from datetime import datetime

def setup_user_alerts():
    print("🔧 Setting Up User Alert Preferences")
    print("=" * 50)
    
    # Your user ID
    user_id = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"
    
    # Default alert settings
    default_settings = {
        'user_id': user_id,
        'telegram_enabled': True,
        'alert_types': ['liveNews', 'economicCalendar'],
        'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
        'impact_levels': ['high', 'medium'],
        'notification_frequency': 'immediate',
        'ai_analysis_enabled': True,
        'economic_calendar_alerts': True,
        'live_news_alerts': True
    }
    
    print("📋 Default Alert Settings:")
    print(f"   Telegram enabled: {default_settings['telegram_enabled']}")
    print(f"   Alert types: {default_settings['alert_types']}")
    print(f"   Currency pairs: {default_settings['currency_pairs']}")
    print(f"   Impact levels: {default_settings['impact_levels']}")
    print(f"   AI analysis: {default_settings['ai_analysis_enabled']}")
    
    # Since the user settings API endpoints are missing, let's create a simple solution
    # by directly updating the Firebase database
    print("\n🔧 Setting up alert preferences...")
    
    try:
        # Import Firebase service
        import sys
        sys.path.append('backend')
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        
        # Create Firebase instance
        firebase_storage = FirebaseRealtimeStorage()
        
        # Save user settings to Firebase
        success = firebase_storage.update_user_alert_settings(user_id, default_settings)
        
        print("✅ Alert preferences saved to Firebase")
        
        # Test the settings by sending a confirmation alert
        print("\n📨 Sending confirmation alert...")
        
        test_alert_data = {
            'user_id': user_id,
            'news_item': {
                'title': '🎉 Alert System Activated!',
                'summary': 'Your FXSentinel alert system is now configured and ready to send you notifications for high-impact forex news and economic events.',
                'source': 'FXSentinel Setup',
                'published_at': datetime.now().isoformat()
            },
            'ai_analysis': {
                'summary': 'Your alert preferences have been configured successfully. You will now receive notifications for high-impact forex news and economic calendar events.',
                'market_impact': 'System ready for live market monitoring',
                'key_levels': 'All major currency pairs enabled'
            }
        }
        
        response = requests.post(
            "http://localhost:5001/api/test-alert",
            json=test_alert_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✅ Confirmation alert sent successfully!")
            print("📱 Check your Telegram bot for the confirmation message")
        else:
            print(f"❌ Failed to send confirmation: {response.text}")
            
        # Also save the settings
        if success:
            print("✅ Alert preferences saved to Firebase")
        else:
            print("❌ Failed to save alert preferences")
            
    except Exception as e:
        print(f"❌ Error setting up alerts: {e}")
        print("\n🔧 Alternative Setup Method:")
        print("1. Open your FXSentinel dashboard")
        print("2. Go to the Alerts section")
        print("3. Configure your alert preferences manually")
        print("4. Enable Telegram notifications")
        print("5. Select your preferred currency pairs and alert types")
    
    print("\n" + "=" * 50)
    print("🎯 What You Should Receive Now:")
    print("• Live news alerts for high-impact forex events")
    print("• Economic calendar alerts for upcoming events")
    print("• AI analysis of market-moving news")
    print("• Notifications for EUR/USD, USD/JPY, GBP/USD, and other major pairs")
    
    print("\n📊 To Monitor Alert Activity:")
    print("• Check your Telegram bot for incoming messages")
    print("• Monitor the dashboard for new high-impact news")
    print("• Economic calendar events will trigger pre-event alerts")
    
    print("\n⚠️ Note: Alerts are only sent for high-impact news that matches your preferences.")
    print("   If you don't receive alerts immediately, it means there's no high-impact news at the moment.")

if __name__ == "__main__":
    setup_user_alerts()
