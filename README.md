# 🌐 FXSentinel - AI-Powered Forex Trading Dashboard

> An AI-powered web application providing macroeconomic news analysis, forecasts, and smart alerts for Forex and commodity traders.

## 🚀 Features

### 📊 News & Analysis Dashboard
- **Real-time Economic Events**: Aggregates key events from ForexFactory
- **AI-Powered Analysis**: GPT-generated explanations of market impact
- **Currency Pair Insights**: Tailored analysis for EUR/USD, USD/JPY, and Gold
- **Impact Assessment**: High/Medium/Low impact classification

### 🔔 Smart Alert System
- **Telegram Bot Integration**: Instant notifications for important events
- **Email Alerts**: Customizable email notifications
- **Impact Level Filtering**: Choose which events to receive alerts for
- **Alert Statistics**: Track delivery and engagement metrics

### 📈 Trading Insights
- **Market Sentiment Analysis**: Real-time sentiment indicators
- **Currency Pair Tracking**: Live prices and percentage changes
- **AI Trading Insights**: Machine learning-powered analysis
- **Volatility Monitoring**: Market volatility index tracking

## 🛠️ Tech Stack

| Layer       | Technology                |
|-------------|---------------------------|
| Frontend    | React + Vite              |
| Backend     | Python + Flask            |
| AI          | OpenAI GPT-4-turbo        |
| Styling     | CSS3 + Glassmorphism      |
| APIs        | ForexFactory (scraped)    |
| Alerts      | Telegram Bot API          |

## 🚀 Quick Start

### Prerequisites
- Node.js (v16+)
- Python (v3.8+)
- OpenAI API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fxsentinel
   ```

2. **Setup Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Set your OpenAI API key
   export OPENAI_API_KEY="your-api-key-here"
   
   # Run the Flask server
   python app.py
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   
   # Create .env file
   echo "VITE_API_URL=http://localhost:5000" > .env
   
   # Run the development server
   npm run dev
   ```

4. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5000

## 📱 Dashboard Features

### Tab Navigation
- **📊 News & Analysis**: View upcoming economic events with AI analysis
- **🔔 Smart Alerts**: Manage notification preferences and view alert history
- **📈 Trading Insights**: Monitor market sentiment and trading opportunities

### Key Components
- **Real-time Data**: Live updates from economic calendars
- **Interactive UI**: Click events for detailed AI analysis
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Professional Styling**: Dark theme with glassmorphism effects

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/news` | GET | Fetch economic events |
| `/api/analysis/<id>` | GET | Get AI analysis for event |
| `/api/trading-data` | GET | Get market data and sentiment |
| `/api/alerts` | GET | Get alert history and stats |
| `/api/ai-insights` | GET | Get AI trading insights |
| `/api/alert-settings` | GET/POST | Manage alert preferences |

## 🎯 Core Value Propositions

1. **Smart Alerts**: Never miss important market-moving events
2. **AI Analysis**: Understand complex market dynamics instantly
3. **Trading Insights**: Make informed decisions with confidence
4. **Real-time Updates**: Stay ahead of market movements

## 🔮 Future Enhancements

- [ ] Real-time price data integration
- [ ] Advanced charting capabilities
- [ ] Mobile app development
- [ ] Social trading features
- [ ] Institutional partnerships
- [ ] Machine learning models for prediction

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**Built with ❤️ for the trading community** 