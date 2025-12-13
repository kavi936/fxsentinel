# Environment Variables Setup Guide

## 🔒 **SECURITY WARNING**
**NEVER commit API keys to your repository!** This guide shows you how to set up environment variables securely.

## 📁 **File Structure**

### Frontend (Vercel)
- **File:** `.env` (root directory)
- **Purpose:** Public variables only
- **Safe variables:**
  ```
  VITE_API_URL=http://localhost:8000
  ```

### Backend (Railway)
- **File:** `backend/.env`
- **Purpose:** Secret API keys
- **Secret variables:**
  ```
  UNIRATE_API_KEY=your_actual_key_here
  OPENAI_API_KEY=your_actual_key_here
  FLASK_ENV=development
  FLASK_DEBUG=True
  ```

## 🚀 **Deployment Setup**

### Vercel (Frontend)
1. Go to your Vercel project dashboard
2. Navigate to Settings → Environment Variables
3. Add:
   - `VITE_API_URL` = `https://your-railway-app.railway.app`

### Railway (Backend)
1. Go to your Railway project dashboard
2. Navigate to Variables tab
3. Add:
   - `UNIRATE_API_KEY` = `your_actual_unirate_key`
   - `OPENAI_API_KEY` = `your_actual_openai_key`
   - `FLASK_ENV` = `production`
   - `FLASK_DEBUG` = `False`

## ⚠️ **What NOT to do**
- ❌ Never put secret keys in frontend `.env`
- ❌ Never commit `.env` files with real keys
- ❌ Never use `VITE_` prefix for secret keys
- ❌ Never expose API keys in browser code

## ✅ **What TO do**
- ✅ Only use `VITE_` for public variables
- ✅ Put all secrets in backend environment
- ✅ Use Railway environment variables for production
- ✅ Keep `.env` files in `.gitignore`

## 🔍 **Verification**
- Frontend should only call your backend API
- Backend should handle all external API calls
- No secret keys should be visible in browser dev tools 