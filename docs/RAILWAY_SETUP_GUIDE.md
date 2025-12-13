# FXSentinel Railway Deployment Setup Guide

## 🎯 **Problem Solved**

Your alert bot stopped working because the `background_alert_worker` on Railway was trying to connect to `localhost:5001`, which doesn't exist in production. This guide fixes the service connectivity issues.

## 🚀 **Solution Overview**

We need to deploy **two separate services** on Railway:
1. **Main Flask App**: Handles API requests and user management
2. **Background Worker**: Processes alerts and sends Telegram messages

Both services will communicate using Railway's internal networking.

## 📋 **Step-by-Step Setup**

### **Step 1: Prepare Your Railway Account**

1. **Install Railway CLI** (if not already installed):
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Verify login**:
   ```bash
   railway whoami
   ```

### **Step 2: Deploy Main Flask App**

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Initialize Railway project** (if not already done):
   ```bash
   railway init --name "fxsentinel-main-app"
   ```

3. **Deploy the main app**:
   ```bash
   railway up
   ```

4. **Get your app URL**:
   ```bash
   railway domain
   ```
   
   **Save this URL** - you'll need it for the next step!

### **Step 3: Deploy Background Worker**

1. **Stay in backend directory** and create a new Railway project for the worker:
   ```bash
   railway init --name "fxsentinel-background-worker"
   ```

2. **Deploy the worker**:
   ```bash
   railway up
   ```

3. **Get worker URL** (for monitoring):
   ```bash
   railway domain
   ```

### **Step 4: Configure Environment Variables**

#### **For Main Flask App:**
Go to your main app in Railway dashboard and set:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
STRIPE_SECRET_KEY=your_stripe_secret_key_here

# Firebase (if using)
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour key here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_email

# Environment
FLASK_ENV=production
FLASK_DEBUG=false
```

#### **For Background Worker:**
Go to your background worker in Railway dashboard and set:

```bash
# CRITICAL: This must point to your main app URL
API_BASE_URL=https://your-main-app-url.up.railway.app

# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here

# Firebase (same as main app)
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour key here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_email

# Environment
FLASK_ENV=production
FLASK_DEBUG=false
```

### **Step 5: Test the Setup**

1. **Test Main App**:
   ```bash
   curl https://your-main-app-url.up.railway.app/api/health
   ```

2. **Test Background Worker**:
   - Check Railway logs for the worker service
   - Look for "Background worker started successfully" message

3. **Test Alert System**:
   ```bash
   curl -X POST https://your-main-app-url.up.railway.app/api/trigger-alerts \
     -H "Content-Type: application/json" \
     -d '{"user_id": "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2", "chat_id": "8008493413"}'
   ```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. "Module not found" errors**
- Make sure you're deploying from the `backend` directory
- All required Python packages should be in `requirements.txt`

#### **2. Background worker not starting**
- Check Railway logs for error messages
- Verify `API_BASE_URL` is set correctly
- Ensure all environment variables are set

#### **3. Services can't communicate**
- Verify both services are deployed to the same Railway account
- Check that `API_BASE_URL` points to the correct main app URL
- Ensure both services are running

#### **4. Telegram bot not responding**
- Verify `TELEGRAM_BOT_TOKEN` is set correctly
- Check if bot is active and not blocked
- Test bot manually with a simple message

### **Debug Commands**

```bash
# Check main app status
curl https://your-main-app-url.up.railway.app/api/health

# Check background worker logs
railway logs --service fxsentinel-background-worker

# Test API connectivity from worker
curl https://your-main-app-url.up.railway.app/api/news

# Test alert trigger
curl -X POST https://your-main-app-url.up.railway.app/api/trigger-alerts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "chat_id": "test"}'
```

## 📊 **Monitoring Your Services**

### **Railway Dashboard**
- **Main App**: Monitor API requests, response times, errors
- **Background Worker**: Check logs for alert processing activity
- **Both Services**: Monitor resource usage, restarts, health checks

### **Key Metrics to Watch**
1. **Main App**: Response times, error rates, API calls
2. **Background Worker**: Alert processing frequency, success rates
3. **Telegram**: Message delivery success, bot response times

### **Log Analysis**
Look for these patterns in your worker logs:
- ✅ "Background worker started successfully"
- ✅ "Alert check completed"
- ✅ "Alert sent successfully to user"
- ❌ "Failed to get news" (connectivity issues)
- ❌ "Module not found" (deployment issues)

## 🎉 **Success Indicators**

Your setup is working correctly when you see:

1. **Main app responds** to health checks
2. **Background worker starts** without errors
3. **Worker logs show** regular alert checking activity
4. **Telegram alerts** are received by users
5. **No localhost errors** in logs

## 🚀 **Next Steps After Setup**

1. **Monitor logs** for the first few hours
2. **Test with real alerts** to verify functionality
3. **Set up alerts** for service downtime
4. **Scale services** if needed (Railway auto-scales)
5. **Set up monitoring** for production reliability

## 🔗 **Useful Links**

- **Railway Dashboard**: https://railway.app/dashboard
- **Railway CLI Docs**: https://docs.railway.app/develop/cli
- **Railway Environment Variables**: https://docs.railway.app/develop/variables
- **Railway Logs**: https://docs.railway.app/develop/logs

Your multi-user alert system will now work reliably in production! 🎯
