# FXSentinel Background Alert Service Setup Guide

## 🎯 Overview

The FXSentinel Background Alert Service automatically monitors for:
- **Live News Alerts**: High-impact forex news with AI analysis
- **Economic Calendar Alerts**: Pre-event notifications for important economic releases
- **Market Updates**: Real-time notifications for major currency pairs

## 🚀 Quick Start (Recommended)

### Option 1: Simple Background Service

1. **Start the Flask app** (if not already running):
   ```bash
   cd backend
   python3 app.py
   ```

2. **Start the background alert service**:
   ```bash
   ./start_alert_service.sh
   ```

   Or manually:
   ```bash
   python3 background_alert_service.py
   ```

3. **The service will**:
   - Check for new high-impact news every 5 minutes
   - Monitor economic calendar for upcoming events
   - Send alerts to your Telegram bot automatically
   - Log all activity to `alert_service.log`

## ⚙️ Advanced Setup Options

### Option 2: System Service (macOS/Linux)

1. **Install as system service**:
   ```bash
   # Copy service file to systemd directory
   sudo cp fxsentinel-alerts.service /etc/systemd/system/
   
   # Reload systemd
   sudo systemctl daemon-reload
   
   # Enable and start the service
   sudo systemctl enable fxsentinel-alerts
   sudo systemctl start fxsentinel-alerts
   ```

2. **Check service status**:
   ```bash
   sudo systemctl status fxsentinel-alerts
   ```

3. **View logs**:
   ```bash
   sudo journalctl -u fxsentinel-alerts -f
   ```

### Option 3: Screen/Tmux Session

1. **Create a persistent session**:
   ```bash
   # Using screen
   screen -S fxsentinel-alerts
   python3 background_alert_service.py
   
   # Detach: Ctrl+A, then D
   # Reattach: screen -r fxsentinel-alerts
   ```

   Or using tmux:
   ```bash
   # Using tmux
   tmux new-session -d -s fxsentinel-alerts 'python3 background_alert_service.py'
   
   # Attach: tmux attach-session -t fxsentinel-alerts
   # Detach: Ctrl+B, then D
   ```

## 📊 Service Configuration

### Check Interval
The service checks for new alerts every **5 minutes** by default. To change this:

Edit `background_alert_service.py`:
```python
self.check_interval = 300  # Change to desired seconds
```

### Alert Types
The service monitors for:
- **Live News**: High-impact forex news
- **Economic Calendar**: Upcoming economic events
- **Currency Pairs**: EUR/USD, USD/JPY, GBP/USD, USD/CHF, AUD/USD, USD/CAD

### User Settings
Your current configuration:
- **User ID**: 0E0xJnQpYzZb8YkfQfSiwKYc8Fz2
- **Chat ID**: 8008493413
- **Alert Types**: Live news + Economic calendar
- **Impact Levels**: High + Medium

## 📱 Monitoring and Logs

### View Service Logs
```bash
# Real-time logs
tail -f alert_service.log

# Last 50 lines
tail -n 50 alert_service.log

# Search for alerts
grep "Alert sent" alert_service.log
```

### Service Status
```bash
# Check if service is running
ps aux | grep background_alert_service

# Check Flask app status
curl http://localhost:5001/api/health
```

## 🔧 Troubleshooting

### Service Won't Start
1. **Check Flask app**: Ensure `python3 app.py` is running
2. **Check dependencies**: Ensure all Python packages are installed
3. **Check permissions**: Ensure script is executable (`chmod +x start_alert_service.sh`)

### No Alerts Received
1. **Check Telegram connection**: Verify bot is working
2. **Check user settings**: Ensure user ID and chat ID are correct
3. **Check logs**: Look for errors in `alert_service.log`

### High CPU/Memory Usage
1. **Adjust check interval**: Increase `check_interval` to reduce frequency
2. **Limit processed items**: Reduce the number of news items processed
3. **Monitor system resources**: Use `htop` or `top` to monitor usage

## 🎯 What You'll Receive

### Live News Alerts
```
🚨 BREAKING FOREX NEWS
**Fed Announces Interest Rate Decision**

**Time:** 14:00 UTC | **Source:** Reuters
**Pairs:** EUR/USD, USD/JPY, GBP/USD

🤖 **AI Analysis:**
The Federal Reserve's decision to raise rates by 25 basis points...
```

### Economic Calendar Alerts
```
📅 UPCOMING ECONOMIC EVENT
**US CPI Data Release**

**Time:** 13:30 UTC | **Impact:** HIGH
**Currency:** USD
**Expected:** 3.2% | **Previous:** 3.1%

💱 **Affected Pairs:** EUR/USD, USD/JPY, GBP/USD
```

## 🔄 Service Management

### Start Service
```bash
./start_alert_service.sh
```

### Stop Service
```bash
# If running in foreground: Ctrl+C
# If running as system service:
sudo systemctl stop fxsentinel-alerts
```

### Restart Service
```bash
# If running as system service:
sudo systemctl restart fxsentinel-alerts
```

### Update Configuration
1. Stop the service
2. Edit `background_alert_service.py`
3. Restart the service

## 📈 Performance Optimization

### For Production Use
1. **Increase check interval** to 10-15 minutes
2. **Limit AI analysis** to reduce API costs
3. **Use system service** for automatic restarts
4. **Monitor logs** for performance issues

### For Development
1. **Decrease check interval** to 1-2 minutes
2. **Enable verbose logging**
3. **Test with manual triggers**

## 🎉 Success Indicators

You'll know the service is working when you receive:
- ✅ Regular news alerts for high-impact events
- ✅ Economic calendar pre-event notifications
- ✅ AI analysis of market-moving news
- ✅ Consistent logging in `alert_service.log`

## 📞 Support

If you encounter issues:
1. Check the logs: `tail -f alert_service.log`
2. Verify Flask app is running: `curl http://localhost:5001/api/health`
3. Test manual alerts: `python3 manual_alert_processor.py`
4. Check Telegram connection: Verify bot messages are received
