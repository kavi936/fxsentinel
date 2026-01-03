# Canonical Alert Settings Format

This document defines the canonical (standard) format for user alert settings in FXSentinel.

## Canonical Structure

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "chatId": "8008493413",
      "username": "K7IV_1"
    },
    "email": {
      "enabled": false,
      "address": ""
    }
  },
  "preferences": {
    "impactLevels": {
      "high": true,
      "medium": true,
      "low": false
    },
    "alertTypes": {
      "liveNews": true,
      "preNews": true,
      "postNews": true,
      "technicalAnalysis": false
    },
    "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
    "quietHours": {
      "enabled": false,
      "start": "22:00",
      "end": "06:00",
      "timezone": "UTC"
    }
  }
}
```

## Field Descriptions

### channels.telegram
- **enabled**: Boolean - Whether Telegram alerts are enabled
- **chatId**: String - Telegram chat ID (stored separately in `alerts/users/{user_id}/telegram_chat_id`)
- **username**: String - Telegram username (optional, for display)

### channels.email
- **enabled**: Boolean - Whether email alerts are enabled
- **address**: String - Email address

### preferences.impactLevels
- **high**: Boolean - Receive high impact alerts
- **medium**: Boolean - Receive medium impact alerts
- **low**: Boolean - Receive low impact alerts

### preferences.alertTypes
- **liveNews**: Boolean - Receive live breaking news alerts
- **preNews**: Boolean - Receive pre-news alerts (upcoming events)
- **postNews**: Boolean - Receive post-news analysis alerts
- **technicalAnalysis**: Boolean - Receive technical analysis alerts

### preferences.currencyPairs
- Array of strings - Currency pairs to monitor (e.g., ["EUR/USD", "GBP/USD"])

### preferences.quietHours
- **enabled**: Boolean - Whether quiet hours are enabled
- **start**: String - Start time in HH:MM format (24-hour)
- **end**: String - End time in HH:MM format (24-hour)
- **timezone**: String - Timezone (default: "UTC")

## Deprecated Structures (to be migrated)

### Old Structure 1: Direct settings
```json
{
  "telegram_enabled": true,
  "telegram_chat_id": "8008493413",
  "alert_types": {
    "liveNews": true
  },
  "impact_levels": {
    "high": true
  }
}
```

### Old Structure 2: Mixed structure
```json
{
  "telegram": true,
  "channels": {
    "telegram": {
      "enabled": true
    }
  },
  "preferences": {
    "alertTypes": {
      "liveNews": true
    }
  }
}
```

## Migration Rules

1. **telegram_enabled** → **channels.telegram.enabled**
2. **telegram_chat_id** → Removed (stored in `alerts/users/{user_id}/telegram_chat_id`)
3. **alert_types** → **preferences.alertTypes** (camelCase keys)
4. **impact_levels** → **preferences.impactLevels** (camelCase keys)
5. **currency_pairs** → **preferences.currencyPairs** (camelCase)
6. **quiet_hours** → **preferences.quietHours** (camelCase)

## Validation Rules

1. **channels.telegram.enabled** must be boolean
2. **channels.telegram.chatId** should be empty string (chat_id stored separately)
3. **preferences.alertTypes** must be object with boolean values
4. **preferences.impactLevels** must be object with boolean values
5. **preferences.currencyPairs** must be array of strings
6. **preferences.quietHours** must have enabled (boolean), start (string), end (string), timezone (string)

