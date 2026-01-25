import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import Signup from './components/Signup';
import TrialWelcomeRoute from './components/TrialWelcomeRoute';
import ProtectedRoute from './components/ProtectedRoute';
import AuthRedirect from './components/AuthRedirect';
import Blog from './components/Blog';
import Disclaimer from './components/Disclaimer';
import Privacy from './components/Privacy';
import FeedbackForm from './components/FeedbackForm';
import AIPoweredNewsAnalysis from './components/blog-posts/AIPoweredNewsAnalysis';
import CentralBankDecisions from './components/blog-posts/CentralBankDecisions';
import ForexMarketSentiment from './components/blog-posts/ForexMarketSentiment';
import NewsToSignals from './components/blog-posts/NewsToSignals';
import MarketVolatility from './components/blog-posts/MarketVolatility';
import AIHiddenPatterns from './components/blog-posts/AIHiddenPatterns';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import BannerNotifications from './components/BannerNotifications';
import { useRouteTracking } from './hooks/useRouteTracking';
import './App.css';

// Component to handle route tracking
function RouteTracker() {
  useRouteTracking();
  return null;
}

function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <Router>
          <RouteTracker />
          <div className="app">
            <BannerNotifications />
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/blog" element={<Blog />} />
              <Route path="/blog/ai-powered-news-analysis-future-of-trading" element={<AIPoweredNewsAnalysis />} />
              <Route path="/blog/central-bank-decisions-currency-pairs" element={<CentralBankDecisions />} />
              <Route path="/blog/understanding-forex-market-sentiment" element={<ForexMarketSentiment />} />
              <Route path="/blog/turning-news-actionable-signals" element={<NewsToSignals />} />
              <Route path="/blog/traders-guide-decoding-market-volatility" element={<MarketVolatility />} />
              <Route path="/blog/ai-detects-hidden-patterns-macroeconomic-news" element={<AIHiddenPatterns />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/auth-redirect" element={<AuthRedirect />} />
              <Route path="/disclaimer" element={<Disclaimer />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/feedback" element={<FeedbackForm />} />
              <Route path="/trial-welcome" element={
                <ProtectedRoute>
                  <TrialWelcomeRoute />
                </ProtectedRoute>
              } />
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
            </Routes>
          </div>
        </Router>
      </NotificationProvider>
    </AuthProvider>
  );
}

export default App;
