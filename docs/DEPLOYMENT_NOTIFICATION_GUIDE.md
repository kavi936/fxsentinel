# Deployment Notification System Guide

## Overview

The deployment notification system allows you to force all users to clear their cache and refresh their news feed when you deploy updates. This ensures that all users get the latest news immediately, including new features like Telegram integration.

## How It Works

1. **Deployment Notification**: When activated, all users who request news will receive a deployment notification
2. **Automatic Cache Clearing**: The system automatically clears server-side caches when a deployment notification is active
3. **Force Refresh**: All users are forced to get fresh news instead of using cached data
4. **User Notification**: The frontend can display a notification to users about the update

## Usage

### Trigger Deployment Notification

```bash
# Basic usage (default message)
python3 trigger_deployment_notification.py

# With custom message
python3 trigger_deployment_notification.py trigger "Telegram integration deployed - clearing cache"

# With custom message and version
python3 trigger_deployment_notification.py trigger "Major update deployed" "2.0.0"
```

### Check Deployment Status

```bash
python3 trigger_deployment_notification.py status
```

### Clear Deployment Notification

```bash
python3 trigger_deployment_notification.py clear
```

## API Endpoints

### Set Deployment Notification
- **POST** `/api/deployment-notification`
- **Body**: 
  ```json
  {
    "message": "System update deployed - clearing cache and refreshing news feed",
    "version": "1.0.0",
    "requires_cache_clear": true
  }
  ```

### Get Deployment Notification Status
- **GET** `/api/deployment-notification`
- **Returns**: Current deployment notification status

### Clear Deployment Notification
- **POST** `/api/clear-deployment-notification`
- **Clears**: The deployment notification

### Clear All Server Caches
- **POST** `/api/clear-all-caches`
- **Clears**: All server-side caches (news, GPT, etc.)

## Response Format

When a deployment notification is active, the `/api/news` endpoint will include:

```json
{
  "news": [...],
  "deployment_notification": {
    "active": true,
    "timestamp": "2025-01-26T10:30:00",
    "message": "System update deployed - clearing cache and refreshing news feed",
    "version": "1.0.0",
    "requires_cache_clear": true
  }
}
```

## Frontend Integration

The frontend should check for `deployment_notification` in the news response and:

1. **Display a notification** to the user about the update
2. **Clear local cache** if `requires_cache_clear` is true
3. **Force refresh** the news feed
4. **Show the message** to inform users about the update

## Example Workflow

1. **Deploy code** to Railway
2. **Wait for deployment** to complete
3. **Trigger notification**:
   ```bash
   python3 trigger_deployment_notification.py trigger "Telegram integration deployed - WatcherGuru alerts now available"
   ```
4. **All users** will automatically clear their cache and get fresh news
5. **Clear notification** when ready:
   ```bash
   python3 trigger_deployment_notification.py clear
   ```

## Benefits

- **Immediate Updates**: All users get fresh news immediately after deployment
- **Cache Consistency**: Ensures no stale data remains in user caches
- **User Awareness**: Users are notified about system updates
- **Automated Process**: No manual intervention required for each user
- **Telegram Integration**: Ensures Telegram news (like WatcherGuru) appears immediately

## Troubleshooting

### Check if deployment notification is working:
```bash
python3 trigger_deployment_notification.py status
```

### Force clear all caches:
```bash
curl -X POST https://fxsentinel-production.up.railway.app/api/clear-all-caches
```

### Test force refresh:
```bash
curl -X POST https://fxsentinel-production.up.railway.app/api/force-refresh-news
```
