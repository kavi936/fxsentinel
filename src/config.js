// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://fxsentinel-production.up.railway.app');

export const config = {
  API_BASE_URL,
  endpoints: {
    news: `${API_BASE_URL}/api/news`,
    analysis: (id) => `${API_BASE_URL}/api/analysis/${id}`,
    tradingData: `${API_BASE_URL}/api/trading-data`,
    alerts: `${API_BASE_URL}/api/alerts`,
    aiInsights: `${API_BASE_URL}/api/ai-insights`,
    alertSettings: `${API_BASE_URL}/api/alert-settings`,
    hello: `${API_BASE_URL}/api/hello`,
    // Forex prices endpoint (secure backend call)
    forexPrices: `${API_BASE_URL}/api/forex-prices`,
    // Optimized dashboard data endpoint (single request)
    dashboardData: `${API_BASE_URL}/api/dashboard-data`
  }
}; 