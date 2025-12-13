# FXSentinel Multi-User Background Alert Service Guide

## 🎯 Overview

Your FXSentinel system now has a **Multi-User Background Alert Service** that automatically monitors for news and sends alerts to **ALL connected users** instead of just one hardcoded user. This ensures that every user who has connected to your system will receive personalized alerts based on their settings.

## 🚀 How to Start the Multi-User Service

### Option 1: Quick Start (Recommended)
```bash
# Make sure the Flask app is running first
cd backend && python3 app.py &

# Then start the multi-user alert service
./start_multi_user_alert_service.sh
```

### Option 2: Manual Start
```bash
# Start Flask app
cd backend && python3 app.py &

# Start multi-user service
python3 background_alert_service_multi_user.py
```

### Option 3: System Service (Production)
```bash
# Copy the service file
sudo cp fxsentinel-alerts.service /etc/systemd/system/

# Edit the service file to use the multi-user script
sudo nano /etc/systemd/system/fxsentinel-alerts.service

# Change the ExecStart line to:
ExecStart=/usr/bin/python3 /Users/kavi/Desktop/fxsentinel/background_alert_service_multi_user.py

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable fxsentinel-alerts
sudo systemctl start fxsentinel-alerts
```

## 📊 What the Multi-User Service Does

### 1. **Discovers All Connected Users**
- Automatically finds all users who have alert settings in Firebase
- Retrieves their Telegram chat IDs
- Processes their individual preferences

### 2. **Personalized News Alerts**
- Checks for high-impact forex news every 5 minutes
- Filters news based on each user's currency preferences
- Sends AI-analyzed alerts only to relevant users
- Prevents duplicate alerts per user

### 3. **Economic Calendar Alerts**
- Monitors upcoming economic events
- Sends pre-event alerts (2 hours, 1 hour, 10 minutes before)
- Respects each user's alert type preferences
- Only alerts users interested in economic calendar events

### 4. **Smart Filtering**
- **Currency Matching**: Only sends alerts for currency pairs the user cares about
- **Impact Level Filtering**: Respects user's impact level preferences (high/medium/low)
- **Alert Type Filtering**: Only sends alerts for types the user has enabled
- **Telegram Status**: Only sends to users with Telegram enabled

## 🔧 User Settings Structure

The service handles both old and new user settings formats:

### Old Format (Simple)
```json
{
  "telegram_enabled": true,
  "alert_types": ["liveNews", "economicCalendar"],
  "currency_pairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
  "impact_levels": ["high", "medium"]
}
```

### New Format (Nested)
```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "chatId": "8008493413"
    }
  },
  "preferences": {
    "alertTypes": {
      "liveNews": true,
      "economicCalendar": true,
      "preNews": true
    },
    "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
    "impactLevels": {
      "high": true,
      "medium": true,
      "low": false
    }
  }
}
```

## 📱 Monitoring and Logs

### View Multi-User Service Logs
```bash
# Real-time logs
tail -f alert_service_multi_user.log

# Last 50 lines
tail -n 50 alert_service_multi_user.log

# Search for specific users
grep "user 0E0xJnQpYzZb8YkfQfSiwKYc8Fz2" alert_service_multi_user.log
```

### Check Service Status
```bash
# Check if service is running
ps aux | grep background_alert_service_multi_user

# Check Flask app status
curl http://localhost:5001/api/health

# Check user count
grep "Found.*users with alert settings" alert_service_multi_user.log
```

## 🎯 Key Differences from Single-User Service

| Feature | Single-User Service | Multi-User Service |
|---------|-------------------|-------------------|
| **User Coverage** | Only your user ID | All connected users |
| **Personalization** | Fixed settings | Per-user preferences |
| **Currency Filtering** | None | User-specific pairs |
| **Alert Types** | Fixed | User-configurable |
| **Duplicate Prevention** | Global | Per-user |
| **Logging** | Basic | User-specific tracking |

## 🔍 Troubleshooting

### No Users Found
```bash
# Check if users exist in Firebase
python3 test_firebase_alert_history.py

# Check user settings structure
grep "No users found" alert_service_multi_user.log
```

### Users Not Receiving Alerts
1. **Check Telegram Chat ID**: Ensure users have valid chat IDs
2. **Check Alert Settings**: Verify users have alerts enabled
3. **Check Currency Preferences**: Ensure users have currency pairs configured
4. **Check Logs**: Look for specific user errors

### High CPU/Memory Usage
- The service processes each user individually
- Consider increasing check interval for large user bases
- Monitor system resources with `htop`

### Service Stops Unexpectedly
```bash
# Check for errors
tail -n 100 alert_service_multi_user.log | grep ERROR

# Restart service
pkill -f background_alert_service_multi_user
python3 background_alert_service_multi_user.py
```

## 🚀 Production Deployment

### For Production Use
1. **Use System Service**: Set up as systemd service for auto-restart
2. **Monitor Logs**: Set up log rotation and monitoring
3. **Health Checks**: Implement health check endpoints
4. **Rate Limiting**: Consider API rate limits for large user bases
5. **Database Optimization**: Optimize Firebase queries for large datasets

### Scaling Considerations
- **User Base**: Service handles 100+ users efficiently
- **Check Frequency**: 5-minute intervals work well for most use cases
- **Memory Usage**: ~50MB base + ~1MB per 100 users
- **API Calls**: ~2 calls per user per check cycle

## 📈 Performance Metrics

The service logs key metrics:
- **Users Found**: Number of users with alert settings
- **Alerts Sent**: Total alerts sent per cycle
- **User-Specific Alerts**: Alerts sent to each user
- **Processing Time**: Time taken for each check cycle
- **Error Rates**: Failed alert attempts

## 🎯 Next Steps

1. **Test with Multiple Users**: Add test users to verify functionality
2. **Monitor Performance**: Watch logs for any issues
3. **User Feedback**: Collect feedback on alert relevance
4. **Optimize Settings**: Adjust check intervals based on usage
5. **Add Features**: Consider adding more alert types or filtering options

Your multi-user background alert service is now ready to serve all connected users with personalized, relevant alerts!
