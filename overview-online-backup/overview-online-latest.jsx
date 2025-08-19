import React, { useState, useEffect } from 'react';
import { useForexPrices } from '../hooks/useForexPrices';
import LiveNewsFeed from './LiveNewsFeed';
import { config } from '../config';
import { formatTimeForTimezone, getUserTimezone, getTimezoneAbbreviation } from '../utils/timezoneUtils';
import './Overview.css';
import EconomicChartPopup from './EconomicChartPopup.jsx';

const Overview = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [selectedPairs, setSelectedPairs] = useState([]);
  const [preferencesLoaded, setPreferencesLoaded] = useState(false);
  const [isTickerEditing, setIsTickerEditing] = useState(false);
  const [selectedTickerPairs, setSelectedTickerPairs] = useState([]);
  const [isCalendarModalOpen, setIsCalendarModalOpen] = useState(false);
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // AI Analysis state
  const [aiAnalysisState, setAiAnalysisState] = useState('default'); // 'default', 'loading', 'event-analysis', 'error'
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  
  // Calendar state
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedDateRange, setSelectedDateRange] = useState({
    start: new Date(),
    end: new Date()
  });
  const [quickSelectOption, setQuickSelectOption] = useState('this-month');
  
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
    NZD: true
  });
  
  const { prices, loading, error } = useForexPrices();

  // Timezone state
  const [currentTimezone, setCurrentTimezone] = useState(getUserTimezone());

  // Format economic calendar time
  const formatCalendarTime = (timeStr, dateStr) => {
    try {
      // Parse the time and date from the backend format
      // Backend sends: time="14:30 UTC", date="Tue, Aug 12"
      const timeMatch = timeStr.match(/(\d{1,2}):(\d{2})\s*UTC/);
      const dateMatch = dateStr.match(/(\w{3}),\s*(\w{3})\s*(\d{1,2})/);
      
      if (timeMatch && dateMatch) {
        const hour = parseInt(timeMatch[1]);
        const minute = timeMatch[2];
        const dayName = dateMatch[1];
        const month = dateMatch[2];
        const day = dateMatch[3];
        
        // Create a date string that we can parse
        const currentYear = new Date().getFullYear();
        const monthMap = {
          'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
          'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
        };
        
        const monthIndex = monthMap[month];
        if (monthIndex !== undefined) {
          // Create UTC date string and parse it properly as UTC
          const utcDateString = `${currentYear}-${String(monthIndex + 1).padStart(2, '0')}-${String(parseInt(day)).padStart(2, '0')}T${String(hour).padStart(2, '0')}:${minute}:00.000Z`;
          const utcDate = new Date(utcDateString);
          
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
            return {
              time: `${convertedTime} ${tzAbbr}`,
              date: convertedDate
            };
          }
        }
      }
      
      // Fallback to original format
      return { time: timeStr, date: dateStr };
    } catch (error) {
      console.error('Error formatting calendar time:', error);
      return { time: timeStr, date: dateStr };
    }
  };

  // Listen for timezone changes
  useEffect(() => {
    const checkTimezone = () => {
      const newTimezone = getUserTimezone();
      if (newTimezone !== currentTimezone) {
        setCurrentTimezone(newTimezone);
      }
    };

    const timezoneInterval = setInterval(checkTimezone, 1000);
    
    const handleTimezoneChange = (e) => {
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

  // Chart popup state
  const [chartPopupOpen, setChartPopupOpen] = useState(false);
  const [selectedChartEvent, setSelectedChartEvent] = useState(null);

  // Economic Calendar Button Handlers
  const handleDatePicker = () => {
    setIsCalendarModalOpen(true);
  };

  const handleFilter = () => {
    setIsFilterModalOpen(true);
  };

  // Chart popup handlers
  const handleChartClick = (event) => {
    setSelectedChartEvent(event);
    setChartPopupOpen(true);
  };

  const handleCloseChart = () => {
    setChartPopupOpen(false);
    setSelectedChartEvent(null);
  };

  // Fetch economic calendar data
  useEffect(() => {
    fetchEconomicCalendar();
  }, [selectedDateRange]);

  const fetchEconomicCalendar = async () => {
    try {
      setCalendarLoading(true);
      setCalendarError(null);
      
      // Format dates for API request
      const startDate = selectedDateRange.start.toISOString().split('T')[0];
      const endDate = selectedDateRange.end.toISOString().split('T')[0];
      
      const url = `${config.endpoints.economicCalendar}?start_date=${startDate}&end_date=${endDate}`;
      console.log(`📅 Fetching calendar data for ${startDate} to ${endDate}`);
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (response.ok && data.events) {
        setEconomicEvents(data.events);
        setCalendarSource(data.source || 'API');
        console.log(`✅ Fetched ${data.events.length} economic events from ${data.source} for ${startDate} to ${endDate}`);
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
    
    return economicEvents.filter(event => {
      // Filter by impact level
      const impactMatch = filterImpactLevels[event.impact] || false;
      
      // Filter by currency
      const currencyMatch = filterCurrencies[event.currency] || false;
      
      // Event passes if both impact and currency filters match
      return impactMatch && currencyMatch;
    });
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

  const isSameDay = (date1, date2) => {
    return date1.getDate() === date2.getDate() && 
           date1.getMonth() === date2.getMonth() && 
           date1.getFullYear() === date2.getFullYear();
  };

  const isToday = (date) => {
    return isSameDay(date, new Date());
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
    
    // Next month days
    for (let i = 1; i <= 6 - lastDay; i++) {
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
    setSelectedDate(day.date);
  };

  // Quick select handlers
  const handleQuickSelect = (option) => {
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
        const lastWeekStart = new Date(today.getTime() - (dayOfWeek + 7) * 24 * 60 * 60 * 1000);
        startDate = lastWeekStart;
        endDate = new Date(lastWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000);
        break;
      case 'next-week':
        const nextWeekStart = new Date(today.getTime() + (7 - dayOfWeek) * 24 * 60 * 60 * 1000);
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
  };

  // Save preferences and close modal
  const handleSaveDateSelection = () => {
    // Save to localStorage
    const preferences = {
      selectedDate: selectedDate.toISOString(),
      selectedDateRange: {
        start: selectedDateRange.start.toISOString(),
        end: selectedDateRange.end.toISOString()
      },
      quickSelectOption: quickSelectOption,
      lastUpdated: new Date().toISOString()
    };
    
    localStorage.setItem('fxSentinel_calendarPreferences', JSON.stringify(preferences));
    console.log('💾 Calendar preferences saved:', preferences);
    
    // Close modal
    setIsCalendarModalOpen(false);
    
    // Refresh calendar data with new date range
    fetchEconomicCalendar();
  };

  // Filter handlers
  const handleImpactLevelToggle = (level) => {
    setFilterImpactLevels(prev => ({
      ...prev,
      [level]: !prev[level]
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
      NZD: true
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
      NZD: false
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
    console.log('💾 Filter preferences saved:', filterPreferences);
    
    // Close modal
    setIsFilterModalOpen(false);
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
    setAiAnalysisState('loading');
    
    try {
      // Generate real AI analysis
      const analysis = await generateEventAnalysis(event);
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
    try {
      console.log('🤖 Generating AI analysis for event:', event);
      
      // Call our enhanced AI analysis endpoint
      const response = await fetch(`${config.endpoints.backend}/api/enhanced-analysis/${event.id}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const analysis = await response.json();
      console.log('✅ AI analysis received:', analysis);
      
      // Transform the backend response to match frontend expectations
      return {
        event: event,
        marketConfidence: analysis.basic_analysis?.confidence_score > 80 ? 'High' : 'Medium',
        confidenceScore: parseInt(analysis.basic_analysis?.confidence?.replace('%', '') || '75'),
        sentiment: analysis.sentiment_analysis?.sentiment || 'neutral',
        predictions: [
          {
            type: 'positive',
            icon: '🎯',
            text: analysis.basic_analysis?.summary || 'AI analysis available'
          }
        ],
        insights: analysis.sentiment_analysis?.trading_implications?.map(implication => ({
          type: 'positive',
          icon: '🤖',
          text: implication
        })) || [],
        tradingOpportunities: analysis.basic_analysis?.trading_opportunities?.map(opp => ({
          pair: opp.pair,
          strategy: opp.strategy,
          entry: opp.entry_zone?.min || 'N/A',
          stopLoss: opp.stop_loss,
          takeProfit: opp.take_profit,
          probability: opp.probability
        })) || [],
        // Add new fields from enhanced analysis
        sentimentAnalysis: analysis.sentiment_analysis,
        technicalAnalyses: analysis.technical_analyses,
        riskAssessment: analysis.basic_analysis?.risk_assessment
      };
      
    } catch (error) {
      console.error('❌ Error generating AI analysis:', error);
      
      // Fallback to basic analysis if enhanced fails
      try {
        const basicResponse = await fetch(`${config.endpoints.backend}/api/analysis/${event.id}`);
        if (basicResponse.ok) {
          const basicAnalysis = await basicResponse.json();
          return {
            event: event,
            marketConfidence: 'Medium',
            confidenceScore: parseInt(basicAnalysis.confidence?.replace('%', '') || '70'),
            sentiment: 'neutral',
            predictions: [
              {
                type: 'positive',
                icon: '🎯',
                text: basicAnalysis.summary || 'Analysis available'
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
        console.error('❌ Basic analysis also failed:', basicError);
      }
      
      // Final fallback - return basic structure
      return {
        event: event,
        marketConfidence: 'Low',
        confidenceScore: 60,
        sentiment: 'neutral',
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
        if (Array.isArray(parsed) && parsed.length > 0 && parsed.length <= 5) {
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

  // Load calendar preferences from localStorage on component mount
  useEffect(() => {
    try {
      const savedCalendarPrefs = localStorage.getItem('fxSentinel_calendarPreferences');
      if (savedCalendarPrefs) {
        const parsed = JSON.parse(savedCalendarPrefs);
        if (parsed.selectedDate && parsed.selectedDateRange) {
          setSelectedDate(new Date(parsed.selectedDate));
          setSelectedDateRange({
            start: new Date(parsed.selectedDateRange.start),
            end: new Date(parsed.selectedDateRange.end)
          });
          setQuickSelectOption(parsed.quickSelectOption || 'this-month');
          console.log('✅ Loaded saved calendar preferences:', parsed);
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

  // Currently displayed ticker pairs (max 5) - ordered by selection order
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
      } else {
        // Add pair (max 5) - add to the end to maintain order
        if (prev.length < 5) {
          const newPairs = [...prev, pairKey];
          console.log('➕ Added ticker pair:', pairKey, 'New order:', newPairs);
          return newPairs;
        }
        console.log('⚠️ Maximum 5 ticker pairs reached, cannot add:', pairKey);
        return prev; // Don't add if already at max
      }
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
                <button className="filter-btn" onClick={handleFilter}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"></path>
                  </svg>
                </button>
                <button className={`refresh-btn ${isRefreshing ? 'refreshing' : ''}`} onClick={handleRefresh} disabled={isRefreshing}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                  </svg>
                </button>
              </div>
            </div>
            <div className="calendar-content">
              {/* Filter status indicator */}
              <div className="filter-status">
                <span className="filter-info">
                  Showing {getFilteredEvents().length} of {economicEvents.length} events
                  {calendarSource && <span className="data-source"> • Source: {calendarSource}</span>}
                </span>
                {calendarLoading && <span className="loading-indicator">Loading...</span>}
              </div>
              <div className="events-list">
                {getFilteredEvents().length > 0 ? (
                  getFilteredEvents().map((event) => (
                    <div 
                      key={event.id} 
                      className={`event-card ${selectedEvent?.id === event.id ? 'selected' : ''}`}
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
                            <span className={`event-status-indicator ${event.status.toLowerCase()}`}>{event.status}</span>
                          </div>
                        </div>
                        <div className="event-meta-row">
                          <span className="event-category">{event.type}</span>
                          <div className="affected-pairs">
                            {event.currencyPairs && event.currencyPairs.length > 0 ? (
                              event.currencyPairs.map((pair, pairIndex) => (
                                <span key={pairIndex} className="pair-badge">{pair}</span>
                              ))
                            ) : (
                              <span className="pair-badge no-pairs">No specific pairs</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="event-data">
                      <div className="data-point">
                        <span className="label">Previous:</span>
                        <span className="value">{event.previous}</span>
                      </div>
                      <div className="data-point">
                        <span className="label">Expected:</span>
                        <span className="value">{event.expected}</span>
                      </div>
                      <div className="data-point">
                        <span className="label">Actual:</span>
                        <span className="value">{event.actual}</span>
                      </div>
                      <div className="graph-icon" onClick={(e) => {
                        e.stopPropagation();
                        handleChartClick(event);
                      }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M3 3v18h18"></path>
                          <path d="M18 17V9"></path>
                          <path d="M13 17V5"></path>
                          <path d="M8 17v-3"></path>
                        </svg>
                      </div>
                    </div>
                  </div>
                ))
                ) : (
                  <div className="no-events-state">
                    <div className="no-events-icon">📅</div>
                    <div className="no-events-text">No events match your current filters</div>
                    <div className="no-events-subtext">Try adjusting your filter settings to see more events</div>
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
              <div className="ai-controls">
                <button className="refresh-btn" onClick={handleRefreshAI}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                  </svg>
                </button>
              </div>
            </div>
            <div className="ai-content">
              {aiAnalysisState === 'loading' && (
                <div className="ai-loading-state">
                  <div className="loading-spinner"></div>
                  <div className="loading-text">Analyzing {selectedEvent?.title}...</div>
                  <div className="loading-subtext">AI is processing market data and generating insights</div>
                </div>
              )}

              {aiAnalysisState === 'error' && (
                <div className="ai-error-state">
                  <div className="error-icon">⚠️</div>
                  <div className="error-text">Analysis failed</div>
                  <div className="error-subtext">Unable to generate AI analysis. Please try again.</div>
                  <button className="retry-btn" onClick={handleRefreshAI}>Retry Analysis</button>
                </div>
              )}

              {aiAnalysisState === 'event-analysis' && aiAnalysis && (
                <>
                  <div className="ai-overview">
                    <div className="ai-indicator">
                      <div className="ai-label">Market Confidence</div>
                      <div className={`ai-value ${aiAnalysis.sentiment}`}>{aiAnalysis.marketConfidence}</div>
                      <div className="ai-bar">
                        <div className={`ai-fill ${aiAnalysis.sentiment}`} style={{width: `${aiAnalysis.confidenceScore}%`}}></div>
                      </div>
                    </div>
                    
                    <div className="ai-breakdown">
                      <div className="ai-item">
                        <span className="analysis-pair">{aiAnalysis.event.currency} Impact</span>
                        <span className={`analysis-score ${aiAnalysis.sentiment}`}>
                          {aiAnalysis.event.impact === 'high' ? 'Strong' : 'Moderate'}
                        </span>
                      </div>
                      <div className="ai-item">
                        <span className="analysis-pair">Volatility</span>
                        <span className={`analysis-score ${aiAnalysis.event.impact === 'high' ? 'bearish' : 'neutral'}`}>
                          {aiAnalysis.event.impact === 'high' ? 'High' : 'Low'}
                        </span>
                      </div>
                      <div className="ai-item">
                        <span className="analysis-pair">Risk Level</span>
                        <span className={`analysis-score ${aiAnalysis.event.impact === 'high' ? 'bearish' : 'bullish'}`}>
                          {aiAnalysis.event.impact === 'high' ? 'Elevated' : 'Normal'}
                        </span>
                      </div>
                      <div className="ai-item">
                        <span className="analysis-pair">Market Sentiment</span>
                        <span className={`analysis-score ${aiAnalysis.sentiment}`}>
                          {aiAnalysis.sentiment === 'bullish' ? 'Positive' : 'Negative'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="ai-factors">
                    <h3>AI Predictions</h3>
                    <div className="ai-prediction-list">
                      {aiAnalysis.predictions.map((prediction, index) => (
                        <div key={index} className={`ai-prediction-item ${prediction.type}`}>
                          <span className="ai-prediction-icon">{prediction.icon}</span>
                          <span className="ai-prediction-text">{prediction.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="ai-factors">
                    <h3>Key Insights</h3>
                    <div className="ai-insights-list">
                      {aiAnalysis.insights.map((insight, index) => (
                        <div key={index} className={`ai-insight-item ${insight.type}`}>
                          <span className="ai-insight-icon">{insight.icon}</span>
                          <span className="ai-insight-text">{insight.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {aiAnalysis.tradingOpportunities.length > 0 && (
                    <div className="ai-factors">
                      <h3>Trading Opportunities</h3>
                      <div className="trading-opportunities-list">
                        {aiAnalysis.tradingOpportunities.map((opportunity, index) => (
                          <div key={index} className="trading-opportunity-item">
                            <div className="opportunity-header">
                              <span className="opportunity-pair">{opportunity.pair}</span>
                              <span className="opportunity-probability">{opportunity.probability}%</span>
                            </div>
                            <div className="opportunity-details">
                              <div className="opportunity-strategy">{opportunity.strategy}</div>
                              <div className="opportunity-levels">
                                <span>Entry: {opportunity.entry}</span>
                                <span>SL: {opportunity.stopLoss}</span>
                                <span>TP: {opportunity.takeProfit}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {aiAnalysisState === 'default' && (
                <div className="ai-default-message">
                  <div className="default-icon">🎯</div>
                  <div className="default-text">Click on any economic event to get AI analysis</div>
                  <div className="default-subtext">Get personalized insights and trading opportunities</div>
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
              </div>
              <div className="sentiment-controls">
                <button className="refresh-btn" onClick={() => console.log('Refresh sentiment')}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                  </svg>
                </button>
              </div>
            </div>
            <div className="sentiment-content">
              <div className="sentiment-overview">
                <div className="sentiment-indicator">
                  <div className="sentiment-label">Overall Market Sentiment</div>
                  <div className="sentiment-value bullish">Bullish</div>
                  <div className="sentiment-bar">
                    <div className="sentiment-fill bullish" style={{width: '68%'}}></div>
                  </div>
                  <div className="sentiment-score">68/100</div>
                </div>
                
                <div className="sentiment-metrics">
                  <div className="metric-item">
                    <span className="metric-label">Risk Appetite</span>
                    <span className="metric-value high">High</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Volatility Index</span>
                    <span className="metric-value medium">Medium</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Market Stress</span>
                    <span className="metric-value low">Low</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Liquidity</span>
                    <span className="metric-value high">High</span>
                  </div>
                </div>
              </div>
              
              <div className="sentiment-breakdown">
                <h3>Major Pairs Sentiment</h3>
                <div className="pairs-sentiment-grid">
                  <div className="pair-sentiment-item">
                    <div className="pair-header">
                      <span className="pair-name">EUR/USD</span>
                      <span className="pair-change positive">+0.12%</span>
                    </div>
                    <div className="sentiment-gauge">
                      <div className="gauge-fill bullish" style={{width: '72%'}}></div>
                    </div>
                    <div className="pair-metrics">
                      <span className="metric">RSI: 58</span>
                      <span className="metric">Vol: 12.5%</span>
                    </div>
                  </div>
                  
                  <div className="pair-sentiment-item">
                    <div className="pair-header">
                      <span className="pair-name">GBP/USD</span>
                      <span className="pair-change negative">-0.08%</span>
                    </div>
                    <div className="sentiment-gauge">
                      <div className="gauge-fill bearish" style={{width: '35%'}}></div>
                    </div>
                    <div className="pair-metrics">
                      <span className="metric">RSI: 42</span>
                      <span className="metric">Vol: 15.2%</span>
                    </div>
                  </div>
                  
                  <div className="pair-sentiment-item">
                    <div className="pair-header">
                      <span className="pair-name">USD/JPY</span>
                      <span className="pair-change positive">+0.25%</span>
                    </div>
                    <div className="sentiment-gauge">
                      <div className="gauge-fill bullish" style={{width: '85%'}}></div>
                    </div>
                    <div className="pair-metrics">
                      <span className="metric">RSI: 65</span>
                      <span className="metric">Vol: 18.7%</span>
                    </div>
                  </div>
                  
                  <div className="pair-sentiment-item">
                    <div className="pair-header">
                      <span className="pair-name">USD/CHF</span>
                      <span className="pair-change positive">+0.05%</span>
                    </div>
                    <div className="sentiment-gauge">
                      <div className="gauge-fill neutral" style={{width: '52%'}}></div>
                    </div>
                    <div className="pair-metrics">
                      <span className="metric">RSI: 51</span>
                      <span className="metric">Vol: 8.9%</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="sentiment-factors">
                <h3>Market Drivers</h3>
                <div className="drivers-list">
                  <div className="driver-item positive">
                    <div className="driver-icon">📈</div>
                    <div className="driver-content">
                      <div className="driver-title">Strong US Economic Data</div>
                      <div className="driver-description">Recent CPI and employment figures support USD strength</div>
                    </div>
                    <div className="driver-impact">High Impact</div>
                  </div>
                  
                  <div className="driver-item negative">
                    <div className="driver-icon">📉</div>
                    <div className="driver-content">
                      <div className="driver-title">ECB Policy Uncertainty</div>
                      <div className="driver-description">Mixed signals on future rate decisions</div>
                    </div>
                    <div className="driver-impact">Medium Impact</div>
                  </div>
                  
                  <div className="driver-item positive">
                    <div className="driver-icon">📊</div>
                    <div className="driver-content">
                      <div className="driver-title">Risk Sentiment Improving</div>
                      <div className="driver-description">Global markets showing increased risk appetite</div>
                    </div>
                    <div className="driver-impact">Medium Impact</div>
                  </div>
                  
                  <div className="driver-item neutral">
                    <div className="driver-icon">⚖️</div>
                    <div className="driver-content">
                      <div className="driver-title">Central Bank Divergence</div>
                      <div className="driver-description">Mixed policy outlooks creating balanced flows</div>
                    </div>
                    <div className="driver-impact">Low Impact</div>
                  </div>
                </div>
              </div>
              
              <div className="sentiment-summary">
                <div className="summary-header">
                  <h3>Market Outlook</h3>
                  <span className="outlook-time">Next 24h</span>
                </div>
                <div className="summary-content">
                  <p>Overall market sentiment remains bullish with strong USD fundamentals and improving risk appetite. Key focus on upcoming Fed minutes and ECB commentary. Expect continued USD strength against EUR and GBP, while JPY weakness persists.</p>
                </div>
                <div className="summary-actions">
                  <button className="action-btn primary">View Detailed Analysis</button>
                  <button className="action-btn secondary">Set Alerts</button>
                </div>
              </div>
            </div>
          </div>

          {/* Live News + Analysis Card */}
          <div className="live-news-analysis-card">
            <LiveNewsFeed />
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
              <p>Choose which forex pairs to display on your dashboard (max 5 pairs). The order you select them will be the order they appear in the ticker.</p>
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
              <p>Choose which forex pairs to display in the live market ticker (max 5 pairs). The order you select them will be the order they appear.</p>
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
                  {generateCalendarDays(currentDate).map((day, index) => (
                    <span
                      key={index}
                      className={`day ${day.type} ${
                        isToday(day.date) ? 'current' : ''
                      } ${
                        isSameDay(day.date, selectedDate) ? 'selected' : ''
                      }`}
                      onClick={() => handleDateClick(day)}
                    >
                      {day.date.getDate()}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Select Section */}
            <div className="quick-select-section">
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
              <button className="btn-cancel" onClick={handleCloseFilterModal}>
                Cancel
              </button>
              <button className="btn-save" onClick={handleSaveFilterPreferences}>
                Save Changes
              </button>
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
      <div className="overview-footer">
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
      </div>
    </div>
  </div>
  );
};

export default Overview;
