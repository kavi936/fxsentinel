// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const ALPHA_VANTAGE_API_KEY = import.meta.env.VITE_ALPHA_VANTAGE_API_KEY || 'demo';

export const config = {
  API_BASE_URL,
  alphaVantageKey: ALPHA_VANTAGE_API_KEY,
  endpoints: {
    news: `${API_BASE_URL}/api/news`,
    analysis: (id) => `${API_BASE_URL}/api/analysis/${id}`,
    tradingData: `${API_BASE_URL}/api/trading-data`,
    alerts: `${API_BASE_URL}/api/alerts`,
    aiInsights: `${API_BASE_URL}/api/ai-insights`,
    alertSettings: `${API_BASE_URL}/api/alert-settings`,
    hello: `${API_BASE_URL}/api/hello`,
    // Alpha Vantage base URL
    alphaVantage: 'https://www.alphavantage.co',
    // Forex price endpoints
    forexPrice: (fromCurrency, toCurrency) => 
      `https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=${fromCurrency}&to_currency=${toCurrency}&apikey=${ALPHA_VANTAGE_API_KEY}`
  }
}; 