# FXSentinel Alert Templates

This document contains all message templates used by the FXSentinel bot, designed for professional use and easy customization.

---

## Economic Calendar Alerts (Pre-Event)

### Template Location
**File:** `backend/services/economic_calendar_alerts.py`  
**Function:** `_create_pre_event_alert_message()`

### Early Alert Template (2h, 1h before)
```
📅 ECONOMIC EVENT ALERT
**{title}** - Event starts in 1-2 hours

**Time:** {time} UTC | **Date:** {date}
**Impact:** {impact.upper()} | **Currency:** {currency}

**Event Details:**
• Type: {event_type}
• Affected Pairs: {pairs_text}

**Market Expectations:**
• Previous: {previous}
• Expected: {expected}

**Action Required:** Prepare for market volatility
**Dashboard:** Check for detailed analysis
```

### Final Reminder Template (10min before)
```
🚨 ECONOMIC EVENT REMINDER
**{title}** - Event starts in 10 minutes

**Time:** {time} UTC | **Date:** {date}
**Impact:** {impact.upper()} | **Currency:** {currency}

**Event Details:**
• Type: {event_type}
• Affected Pairs: {pairs_text}

**Market Expectations:**
• Previous: {previous}
• Expected: {expected}

**Action Required:** Final position preparation
**Dashboard:** Check for detailed analysis
```

### Filled Examples

#### Example 1: US CPI Release (Early Alert)
```
📅 ECONOMIC EVENT ALERT
**US Consumer Price Index** - Event starts in 1-2 hours

**Time:** 13:30 UTC | **Date:** Wed, Aug 20
**Impact:** HIGH | **Currency:** USD

**Event Details:**
• Type: ECONOMIC_RELEASE
• Affected Pairs: EUR/USD, USD/JPY, GBP/USD, USD/CHF, AUD/USD, USD/CAD

**Market Expectations:**
• Previous: 3.2%
• Expected: 3.1%

**Action Required:** Prepare for market volatility
**Dashboard:** Check for detailed analysis
```

#### Example 2: ECB Rate Decision (Final Reminder)
```
🚨 ECONOMIC EVENT REMINDER
**ECB Interest Rate Decision** - Event starts in 10 minutes

**Time:** 12:45 UTC | **Date:** Thu, Aug 21
**Impact:** HIGH | **Currency:** EUR

**Event Details:**
• Type: CENTRAL_BANK
• Affected Pairs: EUR/USD, EUR/GBP, EUR/JPY, EUR/CHF

**Market Expectations:**
• Previous: 4.50%
• Expected: 4.50%

**Action Required:** Final position preparation
**Dashboard:** Check for detailed analysis
```

---

## Live News Alerts (Breaking News)

### Template Location
**File:** `backend/services/news_alert_trigger.py`  
**Function:** `_create_alert_message()`

### Template with AI Analysis
```
🚨 BREAKING FOREX NEWS
**{title}**

**Time:** {formatted_time} | **Source:** {source}
**Pairs:** {pairs_text}

**AI Analysis:**
{analysis_text}

**Read Full Article:** {url}
**Dashboard:** Detailed analysis available
```

### Template without AI Analysis
```
🚨 BREAKING FOREX NEWS
**{title}**

**Time:** {formatted_time} | **Source:** {source}
**Pairs:** {pairs_text}

**Market Impact:** Monitor for price action

**Read Full Article:** {url}
**Dashboard:** Detailed analysis available
```

### Filled Examples

#### Example 1: Fed Rate Decision (With AI Analysis)
```
🚨 BREAKING FOREX NEWS
**Federal Reserve Raises Interest Rates by 25 Basis Points**

**Time:** 14:30 UTC | **Source:** Reuters
**Pairs:** EUR/USD, USD/JPY, GBP/USD

**AI Analysis:**
The Federal Reserve's decision to raise rates by 25bps aligns with market expectations. This dovish hike suggests the Fed is nearing the end of its tightening cycle. Expect USD strength to be limited, with EUR/USD potentially finding support above 1.0800. Monitor Powell's press conference for forward guidance on future rate path.

**Read Full Article:** https://reuters.com/fed-rate-decision
**Dashboard:** Detailed analysis available
```

#### Example 2: NFP Release (Without AI Analysis)
```
🚨 BREAKING FOREX NEWS
**US Non-Farm Payrolls: +187K Jobs Added in August**

**Time:** 13:30 UTC | **Source:** Bloomberg
**Pairs:** EUR/USD, USD/JPY, GBP/USD

**Market Impact:** Monitor for price action

**Read Full Article:** https://bloomberg.com/nfp-release
**Dashboard:** Detailed analysis available
```

---

## Test Alerts

### Template Location
**File:** `backend/app.py`  
**Function:** `send_test_alert()`

### Template
```
🧪 TEST ALERT
**FXSentinel Alert System Test**

**Time:** {timestamp} | **Type:** {alert_type}
**Status:** Connection Working

**System Status:** Your alert system is ready
**Next Steps:** You'll receive real alerts for breaking news and economic events
```

### Filled Example
```
🧪 TEST ALERT
**FXSentinel Alert System Test**

**Time:** 2025-08-20 14:30:00 UTC | **Type:** test
**Status:** Connection Working

**System Status:** Your alert system is ready
**Next Steps:** You'll receive real alerts for breaking news and economic events
```

---

## Telegram Bot Messages

### Template Location
**File:** `backend/working_bot.py`

### Start Command Template
```
Welcome to FXSentinel Alerts
**Your Personal Forex Alert Assistant**

**I'll send you:**
• Breaking news alerts with AI analysis
• Economic calendar reminders
• Market-moving events

**To get started:**
1. Complete setup on the dashboard
2. Configure your preferences
3. Start receiving alerts

**Commands:**
/help - Show all commands
/status - Check your connection status
/test - Send a test alert
```

### Help Command Template
```
FXSentinel Bot Commands
**Available Commands:**

/start - Welcome message
/help - Show this help
/test - Send a test alert
/status - Check your connection status

**Getting Alerts:**
• Configure preferences on dashboard
• Choose your currency pairs
• Set impact levels
• Enable/disable alert types

**Support:** Contact support@fxsentinel.com
```

### Test Command Template
```
Sending Test Alert...
**Test alert sent successfully**

**Connection Status:**
• Telegram: Connected
• Dashboard: Active
• Alerts: Ready

**Status:** You're all set to receive real alerts
```

---

## Template Customization Guide

### Professional Formatting Rules
1. **Keep under 4096 characters** (Telegram limit)
2. **Use consistent formatting patterns**
3. **Bold important information** with `**text**`
4. **Use bullet points** for lists
5. **Include clear call-to-actions**
6. **Minimize emoji usage** for professional appearance
7. **Use clear section headers**

### Message Structure Guidelines
- **Header:** Clear, concise title with key info
- **First Line:** Most critical information (title + timing)
- **Second Line:** Key details (time, source, impact)
- **Content:** Structured information with bullet points
- **Action:** Clear next steps or required actions
- **Footer:** Links to dashboard or full articles

### Notification Optimization
- **First 2-3 lines** contain the most important information
- **Event title and timing** appear immediately
- **Impact level and currency** visible in preview
- **Key details** condensed for mobile viewing
- **Action items** clearly stated

### Customization Tips
- **Adjust urgency levels** based on event importance
- **Modify call-to-actions** based on user journey
- **Add/remove sections** based on information availability
- **Test formatting** in Telegram before deploying
- **Maintain consistent branding** across all templates

### Expandable Features
- **Template variables** for dynamic content
- **Conditional sections** based on data availability
- **Multi-language support** structure
- **Custom branding** options
- **User preference** integration

---

## Template Status

### Completed Templates
- [x] Economic Calendar Early Alerts (2h, 1h)
- [x] Economic Calendar Final Reminders (10min)
- [x] Live News Alerts (with/without AI)
- [x] Test Alerts
- [x] Telegram Bot Messages

### Templates to Review
- [ ] Economic Calendar formatting
- [ ] Live News AI analysis integration
- [ ] Test alert messaging
- [ ] Bot welcome/help messages

### Next Steps
1. Review and customize templates together
2. Update Python code with new templates
3. Test all templates in Telegram
4. Deploy updated templates

---

*Last updated: August 20, 2025*
