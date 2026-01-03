#!/usr/bin/env python3
"""
Settings Validator
Validates user alert settings against canonical format
"""

import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

# Canonical default settings structure
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

def validate_settings(settings: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate settings structure against canonical format
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(settings, dict):
        return False, ["Settings must be an object"]
    
    # Validate channels structure
    if 'channels' not in settings:
        errors.append("Missing 'channels' key")
    else:
        channels = settings['channels']
        if not isinstance(channels, dict):
            errors.append("'channels' must be an object")
        else:
            # Validate telegram
            if 'telegram' not in channels:
                errors.append("Missing 'channels.telegram' key")
            else:
                tg = channels['telegram']
                if not isinstance(tg, dict):
                    errors.append("'channels.telegram' must be an object")
                else:
                    if 'enabled' not in tg or not isinstance(tg['enabled'], bool):
                        errors.append("'channels.telegram.enabled' must be boolean")
                    if 'chatId' not in tg or not isinstance(tg['chatId'], str):
                        errors.append("'channels.telegram.chatId' must be string")
                    if 'username' not in tg or not isinstance(tg['username'], str):
                        errors.append("'channels.telegram.username' must be string")
            
            # Validate email
            if 'email' not in channels:
                errors.append("Missing 'channels.email' key")
            else:
                email = channels['email']
                if not isinstance(email, dict):
                    errors.append("'channels.email' must be an object")
                else:
                    if 'enabled' not in email or not isinstance(email['enabled'], bool):
                        errors.append("'channels.email.enabled' must be boolean")
                    if 'address' not in email or not isinstance(email['address'], str):
                        errors.append("'channels.email.address' must be string")
    
    # Validate preferences structure
    if 'preferences' not in settings:
        errors.append("Missing 'preferences' key")
    else:
        prefs = settings['preferences']
        if not isinstance(prefs, dict):
            errors.append("'preferences' must be an object")
        else:
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
            else:
                # Validate each currency pair format
                for pair in prefs['currencyPairs']:
                    if not isinstance(pair, str):
                        errors.append(f"Currency pair must be string: {pair}")
                    elif '/' not in pair:
                        errors.append(f"Invalid currency pair format (missing '/'): {pair}")
            
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
                    elif not _validate_time_format(quiet_hours['start']):
                        errors.append(f"Invalid time format for 'preferences.quietHours.start': {quiet_hours['start']} (expected HH:MM)")
                    if 'end' not in quiet_hours or not isinstance(quiet_hours['end'], str):
                        errors.append("'preferences.quietHours.end' must be string")
                    elif not _validate_time_format(quiet_hours['end']):
                        errors.append(f"Invalid time format for 'preferences.quietHours.end': {quiet_hours['end']} (expected HH:MM)")
                    if 'timezone' not in quiet_hours or not isinstance(quiet_hours['timezone'], str):
                        errors.append("'preferences.quietHours.timezone' must be string")
    
    return len(errors) == 0, errors

def _validate_time_format(time_str: str) -> bool:
    """Validate time format (HH:MM)"""
    try:
        parts = time_str.split(':')
        if len(parts) != 2:
            return False
        hour = int(parts[0])
        minute = int(parts[1])
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except (ValueError, AttributeError):
        return False

def normalize_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize settings to canonical format (fills in missing fields with defaults)
    """
    if not settings:
        return CANONICAL_DEFAULTS.copy()
    
    normalized = CANONICAL_DEFAULTS.copy()
    
    # Handle old telegram_enabled field
    if 'telegram_enabled' in settings:
        normalized['channels']['telegram']['enabled'] = bool(settings['telegram_enabled'])
    
    # Merge channels
    if 'channels' in settings and isinstance(settings['channels'], dict):
        if 'telegram' in settings['channels']:
            normalized['channels']['telegram'].update(settings['channels']['telegram'])
        if 'email' in settings['channels']:
            normalized['channels']['email'].update(settings['channels']['email'])
    
    # Handle old alert_types field (snake_case)
    if 'alert_types' in settings and isinstance(settings['alert_types'], dict):
        for key, value in settings['alert_types'].items():
            # Convert snake_case to camelCase
            camel_key = 'liveNews' if key == 'live_news' else \
                       'preNews' if key == 'pre_news' else \
                       'postNews' if key == 'post_news' else \
                       'technicalAnalysis' if key == 'technical_analysis' else key
            if camel_key in normalized['preferences']['alertTypes']:
                normalized['preferences']['alertTypes'][camel_key] = bool(value)
    
    # Handle old impact_levels field (snake_case)
    if 'impact_levels' in settings and isinstance(settings['impact_levels'], dict):
        for key, value in settings['impact_levels'].items():
            if key in normalized['preferences']['impactLevels']:
                normalized['preferences']['impactLevels'][key] = bool(value)
    
    # Merge preferences
    if 'preferences' in settings and isinstance(settings['preferences'], dict):
        prefs = settings['preferences']
        
        if 'alertTypes' in prefs and isinstance(prefs['alertTypes'], dict):
            normalized['preferences']['alertTypes'].update(prefs['alertTypes'])
        
        if 'impactLevels' in prefs and isinstance(prefs['impactLevels'], dict):
            normalized['preferences']['impactLevels'].update(prefs['impactLevels'])
        
        if 'currencyPairs' in prefs and isinstance(prefs['currencyPairs'], list):
            normalized['preferences']['currencyPairs'] = prefs['currencyPairs']
        
        if 'quietHours' in prefs and isinstance(prefs['quietHours'], dict):
            normalized['preferences']['quietHours'].update(prefs['quietHours'])
    
    return normalized

