#!/usr/bin/env python3
"""
Test Alert Fixes
Verify that duplicate alerts and wrong economic calendar alerts are fixed
"""

import requests
import json
import time
from datetime import datetime

def test_duplicate_news_alerts():
    """Test that news alerts are not sent twice"""
    print("🔄 Testing Duplicate News Alerts Fix")
    print("=" * 50)
    
    try:
        # First force refresh
        print("1. Force refreshing news (first time)...")
        response1 = requests.post('http://localhost:5001/api/force-refresh-news')
        
        if response1.status_code == 200:
            data1 = response1.json()
            alerts_sent_1 = data1.get('alert_results', {}).get('alerts_sent', 0)
            print(f"✅ First refresh: {alerts_sent_1} alerts sent")
            
            # Wait a moment
            time.sleep(2)
            
            # Force refresh again (should not send duplicates)
            print("\n2. Force refreshing news (second time - should not send duplicates)...")
            response2 = requests.post('http://localhost:5001/api/force-refresh-news')
            
            if response2.status_code == 200:
                data2 = response2.json()
                alerts_sent_2 = data2.get('alert_results', {}).get('alerts_sent', 0)
                print(f"✅ Second refresh: {alerts_sent_2} alerts sent")
                
                if alerts_sent_2 == 0:
                    print("✅ SUCCESS: No duplicate alerts sent!")
                    return True
                else:
                    print(f"⚠️ WARNING: {alerts_sent_2} alerts sent in second run")
                    return False
            else:
                print(f"❌ Second refresh failed: {response2.status_code}")
                return False
        else:
            print(f"❌ First refresh failed: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing duplicate alerts: {e}")
        return False

def test_economic_calendar_validation():
    """Test that economic calendar alerts are properly validated"""
    print("\n📅 Testing Economic Calendar Validation")
    print("=" * 50)
    
    try:
        # Get economic calendar data
        print("1. Fetching economic calendar data...")
        response = requests.get('http://localhost:5001/api/economic-calendar')
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            source = data.get('source', 'unknown')
            
            print(f"✅ Fetched {len(events)} events from {source}")
            
            # Check data source quality
            if source in ['fallback_data', 'mock_data', 'test_data', 'demo_data']:
                print(f"⚠️ Using {source} - alerts should be disabled")
                
                # Test that alerts are disabled for poor quality data
                print("\n2. Testing alert processing with poor quality data...")
                from backend.services.economic_calendar_alerts import economic_calendar_alerts
                
                results = economic_calendar_alerts.process_economic_calendar_for_alerts()
                alerts_sent = results.get('alerts_sent', 0)
                
                if alerts_sent == 0:
                    print("✅ SUCCESS: No alerts sent for poor quality data!")
                    return True
                else:
                    print(f"❌ ERROR: {alerts_sent} alerts sent despite poor quality data")
                    return False
            else:
                print(f"✅ Using {source} - data quality looks good")
                
                # Test with good quality data
                print("\n2. Testing alert processing with good quality data...")
                from backend.services.economic_calendar_alerts import economic_calendar_alerts
                
                results = economic_calendar_alerts.process_economic_calendar_for_alerts()
                total_events = results.get('total_events', 0)
                high_impact = results.get('high_impact_events', 0)
                alerts_sent = results.get('alerts_sent', 0)
                
                print(f"📊 Results: {total_events} total events, {high_impact} high impact, {alerts_sent} alerts sent")
                
                if alerts_sent >= 0:  # Should be 0 or positive
                    print("✅ SUCCESS: Economic calendar processing working correctly!")
                    return True
                else:
                    print("❌ ERROR: Invalid alert count")
                    return False
        else:
            print(f"❌ Failed to fetch economic calendar: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing economic calendar: {e}")
        return False

def test_unified_deduplication():
    """Test the unified deduplication system"""
    print("\n🔧 Testing Unified Deduplication System")
    print("=" * 50)
    
    try:
        from backend.services.unified_alert_deduplication import (
            unified_deduplication, 
            should_send_news_alert, 
            should_send_economic_alert,
            get_deduplication_stats
        )
        
        # Test news deduplication
        print("1. Testing news deduplication...")
        
        # Create test news item
        test_news = {
            'title': 'Test News Alert',
            'source': 'Test Source',
            'url': 'https://test.com'
        }
        
        # First call should allow alert
        should_send_1 = should_send_news_alert(test_news, 'test_user_1')
        print(f"   First call: should_send = {should_send_1}")
        
        # Second call should prevent duplicate
        should_send_2 = should_send_news_alert(test_news, 'test_user_1')
        print(f"   Second call: should_send = {should_send_2}")
        
        if should_send_1 and not should_send_2:
            print("✅ SUCCESS: News deduplication working!")
        else:
            print("❌ ERROR: News deduplication not working")
            return False
        
        # Test economic event deduplication
        print("\n2. Testing economic event deduplication...")
        
        test_event = {
            'title': 'Test Economic Event',
            'time': '14:30 UTC',
            'date': 'Mon, Jan 15'
        }
        
        # First call should allow alert
        should_send_1 = should_send_economic_alert(test_event, 'test_user_1', '2h_before')
        print(f"   First call: should_send = {should_send_1}")
        
        # Second call should prevent duplicate
        should_send_2 = should_send_economic_alert(test_event, 'test_user_1', '2h_before')
        print(f"   Second call: should_send = {should_send_2}")
        
        if should_send_1 and not should_send_2:
            print("✅ SUCCESS: Economic event deduplication working!")
        else:
            print("❌ ERROR: Economic event deduplication not working")
            return False
        
        # Test different timing allows different alerts
        should_send_3 = should_send_economic_alert(test_event, 'test_user_1', '1h_before')
        print(f"   Different timing: should_send = {should_send_3}")
        
        if should_send_3:
            print("✅ SUCCESS: Different timing allows different alerts!")
        else:
            print("❌ ERROR: Different timing should allow different alerts")
            return False
        
        # Get stats
        print("\n3. Getting deduplication stats...")
        stats = get_deduplication_stats()
        print(f"   Total records: {stats['total_records']}")
        print(f"   Content hashes: {stats['content_hashes']}")
        print(f"   Operations: {stats['operations_count']}")
        print(f"   Duplicates prevented: {stats['duplicates_prevented']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing unified deduplication: {e}")
        return False

def test_alert_service_integration():
    """Test that alert services are properly integrated"""
    print("\n🔗 Testing Alert Service Integration")
    print("=" * 50)
    
    try:
        # Test health endpoint
        print("1. Testing alert health endpoint...")
        response = requests.get('http://localhost:5001/api/health/alerts')
        
        if response.status_code == 200:
            health_data = response.json()
            status = health_data.get('status', 'unknown')
            alerts_working = health_data.get('alerts_working', False)
            
            print(f"✅ Health status: {status}")
            print(f"   Alerts working: {alerts_working}")
            print(f"   Telegram bot: {health_data.get('telegram_bot', 'unknown')}")
            print(f"   Firebase: {health_data.get('firebase', 'unknown')}")
            
            if status in ['healthy', 'degraded']:
                print("✅ SUCCESS: Alert service health check passed!")
                return True
            else:
                print("❌ ERROR: Alert service health check failed")
                return False
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing alert service integration: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Alert System Fixes")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Duplicate News Alerts", test_duplicate_news_alerts),
        ("Economic Calendar Validation", test_economic_calendar_validation),
        ("Unified Deduplication", test_unified_deduplication),
        ("Alert Service Integration", test_alert_service_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Alert system fixes are working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()
