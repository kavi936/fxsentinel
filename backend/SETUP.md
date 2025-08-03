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