# Railway Background Worker Deployment Fix Guide

## Problem Summary
The `fxsentinel-background-worker` service was stuck using old cached code (`simple_worker.py`) instead of the new `worker_app.py` entry point, causing the service to fail to detect environment variables and not start the background alert functionality.

## Root Cause Analysis
1. **Missing Entry Point**: The `backend/Dockerfile.worker` referenced `worker_app.py` which didn't exist
2. **Configuration Mismatch**: `railway.worker.json` had incorrect Dockerfile path
3. **Railway Caching**: Railway was using cached Docker images with old code
4. **Auto-detection Override**: Railway was auto-detecting entry points instead of using configuration

## Solution Implemented

### 1. Created Missing Entry Point
- **File**: `backend/worker_app.py`
- **Purpose**: Definitive entry point for the background worker service
- **Features**: 
  - Proper environment variable detection
  - Background worker initialization
  - Health check endpoints
  - Comprehensive logging
  - Cache-busting version (2.0.0)

### 2. Fixed Configuration Files
- **`railway.worker.json`**: Updated Dockerfile path and added start command
- **`backend/Dockerfile.worker`**: Added cache-busting labels and fixed port
- **`Procfile.worker`**: Updated to use correct entry point

### 3. Added Cache-Busting Mechanisms
- **Version Labels**: Added build version and date labels to Dockerfiles
- **Version File**: Created `backend/VERSION` with timestamp
- **Deployment Script**: Created `force_fresh_deployment.sh` for easy redeployment

## Deployment Instructions

### Option 1: Use the Deployment Script (Recommended)
```bash
./force_fresh_deployment.sh
```

### Option 2: Manual Railway CLI Commands
```bash
# Force redeploy the background worker service
railway redeploy --service fxsentinel-background-worker

# Or if service-specific redeploy fails
railway redeploy
```

### Option 3: Nuclear Option (If all else fails)
1. Delete the service in Railway dashboard
2. Recreate it with the same configuration
3. Or use CLI: `railway service delete fxsentinel-background-worker`

## Verification Steps

### 1. Check Deployment Logs
```bash
railway logs --service fxsentinel-background-worker
```

**Look for these success indicators:**
- `🚀 Starting FXSentinel Background Worker v2.0.0 on Railway`
- `🔄 Cache-busting deployment - fresh code loaded`
- `✅ Environment variables configured`
- `✅ Background worker started successfully`
- `🔄 Worker is now monitoring for alerts...`

### 2. Health Check Endpoint
Visit: `https://your-worker-url.railway.app/api/health`

**Expected response:**
```json
{
  "status": "healthy",
  "service": "background-worker",
  "worker_running": true,
  "timestamp": 1234567890,
  "version": "2.0.0"
}
```

### 3. Monitor Alert Functionality
**Look for these log messages:**
- `Checking for news alerts...`
- `Checking for economic calendar alerts...`
- `🎯 Sending economic alert for: [Event Name]`
- `News alert triggered: X alerts sent`

## Troubleshooting

### If Environment Variables Are Still Missing
1. Check Railway dashboard environment variables
2. Ensure `TELEGRAM_BOT_TOKEN` is set
3. Verify `API_BASE_URL` points to your main app

### If Service Still Shows Old Code
1. Try the nuclear option (delete and recreate service)
2. Check if you're looking at the correct service
3. Verify the service is using the correct repository branch

### If Health Check Fails
1. Check if the service is actually running
2. Verify the port configuration (should be 8080)
3. Check Railway logs for startup errors

## Configuration Files Summary

### Key Files Created/Modified:
- ✅ `backend/worker_app.py` - New entry point
- ✅ `backend/Dockerfile.worker` - Fixed Dockerfile
- ✅ `railway.worker.json` - Fixed configuration
- ✅ `Procfile.worker` - Updated entry point
- ✅ `force_fresh_deployment.sh` - Deployment script
- ✅ `backend/VERSION` - Version tracking

### Environment Variables Required:
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `API_BASE_URL` - URL of main Flask app (optional, defaults to localhost)

## Success Criteria
The deployment is successful when:
1. ✅ Logs show "FXSentinel Background Worker v2.0.0"
2. ✅ Health check returns `worker_running: true`
3. ✅ Environment variables are detected
4. ✅ Background worker starts monitoring
5. ✅ Alerts are being sent to users

## Next Steps After Successful Deployment
1. Monitor the service for 24-48 hours
2. Verify alerts are being sent to users
3. Check economic calendar and news alert functionality
4. Update monitoring and alerting systems
5. Document any additional configuration needed
