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
    
    console.log('🔍 Filtering events:', {
      totalEvents: economicEvents.length,
      filterImpactLevels,
      filterCurrencies,
      dateRange: `${selectedDateRange.start.toISOString().split('T')[0]} to ${selectedDateRange.end.toISOString().split('T')[0]}`
    });
    
    // Debug: Log all unique impact levels and currencies in the data
    const uniqueImpacts = [...new Set(economicEvents.map(event => event.impact))];
    const uniqueCurrencies = [...new Set(economicEvents.map(event => event.currency))];
    console.log('🔍 Unique impacts in data:', uniqueImpacts);
    console.log('🔍 Unique currencies in data:', uniqueCurrencies);
    
    const filtered = economicEvents.filter(event => {
      // Filter by impact level - handle case sensitivity
      const eventImpact = event.impact?.toLowerCase();
      const impactMatch = filterImpactLevels[eventImpact] || false;
      
      // Filter by currency
      const currencyMatch = filterCurrencies[event.currency] || false;
      
      // Debug logging for first few events
      if (economicEvents.indexOf(event) < 3) {
        console.log(`🔍 Event "${event.title}":`, {
          impact: event.impact,
          eventImpact,
          currency: event.currency,
          impactMatch,
          currencyMatch,
          passes: impactMatch && currencyMatch
        });
      }
      
      // Event passes if both impact and currency filters match
      return impactMatch && currencyMatch;
    });
    
    console.log(`✅ Filtered ${filtered.length} events from ${economicEvents.length} total for date range ${selectedDateRange.start.toISOString().split('T')[0]} to ${selectedDateRange.end.toISOString().split('T')[0]}`);
    return filtered;
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
    console.log('📅 Quick select date range:', startDate.toDateString(), 'to', endDate.toDateString());
    // Also update the selected date to the start date for single-day selections
    if (['today', 'yesterday', 'tomorrow'].includes(option)) {
      setSelectedDate(startDate);
      console.log('📅 Updated selected date:', startDate.toDateString());
    }
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
    
    // Refresh calendar data with new date range
    fetchEconomicCalendar();
  };

  // Filter handlers
  const handleImpactLevelToggle = (level) => {
    console.log(`🔄 Toggling impact level: ${level}`);
    setFilterImpactLevels(prev => {
      const newState = {
        ...prev,
        [level.toLowerCase()]: !prev[level.toLowerCase()]
      };
      console.log(`✅ Updated impact levels:`, newState);
      return newState;
    });
  };

  const handleCurrencyToggle = (currency) => {
    console.log(`🔄 Toggling currency: ${currency}`);
    setFilterCurrencies(prev => {
      const newState = {
        ...prev,
        [currency]: !prev[currency]
      };
      console.log(`✅ Updated currencies:`, newState);
      return newState;
    });
  };

  const handleSelectAllImpact = () => {
    console.log('🔄 Selecting all impact levels');
    setFilterImpactLevels({
      high: true,
      medium: true,
      low: true
    });
  };

  const handleSelectAllCurrencies = () => {
    console.log('🔄 Selecting all currencies');
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
    console.log('🔄 Clearing all impact levels');
    setFilterImpactLevels({
      high: false,
      medium: false,
      low: false
    });
  };

  const handleClearAllCurrencies = () => {
    console.log('🔄 Clearing all currencies');
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
    console.log('💾 Saving filter preferences:', {
      impactLevels: filterImpactLevels,
      currencies: filterCurrencies
    });
    
    // Save to localStorage
    const filterPreferences = {
      impactLevels: filterImpactLevels,
      currencies: filterCurrencies,
      lastUpdated: new Date().toISOString()
    };
    
    localStorage.setItem('fxSentinel_filterPreferences', JSON.stringify(filterPreferences));
    console.log('💾 Filter preferences saved to localStorage');
    
    // Close modal
    setIsFilterModalOpen(false);
  };

  // Helper function to check if filters are at default state
  const areFiltersAtDefault = () => {
    const defaultImpactLevels = { high: true, medium: true, low: true };
    const defaultCurrencies = { USD: true, EUR: true, GBP: true, JPY: true, AUD: true, CAD: true, CHF: true, NZD: true };
    
    const impactMatch = JSON.stringify(filterImpactLevels) === JSON.stringify(defaultImpactLevels);
    const currencyMatch = JSON.stringify(filterCurrencies) === JSON.stringify(defaultCurrencies);
    
    return impactMatch && currencyMatch;
  };

  // Reset filters to default state
  const handleResetFilters = () => {
    console.log('🔄 Resetting filters to defaults');
    handleSelectAllImpact();
    handleSelectAllCurrencies();
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
      console.log('🤖 Generating comprehensive AI analysis for event:', event);
      
      // Determine if this is pre-event or post-event analysis based on actual data availability
      const hasActualData = event.actual && event.actual !== 'N/A' && event.actual !== '' && event.actual !== null;
      const isPostEvent = hasActualData;
      
      console.log(`📊 Analysis type: ${isPostEvent ? 'POST-EVENT' : 'PRE-EVENT'} (Actual data: ${event.actual || 'Not available'})`);
      
      // Call our enhanced AI analysis endpoint with proper structure
      console.log('🚨🚨🚨 FRONTEND: About to call enhanced-analysis endpoint 🚨🚨🚨');
      console.log('🚨 Config endpoints backend:', config.endpoints.backend);
      console.log('🚨 Event object:', event);
      console.log('🚨 Event ID:', event.id);
      console.log('🚨 Event Title:', event.title);
      console.log('🚨 URL:', `${config.endpoints.backend}/api/enhanced-analysis/${event.id}`);
      
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
      
      console.log('🚨🚨🚨 FRONTEND: Fetch response received 🚨🚨🚨');
      console.log('🚨 Response status:', response.status);
      console.log('🚨 Response ok:', response.ok);
      
      if (!response.ok) {
        console.log('🚨🚨🚨 FRONTEND: HTTP error occurred 🚨🚨🚨');
        console.log('🚨 Error status:', response.status);
        const errorText = await response.text();
        console.log('🚨 Error text:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const analysis = await response.json();
      console.log('🚨🚨🚨 FRONTEND: Analysis JSON parsed successfully 🚨🚨🚨');
      console.log('✅ Comprehensive AI analysis received:', analysis);
      
      // Debug: Log the actual content lengths
      console.log('🔍 Frontend Debug - Content Lengths:');
      console.log('   Event Explanation:', analysis.general_overview?.event_explanation?.length || 0);
      console.log('   Market Logic:', analysis.general_overview?.market_logic?.length || 0);
      console.log('   Detailed Analysis:', analysis.immediate_impact?.detailed_analysis?.length || 0);
      console.log('   Historical Context:', analysis.context_expectations?.historical_context?.length || 0);
      console.log('   Sample Event Explanation:', analysis.general_overview?.event_explanation?.substring(0, 100) || 'No content');
      
      // Transform the backend response to preserve detailed GPT content
      return {
        event: event,
        analysisType: isPostEvent ? 'post-event' : 'pre-event',
        
        // General Overview - Preserve full GPT content
        generalOverview: {
          eventExplanation: analysis.general_overview?.event_explanation || 'Economic indicator analysis',
          marketLogic: analysis.general_overview?.market_logic || 'Market impact assessment',
          impactLevel: analysis.general_overview?.impact_level || event.impact || 'Medium'
        },
        
        // Immediate Market Impact - Preserve full GPT content
        immediateImpact: {
          direction: analysis.immediate_impact?.direction || 'Sideways',
          magnitude: analysis.immediate_impact?.magnitude || 'Medium',
          affectedPairs: analysis.immediate_impact?.affected_pairs || [event.currency + 'USD'],
          confidence: analysis.immediate_impact?.confidence || 75,
          detailedAnalysis: analysis.immediate_impact?.detailed_analysis || null
        },
        
        // Context vs Expectations - Preserve full GPT content
        expectationsAnalysis: {
          pricedInPercentage: analysis.context_expectations?.priced_in_percentage || 60,
          surprisePotential: analysis.context_expectations?.surprise_potential || 'Medium',
          historicalContext: analysis.context_expectations?.historical_context || 'Historical performance context',
          marketPositioning: analysis.context_expectations?.market_positioning || 'Market positioning analysis'
        },
        
        // Trading Framework - Preserve full GPT content
        tradingFramework: {
          keyLevels: {
            support: analysis.trading_framework?.key_levels?.support || ['Level 1', 'Level 2'],
            resistance: analysis.trading_framework?.key_levels?.resistance || ['Level 1', 'Level 2']
          },
          timing: {
            avoidTrading: analysis.trading_framework?.timing?.avoid_trading || '30 min before to 30 min after',
            bestSetup: analysis.trading_framework?.timing?.best_setup || '1-2 hours after release',
            monitoringStart: analysis.trading_framework?.timing?.monitoring_start || '1 hour before'
          },
          riskManagement: {
            positionSizing: analysis.trading_framework?.risk_management?.position_sizing || 'Conservative',
            correlationRisk: analysis.trading_framework?.risk_management?.correlation_risk || 'Medium'
          }
        },
        
        // Big Picture Implications - Preserve full GPT content
        bigPicture: {
          policyImplications: analysis.big_picture?.policy_implications || 'Central bank policy impact',
          economicHealth: analysis.big_picture?.economic_health || 'Economic health assessment',
          narrativeShift: analysis.big_picture?.narrative_shift || 'Market story changes',
          riskLevel: analysis.big_picture?.risk_level || 'Medium'
        },
        
        // Sentiment Analysis - Preserve full GPT content
        sentiment: analysis.sentiment_analysis?.overall_tone || 'neutral',
        marketConfidence: analysis.immediate_impact?.confidence > 80 ? 'High' : analysis.immediate_impact?.confidence > 60 ? 'Medium' : 'Low',
        confidenceScore: analysis.immediate_impact?.confidence || 75,
        
        // Long-term Impact - Preserve full GPT content
        longTermImpact: {
          trendImplications: analysis.long_term_impact?.trend_implications || 'Long-term trend analysis',
          structuralChanges: analysis.long_term_impact?.structural_changes || 'Policy and structural impact',
          timeHorizon: analysis.long_term_impact?.time_horizon || '6 months to 1 year'
        },
        
        // Sentiment Analysis (detailed) - Preserve full GPT content
        sentimentAnalysis: {
          overallTone: analysis.sentiment_analysis?.overall_tone || 'Neutral',
          riskAppetite: analysis.sentiment_analysis?.risk_appetite || 'Risk appetite assessment',
          forwardGuidance: analysis.sentiment_analysis?.forward_guidance || 'Future expectations analysis'
        },
        
        // Cross-Market Links - Preserve full GPT content
        crossMarketLinks: {
          bondMarkets: analysis.cross_market_links?.bond_markets || 'Bond market implications',
          equityMarkets: analysis.cross_market_links?.equity_markets || 'Equity market impact',
          commodities: analysis.cross_market_links?.commodities || 'Commodity market effects',
          safeHavenFlows: analysis.cross_market_links?.safe_haven_flows || 'Safe haven asset implications'
        },
        
        // Legacy fields for backward compatibility
        predictions: [
          {
            type: 'positive',
            icon: '🎯',
            text: analysis.general_overview?.event_explanation || 'AI analysis available'
          }
        ],
        insights: [
          {
            type: 'positive',
            icon: '🤖',
            text: analysis.big_picture?.policy_implications || 'Policy implications analysis'
          }
        ],
        tradingOpportunities: []
      };
      
    } catch (error) {
      console.log('🚨🚨🚨 FRONTEND: Error in generateEventAnalysis 🚨🚨🚨');
      console.log('🚨 Error message:', error.message);
      console.log('🚨 Error stack:', error.stack);
      console.error('❌ Error generating comprehensive AI analysis:', error);
      
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
        console.error('❌ Basic analysis also failed:', basicError);
      }
      
      // Final fallback - return comprehensive structure
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

  // Debug: Log filter state changes
  useEffect(() => {
    console.log('🔄 Filter state changed:', {
      impactLevels: filterImpactLevels,
      currencies: filterCurrencies
    });
  }, [filterImpactLevels, filterCurrencies]);

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
                <button className={`filter-btn ${(() => {
                  const activeImpactLevels = Object.values(filterImpactLevels).filter(Boolean).length;
                  const activeCurrencies = Object.values(filterCurrencies).filter(Boolean).length;
                  return (activeImpactLevels < 3 || activeCurrencies < 8) ? 'active' : '';
                })()}`} onClick={handleFilter}>
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
                  <span className="date-range-info"> • Date: {formatDateRange(selectedDateRange.start, selectedDateRange.end)}</span>
                </span>
                {/* Active filters indicator */}
                <div className="active-filters">
                  {(() => {
                    return null;
                  })()}
                </div>
                {calendarLoading && <span className="loading-indicator">Loading...</span>}
              </div>
              <div className="events-list">
                {getFilteredEvents().length > 0 ? (
                  getFilteredEvents().map((event) => (
                    <div 
                      key={event.id} 
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
                            <span className="currency">{event.currency}</span>
                            <span className={`status-indicator ${event.status.toLowerCase()}`}>{event.status}</span>
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
                (() => {
                  console.log('🔍 Rendering Analysis - State:', aiAnalysisState);
                  console.log('🔍 Rendering Analysis - aiAnalysis object:', aiAnalysis);
                  console.log('🔍 Rendering Analysis - aiAnalysis.generalOverview:', aiAnalysis.generalOverview);
                  return true;
                })() &&
                <>
                  {/* Analysis Type Badge */}
                  <div className="analysis-type-badge">
                    <span className={`type-indicator ${aiAnalysis.analysisType}`}>
                      {aiAnalysis.analysisType === 'post-event' ? '📊 Post-Event Analysis' : '🔮 Pre-Event Analysis'}
                    </span>
                  </div>

                  {/* Market Confidence Overview */}
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
                          {aiAnalysis.generalOverview.impactLevel === 'high' ? 'Strong' : 'Moderate'}
                        </span>
                      </div>
                      <div className="ai-item">
                        <span className="analysis-pair">Market Direction</span>
                        <span className={`analysis-score ${aiAnalysis.immediateImpact.direction === 'Up' ? 'bullish' : aiAnalysis.immediateImpact.direction === 'Down' ? 'bearish' : 'neutral'}`}>
                          {aiAnalysis.immediateImpact.direction}
                        </span>
                      </div>
                      <div className="ai-item">
                        <span className="analysis-pair">Volatility</span>
                        <span className={`analysis-score ${aiAnalysis.immediateImpact.magnitude === 'High' ? 'bearish' : 'neutral'}`}>
                          {aiAnalysis.immediateImpact.magnitude}
                        </span>
                      </div>
                      <div className="ai-item">
                        <span className="analysis-pair">Risk Level</span>
                        <span className={`analysis-score ${aiAnalysis.bigPicture.riskLevel === 'High' ? 'bearish' : 'bullish'}`}>
                          {aiAnalysis.bigPicture.riskLevel}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* AI Analysis - Flowing Paragraphs */}
                  <div className="ai-analysis-flowing">
                    {/* General Overview */}
                    <div className="analysis-section-flowing">
                      <h3 className="section-header">📋 General Overview</h3>
                      <div className="flowing-paragraph">
                        {(() => {
                          console.log('🔍 Rendering Event Explanation:', aiAnalysis.generalOverview.eventExplanation);
                          return aiAnalysis.generalOverview.eventExplanation;
                        })()}
                      </div>
                      <div className="flowing-paragraph">
                        <strong>Market Logic:</strong> {(() => {
                          console.log('🔍 Rendering Market Logic:', aiAnalysis.generalOverview.marketLogic);
                          return aiAnalysis.generalOverview.marketLogic;
                        })()}
                      </div>
                    </div>

                    {/* Immediate Market Impact */}
                    <div className="analysis-section-flowing">
                      <h3 className="section-header">⚡ Immediate Market Impact</h3>
                      <div className="flowing-paragraph">
                        {(() => {
                          const content = aiAnalysis.immediateImpact.detailedAnalysis || `The immediate reaction to this event is expected to be ${aiAnalysis.immediateImpact.direction.toLowerCase()} with ${aiAnalysis.immediateImpact.magnitude.toLowerCase()} volatility. Primary impact will be seen in ${aiAnalysis.immediateImpact.affectedPairs.join(', ')}.`;
                          console.log('🔍 Rendering Immediate Impact:', content);
                          return content;
                        })()}
                      </div>
                      <div className="key-metrics">
                        <span className="metric-item">
                          <strong>Confidence:</strong> {aiAnalysis.immediateImpact.confidence}%
                        </span>
                      </div>
                    </div>

                    {/* Context vs Expectations */}
                    <div className="analysis-section-flowing">
                      <h3 className="section-header">📊 Context vs Expectations</h3>
                      <div className="key-metrics">
                        <span className="metric-item">
                          <strong>Priced In:</strong> {aiAnalysis.expectationsAnalysis.pricedInPercentage}%
                        </span>
                        <span className="metric-item">
                          <strong>Surprise Potential:</strong> {aiAnalysis.expectationsAnalysis.surprisePotential}
                        </span>
                      </div>
                      <div className="flowing-paragraph">
                        {aiAnalysis.expectationsAnalysis.historicalContext}
                      </div>
                      <div className="flowing-paragraph">
                        <strong>Market Positioning:</strong> {aiAnalysis.expectationsAnalysis.marketPositioning}
                      </div>
                    </div>

                    {/* Long-term Market Impact */}
                    <div className="analysis-section-flowing">
                      <h3 className="section-header">📈 Long-term Market Impact</h3>
                      <div className="flowing-paragraph">
                        {aiAnalysis.longTermImpact?.trendImplications || 'Long-term trend analysis available'}
                      </div>
                      <div className="flowing-paragraph">
                        <strong>Structural Changes:</strong> {aiAnalysis.longTermImpact?.structuralChanges || 'Policy and structural impact analysis'}
                      </div>
                    </div>

                    {/* Sentiment Analysis */}
                    <div className="analysis-section-flowing">
                      <h3 className="section-header">🎭 Sentiment Analysis</h3>
                      <div className="key-metrics">
                        <span className={`metric-item sentiment-${aiAnalysis.sentimentAnalysis?.overallTone || 'neutral'}`}>
                          <strong>Overall Tone:</strong> {aiAnalysis.sentimentAnalysis?.overallTone || 'Neutral'}
                        </span>
                      </div>
                      <div className="flowing-paragraph">
                        {aiAnalysis.sentimentAnalysis?.riskAppetite || 'Risk appetite assessment'}
                      </div>
                      <div className="flowing-paragraph">
                        <strong>Forward Guidance:</strong> {aiAnalysis.sentimentAnalysis?.forwardGuidance || 'Future expectations analysis'}
                      </div>
                    </div>

                    {/* Cross-Market Links */}
                    <div className="analysis-section-flowing">
                      <h3 className="section-header">🔗 Cross-Market Links</h3>
                      <div className="flowing-paragraph">
                        <strong>Bond Markets:</strong> {aiAnalysis.crossMarketLinks?.bondMarkets || 'Bond market implications'}
                      </div>
                      <div className="flowing-paragraph">
                        <strong>Equity Markets:</strong> {aiAnalysis.crossMarketLinks?.equityMarkets || 'Equity market impact'}
                      </div>
                      <div className="flowing-paragraph">
                        <strong>Commodities:</strong> {aiAnalysis.crossMarketLinks?.commodities || 'Commodity market effects'}
                      </div>
                      <div className="flowing-paragraph">
                        <strong>Safe Haven Flows:</strong> {aiAnalysis.crossMarketLinks?.safeHavenFlows || 'Safe haven asset implications'}
                      </div>
                    </div>

                    {/* Trading Framework */}
                    <div className="analysis-section-flowing">
                      <h3 className="section-header">🎯 Trading Framework</h3>
                      <div className="key-metrics">
                        <span className="metric-item">
                          <strong>Key Support:</strong> {aiAnalysis.tradingFramework.keyLevels.support.join(', ')}
                        </span>
                        <span className="metric-item">
                          <strong>Key Resistance:</strong> {aiAnalysis.tradingFramework.keyLevels.resistance.join(', ')}
                        </span>
                        <span className="metric-item">
                          <strong>Avoid Trading:</strong> {aiAnalysis.tradingFramework.timing.avoidTrading}
                        </span>
                        <span className="metric-item">
                          <strong>Best Setup:</strong> {aiAnalysis.tradingFramework.timing.bestSetup}
                        </span>
                        <span className="metric-item">
                          <strong>Start Monitoring:</strong> {aiAnalysis.tradingFramework.timing.monitoringStart}
                        </span>
                        <span className="metric-item">
                          <strong>Position Sizing:</strong> {aiAnalysis.tradingFramework.riskManagement?.positionSizing || 'Conservative'}
                        </span>
                        <span className="metric-item">
                          <strong>Correlation Risk:</strong> {aiAnalysis.tradingFramework.riskManagement?.correlationRisk || 'Medium'}
                        </span>
                      </div>
                    </div>

                    {/* Big Picture Implications */}
                    <div className="analysis-section-flowing">
                      <h3 className="section-header">🌍 Big Picture Implications</h3>
                      <div className="flowing-paragraph">
                        <strong>Policy Impact:</strong> {aiAnalysis.bigPicture.policyImplications}
                      </div>
                      <div className="flowing-paragraph">
                        <strong>Economic Health:</strong> {aiAnalysis.bigPicture.economicHealth}
                      </div>
                      <div className="flowing-paragraph">
                        <strong>Narrative Shift:</strong> {aiAnalysis.bigPicture.narrativeShift}
                      </div>
                      <div className="key-metrics">
                        <span className="metric-item">
                          <strong>Risk Assessment:</strong> {aiAnalysis.bigPicture.riskLevel}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Disclaimer */}
                  <div className="analysis-disclaimer">
                    <span className="disclaimer-icon">⚠️</span>
                    <span className="disclaimer-text">This analysis provides market insights and levels, not specific trade recommendations. Always use proper risk management.</span>
                  </div>
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
                  <div className="driver-item positive impact-high">
                    <div className="driver-icon">📈</div>
                    <div className="driver-content">
                      <div className="driver-title">Strong US Economic Data</div>
                      <div className="driver-description">Recent CPI and employment figures support USD strength</div>
                    </div>
                    <div className="driver-impact">High Impact</div>
                  </div>
                  
                  <div className="driver-item negative impact-medium">
                    <div className="driver-icon">📉</div>
                    <div className="driver-content">
                      <div className="driver-title">ECB Policy Uncertainty</div>
                      <div className="driver-description">Mixed signals on future rate decisions</div>
                    </div>
                    <div className="driver-impact">Medium Impact</div>
                  </div>
                  
                  <div className="driver-item positive impact-medium">
                    <div className="driver-icon">📊</div>
                    <div className="driver-content">
                      <div className="driver-title">Risk Sentiment Improving</div>
                      <div className="driver-description">Global markets showing increased risk appetite</div>
                    </div>
                    <div className="driver-impact">Medium Impact</div>
                  </div>
                  
                  <div className="driver-item neutral impact-low">
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

            {/* Filter Info Message */}
            <div className="filter-info-message">
              <div className="info-icon">ℹ️</div>
              <div className="info-text">
                <strong>How filtering works:</strong> Date range filters fetch data from the server, while impact/currency filters are applied to the displayed events. Both work together to show you the most relevant events.
              </div>
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
