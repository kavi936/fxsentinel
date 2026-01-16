import React, { useState, useEffect, Fragment } from 'react';
import { useForexPrices } from '../hooks/useForexPrices';
import { useMarketSentiment } from '../hooks/useMarketSentiment.js';
import { usePredictionMarkets } from '../hooks/usePredictionMarkets.js';
import { useCentralBankDocuments } from '../hooks/useCentralBankDocuments.js';
import LiveNewsFeed from './LiveNewsFeed';
import { config } from '../config';
import { formatTimeForTimezone, getUserTimezone, getTimezoneAbbreviation } from '../utils/timezoneUtils';
import './Overview.css';
import EconomicChartPopup from './EconomicChartPopup.jsx';
import InfoIcon from './InfoIcon.jsx';

const Overview = () => {
  // Helper function to capitalize sentiment values
  const capitalizeSentiment = (value) => {
    return value.charAt(0).toUpperCase() + value.slice(1);
  };

  // Improved parsing helper functions for AI analysis metrics
  const parseRiskLevel = (riskLevel) => {
    if (!riskLevel) return { value: 'Moderate', class: 'neutral' };
    const lower = riskLevel.toLowerCase();
    // Check for high/elevated risk indicators
    if (/\b(high|elevated|significant|substantial|extreme|severe)\b/.test(lower)) {
      return { value: 'Strong', class: 'bearish' };
    }
    // Check for low/minimal risk indicators
    if (/\b(low|minimal|minor|slight|negligible)\b/.test(lower)) {
      return { value: 'Weak', class: 'bullish' };
    }
    // Default to moderate/medium
    return { value: 'Moderate', class: 'neutral' };
  };

  const parseVolatility = (volatility) => {
    if (!volatility) return { value: 'Medium', class: 'neutral' };
    const lower = volatility.toLowerCase();
    // Check for high volatility indicators
    if (/\b(high|elevated|significant|spike|surge|extreme|volatile)\b/.test(lower)) {
      return { value: 'High', class: 'bearish' };
    }
    // Check for low volatility indicators
    if (/\b(low|minimal|calm|stable|quiet|subdued)\b/.test(lower)) {
      return { value: 'Low', class: 'bullish' };
    }
    // Default to medium/moderate
    return { value: 'Medium', class: 'neutral' };
  };

  const parseMarketBias = (marketBias) => {
    if (!marketBias) return { value: 'Neutral', class: 'neutral' };
    const lower = marketBias.toLowerCase();
    // Check for bullish indicators
    if (/\b(bullish|positive|upward|rising|strengthening|optimistic|favorable)\b/.test(lower)) {
      return { value: 'Bullish', class: 'bullish' };
    }
    // Check for bearish indicators
    if (/\b(bearish|negative|downward|falling|weakening|pessimistic|unfavorable)\b/.test(lower)) {
      return { value: 'Bearish', class: 'bearish' };
    }
    // Default to neutral
    return { value: 'Neutral', class: 'neutral' };
  };

  // Helper function to safely convert any value to a string for rendering
  // Prevents React errors when objects are accidentally rendered
  const safeRenderValue = (value) => {
    if (value === null || value === undefined) return '';
    // If it's already a string, return it
    if (typeof value === 'string') return value;
    // If it's a number, convert to string
    if (typeof value === 'number') return String(value);
    // If it's a boolean, convert to string
    if (typeof value === 'boolean') return String(value);
    // If it's an array, join it
    if (Array.isArray(value)) {
      return value.map(item => safeRenderValue(item)).join(', ');
    }
    // If it's an object, format it nicely
    if (typeof value === 'object' && value !== null) {
      const entries = Object.entries(value);
      if (entries.length === 0) return '';
      // Format as "Key1: value1, Key2: value2"
      return entries.map(([key, val]) => {
        const formattedVal = safeRenderValue(val);
        return `${key}: ${formattedVal}`;
      }).join(', ');
    }
    // Fallback: convert to string
    return String(value);
  };

  // Helper function specifically for positioning context values
  const safePositioningValue = (value) => {
    return safeRenderValue(value);
  };

  // Helper function to parse numeric values from strings (handles "55.2", "55.2%", "-2.5K", etc.)
  const parseNumericValue = (value) => {
    if (!value || value === 'N/A' || value === '' || value === null || value === undefined) {
      return null;
    }
    
    // Handle string values like "55.2", "55.2%", "-2.5K", "200K", etc.
    const cleaned = String(value).replace(/[^\d.-]/g, '');
    const parsed = parseFloat(cleaned);
    
    return isNaN(parsed) ? null : parsed;
  };

  // Determine event type and direction mapping
  // Returns: { higherIsBullish: boolean, eventType: string }
  const getEventDirectionMapping = (eventTitle) => {
    if (!eventTitle) return { higherIsBullish: true, eventType: 'unknown' };
    
    const titleLower = eventTitle.toLowerCase();
    
    // IMPORTANT: Check more specific patterns first to avoid conflicts
    
    // Unemployment indicators - Higher = Bearish, Lower = Bullish
    // Check this BEFORE employment to avoid conflicts
    if (titleLower.includes('unemployment') || 
        titleLower.includes('jobless') ||
        titleLower.includes('jobless claims') ||
        titleLower.includes('initial claims') ||
        titleLower.includes('continuing claims') ||
        titleLower.includes('unemployment rate') ||
        titleLower.includes('unemployment claims')) {
      return { higherIsBullish: false, eventType: 'unemployment' };
    }
    
    // Wage/Earnings indicators - Higher = Bearish (inflationary pressure), Lower = Bullish
    if (titleLower.includes('wage') ||
        titleLower.includes('average earnings') ||
        titleLower.includes('earnings growth') ||
        titleLower.includes('hourly earnings') ||
        titleLower.includes('wage growth')) {
      return { higherIsBullish: false, eventType: 'wages' };
    }
    
    // Inflation/CPI indicators - Higher = Bearish (inflationary), Lower = Bullish
    // Check this early to avoid conflicts with other indicators
    if (titleLower.includes('cpi') ||
        titleLower.includes('consumer price index') ||
        titleLower.includes('consumer price') ||
        titleLower.includes('inflation') ||
        titleLower.includes('ppi') ||
        titleLower.includes('producer price index') ||
        titleLower.includes('producer price') ||
        titleLower.includes('core inflation') ||
        titleLower.includes('core cpi')) {
      return { higherIsBullish: false, eventType: 'inflation' };
    }
    
    // Employment indicators - Higher = Bullish, Lower = Bearish
    // Check after unemployment to avoid conflicts
    if (titleLower.includes('non-farm payrolls') ||
        titleLower.includes('nonfarm payrolls') ||
        titleLower.includes('nfp') ||
        titleLower.includes('adp employment') ||
        titleLower.includes('adp payrolls') ||
        titleLower.includes('payrolls') ||
        titleLower.includes('employment change') ||
        titleLower.includes('employment rate') ||
        titleLower.includes('job creation') ||
        titleLower.includes('jobs created') ||
        (titleLower.includes('employment') && !titleLower.includes('unemployment'))) {
      return { higherIsBullish: true, eventType: 'employment' };
    }
    
    // Interest Rate indicators - Higher = Bullish for currency, Lower = Bearish
    if (titleLower.includes('interest rate') ||
        titleLower.includes('rate decision') ||
        titleLower.includes('fed rate') ||
        titleLower.includes('ecb rate') ||
        titleLower.includes('boe rate') ||
        titleLower.includes('boj rate') ||
        titleLower.includes('rba rate') ||
        titleLower.includes('boc rate') ||
        titleLower.includes('snb rate') ||
        titleLower.includes('rbnz rate') ||
        titleLower.includes('cash rate') ||
        titleLower.includes('policy rate') ||
        titleLower.includes('monetary policy')) {
      return { higherIsBullish: true, eventType: 'interest_rate' };
    }
    
    // GDP indicators - Higher = Bullish, Lower = Bearish
    if (titleLower.includes('gdp') ||
        titleLower.includes('gross domestic product') ||
        titleLower.includes('economic growth') ||
        titleLower.includes('gdp growth') ||
        titleLower.includes('gdp qoq') ||
        titleLower.includes('gdp yoy')) {
      return { higherIsBullish: true, eventType: 'gdp' };
    }
    
    // Trade Balance - Higher = Bullish (surplus), Lower = Bearish (deficit)
    // Note: Trade deficit is negative, so "higher" (less negative) = Bullish
    if (titleLower.includes('trade balance') ||
        titleLower.includes('trade surplus') ||
        titleLower.includes('trade deficit') ||
        titleLower.includes('current account') ||
        titleLower.includes('balance of trade')) {
      return { higherIsBullish: true, eventType: 'trade_balance' };
    }
    
    // Retail Sales - Higher = Bullish, Lower = Bearish
    if (titleLower.includes('retail sales') ||
        titleLower.includes('consumer spending') ||
        titleLower.includes('retail trade')) {
      return { higherIsBullish: true, eventType: 'retail_sales' };
    }
    
    // Manufacturing/Industrial - Higher = Bullish, Lower = Bearish
    if (titleLower.includes('manufacturing') ||
        titleLower.includes('industrial production') ||
        titleLower.includes('factory orders') ||
        titleLower.includes('durable goods') ||
        titleLower.includes('industrial output')) {
      return { higherIsBullish: true, eventType: 'manufacturing' };
    }
    
    // PMI indicators - Higher = Bullish (above 50), Lower = Bearish (below 50)
    if (titleLower.includes('pmi') ||
        titleLower.includes('purchasing managers index') ||
        titleLower.includes('purchasing managers')) {
      return { higherIsBullish: true, eventType: 'pmi' };
    }
    
    // Housing indicators - Higher = Bullish, Lower = Bearish
    if (titleLower.includes('home sales') ||
        titleLower.includes('housing starts') ||
        titleLower.includes('building permits') ||
        titleLower.includes('new home sales') ||
        titleLower.includes('existing home sales') ||
        titleLower.includes('house price') ||
        titleLower.includes('housing market')) {
      return { higherIsBullish: true, eventType: 'housing' };
    }
    
    // Consumer Confidence/Sentiment - Higher = Bullish, Lower = Bearish
    if (titleLower.includes('consumer confidence') ||
        titleLower.includes('consumer sentiment') ||
        titleLower.includes('business confidence') ||
        titleLower.includes('business sentiment') ||
        titleLower.includes('sentiment index')) {
      return { higherIsBullish: true, eventType: 'confidence' };
    }
    
    // Budget/Government Finance - Higher surplus = Bullish, Higher deficit = Bearish
    // Note: Budget deficit is negative, so "higher" (less negative) = Bullish
    if (titleLower.includes('budget balance') ||
        titleLower.includes('budget surplus') ||
        titleLower.includes('budget deficit') ||
        titleLower.includes('government budget')) {
      return { higherIsBullish: true, eventType: 'budget' };
    }
    
    // Business Inventories - Higher = Bearish (oversupply), Lower = Bullish
    if (titleLower.includes('business inventories') ||
        titleLower.includes('inventory') ||
        titleLower.includes('stockpiles')) {
      return { higherIsBullish: false, eventType: 'inventories' };
    }
    
    // Personal Income/Spending - Higher = Bullish, Lower = Bearish
    if (titleLower.includes('personal income') ||
        titleLower.includes('personal spending') ||
        titleLower.includes('personal consumption')) {
      return { higherIsBullish: true, eventType: 'personal' };
    }
    
    // Default: assume higher is bullish (most economic indicators)
    return { higherIsBullish: true, eventType: 'default' };
  };

  // Helper function to format value with unit (preserves % or other units from original)
  const formatValueWithUnit = (value, originalExpected) => {
    if (!originalExpected || originalExpected === 'N/A') {
      return String(value);
    }
    
    // Check if original has a % sign
    const hasPercent = String(originalExpected).includes('%');
    // Check if original has other units (K, M, B, etc.)
    const unitMatch = String(originalExpected).match(/[KMkmBb]/);
    const unit = unitMatch ? unitMatch[0].toUpperCase() : '';
    
    // Format the number
    const formattedValue = Math.round(value * 100) / 100;
    
    // Add unit if present
    if (hasPercent) {
      return `${formattedValue}%`;
    } else if (unit) {
      return `${formattedValue}${unit}`;
    }
    return String(formattedValue);
  };

  // Calculate market scenarios based on actual vs expected with event-specific logic
  const calculateMarketScenarios = (eventSummary, eventTitle) => {
    const expected = parseNumericValue(eventSummary?.expected);
    const originalExpected = eventSummary?.expected || '';
    
    // If we don't have an expected value, we can't calculate scenarios
    if (expected === null) {
      return null;
    }
    
    const directionMapping = getEventDirectionMapping(eventTitle);
    const { higherIsBullish } = directionMapping;
    
    const scenarios = {
      above: [],
      onForecast: [],
      below: []
    };
    
    // Format forecast value (no < or >)
    const forecastValue = formatValueWithUnit(expected, originalExpected);
    
    // Simple scenarios: Just show above/below forecast with appropriate sentiment
    // No made-up multipliers - just show what happens if actual is above or below expected
    if (higherIsBullish) {
      // Higher values are bullish (e.g., GDP, Employment, Retail Sales)
      // Above forecast = Bullish
      scenarios.above.push({
        value: `>${forecastValue}`,
        sentiment: 'Bullish',
        sentimentClass: 'bullish'
      });
      
      // Below forecast = Bearish
      scenarios.below.push({
        value: `<${forecastValue}`,
        sentiment: 'Bearish',
        sentimentClass: 'bearish'
      });
    } else {
      // Higher values are bearish (e.g., Unemployment, CPI)
      // Above forecast = Bearish
      scenarios.above.push({
        value: `>${forecastValue}`,
        sentiment: 'Bearish',
        sentimentClass: 'bearish'
      });
      
      // Below forecast = Bullish
      scenarios.below.push({
        value: `<${forecastValue}`,
        sentiment: 'Bullish',
        sentimentClass: 'bullish'
      });
    }
    
    // On forecast scenario (neutral/ranging) - show forecast value without < or >
    scenarios.onForecast.push({
      value: forecastValue,
      sentiment: 'Ranging',
      sentimentClass: 'ranging'
    });
    
    return scenarios;
  };

  // Helper function to clean up old cache entries
  const cleanupOldCache = () => {
    try {
      const keysToRemove = [];
      const maxCacheAge = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds
      
      // Iterate through localStorage keys
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('economic_calendar_')) {
          try {
            const data = JSON.parse(localStorage.getItem(key));
            const cacheAge = Date.now() - data.timestamp;
            
            // Remove entries older than 7 days
            if (cacheAge > maxCacheAge) {
              keysToRemove.push(key);
            }
          } catch (e) {
            // Invalid cache entry, mark for removal
            keysToRemove.push(key);
          }
        }
      }
      
      // Remove old entries
      keysToRemove.forEach(key => {
        localStorage.removeItem(key);
        console.log(`🗑️ Removed old cache entry: ${key}`);
      });
      
      if (keysToRemove.length > 0) {
        console.log(`🗑️ Cleaned up ${keysToRemove.length} old cache entries`);
      }
    } catch (e) {
      console.warn('⚠️ Failed to cleanup old cache:', e);
    }
  };

  const [isEditing, setIsEditing] = useState(false);
  const [selectedPairs, setSelectedPairs] = useState([]);
  const [preferencesLoaded, setPreferencesLoaded] = useState(false);
  const [isTickerEditing, setIsTickerEditing] = useState(false);
  const [selectedTickerPairs, setSelectedTickerPairs] = useState([]);
  const [isCalendarModalOpen, setIsCalendarModalOpen] = useState(false);
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isVixContextExpanded, setIsVixContextExpanded] = useState(false);
  
  // AI Analysis state
  const [aiAnalysisState, setAiAnalysisState] = useState('default'); // 'default', 'pending', 'loading', 'event-analysis', 'error'
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  
  // Calendar state
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedDateRange, setSelectedDateRange] = useState({
    start: new Date(),
    end: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000) // 2 weeks from today
  });
  const [quickSelectOption, setQuickSelectOption] = useState('this-month');
  const [isSelectingRange, setIsSelectingRange] = useState(false);
  const [rangeStartDate, setRangeStartDate] = useState(null);
  
  // Filter state
  const [filterImpactLevels, setFilterImpactLevels] = useState({
    high: true,
    medium: true,
    low: true
  });
  const [filterCurrencies, setFilterCurrencies] = useState({
    USD: true,
    EUR: true,
    GBP: true,
    JPY: true,
    AUD: true,
    CAD: true,
    CHF: true,
    NZD: true,
    CNY: true
  });
  
  const { prices, loading, error } = useForexPrices();
  const { 
    sentiment, 
    loading: sentimentLoading, 
    error: sentimentError, 
    lastUpdate,
    refreshSentiment, 
    getConditionValue, 
    getConditionPercentage, 
    getPairSentiment, 
    getSentimentColor, 
    formatTimeAgo 
  } = useMarketSentiment();

  // Prediction Markets hook
  const {
    markets: predictionMarkets,
    summary: predictionMarketsSummary,
    loading: predictionMarketsLoading,
    error: predictionMarketsError,
    lastUpdate: predictionMarketsLastUpdate,
    refresh: refreshPredictionMarkets
  } = usePredictionMarkets();

  // Central Bank Documents hook
  const {
    documents: centralBankDocuments,
    loading: centralBankDocumentsLoading,
    error: centralBankDocumentsError,
    refresh: refreshCentralBankDocuments
  } = useCentralBankDocuments();

  // Timezone state
  const [currentTimezone, setCurrentTimezone] = useState(() => {
    const tz = getUserTimezone();
    console.log('🌍 Initial timezone:', tz);
    return tz;
  });

  // Central Bank Documents filter state
  const [cbSearchQuery, setCbSearchQuery] = useState('');
  const [cbFilterBank, setCbFilterBank] = useState('all');
  const [cbFilterType, setCbFilterType] = useState('all');
  const [cbFilterImpact, setCbFilterImpact] = useState('all');

  // Format last updated time
  const formatLastUpdated = (timestamp) => {
    if (!timestamp) return '';
    const now = new Date();
    const diffMs = now - timestamp;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  // Format economic calendar time
  const formatCalendarTime = (timeStr, dateStr) => {
    try {
      // Backend sends: time="14:30 UTC", date="2025-10-06" (YYYY-MM-DD)
      const timeMatch = timeStr.match(/(\d{1,2}):(\d{2})\s*UTC/);
      
      if (!timeMatch) {
        console.log('⚠️ Time format not matched:', timeStr);
        return { time: timeStr, date: dateStr };
      }
      
      const hour = parseInt(timeMatch[1]);
      const minute = timeMatch[2];
      
      // Parse date - backend sends YYYY-MM-DD format
      let utcDate;
      
      // Try YYYY-MM-DD format first (what backend actually sends)
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        // Backend format: "2025-10-06"
        utcDate = new Date(`${dateStr}T${String(hour).padStart(2, '0')}:${minute}:00.000Z`);
      } 
      // Fallback to old format if needed (Mon, Oct 6)
      else {
        const dateMatch = dateStr.match(/(\w{3}),\s*(\w{3})\s*(\d{1,2})/);
        if (!dateMatch) {
          console.log('⚠️ Date format not matched:', dateStr);
          return { time: timeStr, date: dateStr };
        }
        
        const month = dateMatch[2];
        const day = dateMatch[3];
        const currentYear = new Date().getFullYear();
        const monthMap = {
          'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
          'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
        };
        
        const monthIndex = monthMap[month];
        if (monthIndex === undefined) {
          console.log('⚠️ Invalid month:', month);
          return { time: timeStr, date: dateStr };
        }
        
        const utcDateString = `${currentYear}-${String(monthIndex + 1).padStart(2, '0')}-${String(parseInt(day)).padStart(2, '0')}T${String(hour).padStart(2, '0')}:${minute}:00.000Z`;
        utcDate = new Date(utcDateString);
      }
      
      // Convert to user's timezone
      if (currentTimezone !== 'UTC') {
        const convertedTime = utcDate.toLocaleTimeString('en-US', {
          timeZone: currentTimezone,
          hour12: false,
          hour: '2-digit',
          minute: '2-digit'
        });
        
        const convertedDate = utcDate.toLocaleDateString('en-US', {
          timeZone: currentTimezone,
          weekday: 'short',
          month: 'short',
          day: 'numeric'
        });
        
        const tzAbbr = getTimezoneAbbreviation(currentTimezone);
        console.log('✅ Converted:', { 
          original: `${timeStr} on ${dateStr}`, 
          converted: `${convertedTime} ${tzAbbr} on ${convertedDate}`,
          timezone: currentTimezone 
        });
        
        return {
          time: `${convertedTime} ${tzAbbr}`,
          date: convertedDate
        };
      }
      
      // If timezone is UTC, format the date nicely but keep UTC
      const formattedDate = utcDate.toLocaleDateString('en-US', {
        timeZone: 'UTC',
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      });
      
      return { time: timeStr, date: formattedDate };
      
    } catch (error) {
      console.error('❌ Error formatting calendar time:', error);
      return { time: timeStr, date: dateStr };
    }
  };

  // Listen for timezone changes
  useEffect(() => {
    const checkTimezone = () => {
      const newTimezone = getUserTimezone();
      if (newTimezone !== currentTimezone) {
        console.log('🌍 Timezone changed (from check):', { old: currentTimezone, new: newTimezone });
        setCurrentTimezone(newTimezone);
      }
    };

    const timezoneInterval = setInterval(checkTimezone, 1000);
    
    const handleTimezoneChange = (e) => {
      console.log('🌍 Timezone changed (from event):', { old: currentTimezone, new: e.detail.timezone });
      setCurrentTimezone(e.detail.timezone);
    };

    window.addEventListener('timezoneChanged', handleTimezoneChange);
    
    return () => {
      clearInterval(timezoneInterval);
      window.removeEventListener('timezoneChanged', handleTimezoneChange);
    };
  }, [currentTimezone]);

  // Economic calendar state
  const [economicEvents, setEconomicEvents] = useState([]);
  const [calendarLoading, setCalendarLoading] = useState(true);
  const [calendarError, setCalendarError] = useState(null);
  const [calendarSource, setCalendarSource] = useState('loading');
  const [lastUpdated, setLastUpdated] = useState(null);

  // Chart popup state
  const [chartPopupOpen, setChartPopupOpen] = useState(false);
  const [selectedChartEvent, setSelectedChartEvent] = useState(null);

  // Economic Calendar Button Handlers
  const handleDatePicker = () => {
    setIsCalendarModalOpen(true);
  };

  const handleFilter = () => {
    console.log('🔄 Opening filter modal');
    setIsFilterModalOpen(true);
  };

  // Chart popup handlers
  const handleChartClick = (event) => {
    console.log('🔍 Chart clicked for event:', event);
    console.log('🔍 Event title:', event.title);
    setSelectedChartEvent(event);
    setChartPopupOpen(true);
  };

  const handleCloseChart = () => {
    setChartPopupOpen(false);
    setSelectedChartEvent(null);
  };

  // Cleanup old cache on mount
  useEffect(() => {
    cleanupOldCache();
  }, []);

  // Fetch economic calendar data
  useEffect(() => {
    fetchEconomicCalendar();
  }, [selectedDateRange]);

  // Auto-refresh calendar data every 5 minutes to get updated status and new events
  useEffect(() => {
    const autoRefreshInterval = setInterval(() => {
      console.log('🔄 Auto-refreshing calendar data...');
      fetchEconomicCalendar();
    }, 5 * 60 * 1000); // 5 minutes

    // Cleanup interval on unmount
    return () => clearInterval(autoRefreshInterval);
  }, []);

  // Real-time status updates every minute (for events that are about to become imminent/completed)
  useEffect(() => {
    const statusUpdateInterval = setInterval(() => {
      // Force re-render to update status indicators
      setEconomicEvents(prevEvents => [...prevEvents]);
    }, 60 * 1000); // 1 minute

    return () => clearInterval(statusUpdateInterval);
  }, []);

  // Auto-refresh when fallback data is detected
  useEffect(() => {
    if (calendarSource === 'fallback_data' && !isRefreshing) {
      console.log('🔄 Fallback data detected, triggering automatic refresh...');
      // Add a small delay to avoid immediate refresh loops
      setTimeout(() => {
        handleRefresh();
      }, 2000); // 2 second delay
    }
  }, [calendarSource, isRefreshing]);

  const fetchEconomicCalendar = async () => {
    try {
      // Format dates for API request
      const startDate = selectedDateRange.start.toISOString().split('T')[0];
      const endDate = selectedDateRange.end.toISOString().split('T')[0];
      const cacheKey = `economic_calendar_${startDate}_${endDate}`;
      
      // Check localStorage cache first
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        try {
          const parsed = JSON.parse(cachedData);
          const cacheAge = Date.now() - parsed.timestamp;
          const maxCacheAge = 6 * 60 * 60 * 1000; // 6 hours in milliseconds
          
          if (cacheAge < maxCacheAge) {
            console.log(`📋 Using cached calendar data (age: ${(cacheAge / 3600000).toFixed(1)}h)`);
            setEconomicEvents(parsed.events);
            setCalendarSource(parsed.source + ' (cached)');
            setLastUpdated(new Date(parsed.timestamp));
            setCalendarLoading(false);
            setCalendarError(null);
            // Continue to fetch fresh data in background
          } else {
            console.log(`⚠️ Cache expired (age: ${(cacheAge / 3600000).toFixed(1)}h)`);
          }
        } catch (e) {
          console.warn('⚠️ Failed to parse cached data:', e);
        }
      }
      
      // Always fetch fresh data
      setCalendarLoading(true);
      setCalendarError(null);
      
      const url = `${config.endpoints.economicCalendar}?start_date=${startDate}&end_date=${endDate}`;
      console.log(`📅 Fetching fresh calendar data for ${startDate} to ${endDate}`);
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (response.ok && data.events) {
        setEconomicEvents(data.events);
        setCalendarSource(data.source || 'API');
        
        // Cache the fresh data in localStorage
        try {
          const cacheData = {
            events: data.events,
            source: data.source,
            timestamp: Date.now()
          };
          localStorage.setItem(cacheKey, JSON.stringify(cacheData));
          console.log(`💾 Cached ${data.events.length} events to localStorage`);
        } catch (e) {
          console.warn('⚠️ Failed to cache data to localStorage:', e);
        }
        
        // Debug logging
        console.log(`📊 Received ${data.events.length} events from ${data.source}`);
        
        if (data.demo_api_limitations) {
          console.warn('⚠️ Demo API limitations detected');
        }
        if (data.historical_events_filtered > 0) {
          console.warn(`⚠️ ${data.historical_events_filtered} historical events filtered`);
        }
        
        console.log(`✅ Fetched ${data.events.length} economic events from ${data.source}`);
        setLastUpdated(new Date());
      } else {
        throw new Error(data.message || 'Failed to fetch economic calendar');
      }
    } catch (error) {
      console.error('❌ Error fetching economic calendar:', error);
      setCalendarError(error.message);
      setCalendarSource('error');
    } finally {
      setCalendarLoading(false);
    }
  };

  // Filter economic events based on current filter settings
  const getFilteredEvents = () => {
    if (!economicEvents.length) return [];
    
    const filtered = economicEvents.filter(event => {
      // First, filter by date range to ensure events are from the correct year
      const eventDate = getEventDateFromRawData(event);
      if (!eventDate) {
        console.log(`⚠️ Event "${event.title}" has no valid date data`);
        return false;
      }
      
      const startDate = selectedDateRange.start.toISOString().split('T')[0];
      const endDate = selectedDateRange.end.toISOString().split('T')[0];
      
      // Check if event date is within the selected range
      const isInDateRange = eventDate >= startDate && eventDate <= endDate;
      if (!isInDateRange) {
        console.log(`❌ Event "${event.title}" (${eventDate}) not in date range ${startDate} to ${endDate}`);
        return false;
      }
      
      // Filter by impact level - handle case sensitivity
      const eventImpact = event.impact?.toLowerCase();
      const impactMatch = filterImpactLevels[eventImpact] || false;
      
      // Filter by currency
      const currencyMatch = filterCurrencies[event.currency] || false;
      

      
      // Event passes if all filters match
      return isInDateRange && impactMatch && currencyMatch;
    });
    
    // Sort events by date and time (earliest first)
    const sortedEvents = filtered.sort((a, b) => {
      const dateA = getEventDateTime(a);
      const dateB = getEventDateTime(b);
      return dateA - dateB;
    });
    
    return sortedEvents;
  };

  // Helper function to extract event date from raw data
  const getEventDateFromRawData = (event) => {
    try {
      // First try direct date field (for FRED events)
      if (event.date) {
        return event.date;
      }
      
      // Fallback to raw_data for legacy events
      const rawData = event.raw_data;
      if (!rawData) return null;
      
      const eventTime = rawData.time;
      if (!eventTime) return null;
      
      // Parse the event datetime from the raw data
      if (eventTime.includes(' ') && eventTime.length > 10) {
        // Format: "2025-08-15 00:15:00" - extract date part
        return eventTime.split(' ')[0]; // Just get "2025-08-15"
      } else if (rawData.date && eventTime) {
        // Format: "2025-08-15" and "00:15"
        return rawData.date;
      }
      
      return null;
    } catch (error) {
      console.error(`❌ Error parsing date for event ${event.title}:`, error);
      return null;
    }
  };

  // Helper function to extract event date and time for sorting
  const getEventDateTime = (event) => {
    try {
      const rawData = event.raw_data;
      if (!rawData || !rawData.time) {
        return new Date(0); // Return epoch date for invalid events
      }
      
      if (rawData.time.includes(' ') && rawData.time.length > 10) {
        // Format: "2025-08-13 00:00:00" - parse as UTC to avoid timezone issues
        const [datePart, timePart] = rawData.time.split(' ');
        const [year, month, day] = datePart.split('-').map(Number);
        const [hour, minute, second] = timePart.split(':').map(Number);
        
        // Create date in UTC to avoid timezone conversion issues
        return new Date(Date.UTC(year, month - 1, day, hour, minute, second || 0));
      } else if (rawData.date && rawData.time) {
        // Format: "2025-08-13" and "13:30"
        const dateTimeStr = `${rawData.date} ${rawData.time}`;
        return new Date(dateTimeStr);
      }
      
      return new Date(0); // Return epoch date for invalid events
    } catch (error) {
      console.error(`❌ Error parsing event datetime for ${event.title}:`, error);
      return new Date(0);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await fetchEconomicCalendar();
      console.log('🔄 Calendar data refreshed');
    } catch (error) {
      console.error('❌ Error refreshing calendar data:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCloseCalendarModal = () => {
    setIsCalendarModalOpen(false);
  };

  const handleCloseFilterModal = () => {
    console.log('🔄 Closing filter modal');
    setIsFilterModalOpen(false);
  };

  // Calendar utility functions
  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const getLastDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDay();
  };

  const formatDate = (date) => {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December'];
    return `${months[date.getMonth()]} ${date.getFullYear()}`;
  };

  const formatDateRange = (startDate, endDate) => {
    if (!startDate || !endDate) return 'No date selected';
    
    const formatSingleDate = (date) => {
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
    };
    
    if (startDate.toDateString() === endDate.toDateString()) {
      return formatSingleDate(startDate);
    } else {
      return `${formatSingleDate(startDate)} - ${formatSingleDate(endDate)}`;
    }
  };

  const isSameDay = (date1, date2) => {
    return date1.getDate() === date2.getDate() && 
           date1.getMonth() === date2.getMonth() && 
           date1.getFullYear() === date2.getFullYear();
  };

  const isToday = (date) => {
    return isSameDay(date, new Date());
  };

  const isInDateRange = (date, startDate, endDate) => {
    if (!startDate || !endDate) return false;
    return date >= startDate && date <= endDate;
  };

  const generateCalendarDays = (date) => {
    const daysInMonth = getDaysInMonth(date);
    const firstDay = getFirstDayOfMonth(date);
    const lastDay = getLastDayOfMonth(date);
    
    const days = [];
    
    // Previous month days
    const prevMonth = new Date(date.getFullYear(), date.getMonth() - 1, 0);
    const prevMonthDays = getDaysInMonth(prevMonth);
    for (let i = firstDay - 1; i >= 0; i--) {
      const day = new Date(date.getFullYear(), date.getMonth() - 1, prevMonthDays - i);
      days.push({ date: day, type: 'prev-month' });
    }
    
    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      const day = new Date(date.getFullYear(), date.getMonth(), i);
      days.push({ date: day, type: 'current-month' });
    }
    
    // Next month days - ensure we have exactly 42 days total (6 rows x 7 days)
    const totalDays = days.length;
    const nextMonthDaysNeeded = 42 - totalDays;
    for (let i = 1; i <= nextMonthDaysNeeded; i++) {
      const day = new Date(date.getFullYear(), date.getMonth() + 1, i);
      days.push({ date: day, type: 'next-month' });
    }
    
    return days;
  };

  // Calendar navigation handlers
  const handlePrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const handlePrevYear = () => {
    setCurrentDate(new Date(currentDate.getFullYear() - 1, currentDate.getMonth(), 1));
  };

  const handleNextYear = () => {
    setCurrentDate(new Date(currentDate.getFullYear() + 1, currentDate.getMonth(), 1));
  };

  // Date selection handlers
  const handleDateClick = (day) => {
    console.log('📅 Date clicked:', day.date.toDateString(), 'Type:', day.type);
    
    // Clear quick select option when manually selecting a date
    setQuickSelectOption('custom');
    
    if (isSelectingRange) {
      // Range selection mode
      if (!rangeStartDate) {
        // First click - set start date
        setRangeStartDate(day.date);
        setSelectedDate(day.date);
        console.log('📅 Range start date set:', day.date.toDateString());
      } else {
        // Second click - set end date and complete range
        const start = rangeStartDate < day.date ? rangeStartDate : day.date;
        const end = rangeStartDate < day.date ? day.date : rangeStartDate;
        
        setSelectedDateRange({ start, end });
        setSelectedDate(start);
        setRangeStartDate(null);
        setIsSelectingRange(false);
        console.log('📅 Range selection completed:', start.toDateString(), 'to', end.toDateString());
      }
    } else {
      // Single date selection mode
      setSelectedDate(day.date);
      const newDateRange = {
        start: day.date,
        end: day.date
      };
      setSelectedDateRange(newDateRange);
      console.log('📅 Updated date range:', newDateRange.start.toDateString(), 'to', newDateRange.end.toDateString());
    }
  };

  const toggleRangeSelection = () => {
    setIsSelectingRange(!isSelectingRange);
    if (isSelectingRange) {
      // Cancel range selection
      setRangeStartDate(null);
    } else {
      // Starting range selection - clear quick select option
      setQuickSelectOption('custom');
    }
  };

  const resetCalendarSelection = () => {
    const today = new Date();
    setSelectedDate(today);
    setSelectedDateRange({ start: today, end: today });
    setQuickSelectOption('today');
    setRangeStartDate(null);
    setIsSelectingRange(false);
    console.log('🔄 Calendar selection reset to today');
  };

  // Quick select handlers
  const handleQuickSelect = (option) => {
    console.log('📅 Quick select option:', option);
    setQuickSelectOption(option);
    const today = new Date();
    let startDate, endDate;

    switch (option) {
      case 'today':
        startDate = new Date(today);
        endDate = new Date(today);
        break;
      case 'yesterday':
        startDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
        endDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
        break;
      case 'tomorrow':
        startDate = new Date(today.getTime() + 24 * 60 * 60 * 1000);
        endDate = new Date(today.getTime() + 24 * 60 * 60 * 1000);
        break;
      case 'this-week':
        const dayOfWeek = today.getDay();
        startDate = new Date(today.getTime() - dayOfWeek * 24 * 60 * 60 * 1000);
        endDate = new Date(startDate.getTime() + 6 * 24 * 60 * 60 * 1000);
        break;
      case 'last-week':
        const dayOfWeekLast = today.getDay();
        const lastWeekStart = new Date(today.getTime() - (dayOfWeekLast + 7) * 24 * 60 * 60 * 1000);
        startDate = lastWeekStart;
        endDate = new Date(lastWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000);
        break;
      case 'next-week':
        const dayOfWeekNext = today.getDay();
        const nextWeekStart = new Date(today.getTime() + (7 - dayOfWeekNext) * 24 * 60 * 60 * 1000);
        startDate = nextWeekStart;
        endDate = new Date(nextWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000);
        break;
      case 'this-month':
        startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        break;
      case 'last-month':
        startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        endDate = new Date(today.getFullYear(), today.getMonth(), 0);
        break;
      case 'next-month':
        startDate = new Date(today.getFullYear(), today.getMonth() + 1, 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 2, 0);
        break;
      default:
        startDate = today;
        endDate = today;
    }

    setSelectedDateRange({ start: startDate, end: endDate });
    
    // Clear manual date selection by setting selectedDate to the start date of the range
    // This ensures the calendar grid shows the correct selected date for the quick select option
    setSelectedDate(startDate);
    
    // Clear any range selection state
    setRangeStartDate(null);
    setIsSelectingRange(false);
    
    console.log('📅 Quick select date range:', startDate.toDateString(), 'to', endDate.toDateString());
    console.log('📅 Updated selected date to match quick select:', startDate.toDateString());
  };

  // Save preferences and close modal
  const handleSaveDateSelection = () => {
    // Ensure we have a valid date range
    const finalDateRange = {
      start: selectedDateRange.start,
      end: selectedDateRange.end
    };
    
    // If no date range is set, use the selected date
    if (!finalDateRange.start || !finalDateRange.end) {
      finalDateRange.start = selectedDate;
      finalDateRange.end = selectedDate;
    }
    
    // Save to localStorage
    const preferences = {
      selectedDate: selectedDate.toISOString(),
      selectedDateRange: {
        start: finalDateRange.start.toISOString(),
        end: finalDateRange.end.toISOString()
      },
      quickSelectOption: quickSelectOption,
      lastUpdated: new Date().toISOString()
    };
    
    localStorage.setItem('fxSentinel_calendarPreferences', JSON.stringify(preferences));
    console.log('💾 Calendar preferences saved:', preferences);
    
    // Update the state with the final date range
    setSelectedDateRange(finalDateRange);
    
    // Close modal
    setIsCalendarModalOpen(false);
    
    // Show loading state and refresh calendar data with new date range
    setCalendarLoading(true);
    fetchEconomicCalendar().finally(() => {
      setCalendarLoading(false);
      console.log('🔄 Calendar data refreshed with new date range');
    });
  };

  // Filter handlers
  const handleImpactLevelToggle = (level) => {
    setFilterImpactLevels(prev => ({
      ...prev,
      [level.toLowerCase()]: !prev[level.toLowerCase()]
    }));
  };

  const handleCurrencyToggle = (currency) => {
    setFilterCurrencies(prev => ({
      ...prev,
      [currency]: !prev[currency]
    }));
  };

  const handleSelectAllImpact = () => {
    setFilterImpactLevels({
      high: true,
      medium: true,
      low: true
    });
  };

  const handleSelectAllCurrencies = () => {
    setFilterCurrencies({
      USD: true,
      EUR: true,
      GBP: true,
      JPY: true,
      AUD: true,
      CAD: true,
      CHF: true,
      NZD: true,
      CNY: true
    });
  };

  const handleClearAllImpact = () => {
    setFilterImpactLevels({
      high: false,
      medium: false,
      low: false
    });
  };

  const handleClearAllCurrencies = () => {
    setFilterCurrencies({
      USD: false,
      EUR: false,
      GBP: false,
      JPY: false,
      AUD: false,
      CAD: false,
      CHF: false,
      NZD: false,
      CNY: false
    });
  };

  // Save filter preferences and close modal
  const handleSaveFilterPreferences = () => {
    // Save to localStorage
    const filterPreferences = {
      impactLevels: filterImpactLevels,
      currencies: filterCurrencies,
      lastUpdated: new Date().toISOString()
    };
    
    localStorage.setItem('fxSentinel_filterPreferences', JSON.stringify(filterPreferences));
    
    // Close modal
    setIsFilterModalOpen(false);
    
    // Show brief loading state to indicate filter is being applied
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
    }, 500);
  };

  // Helper function to check if filters are at default state
  const areFiltersAtDefault = () => {
    const defaultImpactLevels = { high: true, medium: true, low: true };
    const defaultCurrencies = { USD: true, EUR: true, GBP: true, JPY: true, AUD: true, CAD: true, CHF: true, NZD: true, CNY: true };
    
    const impactMatch = JSON.stringify(filterImpactLevels) === JSON.stringify(defaultImpactLevels);
    const currencyMatch = JSON.stringify(filterCurrencies) === JSON.stringify(defaultCurrencies);
    
    return impactMatch && currencyMatch;
  };

  // Reset filters to default state
  const handleResetFilters = () => {
    setFilterImpactLevels({
      high: true,
      medium: true,
      low: true
    });
    setFilterCurrencies({
      USD: true,
      EUR: true,
      GBP: true,
      JPY: true,
      AUD: true,
      CAD: true,
      CHF: true,
      NZD: true,
      CNY: true
    });
  };

  const handleCurrencyPair = (pair) => {
    console.log(`💱 Currency pair ${pair} clicked - would navigate to ${pair} charts`);
    // In a real implementation, this would navigate to currency pair charts
  };

  const handleChartView = (eventTitle) => {
    console.log(`📊 Chart button clicked for ${eventTitle} - would open detailed charts`);
    // In a real implementation, this would open detailed charts for the event
  };

  // AI Analysis handlers
  const handleEventClick = async (event) => {
    console.log(`🎯 Event clicked: ${event.title}`);
    setSelectedEvent(event);
    setAiAnalysisState('pending'); // Set to pending instead of immediately loading
    // Don't call API yet - wait for user confirmation
  };

  const handleConfirmAnalysis = async () => {
    if (!selectedEvent) return;
    
    console.log(`✅ User confirmed analysis for: ${selectedEvent.title}`);
    setAiAnalysisState('loading');
    
    try {
      // Generate real AI analysis
      const analysis = await generateEventAnalysis(selectedEvent);
      setAiAnalysis(analysis);
      setAiAnalysisState('event-analysis');
    } catch (error) {
      console.error('❌ Error generating AI analysis:', error);
      setAiAnalysisState('error');
    }
  };

  const handleClearAnalysis = () => {
    setSelectedEvent(null);
    setAiAnalysis(null);
    setAiAnalysisState('default');
  };

  const generateEventAnalysis = async (event) => {
    console.log('🦒🦒🦒 FRONTEND: generateEventAnalysis function called 🦒🦒🦒');
    console.log('🦒 Event received:', event);
    try {
      console.log('🤖 Generating comprehensive AI analysis for event:', event);
      
      // Determine if this is pre-event or post-event analysis based on actual data availability
      const hasActualData = event.actual && event.actual !== 'N/A' && event.actual !== '' && event.actual !== null;
      const isPostEvent = hasActualData;
      
      console.log(`📊 Analysis type: ${isPostEvent ? 'POST-EVENT' : 'PRE-EVENT'} (Actual data: ${event.actual || 'Not available'})`);
      
      // Call our enhanced AI analysis endpoint with proper structure
      console.log('🦄🦄🦄 FRONTEND: About to call enhanced-analysis endpoint 🦄🦄🦄');
      console.log('🦄 Config endpoints backend:', config.endpoints.backend);
      console.log('🦄 Event object:', event);
      console.log('🦄 Event ID:', event.id);
      console.log('🦄 Event Title:', event.title);
      console.log('🦄 URL:', `${config.endpoints.backend}/api/enhanced-analysis/${event.id}`);
      
      const response = await fetch(`${config.endpoints.backend}/api/enhanced-analysis/${event.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: event,
          analysisType: isPostEvent ? 'post-event' : 'pre-event',
          marketContext: {
            currentTime: new Date().toISOString(),
            eventTime: new Date().toISOString(),
            isPostEvent: isPostEvent
          }
        })
      });
      
      console.log('🐸🐸🐸 FRONTEND: Fetch response received 🐸🐸🐸');
      console.log('🐸 Response status:', response.status);
      console.log('🐸 Response ok:', response.ok);
      
      if (!response.ok) {
        console.log('🦒🦒🦒 FRONTEND: HTTP error occurred 🦒🦒🦒');
        console.log('🦒 Error status:', response.status);
        const errorText = await response.text();
        console.log('🦒 Error text:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const analysis = await response.json();
      console.log('🦊🦊🦊 FRONTEND: Analysis JSON parsed successfully 🦊🦊🦊');
      console.log('🦊 Comprehensive AI analysis received:', analysis);
      console.log('🦊 Headline from backend:', analysis.headline);
      console.log('🦊 Key Takeaway from backend:', analysis.key_takeaway);
      console.log('🦊 Forward Scenarios from backend:', analysis.forward_scenarios);
      
      // Debug: Log the actual content from new enhanced structure
      console.log('🐨🐨🐨 Frontend Debug - Enhanced Structure Content 🐨🐨🐨');
      console.log('🐨 Event Summary:', analysis.eventSummary);
      console.log('🐨 Market Reaction:', analysis.market_reaction);
      console.log('🐨 Implications Takeaways:', analysis.implications_takeaways);
      console.log('🐨 Key Takeaway:', analysis.key_takeaway);
      console.log('🐨 Forward Scenarios:', analysis.forward_scenarios);
      console.log('🐨 Trading Plan:', analysis.trading_plan);
      console.log('🐨 Big Picture:', analysis.big_picture);
      // console.log('🐨 Positioning Context:', analysis.positioning_context); // Removed - positioning context no longer used
      console.log('🐨 Next Catalysts:', analysis.next_catalysts);
      console.log('🐨 Sample Event Summary:', JSON.stringify(analysis.eventSummary || {}).substring(0, 200) || 'No content');
      console.log('🐨 Sample Market Reaction:', JSON.stringify(analysis.market_reaction || {}).substring(0, 200) || 'No content');
      console.log('🐨 Sample Key Takeaway:', analysis.key_takeaway || 'No content');
      
      // Transform the backend response to work with new enhanced structure
      return {
        event: event,
        analysisType: isPostEvent ? 'post-event' : 'pre-event',
        
        // Event Summary - New detailed structure
        eventSummary: analysis.eventSummary || {
          release: event.title,
          date_time: (() => {
            // Handle different date/time formats from news items
            if (event.date && event.time) {
              return `${event.date} ${event.time}`;
            } else if (event.published_at) {
              // Convert published_at to date/time format
              const date = new Date(event.published_at);
              const dateStr = date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
              const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
              return `${dateStr}, ${timeStr}`;
            } else if (analysis.event?.date && analysis.event?.time) {
              return `${analysis.event.date} ${analysis.event.time}`;
            } else {
              return 'Not specified';
            }
          })(),
          previous: event.previous || analysis.event?.previous || 'N/A',
          expected: event.expected || analysis.event?.expected || 'N/A',
          actual: event.actual || analysis.event?.actual || 'N/A',
          outcome: 'Analysis based on expected vs previous data'
        },
        
        // Professional Analysis Sections
        professionalSummary: analysis.summary || 'Professional summary not available',
        professionalMarketImpact: analysis.market_impact || 'Market impact analysis not available',
        professionalPolicyContext: analysis.policy_context || 'Policy context not available',
        professionalTradingView: analysis.trading_view || 'Trading view not available',
        professionalBigPicture: analysis.big_picture || 'Big picture analysis not available',
        
        // Market Reaction - New streamlined structure
        market_reaction: analysis.market_reaction || {
          price_action: `Expected price movements in ${event.currency} pairs will depend on the actual data versus expectations.`,
          volatility: 'Medium volatility expected around the release',
          reason: 'Market reaction will be driven by the comparison between actual and expected data'
        },
        
        // Implications and Takeaways - New streamlined structure
        implications_takeaways: analysis.implications_takeaways || {
          economic_context: 'Economic context analysis based on the indicator type and current conditions',
          policy_implications: 'Policy implications will depend on the data outcome',
          market_positioning: 'Market positioning analysis based on current sentiment',
          event_bias: 'Neutral - depends on actual vs expected data',
          sentiment: 'Market sentiment will shift based on surprise factor',
          risk_level: 'Medium - typical volatility around economic releases'
        },
        
        // Trading Plan - New streamlined structure
        trading_plan: analysis.trading_plan || {
          best_approach: 'Range trading with breakout potential based on surprise factor',
          key_levels: 'Monitor key support and resistance levels around current price',
          position_sizing: 'Conservative position sizing due to potential volatility',
          avoid_strategies: 'Avoid aggressive positioning before data release',
          next_catalysts: 'Focus on upcoming central bank meetings and related economic data',
          support_levels: ['Key support levels to be determined'],
          resistance_levels: ['Key resistance levels to be determined'],
          best_setup: 'Range trading with breakout potential',
          position_sizing_risk: 'Conservative'
        },
        
        // Big Picture - New streamlined structure
        big_picture: analysis.big_picture || {
          economic_outlook: `The data will provide insights into ${event.currency} economic health`,
          policy_trajectory: 'Central bank policy trajectory will be influenced by the data outcome',
          medium_term_direction: `Medium-term ${event.currency} direction will depend on policy implications`,
          forward_focus: 'Monitor for follow-up data releases and central bank communications',
          policy_impact: 'Policy implications will be determined by the data outcome',
          risk_assessment: 'Medium'
        },
        
        // Quick-scan elements (NEW)
        headline: analysis.headline || `📊 ${event.title} Analysis`,
        key_takeaway: analysis.key_takeaway || 'Analysis based on current market conditions',
        forward_scenarios: analysis.forward_scenarios || {
          bullish: '✅ Above key resistance: potential move higher on positive data surprise',
          bearish: '❌ Below key support: potential move lower on negative data surprise',
          neutral: 'Range likely between key support and resistance if no breakout.'
        },
        
        // Enhanced positioning context (NEW)
        positioning_context: analysis.positioning_context || {
          retail_sentiment: 'Retail positioning analysis based on current market conditions',
          institutional_flow: 'Institutional money flow analysis',
          market_bias: 'Overall market bias based on positioning'
        },
        next_catalysts: analysis.next_catalysts || [
          'Central bank meetings and CPI releases',
          'Economic data releases',
          'Policy announcements'
        ],
        
        // Confidence and metadata
        confidence_score: analysis.confidence_score || 75,
        analysis_timestamp: analysis.analysis_timestamp || new Date().toISOString(),
        analysis_type: analysis.analysis_type || (isPostEvent ? 'post-event' : 'pre-event'),
        model_used: analysis.model_used || 'gpt_ai_analyzer',
        cache_hit: analysis.cache_hit || false
      };
      
      // Debug: Log the transformed data structure
      console.log('🔍 Frontend Debug - Transformed Data Structure:');
      console.log('   Transformed Data:', returnObject);
      console.log('🔍 Headline in return object:', returnObject.headline);
      console.log('🔍 Key Takeaway in return object:', returnObject.key_takeaway);
      console.log('🔍 Forward Scenarios in return object:', returnObject.forward_scenarios);
      
      return returnObject;
      
    } catch (error) {
      console.log('🦁🦁🦁 FRONTEND: Error in generateEventAnalysis 🦁🦁🦁');
      console.log('🦁 Error message:', error.message);
      console.log('🦁 Error stack:', error.stack);
      console.error('🦁 Error generating comprehensive AI analysis:', error);
      
      // Fallback to basic analysis if enhanced fails
      try {
        const basicResponse = await fetch(`${config.endpoints.backend}/api/analysis/${event.id}`);
        if (basicResponse.ok) {
          const basicAnalysis = await basicResponse.json();
          return {
            event: event,
            analysisType: 'pre-event',
            generalOverview: {
              eventExplanation: basicAnalysis.summary || 'Basic economic analysis',
              marketLogic: 'Market impact assessment',
              impactLevel: event.impact || 'Medium'
            },
            immediateImpact: {
              direction: 'Sideways',
              magnitude: 'Medium',
              affectedPairs: [event.currency + 'USD'],
              confidence: parseInt(basicAnalysis.confidence?.replace('%', '') || '70')
            },
            expectationsAnalysis: {
              pricedInPercentage: 60,
              surprisePotential: 'Medium',
              historicalContext: 'Historical context available'
            },
            tradingFramework: {
              keyLevels: {
                support: ['Support 1', 'Support 2'],
                resistance: ['Resistance 1', 'Resistance 2']
              },
              timing: {
                avoidTrading: '30 min before to 30 min after',
                bestSetup: '1-2 hours after release',
                monitoringStart: '1 hour before'
              }
            },
            bigPicture: {
              policyImplications: 'Central bank policy impact',
              narrativeShift: 'Market story changes',
              riskLevel: 'Medium'
            },
            sentiment: 'neutral',
            marketConfidence: 'Medium',
            confidenceScore: parseInt(basicAnalysis.confidence?.replace('%', '') || '70'),
            predictions: [
              {
                type: 'positive',
                icon: '🎯',
                text: basicAnalysis.summary || 'Basic analysis available'
              }
            ],
            insights: [
              {
                type: 'positive',
                icon: '🤖',
                text: 'Basic AI analysis completed'
              }
            ],
            tradingOpportunities: []
          };
        }
      } catch (basicError) {
        console.error('🐯🐯🐯 Basic analysis also failed:', basicError);
      }
      
      // Final fallback - return comprehensive structure
      console.log('🦘🦘🦘 FRONTEND: Using final fallback data 🦘🦘🦘');
      return {
        event: event,
        analysisType: 'pre-event',
        generalOverview: {
          eventExplanation: 'Analysis temporarily unavailable',
          marketLogic: 'Market impact assessment',
          impactLevel: event.impact || 'Medium'
        },
        immediateImpact: {
          direction: 'Sideways',
          magnitude: 'Medium',
          affectedPairs: [event.currency + 'USD'],
          confidence: 60
        },
        expectationsAnalysis: {
          pricedInPercentage: 60,
          surprisePotential: 'Medium',
          historicalContext: 'Historical context unavailable'
        },
        tradingFramework: {
          keyLevels: {
            support: ['Support 1', 'Support 2'],
            resistance: ['Resistance 1', 'Resistance 2']
          },
          timing: {
            avoidTrading: '30 min before to 30 min after',
            bestSetup: '1-2 hours after release',
            monitoringStart: '1 hour before'
          }
        },
        bigPicture: {
          policyImplications: 'Policy implications analysis',
          narrativeShift: 'Market story analysis',
          riskLevel: 'Medium'
        },
        sentiment: 'neutral',
        marketConfidence: 'Low',
        confidenceScore: 60,
        predictions: [
          {
            type: 'negative',
            icon: '⚠️',
            text: 'Analysis temporarily unavailable'
          }
        ],
        insights: [
          {
            type: 'negative',
            icon: '📊',
            text: 'Please try again later'
          }
        ],
        tradingOpportunities: []
      };
    }
  };

  const handleRefreshAI = async () => {
    if (selectedEvent) {
      setAiAnalysisState('loading');
      try {
        const analysis = await generateEventAnalysis(selectedEvent);
        setAiAnalysis(analysis);
        setAiAnalysisState('event-analysis');
      } catch (error) {
        console.error('❌ Error refreshing AI analysis:', error);
        setAiAnalysisState('error');
      }
    }
  };

  // Default pairs (only used if no saved preferences exist)
  const defaultPairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD'];

  // Load user preferences from localStorage on component mount
  useEffect(() => {
    try {
      const savedPairs = localStorage.getItem('fxSentinel_selectedPairs');
      if (savedPairs) {
        const parsed = JSON.parse(savedPairs);
        if (Array.isArray(parsed) && parsed.length > 0 && parsed.length <= 5) {
          setSelectedPairs(parsed);
          console.log('✅ Loaded saved preferences:', parsed);
        } else {
          console.log('⚠️ Invalid saved preferences, using defaults');
          setSelectedPairs(defaultPairs);
        }
      } else {
        console.log('📝 No saved preferences found, using defaults');
        setSelectedPairs(defaultPairs);
      }
    } catch (error) {
      console.error('❌ Error loading saved pairs:', error);
      console.log('🔄 Falling back to default pairs');
      setSelectedPairs(defaultPairs);
    } finally {
      setPreferencesLoaded(true);
    }
  }, []);

  // Load ticker preferences from localStorage on component mount
  useEffect(() => {
    try {
      const savedTickerPairs = localStorage.getItem('fxSentinel_selectedTickerPairs');
      if (savedTickerPairs) {
        const parsed = JSON.parse(savedTickerPairs);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setSelectedTickerPairs(parsed);
          console.log('✅ Loaded saved ticker preferences:', parsed);
        } else {
          console.log('⚠️ Invalid saved ticker preferences, using defaults');
          setSelectedTickerPairs(['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']);
        }
      } else {
        console.log('📝 No saved ticker preferences found, using defaults');
        setSelectedTickerPairs(['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']);
      }
    } catch (error) {
      console.error('❌ Error loading saved ticker pairs:', error);
      console.log('🔄 Falling back to default ticker pairs');
      setSelectedTickerPairs(['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']);
    }
  }, []);

  // Helper function to calculate date range for quick select options
  const calculateDateRangeForOption = (option) => {
    const today = new Date();
    let startDate, endDate;

    switch (option) {
      case 'today':
        startDate = new Date(today);
        endDate = new Date(today);
        break;
      case 'yesterday':
        startDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
        endDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
        break;
      case 'tomorrow':
        startDate = new Date(today.getTime() + 24 * 60 * 60 * 1000);
        endDate = new Date(today.getTime() + 24 * 60 * 60 * 1000);
        break;
      case 'this-week':
        const dayOfWeek = today.getDay();
        startDate = new Date(today.getTime() - dayOfWeek * 24 * 60 * 60 * 1000);
        endDate = new Date(startDate.getTime() + 6 * 24 * 60 * 60 * 1000);
        break;
      case 'last-week':
        const dayOfWeekLast = today.getDay();
        const lastWeekStart = new Date(today.getTime() - (dayOfWeekLast + 7) * 24 * 60 * 60 * 1000);
        startDate = lastWeekStart;
        endDate = new Date(lastWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000);
        break;
      case 'next-week':
        const dayOfWeekNext = today.getDay();
        const nextWeekStart = new Date(today.getTime() + (7 - dayOfWeekNext) * 24 * 60 * 60 * 1000);
        startDate = nextWeekStart;
        endDate = new Date(nextWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000);
        break;
      case 'this-month':
        startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        break;
      case 'last-month':
        startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        endDate = new Date(today.getFullYear(), today.getMonth(), 0);
        break;
      case 'next-month':
        startDate = new Date(today.getFullYear(), today.getMonth() + 1, 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 2, 0);
        break;
      default:
        // Default to this week for unknown options
        const dayOfWeekDefault = today.getDay();
        startDate = new Date(today.getTime() - dayOfWeekDefault * 24 * 60 * 60 * 1000);
        endDate = new Date(startDate.getTime() + 6 * 24 * 60 * 60 * 1000);
    }

    return { start: startDate, end: endDate };
  };

  // Load calendar preferences from localStorage on component mount
  useEffect(() => {
    try {
      const savedCalendarPrefs = localStorage.getItem('fxSentinel_calendarPreferences');
      if (savedCalendarPrefs) {
        const parsed = JSON.parse(savedCalendarPrefs);
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Reset time to start of day for comparison
        
        let shouldUseSavedPrefs = false;
        let finalDateRange = null;
        let finalQuickSelectOption = parsed.quickSelectOption || 'this-month';

        // Check if saved preferences have a quick select option
        if (parsed.quickSelectOption) {
          const relativeOptions = ['this-week', 'this-month', 'next-week', 'next-month', 'today', 'tomorrow'];
          
          // If it's a relative option, always recalculate based on current date
          if (relativeOptions.includes(parsed.quickSelectOption)) {
            console.log(`🔄 Recalculating relative date range for: ${parsed.quickSelectOption}`);
            finalDateRange = calculateDateRangeForOption(parsed.quickSelectOption);
            shouldUseSavedPrefs = true;
            console.log(`✅ Recalculated date range: ${finalDateRange.start.toDateString()} to ${finalDateRange.end.toDateString()}`);
          } else if (parsed.selectedDateRange) {
            // For custom ranges or absolute dates, check if they're still relevant
            const savedStart = new Date(parsed.selectedDateRange.start);
            const savedEnd = new Date(parsed.selectedDateRange.end);
            savedStart.setHours(0, 0, 0, 0);
            savedEnd.setHours(0, 0, 0, 0);
            
            // Check if saved range is in the past (end date is before today)
            if (savedEnd < today) {
              console.log('⚠️ Saved date range is in the past, resetting to this week');
              finalQuickSelectOption = 'this-week';
              finalDateRange = calculateDateRangeForOption('this-week');
              shouldUseSavedPrefs = true;
            } else {
              // Range is still current or future, use it
              finalDateRange = {
                start: savedStart,
                end: savedEnd
              };
              shouldUseSavedPrefs = true;
              console.log('✅ Using saved date range (still current):', savedStart.toDateString(), 'to', savedEnd.toDateString());
            }
          }
        } else if (parsed.selectedDateRange) {
          // No quick select option but has date range - check if outdated
          const savedStart = new Date(parsed.selectedDateRange.start);
          const savedEnd = new Date(parsed.selectedDateRange.end);
          savedStart.setHours(0, 0, 0, 0);
          savedEnd.setHours(0, 0, 0, 0);
          
          if (savedEnd < today) {
            console.log('⚠️ Saved date range is in the past, resetting to this week');
            finalQuickSelectOption = 'this-week';
            finalDateRange = calculateDateRangeForOption('this-week');
            shouldUseSavedPrefs = true;
          } else {
            finalDateRange = {
              start: savedStart,
              end: savedEnd
            };
            shouldUseSavedPrefs = true;
          }
        }

        if (shouldUseSavedPrefs && finalDateRange) {
          // Set the calculated/validated date range
          setSelectedDateRange(finalDateRange);
          setSelectedDate(finalDateRange.start);
          setQuickSelectOption(finalQuickSelectOption);
          console.log('✅ Loaded and validated calendar preferences');
        } else {
          // No valid preferences, use defaults
          console.log('📝 No valid saved calendar preferences found, using defaults');
        }
      } else {
        console.log('📝 No saved calendar preferences found, using defaults');
      }
    } catch (error) {
      console.error('❌ Error loading saved calendar preferences:', error);
      console.log('🔄 Falling back to default calendar preferences');
    }
  }, []);

  // Load filter preferences from localStorage on component mount
  useEffect(() => {
    try {
      const savedFilterPrefs = localStorage.getItem('fxSentinel_filterPreferences');
      if (savedFilterPrefs) {
        const parsed = JSON.parse(savedFilterPrefs);
        if (parsed.impactLevels && parsed.currencies) {
          setFilterImpactLevels(parsed.impactLevels);
          setFilterCurrencies(parsed.currencies);
          console.log('✅ Loaded saved filter preferences:', parsed);
        }
      } else {
        console.log('📝 No saved filter preferences found, using defaults');
      }
    } catch (error) {
      console.error('❌ Error loading saved filter preferences:', error);
      console.log('🔄 Falling back to default filter preferences');
    }
  }, []);



  // Save user preferences to localStorage whenever selectedPairs changes
  useEffect(() => {
    if (preferencesLoaded && selectedPairs.length > 0) {
      try {
        localStorage.setItem('fxSentinel_selectedPairs', JSON.stringify(selectedPairs));
        console.log('💾 Saved preferences to localStorage:', selectedPairs);
      } catch (error) {
        console.error('❌ Error saving preferences:', error);
      }
    }
  }, [selectedPairs, preferencesLoaded]);

  // Save ticker preferences to localStorage whenever selectedTickerPairs changes
  useEffect(() => {
    if (selectedTickerPairs.length > 0) {
      try {
        localStorage.setItem('fxSentinel_selectedTickerPairs', JSON.stringify(selectedTickerPairs));
        console.log('💾 Saved ticker preferences to localStorage:', selectedTickerPairs);
      } catch (error) {
        console.error('❌ Error saving ticker preferences:', error);
      }
    }
  }, [selectedTickerPairs]);

  // All available forex pairs
  const allPairs = [
    { key: 'EURUSD', label: 'EUR/USD' },
    { key: 'GBPUSD', label: 'GBP/USD' },
    { key: 'USDJPY', label: 'USD/JPY' },
    { key: 'USDCHF', label: 'USD/CHF' },
    { key: 'AUDUSD', label: 'AUD/USD' },
    { key: 'USDCAD', label: 'USD/CAD' },
    { key: 'NZDUSD', label: 'NZD/USD' },
    { key: 'EURGBP', label: 'EUR/GBP' },
    { key: 'EURJPY', label: 'EUR/JPY' },
    { key: 'GBPJPY', label: 'GBP/JPY' },
    { key: 'USDSEK', label: 'USD/SEK' },
    { key: 'USDNOK', label: 'USD/NOK' },
    { key: 'USDHKD', label: 'USD/HKD' },
    { key: 'EURCHF', label: 'EUR/CHF' },
    { key: 'GBPCHF', label: 'GBP/CHF' }
  ];

  // Currently displayed pairs (max 5) - ordered by selection order
  const currencyPairs = allPairs.filter(pair => selectedPairs.includes(pair.key));

  // All available forex pairs for ticker
  const allTickerPairs = [
    { key: 'EURUSD', label: 'EUR/USD' },
    { key: 'GBPUSD', label: 'GBP/USD' },
    { key: 'USDJPY', label: 'USD/JPY' },
    { key: 'USDCHF', label: 'USD/CHF' },
    { key: 'AUDUSD', label: 'AUD/USD' },
    { key: 'USDCAD', label: 'USD/CAD' },
    { key: 'NZDUSD', label: 'NZD/USD' },
    { key: 'EURGBP', label: 'EUR/GBP' },
    { key: 'EURJPY', label: 'EUR/JPY' },
    { key: 'GBPJPY', label: 'GBP/JPY' },
    { key: 'USDSEK', label: 'USD/SEK' },
    { key: 'USDNOK', label: 'USD/NOK' },
    { key: 'USDHKD', label: 'USD/HKD' },
    { key: 'EURCHF', label: 'EUR/CHF' },
    { key: 'GBPCHF', label: 'GBP/CHF' }
  ];

  // Currently displayed ticker pairs - ordered by selection order
  const tickerPairs = selectedTickerPairs.map(pairKey => 
    allTickerPairs.find(pair => pair.key === pairKey)
  ).filter(Boolean);

  const handleEditClick = () => {
    setIsEditing(true);
  };

  const handleTickerEditClick = () => {
    setIsTickerEditing(true);
  };

  const handleCloseModal = () => {
    setIsEditing(false);
  };

  const handleCloseTickerModal = () => {
    setIsTickerEditing(false);
  };

  const handlePairToggle = (pairKey) => {
    setSelectedPairs(prev => {
      if (prev.includes(pairKey)) {
        // Remove pair
        const newPairs = prev.filter(key => key !== pairKey);
        console.log('🗑️ Removed pair:', pairKey, 'New order:', newPairs);
        return newPairs;
      } else {
        // Add pair (max 5) - add to the end to maintain order
        if (prev.length < 5) {
          const newPairs = [...prev, pairKey];
          console.log('➕ Added pair:', pairKey, 'New order:', newPairs);
          return newPairs;
        }
        console.log('⚠️ Maximum 5 pairs reached, cannot add:', pairKey);
        return prev; // Don't add if already at max
      }
    });
  };

  const handleTickerPairToggle = (pairKey) => {
    setSelectedTickerPairs(prev => {
      if (prev.includes(pairKey)) {
        // Remove pair
        const newPairs = prev.filter(key => key !== pairKey);
        console.log('🗑️ Removed ticker pair:', pairKey, 'New order:', newPairs);
        return newPairs;
      }
      const newPairs = [...prev, pairKey];
      console.log('➕ Added ticker pair:', pairKey, 'New order:', newPairs);
      return newPairs;
    });
  };

  const handleSaveChanges = () => {
    setIsEditing(false);
    console.log('💾 Changes saved! Current selection:', selectedPairs);
    // Preferences are automatically saved via useEffect
  };

  const handleSaveTickerChanges = () => {
    setIsTickerEditing(false);
    console.log('💾 Ticker changes saved! Current selection:', selectedTickerPairs);
    // Preferences are automatically saved via useEffect
  };

  // Helper function to reset to defaults
  const handleResetToDefaults = () => {
    setSelectedPairs(defaultPairs);
    console.log('🔄 Reset to default pairs:', defaultPairs);
  };

  // Helper function to reset ticker to defaults
  const handleResetTickerToDefaults = () => {
    setSelectedTickerPairs(['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']);
    console.log('🔄 Reset to default ticker pairs:', ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']);
  };


  // Helper functions for formatting
  const formatPrice = (price) => {
    if (!price) return '0.0000';
    return parseFloat(price).toFixed(4);
  };

  const formatChange = (change) => {
    if (!change) return '+0.0000';
    const num = parseFloat(change);
    return (num >= 0 ? '+' : '') + num.toFixed(4);
  };

  const formatPercentage = (change, price) => {
    if (!change || !price) return '+0.00%';
    const num = parseFloat(change);
    const percent = (num / parseFloat(price)) * 100;
    return (percent >= 0 ? '+' : '') + percent.toFixed(2) + '%';
  };

  const getChangeColor = (change) => {
    if (!change) return '#666';
    return parseFloat(change) >= 0 ? '#00ff88' : '#ff4757';
  };

  // Central Bank Documents filtering and helpers
  const getFilteredCentralBankDocuments = () => {
    if (!centralBankDocuments || centralBankDocuments.length === 0) {
      return [];
    }

    return centralBankDocuments.filter(doc => {
      // Search query filter
      if (cbSearchQuery) {
        const query = cbSearchQuery.toLowerCase();
        const matchesSearch = 
          doc.title.toLowerCase().includes(query) ||
          doc.description.toLowerCase().includes(query) ||
          doc.tags.some(tag => tag.toLowerCase().includes(query)) ||
          doc.centralBank.toLowerCase().includes(query);
        
        if (!matchesSearch) return false;
      }

      // Central bank filter
      if (cbFilterBank !== 'all' && doc.centralBank !== cbFilterBank) {
        return false;
      }

      // Type filter
      if (cbFilterType !== 'all' && doc.type !== cbFilterType) {
        return false;
      }

      // Impact filter
      if (cbFilterImpact !== 'all' && doc.impact !== cbFilterImpact) {
        return false;
      }

      return true;
    }).sort((a, b) => {
      // Sort by date (newest first)
      return new Date(b.date) - new Date(a.date);
    });
  };

  const getCentralBankName = (code) => {
    const banks = {
      'FED': 'Federal Reserve',
      'ECB': 'European Central Bank',
      'BOJ': 'Bank of Japan',
      'BOE': 'Bank of England',
      'RBA': 'Reserve Bank of Australia',
      'BOC': 'Bank of Canada',
      'SNB': 'Swiss National Bank',
      'RBNZ': 'Reserve Bank of New Zealand'
    };
    return banks[code] || code;
  };

  const getDocumentTypeLabel = (type) => {
    const types = {
      'meeting_minutes': 'Meeting Minutes',
      'speech': 'Speech',
      'report': 'Report',
      'cot_report': 'COT Report',
      'chart': 'Chart',
      'statement': 'Statement'
    };
    return types[type] || type;
  };

  const handleDocumentDownload = (doc) => {
    // Ensure filePath is absolute (starts with /)
    // This ensures PDFs work correctly in both development and production
    const filePath = doc.filePath.startsWith('/') 
      ? doc.filePath 
      : `/${doc.filePath}`;
    
    // Create a link element and trigger download/view
    const link = document.createElement('a');
    link.href = filePath;
    link.download = doc.fileName || doc.title;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatDocumentDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch (e) {
      return dateStr;
    }
  };



  return (
    <div className="overview-tab">
      <div className="overview-content">
        {/* Live Market Ticker */}
        <div className="market-ticker-container">
          <div className="market-ticker">
            {/* Edit Button */}
            <div className="ticker-edit-btn" onClick={handleTickerEditClick}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </div>

            {/* Currency Pairs */}
            <div className="ticker-pairs-inline">
              {loading ? (
                <span className="loading-pairs">Loading...</span>
              ) : (
                tickerPairs.map((pair, index) => {
                  const priceData = prices[pair.key];
                  const price = priceData?.price || '0.0000';
                  const change = priceData?.change || '0.0000';
                  const isUp = parseFloat(change) >= 0;

                  return (
                    <React.Fragment key={pair.key}>
                      <div className="ticker-pair-inline">
                        <span className="pair-label-inline">{pair.label}</span>
                        <span className={`pair-rate-inline ${isUp ? 'positive' : 'negative'}`}>
                          {formatPrice(price)}
                        </span>
                        <span className={`pair-change-inline ${isUp ? 'positive' : 'negative'}`}>
                          {formatChange(change)}
                        </span>
                        <span className={`pair-percentage-inline ${isUp ? 'positive' : 'negative'}`}>
                          {formatPercentage(change, price)}
                        </span>
                      </div>
                      {index < tickerPairs.length - 1 && (
                        <span className="pair-separator-inline">|</span>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </div>

            {/* Error indicator */}
            {error && (
              <span className="ticker-error" title={error}>
                ⚠️
              </span>
            )}
          </div>
        </div>

        {/* Cards Grid Container */}
        <div className="cards-grid-container">
          {/* Economic Calendar - Based on recovered structure */}
          <div className="news-calendar">
            <div className="calendar-header">
              <div className="header-main">
                <h2 className="calendar-title">ECONOMIC CALENDAR</h2>
              </div>
              <div className="calendar-controls">
                <button className="date-select-btn" onClick={handleDatePicker}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"></path>
                  </svg>
                </button>
                <button className={`filter-btn ${(() => {
                  const activeImpactLevels = Object.values(filterImpactLevels).filter(Boolean).length;
                  const activeCurrencies = Object.values(filterCurrencies).filter(Boolean).length;
                  return (activeImpactLevels < 3 || activeCurrencies < 8) ? 'active' : '';
                })()}`} onClick={handleFilter}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"></path>
                  </svg>
                </button>
                <button 
                  className={`calendar-refresh-btn ${isRefreshing ? 'refreshing' : ''}`} 
                  onClick={handleRefresh} 
                  disabled={isRefreshing}
                  title={`Refresh calendar data${lastUpdated ? ` (Last updated: ${formatLastUpdated(lastUpdated)})` : ''}`}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                  </svg>
                </button>
              </div>
            </div>
            <div className="calendar-content">
              {/* Filter status indicator */}
              <div className="filter-status">
                <div className="filter-info-grid">
                  <div className="filter-info-main">
                    <span className="events-count">
                      Showing <strong>{getFilteredEvents().length}</strong> events
                    </span>
                  </div>
                  <div className="filter-info-details">
                    {lastUpdated && (
                      <div className="info-item">
                        <span className="info-label">Updated:</span>
                        <span className="info-value">{formatLastUpdated(lastUpdated)}</span>
                      </div>
                    )}
                    <div className="info-item">
                      <span className="info-label">Date:</span>
                      <span className="info-value">{formatDateRange(selectedDateRange.start, selectedDateRange.end)}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Timezone:</span>
                      <span className="info-value">{getTimezoneAbbreviation(currentTimezone)}</span>
                    </div>
                  </div>
                </div>
                {/* Active filters indicator */}
                <div className="active-filters">
                  {(() => {
                    return null;
                  })()}
                </div>
                {calendarLoading && <span className="loading-indicator">Loading...</span>}
                {isRefreshing && <span className="filter-applying-indicator">Applying filters...</span>}
              </div>
              <div className="events-list">
                {getFilteredEvents().length > 0 ? (
                  getFilteredEvents().map((event, index) => (
                    <div 
                      key={`${event.id}-${currentTimezone}-${index}`}
                      className={`event-card impact-${event.impact} ${selectedEvent?.id === event.id ? 'selected' : ''}`}
                      onClick={() => handleEventClick(event)}
                    >
                    <div className="event-main-row">
                      <div className={`event-time impact-${event.impact}`}>
                        {(() => {
                          const formatted = formatCalendarTime(event.time, event.date);
                          return (
                            <>
                              <span className="time">{formatted.time}</span>
                              <span className="date">{formatted.date}</span>
                            </>
                          );
                        })()}
                      </div>
                      <div className="event-content">
                        <div className="event-header-row">
                          <h3 className="event-title">{event.title}</h3>
                          <div className="status-box">
                            <span className="currency-badge">{event.currency}</span>
                            <span className={`event-status-indicator ${(event.status || 'upcoming').toLowerCase()}`}>{event.status || 'Upcoming'}</span>
                          </div>
                        </div>
                        <div className="event-meta-row">
                          <span className="event-category">{event.type}</span>
                          <div className="affected-pairs">
                            {event.currencyPairs && event.currencyPairs.length > 0 ? (
                              <>
                                {event.currencyPairs.slice(0, 3).map((pair, pairIndex) => (
                                  <span key={pairIndex} className="pair-badge">{pair}</span>
                                ))}
                                {event.currencyPairs.length > 3 && (
                                  <span className="pair-badge pair-count">
                                    +{event.currencyPairs.length - 3} more
                                  </span>
                                )}
                              </>
                            ) : (
                              <span className="pair-badge no-pairs">No specific pairs</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="event-data">
                      <div className="data-point">
                        <span className="label">Actual:</span>
                        <span className="value">{event.actual}</span>
                      </div>
                      <div className="data-point">
                        <span className="label">Expected:</span>
                        <span className="value">{event.expected}</span>
                      </div>
                      <div className="data-point">
                        <span className="label">Previous:</span>
                        <span className="value">{event.previous}</span>
                      </div>
                      {/* Chart button commented out - opens chart popup for historical data points */}
                      {/* <div className="graph-icon" onClick={(e) => {
                        e.stopPropagation();
                        handleChartClick(event);
                      }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M3 3v18h18"></path>
                          <path d="M18 17V9"></path>
                          <path d="M13 17V5"></path>
                          <path d="M8 17v-3"></path>
                        </svg>
                      </div> */}
                    </div>
                  </div>
                ))
                ) : (
                  <div className="no-events-state">
                    <div className="no-events-icon">📅</div>
                    <div className="no-events-text">No events match your current filters</div>
                    <div className="no-events-subtext">
                      {(() => {
                        const activeImpactLevels = Object.entries(filterImpactLevels)
                          .filter(([level, active]) => active)
                          .map(([level]) => level);
                        
                        const activeCurrencies = Object.entries(filterCurrencies)
                          .filter(([currency, active]) => active)
                          .map(([currency]) => currency);
                        
                        if (activeImpactLevels.length === 0) {
                          return "No impact levels selected. Try selecting at least one impact level.";
                        } else if (activeCurrencies.length === 0) {
                          return "No currencies selected. Try selecting at least one currency.";
                        } else {
                          return "Try adjusting your filter settings to see more events";
                        }
                      })()}
                    </div>
                    <button className="reset-filters-btn" onClick={handleResetFilters}>
                      Reset Filters
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* AI Analysis Card */}
          <div className="ai-analysis-card">
            <div className="ai-header">
              <div className="header-main">
                <h2 className="ai-title">AI ANALYSIS</h2>
                <InfoIcon 
                  tooltipText="AI Analysis System: Our advanced machine learning algorithms process economic data and news events. The system analyzes historical patterns, market correlations, and economic relationships to provide trading insights. Analysis includes immediate market impact, trading implications, and confidence scores based on data quality and market conditions."
                  position="bottom"
                />
                {selectedEvent && (
                  <div className="selected-event-info">
                    <span className="event-name">{selectedEvent.title}</span>
                    <button className="clear-analysis-btn" onClick={handleClearAnalysis}>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M18 6L6 18M6 6L18 18"/>
                      </svg>
                    </button>
                  </div>
                )}
              </div>
              {/* AI Refresh button - commented out as it's not needed */}
              {/* <div className="ai-controls">
                <button className="ai-refresh-btn" onClick={handleRefreshAI}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                  </svg>
                </button>
              </div> */}
            </div>
            <div className="ai-content">
              {aiAnalysisState === 'loading' && (
                <div className="ai-loading-state">
                  <div className="loading-spinner"></div>
                  <div className="loading-text">Analyzing {selectedEvent?.title}...</div>
                  <div className="loading-subtext">Processing live market data, economic release forecast, and generating insights. EST: 15-60s. Good things take time.</div>
                </div>
              )}

              {aiAnalysisState === 'error' && (
                <div className="ai-error-state">
                  <div className="error-icon"></div>
                  <div className="error-text">Analysis failed</div>
                  <div className="error-subtext">Unable to generate AI analysis. Please try again.</div>
                  <button className="retry-btn" onClick={handleRefreshAI}>Retry Analysis</button>
                </div>
              )}

              {aiAnalysisState === 'event-analysis' && aiAnalysis && (
                <div>
                  {/* NEW: Quick-Scan Headline */}
                  <div className="quick-scan-headline">
                    <div className="headline-main">
                      <div className="headline-header-row">
                        <h3 className="headline-text">{aiAnalysis.headline || 'Economic Event Analysis'}</h3>
                        {selectedEvent?.currency && (
                          <div className="currency-bubble">
                            {selectedEvent.currency}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="key-takeaway">
                      {aiAnalysis.key_takeaway || 'Analysis based on current market conditions.'}
                    </div>
                  </div>

                  {/* AI Overview */}
                  <div className="ai-overview">
                    <div className="ai-indicator">
                      <div className="ai-label">Analysis Confidence</div>
                      <div className={`ai-value ${aiAnalysis.implications_takeaways?.market_bias?.toLowerCase().includes('bullish') ? 'bullish' : aiAnalysis.implications_takeaways?.market_bias?.toLowerCase().includes('bearish') ? 'bearish' : 'neutral'}`}>
                        {aiAnalysis.confidence_score ? `${aiAnalysis.confidence_score}%` : '85%'}
                      </div>
                      <div className="ai-bar">
                        <div className={`ai-fill ${aiAnalysis.implications_takeaways?.market_bias?.toLowerCase().includes('bullish') ? 'bullish' : aiAnalysis.implications_takeaways?.market_bias?.toLowerCase().includes('bearish') ? 'bearish' : 'neutral'}`} 
                             style={{width: `${aiAnalysis.confidence_score || 85}%`}}></div>
                      </div>
                    </div>
                    
                    <div className="ai-breakdown">
                      {(() => {
                        const eventImpact = parseRiskLevel(aiAnalysis.implications_takeaways?.risk_level);
                        const volatility = parseVolatility(aiAnalysis.market_reaction?.volatility);
                        const riskLevel = parseRiskLevel(aiAnalysis.implications_takeaways?.risk_level);
                        const marketSentiment = parseMarketBias(aiAnalysis.implications_takeaways?.market_bias);
                        
                        return (
                          <>
                            <div className="ai-item">
                              <span className="analysis-pair">{aiAnalysis.eventSummary?.release?.split(' ')[0] || 'Event'} Impact</span>
                              <span className={`analysis-score ${eventImpact.class}`}>
                                {eventImpact.value}
                              </span>
                            </div>
                            <div className="ai-item">
                              <span className="analysis-pair">Volatility</span>
                              <span className={`analysis-score ${volatility.class}`}>
                                {volatility.value}
                              </span>
                            </div>
                            <div className="ai-item">
                              <span className="analysis-pair">Risk Level</span>
                              <span className={`analysis-score ${riskLevel.class}`}>
                                {riskLevel.class === 'bearish' ? 'Elevated' : riskLevel.class === 'bullish' ? 'Low' : 'Normal'}
                              </span>
                            </div>
                            <div className="ai-item">
                              <span className="analysis-pair">Market Sentiment</span>
                              <span className={`analysis-score ${marketSentiment.class}`}>
                                {marketSentiment.value}
                              </span>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  </div>

                  {/* NEW: Forward Scenarios */}
                  <div className="forward-scenarios-section">
                    <h3 className="section-header">Forward Scenarios</h3>
                    {/* DEBUG: Log the actual aiAnalysis state */}
                    {console.log('🦘🦘🦘 FRONTEND DISPLAY DEBUG - aiAnalysis state 🦘🦘🦘', aiAnalysis)}
                    {console.log('🦘 Forward Scenarios:', aiAnalysis?.forward_scenarios)}
                    {/* Positioning Context removed - no longer displayed */}
                    <div className="scenarios-grid">
                      <div className="scenario bullish">
                        <div className="scenario-content">
                          <h4>Bullish</h4>
                          <p>{safeRenderValue(aiAnalysis.forward_scenarios?.bullish) || 'Above key resistance: potential move higher on positive data surprise'}</p>
                        </div>
                      </div>
                      <div className="scenario bearish">
                        <div className="scenario-content">
                          <h4>Bearish</h4>
                          <p>{safeRenderValue(aiAnalysis.forward_scenarios?.bearish) || 'Below key support: potential move lower on negative data surprise'}</p>
                        </div>
                      </div>
                      <div className="scenario neutral">
                        <div className="scenario-content">
                          <h4>Neutral</h4>
                          <p>{safeRenderValue(aiAnalysis.forward_scenarios?.neutral) || 'Range likely between key support and resistance if no breakout'}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Market Scenarios Section */}
                  {(() => {
                    const eventTitle = aiAnalysis.eventSummary?.release || selectedEvent?.title || '';
                    const marketScenarios = calculateMarketScenarios(aiAnalysis.eventSummary, eventTitle);
                    
                    if (!marketScenarios) {
                      return null; // Don't show if we can't calculate scenarios
                    }
                    
                    // Combine all scenarios into rows for table display
                    const scenarioRows = [
                      // Above rows
                      ...marketScenarios.above.map((scenario, index) => ({
                        category: index === 0 ? 'Above' : '',
                        categoryIcon: index === 0 ? 'above' : null,
                        value: scenario.value,
                        sentiment: scenario.sentiment,
                        sentimentClass: scenario.sentimentClass,
                        rowClass: scenario.sentimentClass.includes('bearish') ? 'bearish' : 'bullish'
                      })),
                      // On Forecast rows
                      ...marketScenarios.onForecast.map((scenario, index) => ({
                        category: index === 0 ? 'On forecast' : '',
                        categoryIcon: null,
                        value: scenario.value,
                        sentiment: scenario.sentiment,
                        sentimentClass: scenario.sentimentClass,
                        rowClass: 'neutral'
                      })),
                      // Below rows
                      ...marketScenarios.below.map((scenario, index) => ({
                        category: index === 0 ? 'Below' : '',
                        categoryIcon: index === 0 ? 'below' : null,
                        value: scenario.value,
                        sentiment: scenario.sentiment,
                        sentimentClass: scenario.sentimentClass,
                        rowClass: scenario.sentimentClass.includes('bullish') ? 'bullish' : 'bearish'
                      }))
                    ];
                    
                    return (
                      <div className="market-scenarios-section">
                        <h3 className="section-header">Market Scenarios</h3>
                        <div className="market-scenarios-table">
                          {scenarioRows.map((row, index) => (
                            <div key={index} className={`scenario-row ${row.rowClass}`}>
                              {/* Column 1: Category Label */}
                              <div className="scenario-column category-column">
                                {row.category && (
                                  <div className="category-label">
                                    {row.categoryIcon === 'above' && (
                                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="scenario-icon above-icon">
                                        <path d="M12 19V5M5 12l7-7 7 7"/>
                                      </svg>
                                    )}
                                    {row.categoryIcon === 'below' && (
                                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="scenario-icon below-icon">
                                        <path d="M12 5v14M19 12l-7 7-7-7"/>
                                      </svg>
                                    )}
                                    <span>{row.category}</span>
                                  </div>
                                )}
                              </div>
                              
                              {/* Column 2: Value */}
                              <div className="scenario-column value-column">
                                <span className={`scenario-value-box ${row.rowClass}`}>
                                  {row.value}
                                </span>
                              </div>
                              
                              {/* Column 3: Sentiment */}
                              <div className="scenario-column sentiment-column">
                                <span className={`scenario-sentiment ${row.sentimentClass}`}>
                                  {row.sentiment}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        {/* Currency Explanation Text */}
                        {(() => {
                          // Get currency from selectedEvent or from the event in aiAnalysis
                          const currency = selectedEvent?.currency || 
                                         aiAnalysis.event?.currency || 
                                         'Currency';
                          return (
                            <div className="market-scenarios-explanation">
                              <p className="scenarios-explanation-text">
                                For the <span className="currency-highlight">{currency}</span> Currency
                              </p>
                            </div>
                          );
                        })()}
                      </div>
                    );
                  })()}

                  {/* NEW: Positioning Context - REMOVED */}
                  {/* <div className="positioning-context-section">
                    <h3 className="section-header">Market Positioning</h3>
                    <div className="positioning-grid">
                      <div className="positioning-item">
                        <h4>Retail Sentiment</h4>
                        <p>{safePositioningValue(aiAnalysis.positioning_context?.retail_sentiment) || 'Retail positioning analysis based on current market conditions'}</p>
                      </div>
                      <div className="positioning-item">
                        <h4>Institutional Flow</h4>
                        <p>{safePositioningValue(aiAnalysis.positioning_context?.institutional_flow) || 'Institutional money flow analysis'}</p>
                      </div>
                      <div className="positioning-item">
                        <h4>Market Bias</h4>
                        <p>{safePositioningValue(aiAnalysis.positioning_context?.market_bias) || 'Overall market bias based on positioning'}</p>
                      </div>
                    </div>
                  </div> */}

                  {/* AI Analysis - Expandable Detailed Sections */}
                  <div className="ai-analysis-expandable">
                    {/* Event Summary - Expandable */}
                    <details className="analysis-details">
                      <summary className="details-summary">
                        {/* <span className="summary-icon"></span> */}
                        <span className="summary-title">Event Summary</span>
                        <span className="summary-arrow">▼</span>
                      </summary>
                      <div className="details-content">
                        <div className="event-summary-content">
                          <div className="event-summary-header">
                            <div className="event-summary-label">Event</div>
                            <div className="event-summary-value">{aiAnalysis.eventSummary?.release || 'Economic event analysis'}</div>
                          </div>
                          {aiAnalysis.eventSummary?.outcome && 
                           aiAnalysis.eventSummary.outcome !== 'Analysis based on expected vs previous data' && (
                            <div className="event-summary-header">
                              <div className="event-summary-label">Outcome</div>
                              <div className="event-summary-value">{aiAnalysis.eventSummary.outcome}</div>
                            </div>
                          )}
                          <div className="event-metrics-grid">
                            <div className="event-metric">
                              <div className="event-metric-label">Actual</div>
                              <div className="event-metric-value">{aiAnalysis.eventSummary?.actual || 'N/A'}</div>
                            </div>
                            <div className="event-metric">
                              <div className="event-metric-label">Expected</div>
                              <div className="event-metric-value">{aiAnalysis.eventSummary?.expected || 'N/A'}</div>
                            </div>
                            <div className="event-metric">
                              <div className="event-metric-label">Previous</div>
                              <div className="event-metric-value">{aiAnalysis.eventSummary?.previous || 'N/A'}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </details>

                    {/* Market Reaction - Expandable */}
                    <details className="analysis-details">
                      <summary className="details-summary">
                        {/* <span className="summary-icon"></span> */}
                        <span className="summary-title">Market Reaction</span>
                        <span className="summary-arrow">▼</span>
                      </summary>
                      <div className="details-content">
                        <div className="market-reaction-content">
                          {aiAnalysis.market_reaction?.price_action && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Price Action</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.market_reaction.price_action)}</div>
                            </div>
                          )}
                          {aiAnalysis.market_reaction?.volatility && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Volatility</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.market_reaction.volatility)}</div>
                            </div>
                          )}
                          {aiAnalysis.market_reaction?.reason && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Reason</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.market_reaction.reason)}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </details>

                    {/* Implications & Takeaways - Expandable */}
                    <details className="analysis-details">
                      <summary className="details-summary">
                        {/* <span className="summary-icon"></span> */}
                        <span className="summary-title">Implications & Takeaways</span>
                        <span className="summary-arrow">▼</span>
                      </summary>
                      <div className="details-content">
                        <div className="market-reaction-content">
                          {aiAnalysis.implications_takeaways?.economic_context && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Economic Context</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.implications_takeaways.economic_context)}</div>
                            </div>
                          )}
                          {aiAnalysis.implications_takeaways?.event_bias && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Market Bias</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.implications_takeaways.event_bias)}</div>
                            </div>
                          )}
                          {aiAnalysis.implications_takeaways?.risk_level && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Risk Level</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.implications_takeaways.risk_level)}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </details>

                    {/* Trading Plan - Expandable */}
                    <details className="analysis-details">
                      <summary className="details-summary">
                        {/* <span className="summary-icon"></span> */}
                        <span className="summary-title">Trading Plan</span>
                        <span className="summary-arrow">▼</span>
                      </summary>
                      <div className="details-content">
                        <div className="market-reaction-content">
                          {aiAnalysis.trading_plan?.best_approach && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Strategy</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.trading_plan.best_approach)}</div>
                            </div>
                          )}
                          {aiAnalysis.trading_plan?.avoid_strategies && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Risk Management</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.trading_plan.avoid_strategies)}</div>
                            </div>
                          )}
                          {aiAnalysis.trading_plan?.key_levels && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Key Levels</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.trading_plan.key_levels)}</div>
                            </div>
                          )}
                          {aiAnalysis.trading_plan?.position_sizing_risk && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Position Sizing</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.trading_plan.position_sizing_risk)}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </details>

                    {/* Big Picture - Expandable */}
                    <details className="analysis-details">
                      <summary className="details-summary">
                        {/* <span className="summary-icon"></span> */}
                        <span className="summary-title">Big Picture</span>
                        <span className="summary-arrow">▼</span>
                      </summary>
                      <div className="details-content">
                        <div className="market-reaction-content">
                          {aiAnalysis.big_picture?.economic_outlook && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Economic Outlook</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.big_picture.economic_outlook)}</div>
                            </div>
                          )}
                          {aiAnalysis.big_picture?.medium_term_direction && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Medium-term Direction</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.big_picture.medium_term_direction)}</div>
                            </div>
                          )}
                          {aiAnalysis.big_picture?.forward_focus && (
                            <div className="market-reaction-item">
                              <div className="market-reaction-label">Forward Focus</div>
                              <div className="market-reaction-value">{safeRenderValue(aiAnalysis.big_picture.forward_focus)}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </details>

                    {/* Next Catalysts - Expandable */}
                    <details className="analysis-details">
                      <summary className="details-summary">
                        {/* <span className="summary-icon"></span> */}
                        <span className="summary-title">Next Catalysts</span>
                        <span className="summary-arrow">▼</span>
                      </summary>
                      <div className="details-content">
                        <div className="catalysts-list">
                          {aiAnalysis.next_catalysts?.map((catalyst, index) => (
                            <div key={index} className="catalyst-item">
                              <span className="catalyst-icon"></span>
                              <span className="catalyst-text">{catalyst}</span>
                            </div>
                          )) || (
                            <div className="catalyst-item">
                              <span className="catalyst-icon"></span>
                              <span className="catalyst-text">Central bank meetings and CPI releases</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </details>
                  </div>
                </div>
              )}

              {aiAnalysisState === 'default' && (
                <div className="ai-default-message">
                  <div className="default-icon"></div>
                  <div className="default-text">Click on any economic event to get AI analysis</div>
                  <div className="default-subtext">Get specific insights and trading opportunities</div>
                </div>
              )}

              {aiAnalysisState === 'pending' && selectedEvent && (
                <div className="ai-pending-message">
                  <div className="default-icon"></div>
                  <div className="pending-text">
                    <div className="pending-event-title">{selectedEvent.title}</div>
                    <div className="pending-event-details">
                      {selectedEvent.date && selectedEvent.time && (
                        <div className="pending-detail-item">
                          <span className="pending-detail-label">Date & Time:</span>
                          <span className="pending-detail-value">
                            {(() => {
                              const formatted = formatCalendarTime(selectedEvent.time, selectedEvent.date);
                              return formatted.date && formatted.time 
                                ? `${formatted.date} at ${formatted.time}`
                                : selectedEvent.date && selectedEvent.time
                                ? `${selectedEvent.date} ${selectedEvent.time}`
                                : selectedEvent.date || selectedEvent.time || 'TBD';
                            })()}
                          </span>
                        </div>
                      )}
                      {selectedEvent.impact && (
                        <div className="pending-detail-item">
                          <span className="pending-detail-label">Impact:</span>
                          <span className={`pending-detail-value impact-${selectedEvent.impact.toLowerCase()}`}>
                            {selectedEvent.impact.charAt(0).toUpperCase() + selectedEvent.impact.slice(1)}
                          </span>
                        </div>
                      )}
                      {selectedEvent.currency && (
                        <div className="pending-detail-item">
                          <span className="pending-detail-label">Currency:</span>
                          <span className="pending-detail-value">{selectedEvent.currency}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="default-subtext">Get specific insights and trading opportunities</div>
                  <button className="confirm-analysis-btn" onClick={handleConfirmAnalysis}>
                    Confirm
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Second Cards Grid Container */}
        <div className="cards-grid-container-second">
          {/* Market Sentiment Card */}
          <div className="market-sentiment-card">
            <div className="sentiment-header">
              <div className="header-main">
                <h2 className="sentiment-title">MARKET SENTIMENT</h2>
                <InfoIcon 
                  tooltipText="Market Sentiment Analysis: Our system combines multiple data sources including price action, volatility patterns, and market correlations. We analyze RSI, volatility metrics, and risk appetite indicators to provide a comprehensive view of current market conditions. Sentiment is calculated using proprietary algorithms that process real-time market data."
                  position="bottom"
                />
              </div>
              <div className="sentiment-controls">
                <button 
                  className={`sentiment-refresh-btn ${sentimentLoading ? 'spinning' : ''}`}
                  onClick={refreshSentiment}
                  disabled={sentimentLoading}
                  title="Refresh Market Sentiment"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                  </svg>
                </button>
              </div>
            </div>
            <div className="sentiment-content">
              <React.Fragment>
                {sentiment.is_market_closed ? (
                  <div className="market-closed-state">
                    <div className="market-closed-icon">🔒</div>
                    <div className="market-closed-title">Markets Closed</div>
                    <div className="market-closed-message">
                      {sentiment.market_status === 'weekend' 
                        ? 'Markets are closed for the weekend. Live sentiment analysis will resume on Monday.'
                        : 'Markets are currently closed. Live sentiment analysis will resume when markets reopen.'
                      }
                    </div>
                    <div className="market-closed-status">
                      <span className="status-badge">{sentiment.market_status.toUpperCase()}</span>
                    </div>
                  </div>
                ) : (
                  <React.Fragment>
                    {/* VIX Fear Indicator Section */}
                        <div className="vix-section">
                          <div className="vix-header">
                            <h4 className="vix-title">VIX Fear Indicator</h4>
                            <InfoIcon 
                          tooltipText="The VIX measures implied volatility of S&P 500 options, reflecting US equity market fear and demand for downside protection. Use it as a macro confirmation tool for FX and Gold trading."
                              position="bottom"
                            />
                          </div>
                          <div className="vix-content">
                                  {(() => {
                          // Get VIX data from API
                          let vixData = sentiment.vix;
                          
                          // Development fallback: Try to parse from market conditions if vix field is missing
                          if (!vixData || vixData.value === null || vixData.value === undefined) {
                            // Try to parse from Volatility Environment condition detail
                            const volatilityCondition = sentiment.market_conditions?.find(c => 
                              c.name === 'Volatility Environment' || 
                              c.name?.toLowerCase().includes('volatility')
                            );
                            
                            if (volatilityCondition && volatilityCondition.detail) {
                              const detail = volatilityCondition.detail;
                              // Parse "VIX: 15.0 (+0.0)" format
                              const vixMatch = detail.match(/VIX:\s*([\d.]+)\s*\(([+-]?[\d.]+)\)/);
                              if (vixMatch) {
                                const parsedValue = parseFloat(vixMatch[1]);
                                const parsedChange = parseFloat(vixMatch[2]);
                                if (!isNaN(parsedValue) && parsedValue > 0) {
                                  vixData = {
                                    value: parsedValue,
                                    change: parsedChange,
                                    level: parsedValue < 15 ? 'low' : parsedValue < 25 ? 'medium' : 'high'
                                  };
                                  if (process.env.NODE_ENV === 'development') {
                                    console.log('✅ Parsed VIX from market condition:', vixData);
                                  }
                                }
                              }
                            }
                            
                            // Development fallback: Use mock data if still no VIX data
                            if ((!vixData || vixData.value === null || vixData.value === undefined) && 
                                (process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost')) {
                              vixData = {
                                value: 18.5,
                                change: 2.3,
                                level: 'medium'
                              };
                              console.warn('⚠️ Using development fallback VIX data:', vixData);
                            }
                            
                            // If still no data, show loading
                            if (!vixData || vixData.value === null || vixData.value === undefined) {
                              return (
                                <div className="vix-loading">
                                  <div className="vix-loading-spinner"></div>
                                  <span>Loading VIX data...</span>
                                  {process.env.NODE_ENV === 'development' && (
                                    <div style={{ marginTop: '8px', fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>
                                      Debug: sentiment.vix = {JSON.stringify(sentiment.vix)}
                                    </div>
                                  )}
                                </div>
                              );
                            }
                          }
                          
                          const vixValue = vixData.value;
                          const vixChange = vixData.change || 0;
                          const vixLevel = vixData.level || (vixValue < 15 ? 'low' : vixValue < 25 ? 'medium' : 'high');
                          
                          // Map VIX to bar position (0-50 range)
                          const maxVix = 50;
                          const minVix = 0;
                          const clampedVix = Math.max(minVix, Math.min(maxVix, vixValue));
                          const barPercentage = ((clampedVix - minVix) / (maxVix - minVix)) * 100;
                          
                          // Determine colors based on VIX level
                          let vixColor = '#ffa500'; // Default orange
                          let vixLevelLabel = 'Normal';
                          let barColor = '#ffa500';
                          
                          if (vixLevel === 'low' || vixValue < 15) {
                            vixColor = '#00ff88';
                            vixLevelLabel = 'Low Fear';
                            barColor = '#00ff88';
                          } else if (vixLevel === 'high' || vixValue >= 25) {
                            vixColor = '#ff4757';
                            vixLevelLabel = 'High Fear';
                            barColor = '#ff4757';
                          }
                          
                          // Determine change indicator
                          const changePositive = vixChange >= 0;
                          const changeColor = changePositive ? '#ff4757' : '#00ff88'; // Red for increase (more fear), Green for decrease (less fear)
                                    
                                    return (
                            <div className="vix-display">
                              {/* Main Value and Change */}
                              <div className="vix-main-display">
                                <div className="vix-value-wrapper">
                                  <span className="vix-label">Current VIX</span>
                                  <div className="vix-number-row">
                                    <span className="vix-number" style={{ color: vixColor }}>
                                      {vixValue.toFixed(1)}
                                    </span>
                                    <div className="vix-change-indicator" style={{ color: changeColor }}>
                                      <span className="vix-change-arrow">
                                        {changePositive ? '↑' : '↓'}
                                      </span>
                                      <span className="vix-change-value">
                                        {changePositive ? '+' : ''}{vixChange.toFixed(1)}
                                      </span>
                                    </div>
                                    <div className="vix-level-badge" style={{ 
                                      backgroundColor: `${barColor}20`,
                                      borderColor: barColor,
                                      color: barColor
                                    }}>
                                      {vixLevelLabel}
                                    </div>
                                  </div>
                                </div>
                              </div>
                              
                              {/* Horizontal Bar with Range Markers */}
                              <div className="vix-bar-container">
                                <div className="vix-bar-wrapper">
                                  <div className="vix-bar-background">
                                    {/* Range Markers */}
                                    <div className="vix-bar-markers">
                                      <span className="vix-marker" style={{ left: '0%' }}>0</span>
                                      <span className="vix-marker" style={{ left: '30%' }}>15</span>
                                      <span className="vix-marker" style={{ left: '50%' }}>25</span>
                                      <span className="vix-marker" style={{ left: '70%' }}>35</span>
                                      <span className="vix-marker" style={{ left: '100%' }}>50</span>
                                    </div>
                                    
                                    {/* Colored Bar Fill */}
                                    <div 
                                      className="vix-bar-fill"
                                            style={{
                                        width: `${barPercentage}%`,
                                        background: `linear-gradient(90deg, ${barColor} 0%, ${barColor}80 100%)`,
                                        boxShadow: `0 0 15px ${barColor}40`
                                      }}
                                    ></div>
                                    
                                    {/* Current Value Indicator */}
                                    <div 
                                      className="vix-bar-indicator"
                                      style={{
                                        left: `${barPercentage}%`,
                                        backgroundColor: vixColor,
                                        borderColor: vixColor
                                      }}
                                    >
                                      <div className="vix-indicator-dot"></div>
                                    </div>
                                  </div>
                                  
                                  {/* Range Labels */}
                                  <div className="vix-bar-labels">
                                    <span className="vix-range-label" style={{ color: '#00ff88' }}>Low</span>
                                    <span className="vix-range-label" style={{ color: '#ffa500' }}>Normal</span>
                                    <span className="vix-range-label" style={{ color: '#ff4757' }}>High</span>
                                  </div>
                                </div>
                              </div>
                                                </div>
                                              );
                        })()}
                                          </div>
                                          
                      {/* Use in Context Expandable Section */}
                      <div className="vix-context-section">
                        <button 
                          className="vix-context-toggle"
                          onClick={() => setIsVixContextExpanded(!isVixContextExpanded)}
                          aria-expanded={isVixContextExpanded}
                        >
                          <span className="vix-context-title">Use in Context</span>
                          <svg 
                            className={`vix-context-arrow ${isVixContextExpanded ? 'expanded' : ''}`}
                            width="12" 
                            height="12" 
                            viewBox="0 0 24 24" 
                            fill="none" 
                            stroke="currentColor" 
                            strokeWidth="2" 
                            strokeLinecap="round" 
                            strokeLinejoin="round"
                          >
                            <polyline points="6 9 12 15 18 9"></polyline>
                          </svg>
                        </button>
                        
                        {isVixContextExpanded && (
                          <div className="vix-context-content">
                            {/* What VIX Measures */}
                            <div className="vix-context-item">
                              <div className="vix-context-item-header">
                                <svg 
                                  width="18" 
                                  height="18" 
                                  viewBox="0 0 24 24" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  strokeWidth="2" 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round"
                                  className="vix-context-icon"
                                >
                                  <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                                  <path d="M2 17l10 5 10-5"></path>
                                  <path d="M2 12l10 5 10-5"></path>
                                </svg>
                                <h5 className="vix-context-item-title">What VIX Actually Measures</h5>
                                            </div>
                              <p className="vix-context-text">
                                VIX = implied volatility of S&P 500 options
                              </p>
                              <p className="vix-context-text">
                                So it reflects:
                              </p>
                              <ul className="vix-context-list">
                                <li>US equity market fear</li>
                                <li>Demand for downside protection in stocks</li>
                                <li>US-centric risk perception</li>
                              </ul>
                                          </div>
                                          
                            {/* When VIX Matters */}
                            <div className="vix-context-item">
                              <div className="vix-context-item-header">
                                <svg 
                                  width="18" 
                                  height="18" 
                                  viewBox="0 0 24 24" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  strokeWidth="2" 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round"
                                  className="vix-context-icon"
                                >
                                  <circle cx="12" cy="12" r="10"></circle>
                                  <line x1="12" y1="8" x2="12" y2="12"></line>
                                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                </svg>
                                <h5 className="vix-context-item-title">When VIX Matters for FX & Gold</h5>
                                          </div>
                              <p className="vix-context-text">
                                VIX is useful indirectly when:
                              </p>
                              <ul className="vix-context-list">
                                <li>There is global risk-off</li>
                                <li>US equities drive global flows</li>
                              </ul>
                                        </div>
                                        
                            {/* Typical Correlations */}
                            <div className="vix-context-item">
                              <div className="vix-context-item-header">
                                <svg 
                                  width="18" 
                                  height="18" 
                                  viewBox="0 0 24 24" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  strokeWidth="2" 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round"
                                  className="vix-context-icon"
                                >
                                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                                </svg>
                                <h5 className="vix-context-item-title">Typical Correlations</h5>
                              </div>
                              <div className="vix-correlations">
                                <div className="vix-correlation-item">
                                  <svg 
                                    width="16" 
                                    height="16" 
                                    viewBox="0 0 24 24" 
                                    fill="none" 
                                    stroke="currentColor" 
                                    strokeWidth="2" 
                                    strokeLinecap="round" 
                                    strokeLinejoin="round"
                                    className="vix-correlation-icon up"
                                  >
                                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                                    <polyline points="17 6 23 6 23 12"></polyline>
                                  </svg>
                                  <span className="vix-correlation-text">
                                    <strong>VIX ↑</strong> → USD ↑ (safe haven), JPY ↑, CHF ↑
                                          </span>
                                        </div>
                                <div className="vix-correlation-item">
                                  <svg 
                                    width="16" 
                                    height="16" 
                                    viewBox="0 0 24 24" 
                                    fill="none" 
                                    stroke="currentColor" 
                                    strokeWidth="2" 
                                    strokeLinecap="round" 
                                    strokeLinejoin="round"
                                    className="vix-correlation-icon up"
                                  >
                                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                                    <polyline points="17 6 23 6 23 12"></polyline>
                                  </svg>
                                  <span className="vix-correlation-text">
                                    <strong>VIX ↑</strong> → EM FX ↓
                                  </span>
                                          </div>
                                <div className="vix-correlation-item">
                                  <svg 
                                    width="16" 
                                    height="16" 
                                    viewBox="0 0 24 24" 
                                    fill="none" 
                                    stroke="currentColor" 
                                    strokeWidth="2" 
                                    strokeLinecap="round" 
                                    strokeLinejoin="round"
                                    className="vix-correlation-icon up"
                                  >
                                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                                    <polyline points="17 6 23 6 23 12"></polyline>
                                  </svg>
                                  <span className="vix-correlation-text">
                                    <strong>VIX ↑</strong> → Gold ↑ (but not always)
                                  </span>
                                            </div>
                                        </div>
                                      </div>
                                </div>
                            )}
                          </div>
                        </div>
                    
                    <div className="market-conditions-overview">
                      <div className="conditions-header">
                        <h3>Market Conditions</h3>
                        <span className="update-time">
                          {sentimentLoading ? 'Updating...' : `Updated ${formatTimeAgo(lastUpdate || sentiment.timestamp)}`}
                        </span>
                      </div>
                
                <div className="conditions-grid">
                  {sentiment.market_conditions.map((condition, index) => (
                    <div key={index} className="condition-item">
                      <div className="condition-label-row">
                        <div className="condition-label">{condition.name}</div>
                        {condition.trend && (
                          <span className={`trend-indicator trend-${condition.trend}`}>
                            {condition.trend === 'increasing' ? '↑' : 
                             condition.trend === 'decreasing' ? '↓' : '→'}
                          </span>
                        )}
                      </div>
                      <div className={`condition-value ${condition.value}`}>
                        {condition.name === 'Volatility Environment' ? `${capitalizeSentiment(condition.value)} Volatility` : 
                         condition.name === 'Risk Appetite' ? capitalizeSentiment(condition.value) : 
                         capitalizeSentiment(condition.value)}
                      </div>
                      <div className="condition-bar">
                        <div 
                          className="bar-fill" 
                          style={{
                            width: `${condition.percentage}%`,
                            background: `linear-gradient(90deg, ${getSentimentColor(condition.value)} 0%, ${getSentimentColor(condition.value)}80 100%)`
                          }}
                        ></div>
                      </div>
                      <div className="condition-detail">{condition.detail}</div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="sentiment-breakdown">
                <h3>Major Pairs Sentiment</h3>
                {sentimentLoading ? (
                  <div className="loading-pairs">Loading pairs sentiment...</div>
                ) : sentimentError ? (
                  <div className="error-pairs">
                    Error loading pairs: {sentimentError}
                    <br />
                    <button 
                      onClick={refreshSentiment}
                      style={{ marginTop: '10px', padding: '5px 10px', cursor: 'pointer' }}
                    >
                      Retry
                    </button>
                  </div>
                ) : !sentiment.pairs_sentiment || sentiment.pairs_sentiment.length === 0 ? (
                  <div className="error-pairs">No pairs sentiment data available</div>
                ) : (
                <div className="pairs-sentiment-grid">
                  {sentiment.pairs_sentiment.map((pair, index) => {
                    // Debug logging in development
                    if (process.env.NODE_ENV === 'development') {
                      console.log(`🔍 Rendering pair ${pair.pair}:`, {
                        sentiment: pair.sentiment,
                        percentage: pair.percentage,
                        price_change: pair.price_change,
                        rsi: pair.rsi,
                        volatility: pair.volatility
                      });
                    }
                    
                    // Safety checks - ensure all values exist and are valid numbers
                    const priceChange = (pair.price_change !== undefined && pair.price_change !== null) 
                      ? Number(pair.price_change) 
                      : 0;
                    const rsi = (pair.rsi !== undefined && pair.rsi !== null) 
                      ? Number(pair.rsi) 
                      : 50;
                    const volatility = (pair.volatility !== undefined && pair.volatility !== null) 
                      ? Number(pair.volatility) 
                      : 0;
                    const percentage = (pair.percentage !== undefined && pair.percentage !== null) 
                      ? Number(pair.percentage) 
                      : 50;
                    const sentimentValue = pair.sentiment || 'neutral';
                    
                    // Warn if values are missing (only in development)
                    if (process.env.NODE_ENV === 'development') {
                      if (pair.price_change === undefined || pair.price_change === null) {
                        console.warn(`⚠️ ${pair.pair} missing price_change, using default: 0`);
                      }
                      if (pair.rsi === undefined || pair.rsi === null) {
                        console.warn(`⚠️ ${pair.pair} missing rsi, using default: 50`);
                      }
                      if (pair.volatility === undefined || pair.volatility === null) {
                        console.warn(`⚠️ ${pair.pair} missing volatility, using default: 0`);
                      }
                    }
                    
                    return (
                    <div key={index} className="pair-sentiment-item">
                      <div className="pair-header">
                        <span className="pair-name">{pair.pair}</span>
                        <div className="pair-price-change-container">
                          <span className="pair-change-label">Daily Change</span>
                          <span className={`pair-change ${priceChange >= 0 ? 'positive' : 'negative'}`}>
                            {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                      <div className="sentiment-gauge">
                        <div 
                          className={`gauge-fill ${sentimentValue}`} 
                          style={{
                            width: `${percentage}%`,
                            background: `linear-gradient(90deg, ${getSentimentColor(sentimentValue)} 0%, ${getSentimentColor(sentimentValue)}80 100%)`
                          }}
                        ></div>
                      </div>
                      <div className="pair-metrics">
                        <span className="metric">RSI: {rsi.toFixed(0)}</span>
                        <span className="metric">Vol: {volatility.toFixed(1)}%</span>
                      </div>
                    </div>
                    );
                  })}
                </div>
                )}
              </div>
              
              <div className="sentiment-factors">
                <h3>Market Drivers</h3>
                <div className="drivers-list">
                  {sentiment.market_drivers.map((driver, index) => (
                    <div key={index} className={`driver-item ${driver.sentiment} impact-${driver.impact}`}>
                      <div className="driver-icon">
                        {driver.sentiment === 'positive' ? (
                          <span className="driver-sentiment-indicator bullish">↑</span>
                        ) : driver.sentiment === 'negative' ? (
                          <span className="driver-sentiment-indicator bearish">↓</span>
                        ) : (
                          <span className="driver-sentiment-indicator neutral">→</span>
                        )}
                      </div>
                      <div className="driver-content">
                        <div className="driver-title">{driver.title}</div>
                        <div className="driver-description">{driver.description}</div>
                        {driver.source && (
                          <div className="driver-source">Source: {driver.source}</div>
                        )}
                      </div>
                      <div className="driver-impact">{driver.impact.charAt(0).toUpperCase() + driver.impact.slice(1)} Impact</div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* <div className="sentiment-summary">
                <div className="summary-header">
                  <h3>Market Outlook</h3>
                  <span className="outlook-time">Next 24h</span>
                </div>
                <div className="summary-content">
                  <p>{sentiment.market_outlook}</p>
                </div>
                <div className="summary-actions">
                  <button className="action-btn primary">View Detailed Analysis - Coming Soon</button>
                  <button className="action-btn secondary">Set Alerts</button>
                </div>
              </div> */}
                  </React.Fragment>
                )}
              </React.Fragment>
              </div>
            </div>

          {/* Live News + Analysis Card */}
          <div className="live-news-analysis-card">
            <LiveNewsFeed />
          </div>

          {/* Prediction Markets Card */}
          <div className="prediction-markets-card">
            <div className="prediction-markets-header">
              <div className="header-main">
                <h2 className="prediction-markets-title">PREDICTION MARKETS</h2>
                <InfoIcon 
                  tooltipText="Prediction Markets: See what retail and institutional traders are betting on. These markets aggregate crowd wisdom on economic events like Fed decisions, inflation data, and GDP releases. Use this as a sentiment indicator alongside technical analysis."
                  position="bottom"
                />
        </div>
              <div className="prediction-markets-controls">
                <button 
                  className={`prediction-markets-refresh-btn ${predictionMarketsLoading ? 'spinning' : ''}`}
                  onClick={refreshPredictionMarkets}
                  disabled={predictionMarketsLoading}
                  title="Refresh Prediction Markets"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                  </svg>
                </button>
              </div>
            </div>
            <div className="prediction-markets-content">
              {predictionMarketsLoading ? (
                <div className="prediction-markets-loading">
                  <div className="loading-spinner"></div>
                  <span>Loading prediction markets...</span>
                </div>
              ) : predictionMarketsError ? (
                <div className="prediction-markets-error">
                  <div className="error-icon">⚠️</div>
                  <div className="error-text">{predictionMarketsError}</div>
                  <button className="retry-btn" onClick={refreshPredictionMarkets}>Retry</button>
                </div>
              ) : predictionMarkets.length === 0 ? (
                <div className="prediction-markets-empty">
                  <div className="empty-icon">📊</div>
                  <div className="empty-text">No Active Markets</div>
                  <div className="empty-subtext">No active prediction markets available at this time. Check back later for new markets on upcoming economic events.</div>
                </div>
              ) : (
                <>
                  <div className="prediction-markets-list">
                    {(() => {
                      // Filter: Show active markets OR recently resolved markets (within 30 days) for context
                      // This ensures users see some markets even if most are historical
                      const activeMarkets = predictionMarkets.filter(m => {
                        // Show if not resolved and not closed
                        if (!m.is_resolved && !m.closed) {
                          return true;
                        }
                        // Show if recently resolved (within 30 days) - useful context
                        if (m.is_recently_resolved) {
                          return true;
                        }
                        return false;
                      });
                      
                      // Sort by volume (highest to lowest), then by other factors
                      const sortedMarkets = [...activeMarkets].sort((a, b) => {
                        const volumeA = a.volume || 0;
                        const volumeB = b.volume || 0;
                        
                        // Primary sort: volume (highest first)
                        if (volumeB !== volumeA) {
                          return volumeB - volumeA;
                        }
                        
                        // Secondary sort: accepting orders first
                        if (a.accepting_orders !== b.accepting_orders) {
                          return b.accepting_orders ? 1 : -1;
                        }
                        
                        // Tertiary sort: future markets first
                        if (a.is_future !== b.is_future) {
                          return b.is_future ? 1 : -1;
                        }
                        
                        return 0;
                      });
                      
                      return sortedMarkets
                        .filter(market => {
                          // Filter out markets with invalid prices (already filtered in backend, but double-check)
                          const yesPrice = market.yes_price;
                          const noPrice = market.no_price;
                          const volume = market.volume || 0;
                          
                          // Skip if prices are null/undefined (invalid data)
                          if (yesPrice === null && noPrice === null && volume === 0) {
                            return false;
                          }
                          
                          // Skip if prices are 0/1 with no volume (no real trading data)
                          if (yesPrice === 0 && noPrice === 1 && volume === 0) {
                            return false;
                          }
                          
                          return true;
                        })
                        .map((market) => {
                          const yesPrice = market.yes_price;
                          const noPrice = market.no_price;
                          
                          // Handle invalid/null prices
                          const hasValidPrices = (yesPrice !== null && yesPrice !== undefined) || 
                                                (noPrice !== null && noPrice !== undefined);
                          
                          const yesPriceValue = yesPrice || 0;
                          const noPriceValue = noPrice || 0;
                          const total = yesPriceValue + noPriceValue;
                          
                          // Normalize to percentages if we have valid prices
                          const yesPercent = total > 0 ? ((yesPriceValue / total) * 100).toFixed(0) : '0';
                          const noPercent = total > 0 ? ((noPriceValue / total) * 100).toFixed(0) : '0';
                          
                          return (
                            <div key={market.id} className="prediction-market-item">
                              {/* Simplified Header - Just Question */}
                              <div className="market-header-row">
                                <div className="market-question">
                                  {market.question}
                                </div>
                              </div>
                              
                              {/* Simplified Probability Display */}
                              {hasValidPrices && total > 0 ? (
                                <div className="market-probability-row">
                                  <div className="probability-bar-container">
                                    <div className="probability-bar">
                                      {yesPriceValue > 0 && (
                                        <div 
                                          className="probability-fill yes-fill" 
                                          style={{ width: `${yesPercent}%` }}
                                        >
                                          {(parseFloat(yesPercent) >= 10 || noPriceValue === 0) && (
                                            <span className="probability-label yes-label">
                                              YES {yesPercent}%
                                            </span>
                                          )}
                                        </div>
                                      )}
                                      {noPriceValue > 0 && (
                                        <div 
                                          className="probability-fill no-fill" 
                                          style={{ width: `${noPercent}%` }}
                                        >
                                          {(parseFloat(noPercent) >= 10 || yesPriceValue === 0) && (
                                            <span className="probability-label no-label">
                                              NO {noPercent}%
                                            </span>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ) : (
                                <div className="market-probability-row">
                                  <div className="probability-bar-container">
                                    <div className="probability-bar no-data">
                                      <span className="probability-label no-data-label">
                                        No price data available
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              )}
                              
                              {/* Meta Row - Resolution Date and URL */}
                              <div className="market-meta-row">
                                {market.resolution_date && market.is_future && (
                                  <div className="market-meta-item">
                                    <span className="meta-label">Resolves:</span>
                                    <span className="meta-value">
                                      {(() => {
                                        const date = new Date(market.resolution_date);
                                        const now = new Date();
                                        
                                        const daysUntil = Math.ceil((date - now) / (1000 * 60 * 60 * 24));
                                        if (daysUntil <= 7) {
                                          return `In ${daysUntil} day${daysUntil !== 1 ? 's' : ''}`;
                                        }
                                        
                                        return date.toLocaleDateString('en-US', { 
                                          month: 'short', 
                                          day: 'numeric',
                                          year: 'numeric'
                                        });
                                      })()}
                                    </span>
                                  </div>
                                )}
                                {market.url && (
                                  <div className="market-meta-item">
                                    <a 
                                      href={market.url} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className="market-link"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      View on {market.platform === 'kalshi' ? 'Kalshi' : 'Polymarket'} →
                                    </a>
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        });
                    })()}
                  </div>
                  {(() => {
                    // Check if we have any markets (active or recently resolved)
                    const hasMarkets = predictionMarkets.some(m => {
                      return (!m.is_resolved && !m.closed) || m.is_recently_resolved;
                    });
                    
                    if (!hasMarkets) {
                      return (
                        <div className="prediction-markets-notice">
                          <div className="notice-icon">⏳</div>
                          <div className="notice-content">
                            <div className="notice-title">No Active Markets</div>
                            <div className="notice-text">No active prediction markets available at this time. Check back later for new markets on upcoming economic events.</div>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()}
                </>
              )}
            </div>
          </div>

          {/* Central Bank Analysis Card */}
          <div className="central-bank-analysis-card">
            <div className="central-bank-analysis-header">
              <div className="header-main">
                <h2 className="central-bank-analysis-title">CENTRAL BANK ANALYSIS</h2>
                <InfoIcon 
                  tooltipText="Central Bank Documents: Access official documents, meeting minutes, speeches, reports, and COT data from major central banks. Filter by bank, document type, or search by keywords. AI analysis coming soon."
                  position="bottom"
                />
              </div>
              <div className="central-bank-controls">
                <button 
                  className={`central-bank-refresh-btn ${centralBankDocumentsLoading ? 'spinning' : ''}`}
                  onClick={refreshCentralBankDocuments}
                  disabled={centralBankDocumentsLoading}
                  title="Refresh Documents"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                  </svg>
                </button>
              </div>
            </div>
            <div className="central-bank-analysis-content">
              {centralBankDocumentsLoading ? (
                <div className="central-bank-loading">
                  <div className="loading-spinner"></div>
                  <span>Loading documents...</span>
                </div>
              ) : centralBankDocumentsError ? (
                <div className="central-bank-error">
                  <div className="error-icon">⚠️</div>
                  <div className="error-text">{centralBankDocumentsError}</div>
                  <button className="retry-btn" onClick={refreshCentralBankDocuments}>Retry</button>
                </div>
              ) : (
                <>
                  {/* Search and Filters */}
                  <div className="central-bank-filters">
                    <div className="cb-search-container">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="search-icon">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="M21 21l-4.35-4.35"></path>
                      </svg>
                      <input
                        type="text"
                        className="cb-search-input"
                        placeholder="Search documents..."
                        value={cbSearchQuery}
                        onChange={(e) => setCbSearchQuery(e.target.value)}
                      />
                      {cbSearchQuery && (
                        <button 
                          className="cb-clear-search"
                          onClick={() => setCbSearchQuery('')}
                          title="Clear search"
                        >
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 6L6 18M6 6l12 12"></path>
                          </svg>
                        </button>
                      )}
                    </div>
                    <div className="cb-filter-row">
                      <select 
                        className="cb-filter-select"
                        value={cbFilterBank}
                        onChange={(e) => setCbFilterBank(e.target.value)}
                      >
                        <option value="all">All Banks</option>
                        <option value="FED">Federal Reserve</option>
                        <option value="ECB">European Central Bank</option>
                        <option value="BOJ">Bank of Japan</option>
                        <option value="BOE">Bank of England</option>
                        <option value="RBA">Reserve Bank of Australia</option>
                        <option value="BOC">Bank of Canada</option>
                        <option value="SNB">Swiss National Bank</option>
                        <option value="RBNZ">Reserve Bank of New Zealand</option>
                      </select>
                      <select 
                        className="cb-filter-select"
                        value={cbFilterType}
                        onChange={(e) => setCbFilterType(e.target.value)}
                      >
                        <option value="all">All Types</option>
                        <option value="meeting_minutes">Meeting Minutes</option>
                        <option value="speech">Speech</option>
                        <option value="report">Report</option>
                        <option value="cot_report">COT Report</option>
                        <option value="chart">Chart</option>
                        <option value="statement">Statement</option>
                      </select>
                      <select 
                        className="cb-filter-select"
                        value={cbFilterImpact}
                        onChange={(e) => setCbFilterImpact(e.target.value)}
                      >
                        <option value="all">All Impact</option>
                        <option value="high">High Impact</option>
                        <option value="medium">Medium Impact</option>
                        <option value="low">Low Impact</option>
                      </select>
                    </div>
                  </div>

                  {/* Documents List */}
                  <div className="central-bank-documents-list">
                    {getFilteredCentralBankDocuments().length > 0 ? (
                      getFilteredCentralBankDocuments().map((doc) => (
                        <div key={doc.id} className={`cb-document-item impact-${doc.impact}`}>
                          <div className="cb-document-header">
                            <div className="cb-document-title-row">
                              <h3 className="cb-document-title">{doc.title}</h3>
                              <div className="cb-document-badges">
                                <span className={`cb-bank-badge bank-${doc.centralBank.toLowerCase()}`}>
                                  {doc.centralBank}
                                </span>
                                <span className={`cb-impact-badge impact-${doc.impact}`}>
                                  {doc.impact.toUpperCase()}
                                </span>
                              </div>
                            </div>
                            <div className="cb-document-meta">
                              <span className="cb-document-date">{formatDocumentDate(doc.date)}</span>
                              <span className="cb-document-type">{getDocumentTypeLabel(doc.type)}</span>
                              <span className="cb-document-size">{doc.fileSize}</span>
                            </div>
                          </div>
                          <div className="cb-document-description">
                            {doc.description}
                          </div>
                          <div className="cb-document-footer">
                            <div className="cb-document-tags">
                              {doc.tags.slice(0, 3).map((tag, idx) => (
                                <span key={idx} className="cb-tag">{tag}</span>
                              ))}
                              {doc.tags.length > 3 && (
                                <span className="cb-tag-more">+{doc.tags.length - 3} more</span>
                              )}
                            </div>
                            <div className="cb-document-actions">
                              <button 
                                className="cb-download-btn"
                                onClick={() => handleDocumentDownload(doc)}
                                title={`Download ${doc.fileName}`}
                              >
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                  <polyline points="7 10 12 15 17 10"></polyline>
                                  <line x1="12" y1="15" x2="12" y2="3"></line>
                                </svg>
                                Download
                              </button>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="central-bank-empty">
                        <div className="empty-icon">📄</div>
                        <div className="empty-text">No documents found</div>
                        <div className="empty-subtext">
                          {cbSearchQuery || cbFilterBank !== 'all' || cbFilterType !== 'all' || cbFilterImpact !== 'all'
                            ? "Try adjusting your filters to see more documents"
                            : "No central bank documents available at this time"}
                        </div>
                        {(cbSearchQuery || cbFilterBank !== 'all' || cbFilterType !== 'all' || cbFilterImpact !== 'all') && (
                          <button 
                            className="cb-reset-filters-btn"
                            onClick={() => {
                              setCbSearchQuery('');
                              setCbFilterBank('all');
                              setCbFilterType('all');
                              setCbFilterImpact('all');
                            }}
                          >
                            Reset Filters
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        

      {/* Forex Pairs Selection Modal */}
      {isEditing && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="modal-header">
              <h2>Select Forex Pairs</h2>
              <button className="modal-close-btn" onClick={handleCloseModal}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>

            {/* Modal Instructions */}
            <div className="modal-instructions">
              <p>Choose which forex pairs to display on your dashboard. The order you select them will be the order they appear in the ticker.</p>
            </div>

            {/* Forex Pairs Grid */}
            <div className="pairs-grid">
              {allPairs.map((pair) => {
                const isSelected = selectedPairs.includes(pair.key);
                const selectedIndex = selectedPairs.indexOf(pair.key);
                return (
                  <div
                    key={pair.key}
                    className={`pair-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => handlePairToggle(pair.key)}
                  >
                    <div className="pair-checkbox">
                      {isSelected && (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M20 6L9 17L4 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </div>
                    <span className="pair-label">{pair.label}</span>
                    {isSelected && (
                      <div className="pair-order-badge">
                        {selectedIndex + 1}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Modal Actions */}
            <div className="modal-actions">
              <button className="btn-reset" onClick={handleResetToDefaults}>
                Reset to Defaults
              </button>
              <div className="modal-actions-right">
                <button className="btn-cancel" onClick={handleCloseModal}>
                  Cancel
                </button>
                <button className="btn-save" onClick={handleSaveChanges}>
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Ticker Pairs Selection Modal */}
      {isTickerEditing && (
        <div className="modal-overlay" onClick={handleCloseTickerModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="modal-header">
              <h2>Select Ticker Pairs</h2>
              <button className="modal-close-btn" onClick={handleCloseTickerModal}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>

            {/* Modal Instructions */}
            <div className="modal-instructions">
              <p>Choose which forex pairs to display in the live market ticker. The order you select them will be the order they appear.</p>
            </div>

            {/* Ticker Pairs Grid */}
            <div className="pairs-grid">
              {allTickerPairs.map((pair) => {
                const isSelected = selectedTickerPairs.includes(pair.key);
                const selectedIndex = selectedTickerPairs.indexOf(pair.key);
                return (
                  <div
                    key={pair.key}
                    className={`pair-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleTickerPairToggle(pair.key)}
                  >
                    <div className="pair-checkbox">
                      {isSelected && (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M20 6L9 17L4 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </div>
                    <span className="pair-label">{pair.label}</span>
                    {isSelected && (
                      <div className="pair-order-badge">
                        {selectedIndex + 1}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Modal Actions */}
            <div className="modal-actions">
              <button className="btn-reset" onClick={handleResetTickerToDefaults}>
                Reset to Defaults
              </button>
              <div className="modal-actions-right">
                <button className="btn-cancel" onClick={handleCloseTickerModal}>
                  Cancel
                </button>
                <button className="btn-save" onClick={handleSaveTickerChanges}>
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Calendar Date Picker Modal */}
      {isCalendarModalOpen && (
        <div className="modal-overlay" onClick={handleCloseCalendarModal}>
          <div className="modal-content calendar-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Select Date Range</h2>
              <button className="modal-close-btn" onClick={handleCloseCalendarModal}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
            
            {/* Current Selection Indicator */}
            <div className="current-selection-indicator">
              <div className="selection-info">
                <span className="selection-label">Current Selection:</span>
                <span className="selection-dates">
                  {formatDateRange(selectedDateRange.start, selectedDateRange.end)}
                </span>
                {economicEvents.length > 0 && (
                  <span className="events-count">
                    ({getFilteredEvents().length} of {economicEvents.length} events)
                  </span>
                )}
              </div>
              <div className="selection-controls">
                <button 
                  className={`range-toggle-btn ${isSelectingRange ? 'active' : ''}`}
                  onClick={toggleRangeSelection}
                  title={isSelectingRange ? 'Cancel range selection' : 'Enable range selection'}
                >
                  {isSelectingRange ? 'Cancel Range' : 'Select Range'}
                </button>
                <button 
                  className="reset-btn"
                  onClick={resetCalendarSelection}
                  title="Reset to today"
                >
                  Reset
                </button>
                {isSelectingRange && rangeStartDate && (
                  <span className="range-instruction">
                    Click another date to complete range
                  </span>
                )}
              </div>
            </div>
            
            {/* Calendar Section */}
            <div className="calendar-section">
              <div className="calendar-header-nav">
                <button className="nav-btn year-prev" onClick={handlePrevYear}>«</button>
                <button className="nav-btn month-prev" onClick={handlePrevMonth}>&lt;</button>
                <h3 className="current-month">{formatDate(currentDate)}</h3>
                <button className="nav-btn month-next" onClick={handleNextMonth}>&gt;</button>
                <button className="nav-btn year-next" onClick={handleNextYear}>»</button>
              </div>
              
              <div className="calendar-grid">
                <div className="days-header">
                  <span>S</span>
                  <span>M</span>
                  <span>T</span>
                  <span>W</span>
                  <span>T</span>
                  <span>F</span>
                  <span>S</span>
                </div>
                <div className="calendar-days">
                  {generateCalendarDays(currentDate).map((day, index) => {
                    const isInRange = isInDateRange(day.date, selectedDateRange.start, selectedDateRange.end);
                    const isRangeStart = rangeStartDate && isSameDay(day.date, rangeStartDate);
                    const isRangeEnd = selectedDateRange.end && isSameDay(day.date, selectedDateRange.end);
                    
                    return (
                      <span
                        key={index}
                        className={`day ${day.type} ${
                          isToday(day.date) ? 'current' : ''
                        } ${
                          isSameDay(day.date, selectedDate) ? 'selected' : ''
                        } ${
                          isInRange ? 'in-range' : ''
                        } ${
                          isRangeStart ? 'range-start' : ''
                        } ${
                          isRangeEnd ? 'range-end' : ''
                        }`}
                        onClick={() => handleDateClick(day)}
                      >
                        {day.date.getDate()}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Quick Select Section */}
            <div className="quick-select-section">
              {/* Custom Range Indicator */}
              {quickSelectOption === 'custom' && (
                <div className="custom-range-indicator">
                  <span className="custom-range-text">Custom Range Selected</span>
                </div>
              )}
              <div className="quick-select-grid">
                <div className="quick-select-column">
                  <button 
                    className={`quick-select-btn ${quickSelectOption === 'today' ? 'selected' : ''}`}
                    onClick={() => handleQuickSelect('today')}
                  >
                    Today
                  </button>
                  <button 
                    className={`quick-select-btn ${quickSelectOption === 'yesterday' ? 'selected' : ''}`}
                    onClick={() => handleQuickSelect('yesterday')}
                  >
                    Yesterday
                  </button>
                  <button 
                    className={`quick-select-btn ${quickSelectOption === 'tomorrow' ? 'selected' : ''}`}
                    onClick={() => handleQuickSelect('tomorrow')}
                  >
                    Tomorrow
                  </button>
                </div>
                <div className="quick-select-column">
                  <button 
                    className={`quick-select-btn ${quickSelectOption === 'this-week' ? 'selected' : ''}`}
                    onClick={() => handleQuickSelect('this-week')}
                  >
                    This Week
                  </button>
                  <button 
                    className={`quick-select-btn ${quickSelectOption === 'last-week' ? 'selected' : ''}`}
                    onClick={() => handleQuickSelect('last-week')}
                  >
                    Last Week
                  </button>
                  <button 
                    className={`quick-select-btn ${quickSelectOption === 'next-week' ? 'selected' : ''}`}
                    onClick={() => handleQuickSelect('next-week')}
                  >
                    Next Week
                  </button>
                </div>
                <div className="quick-select-column">
                  <button 
                    className={`quick-select-btn ${quickSelectOption === 'this-month' ? 'selected' : ''}`}
                    onClick={() => handleQuickSelect('this-month')}
                  >
                    This Month
                  </button>
                  <button 
                    className={`quick-select-btn ${quickSelectOption === 'last-month' ? 'selected' : ''}`}
                    onClick={() => handleQuickSelect('last-month')}
                  >
                    Last Month
                  </button>
                  <button 
                    className={`quick-select-btn ${quickSelectOption === 'next-month' ? 'selected' : ''}`}
                    onClick={() => handleQuickSelect('next-month')}
                  >
                    Next Month
                  </button>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="calendar-modal-actions">
              <button className="btn-cancel" onClick={handleCloseCalendarModal}>
                Cancel
              </button>
              <button className="btn-save" onClick={handleSaveDateSelection}>
                Select Date
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filter Options Modal */}
      {isFilterModalOpen && (
        <div className="modal-overlay" onClick={handleCloseFilterModal}>
          <div className="modal-content filter-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Filter Economic Events</h2>
              <button className="modal-close-btn" onClick={handleCloseFilterModal}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>



            {/* Impact Level Section */}
            <div className="filter-section">
              <div className="filter-section-header">
                <h3>Impact Level</h3>
                <div className="filter-section-actions">
                  <button className="filter-action-btn" onClick={handleSelectAllImpact}>
                    Select All
                  </button>
                  <button className="filter-action-btn" onClick={handleClearAllImpact}>
                    Clear All
                  </button>
                </div>
              </div>
              <div className="filter-options-grid">
                <div className="filter-option">
                  <input
                    type="checkbox"
                    id="impact-high"
                    checked={filterImpactLevels.high}
                    onChange={() => handleImpactLevelToggle('high')}
                  />
                  <label htmlFor="impact-high" className="filter-label">
                    <span className="impact-indicator high">High Impact</span>
                  </label>
                </div>
                <div className="filter-option">
                  <input
                    type="checkbox"
                    id="impact-medium"
                    checked={filterImpactLevels.medium}
                    onChange={() => handleImpactLevelToggle('medium')}
                  />
                  <label htmlFor="impact-medium" className="filter-label">
                    <span className="impact-indicator medium">Medium Impact</span>
                  </label>
                </div>
                <div className="filter-option">
                  <input
                    type="checkbox"
                    id="impact-low"
                    checked={filterImpactLevels.low}
                    onChange={() => handleImpactLevelToggle('low')}
                  />
                  <label htmlFor="impact-low" className="filter-label">
                    <span className="impact-indicator low">Low Impact</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Currencies Section */}
            <div className="filter-section">
              <div className="filter-section-header">
                <h3>Currencies Affected</h3>
                <div className="filter-section-actions">
                  <button className="filter-action-btn" onClick={handleSelectAllCurrencies}>
                    Select All
                  </button>
                  <button className="filter-action-btn" onClick={handleClearAllCurrencies}>
                    Clear All
                  </button>
                </div>
              </div>
              <div className="filter-options-grid">
                {Object.keys(filterCurrencies).map(currency => (
                  <div key={currency} className="filter-option">
                    <input
                      type="checkbox"
                      id={`currency-${currency}`}
                      checked={filterCurrencies[currency]}
                      onChange={() => handleCurrencyToggle(currency)}
                    />
                    <label htmlFor={`currency-${currency}`} className="filter-label">
                      <span className="currency-badge">{currency}</span>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="filter-modal-actions">
              <button className="btn-reset" onClick={handleResetFilters}>
                Reset to Defaults
              </button>
              <div className="modal-actions-right">
                <button className="btn-cancel" onClick={handleCloseFilterModal}>
                  Cancel
                </button>
                <button className="btn-save" onClick={handleSaveFilterPreferences}>
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chart Popup */}
      <EconomicChartPopup
        event={selectedChartEvent}
        isOpen={chartPopupOpen}
        onClose={handleCloseChart}
      />

      {/* Footer Disclaimer */}
      {/* <div className="overview-footer">
        <div className="footer-disclaimer">
          <div className="disclaimer-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <div className="disclaimer-content">
            <h4>Financial Disclaimer</h4>
            <p>
              We are not financial advisors. The information provided on this platform is for educational and informational purposes only. 
              All trading involves risk, and past performance does not guarantee future results. 
              Always conduct your own research and consider consulting with a qualified financial advisor before making any investment decisions. 
              FXSentinel does not provide investment advice or recommendations.
            </p>
          </div>
        </div>
      </div> */}
    </div>
  </div>
  );
};

export default Overview;
