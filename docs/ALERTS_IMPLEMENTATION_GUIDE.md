# FXSentinel Alerts Implementation Guide

## Overview

The alerts system is a core feature of FXSentinel that provides real-time notifications to users about important market events and AI analysis results. Based on your project structure and the existing live news analysis functionality, here's how to implement a comprehensive alerts system.

## Current State Analysis

### Existing Infrastructure
- **Live News Feed**: Already implemented with AI analysis capabilities
- **Telegram Integration**: WatcherGuru channel monitoring via `telegram_monitor_user.py`
- **AI Analysis**: GPT-powered analysis of news items with detailed market impact assessment
- **User Management**: Authentication system with user profiles and preferences
- **Backend API**: Flask-based API with endpoints for news, analysis, and user data

### What's Missing for Alerts
- **Alert Configuration UI**: User interface for setting up alert preferences
- **Alert Triggering Logic**: System to detect when alerts should be sent
- **Notification Delivery**: Telegram bot and email service for sending alerts
- **Alert History**: Tracking and displaying sent alerts
- **User Alert Settings**: Database storage for user preferences

## Alert System Architecture

### 1. Alert Types

#### **Pre-News Alerts**
- **Trigger**: Upcoming high-impact economic events (CPI, NFP, Fed meetings)
- **Content**: Event preview, expected market impact, key levels to watch
- **Timing**: 1-2 hours before event release
- **Source**: Economic calendar data

#### **Post-News Alerts**
- **Trigger**: News release with significant deviation from expectations
- **Content**: AI analysis of actual vs expected data, immediate market reaction
- **Timing**: 5-15 minutes after news release
- **Source**: Live news feed + AI analysis

#### **Live News Alerts**
- **Trigger**: Breaking news with high market impact
- **Content**: Quick AI analysis, affected currency pairs, volatility assessment
- **Timing**: Real-time (within 1-2 minutes of news)
- **Source**: WatcherGuru Telegram channel + AI analysis

#### **Technical Analysis Alerts**
- **Trigger**: Significant price movements or technical breakouts
- **Content**: Technical analysis, support/resistance levels, trading opportunities
- **Timing**: Real-time based on price action
- **Source**: Market data feeds + technical analysis

### 2. Alert Configuration System

#### **User Alert Settings**
```javascript
// Alert Settings Structure
{
  userId: "user123",
  channels: {
    telegram: {
      enabled: true,
      chatId: "123456789",
      username: "@user123"
    },
    email: {
      enabled: false,
      address: "user@example.com"
    }
  },
  preferences: {
    impactLevels: {
      high: true,
      medium: true,
      low: false
    },
    alertTypes: {
      preNews: true,
      postNews: true,
      liveNews: true,
      technicalAnalysis: false
    },
    currencyPairs: ["EUR/USD", "USD/JPY", "GBP/USD"],
    quietHours: {
      enabled: true,
      start: "22:00",
      end: "06:00",
      timezone: "UTC"
    }
  }
}
```

#### **Alert Content Templates**
```javascript
// Pre-News Alert Template
{
  type: "pre_news",
  title: "🚨 HIGH IMPACT EVENT: US CPI Data",
  content: `
📊 Event: US Consumer Price Index (CPI)
⏰ Time: 13:30 UTC (2 hours from now)
📈 Expected: 3.1% YoY
🎯 Key Levels: EUR/USD 1.0850, USD/JPY 148.00

💡 Market Impact:
• Higher than expected → USD Bullish
• Lower than expected → USD Bearish
• Watch for volatility spike

🔍 AI Analysis: Market positioning suggests...
  `,
  priority: "high",
  currencyPairs: ["EUR/USD", "USD/JPY", "GBP/USD"]
}

// Post-News Alert Template
{
  type: "post_news",
  title: "📊 US CPI ACTUAL: 3.2% (vs 3.1% expected)",
  content: `
🔥 BREAKING: US CPI comes in ABOVE expectations!

📊 Data:
• Actual: 3.2% YoY
• Expected: 3.1% YoY
• Previous: 3.1% YoY

💥 Immediate Market Reaction:
• USD strengthening across the board
• EUR/USD down 20 pips to 1.0830
• USD/JPY up 15 pips to 148.15

🤖 AI Analysis: This higher-than-expected inflation...
  `,
  priority: "high",
  currencyPairs: ["EUR/USD", "USD/JPY", "GBP/USD"]
}
```

### 3. Technical Implementation

#### **Backend Alert Service**

Create `backend/services/alert_service.py`:

```python
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from telegram import Bot
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertService:
    def __init__(self):
        self.telegram_bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD')
        }
        
    async def send_telegram_alert(self, chat_id: str, message: str, parse_mode: str = 'HTML'):
        """Send alert via Telegram"""
        try:
            await self.telegram_bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            logging.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def send_email_alert(self, email: str, subject: str, content: str):
        """Send alert via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'html'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")
            return False
    
    async def process_alert(self, alert_data: Dict[str, Any], user_settings: Dict[str, Any]):
        """Process and send alert to user based on their settings"""
        # Check if user wants this type of alert
        if not self._should_send_alert(alert_data, user_settings):
            return False
        
        # Check quiet hours
        if self._is_quiet_hours(user_settings):
            return False
        
        # Send via configured channels
        success = True
        
        if user_settings['channels']['telegram']['enabled']:
            telegram_success = await self.send_telegram_alert(
                user_settings['channels']['telegram']['chatId'],
                self._format_telegram_message(alert_data)
            )
            success = success and telegram_success
        
        if user_settings['channels']['email']['enabled']:
            email_success = self.send_email_alert(
                user_settings['channels']['email']['address'],
                alert_data['title'],
                self._format_email_message(alert_data)
            )
            success = success and email_success
        
        return success
```

#### **Alert Triggering System**

Create `backend/services/alert_triggers.py`:

```python
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
from .alert_service import AlertService
from .telegram_monitor_user import telegram_user_monitor
from .enhanced_ai_analysis import analyze_news_with_gpt

class AlertTriggers:
    def __init__(self):
        self.alert_service = AlertService()
        
    async def check_live_news_alerts(self):
        """Check for new high-impact news and trigger alerts"""
        try:
            # Get recent news from WatcherGuru
            recent_news = await telegram_user_monitor.get_recent_telegram_news(hours=1)
            
            for news_item in recent_news:
                # Only alert for high-impact news
                if news_item['impact'] == 'high':
                    # Get AI analysis
                    analysis = await analyze_news_with_gpt(news_item)
                    
                    # Create alert data
                    alert_data = {
                        'type': 'live_news',
                        'title': f"🔥 BREAKING: {news_item['title']}",
                        'content': self._format_live_news_alert(news_item, analysis),
                        'priority': 'high',
                        'currencyPairs': news_item.get('currency_pairs', []),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Send to all users with live news alerts enabled
                    await self._send_to_subscribers(alert_data, 'liveNews')
                    
        except Exception as e:
            logging.error(f"Error checking live news alerts: {e}")
    
    async def check_economic_calendar_alerts(self):
        """Check upcoming economic events and send pre-news alerts"""
        try:
            # Get upcoming high-impact events (next 2 hours)
            upcoming_events = self._get_upcoming_events(hours=2)
            
            for event in upcoming_events:
                if event['impact'] == 'high':
                    alert_data = {
                        'type': 'pre_news',
                        'title': f"🚨 UPCOMING: {event['title']}",
                        'content': self._format_pre_news_alert(event),
                        'priority': 'high',
                        'currencyPairs': event.get('currency_pairs', []),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    await self._send_to_subscribers(alert_data, 'preNews')
                    
        except Exception as e:
            logging.error(f"Error checking economic calendar alerts: {e}")
    
    async def _send_to_subscribers(self, alert_data: Dict[str, Any], alert_type: str):
        """Send alert to all users who have this type enabled"""
        # Get all users with this alert type enabled
        users = self._get_users_with_alert_enabled(alert_type)
        
        for user in users:
            await self.alert_service.process_alert(alert_data, user['alert_settings'])
```

#### **Frontend Alert Configuration**

Enhance the existing `src/components/Alerts.jsx`:

```jsx
import React, { useState, useEffect } from 'react';
import { config } from '../config';
import './Alerts.css';

const Alerts = () => {
  const [alertSettings, setAlertSettings] = useState({
    channels: {
      telegram: { enabled: false, chatId: '', username: '' },
      email: { enabled: false, address: '' }
    },
    preferences: {
      impactLevels: { high: true, medium: true, low: false },
      alertTypes: { preNews: true, postNews: true, liveNews: true, technicalAnalysis: false },
      currencyPairs: ['EUR/USD', 'USD/JPY', 'GBP/USD'],
      quietHours: { enabled: false, start: '22:00', end: '06:00', timezone: 'UTC' }
    }
  });
  
  const [telegramSetup, setTelegramSetup] = useState({
    step: 'connect', // connect, verify, complete
    botUsername: '@FXSentinelBot',
    instructions: []
  });
  
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  // Telegram Bot Setup Flow
  const setupTelegramBot = async () => {
    setLoading(true);
    try {
      // Step 1: Generate unique bot link
      const response = await fetch(`${config.API_BASE_URL}/api/telegram/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: 'current_user_id' })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setTelegramSetup({
          step: 'verify',
          botUsername: data.botUsername,
          instructions: [
            '1. Click the link below to start the bot',
            '2. Send /start to begin setup',
            '3. Follow the bot instructions to complete setup'
          ],
          botLink: data.botLink
        });
      }
    } catch (error) {
      console.error('Error setting up Telegram bot:', error);
    } finally {
      setLoading(false);
    }
  };

  const verifyTelegramConnection = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/telegram/verify`);
      const data = await response.json();
      
      if (data.connected) {
        setTelegramSetup({ step: 'complete' });
        setAlertSettings(prev => ({
          ...prev,
          channels: {
            ...prev.channels,
            telegram: { enabled: true, chatId: data.chatId, username: data.username }
          }
        }));
      }
    } catch (error) {
      console.error('Error verifying Telegram connection:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="alerts-section">
      <div className="alerts-header">
        <h2>🔔 Smart Alert System</h2>
        <p>Get instant notifications for important market events</p>
      </div>

      <div className="alerts-content">
        {/* Telegram Setup Section */}
        <div className="telegram-setup-section">
          <h3>📱 Telegram Bot Setup</h3>
          
          {telegramSetup.step === 'connect' && (
            <div className="setup-step">
              <p>Connect your Telegram account to receive instant alerts</p>
              <button 
                className="setup-telegram-btn"
                onClick={setupTelegramBot}
                disabled={loading}
              >
                {loading ? 'Setting up...' : 'Connect Telegram Bot'}
              </button>
            </div>
          )}
          
          {telegramSetup.step === 'verify' && (
            <div className="setup-step">
              <div className="bot-instructions">
                {telegramSetup.instructions.map((instruction, index) => (
                  <p key={index}>{instruction}</p>
                ))}
              </div>
              <a 
                href={telegramSetup.botLink} 
                target="_blank" 
                rel="noopener noreferrer"
                className="bot-link-btn"
              >
                Start @{telegramSetup.botUsername}
              </a>
              <button 
                className="verify-connection-btn"
                onClick={verifyTelegramConnection}
                disabled={loading}
              >
                {loading ? 'Verifying...' : 'I\'ve Completed Setup'}
              </button>
            </div>
          )}
          
          {telegramSetup.step === 'complete' && (
            <div className="setup-complete">
              <div className="success-icon">✅</div>
              <p>Telegram bot connected successfully!</p>
              <p>You'll now receive alerts on Telegram</p>
            </div>
          )}
        </div>

        {/* Alert Preferences */}
        <div className="alert-preferences">
          <h3>⚙️ Alert Preferences</h3>
          
          <div className="preferences-grid">
            <div className="preference-group">
              <h4>Impact Levels</h4>
              <label className="preference-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.preferences.impactLevels.high}
                  onChange={(e) => updatePreference('impactLevels', 'high', e.target.checked)}
                />
                <span>🔴 High Impact Events</span>
              </label>
              <label className="preference-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.preferences.impactLevels.medium}
                  onChange={(e) => updatePreference('impactLevels', 'medium', e.target.checked)}
                />
                <span>🟡 Medium Impact Events</span>
              </label>
              <label className="preference-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.preferences.impactLevels.low}
                  onChange={(e) => updatePreference('impactLevels', 'low', e.target.checked)}
                />
                <span>🟢 Low Impact Events</span>
              </label>
            </div>
            
            <div className="preference-group">
              <h4>Alert Types</h4>
              <label className="preference-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.preferences.alertTypes.preNews}
                  onChange={(e) => updatePreference('alertTypes', 'preNews', e.target.checked)}
                />
                <span>📅 Pre-News Alerts</span>
              </label>
              <label className="preference-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.preferences.alertTypes.postNews}
                  onChange={(e) => updatePreference('alertTypes', 'postNews', e.target.checked)}
                />
                <span>📊 Post-News Analysis</span>
              </label>
              <label className="preference-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.preferences.alertTypes.liveNews}
                  onChange={(e) => updatePreference('alertTypes', 'liveNews', e.target.checked)}
                />
                <span>🔥 Live Breaking News</span>
              </label>
            </div>
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="recent-alerts">
          <h3>📋 Recent Alerts</h3>
          <div className="alerts-list">
            {recentAlerts.map(alert => (
              <div key={alert.id} className="alert-item">
                <div className="alert-icon">
                  {alert.type === 'telegram' ? '📱' : '📧'}
                </div>
                <div className="alert-content">
                  <h4>{alert.title}</h4>
                  <p>{alert.content}</p>
                  <small>{new Date(alert.timestamp).toLocaleString()}</small>
                </div>
                <div className="alert-status">
                  {alert.status === 'sent' ? '✅ Delivered' : '⏳ Scheduled'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Alerts;
```

### 4. Database Schema

#### **User Alert Settings Table**
```sql
CREATE TABLE user_alert_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    telegram_enabled BOOLEAN DEFAULT FALSE,
    telegram_chat_id VARCHAR(255),
    telegram_username VARCHAR(255),
    email_enabled BOOLEAN DEFAULT FALSE,
    email_address VARCHAR(255),
    impact_levels JSONB DEFAULT '{"high": true, "medium": true, "low": false}',
    alert_types JSONB DEFAULT '{"preNews": true, "postNews": true, "liveNews": true, "technicalAnalysis": false}',
    currency_pairs JSONB DEFAULT '["EUR/USD", "USD/JPY", "GBP/USD"]',
    quiet_hours JSONB DEFAULT '{"enabled": false, "start": "22:00", "end": "06:00", "timezone": "UTC"}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Alert History Table**
```sql
CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    currency_pairs JSONB,
    sent_via JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'sent',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    metadata JSONB
);
```

### 5. Implementation Steps

#### **Phase 1: Core Alert Infrastructure**
1. **Create Alert Service**: Implement `AlertService` class for sending notifications
2. **Database Setup**: Create tables for user settings and alert history
3. **Telegram Bot**: Set up bot for user registration and alert delivery
4. **Email Service**: Configure SMTP for email alerts

#### **Phase 2: Alert Triggers**
1. **Live News Alerts**: Integrate with existing WatcherGuru monitoring
2. **Economic Calendar**: Add pre-news alerts for upcoming events
3. **Post-News Analysis**: Trigger alerts after news release with AI analysis
4. **Background Processing**: Set up scheduled tasks for alert checking

#### **Phase 3: User Interface**
1. **Alert Settings Page**: Complete the alerts configuration UI
2. **Telegram Setup Flow**: Implement bot connection process
3. **Alert History**: Display sent alerts with read/unread status
4. **Real-time Updates**: WebSocket connection for live alert status

#### **Phase 4: Advanced Features**
1. **Smart Filtering**: AI-powered alert relevance scoring
2. **Custom Alerts**: User-defined price levels and conditions
3. **Alert Analytics**: Track alert effectiveness and user engagement
4. **Mobile Push**: Add mobile push notifications

### 6. Integration with Existing Systems

#### **Live News Feed Integration**
```python
# In telegram_monitor_user.py, add alert triggering
async def process_new_message(self, message):
    """Process new message and trigger alerts if needed"""
    # Existing news processing logic...
    
    # Check if this should trigger an alert
    if self._should_trigger_alert(news_item):
        await self._trigger_live_news_alert(news_item)
```

#### **AI Analysis Integration**
```python
# In enhanced_ai_analysis.py, add alert triggering
async def analyze_news_with_gpt(news_item):
    """Analyze news and trigger post-news alert if high impact"""
    # Existing analysis logic...
    
    # If high impact, trigger post-news alert
    if news_item['impact'] == 'high':
        await alert_triggers.trigger_post_news_alert(news_item, analysis)
```

### 7. Testing Strategy

#### **Unit Tests**
- Alert service functionality
- Message formatting
- User preference validation
- Database operations

#### **Integration Tests**
- Telegram bot communication
- Email delivery
- Alert triggering logic
- End-to-end alert flow

#### **User Acceptance Tests**
- Alert setup process
- Message delivery timing
- Alert content quality
- User preference management

## Conclusion

This alerts implementation leverages your existing infrastructure while adding powerful notification capabilities. The system is designed to be scalable, reliable, and user-friendly, providing traders with the real-time information they need to make informed decisions.

The key advantages of this approach:
- **Leverages existing AI analysis** for high-quality alert content
- **Uses proven Telegram integration** for reliable delivery
- **Scalable architecture** that can handle thousands of users
- **User-friendly setup** with guided bot connection
- **Comprehensive alert types** covering all trading scenarios

By implementing this system, you'll provide users with the real-time market intelligence they need, significantly increasing the value proposition of FXSentinel.

Essentially:

Live news input (Macro news releases / Trump comments / political statements)
Ai Analyses it.
Message is formatted with title description + analysis 

User sets up alerts preferences etc 
Bot sends alerts through telegram or through email.