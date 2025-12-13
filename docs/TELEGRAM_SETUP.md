# Telegram Integration Setup Guide

## Overview
This guide will help you set up Telegram integration to monitor WatcherGuru channel for forex news and integrate it into your FXSentinel news feed.

## Prerequisites
- Telegram account
- Access to WatcherGuru channel
- Python environment with the required dependencies

## Step 1: Create Telegram Bot

### 1.1 Create Bot via BotFather
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Save the **Bot Token** (you'll need this later)

### 1.2 Get API Credentials
1. Go to https://my.telegram.org/
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Save the **API ID** and **API Hash**

## Step 2: Configure Environment Variables

Add these environment variables to your `.env` file in the backend directory:

```env
# Telegram API Credentials
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Step 3: Install Dependencies

The required packages have been added to `requirements.txt`. Install them:

```bash
cd backend
pip install -r requirements.txt
```

## Step 4: Configure Channel Access

### 4.1 Public Channel
If WatcherGuru is a public channel, no additional setup is needed.

### 4.2 Private Channel
If WatcherGuru is a private channel:
1. Add your bot to the channel as an admin
2. Or use a user account instead of bot token (requires additional setup)

## Step 5: Test the Integration

### 5.1 Start the Backend
```bash
cd backend
python app.py
```

### 5.2 Test the API
Visit: `http://localhost:8000/api/news`

You should see Telegram news items in the response.

## Step 6: Customize Channel Monitoring

### 6.1 Add More Channels
Edit `backend/services/telegram_monitor.py` and add more channels to the `target_channels` list:

```python
self.target_channels = [
    'WatcherGuru',
    'WatcherGuru_News',
    '@WatcherGuru',
    'YourOtherChannel',  # Add more channels here
]
```

### 6.2 Customize Keywords
Modify the forex keywords in the same file to match your needs:

```python
self.forex_keywords = [
    'forex', 'currency', 'dollar', 'euro', 'yen', 'pound',
    # Add your custom keywords here
]
```

## Step 7: Monitor and Debug

### 7.1 Check Logs
The integration logs to the console. Look for:
- "Telegram client initialized successfully"
- "Fetched X forex-related messages from WatcherGuru"

### 7.2 Common Issues

#### Issue: "Telegram API credentials not configured"
**Solution**: Check your `.env` file and ensure all credentials are set correctly.

#### Issue: "Could not find channel: WatcherGuru"
**Solution**: 
1. Verify the channel name is correct
2. Ensure the channel is public or your bot has access
3. Try different channel name formats (with/without @)

#### Issue: "Failed to initialize Telegram client"
**Solution**:
1. Check your API credentials
2. Ensure internet connectivity
3. Verify the bot token is valid

## Step 8: Production Deployment

### 8.1 Railway Deployment
When deploying to Railway, add the environment variables in the Railway dashboard:
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_BOT_TOKEN`

### 8.2 Security Notes
- Never commit your `.env` file to version control
- Use environment variables in production
- Regularly rotate your API credentials

## Features

### What the Integration Does:
1. **Monitors WatcherGuru channel** for new messages
2. **Filters for forex-related content** using keyword matching
3. **Determines impact levels** (High/Medium/Low) based on content
4. **Extracts currency pairs** mentioned in messages
5. **Converts to news format** compatible with your existing feed
6. **Removes duplicates** and sorts by date
7. **Integrates seamlessly** with RSS feeds and ForexFactory data

### Data Structure:
Each Telegram message is converted to:
```json
{
  "id": 123456789,
  "title": "Message Title",
  "summary": "Message content...",
  "source": "Telegram - WatcherGuru",
  "published_at": "2024-01-15T10:30:00Z",
  "impact": "high",
  "currency_pairs": ["EUR/USD", "USD/JPY"],
  "type": "TELEGRAM",
  "status": "PUBLISHED"
}
```

## Support

If you encounter issues:
1. Check the backend logs for error messages
2. Verify your Telegram API credentials
3. Test with a simple public channel first
4. Ensure all dependencies are installed correctly

## Next Steps

Once the integration is working:
1. Add more forex-related Telegram channels
2. Customize the keyword filtering
3. Implement real-time notifications
4. Add message analytics and trending topics
