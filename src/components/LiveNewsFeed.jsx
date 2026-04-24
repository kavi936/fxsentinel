import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { config } from '../config';
import { formatNewsTime, getUserTimezone, getTimezoneAbbreviation } from '../utils/timezoneUtils';
import { sanitizeNewsItem, sanitizeAnalysis } from '../utils/sanitize';
import { useAuth } from '../contexts/AuthContext';
import './LiveNewsFeed.css';
import InfoIcon from './InfoIcon.jsx';

const FXSTREET_GOLD_SLOP_REGEX = /gold price today:.*according to fxstreet data/i;

// Keyword mappings for currency pair detection - created once outside component
// This prevents recreating the 500+ entry object on every render
const KEYWORD_MAPPINGS = {
  // USD-related keywords - US Political Figures & Officials
  usd: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  fed: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'federal reserve': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'jerome powell': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  powell: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'fed chair': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'scott bessent': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  bessent: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'treasury secretary': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'us treasury': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  trump: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'donald trump': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  biden: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'joe biden': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'us president': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'white house': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'us dollar': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  dollar: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'us economy': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'us inflation': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'us gdp': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'non-farm payrolls': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  nfp: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'us cpi': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'us jobs': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  'us employment': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
  
  // EUR-related keywords - EU Political Figures & Officials
  eur: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  euro: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  ecb: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'european central bank': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'christine lagarde': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  lagarde: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'ecb president': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'ursula von der leyen': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'von der leyen': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'european commission': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'emmanuel macron': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  macron: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'french president': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'friedrich merz': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  merz: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'german chancellor': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'giorgia meloni': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  meloni: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'italian prime minister': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'christian lindner': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  lindner: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'german finance minister': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'bruno le maire': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'le maire': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'french finance minister': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'jörg kukies': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  kukies: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'eric lombard': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  lombard: ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'eurozone': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'european union': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'eu economy': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'eurozone inflation': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  'eurozone gdp': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
  
  // GBP-related keywords - UK Political Figures & Officials
  gbp: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  pound: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'british pound': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  boe: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'bank of england': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'huw pill': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  pill: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'boe governor': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'andrew bailey': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  bailey: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'keir starmer': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  starmer: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'rachel reeves': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  reeves: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'rishi sunak': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  sunak: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'jeremy hunt': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  hunt: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'uk chancellor': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'chancellor of the exchequer': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'uk prime minister': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'uk pm': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'british pm': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  brexit: ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'uk economy': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'uk inflation': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  'uk gdp': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
  
  // JPY-related keywords - Japan Political Figures & Officials
  jpy: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  yen: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  boj: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'bank of japan': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'ueda kazuo': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  ueda: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'boj governor': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'boj officials': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'sanae takaichi': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  takaichi: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'satsuki katayama': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  katayama: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japanese finance minister': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japan finance minister': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'katsunobu kato': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  kato: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'shigeru ishiba': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  ishiba: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'kishida fumio': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  kishida: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'shunichi suzuki': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  suzuki: ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japan pm': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japanese pm': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japan prime minister': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japanese prime minister': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japanese economy': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japan economy': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japanese inflation': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japan inflation': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japanese gdp': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japan gdp': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'tokyo': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  'japanese': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
  
  // AUD-related keywords - Australia Political Figures & Officials
  aud: ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'australian dollar': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  rba: ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'reserve bank of australia': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'michele bullock': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  bullock: ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'rba governor': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'anthony albanese': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  albanese: ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'australia pm': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'australian pm': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'australia prime minister': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'australian economy': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  'australia economy': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
  
  // CAD-related keywords - Canada Political Figures & Officials
  cad: ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'canadian dollar': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  boc: ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'bank of canada': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'tiff macklem': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  macklem: ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'boc governor': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'justin trudeau': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  trudeau: ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'francois-philippe champagne': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  champagne: ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'canada finance minister': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'canadian finance minister': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'canada pm': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'canadian pm': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'canada prime minister': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'canadian economy': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  'canada economy': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD'],
  
  // CHF-related keywords - Switzerland Political Figures & Officials
  chf: ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
  franc: ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
  'swiss franc': ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
  snb: ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
  'swiss national bank': ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
  'thomas jordan': ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
  jordan: ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
  'snb governor': ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
  'swiss economy': ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
};

const LiveNewsFeed = () => {
  const isUnwantedFxstreetGoldSlop = (item) => {
    const title = item?.title || '';
    const summary = item?.summary || '';
    return FXSTREET_GOLD_SLOP_REGEX.test(`${title} ${summary}`);
  };

  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [filter, setFilter] = useState('all'); // all, high, medium, low
  const [currentTimezone, setCurrentTimezone] = useState(getUserTimezone());
  const [activeTab, setActiveTab] = useState('live'); // live, history
  const [newsHistory, setNewsHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyStats, setHistoryStats] = useState(null);
  const [selectedNews, setSelectedNews] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [forceRefreshing, setForceRefreshing] = useState(false);
  const [mobileControlsOpen, setMobileControlsOpen] = useState(false);

  // Prevent body scroll when mobile controls overlay is open
  useEffect(() => {
    if (mobileControlsOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileControlsOpen]);
  const { currentUser } = useAuth();

  // Debug useEffect to monitor state changes (development only)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development' && window.location.hostname === 'localhost') {
      console.log('🦊 React app - State changed - selectedNews:', selectedNews);
      console.log('🦊 React app - State changed - aiAnalysis:', aiAnalysis);
      console.log('🦊 React app - State changed - analyzing:', analyzing);
      console.log('🦊 React app - State changed - error:', error);
    }
  }, [selectedNews, aiAnalysis, analyzing, error]);

  useEffect(() => {
    fetchNews();
    // Poll every 2 min so when backend/scheduler updates Firebase cache, frontend sees it without manual refresh
    const POLL_MS = 2 * 60 * 1000;
    const interval = setInterval(fetchNews, POLL_MS);
    return () => clearInterval(interval);
  }, []);

  // When user returns to the tab, refetch so they see cache updates that happened while the tab was in background
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && activeTab === 'live') {
        fetchNews();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [activeTab]);

  // Listen for timezone changes (event-driven, no polling)
  useEffect(() => {
    // Initial timezone check on mount
    const initialTimezone = getUserTimezone();
    setCurrentTimezone(initialTimezone);
    
    // Listen for storage events (when timezone is changed in another tab)
    const handleStorageChange = (e) => {
      if (e.key === 'fxSentinel_userTimezone') {
        setCurrentTimezone(e.newValue || 'UTC');
      }
    };

    // Listen for custom timezone change events
    const handleTimezoneChange = (e) => {
      setCurrentTimezone(e.detail.timezone);
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('timezoneChanged', handleTimezoneChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('timezoneChanged', handleTimezoneChange);
    };
  }, []); // Empty dependency array - only run on mount/unmount

  const fetchNews = async (forceRefresh = false) => {
    try {
      setLoading(true);
      if (forceRefresh) {
        setForceRefreshing(true);
      }
      setError(null);
      
      const url = forceRefresh 
        ? `${config.API_BASE_URL}/api/news?force_refresh=true&wait_fresh=true`
        : config.endpoints.news;
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`📡 Fetching news from: ${url}`);
      }
      
      let response;
      try {
        // Longer timeout for force refresh (full fetch + merge + cache write can take 60–90s under load)
        const timeout = forceRefresh ? 120000 : 15000;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        response = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (process.env.NODE_ENV === 'development') {
          console.log(`📡 Response status: ${response.status}`);
        }
      } catch (fetchError) {
        console.error('❌ Fetch error:', fetchError);
        if (fetchError.name === 'AbortError') {
          throw new Error(`Refresh is taking longer than usual. The server may be busy—please try again in a moment.`);
        }
        throw new Error(`Network error: ${fetchError.message}`);
      }
      
      if (!response.ok) {
        // Handle rate limit errors specifically
        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After');
          throw new Error(`API error: 429 Too many requests. Please wait ${retryAfter || 'a moment'} before trying again.`);
        }
        const errorText = await response.text();
        console.error(`❌ API error ${response.status}:`, errorText);
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      if (process.env.NODE_ENV === 'development') {
        console.log('📦 Raw API response:', {
          hasNews: !!data.news,
          newsLength: data.news?.length || 0,
          cacheStatus: data.cache_status,
          keys: Object.keys(data)
        });
      }
      
      if (!data.news || !Array.isArray(data.news)) {
        console.error('❌ Invalid response format - news is not an array:', data);
        throw new Error('Invalid response format from API');
      }
      
      // Ensure all news item IDs are preserved as strings to prevent precision loss
      // Also sanitize all content to prevent XSS attacks
      const processedNews = data.news.map(item => {
        // First ensure ID is string
        const itemWithStringId = {
          ...item,
          id: String(item.id || item.title || Math.random()) // Force ID to be string
        };
        const sanitized = sanitizeNewsItem(itemWithStringId);
        if (!sanitized.id) {
          sanitized.id = itemWithStringId.id;
        }
        return sanitized;
      });
      
      if (process.env.NODE_ENV === 'development') {
        console.log('📰 News processed:', {
          total: processedNews.length,
          cacheStatus: data.cache_status
        });
      }
      
      setNews(processedNews);
      
      // Use current time as fallback if last_updated is not provided or invalid
      const lastUpdatedValue = data.last_updated || new Date().toISOString();
      setLastUpdated(lastUpdatedValue);
    } catch (err) {
      console.error('❌ Error fetching news:', err);
      console.error('❌ Error details:', {
        message: err.message,
        stack: err.stack,
        name: err.name
      });
      // Don't clear news array - preserve cached news if available
      // Only set error message so user can see what went wrong
      setError(getUserFriendlyError(err));
    } finally {
      setLoading(false);
      setForceRefreshing(false);
    }
  };

  const fetchNewsHistory = async (hours = 168) => {
    try {
      setHistoryLoading(true);
      setError(null);
      
      const response = await fetch(`${config.API_BASE_URL}/api/news-history?hours=${hours}`);
      const data = await response.json();
      
      if (response.ok) {
        const sanitizedHistory = (data.history || []).map(item => sanitizeNewsItem(item));
        setNewsHistory(sanitizedHistory);
        setHistoryStats(data.analysis_stats);
      } else {
        throw new Error(data.error || 'Failed to fetch news history');
      }
    } catch (err) {
      console.error('Error fetching news history:', err);
      // Don't clear history - preserve existing history if available
      setError(getUserFriendlyError(err));
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleNewsClick = (newsItem) => {
    setSelectedNews(newsItem);
    setAiAnalysis(null);
    setError(null);
  };

  const getCachedAnalysis = async (newsItem) => {
    try {
      setAnalyzing(true);
      setError(null);
      setAiAnalysis(null); // Clear previous analysis so we don't show stale content while loading
      
      // Ensure news ID is treated as string to preserve precision
      const newsId = String(newsItem.id);
      const requestUrl = `${config.API_BASE_URL}/api/get-cached-analysis/${newsId}`;
      
      // Make API call to get cached analysis
      const response = await fetch(requestUrl);
      
      if (response.ok) {
        const analysis = await response.json();
        const sanitizedAnalysis = sanitizeAnalysis(analysis);
        setAiAnalysis(sanitizedAnalysis);
        setSelectedNews(newsItem);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || `Failed to get cached analysis: ${response.status}`);
      }
      
    } catch (err) {
      console.error('Error getting cached analysis:', err);
      
      // Use user-friendly error messages
      setError(getUserFriendlyError(err));
      setAiAnalysis(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const analyzeNews = async (newsItem) => {
    try {
      setAnalyzing(true);
      setError(null);
      setAiAnalysis(null); // Clear previous analysis so we don't show stale content while the new one loads
      
      // Ensure news ID is treated as string to preserve precision
      const newsId = String(newsItem.id);
      const requestUrl = config.endpoints.analysis(newsId) + '?t=' + Date.now();
      
      // Get Firebase ID token for backend authentication and user tracking
      let authToken = null;
      if (currentUser) {
        try {
          authToken = await currentUser.getIdToken();
        } catch (error) {
          console.error('Error getting Firebase token:', error);
        }
      }
      
      // Prepare headers with Authorization token if available
      const headers = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }
      
      // Make API call to get real GPT analysis
      const response = await fetch(requestUrl, {
        headers: headers
      });
      
      // Handle rate limit errors before parsing JSON
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        throw new Error(`API error: 429 Too many requests. Please wait ${retryAfter || 'a moment'} before trying again.`);
      }
      
      const analysis = await response.json();
      
      if (response.ok) {
        // Sanitize AI analysis content to prevent XSS
        const sanitizedAnalysis = sanitizeAnalysis(analysis);
        setAiAnalysis(sanitizedAnalysis);
        setSelectedNews(newsItem);
        
        // Refresh history if we're on the history tab to show the new analysis
        if (activeTab === 'history') {
          fetchNewsHistory();
        }
      } else {
        throw new Error(`Failed to analyze news: ${response.status} ${response.statusText}`);
      }
      
    } catch (err) {
      console.error('Error analyzing news:', err);
      
      // Use user-friendly error messages
      setError(getUserFriendlyError(err));
      setAiAnalysis(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const closeAnalysis = () => {
    setSelectedNews(null);
    setAiAnalysis(null);
    setError(null);
  };

  // Get user-friendly error messages (not technical)
  const getUserFriendlyError = (error) => {
    if (!error) return 'Something went wrong. Please try again.';
    
    const errorMessage = error.message || String(error);
    const lowerMessage = errorMessage.toLowerCase();
    
    // Network errors
    if (error.name === 'AbortError' || lowerMessage.includes('timeout') || lowerMessage.includes('took too long')) {
      if (lowerMessage.includes('longer than usual') || lowerMessage.includes('server may be busy')) {
        return error.message || 'Refresh is taking longer than usual. Please try again in a moment.';
      }
      return 'Request took too long. Please check your connection and try again.';
    }
    
    if (error.name === 'TypeError' && (lowerMessage.includes('fetch') || lowerMessage.includes('network'))) {
      return 'Unable to connect. Please check your internet connection.';
    }
    
    // API errors
    if (lowerMessage.includes('api error: 500') || lowerMessage.includes('500')) {
      return 'Server error. Please try again in a moment.';
    }
    
    if (lowerMessage.includes('api error: 429') || lowerMessage.includes('429')) {
      return 'Too many requests. Please wait a moment before trying again.';
    }
    
    if (lowerMessage.includes('api error: 404') || lowerMessage.includes('404')) {
      return 'Content not found. Please refresh the page.';
    }
    
    if (lowerMessage.includes('invalid response format') || lowerMessage.includes('invalid response')) {
      return 'Received unexpected data. Please refresh the page.';
    }
    
    // Analysis errors
    if (lowerMessage.includes('failed ai analysis') || lowerMessage.includes('analyze news')) {
      return 'Unable to analyze news. Please try again.';
    }
    
    if (lowerMessage.includes('failed to load cached analysis')) {
      return 'Unable to load saved analysis. Please try again.';
    }
    
    if (lowerMessage.includes('failed to load news history')) {
      return 'Unable to load news history. Please try again.';
    }
    
    // Generic fallback
    return 'Something went wrong. Please try again.';
  };

  const getImpactColor = (impact) => {
    switch (impact?.toLowerCase()) {
      case 'high': return '#ff4757';
      case 'medium': return '#ffa502';
      case 'low': return '#2ed573';
      default: return '#747d8c';
    }
  };

  const getImpactIcon = (impact) => {
    // Return empty string - no emojis, just use text
    return '';
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'bullish': return '#2ed573';
      case 'bearish': return '#ff4757';
      case 'neutral': return '#ffa502';
      default: return '#747d8c';
    }
  };

  const getSentimentIcon = (sentiment) => {
    // Return empty string - no emojis, just use text
    return '';
  };

  const formatTime = (timestamp) => {
    return formatNewsTime(timestamp, currentTimezone);
  };

  const formatTimeAgo = (timestamp) => {
    // Handle null/undefined
    if (!timestamp) {
      return 'Recently';
    }
    
    // Ensure timestamp is a valid Date object
    let date;
    if (timestamp instanceof Date) {
      date = timestamp;
    } else if (typeof timestamp === 'string') {
      // Handle ISO string format
      date = new Date(timestamp);
    } else {
      // Try to create Date from any other format
      date = new Date(timestamp);
    }
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Invalid timestamp after conversion:', timestamp, 'converted to:', date);
      }
      return 'Recently';
    }
    
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  // Intelligent currency pair detection and cleaning
  const getIntelligentCurrencyPairs = (newsItem) => {
    const title = (newsItem.title || '').toLowerCase();
    const summary = (newsItem.summary || '').toLowerCase();
    const text = `${title} ${summary}`;
    
    // Valid currency pair pattern (e.g., EUR/USD, USDJPY, GBP-USD)
    const validPairPattern = /^[A-Z]{3}\/?[A-Z]{3}$/i;
    
    // Clean and filter existing currency pairs
    let pairs = (newsItem.currency_pairs || [])
      .map(pair => {
        // Convert to string and clean
        const cleaned = String(pair).trim().toUpperCase();
        // Remove invalid characters and fix common issues
        const normalized = cleaned
          .replace(/[^A-Z\/]/g, '') // Remove non-letter/non-slash characters
          .replace(/([A-Z]{3})([A-Z]{3})/, '$1/$2'); // Add slash if missing (EURUSD -> EUR/USD)
        
        // Validate pattern
        if (validPairPattern.test(normalized)) {
          return normalized;
        }
        return null;
      })
      .filter(pair => pair !== null && pair.length > 0);
    
    // Remove duplicates
    pairs = [...new Set(pairs)];
    
    // If we have valid pairs, return them
    if (pairs.length > 0) {
      return pairs;
    }
    
    // Intelligent keyword-based detection
    // Use KEYWORD_MAPPINGS constant defined outside component (created once, not on every render)
    
    // Check for keywords in text (case-insensitive)
    const detectedPairs = new Set();
    
    for (const [keyword, pairs] of Object.entries(KEYWORD_MAPPINGS)) {
      // Use word boundary to avoid partial matches
      const regex = new RegExp(`\\b${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
      if (regex.test(text)) {
        pairs.forEach(pair => detectedPairs.add(pair));
      }
    }
    
    // Convert to array and limit to 4 most relevant pairs
    const finalPairs = Array.from(detectedPairs).slice(0, 4);
    
    // If still no pairs found, return empty array (don't show section)
    return finalPairs;
  };

      const getCurrentNewsList = () => {
        const currentList = activeTab === 'live' ? news : newsHistory;
        
        // Debug logging
        if (process.env.NODE_ENV === 'development') {
          console.log('🔍 getCurrentNewsList:', {
            activeTab,
            rawCount: currentList.length,
            filter
          });
        }
        
        // Filter out unwanted news items (e.g., FXStreet gold price spam)
        // This is a safety filter in case any unwanted items made it through backend filtering
        const filteredList = currentList.filter(item => {
          if (isUnwantedFxstreetGoldSlop(item)) {
            const title = item.title || '';
            if (process.env.NODE_ENV === 'development') {
              console.log('🚫 Frontend filtered out unwanted news item:', title.substring(0, 80));
            }
            return false;
          }
          return true;
        });
        
        // Remove duplicates based on title similarity
        const uniqueNews = removeDuplicateNews(filteredList);
        
        const filteredAndSorted = uniqueNews
            .filter(item => {
                // For history tab, only show analyzed news items
                if (activeTab === 'history' && !item.is_analyzed) {
                    return false;
                }
                
                // Enhanced filtering logic
                let passes = false;
                if (filter === 'all') {
                    // For 'all' filter, apply broad market relevance (exclude stocks/equities)
                    passes = isMarketRelevant(item);
                } else if (filter === 'high') {
                    // For 'high' filter, apply strict high-impact market criteria
                    passes = isHighImpactMarket(item);
                } else {
                    // For 'medium' and 'low' filters, check impact level + market relevance
                    passes = item.impact?.toLowerCase() === filter && isMarketRelevant(item);
                }
                
                // Debug logging for filtered items
                if (process.env.NODE_ENV === 'development' && !passes && item.source?.toLowerCase().includes('telegram')) {
                  console.log('❌ Telegram item filtered out:', {
                    title: item.title?.substring(0, 60),
                    source: item.source,
                    impact: item.impact,
                    filter,
                    isMarketRelevant: isMarketRelevant(item)
                  });
                }
                
                return passes;
            })
            .sort((a, b) => {
                // Sort by added_to_feed_at timestamp in descending order (newest additions first)
                // Fallback to published_at if added_to_feed_at is not available
                const dateA = new Date(a.added_to_feed_at || a.published_at);
                const dateB = new Date(b.added_to_feed_at || b.published_at);
                return dateB - dateA;
            });
        
        // Debug logging
        if (process.env.NODE_ENV === 'development') {
          console.log('✅ Filtered news list:', {
            uniqueCount: uniqueNews.length,
            filteredCount: filteredAndSorted.length,
            telegramInFiltered: filteredAndSorted.filter(item => item.source?.toLowerCase().includes('telegram')).length
          });
        }
        
        return filteredAndSorted;
    };
    
    // Enhanced filtering functions
    const isMarketRelevant = (item) => {
        const title = (item.title || '').toLowerCase();
        const summary = (item.summary || '').toLowerCase();
        const text = `${title} ${summary}`;

        // Policy: exclude stock/equity/company-specific items, but keep indices.
        const stockExclusionKeywords = [
            'stock', 'stocks', 'equity', 'equities', 'shares', 'share price', 'shareholder',
            'earnings', 'earnings call', 'eps', 'revenue', 'guidance', 'analyst rating',
            'price target', 'dividend', 'ipo', 'buyback', 'market cap', 'pe ratio',
            'quarterly results', 'ceo', 'board of directors'
        ];
        const indexKeywords = [
            'index', 'indices', 's&p 500', 'sp 500', 'nasdaq 100', 'dow jones',
            'ftse', 'dax', 'nikkei', 'hang seng', 'stoxx', 'sensex'
        ];

        const hasStockTerm = stockExclusionKeywords.some(keyword => text.includes(keyword));
        const hasIndexTerm = indexKeywords.some(keyword => text.includes(keyword));
        if (hasStockTerm && !hasIndexTerm) return false;

        // Market-inclusive keywords
        const marketKeywords = [
            'forex', 'currency', 'fx', 'foreign exchange',
            'fed', 'ecb', 'boj', 'boe', 'rba', 'boc', 'snb', 'rbnz',
            'cpi', 'inflation', 'interest rate', 'non-farm payrolls', 'gdp',
            'treasury yield', 'bond yield', 'yield curve',
            'commodity', 'oil', 'crude', 'gold', 'silver', 'copper', 'natural gas',
            'bitcoin', 'ethereum', 'crypto', 'cryptocurrency', 'digital asset',
            'index', 'indices', 's&p 500', 'nasdaq 100', 'dow jones', 'ftse', 'dax', 'nikkei',
            'trade', 'tariff', 'geopolitical', 'sanctions', 'risk-off', 'risk-on', 'safe haven'
        ];

        return marketKeywords.some(keyword => text.includes(keyword));
    };
    
    const isHighImpactMarket = (item) => {
        const title = (item.title || '').toLowerCase();
        const summary = (item.summary || '').toLowerCase();
        const source = (item.source || '').toLowerCase();
        const text = `${title} ${summary}`;
        
        if (!isMarketRelevant(item)) return false;

        // Critical market-moving keywords that should always trigger high impact
        const criticalKeywords = [
            'fed', 'federal reserve', 'ecb', 'european central bank', 'boj', 'bank of japan',
            'boe', 'bank of england', 'rba', 'reserve bank of australia', 'boc', 'bank of canada',
            'nfp', 'non-farm payrolls', 'cpi', 'inflation', 'interest rate', 'monetary policy',
            'rate decision', 'policy meeting', 'speech', 'testimony', 'breaking', 'urgent',
            'bitcoin', 'ethereum', 'crypto', 'liquidation',
            'oil', 'crude', 'gold', 'treasury yield', 'yield curve', 'index', 'indices'
        ];
        
        // High impact keywords
        const highImpactKeywords = [
            'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe', 'interest rate', 'non-farm payrolls', 'gdp',
            'rate decision', 'policy meeting', 'speech', 'testimony',
            'trump', 'biden', 'election', 'trade war', 'tariff', 'sanctions', 'geopolitical',
            'brexit', 'china trade', 'us china', 'market volatility', 'market uncertainty'
        ];
        
        // Credible sources
        const credibleSources = [
            'reuters', 'bloomberg', 'cnbc', 'marketwatch', 'forexfactory', 'fxstreet',
            'investing.com', 'fxempire', 'dailyfx', 'fxcm', 'oanda', 'ig'
        ];
        
        // Check for critical keywords (automatic high impact)
        const hasCritical = criticalKeywords.some(keyword => text.includes(keyword));
        if (hasCritical) return true;
        
        // Check source credibility
        const isCredibleSource = credibleSources.some(source_name => source.includes(source_name));
        
        // Count high impact keywords
        const highImpactCount = highImpactKeywords.filter(keyword => text.includes(keyword)).length;
        
        // For credible sources, be more lenient but still strict
        if (isCredibleSource) {
            return highImpactCount >= 2;
        }
        
        // For non-credible sources, be very strict
        return highImpactCount >= 3;
    };

  const cleanNewsTitle = (title) => {
    if (!title) return title;
    
    // Remove common prefixes that make titles look unprofessional
    // Order matters: put longer patterns first to avoid partial matches
    const prefixesToRemove = [
      '**JUST IN:**',  // **JUST IN:**
      '**BREAKING:**', // **BREAKING:**
      '**UPDATE:**',   // **UPDATE:**
      '**LIVE:**',     // **LIVE:**
      '**URGENT:**',   // **URGENT:**
      'JUST IN:',      // JUST IN:
      'BREAKING:',     // BREAKING:
      'UPDATE:',       // UPDATE:
      'LIVE:',         // LIVE:
      'URGENT:',       // URGENT:
    ];
    
    let cleanedTitle = title;
    
    // Remove each prefix pattern (case insensitive)
    prefixesToRemove.forEach(prefix => {
      const regex = new RegExp(prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      cleanedTitle = cleanedTitle.replace(regex, '');
    });
    
    // Clean up extra whitespace and punctuation
    cleanedTitle = cleanedTitle.replace(/\s+/g, ' '); // Multiple spaces to single space
    cleanedTitle = cleanedTitle.trim();
    
    // Remove leading/trailing punctuation
    cleanedTitle = cleanedTitle.replace(/^[:\s\-_]+/, ''); // Remove leading colons, spaces, dashes
    cleanedTitle = cleanedTitle.replace(/[:\s\-_]+$/, ''); // Remove trailing colons, spaces, dashes
    
    return cleanedTitle;
  };

  const removeDuplicateNews = (newsList) => {
    const uniqueNews = [];
    const seenTitles = new Set();
    const seenUrls = new Set();
    
    for (const newsItem of newsList) {
      if (!newsItem || !newsItem.title) continue;
      
      // Clean the title first
      const cleanedTitle = cleanNewsTitle(newsItem.title.trim());
      const url = newsItem.url?.trim();
      
      // Create simplified title key (first 5 words, lowercase, no punctuation)
      const simpleTitle = cleanedTitle.toLowerCase().replace(/[^\w\s]/g, '').split(' ').slice(0, 5).join(' ');
      
      // Create source + title combination
      const source = newsItem.source?.toLowerCase() || '';
      const sourceTitleKey = `${source}_${simpleTitle}`;
      
      // Check if this is a duplicate
      const isDuplicate = seenTitles.has(simpleTitle) || 
                         (url && seenUrls.has(url.toLowerCase())) ||
                         seenTitles.has(sourceTitleKey);
      
      if (!isDuplicate) {
        seenTitles.add(simpleTitle);
        if (url) seenUrls.add(url.toLowerCase());
        seenTitles.add(sourceTitleKey);
        
        // Create a copy of the news item with cleaned title and preserved string ID
        const cleanedNewsItem = { 
          ...newsItem, 
          title: cleanedTitle,
          id: String(newsItem.id) // Ensure ID remains as string
        };
        uniqueNews.push(cleanedNewsItem);
      }
    }
    
    return uniqueNews;
  };

  const clearSelection = () => {
    setSelectedNews(null);
    setAiAnalysis(null);
    setError(null);
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSelectedNews(null);
    setAiAnalysis(null);
    setError(null);
    
    if (tab === 'history' && newsHistory.length === 0) {
      fetchNewsHistory();
    }
  };

  // Get current news list for virtual scrolling
  // Memoized to prevent unnecessary recalculations
  const currentNewsList = useMemo(() => {
    return getCurrentNewsList();
  }, [news, newsHistory, activeTab, filter]);


  return (
    <div className="live-news-feed">
      <div className="news-header">
        <div className="header-main">
          <h2 className="news-title">LIVE NEWS</h2>
          <InfoIcon 
            tooltipText="Live News + AI Analysis: Our system aggregates financial news from multiple reliable sources and provides AI-powered analysis. The system uses advanced natural language processing to analyze sentiment, identify market implications, and assess potential trading opportunities. Analysis includes confidence scores and affected currency pairs."
            position="bottom"
          />
        </div>
        <div className="news-controls">
          {/* Inline controls: hidden on mobile, shown on desktop */}
          <div className="news-controls-inline">
            <div className="tab-controls">
              <button 
                className={`tab-btn ${activeTab === 'live' ? 'active' : ''}`}
                onClick={() => handleTabChange('live')}
                title="Live News"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12,6 12,12 16,14"></polyline>
                </svg>
              </button>
              <button 
                className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
                onClick={() => handleTabChange('history')}
                title="News History"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 3v18h18"></path>
                  <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"></path>
                </svg>
              </button>
            </div>
            <div className="filter-controls">
              <button 
                className={`news-filter-btn news-filter-all ${filter === 'all' ? 'active' : ''}`}
                onClick={() => setFilter('all')}
              >
                All
              </button>
              <button 
                className={`news-filter-btn news-filter-high ${filter === 'high' ? 'active' : ''}`}
                onClick={() => setFilter('high')}
              >
                H
              </button>
              <button 
                className={`news-filter-btn news-filter-medium ${filter === 'medium' ? 'active' : ''}`}
                onClick={() => setFilter('medium')}
              >
                M
              </button>
              <button 
                className={`news-filter-btn news-filter-low ${filter === 'low' ? 'active' : ''}`}
                onClick={() => setFilter('low')}
              >
                L
              </button>
            </div>
            <div className="news-refresh-and-meta">
              {forceRefreshing && activeTab === 'live' && (
                <span className="news-refreshing-label">Refreshing…</span>
              )}
              <button className="news-refresh-btn" onClick={activeTab === 'live' ? () => fetchNews(true) : () => fetchNewsHistory()} disabled={loading || historyLoading || forceRefreshing} title={activeTab === 'live' ? 'Fetch latest news' : 'Reload history'}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                </svg>
              </button>
            </div>
          </div>
          {/* Mobile: single Controls button opens overlay */}
          <button
            type="button"
            className="news-mobile-controls-btn"
            onClick={() => setMobileControlsOpen(true)}
            title="Controls"
            aria-label="Open Live News controls"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="4" y1="21" x2="4" y2="14"></line>
              <line x1="4" y1="10" x2="4" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12" y2="3"></line>
              <line x1="20" y1="21" x2="20" y2="16"></line>
              <line x1="20" y1="12" x2="20" y2="3"></line>
              <line x1="1" y1="14" x2="7" y2="14"></line>
              <line x1="9" y1="8" x2="15" y2="8"></line>
              <line x1="17" y1="16" x2="23" y2="16"></line>
            </svg>
            <span>Controls</span>
          </button>
        </div>
      </div>

      {/* Mobile controls overlay: same controls in a popup (mobile/small screens only) */}
      <div
        className={`news-mobile-controls-overlay ${mobileControlsOpen ? 'active' : ''}`}
        onClick={(e) => e.target === e.currentTarget && setMobileControlsOpen(false)}
        role="dialog"
        aria-modal="true"
        aria-label="Live News controls"
      >
        <div className="news-mobile-controls-content" onClick={(e) => e.stopPropagation()}>
          <div className="news-mobile-controls-header">
            <h3>Live News Controls</h3>
            <button
              type="button"
              className="news-mobile-controls-close"
              onClick={() => setMobileControlsOpen(false)}
              aria-label="Close"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div className="news-mobile-controls-sections">
            <div className="news-mobile-controls-section">
              <h4>Tab</h4>
              <div className="tab-controls">
                <button 
                  className={`tab-btn ${activeTab === 'live' ? 'active' : ''}`}
                  onClick={() => { handleTabChange('live'); }}
                  title="Live News"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12,6 12,12 16,14"></polyline>
                  </svg>
                  Live
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
                  onClick={() => { handleTabChange('history'); }}
                  title="News History"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 3v18h18"></path>
                    <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"></path>
                  </svg>
                  History
                </button>
              </div>
            </div>
            <div className="news-mobile-controls-section">
              <h4>Filter by impact</h4>
              <div className="filter-controls">
                <button 
                  className={`news-filter-btn news-filter-all ${filter === 'all' ? 'active' : ''}`}
                  onClick={() => setFilter('all')}
                >
                  All
                </button>
                <button 
                  className={`news-filter-btn news-filter-high ${filter === 'high' ? 'active' : ''}`}
                  onClick={() => setFilter('high')}
                >
                  High
                </button>
                <button 
                  className={`news-filter-btn news-filter-medium ${filter === 'medium' ? 'active' : ''}`}
                  onClick={() => setFilter('medium')}
                >
                  Medium
                </button>
                <button 
                  className={`news-filter-btn news-filter-low ${filter === 'low' ? 'active' : ''}`}
                  onClick={() => setFilter('low')}
                >
                  Low
                </button>
              </div>
            </div>
            <div className="news-mobile-controls-section">
              <h4>Refresh</h4>
              <button
                type="button"
                className="news-refresh-btn news-mobile-refresh-btn"
                onClick={() => {
                  if (activeTab === 'live') fetchNews(true);
                  else fetchNewsHistory();
                  setMobileControlsOpen(false);
                }}
                disabled={loading || historyLoading || forceRefreshing}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                </svg>
                {loading || historyLoading || forceRefreshing ? 'Refreshing…' : 'Refresh now'}
              </button>
            </div>
          </div>
          <button
            type="button"
            className="news-mobile-controls-done"
            onClick={() => setMobileControlsOpen(false)}
          >
            Done
          </button>
        </div>
      </div>

      <div className="news-content">
        {(loading && activeTab === 'live' && news.length === 0) || (historyLoading && activeTab === 'history' && newsHistory.length === 0) ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading {activeTab === 'live' ? 'latest news' : 'news history'}...</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <div className="error-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
            </div>
            <p className="error-message">{error}</p>
            <div className="error-actions">
              <button 
                onClick={() => {
                  setError(null);
                  if (activeTab === 'live') {
                    fetchNews(true);
                  } else {
                    fetchNewsHistory();
                  }
                }}
                className="retry-btn"
                disabled={loading || historyLoading || forceRefreshing}
              >
                {loading || historyLoading || forceRefreshing ? 'Retrying...' : 'Try Again'}
              </button>
              {currentNewsList.length > 0 && (
                <button 
                  onClick={() => setError(null)}
                  className="dismiss-btn"
                >
                  Dismiss
                </button>
              )}
            </div>
          </div>
        ) : currentNewsList.length === 0 ? (
          <div className="empty-state">
            <div className="placeholder-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {activeTab === 'live' ? (
                  <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/>
                ) : (
                  <path d="M3 3v18h18M7 16l4-4 4 4 6-6"/>
                )}
              </svg>
            </div>
            <p className="placeholder-text">No {activeTab === 'live' ? 'News' : 'Analyzed News'} Available</p>
            <p className="placeholder-subtext">
              {activeTab === 'live' 
                ? 'News feed will appear here when available' 
                : 'Analyzed news items will appear here. Click "Get AI Analysis" on any news item to start building your history.'
              }
            </p>
            {activeTab === 'history' && (
              <div className="history-empty-actions">
                <button onClick={() => handleTabChange('live')} className="switch-tab-btn">
                  Switch to Live News
                </button>
                
              </div>
            )}
            {activeTab === 'live' && (
              <div className="refresh-buttons">
                <button 
                  onClick={() => fetchNews(true)} 
                  className="refresh-btn"
                  disabled={loading || forceRefreshing}
                >
                  {loading || forceRefreshing ? 'Refreshing...' : 'Refresh'}
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
            {forceRefreshing && activeTab === 'live' && news.length > 0 && (
              <div className="news-list-refreshing-bar" aria-live="polite">
                Refreshing feed…
              </div>
            )}
            <div className="news-list">
            {currentNewsList.map((newsItem) => (
              <div 
                key={newsItem.id}
                className={`news-item ${selectedNews?.id === newsItem.id ? 'selected' : ''}`}
                onClick={() => handleNewsClick(newsItem)}
              >
                <div className="news-item-header">
                  <div className="news-source">
                    <span className="source-name">{newsItem.source}</span>
                    <span className="news-time">{formatTime(newsItem.added_to_feed_at || newsItem.published_at)}</span>
                  </div>
                  <div className="news-impact">
                    <span 
                      className="impact-badge"
                      style={{ backgroundColor: getImpactColor(newsItem.impact) }}
                    >
                      {getImpactIcon(newsItem.impact)} {newsItem.impact}
                    </span>
                  </div>
                </div>
                
                <div className="news-item-content">
                  <h3 className="news-title">{newsItem.title}</h3>
                  <p className="news-summary">{newsItem.summary}</p>
                  
                  {(() => {
                    const intelligentPairs = getIntelligentCurrencyPairs(newsItem);
                    return intelligentPairs.length > 0 && (
                      <div className="news-currency-pairs">
                        <span className="news-pairs-label">Affected pairs:</span>
                        {intelligentPairs.map((pair, idx) => (
                          <span key={idx} className="news-currency-pair">{pair}</span>
                        ))}
                      </div>
                    );
                  })()}
                  
                  {/* Analysis Status Indicator */}
                  {newsItem.is_analyzed && (
                    <div className="analysis-status-indicator">
                      <div className="analysis-badge">
                        <span className="analysis-icon">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                          </svg>
                        </span>
                        <span className="analysis-text">Analyzed</span>
                        {activeTab === 'history' && (
                          <button 
                            className="view-analysis-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleNewsClick(newsItem);
                              getCachedAnalysis(newsItem);
                            }}
                            title="View Analysis"
                          >
                            View Analysis
                          </button>
                        )}
                      </div>
                      {newsItem.analysis_summary && (
                        <div className="analysis-summary">
                          <span className="analysis-type">{newsItem.analysis_summary.type === 'gpt_enhanced' ? 'AI Enhanced' : 'Free Analysis'}</span>
                          <span className="analysis-confidence">{newsItem.analysis_summary.confidence}%</span>
                          <span className={`analysis-reaction ${newsItem.analysis_summary.reaction}`}>
                            {newsItem.analysis_summary.reaction?.replace('_', ' ').toUpperCase()}
                          </span>
                          {newsItem.analysis_summary.cost > 0 && (
                            <span className="analysis-cost">${newsItem.analysis_summary.cost.toFixed(4)}</span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="news-actions">
                  <button 
                    className="analyze-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedNews(newsItem);
                      analyzeNews(newsItem);
                    }}
                    disabled={analyzing && selectedNews?.id === newsItem.id}
                  >
                    {analyzing && selectedNews?.id === newsItem.id ? 'Analyzing...' : 'Get AI Analysis'}
                  </button>
                  
                  <a 
                    href={newsItem.url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="read-more-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!newsItem.url) {
                        e.preventDefault();
                        alert('No URL available for this news item');
                      }
                    }}
                  >
                    Read Full Article
                  </a>
                </div>

                {/* AI Analysis Section - Expandable within the news item */}
                {selectedNews?.id === newsItem.id && (aiAnalysis || analyzing || error) && (
                  <div className="ai-analysis-section" onClick={(e) => e.stopPropagation()}>
                    <div className="analysis-header">
                      <h4>AI Analysis</h4>
                      <button className="close-analysis-btn" onClick={closeAnalysis}>×</button>
                    </div>
                    
                    {analyzing && !aiAnalysis ? (
                      <div className="analysis-loading" onClick={(e) => e.stopPropagation()}>
                        <div className="loading-spinner"></div>
                        <p>Analyzing news sentiment and market implications...</p>
                      </div>
                    ) : error ? (
                      <div className="analysis-error" onClick={(e) => e.stopPropagation()}>
                        <p>{error}</p>
                        <button 
                          className="retry-analysis-btn"
                          onClick={() => analyzeNews(newsItem)}
                          disabled={analyzing}
                        >
                          {analyzing ? 'Analyzing...' : 'Try Again'}
                        </button>
                      </div>
                    ) : aiAnalysis ? (
                      <div className="analysis-content" onClick={(e) => e.stopPropagation()}>
                        {/* Simplified Analysis Header */}
                        <div className="analysis-content-header">
                          <div className="sentiment-badge" style={{ backgroundColor: getSentimentColor(aiAnalysis.immediate_reaction?.replace('_', ' ') || 'neutral') }}>
                            {getSentimentIcon(aiAnalysis.immediate_reaction?.replace('_', ' ') || 'neutral')} {aiAnalysis.immediate_reaction?.replace('_', ' ').toUpperCase() || 'NEUTRAL'}
                          </div>
                          <div className={`confidence-score ${aiAnalysis.confidence > 80 ? 'high' : aiAnalysis.confidence > 60 ? 'medium' : 'low'}`}>
                            Confidence: {typeof aiAnalysis.confidence === 'string' ? aiAnalysis.confidence : `${aiAnalysis.confidence}%`}
                          </div>
                        </div>
                        
                        {/* News Impact Paragraph */}
                        <div className="news-impact">
                          <h5>Market Impact</h5>
                          <p>{aiAnalysis.news_impact || 'NO NEWS IMPACT DATA'}</p>
                        </div>
                        
                        {/* Trading Essentials */}
                        <div className="trading-essentials">
                          <div className="essentials-grid">
                            <div className="essential-item">
                              <span className="label">Immediate Reaction:</span>
                              <span className="value bold">{aiAnalysis.immediate_reaction?.replace('_', ' ').toUpperCase() || 'NEUTRAL'}</span>
                            </div>
                            <div className="essential-item">
                              <span className="label">Key Pairs:</span>
                              <span className="value">{aiAnalysis.key_pairs?.join(', ') || 'EUR/USD, USD/JPY'}</span>
                            </div>
                            <div className="essential-item">
                              <span className="label">Volatility:</span>
                              <span className="value">{aiAnalysis.volatility?.toUpperCase() || 'MEDIUM'}</span>
                            </div>
                            <div className="essential-item">
                              <span className="label">Timeframe:</span>
                              <span className="value">{aiAnalysis.timeframe || '1-24 hours'}</span>
                            </div>
                          </div>
                        </div>
                        
                        {/* Trading Implications Paragraph */}
                        <div className="trading-implications">
                          <h5>Trading Implications</h5>
                          <p>{aiAnalysis.trading_implications || 'NO TRADING IMPLICATIONS DATA'}</p>
                        </div>
                        
                        {/* Risk Assessment */}
                        {aiAnalysis.risk_assessment && (
                          <div className="risk-assessment">
                            <h5>Risk Assessment</h5>
                            <div className="risk-grid">
                              <div className="risk-item">
                                <span className="risk-label">Market Volatility:</span>
                                <span className={`risk-value ${aiAnalysis.risk_assessment.market_volatility}`}>
                                  {aiAnalysis.risk_assessment.market_volatility?.toUpperCase() || 'MEDIUM'}
                                </span>
                              </div>
                              <div className="risk-item">
                                <span className="risk-label">Liquidity Impact:</span>
                                <span className={`risk-value ${aiAnalysis.risk_assessment.liquidity_impact}`}>
                                  {aiAnalysis.risk_assessment.liquidity_impact?.toUpperCase() || 'MEDIUM'}
                                </span>
                              </div>
                              <div className="risk-item">
                                <span className="risk-label">Correlation Risk:</span>
                                <span className={`risk-value ${aiAnalysis.risk_assessment.correlation_risk}`}>
                                  {aiAnalysis.risk_assessment.correlation_risk?.toUpperCase() || 'MEDIUM'}
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        <div className="analysis-meta">
                          <span className="analysis-time">Analyzed just now</span>
                        </div>
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            ))}
          </div>
          </>
        )}
      </div>
    </div>
  );
};

export default LiveNewsFeed;
