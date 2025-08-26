# Telegram Session Setup Guide for Railway

## Problem
The Telegram integration requires a user session file that needs to be authenticated with a verification code from your phone. Railway (production server) cannot handle interactive prompts, so we need to generate the session file locally and upload it.

## Solution
Generate the Telegram session file locally, then upload it to Railway.

## Step-by-Step Setup

### 1. Local Setup (Run this on your computer)

First, make sure you have your Telegram credentials in your local `.env` file:

```bash
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone_number
```

### 2. Generate Session File

Run the session generator script:

```bash
python3 generate_telegram_session.py
```

This will:
- Connect to Telegram using your credentials
- Prompt you for the verification code (check your phone)
- Generate a `fxsentinel_user_session.session` file
- Test access to WatcherGuru channel

### 3. Upload to Railway

Once the session file is generated, you need to upload it to Railway:

**Option A: Using Railway CLI**
```bash
# Install Railway CLI if you haven't
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Upload the session file
railway up fxsentinel_user_session.session
```

**Option B: Using Railway Dashboard**
1. Go to your Railway project dashboard
2. Navigate to the "Files" tab
3. Upload `fxsentinel_user_session.session` to the backend directory

### 4. Deploy and Test

After uploading the session file:

```bash
# Push your code changes
git add .
git commit -m "Add Telegram session file"
git push

# Wait for Railway to deploy, then test
python3 trigger_deployment_notification.py trigger "Telegram session uploaded - testing WatcherGuru integration"
```

### 5. Verify Integration

Check if Telegram news is appearing:

```bash
curl -s "https://fxsentinel-production.up.railway.app/api/news" | python3 -c "import sys, json; data=json.load(sys.stdin); telegram_count = sum(1 for item in data.get('news', []) if 'telegram' in str(item.get('source', '')).lower() or 'watcher' in str(item.get('source', '')).lower()); print(f'Telegram articles: {telegram_count}')"
```

## Troubleshooting

### Session File Issues
- **"database is locked"**: Clear the session lock: `rm -f /tmp/telegram_session_fxsentinel_user_session.lock`
- **"Client not connected"**: The session file might be corrupted, regenerate it
- **"Phone migrated"**: This is normal, the client will reconnect automatically

### Railway Issues
- **Session file not found**: Make sure the file is uploaded to the correct directory
- **Permission denied**: Check file permissions on Railway
- **Session expired**: Regenerate the session file

### WatcherGuru Access
- **"Could not access WatcherGuru"**: The channel might be private or require subscription
- **No messages found**: The channel might not have recent public messages

## Expected Results

After successful setup:
- ✅ Telegram appears in the sources list
- ✅ WatcherGuru alerts appear in the live news feed
- ✅ Force refresh includes Telegram articles
- ✅ Deployment notification works properly

## Security Notes

- The session file contains sensitive authentication data
- Keep it secure and don't share it publicly
- Railway encrypts files at rest, but be careful with logs
- Consider regenerating the session file periodically

## Alternative Approach

If the session file approach doesn't work, you can also:
1. Use a Telegram bot instead of user account (limited functionality)
2. Use a different news source for WatcherGuru alerts
3. Implement web scraping for public Telegram channels
