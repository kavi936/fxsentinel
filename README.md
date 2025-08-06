# FXSentinel - Real-Time Forex Market Intelligence

FXSentinel is a comprehensive forex trading platform that provides real-time market data, economic news analysis, and AI-powered insights to help traders make informed decisions.

## 🚀 Features

- **Real-Time Forex Prices**: Live EUR/USD, USD/JPY, and GBP/USD prices from Polygon.io
- **Economic News Analysis**: AI-powered analysis of economic events and their market impact
- **Market Sentiment**: Real-time market sentiment indicators
- **Price Alerts**: Customizable price alerts and notifications
- **Professional UI**: Modern, responsive design with real-time updates

## 🛠️ Tech Stack

- **Frontend**: React + Vite
- **Backend**: Flask (Python)
- **Market Data**: Polygon.io API (Professional forex data)
- **AI Analysis**: OpenAI GPT-3.5-turbo
- **News Source**: ForexFactory scraping + Telegram integration
- **Hosting**: Railway
- **Styling**: CSS3 with glassmorphism effects

## 📊 Market Data Integration

### UniRateAPI Integration
- **Professional forex data** from ECB and major banks
- **Unlimited API calls** (Free forever)
- **Real-time rates** updated continuously
- **Automatic rate limiting** and fallback mechanisms

### Data Quality
- **EUR/USD, USD/JPY, GBP/USD** real-time prices
- **170+ fiat currencies** + 420+ cryptocurrencies
- **Professional-grade reliability** from ECB and bank sources

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd fxsentinel
```

### 2. Set Up Environment Variables
Create `.env` files with your API keys:

**Backend (.env in backend/ directory):**
```env
UNIRATE_API_KEY=your_unirate_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

**Frontend (.env in root directory):**
```env
VITE_UNIRATE_API_KEY=your_unirate_api_key_here
VITE_API_URL=http://localhost:8000
```

### 3. Install Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ..
npm install
```

### 4. Run the Application
```bash
# Start backend (in backend/ directory)
python app.py

# Start frontend (in root directory)
npm run dev
```

### 5. Test the Integration
```bash
python test_unirate_integration.py
```

## 📈 API Endpoints

- `GET /api/forex-prices` - Real-time forex prices
- `GET /api/news` - Economic news and events
- `GET /api/analysis/<id>` - AI analysis of news events
- `GET /api/api-status` - API usage and rate limit status
- `GET /api/trading-data` - Market sentiment and trading data

## 💰 Pricing & Costs

### Monthly Recurring Costs
- **UniRateAPI Market Data**: $0/month (Free forever)
- **Domain**: $2.92/month
- **Railway Hosting**: $8/month
- **OpenAI API**: $15/month
- **Total**: ~$26/month

### Revenue Model
- **Product Price**: $24.99/month per user
- **Break-even**: 2 paying users
- **Profit Target**: 10+ users for $224+/month profit

## 🔧 Configuration

### UniRateAPI Setup
1. Sign up at [UniRateAPI](https://unirateapi.com/) (Free forever)
2. Get your free API key from the dashboard
3. Add to environment variables
4. Add attribution link to your website

### Rate Limiting
- **30 API calls per minute**
- **Unlimited daily requests**
- **Automatic fallback** when limits exceeded

## 📚 Documentation

- [UniRateAPI Setup Guide](UNIRATE_API_SETUP.md)
- [API Setup Guide](API_SETUP.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Budget Plan](MVP_BUDGET_PLAN.md)

## 🧪 Testing

Run the integration test to verify everything works:
```bash
python test_unirate_integration.py
```

## 🚀 Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section in [UNIRATE_API_SETUP.md](UNIRATE_API_SETUP.md)
2. Review the API status endpoint: `/api/api-status`
3. Run the test script: `python test_unirate_integration.py`
