# FXSentinel Weekend Preparation Checklist
## Prepare Your Alert System for the Week Ahead

**Date**: October 18, 2025 (Weekend)  
**Prep Time**: 15-20 minutes  
**Goal**: Have alert system ready when markets open Monday

---

## ✅ **CHECKLIST FOR NEXT WEEK**

### **□ TASK 1: Update Economic Calendar (10 minutes)**

**Why**: Your calendar has expired events. Need fresh events for Oct 21-25.

**Steps**:
1. Go to: https://www.forexfactory.com/calendar
2. Set filters:
   - **Impact**: High (orange icon)
   - **Dates**: Oct 21-25, 2025
   - **Currencies**: USD, EUR, GBP, JPY, AUD, CAD
3. Copy 5-10 high-impact events
4. Edit: `backend/services/hybrid_economic_calendar.py`
5. Replace lines 84-636 with new events
6. Save file

**Format Example**:
```python
{
    'title': 'US GDP q/q',
    'date': 'Fri, Oct 25',
    'time': '12:30 UTC',
    'currency': 'USD',
    'impact': 'high',
    'actual': 'TBD',
    'forecast': '2.3%',
    'previous': '2.1%'
},
```

---

### **□ TASK 2: Commit & Deploy Calendar (2 minutes)**

**Commands**:
```bash
cd /Users/kavi/Desktop/fxsentinel
git add backend/services/hybrid_economic_calendar.py
git commit -m "Update economic calendar for Oct 21-25, 2025"
git push origin main
```

**What Happens**:
- GitHub receives update
- Railway auto-deploys main app (2-3 minutes)
- Railway auto-deploys background worker (2-3 minutes)

---

### **□ TASK 3: Verify Railway Services (3 minutes)**

**Go to**: https://railway.app

**Check Main App**:
- Status: Should show "Active" (green)
- Deployment: Latest commit should be deployed
- Logs: Should show "Flask app running"

**Check Background Worker**:
- Status: Should show "Active" (green)
- Deployment: Latest commit should be deployed
- Logs: Should show:
  - "✅ Production Alert Worker initialized"
  - "📊 Worker main loop started"
  - "📰 Checking for news alerts..."
  - "📅 Checking for economic calendar alerts..."

**If Not Active**:
- Click "Redeploy" button
- Wait 2-3 minutes
- Check logs again

---

### **□ TASK 4: Test Alert System (5 minutes)**

**Test 1: Telegram Bot Status**

Open Telegram, send to your bot:
```
/status
```

**Expected Response**:
```
📊 FXSentinel Alert Status

✅ Status: Connected

💬 Chat ID: 8008493413
📱 Telegram: @K7IV_1

Alert Settings:
• Live News: ✅ Enabled
• Economic Calendar: ✅ Enabled
• High Impact: ✅ Enabled
```

If still shows "Not Connected", wait 5 more minutes (Railway deployment delay).

---

**Test 2: Send Manual Test Alert**

Run locally:
```bash
cd /Users/kavi/Desktop/fxsentinel
python3 send_test_alert_now.py
```

Check Telegram - should receive test message immediately.

---

### **□ TASK 5: Verify Calendar API (2 minutes)**

**Check Calendar Endpoint**:

Run:
```bash
curl http://localhost:5001/api/economic-calendar | python3 -m json.tool | head -30
```

OR visit: https://your-railway-app.up.railway.app/api/economic-calendar

**Expected**:
```json
{
  "events": [
    {
      "title": "US GDP q/q",
      "date": "Fri, Oct 25",
      "time": "12:30 UTC",
      "currency": "USD",
      "impact": "high"
    }
  ],
  "source": "hybrid_calendar"
}
```

If `events: []`, calendar update didn't work - check file format.

---

## 📊 **WHAT HAPPENS MONDAY MORNING**

### **When Markets Open (Monday 00:00 UTC / Sunday 8pm ET)**:

**Background Worker Starts**:
- ✅ Checks news feeds every 2 minutes
- ✅ Checks economic calendar every 5 minutes
- ✅ Finds upcoming high-impact events
- ✅ Calculates alert times (2h, 1h, 10min before)

**Live News Alerts**:
```
🚨 BREAKING FOREX NEWS

Title: Fed Official Speaks on Inflation
Time: 14:30 UTC
Source: Bloomberg
Currency Pairs: EUR/USD, USD/JPY

Summary: Federal Reserve Governor discusses 
inflation outlook and potential rate changes.

Market Impact: Monitor for price action
```

**Economic Calendar Alerts**:
```
📅 UPCOMING ECONOMIC EVENT

US GDP q/q - Event starts in 2 hours

📊 Event Details:
• Time: 12:30 UTC
• Currency: USD
• Expected: 2.3%
• Previous: 2.1%

💱 Affected Pairs: EUR/USD, GBP/USD

🎯 Prepare for Market Volatility!
```

---

## 🔍 **TROUBLESHOOTING**

### **Problem: No alerts received Monday**

**Check 1**: Is worker running?
- Go to Railway → Background Worker
- Logs should show activity every 2-5 minutes

**Check 2**: Are there high-impact events?
- Check: https://www.forexfactory.com/calendar
- Filter: High impact only
- If none scheduled, alerts won't be sent (this is normal)

**Check 3**: Is it market hours?
- Best alert times: 
  - London session: 07:00-16:00 UTC
  - NY session: 12:00-21:00 UTC
  - Weekend: No alerts (markets closed)

**Check 4**: Check deduplication
- Alerts are sent once per event per timing window
- If you already received "2h before" alert, you won't get it again
- Next alert will be "1h before"

---

## 🎯 **SUCCESS CRITERIA**

By end of this prep, you should have:

- ✅ Economic calendar updated with next week's events
- ✅ Changes committed and pushed to GitHub
- ✅ Both Railway services deployed and "Active"
- ✅ Telegram bot responding with "Connected" status
- ✅ Test alert received successfully
- ✅ Calendar API returning new events

**If all ✅ checked** → System ready for Monday! 🎉

---

## 📅 **MAINTENANCE SCHEDULE**

**Weekly** (Every Sunday evening):
- Update economic calendar with next week's events (10 min)
- Verify Railway services are active (2 min)
- Test with /status command (1 min)

**Monthly**:
- Review alert history in Firebase
- Check for any missed alerts
- Optimize currency pair preferences if needed

**As Needed**:
- Update calendar if major surprise events announced
- Check Railway logs if alerts seem delayed
- Update user preferences in dashboard

---

## 💡 **PRO TIPS**

1. **Best Events to Include**:
   - US Non-Farm Payrolls (NFP) - 1st Friday of month
   - US CPI / Core CPI - Mid-month
   - Federal Reserve FOMC Decision - 8 times per year
   - ECB Interest Rate Decision - Monthly
   - Central bank speeches (Powell, Lagarde, etc.)

2. **Alert Timing Strategy**:
   - **2h before**: Good for position planning
   - **1h before**: Time to place orders
   - **10min before**: Final check before volatility

3. **Currency Pairs to Watch**:
   - EUR/USD: Most liquid, responds to Fed/ECB
   - GBP/USD: Brexit news, BOE decisions
   - USD/JPY: Risk sentiment, BOJ policy
   - AUD/USD: Commodity prices, RBA

4. **Market Hours**:
   - **Sydney**: 22:00-07:00 UTC (slow)
   - **Tokyo**: 00:00-09:00 UTC (moderate)
   - **London**: 07:00-16:00 UTC (active)
   - **New York**: 12:00-21:00 UTC (most active)
   - **Overlap (London+NY)**: 12:00-16:00 UTC (best)

---

## ✅ **CHECKLIST SUMMARY**

```
□ Update economic calendar with Oct 21-25 events
□ Commit and push changes to GitHub
□ Verify Railway main app deployed
□ Verify Railway background worker deployed
□ Test /status command (shows Connected)
□ Send manual test alert (receives in Telegram)
□ Verify calendar API returns new events
```

**All done?** → Your alert system is ready for the week! 🚀

