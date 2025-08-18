# Live News + Analysis Card - Complete Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [Backend Components](#backend-components)
5. [Frontend Components](#frontend-components)
6. [AI Analysis Pipeline](#ai-analysis-pipeline)
7. [Caching System](#caching-system)
8. [API Endpoints](#api-endpoints)
9. [User Interface](#user-interface)
10. [Error Handling](#error-handling)
11. [Performance Optimizations](#performance-optimizations)
12. [Testing](#testing)
13. [Troubleshooting](#troubleshooting)

## Overview

The Live News + Analysis Card is a sophisticated real-time news aggregation and analysis system designed specifically for forex traders. It provides live news feeds from multiple sources, AI-powered sentiment analysis, trading implications, and historical news tracking.

### Key Features
- **Real-time News Aggregation**: Collects news from RSS feeds (Reuters, Bloomberg, CNBC, MarketWatch)
- **AI Sentiment Analysis**: Analyzes news sentiment and generates trading implications
- **News Caching**: Intelligent caching system with 2-hour duration and history tracking
- **Live/History Tabs**: Switch between current news and historical analysis
- **Impact Filtering**: Filter news by impact level (High, Medium, Low)
- **Currency Pair Analysis**: Specific analysis for affected currency pairs
- **Trading Opportunities**: Actionable trading recommendations with risk levels

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RSS Feeds     │    │  News Cache     │    │  Frontend UI    │
│  (Reuters,      │───▶│  (2hr cache +   │───▶│  (Live/History  │
│   Bloomberg,    │    │   history)      │    │   tabs)         │
│   CNBC, etc.)   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ News Aggregator │    │ Sentiment       │    │ AI Analysis     │
│ (Filtering &    │    │ Analyzer        │    │ Display         │
│  Processing)    │    │ (Keywords &     │    │ (Trading        │
│                 │    │  Impact)        │    │  Opportunities) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Data Flow

### 1. News Collection Flow
```
RSS Feeds → News Aggregator → Enhanced Filtering → Cache Storage → Frontend Display
```

**Step-by-step process:**
1. **RSS Feed Fetching**: System fetches from 4 major financial news sources
2. **Forex Filtering**: Only forex-related articles are retained
3. **Impact Assessment**: Articles are categorized by impact level
4. **Currency Pair Extraction**: Affected currency pairs are identified
5. **Cache Storage**: Articles are stored in cache and history
6. **Frontend Delivery**: News is displayed in the UI

### 2. AI Analysis Flow
```
News Item Selection → Sentiment Analysis → Trading Implications → Currency Analysis → UI Display
```

**Step-by-step process:**
1. **User Selection**: User clicks on a news item
2. **Analysis Request**: Frontend sends analysis request to backend
3. **Sentiment Analysis**: News content is analyzed for sentiment
4. **Trading Implications**: Trading opportunities are generated
5. **Currency Analysis**: Specific pair analysis is created
6. **Response Formatting**: Structured response is sent to frontend
7. **UI Display**: Analysis is displayed with sentiment indicators

## Backend Components

### 1. News Aggregator (`backend/services/news_aggregator.py`)

**Purpose**: Collects and processes news from RSS feeds

**Key Functions:**
```python
class NewsAggregator:
    def fetch_rss_feed(self, feed_url, source_name):
        # Fetches RSS feed with 8-second timeout
        # Filters for forex-related content
        # Returns up to 3 articles per source
    
    def is_forex_related(self, title, summary):
        # Uses enhanced forex filter to determine relevance
        # Checks for forex keywords and currency pairs
    
    def determine_impact_level(self, title, summary):
        # Analyzes content for impact keywords
        # Returns High/Medium/Low impact level
    
    def extract_currency_pairs(self, title, summary):
        # Identifies affected currency pairs
        # Returns list of pairs (e.g., ['EUR/USD', 'USD/JPY'])
```

**Data Structure:**
```python
{
    'id': 123456789,
    'title': 'US CPI Data Release',
    'summary': 'Consumer Price Index for December 2024...',
    'source': 'Reuters',
    'url': 'https://reuters.com/article/...',
    'published_at': '2024-01-15T13:30:00Z',
    'impact': 'High',
    'currency_pairs': ['EUR/USD', 'USD/JPY'],
    'type': 'RSS_FEED',
    'status': 'PUBLISHED'
}
```

### 2. News Cache (`backend/services/news_cache.py`)

**Purpose**: Manages news storage and retrieval

**Key Functions:**
```python
class NewsCache:
    def save_news(self, news_items):
        # Saves current news to cache (2-hour duration)
        # Adds items to history (last 100 items)
    
    def load_news(self):
        # Loads news from cache if not expired
        # Returns None if cache is too old
    
    def get_recent_history(self, hours=24):
        # Retrieves news from last N hours
        # Filters by timestamp
    
    def get_news_by_id(self, news_id):
        # Finds specific news item in cache or history
```

**Cache Structure:**
```json
{
    "timestamp": "2024-01-15T14:30:00Z",
    "news_count": 12,
    "news": [
        // Array of news items
    ]
}
```

**History Structure:**
```json
[
    {
        "id": 123456789,
        "title": "US CPI Data Release",
        "summary": "Consumer Price Index...",
        "source": "Reuters",
        "url": "https://...",
        "published_at": "2024-01-15T13:30:00Z",
        "impact": "High",
        "currency_pairs": ["EUR/USD", "USD/JPY"],
        "cached_at": "2024-01-15T14:30:00Z",
        "type": "RSS_FEED"
    }
]
```

### 3. Sentiment Analyzer (`backend/services/news_sentiment_analyzer.py`)

**Purpose**: Analyzes news sentiment and generates trading implications

**Key Functions:**
```python
class NewsSentimentAnalyzer:
    def analyze_news_sentiment(self, news_text, title):
        # Analyzes sentiment of news content
        # Returns sentiment result with confidence
    
    def _calculate_sentiment(self, text):
        # Calculates sentiment score and confidence
        # Uses keyword analysis and pattern matching
    
    def _extract_keywords(self, text):
        # Extracts relevant keywords from text
        # Identifies forex-specific terms
    
    def _identify_affected_pairs(self, text):
        # Identifies currency pairs mentioned in text
        # Maps to standard pair formats
```

**Sentiment Result Structure:**
```python
@dataclass
class SentimentResult:
    sentiment: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0.0 to 1.0
    keywords: List[str]  # ['forex', 'dollar', 'inflation']
    impact_score: int  # 1-10 scale
    affected_pairs: List[str]  # ['EUR/USD', 'USD/JPY']
    trading_implications: Dict  # Trading recommendations
```

## Frontend Components

### 1. LiveNewsFeed Component (`src/components/LiveNewsFeed.jsx`)

**Purpose**: Main UI component for news display and interaction

**State Management:**
```javascript
const [news, setNews] = useState([]);           // Current news items
const [newsHistory, setNewsHistory] = useState([]); // Historical news
const [selectedNews, setSelectedNews] = useState(null); // Selected item
const [aiAnalysis, setAiAnalysis] = useState(null); // AI analysis result
const [activeTab, setActiveTab] = useState('live'); // Current tab
const [filter, setFilter] = useState('all');    // Impact filter
const [loading, setLoading] = useState(true);   // Loading state
```

**Key Functions:**
```javascript
const fetchNews = async () => {
    // Fetches current news from /api/news
    // Updates news state and last updated timestamp
    // Handles errors gracefully
};

const fetchNewsHistory = async (hours = 24) => {
    // Fetches news history from /api/news-history
    // Updates history state
    // Used when switching to History tab
};

const analyzeNews = async (newsItem) => {
    // Sends analysis request to /api/analysis/{id}
    // Updates AI analysis state
    // Shows loading state during analysis
};

const handleTabChange = (tab) => {
    // Switches between Live and History tabs
    // Clears selection and analysis
    // Loads history if needed
};
```

### 2. UI Structure

**Header Section:**
```jsx
<div className="news-header">
    <div className="header-main">
        <h2 className="news-title">LIVE NEWS + ANALYSIS</h2>
        <div className="news-stats">
            {/* Last updated time or history count */}
        </div>
    </div>
    <div className="news-controls">
        <div className="tab-controls">
            {/* Live/History tab buttons */}
        </div>
        <div className="filter-controls">
            {/* All/H/M/L filter buttons */}
        </div>
        <button className="refresh-btn">
            {/* Refresh button */}
        </button>
    </div>
</div>
```

**Content Section:**
```jsx
<div className="news-content">
    {/* Loading state */}
    {/* Error state */}
    {/* Empty state */}
    {/* News list */}
    <div className="news-list">
        {newsItems.map(newsItem => (
            <div className="news-item">
                {/* News item content */}
                {/* AI analysis panel */}
            </div>
        ))}
    </div>
</div>
```

## AI Analysis Pipeline

### 1. Analysis Request Flow

**Frontend Request:**
```javascript
const response = await fetch(`${config.endpoints.analysis}/${newsItem.id}`);
const analysis = await response.json();
```

**Backend Processing:**
```python
@app.route('/api/analysis/<int:news_id>')
def get_analysis(news_id):
    # 1. Find news item in cache or history
    news_item = news_cache.get_news_by_id(news_id)
    
    # 2. Generate news-specific analysis
    if news_item:
        analysis = generate_news_analysis(news_item)
        return jsonify(analysis)
    
    # 3. Fallback to economic event analysis
    # 4. Return mock analysis if all else fails
```

### 2. News Analysis Generation

**Step 1: Sentiment Analysis**
```python
def generate_news_analysis(news_item):
    # Analyze sentiment of news content
    sentiment_result = news_sentiment_analyzer.analyze_news_sentiment(
        news_item.get('summary', ''),
        news_item.get('title', '')
    )
```

**Step 2: Trading Implications**
```python
def generate_trading_implications_from_news(sentiment_result, currency_pairs, impact):
    # Generate trading opportunities based on sentiment
    implications = {
        'summary': f"Positive market sentiment detected with {impact_score}/10 impact score...",
        'opportunities': [
            {
                'pair': 'EUR/USD',
                'strategy': 'sentiment_following',
                'direction': 'bullish',
                'confidence': 75,
                'timeframe': '1-4 hours',
                'risk_level': 'medium'
            }
        ]
    }
```

**Step 3: Currency Pair Analysis**
```python
def generate_currency_pair_analysis(currency_pairs, sentiment_result):
    # Generate specific analysis for each currency pair
    analysis = {}
    for pair in currency_pairs:
        if sentiment == 'bullish':
            analysis[pair] = f"Positive sentiment suggests potential upside for {pair}..."
        elif sentiment == 'bearish':
            analysis[pair] = f"Negative sentiment suggests potential downside for {pair}..."
        else:
            analysis[pair] = f"Neutral sentiment for {pair}. Range-bound trading likely..."
```

### 3. Analysis Response Structure

```json
{
    "summary": "Positive market sentiment detected with 7/10 impact score. Consider long positions on affected currency pairs.",
    "currency_pairs": {
        "EUR/USD": "Positive sentiment suggests potential upside for EUR/USD. Monitor for breakout above key resistance levels.",
        "USD/JPY": "Positive sentiment suggests potential upside for USD/JPY. Monitor for breakout above key resistance levels."
    },
    "trading_opportunities": [
        {
            "pair": "EUR/USD",
            "strategy": "sentiment_following",
            "direction": "bullish",
            "confidence": 75,
            "timeframe": "1-4 hours",
            "risk_level": "medium"
        }
    ],
    "confidence": "75%",
    "sentiment": "bullish",
    "impact_score": 7,
    "keywords": ["forex", "dollar", "inflation", "fed"],
    "analysis_type": "news_sentiment"
}
```

## Caching System

### 1. Cache Strategy

**Current News Cache:**
- **Duration**: 2 hours
- **Location**: `backend/news_cache.json`
- **Purpose**: Reduce API calls and improve performance
- **Invalidation**: Automatic expiration after 2 hours

**News History:**
- **Storage**: Last 100 news items
- **Location**: `backend/news_history.json`
- **Purpose**: Provide historical context and analysis
- **Cleanup**: Automatic removal of oldest items

### 2. Cache Operations

**Saving News:**
```python
def save_news(self, news_items):
    # Save current news to cache
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'news_count': len(news_items),
        'news': news_items
    }
    
    # Add to history
    self._add_to_history(news_items)
```

**Loading News:**
```python
def load_news(self):
    # Check if cache exists and is valid
    if not os.path.exists(self.cache_file):
        return None
    
    # Check if cache is too old
    cache_timestamp = datetime.fromisoformat(cache_data['timestamp'])
    age = datetime.now() - cache_timestamp
    
    if age > timedelta(hours=self.max_age_hours):
        return None  # Cache expired
    
    return cache_data.get('news', [])
```

### 3. Cache Status Monitoring

**Cache Status Response:**
```json
{
    "exists": true,
    "age": "0:30:15.123456",
    "news_count": 12,
    "is_valid": true,
    "last_updated": "2024-01-15T14:30:00Z"
}
```

## API Endpoints

### 1. News Endpoint (`/api/news`)

**Purpose**: Get current news with caching

**Request:**
```
GET /api/news
```

**Response:**
```json
{
    "news": [
        {
            "id": 123456789,
            "title": "US CPI Data Release",
            "summary": "Consumer Price Index for December 2024...",
            "source": "Reuters",
            "url": "https://reuters.com/article/...",
            "published_at": "2024-01-15T13:30:00Z",
            "impact": "High",
            "currency_pairs": ["EUR/USD", "USD/JPY"],
            "type": "RSS_FEED",
            "status": "PUBLISHED"
        }
    ],
    "last_updated": "2024-01-15T14:30:00Z",
    "sources": ["Reuters", "Bloomberg"],
    "total_articles": 12,
    "cache_status": "fresh"
}
```

### 2. News History Endpoint (`/api/news-history`)

**Purpose**: Get historical news data

**Request:**
```
GET /api/news-history?hours=24
```

**Response:**
```json
{
    "history": [
        // Array of historical news items
    ],
    "status": {
        "total_items": 45,
        "oldest_item": "2024-01-14T14:30:00Z",
        "newest_item": "2024-01-15T14:30:00Z"
    },
    "hours_requested": 24,
    "total_items": 12
}
```

### 3. Analysis Endpoint (`/api/analysis/<news_id>`)

**Purpose**: Generate AI analysis for news item

**Request:**
```
GET /api/analysis/123456789
```

**Response:**
```json
{
    "summary": "Positive market sentiment detected...",
    "currency_pairs": {
        "EUR/USD": "Positive sentiment suggests potential upside..."
    },
    "trading_opportunities": [
        {
            "pair": "EUR/USD",
            "strategy": "sentiment_following",
            "direction": "bullish",
            "confidence": 75,
            "timeframe": "1-4 hours",
            "risk_level": "medium"
        }
    ],
    "confidence": "75%",
    "sentiment": "bullish",
    "impact_score": 7,
    "keywords": ["forex", "dollar", "inflation"],
    "analysis_type": "news_sentiment"
}
```

### 4. News by ID Endpoint (`/api/news/<news_id>`)

**Purpose**: Get specific news item

**Request:**
```
GET /api/news/123456789
```

**Response:**
```json
{
    "id": 123456789,
    "title": "US CPI Data Release",
    "summary": "Consumer Price Index for December 2024...",
    "source": "Reuters",
    "url": "https://reuters.com/article/...",
    "published_at": "2024-01-15T13:30:00Z",
    "impact": "High",
    "currency_pairs": ["EUR/USD", "USD/JPY"],
    "type": "RSS_FEED",
    "status": "PUBLISHED"
}
```

## User Interface

### 1. Tab System

**Live Tab:**
- Shows current news from RSS feeds
- Auto-refreshes every 5 minutes
- Displays last updated time
- Shows cache status

**History Tab:**
- Shows previously cached news items
- Displays total items count
- Allows analysis of historical news
- Maintains analysis results

### 2. Filtering System

**Impact Filters:**
- **All**: Shows all news items
- **H (High)**: Shows only high-impact news
- **M (Medium)**: Shows only medium-impact news
- **L (Low)**: Shows only low-impact news

**Filter Logic:**
```javascript
const filteredNews = newsItems.filter(item => {
    if (filter === 'all') return true;
    return item.impact?.toLowerCase() === filter;
});
```

### 3. News Item Display

**News Item Structure:**
```jsx
<div className="news-item">
    <div className="news-item-header">
        <div className="news-source">
            <span className="source-name">{newsItem.source}</span>
            <span className="news-time">{formatTime(newsItem.published_at)}</span>
        </div>
        <div className="news-impact">
            <span className="impact-badge">
                {getImpactIcon(newsItem.impact)} {newsItem.impact}
            </span>
        </div>
    </div>
    
    <div className="news-item-content">
        <h3 className="news-title">{newsItem.title}</h3>
        <p className="news-summary">{newsItem.summary}</p>
        
        {newsItem.currency_pairs && (
            <div className="news-currency-pairs">
                <span className="news-pairs-label">Affected pairs:</span>
                {newsItem.currency_pairs.map(pair => (
                    <span className="news-currency-pair">{pair}</span>
                ))}
            </div>
        )}
    </div>
    
    {selectedNews?.id === newsItem.id && (
        <div className="news-actions">
            <button className="analyze-btn">Analyze with AI</button>
            <a className="read-more-btn" href={newsItem.url}>Read Full Article</a>
        </div>
    )}
</div>
```

### 4. AI Analysis Display

**Sentiment Overview:**
```jsx
<div className="sentiment-overview">
    <div className="sentiment-badge" style={{ backgroundColor: getSentimentColor(aiAnalysis.sentiment) }}>
        {getSentimentIcon(aiAnalysis.sentiment)} {aiAnalysis.sentiment}
    </div>
    <div className="sentiment-metrics">
        <span className="confidence">Confidence: {aiAnalysis.confidence}</span>
        <span className="impact-score">Impact: {aiAnalysis.impact_score}/10</span>
    </div>
</div>
```

**Trading Opportunities:**
```jsx
{aiAnalysis.trading_opportunities.map((opportunity, index) => (
    <div key={index} className="opportunity-item">
        <div className="opportunity-header">
            <span className="pair">{opportunity.pair}</span>
            <span className="strategy">{opportunity.strategy}</span>
            <span className="direction">{opportunity.direction}</span>
        </div>
        <div className="opportunity-details">
            <span className="timeframe">Timeframe: {opportunity.timeframe}</span>
            <span className="confidence">Confidence: {opportunity.confidence}%</span>
            <span className="risk">Risk: {opportunity.risk_level}</span>
        </div>
    </div>
))}
```

## Error Handling

### 1. Backend Error Handling

**News Fetching Errors:**
```python
try:
    response = requests.get(feed_url, headers=headers, timeout=8)
    response.raise_for_status()
except Exception as e:
    logger.error(f"Error fetching RSS feed from {source_name}: {str(e)}")
    return []  # Return empty list, continue with other sources
```

**Analysis Errors:**
```python
try:
    analysis = generate_news_analysis(news_item)
    return jsonify(analysis)
except Exception as e:
    print(f"Error generating analysis: {e}")
    return jsonify(get_mock_news_analysis(news_item.get('title', 'News Event')))
```

**Cache Errors:**
```python
try:
    with open(self.cache_file, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)
except Exception as e:
    logger.error(f"Error loading news from cache: {e}")
    return None  # Return None to trigger fresh fetch
```

### 2. Frontend Error Handling

**Network Errors:**
```javascript
try {
    const response = await fetch(config.endpoints.news);
    const data = await response.json();
    
    if (response.ok) {
        setNews(data.news || []);
        setLastUpdated(data.last_updated);
    } else {
        throw new Error('Failed to fetch news');
    }
} catch (err) {
    console.error('Error fetching news:', err);
    setNews([]);  // Set empty array to show empty state
    setError(null);  // Don't show error, show empty state instead
}
```

**Analysis Errors:**
```javascript
try {
    const response = await fetch(`${config.endpoints.analysis}/${newsItem.id}`);
    const analysis = await response.json();
    
    if (response.ok) {
        setAiAnalysis(analysis);
    } else {
        throw new Error('Failed to analyze news');
    }
} catch (err) {
    console.error('Error analyzing news:', err);
    setError('Failed to analyze news. Please try again.');
}
```

### 3. Fallback Systems

**News Fallback:**
- If RSS feeds fail → Use cached data
- If cache is expired → Use mock data
- If all fails → Show empty state

**Analysis Fallback:**
- If sentiment analysis fails → Use mock analysis
- If news item not found → Try economic event analysis
- If all fails → Return generic analysis

## Performance Optimizations

### 1. Caching Strategy

**Multi-level Caching:**
- **Current News**: 2-hour cache for fresh data
- **History**: Last 100 items for quick access
- **Analysis**: Cached results to reduce processing

**Cache Invalidation:**
```python
# Check if cache is too old
cache_timestamp = datetime.fromisoformat(cache_data['timestamp'])
age = datetime.now() - cache_timestamp

if age > timedelta(hours=self.max_age_hours):
    return None  # Cache expired, fetch fresh data
```

### 2. Data Management

**News Item Limits:**
- **Per Source**: Maximum 3 forex-related articles
- **Total Articles**: Maximum 15 articles
- **History**: Maximum 100 items

**Timeout Management:**
- **RSS Feeds**: 8-second timeout per source
- **Analysis**: 15-second timeout
- **Overall**: 10-second timeout for dashboard

### 3. Frontend Optimizations

**Auto-refresh:**
```javascript
useEffect(() => {
    fetchNews();
    const interval = setInterval(fetchNews, 5 * 60 * 1000); // 5 minutes
    return () => clearInterval(interval);
}, []);
```

**Lazy Loading:**
- History is only loaded when switching to History tab
- Analysis is only generated when user requests it

**State Management:**
- Efficient state updates to prevent unnecessary re-renders
- Proper cleanup of intervals and event listeners

## Testing

### 1. Test Script (`test_live_news_analysis.py`)

**Test Coverage:**
- News endpoint functionality
- History retrieval
- AI analysis generation
- Cache status monitoring
- Error handling

**Running Tests:**
```bash
python3 test_live_news_analysis.py
```

**Expected Output:**
```
🚀 Starting Live News Analysis Tests
==================================================
🔍 Testing News Endpoint...
✅ News endpoint working - 12 articles
   Cache status: fresh
   Sources: ['Reuters', 'Bloomberg']
   Sample article: US CPI Data Release...
   Impact: High
   Currency pairs: ['EUR/USD', 'USD/JPY']

🔍 Testing News History Endpoint...
✅ News history working - 8 items
   Total items in history: 45

🔍 Testing AI Analysis...
✅ AI Analysis working
   Summary: Positive market sentiment detected...
   Confidence: 75%
   Sentiment: bullish
   Analysis type: news_sentiment
   Trading opportunities: 2 found
     - EUR/USD: sentiment_following
     - USD/JPY: sentiment_following

🔍 Testing Get News by ID...
✅ Get news by ID working
   Retrieved: US CPI Data Release...
   Source: Reuters
   Impact: High

🔍 Testing Cache Status...
✅ Cache status: fresh
   Using fresh data

==================================================
🏁 Live News Analysis Tests Complete

📊 Summary:
   News items: 12
   History items: 8
   AI analysis: ✅ Working

💡 Next Steps:
   1. Check the frontend to see the enhanced live news analysis card
   2. Try analyzing news items to see sentiment analysis
   3. Switch between Live and History tabs
   4. Test the filtering by impact level
```

### 2. Manual Testing

**Frontend Testing:**
1. **Live Tab**: Verify news loads and displays correctly
2. **History Tab**: Verify history loads when switching tabs
3. **Filtering**: Test H/M/L filters work correctly
4. **Analysis**: Click on news items and verify AI analysis appears
5. **Responsive**: Test on different screen sizes

**Backend Testing:**
1. **API Endpoints**: Test all endpoints return correct data
2. **Error Handling**: Test with invalid requests
3. **Cache Behavior**: Test cache expiration and refresh
4. **Performance**: Monitor response times

## Troubleshooting

### 1. Common Issues

**No News Loading:**
- Check if backend is running on correct port
- Verify RSS feeds are accessible
- Check network connectivity
- Review backend logs for errors

**Analysis Not Working:**
- Verify news item has valid ID
- Check sentiment analyzer is working
- Review analysis endpoint logs
- Test with mock data

**Cache Issues:**
- Check cache file permissions
- Verify cache directory exists
- Clear cache files if corrupted
- Check disk space

### 2. Debug Commands

**Check Backend Status:**
```bash
curl http://localhost:5001/api/hello
```

**Test News Endpoint:**
```bash
curl http://localhost:5001/api/news
```

**Test Analysis:**
```bash
curl http://localhost:5001/api/analysis/123456789
```

**Clear Cache:**
```python
from services.news_cache import news_cache
news_cache.clear_cache()
news_cache.clear_history()
```

### 3. Log Analysis

**Backend Logs:**
- Look for RSS feed errors
- Check analysis generation errors
- Monitor cache operations
- Verify API endpoint calls

**Frontend Console:**
- Check for network errors
- Verify API responses
- Monitor state changes
- Check for JavaScript errors

### 4. Performance Monitoring

**Response Times:**
- News endpoint: < 2 seconds
- Analysis endpoint: < 5 seconds
- History endpoint: < 1 second

**Cache Hit Rates:**
- Target: > 80% cache hits for news
- Monitor cache expiration patterns
- Track analysis cache usage

**Error Rates:**
- Target: < 5% error rate
- Monitor RSS feed failures
- Track analysis failures

This documentation provides a comprehensive understanding of how the Live News + Analysis Card works, from data collection to user interface, enabling developers to maintain, extend, and troubleshoot the system effectively.
