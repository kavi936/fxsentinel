# FXSentinel Frontend

A React-based frontend for FXSentinel, an AI-powered forex news analysis platform.

## Features

- **Real-time Forex Prices**: Live market data from Alpha Vantage API
- **Responsive Design**: Modern UI with smooth animations
- **Authentication**: User login and signup functionality
- **Dashboard**: Comprehensive trading insights and alerts

## Alpha Vantage API Integration

The landing page now displays real-time forex prices using the Alpha Vantage API:

### Setup

1. **Get API Key**: Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key) and get a free API key
2. **Configure Environment**: Create a `.env` file in the frontend directory:
   ```
   VITE_ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
   ```
3. **Restart App**: Restart your development server

### Features

- **Live Ticker**: Real-time EUR/USD, USD/JPY, and GBP/USD prices
- **Smart Caching**: API calls cached for 5 minutes to respect rate limits
- **Fallback Data**: Graceful degradation when API is unavailable
- **Visual Indicators**: 
  - 📡 = Live API data
  - ⚙️ = Fallback data
  - ⚠️ = Error state

### Rate Limits

- Free tier: 5 API calls per minute, 500 per day
- Automatic caching prevents excessive API usage
- Fallback to static data when limits are exceeded

## Development

```bash
npm install
npm run dev
```

## Building for Production

```bash
npm run build
```
