#!/usr/bin/env python3
"""
Migration Script: Normalize Settings to Canonical Format
Migrates all user alert settings to the canonical format defined in CANONICAL_SETTINGS_FORMAT.md

This script:
1. Reads all user settings from Firebase
2. Normalizes them to canonical format
3. Validates the normalized structure
4. Saves back to Firebase
5. Reports migration statistics
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.firebase_realtime_storage import FirebaseRealtimeStorage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Canonical default settings
CANONICAL_DEFAULTS = {
    "channels": {
        "telegram": {
            "enabled": False,
            "chatId": "",
            "username": ""
        },
        "email": {
            "enabled": False,
            "address": ""
        }
    },
    "preferences": {
        "impactLevels": {
            "high": True,
            "medium": True,
            "low": False
        },
        "alertTypes": {
            "liveNews": True,
            "preNews": True,
            "postNews": True,
            "technicalAnalysis": False
        },
        "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
        "quietHours": {
            "enabled": False,
            "start": "22:00",
            "end": "06:00",
            "timezone": "UTC"
        }
    }
}

def normalize_settings(old_settings: dict) -> dict:
    """
    Normalize old settings structure to canonical format
    """
    if not old_settings:
        return CANONICAL_DEFAULTS.copy()
    
    # Start with canonical defaults
    normalized = CANONICAL_DEFAULTS.copy()
    
    # Migrate channels.telegram
    if old_settings.get('telegram_enabled'):
        normalized['channels']['telegram']['enabled'] = True
    elif old_settings.get('telegram') is True:
        normalized['channels']['telegram']['enabled'] = True
    elif old_settings.get('channels', {}).get('telegram', {}).get('enabled'):
        normalized['channels']['telegram']['enabled'] = True
        # Preserve chatId and username if they exist
        old_tg = old_settings.get('channels', {}).get('telegram', {})
        if old_tg.get('chatId'):
            # Note: chatId should be stored separately, but we preserve it here for migration
            normalized['channels']['telegram']['chatId'] = old_tg['chatId']
        if old_tg.get('username'):
            normalized['channels']['telegram']['username'] = old_tg['username']
    
    # Migrate channels.email
    if old_settings.get('channels', {}).get('email'):
        normalized['channels']['email'] = old_settings['channels']['email'].copy()
    
    # Migrate preferences.alertTypes
    old_alert_types = (
        old_settings.get('preferences', {}).get('alertTypes') or
        old_settings.get('alert_types') or
        {}
    )
    
    if isinstance(old_alert_types, dict):
        for key in ['liveNews', 'preNews', 'postNews', 'technicalAnalysis']:
            # Check both camelCase and snake_case
            value = (
                old_alert_types.get(key) or
                old_alert_types.get(key.replace('News', '_news').replace('Analysis', '_analysis')) or
                CANONICAL_DEFAULTS['preferences']['alertTypes'][key]
            )
            normalized['preferences']['alertTypes'][key] = bool(value)
    elif isinstance(old_alert_types, list):
        # Convert list to dict
        for key in ['liveNews', 'preNews', 'postNews', 'technicalAnalysis']:
            normalized['preferences']['alertTypes'][key] = key in old_alert_types or 'news' in old_alert_types
    
    # Migrate preferences.impactLevels
    old_impact_levels = (
        old_settings.get('preferences', {}).get('impactLevels') or
        old_settings.get('impact_levels') or
        {}
    )
    
    if isinstance(old_impact_levels, dict):
        for key in ['high', 'medium', 'low']:
            value = old_impact_levels.get(key)
            if value is not None:
                normalized['preferences']['impactLevels'][key] = bool(value)
    
    # Migrate preferences.currencyPairs
    old_currency_pairs = (
        old_settings.get('preferences', {}).get('currencyPairs') or
        old_settings.get('currency_pairs') or
        []
    )
    
    if isinstance(old_currency_pairs, list) and old_currency_pairs:
        normalized['preferences']['currencyPairs'] = old_currency_pairs.copy()
    
    # Migrate preferences.quietHours
    old_quiet_hours = (
        old_settings.get('preferences', {}).get('quietHours') or
        old_settings.get('quiet_hours') or
        {}
    )
    
    if isinstance(old_quiet_hours, dict):
        if old_quiet_hours.get('enabled') is not None:
            normalized['preferences']['quietHours']['enabled'] = bool(old_quiet_hours['enabled'])
        if old_quiet_hours.get('start'):
            normalized['preferences']['quietHours']['start'] = str(old_quiet_hours['start'])
        if old_quiet_hours.get('end'):
            normalized['preferences']['quietHours']['end'] = str(old_quiet_hours['end'])
        if old_quiet_hours.get('timezone'):
            normalized['preferences']['quietHours']['timezone'] = str(old_quiet_hours['timezone'])
    
    return normalized

def validate_settings(settings: dict) -> tuple[bool, list[str]]:
    """
    Validate settings structure against canonical format
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate channels structure
    if 'channels' not in settings:
        errors.append("Missing 'channels' key")
    else:
        channels = settings['channels']
        
        # Validate telegram
        if 'telegram' not in channels:
            errors.append("Missing 'channels.telegram' key")
        else:
            tg = channels['telegram']
            if not isinstance(tg.get('enabled'), bool):
                errors.append("'channels.telegram.enabled' must be boolean")
        
        # Validate email
        if 'email' not in channels:
            errors.append("Missing 'channels.email' key")
        else:
            email = channels['email']
            if not isinstance(email.get('enabled'), bool):
                errors.append("'channels.email.enabled' must be boolean")
    
    # Validate preferences structure
    if 'preferences' not in settings:
        errors.append("Missing 'preferences' key")
    else:
        prefs = settings['preferences']
        
        # Validate alertTypes
        if 'alertTypes' not in prefs:
            errors.append("Missing 'preferences.alertTypes' key")
        else:
            alert_types = prefs['alertTypes']
            if not isinstance(alert_types, dict):
                errors.append("'preferences.alertTypes' must be object")
            else:
                for key in ['liveNews', 'preNews', 'postNews', 'technicalAnalysis']:
                    if key not in alert_types:
                        errors.append(f"Missing 'preferences.alertTypes.{key}'")
                    elif not isinstance(alert_types[key], bool):
                        errors.append(f"'preferences.alertTypes.{key}' must be boolean")
        
        # Validate impactLevels
        if 'impactLevels' not in prefs:
            errors.append("Missing 'preferences.impactLevels' key")
        else:
            impact_levels = prefs['impactLevels']
            if not isinstance(impact_levels, dict):
                errors.append("'preferences.impactLevels' must be object")
            else:
                for key in ['high', 'medium', 'low']:
                    if key not in impact_levels:
                        errors.append(f"Missing 'preferences.impactLevels.{key}'")
                    elif not isinstance(impact_levels[key], bool):
                        errors.append(f"'preferences.impactLevels.{key}' must be boolean")
        
        # Validate currencyPairs
        if 'currencyPairs' not in prefs:
            errors.append("Missing 'preferences.currencyPairs' key")
        elif not isinstance(prefs['currencyPairs'], list):
            errors.append("'preferences.currencyPairs' must be array")
        
        # Validate quietHours
        if 'quietHours' not in prefs:
            errors.append("Missing 'preferences.quietHours' key")
        else:
            quiet_hours = prefs['quietHours']
            if not isinstance(quiet_hours, dict):
                errors.append("'preferences.quietHours' must be object")
            else:
                if 'enabled' not in quiet_hours or not isinstance(quiet_hours['enabled'], bool):
                    errors.append("'preferences.quietHours.enabled' must be boolean")
                if 'start' not in quiet_hours or not isinstance(quiet_hours['start'], str):
                    errors.append("'preferences.quietHours.start' must be string")
                if 'end' not in quiet_hours or not isinstance(quiet_hours['end'], str):
                    errors.append("'preferences.quietHours.end' must be string")
    
    return len(errors) == 0, errors

def migrate_settings():
    """Migrate all user settings to canonical format"""
    firebase = FirebaseRealtimeStorage()
    
    print("=" * 60)
    print("SETTINGS MIGRATION: Normalize to Canonical Format")
    print("=" * 60)
    print()
    
    # Statistics
    stats = {
        'users_processed': 0,
        'settings_migrated': 0,
        'settings_already_canonical': 0,
        'settings_errors': 0,
        'validation_errors': 0
    }
    
    # Step 1: Get all users
    print("Step 1: Getting all users...")
    users_path = "alerts/users"
    all_users = firebase._make_request('GET', users_path)
    
    if not all_users or not isinstance(all_users, dict):
        print("❌ No users found")
        return stats
    
    print(f"✅ Found {len(all_users)} users")
    print()
    
    # Step 2: Process each user
    print("Step 2: Processing user settings...")
    for safe_user_id, user_data in all_users.items():
        if not isinstance(user_data, dict):
            continue
        
        stats['users_processed'] += 1
        
        # Get current settings
        settings_path = f"alerts/users/{safe_user_id}/settings"
        old_settings = firebase._make_request('GET', settings_path)
        
        if not old_settings:
            # No settings found, create default canonical settings
            print(f"  User {safe_user_id}: No settings found, creating defaults...")
            normalized = CANONICAL_DEFAULTS.copy()
            result = firebase._make_request('PUT', settings_path, normalized)
            
            if result is not None:
                stats['settings_migrated'] += 1
                print(f"    ✅ Created default canonical settings")
            else:
                stats['settings_errors'] += 1
                print(f"    ❌ Failed to create default settings")
            continue
        
        # Normalize settings
        normalized = normalize_settings(old_settings)
        
        # Validate normalized settings
        is_valid, errors = validate_settings(normalized)
        
        if not is_valid:
            stats['validation_errors'] += 1
            print(f"  User {safe_user_id}: Validation errors:")
            for error in errors:
                print(f"    - {error}")
            continue
        
        # Check if settings changed (need to migrate)
        import json
        old_json = json.dumps(old_settings, sort_keys=True)
        new_json = json.dumps(normalized, sort_keys=True)
        
        if old_json == new_json:
            # Already in canonical format
            stats['settings_already_canonical'] += 1
            continue
        
        # Save normalized settings
        print(f"  User {safe_user_id}: Migrating settings...")
        result = firebase._make_request('PUT', settings_path, normalized)
        
        if result is not None:
            stats['settings_migrated'] += 1
            print(f"    ✅ Migrated successfully")
        else:
            stats['settings_errors'] += 1
            print(f"    ❌ Failed to migrate")
    
    print()
    print("=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print(f"Users processed: {stats['users_processed']}")
    print(f"Settings already canonical: {stats['settings_already_canonical']}")
    print(f"Settings migrated: {stats['settings_migrated']}")
    print(f"Settings errors: {stats['settings_errors']}")
    print(f"Validation errors: {stats['validation_errors']}")
    print()
    
    return stats

if __name__ == "__main__":
    try:
        migrate_settings()
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)

