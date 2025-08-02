# 🌐 FXSentinel

> AI-Powered Macro News Analysis for Forex Traders

FXSentinel is a web application that provides AI-generated analysis of macroeconomic news events, helping retail traders make informed decisions for key instruments like EUR/USD, USD/JPY, and Gold.

## 🚀 Current Status

**MVP Phase 1 Complete** ✅
- ✅ Beautiful news dashboard with mock data
- ✅ AI analysis panel for each news event
- ✅ Responsive design with dark theme
- ✅ Flask backend with REST API
- ✅ React frontend with modern UI

## 🛠️ Tech Stack

- **Frontend**: React + Vite
- **Backend**: Python + Flask
- **Styling**: Modern CSS with dark theme
- **API**: RESTful endpoints for news and analysis

## 📦 Installation & Setup

### Prerequisites
- Node.js (v16+)
- Python 3.8+
- pip

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install flask flask-cors
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000

## 🎯 Features

### Current Features (MVP)
1. **News Dashboard**: Displays upcoming macroeconomic events
2. **Impact Levels**: Color-coded impact indicators (High/Medium/Low)
3. **Trading Pairs**: Shows affected currency pairs for each event
4. **AI Analysis**: Mock AI-generated insights for each news event
5. **Responsive Design**: Works on desktop and mobile

### Mock Data Includes
- US CPI Data Release
- ECB Interest Rate Decision
- UK GDP Preliminary
- BoJ Policy Rate Decision

## 📊 API Endpoints

- `GET /api/hello` - Health check
- `GET /api/news` - Get all news events
- `GET /api/analysis/<id>` - Get AI analysis for specific news event

## 🎨 UI/UX Features

- **Dark Theme**: Professional dark interface
- **Interactive Cards**: Click to view detailed analysis
- **Impact Badges**: Visual impact indicators
- **Responsive Layout**: Adapts to different screen sizes
- **Loading States**: Smooth user experience

## 🔄 Next Steps

### Phase 2 (Next Sprint)
- [ ] Integrate real news APIs (TradingEconomics, ForexFactory)
- [ ] Implement OpenAI GPT-4 for real AI analysis
- [ ] Add user authentication
- [ ] Create Telegram bot integration

### Phase 3 (Future)
- [ ] Real-time price data integration
- [ ] Advanced charting and technical analysis
- [ ] Mobile app development
- [ ] Premium subscription features

## 🏗️ Project Structure

```
fxsentinel/
├── backend/          # Flask API server
│   ├── app.py       # Main Flask application
│   └── venv/        # Python virtual environment
├── frontend/         # React application
│   ├── src/
│   │   ├── App.jsx  # Main React component
│   │   └── App.css  # Styling
│   └── package.json
├── bot/             # Telegram bot (future)
├── data/            # Data scrapers (future)
├── stripe/          # Payment integration (future)
└── README.md
```

## 🤝 Contributing

This is an MVP build. The project is structured to easily add:
- Real API integrations
- Database models
- Authentication
- Payment processing
- Real-time features

## 📝 License

This project is for educational and development purposes.

---

**Built with ❤️ for the trading community** 