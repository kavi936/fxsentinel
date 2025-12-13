# FXSentinel Alerts MVP - 2-3 Day Implementation Plan

## 🎯 **User Workflow Overview**

### **Complete User Journey:**
1. **User visits Alerts tab** → Sees overview with setup status
2. **Clicks "Connect Telegram Bot"** → Gets unique bot link and instructions
3. **Follows bot setup in Telegram** → Sends /start, gets confirmation
4. **Returns to app and verifies** → Connection confirmed, alerts enabled
5. **Configures preferences** → Sets impact levels, alert types, currency pairs
6. **Receives first alert** → Gets notified about breaking news or economic events
7. **Views alert history** → Sees all sent alerts with delivery status

---

## 📅 **Day 1: Core Backend Infrastructure**

### **Priority 1: Alert Service & Database (4-5 hours)**

#### **Step 1.1: Create Alert Service**
```bash
# Create the core alert service
touch backend/services/alert_service.py
```

**Implementation:**
- Telegram bot integration using python-telegram-bot
- Email service using SMTP
- User preference management
- Alert history tracking

#### **Step 1.2: Database Schema**
```sql
-- User alert settings
CREATE TABLE user_alert_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    telegram_enabled BOOLEAN DEFAULT FALSE,
    telegram_chat_id VARCHAR(255),
    telegram_username VARCHAR(255),
    email_enabled BOOLEAN DEFAULT FALSE,
    email_address VARCHAR(255),
    impact_levels JSONB DEFAULT '{"high": true, "medium": true, "low": false}',
    alert_types JSONB DEFAULT '{"preNews": true, "postNews": true, "liveNews": true}',
    currency_pairs JSONB DEFAULT '["EUR/USD", "USD/JPY", "GBP/USD"]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alert history
CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    sent_via JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'sent',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Step 1.3: API Endpoints**
```python
# Add to backend/app.py
@app.route('/api/alerts/setup-telegram', methods=['POST'])
def setup_telegram_bot():
    """Generate unique bot link for user"""
    
@app.route('/api/alerts/verify-telegram', methods=['POST'])
def verify_telegram_connection():
    """Verify user completed bot setup"""
    
@app.route('/api/alerts/settings', methods=['GET', 'PUT'])
def manage_alert_settings():
    """Get/update user alert preferences"""
    
@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """Get user's alert history"""
```

### **Priority 2: Telegram Bot Setup (2-3 hours)**

#### **Step 2.1: Create Telegram Bot**
```bash
# Create bot setup service
touch backend/services/telegram_bot_setup.py
```

**Implementation:**
- Bot token management
- User registration flow
- Chat ID storage
- Connection verification

#### **Step 2.2: Bot Commands**
```python
# Bot command handlers
/start - Welcome message and setup instructions
/connect - Link user account to alerts
/status - Show current alert settings
/help - Show available commands
```

---

## 📅 **Day 2: Alert Triggering & Integration**

### **Priority 1: Alert Trigger System (3-4 hours)**

#### **Step 1.1: Create Alert Triggers**
```bash
# Create alert triggering service
touch backend/services/alert_triggers.py
```

**Implementation:**
- Live news alert detection
- Economic calendar monitoring
- Post-news analysis triggering
- Background processing

#### **Step 1.2: Integrate with Existing Services**
```python
# Modify telegram_monitor_user.py
async def process_new_message(self, message):
    # Existing news processing...
    
    # Add alert triggering
    if self._should_trigger_alert(news_item):
        await self._trigger_live_news_alert(news_item)

# Modify enhanced_ai_analysis.py
async def analyze_news_with_gpt(news_item):
    # Existing analysis...
    
    # Add post-news alert
    if news_item['impact'] == 'high':
        await alert_triggers.trigger_post_news_alert(news_item, analysis)
```

### **Priority 2: Alert Content Templates (2-3 hours)**

#### **Step 2.1: Message Templates**
```python
# Alert message templates
LIVE_NEWS_TEMPLATE = """
🔥 BREAKING: {title}

📊 Impact: {impact_level}
💱 Pairs: {currency_pairs}

🤖 AI Analysis:
{analysis}

⏰ {timestamp}
"""

PRE_NEWS_TEMPLATE = """
🚨 UPCOMING: {event_title}

⏰ Time: {event_time}
📈 Expected: {expected_value}
🎯 Key Levels: {key_levels}

💡 Market Impact:
{impact_analysis}
"""
```

#### **Step 2.2: Content Formatting**
- HTML formatting for Telegram
- Plain text for email
- Emoji usage for visual appeal
- Currency pair highlighting

---

## 📅 **Day 3: Frontend Integration & Testing**

### **Priority 1: Connect Frontend to Backend (3-4 hours)**

#### **Step 1.1: API Integration**
```javascript
// Add to src/components/Alerts.jsx
const setupTelegramBot = async () => {
  const response = await fetch('/api/alerts/setup-telegram', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId: currentUser.id })
  });
  // Handle response...
};

const verifyTelegramConnection = async () => {
  const response = await fetch('/api/alerts/verify-telegram', {
    method: 'POST'
  });
  // Handle verification...
};

const updateAlertSettings = async (settings) => {
  const response = await fetch('/api/alerts/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  });
  // Handle update...
};
```

#### **Step 1.2: Real-time Updates**
```javascript
// Add WebSocket connection for live updates
const [alertHistory, setAlertHistory] = useState([]);

useEffect(() => {
  const ws = new WebSocket('ws://localhost:5000/ws/alerts');
  
  ws.onmessage = (event) => {
    const newAlert = JSON.parse(event.data);
    setAlertHistory(prev => [newAlert, ...prev]);
  };
  
  return () => ws.close();
}, []);
```

### **Priority 2: Testing & Debugging (2-3 hours)**

#### **Step 2.1: End-to-End Testing**
```bash
# Test script
touch test_alerts_flow.py
```

**Test Scenarios:**
1. User sets up Telegram bot
2. User configures alert preferences
3. System sends test alert
4. User receives alert on Telegram
5. Alert appears in history

#### **Step 2.2: Error Handling**
- Network connection issues
- Bot setup failures
- Invalid user preferences
- Alert delivery failures

---

## 🚀 **MVP Success Criteria**

### **Minimum Viable Features:**
✅ **Telegram Bot Setup**: User can connect their Telegram account
✅ **Alert Preferences**: User can configure what alerts they want
✅ **Live News Alerts**: System sends alerts for breaking news
✅ **Alert History**: User can see all sent alerts
✅ **Basic Error Handling**: Graceful failure handling

### **Nice-to-Have (Post-MVP):**
- Email alerts
- Economic calendar alerts
- Advanced filtering
- Alert analytics
- Mobile push notifications

---

## 🔧 **Technical Requirements**

### **Environment Variables:**
```bash
# Add to .env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_BOT_USERNAME=@FXSentinelBot
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=alerts@fxsentinel.com
EMAIL_PASSWORD=your_email_password
```

### **Dependencies:**
```python
# Add to requirements.txt
python-telegram-bot==20.7
asyncio-mqtt==0.16.1
```

### **File Structure:**
```
backend/
├── services/
│   ├── alert_service.py          # Core alert functionality
│   ├── alert_triggers.py         # Alert detection logic
│   ├── telegram_bot_setup.py     # Bot setup and management
│   └── alert_templates.py        # Message templates
├── app.py                        # API endpoints
└── requirements.txt              # Dependencies

src/
├── components/
│   ├── Alerts.jsx               # Main alerts component
│   └── Alerts.css               # Styling
└── utils/
    └── alertUtils.js            # Frontend utilities
```

---

## 📋 **Daily Checklist**

### **Day 1 Checklist:**
- [ ] Alert service created and tested
- [ ] Database schema implemented
- [ ] API endpoints working
- [ ] Telegram bot created and configured
- [ ] Basic bot commands working

### **Day 2 Checklist:**
- [ ] Alert triggers implemented
- [ ] Integration with existing services
- [ ] Message templates created
- [ ] Background processing working
- [ ] Test alerts being sent

### **Day 3 Checklist:**
- [ ] Frontend connected to backend
- [ ] Real-time updates working
- [ ] End-to-end testing complete
- [ ] Error handling implemented
- [ ] MVP ready for user testing

---

## 🎯 **Success Metrics**

### **Technical Metrics:**
- Alert delivery success rate > 95%
- Bot setup completion rate > 80%
- API response time < 500ms
- Zero critical errors in production

### **User Metrics:**
- Users who complete bot setup
- Alert engagement rate
- User retention after first alert
- Support ticket volume

This plan focuses on the essential components needed for a working alerts MVP while leveraging your existing infrastructure. The 2-3 day timeline is aggressive but achievable with focused development.
