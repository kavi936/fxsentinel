# Alert System - Explained Like You're 8 Years Old 🎈

Imagine you have a **magic mailbox** that watches the news and sends you messages when something important happens. That's what our alert system does!

---

## 🏠 The Big Picture

Think of it like this:

```
📰 News Sources (like newspapers)
    ↓
👀 A Robot Watcher (checks every minute)
    ↓
🔍 A Smart Filter (finds important stuff)
    ↓
📋 Your Preferences (what you want to know)
    ↓
📱 Telegram Bot (sends you a message)
```

---

## 🎯 The Main Characters

### 1. **The Background Worker** 🤖
**What it is**: A robot that never sleeps and checks for news every minute

**What it does**:
- Every 60 seconds, it wakes up and says: "Is there any new news?"
- It looks at the news that came in
- It finds the really important stuff (like when the Fed changes interest rates)
- It tells the main app: "Hey! I found something important!"

**Where it lives**: Runs separately on Railway (like a separate computer that just does this job)

---

### 2. **The News Sources** 📰
**What it is**: Where news comes from (like WatcherGuru Telegram channel)

**What it does**:
- Watches Telegram channels for breaking news
- Saves news in a special box (Firebase) so it doesn't get lost
- Keeps news for 15 minutes before checking for new stuff

**Example**: "President Trump says something about the Fed" → This gets saved

---

### 3. **The Smart Filter** 🔍
**What it is**: A smart helper that decides if news is important enough

**What it does**:
- Looks at each news item
- Asks: "Is this about forex? Is it really important?"
- Only picks news about:
  - Central banks (Fed, ECB, BoE)
  - Big economic numbers (inflation, jobs, GDP)
  - Breaking/urgent news
- Ignores boring stuff

**Example**: 
- ✅ "Fed raises interest rates" → IMPORTANT! 
- ❌ "Stock market closed today" → NOT IMPORTANT (not forex)

---

### 4. **Your Preferences** 📋
**What it is**: A list of what YOU want to know about

**What it does**:
- Remembers if you want:
  - Live news alerts (breaking news)
  - Pre-news alerts (upcoming events)
  - Post-news alerts (analysis after news)
- Remembers which currency pairs you care about (EUR/USD, GBP/USD, etc.)
- Remembers if you want high/medium/low impact news

**Where it's stored**: Firebase (like a safe that remembers your settings)

**Example**: If you only care about EUR/USD, you won't get alerts about USD/JPY

---

### 5. **The Deduplication System** 🚫
**What it is**: A memory that remembers what you already got

**What it does**:
- Before sending an alert, it checks: "Did I already send this to this person?"
- If yes → Doesn't send it again (no duplicates!)
- If no → Sends it and remembers it

**Why it's important**: Prevents you from getting the same alert 10 times

**Where it's stored**: Firebase (so it remembers even if the app restarts)

---

### 6. **The Main App** 🏢
**What it is**: The boss that coordinates everything

**What it does**:
- Receives messages from the background worker: "I found important news!"
- Gets a list of all users who want alerts
- For each user:
  - Checks: "Does this user want this type of alert?"
  - Checks: "Did we already send this to them?"
  - Checks: "Is their subscription active?"
  - If all yes → Sends the alert!

**The Flow**:
```
Worker: "I found important news!"
Main App: "Okay, let me check who wants it..."
Main App: "User 1 wants it? Yes! Send it!"
Main App: "User 2 wants it? No, they disabled it. Skip!"
Main App: "User 3 already got it? Yes, skip!"
```

---

### 7. **The Telegram Bot** 📱
**What it is**: The messenger that sends you alerts

**What it does**:
- Takes the alert message
- Formats it nicely (no emojis, professional)
- Sends it to your Telegram chat
- You see it on your phone!

**Example Message**:
```
EUR/GBP softens below 0.8750 as BoE hints at a slower pace for future cuts

Time: 20:46 UTC
Currency Pairs: EUR/GBP
AI Analysis: [analysis text]
```

---

## 🔄 The Complete Journey of an Alert

Let's follow one piece of news from start to finish:

### Step 1: News Arrives 📰
- WatcherGuru Telegram posts: "Fed raises interest rates!"
- News gets saved to Firebase cache

### Step 2: Worker Checks (Every 60 seconds) 🤖
- Background worker wakes up
- Asks main app: "Any new news?"
- Gets the news list

### Step 3: Filtering 🔍
- Worker looks at each news item
- "Fed raises interest rates" → ✅ High impact! ✅ Forex-related!
- Worker says: "This is important! I'll send it!"

### Step 4: Worker Calls Main App 📞
- Worker sends message to main app: `/api/alerts/trigger`
- Says: "I found this important news, please send alerts!"

### Step 5: Main App Gets Users 👥
- Main app asks Firebase: "Who wants alerts?"
- Gets list of all users with alerts enabled

### Step 6: Main App Checks Each User 🔎
For each user:
- ✅ Does user have Telegram enabled? → Check
- ✅ Does user want live news alerts? → Check
- ✅ Is user's subscription active? → Check
- ✅ Did we already send this to them? → Check (deduplication)

### Step 7: Send Alert! 📤
- If all checks pass → Format the message
- Send via Telegram Bot API
- Mark as sent in deduplication (so we don't send again)

### Step 8: You Receive It! 📱
- Alert appears in your Telegram
- You read it and know what's happening in the market!

---

## 🐛 Common Problems (And Why They Happen)

### Problem 1: "I'm not getting any alerts!"
**Why it happens**:
- Your alert types are disabled in Firebase (Live News: False)
- Background worker isn't running
- No new high-impact news
- All news already sent (deduplication)

**How to check**:
1. Check Firebase: `alerts/users/{your_id}/settings/preferences/alertTypes`
2. Check Railway: Is background worker running?
3. Check Firebase: `news_cache/current` - Is there recent news?

---

### Problem 2: "I'm getting the same alert twice!"
**Why it happens**:
- Deduplication didn't work (maybe Firebase error)
- Worker and main app both sent it
- Timing issue (sent before deduplication marked it)

**How to fix**:
- Check deduplication in Firebase: `alert_deduplication/`
- Make sure only one worker is running

---

### Problem 3: "I'm getting alerts I don't want!"
**Why it happens**:
- Your preferences aren't set correctly
- Filter isn't strict enough
- Currency pair matching is too broad

**How to fix**:
- Update your preferences in Firebase
- Check which currency pairs you have enabled

---

## 🎯 The Key Things to Remember

1. **Two Separate Services**:
   - Background Worker (checks for news) - runs separately
   - Main App (sends alerts) - runs separately
   - They talk to each other via API calls

2. **Everything is Stored in Firebase**:
   - News cache
   - User settings
   - Deduplication state
   - This means it survives restarts!

3. **Multiple Checks Before Sending**:
   - Is news important? (Filter)
   - Does user want it? (Preferences)
   - Did we already send it? (Deduplication)
   - Is subscription active? (Subscription check)

4. **The Worker Runs Every 60 Seconds**:
   - But news is only fetched every 5 minutes
   - So worker might check and find no new news (that's okay!)

---

## 🔧 How to Debug (Simple Version)

If alerts aren't working, check in this order:

1. **Is the worker running?**
   - Check Railway dashboard
   - Look for "Background Worker" service
   - Check if it's green (running)

2. **Is there news?**
   - Check Firebase: `news_cache/current`
   - Is there recent news? (less than 1 hour old)

3. **Are your settings correct?**
   - Check Firebase: `alerts/users/{your_id}/settings`
   - Is `liveNews: true`?
   - Is Telegram enabled?

4. **Is deduplication blocking?**
   - Check Firebase: `alert_deduplication/`
   - See if your news item is already marked as sent

5. **Check the logs**
   - Railway logs for background worker
   - Look for errors or exceptions

---

## 💡 Simple Analogy

Think of it like a **newspaper delivery system**:

- **News Sources** = The newspaper printing press
- **Background Worker** = The delivery person who checks for new papers every minute
- **Smart Filter** = The editor who picks only important stories
- **Your Preferences** = Your subscription (which sections you want)
- **Deduplication** = The delivery person's memory (won't deliver the same paper twice)
- **Main App** = The delivery coordinator (makes sure right papers go to right people)
- **Telegram Bot** = The mailbox where you receive your paper

---

## 🎓 Summary

The alert system is like a **smart assistant** that:
1. Watches the news 24/7
2. Finds the important stuff
3. Remembers what you want
4. Remembers what you already got
5. Sends you messages when something important happens

It's made of **two main parts**:
- **Background Worker**: The watcher (checks every minute)
- **Main App**: The sender (sends alerts to users)

Everything is stored in **Firebase** so it remembers even if the app restarts.

The system checks **many things** before sending:
- Is it important?
- Do you want it?
- Did you already get it?
- Is your subscription active?

If all checks pass → You get an alert! 📱

---

## ❓ Questions?

If something doesn't make sense, think about it like this:
- **Worker** = The person watching
- **Main App** = The person sending
- **Firebase** = The memory/storage
- **Filter** = The decision maker
- **Deduplication** = The memory of what was sent

They all work together to make sure you get the right alerts at the right time! 🎉

