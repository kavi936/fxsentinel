# Prediction Markets Card - Complete System Documentation

## Table of Contents

1. [Overview](#overview)
2. [Developer Quickstart](#developer-quickstart)
3. [Architecture](#architecture)
4. [Backend Implementation](#backend-implementation)
5. [Frontend Implementation](#frontend-implementation)
6. [Data Flow](#data-flow)
7. [Filtering & Prioritization](#filtering--prioritization)
8. [Caching Strategy](#caching-strategy)
9. [API Integration](#api-integration)
10. [Price Tracking & Conviction Scoring](#price-tracking--conviction-scoring)
11. [Error Handling](#error-handling)
12. [Configuration](#configuration)
13. [File Structure](#file-structure)

---

## Overview

The Prediction Markets card displays retail and institutional trader predictions for economic events (Fed decisions, inflation data, GDP releases) from Polymarket and Kalshi. It aggregates crowd wisdom to provide sentiment indicators that complement technical and fundamental analysis for forex traders.

**Key Features:**
- Fetches prediction market data from Polymarket (via CLOB API) and Kalshi (via DOME API)
- Filters for economic/forex-relevant markets using curated keyword matching
- Displays probability bars showing Yes/No predictions with 24h/48h/7d price deltas
- Shows conviction scores (volume-normalized confidence indicators)
- Handles historical vs active markets intelligently
- Caches data persistently in Firebase to reduce API calls and survive restarts
- Background refresh system for seamless updates without blocking UI

**Purpose:** Provides traders with a sentiment indicator showing what the crowd is betting on regarding key economic events that affect forex markets. This complements technical analysis and fundamental analysis by showing market expectations.

---

## Developer Quickstart

### Important Note: Correct API Usage

**Previous Approach (Incorrect):** The system was previously calling the wrong APIs and using incorrect endpoints. This section documents the correct way to fetch Polymarket data.

**Current Approach (Correct):** Use the Gamma API for event/market discovery and the CLOB API for price data. No authentication required.

### Fetching Market Data

Fetch Polymarket data in minutes with no authentication required. Get market data with zero setup - no API key, no authentication, no wallet required.

### Understanding the Data Model

Before fetching data, understand how Polymarket structures its markets:

1. **Event** - The top-level object representing a question like "Will X happen?"
2. **Market** - Each event contains one or more markets. Each market is a specific tradable binary outcome.
3. **Outcomes & Prices** - Markets have `outcomes` and `outcomePrices` arrays that map 1:1. These prices represent implied probabilities.

**Example:**
```json
{
  "outcomes": "[\"Yes\", \"No\"]",
  "outcomePrices": "[\"0.20\", \"0.80\"]"
}
// Index 0: "Yes" → 0.20 (20% probability)
// Index 1: "No" → 0.80 (80% probability)
```

### Fetch Active Events

List all currently active events on Polymarket:

```bash
curl "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=5"
```

**Example Response:**
```json
[
  {
    "id": "123456",
    "slug": "will-bitcoin-reach-100k-by-2025",
    "title": "Will Bitcoin reach $100k by 2025?",
    "active": true,
    "closed": false,
    "tags": [
      { "id": "21", "label": "Crypto", "slug": "crypto" }
    ],
    "markets": [
      {
        "id": "789",
        "question": "Will Bitcoin reach $100k by 2025?",
        "clobTokenIds": ["TOKEN_YES_ID", "TOKEN_NO_ID"],
        "outcomes": "[\"Yes\", \"No\"]",
        "outcomePrices": "[\"0.65\", \"0.35\"]"
      }
    ]
  }
]
```

**Important:** Always use `active=true&closed=false` to filter for live, tradable events.

### Market Discovery Best Practices

#### For Sports Events

Use the `/sports` endpoint to discover leagues, then query by `series_id`:

```bash
# Get all supported sports leagues
curl "https://gamma-api.polymarket.com/sports"

# Get events for a specific league (e.g., NBA series_id=10345)
curl "https://gamma-api.polymarket.com/events?series_id=10345&active=true&closed=false"

# Filter to just game bets (not futures) using tag_id=100639
curl "https://gamma-api.polymarket.com/events?series_id=10345&tag_id=100639&active=true&closed=false&order=startTime&ascending=true"
```

**Note:** `/sports` only returns automated leagues. For others (UFC, Boxing, F1, Golf, Chess), use tag IDs via `/events?tag_id=<tag_id>`.

#### For Non-Sports Topics

Use `/tags` to discover all available categories, then filter events:

```bash
# Get all available tags
curl "https://gamma-api.polymarket.com/tags?limit=100"

# Query events by topic
curl "https://gamma-api.polymarket.com/events?tag_id=2&active=true&closed=false"
```

Each event response includes a `tags` array, useful for discovering categories from live data and building your own tag mapping.

### Get Market Details

Once you have an event, get details for a specific market using its ID or slug:

```bash
curl "https://gamma-api.polymarket.com/markets?slug=will-bitcoin-reach-100k-by-2025"
```

The response includes `clobTokenIds` - you'll need these to fetch prices and place orders.

### Get Current Price

Query the CLOB for the current price of any token:

```bash
curl "https://clob.polymarket.com/price?token_id=YOUR_TOKEN_ID&side=buy"
```

**Example Response:**
```json
{
  "price": "0.65"
}
```

### Get Orderbook Depth

See all bids and asks for a market:

```bash
curl "https://clob.polymarket.com/book?token_id=YOUR_TOKEN_ID"
```

**Example Response:**
```json
{
  "market": "0x...",
  "asset_id": "YOUR_TOKEN_ID",
  "bids": [
    { "price": "0.64", "size": "500" },
    { "price": "0.63", "size": "1200" }
  ],
  "asks": [
    { "price": "0.66", "size": "300" },
    { "price": "0.67", "size": "800" }
  ]
}
```

### Key Takeaways for FXSentinel Implementation

1. **Use Gamma API for Discovery**: `/events` endpoint with `active=true&closed=false` to find active markets
2. **Use CLOB API for Prices**: `/price` endpoint for current prices, `/book` for orderbook depth
3. **No Authentication Required**: Both APIs are public and require no API keys
4. **Filter by Tags**: Use `/tags` to discover economic/political categories, then filter events by `tag_id`
5. **Parse outcomePrices**: The `outcomePrices` array contains probabilities - index 0 is "Yes", index 1 is "No"

---

## Architecture

### System Flow

```
┌─────────────────┐
│   Frontend       │
│  (React/JSX)    │
│                 │
│  Overview Card  │
│  usePrediction  │
│  Markets Hook   │
└────────┬────────┘
         │ HTTP GET
         │ /api/prediction-markets
         ▼
┌─────────────────┐
│   Backend API   │
│   (Flask)       │
│                 │
│  app.py         │
│  /api/prediction│
│  -markets       │
└────────┬────────┘
         │ Calls Service
         ▼
┌─────────────────┐
│  Service Layer  │
│                 │
│  prediction_    │
│  markets_       │
│  service.py     │
│                 │
│  - Fetches from │
│    Polymarket   │
│    (Gamma API   │
│     for events, │
│     CLOB for    │
│     prices)     │
│  - Fetches from │
│    Kalshi       │
│    (DOME API)   │
│  - Filters      │
│  - Normalizes   │
│  - Caches       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cache Layer    │
│                 │
│  Firebase       │
│  Realtime DB    │
│  (persistent)   │
│                 │
│  OR             │
│                 │
│  File Cache     │
│  (fallback)     │
└─────────────────┘
```

### Component Hierarchy

1. **Frontend Component** (`src/components/Overview.jsx`)
   - Renders the prediction markets card UI
   - Uses `usePredictionMarkets` hook for data
   - Handles loading, error, and empty states
   - Displays markets with probability bars and metadata

2. **React Hook** (`src/hooks/usePredictionMarkets.js`)
   - Manages state (loading, error, markets)
   - Fetches data from `/api/prediction-markets`
   - Provides refresh function
   - Handles error recovery (keeps existing data on transient errors)

3. **Backend API Route** (`backend/app.py`)
   - Flask route handler for `/api/prediction-markets`
   - Handles CORS preflight requests
   - Validates query parameters (`refresh` flag)
   - Calls `prediction_markets_service.get_prediction_markets()`
   - Returns JSON response with markets array and summary

4. **Service Layer** (`backend/services/prediction_markets_service.py`)
   - Main business logic for fetching, filtering, and normalizing markets
   - Handles multiple data sources (Polymarket Gamma API for events, CLOB API for prices, Kalshi DOME, PolyRouter)
   - **Note:** Should use Gamma API (`/events`) for market discovery, not CLOB `/markets` endpoint
   - Implements filtering using curated keywords
   - Calculates price deltas and conviction scores
   - Manages caching (Firebase persistent or file-based fallback)

5. **Supporting Services**
   - `curated_prediction_markets.py`: Curated list of high-value markets with priority scoring
   - `persistent_prediction_markets_cache.py`: Firebase-based persistent cache
   - `dome_api_rate_limiter.py`: Rate limiting for DOME API calls
   - `polyrouter_api_client.py`: PolyRouter API client (optional unified API)

---

## Backend Implementation

### Service Class: `PredictionMarketsService`

**Location:** `backend/services/prediction_markets_service.py`

**Initialization:**

The service initializes with tier-based configuration (free vs paid):

```python
class PredictionMarketsService:
    def __init__(self):
        # Detect API tier (default to free tier for safety)
        self.is_free_tier = os.getenv('DOME_API_TIER', 'free').lower() == 'free'
        
        # Free tier: 2 pages per platform, 30min cache, no price fetching
        # Paid tier: 5/3 pages per platform, 10min cache, price fetching enabled
```

**Key Configuration:**

- **Free Tier:**
  - Max 2 pages per platform (Polymarket/Kalshi)
  - 30-minute cache expiration
  - Background refresh every 20 minutes
  - Early stop threshold: 2000 markets
  - No price fetching via API (uses embedded prices only)

- **Paid Tier:**
  - Max 5 pages Polymarket, 3 pages Kalshi
  - 10-minute cache expiration
  - Background refresh every 5 minutes
  - Early stop threshold: 150 markets
  - Price fetching enabled (if `FETCH_MARKET_PRICES=true`)

**Data Sources:**

1. **Polymarket CLOB API** (Primary - default)
   - Endpoint: `https://clob.polymarket.com/markets`
   - Method: Direct HTTP requests (no auth required)
   - Rate limit: 0.5s delay between requests
   - Pagination: `limit=1000`, `cursor` for next page
   - Max pages: 3 (3,000 markets) by default

2. **Kalshi via DOME API** (Secondary)
   - Endpoint: `https://api.domeapi.io/v1/kalshi`
   - Method: DOME API SDK or HTTP fallback
   - Rate limit: 1 request/second (free tier), 10 requests/10 seconds max
   - Requires: `DOME_API_KEY` environment variable
   - Max pages: 2 (free tier), 3 (paid tier)

3. **PolyRouter API** (Optional - unified API)
   - Provides normalized data from multiple platforms
   - Requires: `POLYROUTER_API_KEY` environment variable
   - Enabled by default if available (`USE_POLYROUTER=true`)

### Core Methods

**`get_prediction_markets(force_refresh=False)`**

Main public method that returns filtered markets. Implements smart caching strategy:

1. Loads cache (even if stale) for fast UI response
2. Checks if should fetch new markets (based on last_fetch interval)
3. If cache exists and not forcing refresh, returns stale cache immediately
4. If should fetch new, triggers background refresh (non-blocking)
5. Only blocks and waits if `force_refresh=True` AND no refresh in progress

**Returns:**
```python
{
    "status": "success" | "error",
    "markets": [List of market dicts],
    "cached": bool,
    "stale": bool,  # True if cache is stale but returned for fast UI
    "timestamp": "ISO timestamp",
    "error": "Error message if status=error"
}
```

**`_do_refresh(force_refresh=False)`**

Internal method that performs the actual data refresh. Called with lock protection to prevent concurrent refreshes.

**Process:**
1. Fetches markets from all available sources (PolyRouter, Polymarket CLOB, Kalshi DOME)
2. Filters for economic relevance using `_filter_economic_markets()`
3. Normalizes market data using `_normalize_market_data()`
4. Sorts by priority (conviction score, price delta, volume, etc.)
5. Limits to top 10 markets (configurable via `MAX_FILTERED_MARKETS`)
6. Saves to cache (Firebase or file)
7. Returns result

**`_fetch_polymarket_markets(early_stop_threshold=None)`**

Fetches markets from Polymarket. **Note:** Current implementation uses CLOB API `/markets` endpoint, but should be updated to use Gamma API `/events` endpoint for proper market discovery (see Developer Quickstart section).

**Current Process:**
1. Calls `_fetch_polymarket_clob_direct()` if `USE_DIRECT_CLOB=true`
2. Makes paginated requests to `https://clob.polymarket.com/markets` (legacy endpoint)
3. Stops early if threshold reached (default: 2000 markets for free tier)
4. Returns list of raw market dictionaries

**Recommended Process (to be implemented):**
1. Use Gamma API `/events` endpoint with `active=true&closed=false`
2. Filter by economic tags using `/tags` endpoint to discover relevant tag IDs
3. Fetch market details using `/markets?slug=...` for specific markets
4. Use CLOB API `/price` endpoint to get current prices using `clobTokenIds` from Gamma API

**`_fetch_kalshi_markets(early_stop_threshold=None)`**

Fetches markets from Kalshi via DOME API.

**Process:**
1. Uses DOME API SDK or HTTP fallback
2. Respects rate limiting (1 req/sec for free tier)
3. Makes paginated requests with `limit` and `offset`
4. Returns list of raw market dictionaries

**`_filter_economic_markets(markets)`**

Filters markets for economic/forex relevance using keyword matching and curated market priorities.

**Filtering Criteria:**

1. **Inclusion Requirements:**
   - Market must have unique ID (deduplication)
   - Must not be archived
   - Must match at least one economic keyword (see keyword list below)
   - Must not match exclude keywords (sports, entertainment, etc.)
   - Must have valid data structure

2. **Date Filtering:**
   - **Active markets**: `accepting_orders=true` → Always included
   - **Future markets**: Resolution date in future → Included
   - **Recently resolved**: Closed within last 30 days → Included
   - **Historical markets**: Closed > 30 days ago → Only if `relevance="high"`

3. **Keyword Matching:**
   - Uses curated keywords from `curated_prediction_markets.py`
   - Matches against market title/question, description, tags
   - Special handling: `"fed"` uses regex word boundary to avoid false matches

4. **Relevance Scoring:**
   - **High**: Fed/FOMC, inflation/CPI, employment/NFP, central banks (ECB, BOE, BOJ)
   - **Medium**: GDP, general economic keywords
   - **Low**: Other economic-related keywords

5. **Priority Scoring:**
   - Uses `get_market_priority()` from curated markets
   - Priority 1: Fed, CPI, NFP, ECB, BOE, BOJ
   - Priority 2: GDP, political events
   - Priority 3: Gold/commodities

**`_normalize_market_data(market, fetch_price=False)`**

Converts raw market data from various sources into standardized format.

**Process:**
1. Detects platform (Polymarket vs Kalshi)
2. Extracts prices using `_extract_prices_from_dome_market()` or CLOB price extraction
3. Calculates price deltas from historical snapshots
4. Calculates conviction score (volume-normalized)
5. Determines market status (active, closed, resolved, future, historical)
6. Extracts metadata (resolution date, volume, liquidity, URL)
7. Returns normalized market dictionary

**Returns:**
```python
{
    "id": "market_id",
    "platform": "polymarket" | "kalshi",
    "question": "Market question/title",
    "description": "Market description",
    "category": "Category name",
    "yes_price": 0.65,  # Probability (0.0-1.0)
    "no_price": 0.35,   # Probability (0.0-1.0)
    "price_source": "resolved" | "api" | "embedded" | "fallback",
    "price_quality": "high" | "medium" | "low",
    "liquidity": 10000.0,
    "volume": 50000.0,
    "resolution_date": "2024-02-15T00:00:00Z",
    "active": True,
    "closed": False,
    "accepting_orders": True,
    "is_resolved": False,
    "is_future": True,
    "is_historical": False,
    "is_recently_resolved": False,
    "days_until_resolution": 30,
    "relevance": "high" | "medium" | "low",
    "related_event": "FOMC Meeting",
    "affected_currency_pairs": ["EUR/USD", "GBP/USD"],
    "url": "https://polymarket.com/...",
    "price_delta_24h": 2.5,  # Percentage point change
    "price_delta_48h": 5.0,
    "price_delta_7d": -3.2,
    "conviction_score": 75,  # 0-100
    "conviction_level": "high" | "medium" | "low"
}
```

**`_extract_prices_from_dome_market(market, fetch_price=False)`**

Extracts Yes/No prices from market data. Handles multiple data formats (CLOB, DOME, PolyRouter).

**Price Sources (priority order):**
1. **Resolved markets**: Prices are 1.0/0.0 (certain outcome)
2. **API fetch**: If `fetch_price=True` and paid tier, fetches via API
3. **Embedded prices**: From market data structure (Kalshi markets have this)
4. **Fallback**: 50/50 estimate if no price data available

**`_calculate_price_deltas(market_id, yes_price, no_price)`**

Calculates price changes over 24h, 48h, and 7d periods using historical price snapshots.

**Process:**
1. Retrieves price history for market from `self.price_history`
2. Finds snapshots at 24h, 48h, and 7d ago
3. Calculates percentage point changes (not percentage changes)
4. Returns deltas: `{"delta_24h": 2.5, "delta_48h": 5.0, "delta_7d": -3.2}`

**`_store_price_snapshot(market_id, yes_price, no_price)`**

Stores current price snapshot for future delta calculations. Maintains rolling history in `self.price_history`.

**Conviction Scoring:**

Conviction score is a volume-normalized confidence indicator (0-100):

```python
conviction_score = min(100, (volume / max_volume) * 100)
```

Where `max_volume` is the maximum volume seen across all markets. This normalizes volume to show relative confidence/trading activity.

**Conviction Levels:**
- **High**: Score >= 70
- **Medium**: Score >= 40
- **Low**: Score < 40

---

## Frontend Implementation

### React Hook: `usePredictionMarkets`

**Location:** `src/hooks/usePredictionMarkets.js`

**State Management:**

```javascript
const [markets, setMarkets] = useState(fallbackMarkets)
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)
const [lastUpdate, setLastUpdate] = useState(null)
```

**Fetch Function:**

```javascript
const fetchMarkets = useCallback(async (forceRefresh = false) => {
  // Sets loading state
  // Makes HTTP GET to /api/prediction-markets?refresh=true if forceRefresh
  // Handles errors gracefully (keeps existing data on transient errors)
  // Updates state with new data
}, [])
```

**Return Values:**

```javascript
{
  markets: Array,        // Array of market objects
  summary: Object,       // Summary metadata
  loading: Boolean,      // Loading state
  error: String|null,    // Error message if any
  lastUpdate: Date,      // Last successful update timestamp
  refresh: Function     // Function to force refresh
}
```

**Hook Behavior:**
- Fetches data on component mount
- Handles loading and error states
- Provides refresh function for manual updates
- Keeps existing data on transient errors (doesn't clear on network failures)

### Component: Prediction Markets Card

**Location:** `src/components/Overview.jsx` (lines ~3530-3864)

**Component Structure:**

```jsx
<div className="prediction-markets-card">
  <div className="prediction-markets-header">
    {/* Title and refresh button */}
  </div>
  <div className="prediction-markets-content">
    {loading ? (
      <LoadingState />
    ) : error ? (
      <ErrorState />
    ) : markets.length === 0 ? (
      <EmptyState />
    ) : (
      <>
        {allHistorical && <NoticeBanner />}
        <MarketsList />
      </>
    )}
  </div>
</div>
```

**Key Variables:**
- `predictionMarkets` - Array of market objects from hook
- `predictionMarketsLoading` - Loading state
- `predictionMarketsError` - Error state
- `refreshPredictionMarkets` - Refresh function

**Market Rendering:**

Each market is rendered with:
1. **Question/Title**: Market question text
2. **Conviction Badge**: Shows conviction level (HIGH/MEDIUM/LOW) if score > 0
3. **Price Delta Badge**: Shows 24h price change if significant (>= 5%)
4. **Probability Bar**: Visual bar showing Yes/No percentages
5. **Metadata Row**: Resolution date, conviction score, link to platform

**Filtering Logic:**

Frontend filters markets to show:
- Active markets (not resolved, not closed)
- Recently resolved markets (within 30 days) for context

**Sorting:**

Markets are sorted by:
1. Volume (highest first)
2. Accepting orders (active markets first)
3. Future markets (not resolved yet)

**Empty State:**

When no markets available, shows:
- Empty state message
- Fallback: Upcoming high-impact events from economic calendar (top 5)

**Notice Banner:**

Shows when ALL markets are historical/resolved:
```
⏳ No Active Markets
No active prediction markets available at this time. Check back later for new markets on upcoming economic events.
```

### Styling

**Location:** `src/components/Overview.css` (lines ~7379-8630)

**Key CSS Classes:**

- `.prediction-markets-card` - Main card container with gradient background
- `.prediction-markets-header` - Header with title and controls
- `.prediction-markets-content` - Scrollable content area
- `.prediction-market-item` - Individual market card
- `.probability-bar-container` - Container for probability visualization
- `.probability-fill.yes-fill` - Green fill for Yes probability
- `.probability-fill.no-fill` - Red fill for No probability
- `.conviction-badge` - Badge showing conviction level
- `.price-delta` - Badge showing price change (positive/negative/neutral)

**Visual Design:**
- Dark theme with blue accent colors
- Gradient backgrounds for depth
- Smooth transitions and hover effects
- Responsive layout with scrollable content

---

## Data Flow

### Complete Request Flow

1. **User Opens Overview Page**
   - React component mounts
   - `usePredictionMarkets` hook initializes

2. **Frontend Hook Fetches Data**
   - Hook calls `/api/prediction-markets`
   - Sets loading state to `true`
   - Makes HTTP GET request

3. **Backend Receives Request**
   - Flask route handler processes request
   - Validates `refresh` query parameter
   - Imports and calls `prediction_markets_service.get_prediction_markets()`

4. **Service Checks Cache**
   - Loads cache from Firebase (or file fallback)
   - Checks if cache is valid (< expiration time)
   - If valid and not forcing refresh, returns cached data immediately

5. **Service Fetches Fresh Data** (if cache invalid or force_refresh)
   - Fetches from PolyRouter API (if available)
   - Fetches from Polymarket Gamma API (`/events`) for market discovery
   - Fetches prices from Polymarket CLOB API (`/price`) using `clobTokenIds` from Gamma API
   - **Note:** Current implementation may still use legacy CLOB `/markets` endpoint - should be updated to Gamma API
   - Fetches from Kalshi via DOME API
   - Combines all markets into single list

6. **Service Filters Markets**
   - Filters for economic relevance using keyword matching
   - Applies date filtering (active/future/recently resolved)
   - Removes duplicates
   - Scores by relevance and priority

7. **Service Normalizes Data**
   - Extracts prices from various formats
   - Calculates price deltas from historical snapshots
   - Calculates conviction scores
   - Normalizes to standard format

8. **Service Sorts & Limits**
   - Sorts by conviction score, price delta, volume, priority
   - Limits to top 10 markets (configurable)

9. **Service Saves to Cache**
   - Saves to Firebase Realtime Database (persistent)
   - Falls back to file cache if Firebase unavailable
   - Stores price history for delta calculations

10. **Service Returns Result**
    - Returns JSON with markets array and summary
    - Includes cache status and timestamp

11. **Backend Returns Response**
    - Flask returns JSON response
    - Includes CORS headers

12. **Frontend Updates State**
    - Hook receives response
    - Updates markets state
    - Sets loading to `false`
    - Updates lastUpdate timestamp

13. **Component Renders**
    - Maps through markets array
    - Renders each market with probability bars
    - Shows loading/error/empty states as needed

### Background Refresh Flow

When cache is stale but user hasn't requested refresh:

1. Service returns stale cache immediately (fast UI)
2. Service triggers background refresh (non-blocking)
3. Background refresh fetches new data
4. Background refresh saves to cache
5. Next request gets fresh data from cache

This ensures fast UI response while keeping data fresh.

---

## Filtering & Prioritization

### Curated Markets System

**Location:** `backend/services/curated_prediction_markets.py`

**Purpose:** Maintains curated list of high-value markets that provide actionable trading signals for forex traders.

**Categories:**

1. **Priority 1 Markets** (Highest priority):
   - Fed/FOMC: Interest rate decisions, FOMC meetings
   - CPI/Inflation: Consumer Price Index, inflation data
   - Employment/NFP: Non-farm payrolls, jobs reports
   - ECB: European Central Bank policy decisions
   - BOE: Bank of England policy decisions
   - BOJ: Bank of Japan policy decisions

2. **Priority 2 Markets**:
   - GDP: Gross Domestic Product releases
   - Political Events: Elections, policy changes affecting forex

3. **Priority 3 Markets**:
   - Gold/Commodities: Precious metals, commodity prices

**Functions:**

- `get_curated_keywords()`: Returns list of all keywords from curated markets
- `get_market_priority(keywords_matched)`: Returns priority score (1-3) based on matched keywords
- `get_affected_pairs_for_keywords(keywords_matched)`: Returns currency pairs affected by matched keywords

### Economic Keywords

**Included Keywords:**

- **Federal Reserve & US Rates**: "federal reserve", "fed", "fomc", "interest rate", "rate hike", "rate cut", "jerome powell"
- **Inflation & Economic Data**: "inflation", "cpi", "consumer price index", "ppi", "gdp", "employment", "non-farm payrolls", "nfp", "unemployment"
- **Central Banks**: "ecb", "european central bank", "christine lagarde", "bank of england", "boe", "bank of japan", "boj"
- **Forex Pairs**: "eur/usd", "gbp/usd", "usd/jpy", "usd/chf", "aud/usd", "nzd/usd", "usd/cad"
- **Economic Indicators**: "pmi", "ism", "consumer confidence", "retail sales", "industrial production"
- **Political Events**: "trump", "biden", "election", "presidential", "congress", "senate"
- **Geopolitical**: "brexit", "sanctions", "war", "conflict", "crisis", "nato"

**Excluded Keywords:**

- Sports: "nba", "nfl", "football", "basketball"
- Entertainment: "oscar", "award", "movie", "film", "actor"
- Gaming: "dota", "counter-strike", "esports", "gaming"
- Crypto price movements: "bitcoin up or down", "ethereum up or down", "15m", "30m", "1h", "4h"

### Sorting Priority

Markets are sorted by (in order):

1. **Conviction Score** (high to low) - Volume-normalized confidence
2. **Price Delta Magnitude** (absolute value, high to low) - Surfaces shifting markets
3. **Priority Score** (curated markets) - Higher priority markets first
4. **Volume** (high to low) - More trading activity = higher priority
5. **Accepting Orders** (active markets first) - Currently tradeable markets
6. **Future Markets** (not resolved yet) - Upcoming events prioritized
7. **Relevance Score** (high > medium > low) - Economic relevance

**Result:** Top 10 markets returned (configurable via `MAX_FILTERED_MARKETS`)

---

## Caching Strategy

### Persistent Cache (Firebase)

**Location:** `backend/services/persistent_prediction_markets_cache.py`

**Purpose:** Stores prediction markets cache in Firebase Realtime Database. Survives app restarts and deployments (unlike local JSON files).

**Implementation:**

- Uses `FirebaseRealtimeStorage` for database access
- Stores cache at path: `prediction_markets_cache/current`
- Includes metadata: timestamp, markets_count, last_fetch, max_age_minutes
- Stores price history for delta calculations

**Cache Structure:**

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "markets_count": 10,
  "markets": [...],
  "max_age_minutes": 30,
  "last_fetch": "2024-01-15T10:30:00Z",
  "price_history": {
    "market_id_1": [
      {"timestamp": "2024-01-15T10:00:00Z", "yes_price": 0.65, "no_price": 0.35},
      ...
    ]
  }
}
```

**Cache Validity:**

- **Free Tier**: 30 minutes
- **Paid Tier**: 10 minutes

**Background Refresh:**

- **Free Tier**: Every 20 minutes
- **Paid Tier**: Every 5 minutes

### File Cache (Fallback)

**Location:** `backend/prediction_markets_cache.json`

**Purpose:** Fallback cache if Firebase unavailable. Local file-based storage.

**Limitations:**
- Doesn't survive deployments
- Not shared across instances
- Less reliable than Firebase

### Cache Loading Strategy

1. **Load cache immediately** (even if stale) for fast UI response
2. **Check if should fetch new** markets (based on last_fetch interval)
3. **Return stale cache immediately** if exists and not forcing refresh
4. **Trigger background refresh** if cache is stale (non-blocking)
5. **Only block and wait** if `force_refresh=True` AND no refresh in progress

This ensures:
- Fast UI response (always returns cache immediately if available)
- Fresh data (background refresh keeps cache updated)
- No blocking (UI never waits for API calls unless explicitly requested)

---

## API Integration

### Polymarket Gamma API (Event/Market Discovery)

**Endpoint:** `https://gamma-api.polymarket.com/events`

**Method:** Direct HTTP GET requests (no authentication required)

**Purpose:** Use Gamma API for discovering active events and markets. This is the correct API for market discovery.

**Key Parameters:**
- `active=true` - Filter for active events (required)
- `closed=false` - Exclude closed events (required)
- `limit` - Number of events per page
- `tag_id` - Filter by category/tag ID
- `series_id` - Filter by sports league series ID

**Example Request:**
```bash
curl "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=100"
```

**Response Format:**
- Returns JSON array of event objects
- Each event contains: `id`, `slug`, `title`, `active`, `closed`, `tags`, `markets[]`
- Each market has: `id`, `question`, `clobTokenIds[]`, `outcomes`, `outcomePrices`

**Important:** Always use `active=true&closed=false` to filter for live, tradable events.

**Tag Discovery:**
```bash
# Get all available tags/categories
curl "https://gamma-api.polymarket.com/tags?limit=100"

# Filter events by tag (e.g., Economics tag_id=2)
curl "https://gamma-api.polymarket.com/events?tag_id=2&active=true&closed=false"
```

**Market Details:**
```bash
# Get specific market by slug
curl "https://gamma-api.polymarket.com/markets?slug=will-bitcoin-reach-100k-by-2025"
```

### Polymarket CLOB API (Price Data)

**Endpoints:**
- `https://clob.polymarket.com/price` - Get current price for a token
- `https://clob.polymarket.com/book` - Get orderbook depth for a token
- `https://clob.polymarket.com/markets` - Legacy endpoint (still works but Gamma API preferred for discovery)

**Method:** Direct HTTP GET requests (no authentication required)

**Purpose:** Use CLOB API for fetching current prices and orderbook data. Requires `clobTokenIds` from Gamma API.

**Get Current Price:**
```bash
curl "https://clob.polymarket.com/price?token_id=YOUR_TOKEN_ID&side=buy"
```

**Get Orderbook:**
```bash
curl "https://clob.polymarket.com/book?token_id=YOUR_TOKEN_ID"
```

**Rate Limiting:**
- 0.5 second delay between requests (configurable via `CLOB_REQUEST_DELAY`)
- No hard rate limit (but respects delays)

**Configuration:**
- `USE_DIRECT_CLOB=true` (default) - Use CLOB API for prices
- `CLOB_MAX_PAGES=3` (default) - Max pages to fetch (if using legacy `/markets` endpoint)

### Kalshi via DOME API

**Endpoint:** `https://api.domeapi.io/v1/kalshi`

**Method:** DOME API SDK or HTTP fallback

**Authentication:** Requires `DOME_API_KEY` environment variable

**Rate Limiting:**
- Free tier: 1 request/second, max 10 requests per 10 seconds
- Paid tier: Higher limits (varies by plan)

**Data Format:**
- Returns JSON with markets array
- Each market has: `question_id`, `title`, `side_a`, `side_b`, `last_price`, `status`, etc.

**Configuration:**
- `DOME_API_KEY` - Required for Kalshi access
- `DOME_API_TIER=free` (default) - Tier level (free/paid)

### PolyRouter API (Optional)

**Purpose:** Unified API providing normalized data from multiple platforms

**Configuration:**
- `USE_POLYROUTER=true` (default) - Enable PolyRouter if available
- `POLYROUTER_API_KEY` - Required for PolyRouter access

**Benefits:**
- Normalized data format
- Multiple platforms in one API
- Better rate limits potentially

---

## Price Tracking & Conviction Scoring

### Price Delta Calculation

**Purpose:** Track how market probabilities change over time to identify shifting sentiment.

**Implementation:**

1. **Store Price Snapshots**: After normalizing each market, store current prices with timestamp
2. **Calculate Deltas**: When normalizing, compare current prices to historical snapshots
3. **Time Periods**: Calculate deltas for 24h, 48h, and 7d periods
4. **Format**: Percentage point changes (not percentage changes)

**Example:**
- Current Yes price: 65%
- 24h ago Yes price: 60%
- Delta 24h: +5 percentage points

**Storage:**
- Price history stored in `self.price_history` dict
- Format: `{market_id: [{"timestamp": "...", "yes_price": 0.65, "no_price": 0.35}, ...]}`
- Persisted to Firebase cache for survival across restarts

**Display:**
- Frontend shows delta badge if change >= 5 percentage points
- Color coding: Green (positive), Red (negative), Neutral (small changes)

### Conviction Scoring

**Purpose:** Volume-normalized confidence indicator showing relative trading activity/confidence.

**Calculation:**

```python
max_volume = max(all market volumes)
conviction_score = min(100, (market_volume / max_volume) * 100)
```

**Levels:**
- **High**: Score >= 70 (high trading activity/confidence)
- **Medium**: Score >= 40 (moderate activity)
- **Low**: Score < 40 (low activity)

**Display:**
- Frontend shows conviction badge (HIGH/MEDIUM/LOW) if score > 0
- Badge color varies by level
- Helps identify markets with strong trader conviction

**Rationale:**
- Raw volume alone doesn't indicate confidence (some markets naturally have higher volume)
- Normalizing by max volume shows relative confidence across all markets
- Helps prioritize markets where traders are most confident

---

## Error Handling

### Backend Error Handling

**Service Level:**

1. **API Failures:**
   - Logs error with details
   - Returns cached data if available
   - Returns error status if no cache

2. **Rate Limit Errors:**
   - Respects rate limits with delays
   - Tracks API calls to avoid exceeding limits
   - Falls back to cached data if rate limited

3. **Invalid Data:**
   - Validates market data structure
   - Filters out invalid markets
   - Continues processing valid markets

4. **Cache Failures:**
   - Falls back to file cache if Firebase fails
   - Continues operation even if cache unavailable
   - Logs warnings but doesn't fail

**API Route Level:**

1. **Invalid Parameters:**
   - Validates `refresh` parameter (must be 'true' or 'false')
   - Returns 400 error with message if invalid

2. **Service Exceptions:**
   - Catches all exceptions
   - Returns 500 error with error message
   - Includes error in response JSON

### Frontend Error Handling

**Hook Level:**

1. **Network Errors:**
   - Catches fetch errors
   - Sets error state
   - Keeps existing data (doesn't clear on transient errors)

2. **Invalid Responses:**
   - Validates response structure
   - Checks for `status === 'success'`
   - Sets error if response invalid

3. **Error Recovery:**
   - Provides retry button in error state
   - Allows manual refresh
   - Preserves user experience

**Component Level:**

1. **Loading State:**
   - Shows spinner while loading
   - Prevents user interaction during load

2. **Error State:**
   - Shows error message
   - Provides retry button
   - Doesn't break UI layout

3. **Empty State:**
   - Shows friendly message
   - Provides fallback (upcoming events)
   - Maintains card structure

---

## Configuration

### Environment Variables

**Required:**
- `DOME_API_KEY` - DOME API key for Kalshi access (optional if only using Polymarket)

**Optional:**
- `DOME_API_TIER` - API tier level: `free` (default) or `paid`
- `USE_DIRECT_CLOB` - Use Polymarket CLOB API directly: `true` (default) or `false`
- `CLOB_MAX_PAGES` - Max pages to fetch from CLOB: `3` (default)
- `CLOB_REQUEST_DELAY` - Delay between CLOB requests (seconds): `0.5` (default)
- `USE_POLYROUTER` - Enable PolyRouter API: `true` (default) or `false`
- `POLYROUTER_API_KEY` - PolyRouter API key (optional)
- `FETCH_MARKET_PRICES` - Fetch prices via API (paid tier only): `false` (default) or `true`

**Firebase Configuration:**
- Firebase credentials configured via `firebase_realtime_storage.py`
- Uses Firebase Realtime Database for persistent cache

### Service Constants

**Free Tier Defaults:**
```python
FREE_TIER_MAX_PAGES_PER_PLATFORM = 2
FREE_TIER_EARLY_STOP_THRESHOLD = 2000
FREE_TIER_CACHE_EXPIRATION_MINUTES = 30
FREE_TIER_BACKGROUND_REFRESH_INTERVAL_MINUTES = 20
FREE_TIER_MAX_PRICE_FETCH_MARKETS = 5
```

**Paid Tier Defaults:**
```python
PAID_TIER_MAX_PAGES_POLYMARKET = 5
PAID_TIER_MAX_PAGES_KALSHI = 3
PAID_TIER_EARLY_STOP_THRESHOLD = 150
PAID_TIER_CACHE_EXPIRATION_MINUTES = 10
PAID_TIER_BACKGROUND_REFRESH_INTERVAL_MINUTES = 5
PAID_TIER_MAX_PRICE_FETCH_MARKETS = 20
```

**Filtering Limits:**
```python
MAX_FILTERED_MARKETS = 10  # Maximum markets to return
RECENTLY_RESOLVED_DAYS = 30  # Markets resolved within this period are "recent"
CLOSED_MARKET_GRACE_PERIOD_DAYS = 30  # Allow closed markets within this period
```

---

## File Structure

### Backend Files

```
backend/
├── app.py                                    # Flask API route: /api/prediction-markets
├── services/
│   ├── prediction_markets_service.py         # Main service class (3017 lines)
│   ├── curated_prediction_markets.py        # Curated markets configuration
│   ├── persistent_prediction_markets_cache.py  # Firebase persistent cache
│   ├── dome_api_rate_limiter.py             # Rate limiting for DOME API
│   ├── polyrouter_api_client.py            # PolyRouter API client (optional)
│   └── firebase_realtime_storage.py         # Firebase storage utility
└── prediction_markets_cache.json            # File cache fallback
```

### Frontend Files

```
src/
├── components/
│   ├── Overview.jsx                         # Prediction markets card component (lines ~3530-3864)
│   └── Overview.css                         # Styles (lines ~7379-8630)
├── hooks/
│   └── usePredictionMarkets.js              # React hook for fetching markets
└── config.js                                # API endpoint configuration
```

### Documentation

```
docs/
└── PREDICTION_MARKETS_SYSTEM.md             # This comprehensive documentation
```

---

## Summary

The Prediction Markets card system is a comprehensive solution for displaying crowd-sourced predictions on economic events relevant to forex trading. It integrates multiple data sources (Polymarket, Kalshi), filters for relevance using curated keywords, tracks price changes over time, calculates conviction scores, and caches data persistently for fast UI response.

**Key Strengths:**
- Multi-source data aggregation (Polymarket CLOB, Kalshi DOME, PolyRouter)
- Intelligent filtering using curated economic keywords
- Persistent caching for fast UI and data survival
- Background refresh for seamless updates
- Price delta tracking for sentiment shifts
- Conviction scoring for market confidence
- Robust error handling and fallbacks
- Tier-based configuration (free/paid)

**Use Cases:**
- Traders want to see market expectations for Fed decisions
- Traders want sentiment indicators for upcoming economic releases
- Traders want to track how market expectations change over time
- Traders want to identify high-conviction markets (strong trader confidence)

**Future Enhancements:**
- Integration with economic calendar for event correlation
- Historical performance tracking (prediction accuracy)
- Comparison with rates-implied probabilities
- Integration into macro narratives as supporting evidence
- Alert system for significant probability shifts

