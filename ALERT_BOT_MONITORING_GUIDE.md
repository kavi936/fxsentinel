# FXSentinel Alert Bot Monitoring Guide

## 🎯 Overview

This guide provides comprehensive instructions on how to monitor your FXSentinel alert bot system to ensure it's actively working and searching for new items to send alerts. The system includes multiple monitoring tools and methods to check the health and activity of your alert bot.

## 🔍 What We Monitor

The alert bot monitoring system tracks several key components:

### **Core Alert Service**
- **Service Status**: Whether the robust alert service is running
- **Uptime**: How long the service has been running
- **Last Successful Check**: When the service last processed alerts
- **Error Count**: Number of consecutive errors
- **Memory Usage**: System resource consumption

### **Alert Activity**
- **Alerts Sent Today**: Number of successful alert deliveries
- **Alerts Failed Today**: Number of failed alert attempts
- **Success Rate**: Percentage of successful deliveries
- **Users Processed**: Number of users the service has processed

### **System Health**
- **Telegram Bot Connection**: Whether the bot can send messages
- **Firebase Connection**: Database connectivity status
- **Background Processes**: Status of critical monitoring processes
- **Overall System Status**: Combined health assessment

## 🛠️ Monitoring Tools

### **1. Comprehensive Status Checker**

**File**: `check_alert_bot_status.py`

This script provides a one-time comprehensive check of your entire alert bot system.

**Usage**:
```bash
# Basic check (uses localhost:5001)
python3 check_alert_bot_status.py

# Check custom URL
python3 check_alert_bot_status.py --url http://your-domain.com

# Set custom URL via environment variable
export FXSENTINEL_URL=http://your-domain.com
python3 check_alert_bot_status.py
```

**What it checks**:
- All health endpoints (`/api/health/*`)
- Alert service status and activity
- Recent activity within the last 15 minutes
- Background process status
- Telegram connection status
- Overall system health

**Output Example**:
```
🚀 FXSentinel Alert Bot Status Check
============================================================
🔗 Checking: http://localhost:5001
⏰ Time: 2025-01-20 15:30:45

🔍 Checking Alert Bot System Health...
============================================================
✅ Main Health: HEALTHY
✅ Alerts Health: HEALTHY
✅ Telegram Health: HEALTHY
✅ Calendar Health: HEALTHY
✅ News Health: HEALTHY
✅ System Health: HEALTHY

🤖 Checking Alert Service Status...
----------------------------------------
📊 Service Status: RUNNING
⏱️  Uptime: 2h 15m
📨 Alerts Sent Today: 12
❌ Alerts Failed Today: 1
🔄 Last Successful Check: 2025-01-20T15:28:30Z
⚠️  Error Count: 0
✅ Alert Service: ACTIVELY WORKING

📈 Checking Recent Activity...
----------------------------------------
🕐 Last Activity: 2025-01-20 15:28:30
⏰ Time Since Last Check: 2m 15s
👥 Users Processed: 45
📨 Total Alerts Sent Today: 12
✅ Recent Activity: DETECTED

🔄 Checking Background Processes...
----------------------------------------
✅ alert_triggers: RUNNING - Healthy
✅ telegram_monitor: RUNNING - Healthy
✅ news_aggregator: RUNNING - Healthy
✅ All Critical Processes: RUNNING

📱 Checking Telegram Connection...
----------------------------------------
✅ Telegram Bot: CONNECTED

============================================================
📊 OVERALL SYSTEM STATUS
============================================================
✅ ALERT BOT SYSTEM: FULLY OPERATIONAL
🎯 The bot is actively working and searching for new items to alert

📋 Summary:
   • Alert Service Active: ✅
   • Recent Activity: ✅
   • Background Processes: ✅
   • Telegram Connected: ✅
```

### **2. Continuous Monitor**

**File**: `monitor_alert_bot.py`

This script provides real-time continuous monitoring with status updates every 30 seconds.

**Usage**:
```bash
# Basic monitoring (30-second intervals)
python3 monitor_alert_bot.py

# Custom check interval (60 seconds)
python3 monitor_alert_bot.py --interval 60

# Custom URL
python3 monitor_alert_bot.py --url http://your-domain.com --interval 45

# Save monitoring history
python3 monitor_alert_bot.py --save-history
```

**Output Example**:
```
🚀 Starting FXSentinel Alert Bot Monitor
🔗 Monitoring: http://localhost:5001
⏰ Check Interval: 30 seconds
================================================================================
Format: [TIME] STATUS | Uptime | Alerts (sent/failed) | Errors | Last Check
================================================================================
[15:30:15] 🟢 RUNNING | Uptime: 2h 15m | Alerts: 12✅/1❌ | Errors: 0 | Last: 2m ago
[15:30:45] 🟢 RUNNING | Uptime: 2h 16m | Alerts: 12✅/1❌ | Errors: 0 | Last: 32s ago
[15:31:15] 🟢 RUNNING | Uptime: 2h 16m | Alerts: 13✅/1❌ | Errors: 0 | Last: 2s ago
⚠️  SIGNIFICANT STATUS CHANGE DETECTED
[15:31:45] 🟢 RUNNING | Uptime: 2h 17m | Alerts: 13✅/1❌ | Errors: 0 | Last: 32s ago
```

### **3. Web Dashboard**

**File**: `alert_bot_dashboard.html`

A beautiful web-based dashboard that provides real-time monitoring with auto-refresh.

**Usage**:
```bash
# Open in browser (make sure your backend is running)
open alert_bot_dashboard.html

# Or serve via Python
python3 -m http.server 8080
# Then open http://localhost:8080/alert_bot_dashboard.html
```

**Features**:
- Real-time status updates every 30 seconds
- Color-coded status indicators (green=healthy, yellow=warning, red=error)
- Success rate visualization
- Mobile-responsive design
- Auto-refresh toggle
- Manual refresh button

## 🔧 API Endpoints for Monitoring

Your system provides several health check endpoints:

### **Main Health Check**
```bash
curl http://localhost:5001/api/health
```

### **Alert System Health**
```bash
curl http://localhost:5001/api/health/alerts
```

### **Telegram Health**
```bash
curl http://localhost:5001/api/health/telegram
```

### **System Health**
```bash
curl http://localhost:5001/api/health/system
```

## 📊 How to Interpret Results

### **✅ Healthy System Indicators**
- **Service Status**: `running`
- **Uptime**: > 0 seconds
- **Error Count**: < 10
- **Last Check**: Within last 10 minutes
- **Telegram Bot**: `connected`
- **Recent Activity**: Within last 15 minutes

### **⚠️ Warning Indicators**
- **Service Status**: `degraded` or `restarting`
- **Error Count**: 5-9 errors
- **Last Check**: 10-15 minutes ago
- **Memory Usage**: > 400MB
- **Success Rate**: 70-89%

### **❌ Critical Issues**
- **Service Status**: `stopped`, `error`, or `unknown`
- **Error Count**: ≥ 10 errors
- **Last Check**: > 15 minutes ago
- **Telegram Bot**: `disconnected`
- **Success Rate**: < 70%

## 🚨 Troubleshooting Common Issues

### **Alert Service Not Running**
```bash
# Check if the robust alert service is started
python3 backend/services/robust_alert_service.py

# Or start it manually
cd backend
python3 -c "from services.robust_alert_service import start_robust_alert_service; start_robust_alert_service()"
```

### **Telegram Bot Disconnected**
```bash
# Check Telegram bot configuration
curl http://localhost:5001/api/health/alerts | jq '.telegram_bot'

# Verify bot token in environment
echo $TELEGRAM_BOT_TOKEN
```

### **High Error Count**
```bash
# Check service logs
tail -f robust_alert_service.log

# Check for specific error types
grep "ERROR" robust_alert_service.log | tail -20
```

### **No Recent Activity**
```bash
# Check if news sources are working
curl http://localhost:5001/api/health/news

# Check if economic calendar is working
curl http://localhost:5001/api/health/calendar
```

## 🔄 Automated Monitoring Setup

### **Cron Job for Regular Checks**
```bash
# Add to crontab for hourly checks
0 * * * * cd /path/to/fxsentinel && python3 check_alert_bot_status.py >> monitoring.log 2>&1

# Add to crontab for daily summary
0 9 * * * cd /path/to/fxsentinel && python3 check_alert_bot_status.py > daily_status_$(date +\%Y\%m\%d).json
```

### **Systemd Service for Continuous Monitoring**
Create `/etc/systemd/system/fxsentinel-monitor.service`:
```ini
[Unit]
Description=FXSentinel Alert Bot Monitor
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/fxsentinel
ExecStart=/usr/bin/python3 monitor_alert_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable fxsentinel-monitor
sudo systemctl start fxsentinel-monitor
sudo systemctl status fxsentinel-monitor
```

## 📈 Performance Metrics

### **Key Performance Indicators (KPIs)**
- **Uptime**: Should be > 99%
- **Success Rate**: Should be > 90%
- **Response Time**: Last check should be < 10 minutes
- **Error Rate**: Should be < 5%

### **Monitoring Alerts**
Set up alerts for:
- Service status changes from `running` to other states
- Error count > 5
- No activity for > 15 minutes
- Success rate < 80%

## 🎯 Quick Status Commands

### **One-liner Status Check**
```bash
curl -s http://localhost:5001/api/health/alerts | jq -r '.robust_service.status'
```

### **Quick Health Overview**
```bash
curl -s http://localhost:5001/api/health/alerts | jq '{status: .status, service: .robust_service.status, uptime: .robust_service.uptime_seconds, alerts: .robust_service.alerts_sent_today}'
```

### **Check if Bot is Actively Working**
```bash
python3 -c "
import requests, json
from datetime import datetime, timedelta
data = requests.get('http://localhost:5001/api/health/alerts').json()
robust = data.get('robust_service', {})
status = robust.get('status') == 'running'
last_check = robust.get('last_successful_check')
if last_check:
    last_time = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
    recent = datetime.now().replace(tzinfo=None) - last_time.replace(tzinfo=None) < timedelta(minutes=10)
else:
    recent = False
print(f'Active: {status and recent}')
"
```

## 🔍 Advanced Monitoring

### **Custom Monitoring Script**
You can create custom monitoring scripts that integrate with your existing monitoring systems (Nagios, Zabbix, etc.) by using the health endpoints.

### **Log Analysis**
```bash
# Monitor for specific patterns
tail -f robust_alert_service.log | grep -E "(ERROR|WARNING|SIGNIFICANT)"

# Check for alert delivery patterns
grep "Alert sent" robust_alert_service.log | tail -20
```

This comprehensive monitoring system ensures you can always know whether your alert bot is actively working and searching for new items to alert your users about. The multiple tools provide different levels of detail and monitoring frequency to suit your needs.
