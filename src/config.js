// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (window.location.hostname === 'localhost' ? 'http://localhost:5001' : 'https://fxsentinel.io');

// Debug logging (only in development)
if (window.location.hostname === 'localhost') {
  console.log('🦊 Config - API_BASE_URL:', API_BASE_URL);
  console.log('🦊 Config - VITE_API_URL:', import.meta.env.VITE_API_URL);
  console.log('🦊 Config - window.location.hostname:', window.location.hostname);
}

export const config = {
  API_BASE_URL,
  endpoints: {
    news: `${API_BASE_URL}/api/news`,
    analysis: (id) => `${API_BASE_URL}/api/analysis/${id}`,
    relatedEvidence: (id) => `${API_BASE_URL}/api/analysis/${id}/related-evidence`,
    tradingData: `${API_BASE_URL}/api/trading-data`,
    alerts: `${API_BASE_URL}/api/alerts`,
    aiInsights: `${API_BASE_URL}/api/ai-insights`,
    alertSettings: `${API_BASE_URL}/api/alerts/settings`,
    hello: `${API_BASE_URL}/api/hello`,
    // Forex prices endpoint (secure backend call)
    forexPrices: `${API_BASE_URL}/api/forex-prices`,
    // Optimized dashboard data endpoint (single request)
    dashboardData: `${API_BASE_URL}/api/dashboard-data`,
    // Economic calendar endpoint (Finnhub integration)
    economicCalendar: `${API_BASE_URL}/api/economic-calendar`,
    // Finnhub test endpoint
    finnhubTest: `${API_BASE_URL}/api/finnhub-test`,
    // Economic chart endpoint
    economicChart: `${API_BASE_URL}/api/economic-chart`,
    // AI Analysis endpoints
    backend: API_BASE_URL,
    enhancedAnalysis: (id) => `${API_BASE_URL}/api/enhanced-analysis/${id}`,
    newsSentiment: `${API_BASE_URL}/api/news-sentiment`,
    technicalAnalysis: (pair) => `${API_BASE_URL}/api/technical-analysis/${pair}`,
    // Market sentiment endpoints
    marketSentiment: `${API_BASE_URL}/api/market-sentiment`,
    sentimentRefresh: `${API_BASE_URL}/api/sentiment/refresh`,
    // Prediction markets endpoint
    predictionMarkets: `${API_BASE_URL}/api/prediction-markets`,
    predictionMarketHistory: (marketId) => `${API_BASE_URL}/api/prediction-markets/${marketId}/history`,
    // Refund request endpoint
    requestRefund: `${API_BASE_URL}/api/request-refund`,
    // Feedback submission endpoint
    submitFeedback: `${API_BASE_URL}/api/submit-feedback`,
    // Economy indicators endpoint (Google Sheets integration)
    economyIndicators: (countryCode) => `${API_BASE_URL}/api/economy-indicators/${countryCode}`,
    // Economy holistic scan endpoint
    economyScan: (countryCode) => `${API_BASE_URL}/api/economy-scan/${countryCode}`,
    // Saved holistic scans (Firestore, same pattern as calendar analysis history)
    economyScanHistory: `${API_BASE_URL}/api/economy-scan-history`,
    // Base URL for direct API calls
    baseUrl: API_BASE_URL
  }
}; 