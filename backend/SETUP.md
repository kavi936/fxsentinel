# FXSentinel Backend Setup Guide

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the backend directory with:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### 3. Get OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up/Login
3. Go to API Keys section
4. Create a new API key
5. Copy and paste it in your `.env` file

### 4. Run the Backend
```bash
python app.py
```

The server will start on `http://localhost:5000`

## 🔧 API Endpoints

- `GET /api/hello` - Health check
- `GET /api/news` - Get economic events
- `GET /api/analysis/<id>` - Get AI analysis for event
- `GET /api/health` - System health check

## 📊 Data Sources

Currently using:
- **ForexFactory** - Economic calendar scraping
- **OpenAI GPT-3.5-turbo** - AI analysis generation

Fallback to mock data if scraping fails.

## 💰 Cost Estimation

- **OpenAI GPT-3.5-turbo**: ~$0.002 per analysis
- **1000 analyses/month**: ~$2.00
- **10,000 analyses/month**: ~$20.00

## 🔐 Security: Firebase service account

The service account contains a **private key** and must be kept secret. It is in `.gitignore`, so it is **never in the repo** and will **not** be deployed with the code.

### Local development

- Place `firebase-service-account.json` in the `backend/` directory (or set `GOOGLE_APPLICATION_CREDENTIALS` to its path).
- Restrict permissions: `chmod 600 backend/firebase-service-account.json`.
- Do not force-add or commit this file.

### Hosted / production app

Because the file is gitignored, the hosted app does **not** have it. Use one of these:

1. **Recommended: env var with JSON**  
   In your host’s dashboard (Railway, Render, Fly.io, etc.), add a **secret** or **env var** named  
   `FIREBASE_SERVICE_ACCOUNT_JSON`  
   and set its value to the **entire contents** of `firebase-service-account.json` (the raw JSON string). The app will use this and Firebase Auth will work in production (usage tracking, per-user OpenAI, etc.).

2. **Alternative: file on server**  
   If your host lets you mount secrets as files, put the JSON at a path on the server and set `GOOGLE_APPLICATION_CREDENTIALS` to that path in the host’s env.

- **If the key is exposed** – Rotate it in [Firebase Console → Project settings → Service accounts](https://console.firebase.google.com/) (generate new key, delete old) and update the env var or file on the host.

## 🚨 Important Notes

1. **Rate Limiting**: ForexFactory may block excessive requests
2. **API Costs**: Monitor OpenAI usage to control costs
3. **Fallback**: System gracefully falls back to mock data if APIs fail
4. **CORS**: Configured for frontend communication

## 🔄 Next Steps

1. Add user authentication
2. Implement rate limiting
3. Add database for user data
4. Set up Telegram bot integration 