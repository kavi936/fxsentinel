# 🚀 FXSentinel Railway Deployment Fix Guide

## **Problem Analysis**

Your Railway deployment was failing because of **deployment architecture confusion**:

1. **Main App**: Railway was trying to run `gunicorn main:app` but `main.py` was configured as a background worker
2. **Background Worker**: Was trying to run the wrong entry point
3. **Mixed Responsibilities**: The main Flask app and background worker were mixed up

## **Solution: Proper Service Separation**

### **Architecture Overview**
```
┌─────────────────────────────────────┐
│           Frontend                  │
│         (Vercel)                    │
│  - React Web Application            │
│  - User Interface                   │
│  - Static Files                     │
└─────────────────────────────────────┘
                    │
                    │ API calls
                    ▼
┌─────────────────────────────────────┐
│           Main App                  │
│  (fxsentinel-production.up.railway.app) │
│  - Flask Web Application            │
│  - API Endpoints                    │
│  - Root Directory: backend/         │
└─────────────────────────────────────┘
                    │
                    │ Internal API calls
                    ▼
┌─────────────────────────────────────┐
│        Background Worker            │
│  (fxsentinel-background-worker)     │
│  - Alert Processing                 │
│  - News Monitoring                  │
│  - Economic Calendar Alerts         │
│  - Telegram Bot Operations          │
│  - Root Directory: backend/         │
└─────────────────────────────────────┘
```

## **Files Created/Modified**

### **Main App Configuration:**
- ✅ `main.py` - Now properly imports and runs the Flask web app
- ✅ `Procfile` - Gunicorn configuration for main app
- ✅ `railway.json` - Railway config for main app

### **Background Worker Configuration:**
- ✅ `worker.py` - Entry point for background worker
- ✅ `Procfile.worker` - Configuration for background worker
- ✅ `railway.worker.json` - Railway config for background worker

## **Deployment Instructions**

### **Step 1: Deploy Main App (Web Application)**

1. **In Railway Dashboard:**
   - Go to your main app project: `fxsentinel-production`
   - Go to **Settings** → **Deploy**
   - Set **Root Directory** to: `backend` (backend directory)
   - Set **Start Command** to: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 2`

2. **Environment Variables for Main App:**
   ```
   FLASK_ENV=production
   FLASK_DEBUG=false
   OPENAI_API_KEY=your_openai_key
   STRIPE_SECRET_KEY=your_stripe_key
   STRIPE_WEBHOOK_SECRET=your_webhook_secret
   FIREBASE_PROJECT_ID=your_firebase_project
   # ... other API keys
   ```

3. **Deploy:**
   - Click **Deploy** or push to main branch
   - Wait for build to complete
   - Test: `https://fxsentinel-production.up.railway.app/api/health`

### **Step 2: Deploy Background Worker**

1. **In Railway Dashboard:**
   - Go to your background worker project: `fxsentinel-background-worker`
   - Go to **Settings** → **Deploy**
   - Set **Root Directory** to: `backend` (backend directory)
   - Set **Start Command** to: `python railway_worker.py`

2. **Environment Variables for Background Worker:**
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   API_BASE_URL=https://fxsentinel-production.up.railway.app
   OPENAI_API_KEY=your_openai_key
   FLASK_ENV=production
   ```

3. **Deploy:**
   - Click **Deploy** or push to main branch
   - Wait for build to complete
   - Check logs for: "✅ Background worker started successfully"

## **Verification Steps**

### **Main App Health Check:**
```bash
curl https://fxsentinel-production.up.railway.app/api/health
# Expected: {"status": "healthy", "service": "web-app"}
```

### **Background Worker Health Check:**
```bash
# Check Railway logs for:
# "🚀 Starting FXSentinel Background Worker on Railway"
# "✅ Background worker started successfully"
# "🔄 Worker is now monitoring for alerts..."
```

### **Integration Test:**
1. Visit main app: `https://fxsentinel-production.up.railway.app`
2. Check if frontend loads properly
3. Test API endpoints
4. Verify background worker is processing alerts

## **Troubleshooting**

### **Main App Issues:**

**Problem**: `gunicorn: command not found`
**Solution**: Ensure `gunicorn>=21.0.0` is in `requirements.txt`

**Problem**: `ModuleNotFoundError: No module named 'app'`
**Solution**: Check that `backend/app.py` exists and is properly configured

**Problem**: App crashes on startup
**Solution**: Check Railway logs for specific error messages

### **Background Worker Issues:**

**Problem**: `ModuleNotFoundError: No module named 'railway_worker'`
**Solution**: Ensure `backend/railway_worker.py` exists

**Problem**: Worker starts but no alerts are sent
**Solution**: Check `TELEGRAM_BOT_TOKEN` and `API_BASE_URL` environment variables

**Problem**: Worker crashes repeatedly
**Solution**: Check Railway logs for import errors or missing dependencies

## **Environment Variables Checklist**

### **Main App Required:**
- [ ] `OPENAI_API_KEY`
- [ ] `STRIPE_SECRET_KEY`
- [ ] `STRIPE_WEBHOOK_SECRET`
- [ ] `FIREBASE_PROJECT_ID`
- [ ] `FIREBASE_PRIVATE_KEY`
- [ ] `FIREBASE_CLIENT_EMAIL`
- [ ] `FLASK_ENV=production`

### **Background Worker Required:**
- [ ] `TELEGRAM_BOT_TOKEN`
- [ ] `API_BASE_URL=https://fxsentinel-production.up.railway.app`
- [ ] `OPENAI_API_KEY`
- [ ] `FLASK_ENV=production`

## **Expected Results**

After successful deployment:

### **Main App:**
- ✅ Web interface loads at `https://fxsentinel-production.up.railway.app`
- ✅ API endpoints respond correctly
- ✅ Health check returns healthy status
- ✅ Frontend serves properly

### **Background Worker:**
- ✅ Starts without errors
- ✅ Monitors for news alerts
- ✅ Processes economic calendar events
- ✅ Sends Telegram notifications
- ✅ Logs status every 5 minutes

## **Monitoring**

### **Main App Monitoring:**
- Check Railway logs for Flask app startup
- Monitor API response times
- Watch for memory/CPU usage spikes

### **Background Worker Monitoring:**
- Check logs for "Worker Status" messages every 5 minutes
- Monitor alert sending success rates
- Watch for any import or connection errors

## **Next Steps**

1. **Deploy both services** using the instructions above
2. **Test thoroughly** with the verification steps
3. **Monitor logs** for any issues
4. **Set up alerts** for service failures
5. **Consider scaling** if needed

---

**Status**: ✅ Ready for deployment
**Confidence**: High - Architecture is now properly separated
**Expected Outcome**: Both services should deploy and run successfully
