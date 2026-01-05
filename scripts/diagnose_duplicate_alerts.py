#!/usr/bin/env python3
"""
Diagnostic script to check for duplicate alert issues
Checks deduplication state, Firebase connection, and recent alerts
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage
from services.persistent_alert_deduplication import get_persistent_deduplication
from datetime import datetime, timedelta
import json

def diagnose_duplicate_alerts():
    """Diagnose potential duplicate alert issues"""
    print("=" * 60)
    print("DUPLICATE ALERT DIAGNOSTIC")
    print("=" * 60)
    print()
    
    firebase = FirebaseRealtimeStorage()
    dedup = get_persistent_deduplication()
    
    # 1. Check Firebase connection
    print("1. Checking Firebase connection...")
    try:
        test_path = "alert_deduplication/alerts"
        test_result = firebase._make_request('GET', test_path)
        if test_result is None:
            print("   ❌ Firebase connection FAILED - this will cause duplicates!")
            print("   ⚠️  Check Firebase credentials and network connectivity")
        else:
            print("   ✅ Firebase connection OK")
    except Exception as e:
        print(f"   ❌ Firebase connection error: {e}")
    
    print()
    
    # 2. Check deduplication records
    print("2. Checking deduplication records...")
    try:
        alerts_path = "alert_deduplication/alerts"
        all_alerts = firebase._make_request('GET', alerts_path)
        
        if not all_alerts:
            print("   ⚠️  No deduplication records found")
        else:
            total_alerts = len(all_alerts) if isinstance(all_alerts, dict) else 0
            print(f"   Total alert records: {total_alerts}")
            
            # Check for reserved alerts (these should be sent, not reserved)
            now = datetime.now()
            reserved_count = 0
            sent_count = 0
            expired_count = 0
            
            for alert_key, alert_data in (all_alerts.items() if isinstance(all_alerts, dict) else []):
                if isinstance(alert_data, dict):
                    status = alert_data.get('status', 'sent')
                    if status == 'reserved':
                        reserved_count += 1
                    elif status == 'sent':
                        sent_count += 1
                    
                    # Check if expired
                    expires_at_str = alert_data.get('expires_at')
                    if expires_at_str:
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str)
                            if now >= expires_at:
                                expired_count += 1
                        except:
                            pass
            
            print(f"   Sent alerts: {sent_count}")
            print(f"   Reserved alerts: {reserved_count}")
            if reserved_count > 0:
                print(f"   ⚠️  {reserved_count} reserved alerts found - these may indicate failed sends")
            print(f"   Expired alerts: {expired_count}")
            
    except Exception as e:
        print(f"   ❌ Error checking deduplication records: {e}")
    
    print()
    
    # 3. Check global content hashes
    print("3. Checking global content hashes...")
    try:
        hashes_path = "alert_deduplication/content_hashes"
        all_hashes = firebase._make_request('GET', hashes_path)
        
        if not all_hashes:
            print("   ⚠️  No global content hashes found")
        else:
            total_hashes = len(all_hashes) if isinstance(all_hashes, dict) else 0
            print(f"   Total content hashes: {total_hashes}")
            
            # Check for expired hashes
            now = datetime.now()
            expired_hashes = 0
            
            for hash_key, hash_data in (all_hashes.items() if isinstance(all_hashes, dict) else []):
                if isinstance(hash_data, dict):
                    expires_at_str = hash_data.get('expires_at')
                    if expires_at_str:
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str)
                            if now >= expires_at:
                                expired_hashes += 1
                        except:
                            pass
            
            print(f"   Expired hashes: {expired_hashes}")
            
    except Exception as e:
        print(f"   ❌ Error checking content hashes: {e}")
    
    print()
    
    # 4. Check recent alert history
    print("4. Checking recent alert history...")
    try:
        # Get alert history for last 24 hours
        history_path = "alert_history"
        all_history = firebase._make_request('GET', history_path)
        
        if not all_history:
            print("   ⚠️  No alert history found")
        else:
            # Count alerts by title (to find duplicates)
            title_counts = {}
            now = datetime.now()
            recent_alerts = []
            
            for user_id, user_history in (all_history.items() if isinstance(all_history, dict) else []):
                if isinstance(user_history, dict):
                    alerts = user_history.get('alerts', [])
                    if isinstance(alerts, list):
                        for alert in alerts:
                            if isinstance(alert, dict):
                                title = alert.get('title', '')
                                timestamp_str = alert.get('timestamp', '')
                                
                                # Check if recent (last 24 hours)
                                if timestamp_str:
                                    try:
                                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                        if (now - timestamp).total_seconds() < 86400:  # 24 hours
                                            recent_alerts.append({
                                                'title': title,
                                                'timestamp': timestamp_str,
                                                'user_id': user_id
                                            })
                                            title_counts[title] = title_counts.get(title, 0) + 1
                                    except:
                                        pass
            
            print(f"   Recent alerts (last 24h): {len(recent_alerts)}")
            
            # Find potential duplicates
            duplicates = {title: count for title, count in title_counts.items() if count > 1}
            if duplicates:
                print(f"   ⚠️  Potential duplicate titles found:")
                for title, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"      - '{title[:50]}...' ({count} times)")
            else:
                print("   ✅ No obvious duplicates in recent history")
            
    except Exception as e:
        print(f"   ❌ Error checking alert history: {e}")
    
    print()
    
    # 5. Check deduplication stats
    print("5. Deduplication statistics...")
    try:
        stats = dedup.get_stats()
        print(f"   Operations: {stats.get('operations_count', 0)}")
        print(f"   Duplicates prevented: {stats.get('duplicates_prevented', 0)}")
        print(f"   TTL: {stats.get('alert_ttl_hours', 0)} hours")
        print(f"   Total records: {stats.get('total_records', 0)}")
    except Exception as e:
        print(f"   ❌ Error getting stats: {e}")
    
    print()
    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print()
    print("If duplicates are occurring:")
    print("1. Check Firebase connection - ensure credentials are valid")
    print("2. Run cleanup: python3 scripts/cleanup_production_data.py")
    print("3. Check for reserved alerts that never got marked as sent")
    print("4. Verify deduplication is being called before sending alerts")
    print("5. Check logs for 'Firebase connection failed' errors")
    print()

if __name__ == "__main__":
    diagnose_duplicate_alerts()

