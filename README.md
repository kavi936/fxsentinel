# FXSentinel - AI-Powered Forex Market Analysis Platform

A comprehensive forex trading analysis platform that combines real-time market data, AI-powered news analysis, and technical indicators to provide actionable trading insights.

## Features

- **Real-time Market Data**: Live forex prices, economic indicators, and market sentiment
- **AI-Powered News Analysis**: GPT-4 powered analysis of financial news and market events
- **Economic Calendar**: Real-time economic events and their market impact
- **Technical Analysis**: Advanced charting and technical indicators
- **Live News Feed**: Aggregated financial news from multiple sources
- **Market Sentiment Analysis**: AI-driven sentiment analysis for currency pairs

## Security Notice

**Important**: This repository contains sensitive API keys in test files. Before pushing to any public repository:

1. **Never commit API keys** - All API keys should be stored as environment variables
2. **Use the provided `.env.example`** as a template for your environment variables
3. **Check all test files** for hardcoded keys before pushing

## Quick Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd fxsentinel
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual API keys
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd ..
   npm install
   ```

5. **Start the development servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python3 app.py
   
   # Terminal 2 - Frontend
   npm run dev
   ```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
FINNHUB_API_KEY=your_finnhub_api_key_here
ALPHA_VANTAGE_API_KEY_1=your_alpha_vantage_key_here
UNIRATE_API_KEY=your_unirate_api_key_here

# Optional API Keys
POLYGON_API_KEY=your_polygon_api_key_here

# Frontend Variables (safe to expose)
VITE_ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
VITE_POLYGON_API_KEY=your_polygon_api_key_here
```

## API Key Sources

- **OpenAI**: [OpenAI API](https://platform.openai.com/api-keys)
- **Finnhub**: [Finnhub.io](https://finnhub.io/register)
- **Alpha Vantage**: [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- **Unirate**: [Unirate API](https://unirateapi.com/)
- **Polygon.io**: [Polygon.io](https://polygon.io/)

## Deployment

### Railway Deployment

The project is configured for Railway deployment with the following environment variables set in Railway dashboard:

- `OPENAI_API_KEY`
- `FINNHUB_API_KEY`
- `ALPHA_VANTAGE_API_KEY_1-4`
- `UNIRATE_API_KEY`

### Local Development

For local development, ensure all environment variables are set in your `.env` file.

## Project Structure

```
fxsentinel/
├── backend/                 # Flask backend
│   ├── app.py              # Main Flask application
│   ├── services/           # API services
│   └── requirements.txt    # Python dependencies
├── src/                    # React frontend
│   ├── components/         # React components
│   ├── contexts/           # React contexts
│   └── utils/              # Utility functions
├── .env                    # Environment variables (not in git)
├── env.example             # Environment template
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure no API keys are hardcoded
5. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For support and questions, please contact the development team.
