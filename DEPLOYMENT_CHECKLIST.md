# Deployment Checklist - Live Market Data

## ✅ **Pre-Deployment Checks**

### **1. Backend (Railway)**
- [x] UniRateAPI integration working locally
- [x] Currency pair mapping fixed (USD/EUR → EUR/USD)
- [x] Rate inversion logic implemented
- [x] Error handling and fallback mechanisms in place
- [x] Environment variables properly configured

### **2. Frontend (Vercel)**
- [x] API configuration uses environment variables
- [x] LiveTicker component updated with debug logging
- [x] useForexPrices hook enhanced with better error handling
- [x] Cache clearing mechanism implemented
- [x] Attribution link added to footer

### **3. Security**
- [x] API keys not committed to repository
- [x] .env files properly ignored
- [x] Frontend only contains public variables
- [x] Backend handles all secret API calls

## 🚀 **Production Deployment Steps**

### **Step 1: Railway Backend**
1. **Environment Variables to Set:**
   ```
   UNIRATE_API_KEY=dsTglrlXhkV21st7nexUlLkSpi5RnpckNVmyescuv2FLP0r8cMEosNkdP1iuhKvl
   OPENAI_API_KEY=your_openai_api_key_here
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```

2. **Test Backend Endpoints:**
   - `https://your-railway-app.railway.app/api/forex-prices`
   - `https://your-railway-app.railway.app/api/api-status`

### **Step 2: Vercel Frontend**
1. **Environment Variables to Set:**
   ```
   VITE_API_URL=https://your-railway-app.railway.app
   ```

2. **Deploy and Test:**
   - Check live ticker displays real data
   - Verify attribution link is present
   - Test error handling and fallback

## 🔍 **Post-Deployment Verification**

### **1. Live Data Test**
- [ ] Frontend displays real forex prices (not fallback data)
- [ ] Prices update every 5 minutes
- [ ] Error states handled gracefully
- [ ] Attribution link visible in footer

### **2. API Endpoints Test**
- [ ] `/api/forex-prices` returns real UniRateAPI data
- [ ] `/api/api-status` shows correct usage statistics
- [ ] Rate limiting working properly

### **3. Security Verification**
- [ ] No API keys visible in browser dev tools
- [ ] All external API calls go through backend
- [ ] Environment variables properly configured

## 📊 **Expected Live Market Data**
- **EUR/USD**: ~1.156 (real-time)
- **USD/JPY**: ~147.35 (real-time)
- **GBP/USD**: ~1.329 (real-time)

## 🚨 **Troubleshooting**
- If fallback data shows: Check Railway environment variables
- If API errors: Check UniRateAPI key validity
- If frontend errors: Check Vercel environment variables
- If CORS issues: Verify Railway CORS configuration

## 📝 **Monitoring**
- Monitor `/api/api-status` for usage statistics
- Check Railway logs for API errors
- Monitor Vercel deployment for frontend issues 