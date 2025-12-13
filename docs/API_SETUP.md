# Alpha Vantage API Setup Guide

## Getting Your Free API Key

1. **Visit Alpha Vantage**: Go to https://www.alphavantage.co/support/#api-key
2. **Sign Up**: Create a free account
3. **Get API Key**: Your free API key will be provided immediately
4. **Rate Limits**: Free tier allows 5 API calls per minute and 500 per day

## Setting Up the API Key

1. **Edit Environment File**: Open `frontend/.env`
2. **Replace Demo Key**: Change `VITE_ALPHA_VANTAGE_API_KEY=demo` to your actual key:
   ```
   VITE_ALPHA_VANTAGE_API_KEY=YOUR_ACTUAL_API_KEY_HERE
   ```
3. **Restart App**: Restart your development server

## How It Works

- **Real-time Data**: The app fetches live market status from Alpha Vantage
- **Fallback Logic**: If API fails, it uses manual time-based logic
- **Rate Limiting**: API calls are limited to once every 5 minutes
- **Visual Indicators**: 
  - 📡 = Using API data
  - ⚙️ = Using manual fallback

## API Endpoint Used

- **Function**: `MARKET_STATUS`
- **URL**: `https://www.alphavantage.co/query?function=MARKET_STATUS&apikey=YOUR_KEY`
- **Response**: JSON with market status for all markets including Forex

## Troubleshooting

- **"API call failed"**: Check your API key and internet connection
- **Rate limit exceeded**: Wait a few minutes, the app will use fallback logic
- **No data**: The app will automatically use manual logic as backup 