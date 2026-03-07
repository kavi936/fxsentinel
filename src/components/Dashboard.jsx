import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import axios from 'axios';
import { config } from '../config';
import './Dashboard.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import Overview from './Overview';
import Alerts from './Alerts';
import Economies from './Economies';
import TimezoneSettings from './TimezoneSettings';
import NotificationsPopup from './NotificationsPopup';
import ProfilePopup from './ProfilePopup';
import MarketStatusPopup from './MarketStatusPopup';
import ReviewBanner from './ReviewBanner';
import OnboardingTour from './OnboardingTour';
import { useMeta } from '../hooks/useMeta';
import { trackEngagement, trackFeatureUsage, trackTrialStart, trackDashboardAccess } from '../utils/analytics';

function Dashboard() {
  useMeta('Market Dashboard – FXSentinel', 'Your FXSentinel market dashboard: economic calendar, AI analysis, live news, and Telegram alerts.');
  const { currentUser, logout, requestWelcomeEmail } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const { unreadCount, addSubscriptionNotification } = useNotifications();
  const navigate = useNavigate();
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dataSource, setDataSource] = useState('');
  const [lastUpdated, setLastUpdated] = useState('');
  const [error, setError] = useState(null);
  
  // New state for enhanced features
  const [activeTab, setActiveTab] = useState('overview');
  const [alerts, setAlerts] = useState([]);
  const [alertStats, setAlertStats] = useState({});
  const [tradingData, setTradingData] = useState({});
  const [aiInsights, setAiInsights] = useState([]);
  const [alertSettings, setAlertSettings] = useState({
    telegram: true,
    email: false,
    highImpact: true,
    mediumImpact: true,
    lowImpact: false
  });
  
  // Enhanced navbar state
  const [currentTime, setCurrentTime] = useState(new Date());
  const [marketStatus, setMarketStatus] = useState({ 
    isOpen: false, 
    lastUpdate: new Date(),
    activeSessions: [],
    nextSession: null
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [timezoneSettingsOpen, setTimezoneSettingsOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [marketStatusOpen, setMarketStatusOpen] = useState(false);
  const [sessionVerificationStatus, setSessionVerificationStatus] = useState(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [navTabsExpanded, setNavTabsExpanded] = useState(false);

  // Track dashboard access and first view; send welcome email on first dashboard visit
  useEffect(() => {
    if (!currentUser) return;
    
    // Check if this is the first time user is viewing dashboard
    const hasVisitedDashboard = localStorage.getItem(`dashboard_visited_${currentUser.uid}`);
    const isFirstView = !hasVisitedDashboard;
    
    // Welcome email for all users (Google or email/password): request on first dashboard visit; backend sends only once per user via Firestore
    if (isFirstView) requestWelcomeEmail();
    
    // Track dashboard access with funnel step
    trackDashboardAccess(isFirstView, subscriptionStatus?.status || 'unknown');
    
    // Mark dashboard as visited
    if (isFirstView) {
      localStorage.setItem(`dashboard_visited_${currentUser.uid}`, 'true');
    }
    
    // Also track engagement for backward compatibility
    trackEngagement('dashboard_view', {
      is_first_view: isFirstView,
      subscription_status: subscriptionStatus?.status || 'unknown'
    });
    
    // Track tier information if needed
    if (subscriptionStatus?.status) {
      console.log(`📊 User tier: ${subscriptionStatus.status}`);
    }
  }, [currentUser, subscriptionStatus]);

  // Reset onboarding when ?reset_onboarding=1 (dev: /dashboard?reset_onboarding=1)
  useEffect(() => {
    if (searchParams.get('reset_onboarding') === '1') {
      const keys = [];
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k?.startsWith('fxsentinel_onboarding_')) keys.push(k);
      }
      keys.forEach(k => localStorage.removeItem(k));
      searchParams.delete('reset_onboarding');
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  // Expand nav tabs before onboarding runs (prevents step 1 flickering and splice)
  useEffect(() => {
    if (!currentUser || activeTab !== 'overview' || loading) return;
    const completed = localStorage.getItem(`fxsentinel_onboarding_${currentUser.uid}`);
    if (completed) return;
    setNavTabsExpanded(true);
  }, [currentUser, activeTab, loading]);

  // Check subscription status on mount
  useEffect(() => {
    const checkSubscriptionStatus = async () => {
      if (!currentUser) return;
      
      try {
        const response = await fetch(`${config.API_BASE_URL}/api/subscription-status/${currentUser.uid}?email=${encodeURIComponent(currentUser.email)}`);
        if (response.ok) {
          const data = await response.json();
          // Handle null response gracefully - check if data exists before accessing properties
          if (data && typeof data === 'object') {
            setSubscriptionStatus(data);
            
            // Additional security check - redirect if no valid subscription
            const validStatuses = ['free', 'premium', 'developer'];
            if (data.status && !validStatuses.includes(data.status)) {
              console.warn('⚠️ User does not have valid subscription status');
              // Don't redirect - let them stay on dashboard but with limited access
              // navigate('/login');
            }
            
            console.log('✅ User subscription status:', data.status || 'unknown');
          } else {
            // If data is null or invalid, set default free status
            console.warn('⚠️ Invalid subscription status response, defaulting to free');
            setSubscriptionStatus({
              status: 'free',
              monthly_analysis_count: 0,
              daily_analysis_count: 0,
              monthly_limit: 10,
              daily_limit: null,
              is_developer: false
            });
          }
        }
      } catch (error) {
        console.error('Error checking subscription status:', error);
      }
    };
    
    checkSubscriptionStatus();
  }, [currentUser, navigate]);

  // Check for checkout session verification on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
      console.log('🔍 Found session_id in URL, verifying checkout session...');
      verifyCheckoutSession(sessionId);
    }
  }, []);

  // Verify checkout session
  const verifyCheckoutSession = async (sessionId) => {
    try {
      setSessionVerificationStatus('verifying');
      
      const response = await fetch(`${config.API_BASE_URL}/api/verify-checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Checkout session verified successfully:', data);
        setSessionVerificationStatus('success');
        
        // Add notification for successful trial activation
        addSubscriptionNotification('trial_started');
        
        // Refresh subscription status after successful verification
        await checkSubscriptionStatus();
        
        // Remove the session_id from URL
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Show success message (optional)
        setTimeout(() => {
          setSessionVerificationStatus(null);
        }, 3000);
      } else {
        console.error('❌ Failed to verify checkout session');
        setSessionVerificationStatus('error');
        
        // Remove the session_id from URL even if verification failed
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    } catch (error) {
      console.error('Error verifying checkout session:', error);
      setSessionVerificationStatus('error');
      
      // Remove the session_id from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  };

  // Fetch news data on mount
  useEffect(() => {
    // Load all data in parallel for better performance
    const loadAllData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Try the optimized single endpoint first
        const optimizedResponse = await axios.get(config.endpoints.dashboardData, {
          timeout: 8000
        });
        
        if (optimizedResponse.data && optimizedResponse.data.status === 'success') {
          // Set all data from single response
          setNews(optimizedResponse.data.news || []);
          setDataSource(optimizedResponse.data.newsSources?.join(', ') || 'API');
          setLastUpdated(optimizedResponse.data.lastUpdated);
          setTradingData(optimizedResponse.data.tradingData || {});
          setAlerts(optimizedResponse.data.alerts || []);
          setAlertStats(optimizedResponse.data.alertStats || {});
          setAiInsights(optimizedResponse.data.aiInsights || []);
          setAlertSettings(optimizedResponse.data.alertSettings || {});
          
          console.log('✅ Loaded all data from optimized endpoint');
          setLoading(false);
          return;
        }
      } catch (error) {
        console.warn('Optimized endpoint failed, falling back to individual calls:', error);
      }
      
      // Fallback to individual API calls if optimized endpoint fails
      try {
        // Create all API calls in parallel
        const promises = [
          fetchNews(),
          fetchTradingData(),
          fetchAlerts(),
          fetchAiInsights(),
          fetchAlertSettings(),
          fetchMarketStatus()
        ];
        
        // Wait for all promises to resolve with a timeout
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 10000)
        );
        
        await Promise.race([
          Promise.all(promises),
          timeoutPromise
        ]);
        
        setLoading(false);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
        setError('Some data failed to load. Using available data.');
        setLoading(false);
      }
    };
    
    loadAllData();
  }, []);

  // Update time every second
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timeInterval);
  }, []);

  // Update market status every 30 seconds
  useEffect(() => {
    const marketInterval = setInterval(() => {
      fetchMarketStatus();
    }, 30000);

    return () => clearInterval(marketInterval);
  }, []);

  // Close mobile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (mobileMenuOpen && !event.target.closest('.mobile-menu-overlay') && !event.target.closest('.mobile-menu-toggle')) {
        setMobileMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [mobileMenuOpen]);

  // Manage body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.classList.add('mobile-menu-open');
    } else {
      document.body.classList.remove('mobile-menu-open');
    }

    return () => {
      document.body.classList.remove('mobile-menu-open');
    };
  }, [mobileMenuOpen]);

  const fetchNews = async (forceRefresh = false) => {
    try {
      // Add timeout to API call
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000); // Increased timeout to 8 seconds
      
      const url = forceRefresh 
        ? `${config.API_BASE_URL}/api/news?force_refresh=true`
        : config.endpoints.news;
      
      const response = await axios.get(url, {
        signal: controller.signal,
        timeout: 8000
      });
      
      clearTimeout(timeoutId);
      setNews(response.data.news);
      setDataSource(response.data.source || 'API');
      setLastUpdated(response.data.last_updated);
    } catch (error) {
      console.error('Error fetching news:', error);
      
      if (error.name === 'AbortError' || error.code === 'ECONNABORTED') {
        console.warn('News request timed out. Using fallback data.');
        // Load fallback data immediately
        setNews([
          {
            id: 1,
            title: "US Non-Farm Payrolls",
            description: "Employment data release expected to show strong job growth",
            impact: "High",
            date: "2025-08-15",
            time: "08:30 EST",
            currency: "USD",
            pairs: ["EUR/USD", "USD/JPY"],
            expected: "180K",
            previous: "173K"
          },
          {
            id: 2,
            title: "ECB Interest Rate Decision",
            description: "European Central Bank expected to maintain current rates",
            impact: "Medium",
            date: "2025-08-16",
            time: "12:45 CET",
            currency: "EUR",
            pairs: ["EUR/USD", "EUR/GBP"],
            expected: "4.50%",
            previous: "4.50%"
          }
        ]);
        setDataSource('Fallback Data');
        setLastUpdated(new Date().toISOString());
      } else {
        console.warn('Failed to load news data. Using fallback data.');
        // Same fallback data
        setNews([
          {
            id: 1,
            title: "US Non-Farm Payrolls",
            description: "Employment data release expected to show strong job growth",
            impact: "High",
            date: "2025-08-15",
            time: "08:30 EST",
            currency: "USD",
            pairs: ["EUR/USD", "USD/JPY"],
            expected: "180K",
            previous: "173K"
          },
          {
            id: 2,
            title: "ECB Interest Rate Decision",
            description: "European Central Bank expected to maintain current rates",
            impact: "Medium",
            date: "2025-08-16",
            time: "12:45 CET",
            currency: "EUR",
            pairs: ["EUR/USD", "EUR/GBP"],
            expected: "4.50%",
            previous: "4.50%"
          }
        ]);
        setDataSource('Fallback Data');
        setLastUpdated(new Date().toISOString());
      }
    }
  };



  const fetchTradingData = async () => {
    try {
      const response = await axios.get(config.endpoints.tradingData);
      setTradingData(response.data);
    } catch (error) {
      console.error('Error fetching trading data:', error);
      // Fallback to mock data if API fails
      setTradingData({
        eurUsd: { price: 1.0856, change: 0.12, sentiment: 'bullish' },
        usdJpy: { price: 148.23, change: -0.08, sentiment: 'bearish' },
        gold: { price: 2034.50, change: 0.45, sentiment: 'bullish' },
        marketSentiment: 'neutral',
        volatilityIndex: 15.2
      });
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(config.endpoints.alerts);
      setAlerts(response.data.alerts);
      setAlertStats(response.data.stats);
    } catch (error) {
      console.error('Error fetching alerts:', error);
      // Fallback to mock data if API fails
      setAlerts([
        {
          id: 1,
          type: 'telegram',
          event: 'US CPI Data',
          status: 'sent',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          recipients: 1250
        },
        {
          id: 2,
          type: 'email',
          event: 'ECB Interest Rate Decision',
          status: 'scheduled',
          timestamp: new Date(Date.now() + 7200000).toISOString(),
          recipients: 890
        }
      ]);
      setAlertStats({
        telegramSubscribers: 1250,
        emailSubscribers: 890,
        alertsThisWeek: 24
      });
    }
  };

  const fetchAiInsights = async () => {
    try {
      const response = await axios.get(config.endpoints.aiInsights);
      setAiInsights(response.data.insights);
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      // Fallback to mock data if API fails
      setAiInsights([
        {
          id: 1,
          title: 'EUR/USD Analysis',
          description: 'Strong support at 1.0850 level. Break above 1.0870 could trigger bullish momentum. Key resistance at 1.0900.',
          confidence: 85,
          timeframe: '4H Timeframe'
        },
        {
          id: 2,
          title: 'USD/JPY Analysis',
          description: 'Consolidating near 148.00 support. Bearish pressure building. Watch for break below 147.80 for short opportunities.',
          confidence: 72,
          timeframe: '1H Timeframe'
        },
        {
          id: 3,
          title: 'Gold Analysis',
          description: 'Bullish momentum continues above $2030. Next target $2050. Safe haven demand supporting prices.',
          confidence: 91,
          timeframe: 'Daily Timeframe'
        }
      ]);
    }
  };

  const fetchAlertSettings = async () => {
    try {
      const response = await axios.get(config.endpoints.alertSettings);
      setAlertSettings(response.data);
    } catch (error) {
      console.error('Error fetching alert settings:', error);
      // Fallback to mock data if API fails
      setAlertSettings({
        telegram: true,
        email: false,
        highImpact: true,
        mediumImpact: true,
        lowImpact: false
      });
    }
  };



  const refreshData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Try the optimized single endpoint first with force refresh for news
      const optimizedResponse = await axios.get(`${config.endpoints.dashboardData}?force_refresh=true`, {
        timeout: 8000
      });
      
      if (optimizedResponse.data && optimizedResponse.data.status === 'success') {
        // Set all data from single response
        setNews(optimizedResponse.data.news || []);
        setDataSource(optimizedResponse.data.newsSources?.join(', ') || 'API');
        setLastUpdated(optimizedResponse.data.lastUpdated);
        setTradingData(optimizedResponse.data.tradingData || {});
        setAlerts(optimizedResponse.data.alerts || []);
        setAlertStats(optimizedResponse.data.alertStats || {});
        setAiInsights(optimizedResponse.data.aiInsights || []);
        setAlertSettings(optimizedResponse.data.alertSettings || {});
        
        console.log('✅ Refreshed all data from optimized endpoint');
        setLoading(false);
        return;
      }
    } catch (error) {
      console.warn('Optimized endpoint failed, falling back to individual calls:', error);
    }
    
    // Fallback to individual API calls - use force refresh for news
    fetchNews(true); // Force refresh to get fresh news
    fetchTradingData();
    fetchAlerts();
    fetchAiInsights();
    fetchAlertSettings();
    fetchMarketStatus();
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Failed to log out:', error);
    }
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const handleMobileTabChange = (tab) => {
    setActiveTab(tab);
    setMobileMenuOpen(false);
  };

  const updateAlertSettings = (setting, value) => {
    setAlertSettings(prev => ({
      ...prev,
      [setting]: value
    }));
    
    // Save settings to backend
    saveAlertSettings({ ...alertSettings, [setting]: value });
  };

  const handleTimezoneChange = (newTimezone) => {
    // Force re-render of components that display time
    setCurrentTime(new Date());
    
    // Trigger a custom event to notify other components
    window.dispatchEvent(new CustomEvent('timezoneChanged', { 
      detail: { timezone: newTimezone } 
    }));
  };

  const saveAlertSettings = async (settings) => {
    try {
      // Get current user ID (you'll need to implement this based on your auth system)
      const userId = "0E0xJnQpYzZb8YkfQfSiwKYc8Fz2"; // For now, hardcoded
      
      const response = await axios.put(config.endpoints.alertSettings, {
        userId: userId,
        settings: settings
      });
      
      if (response.data.success) {
        console.log('✅ Alert settings saved successfully');
      } else {
        console.error('❌ Failed to save alert settings:', response.data.error);
      }
    } catch (error) {
      console.error('❌ Error saving alert settings:', error);
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'bullish': return '#00cc44';
      case 'bearish': return '#ff4444';
      case 'neutral': return '#ffaa00';
      default: return '#666666';
    }
  };

  const getTradingSessions = () => {
    const now = new Date();
    const utcHour = now.getUTCHours();
    const utcDay = now.getUTCDay();
    
    // Check if it's weekend (Saturday = 6, Sunday = 0)
    const isWeekend = utcDay === 0 || utcDay === 6;
    
    // Check for major holidays when forex markets are typically closed
    const utcMonth = now.getUTCMonth();
    const utcDate = now.getUTCDate();
    
    // Major holidays (simplified list - forex markets may have different schedules)
    const isHoliday = (
      // New Year's Day (January 1)
      (utcMonth === 0 && utcDate === 1) ||
      // Christmas Day (December 25)
      (utcMonth === 11 && utcDate === 25) ||
      // Boxing Day (December 26) - some markets
      (utcMonth === 11 && utcDate === 26)
    );
    
    // If it's weekend or holiday, markets are closed
    if (isWeekend || isHoliday) {
      return { 
        activeSessions: [], 
        nextSession: null
      };
    }
    
    // Trading session times (UTC) - only active on weekdays
    const sessions = [
      { name: 'Sydney', start: 22, end: 7, timezone: 'AEST', color: '#4CAF50', localStart: 22, localEnd: 7 },
      { name: 'Tokyo', start: 0, end: 9, timezone: 'JST', color: '#2196F3', localStart: 0, localEnd: 9 },
      { name: 'London', start: 8, end: 17, timezone: 'GMT', color: '#FF9800', localStart: 8, localEnd: 17 },
      { name: 'New York', start: 13, end: 22, timezone: 'EST', color: '#9C27B0', localStart: 13, localEnd: 22 }
    ];
    
    const activeSessions = [];
    
    sessions.forEach(session => {
      let isActive = false;
      
      if (session.start <= session.end) {
        // Same day session (e.g., London 8-17)
        isActive = utcHour >= session.start && utcHour < session.end;
      } else {
        // Overnight session (e.g., Sydney 22-7)
        isActive = utcHour >= session.start || utcHour < session.end;
      }
      
      if (isActive) {
        activeSessions.push(session);
      }
    });
    
    return { activeSessions, nextSession: null };
  };



  const fetchMarketStatus = async () => {
    try {
      // Use the backend endpoint to get forex data and determine market status
      const response = await axios.get(config.endpoints.forexPrices);
      
      if (response.data && response.data.prices) {
        // Check if we have recent data (within last 5 minutes)
        const now = new Date();
        const isRecent = true; // Assume markets are open if we get data
        
        const { activeSessions } = getTradingSessions();
        
        setMarketStatus({
          isOpen: isRecent && activeSessions.length > 0,
          lastUpdate: now,
          activeSessions
        });
      }
    } catch (error) {
      console.error('Error fetching market status:', error);
      // Fallback to proper market hours checking
      const now = new Date();
      const { activeSessions } = getTradingSessions();
      
      // Check if it's weekend (Saturday = 6, Sunday = 0)
      const isWeekend = now.getUTCDay() === 0 || now.getUTCDay() === 6;
      
      // Markets are closed on weekends
      if (isWeekend) {
        setMarketStatus({
          isOpen: false,
          lastUpdate: now,
          activeSessions: []
        });
        return;
      }
      
      // For weekdays, check if there are active sessions
      setMarketStatus({
        isOpen: activeSessions.length > 0,
        lastUpdate: now,
        activeSessions
      });
    }
  };

  const formatCurrentTime = () => {
    const day = String(currentTime.getDate()).padStart(2, '0');
    const month = String(currentTime.getMonth() + 1).padStart(2, '0');
    const year = String(currentTime.getFullYear()).slice(-2);
    const hours = String(currentTime.getHours()).padStart(2, '0');
    const minutes = String(currentTime.getMinutes()).padStart(2, '0');
    const seconds = String(currentTime.getSeconds()).padStart(2, '0');
    
    return {
      date: `${day}/${month}/${year}`,
      time: `${hours}:${minutes}:${seconds}`
    };
  };

  const getUserDisplayName = (truncate = false) => {
    if (!currentUser) return 'Guest';
    
    let displayName = '';
    
    // Check if user has a display name set
    if (currentUser.displayName) {
      displayName = currentUser.displayName;
    }
    // If no display name, try to extract a proper name from email
    else if (currentUser.email) {
      const emailName = currentUser.email.split('@')[0];
      // Convert email name to proper case (e.g., "kavi.cf412" -> "Kavi")
      const nameParts = emailName.split('.');
      if (nameParts.length > 0) {
        // Capitalize the first part and use it as the name
        displayName = nameParts[0].charAt(0).toUpperCase() + nameParts[0].slice(1);
      } else {
        displayName = emailName;
      }
    } else {
      displayName = 'User';
    }
    
    // Truncate to maximum 8 characters to prevent navbar overflow
    if (truncate && displayName.length > 8) {
      return displayName.substring(0, 8);
    }
    
    return displayName;
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading market news...</p>
        <small>Fetching real-time economic events</small>
      </div>
    );
  }

  return (
    <div className={`dashboard ${activeTab === 'economies' ? 'economies-active' : ''} ${activeTab === 'overview' ? 'overview-active' : ''} ${activeTab === 'alerts' ? 'alerts-active' : ''}`}>
      {/* Session Verification Status Notification */}
      {sessionVerificationStatus === 'verifying' && (
        <div className="verification-notification verifying">
          <div className="verification-content">
            <div className="spinner"></div>
            <span>Verifying your subscription...</span>
          </div>
        </div>
      )}
      
      {sessionVerificationStatus === 'success' && (
        <div className="verification-notification success">
          <div className="verification-content">
            <span>✅ Your trial has been activated successfully!</span>
            <button onClick={() => setSessionVerificationStatus(null)}>×</button>
          </div>
        </div>
      )}
      
      {sessionVerificationStatus === 'error' && (
        <div className="verification-notification error">
          <div className="verification-content">
            <span>❌ Failed to verify subscription. Please check your profile for status.</span>
            <button onClick={() => setSessionVerificationStatus(null)}>×</button>
          </div>
        </div>
      )}
      {/* Compact Static Navbar */}
      <nav className="dashboard-navbar">
        <div className="navbar-container">
          <div className="navbar-left">
            <div className="navbar-logo">
              <picture>
                <source srcSet={logoWebp} type="image/webp" />
                <img 
                  src={logoPng} 
                  alt="FXSentinel" 
                  style={{ height: '40px', width: 'auto' }}
                />
              </picture>
            </div>
            <div className="welcome-message">
              Welcome, <span className="username">{getUserDisplayName(true)}</span>
            </div>
            {/* Market status - shown in navbar-left on mobile */}
            <div 
              className="market-status market-status-mobile"
              onClick={() => setMarketStatusOpen(true)}
              style={{ cursor: 'pointer' }}
              title="Click for detailed market status"
            >
              <span className={`status-dot ${marketStatus.isOpen ? 'open' : 'closed'}`}></span>
              <div className="status-content">
                <span className="status-text">
                  {marketStatus.isOpen ? 'Markets Open' : 'Markets Closed'}
                  {marketStatus.activeSessions && marketStatus.activeSessions.length > 0 && (
                    <span className="session-brackets">
                      ({marketStatus.activeSessions.map(session => session.name).join(', ')})
                    </span>
                  )}
                </span>
              </div>
            </div>
            <div className="datetime-container">
              <div className="live-time">
                <span className="date-section">{formatCurrentTime().date}</span>
                <span className="time-section">{formatCurrentTime().time}</span>
              </div>
            </div>
          </div>
          
          <div 
            className="navbar-center"
            onMouseEnter={() => setNavTabsExpanded(true)}
            onMouseLeave={() => {
              if (document.body.classList.contains('driver-active')) return;
              setNavTabsExpanded(false);
            }}
          >
            <div className={`navbar-tabs ${navTabsExpanded ? 'expanded' : 'collapsed'}`} data-onboarding="nav-tabs">
              {!navTabsExpanded ? (
                <div className="nav-home-icon" title="Navigation">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                    <polyline points="9,22 9,12 15,12 15,22"/>
                  </svg>
                </div>
              ) : (
                <>
                  <button 
                    className={`nav-tab ${activeTab === 'economies' ? 'active' : ''}`}
                    onClick={() => setActiveTab('economies')}
                    data-onboarding="nav-economies"
                  >
                    Economies
                  </button>
                  <button 
                    className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                  >
                    Overview
                  </button>
                  <button 
                    className={`nav-tab ${activeTab === 'alerts' ? 'active' : ''}`}
                    onClick={() => setActiveTab('alerts')}
                    data-onboarding="nav-alerts"
                  >
                    Alerts
                  </button>
                </>
              )}
            </div>
          </div>
          
          <div className="navbar-right">
            <div 
              className="market-status"
              onClick={() => setMarketStatusOpen(true)}
              style={{ cursor: 'pointer' }}
              title="Click for detailed market status"
            >
              <span className={`status-dot ${marketStatus.isOpen ? 'open' : 'closed'}`}></span>
              <div className="status-content">
                <span className="status-text">
                  {marketStatus.isOpen ? 'Markets Open' : 'Markets Closed'}
                  {marketStatus.activeSessions && marketStatus.activeSessions.length > 0 && (
                    <span className="session-brackets">
                      ({marketStatus.activeSessions.map(session => session.name).join(', ')})
                    </span>
                  )}

                </span>
              </div>
            </div>
            <button onClick={refreshData} className="navbar-refresh-btn" title="Refresh Data">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M23 4v6h-6M1 20v-6h6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
              </svg>
            </button>
            {/* Notifications button - commented out as it doesn't do anything */}
            {/* <button 
              className="notification-btn" 
              title="Notifications"
              onClick={() => setNotificationsOpen(true)}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
              {unreadCount > 0 && (
                <span className="notification-badge">{unreadCount}</span>
              )}
            </button> */}
            <button 
              className="profile-btn" 
              title="User Profile"
              onClick={() => setProfileOpen(true)}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </button>
            <button 
              className="settings-btn" 
              title="Timezone Settings"
              onClick={() => setTimezoneSettingsOpen(true)}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12,6 12,12 16,14"/>
              </svg>
            </button>
            <Link to="/" className="home-btn" title="Log out / Back to Home">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
            </Link>
          </div>
          
          {/* Mobile Menu Toggle */}
          <button 
            className="mobile-menu-toggle" 
            onClick={toggleMobileMenu}
            title="Menu"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
        </div>
        <div className="navbar-divider"></div>
      </nav>

      {/* Mobile Menu Overlay */}
      <div className={`mobile-menu-overlay ${mobileMenuOpen ? 'active' : ''}`}>
        <div className="mobile-menu-content">
          <div className="mobile-menu-section">
            <h3>Navigation</h3>
            <div className="mobile-nav-tabs">
              <button 
                className={`mobile-nav-tab ${activeTab === 'economies' ? 'active' : ''}`}
                onClick={() => handleMobileTabChange('economies')}
                data-onboarding="nav-economies"
              >
                Economies
              </button>
              <button 
                className={`mobile-nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => handleMobileTabChange('overview')}
              >
                Overview
              </button>
              <button 
                className={`mobile-nav-tab ${activeTab === 'alerts' ? 'active' : ''}`}
                onClick={() => handleMobileTabChange('alerts')}
                data-onboarding="nav-alerts"
              >
                Alerts
              </button>
            </div>
          </div>
          
          <div className="mobile-menu-section">
            <h3>Actions</h3>
            <div className="mobile-actions">
              <button onClick={() => { refreshData(); setMobileMenuOpen(false); }} className="mobile-action-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M23 4v6h-6M1 20v-6h6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
                </svg>
                Refresh Data
              </button>
              {/* Notifications button - commented out as it doesn't do anything */}
              {/* <button 
                className="mobile-action-btn"
                onClick={() => { setNotificationsOpen(true); setMobileMenuOpen(false); }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                  <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                </svg>
                Notifications (3)
              </button> */}
              <button 
                className="mobile-action-btn"
                onClick={() => { setProfileOpen(true); setMobileMenuOpen(false); }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                Profile
              </button>
              <button 
                className="mobile-action-btn"
                onClick={() => { setTimezoneSettingsOpen(true); setMobileMenuOpen(false); }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12,6 12,12 16,14"/>
                </svg>
                Timezone Settings
              </button>
              <Link to="/" className="mobile-action-btn" onClick={() => setMobileMenuOpen(false)}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                  <polyline points="9,22 9,12 15,12 15,22"/>
                </svg>
                Back to Home
              </Link>
              <button onClick={() => { handleLogout(); setMobileMenuOpen(false); }} className="mobile-action-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <polyline points="16,17 21,12 16,7"/>
                  <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={refreshData}>Try Again</button>
        </div>
      )}

      {/* Economies Tab - Rendered outside dashboard-main for full screen */}
      {activeTab === 'economies' && (
        <Economies />
      )}

      {/* Overview Tab - Rendered outside dashboard-main for full screen */}
      {activeTab === 'overview' && (
        <Overview />
      )}

      {/* Alerts Tab - Rendered outside dashboard-main for full screen */}
      {activeTab === 'alerts' && (
        <Alerts 
          alerts={alerts}
          alertStats={alertStats}
          alertSettings={alertSettings}
          updateAlertSettings={updateAlertSettings}
        />
      )}

      {/* Timezone Settings Modal */}
      <TimezoneSettings
        isOpen={timezoneSettingsOpen}
        onClose={() => setTimezoneSettingsOpen(false)}
        onTimezoneChange={handleTimezoneChange}
      />

      {/* Notifications Popup */}
      <NotificationsPopup
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
      />

      {/* Profile Popup */}
      <ProfilePopup
        isOpen={profileOpen}
        onClose={() => setProfileOpen(false)}
      />

      {/* Market Status Popup */}
      <MarketStatusPopup
        isOpen={marketStatusOpen}
        onClose={() => setMarketStatusOpen(false)}
        marketStatus={marketStatus}
      />

      {/* Review Banner */}
      <ReviewBanner />

      {/* Onboarding Tour - auto for first-time, manual from Profile */}
      <OnboardingTour
        userId={currentUser?.uid}
        activeTab={activeTab}
        isOverviewReady={!loading}
        onStartTour={() => setNavTabsExpanded(true)}
        trigger="auto"
      />

  </div>
  );
}

export default Dashboard; 