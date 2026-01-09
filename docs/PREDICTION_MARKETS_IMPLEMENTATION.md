# Prediction Markets Card - Technical Implementation Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Backend Implementation](#backend-implementation)
4. [Data Flow](#data-flow)
5. [Filtering Logic](#filtering-logic)
6. [Frontend Implementation](#frontend-implementation)
7. [Data Structures](#data-structures)
8. [Caching Strategy](#caching-strategy)
9. [Error Handling](#error-handling)
10. [Future Improvements](#future-improvements)

---

## Overview

The Prediction Markets card displays retail and institutional trader predictions for economic events (Fed decisions, inflation data, GDP releases) from Polymarket. It aggregates crowd wisdom to provide sentiment indicators that complement technical and fundamental analysis.

**Key Features:**
- Fetches prediction market data from Polymarket API
- Filters for economic/forex-relevant markets
- Displays probability bars showing Yes/No predictions
- Shows market metadata (volume, liquidity, resolution dates)
- Handles historical vs active markets
- Caches data to reduce API calls

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
└────────┬────────┘
         │ Fetches & Filters
         ▼
┌─────────────────┐
│  Polymarket API │
│  CLOB API       │
│  clob.polymarket│
│  .com/markets   │
└─────────────────┘
```

### Component Structure

**Backend:**
- `backend/services/prediction_markets_service.py` - Main service class
- `backend/app.py` - API endpoint handler
- `prediction_markets_cache.json` - Cache file

**Frontend:**
- `src/hooks/usePredictionMarkets.js` - React hook for data fetching
- `src/components/Overview.jsx` - Card component
- `src/components/Overview.css` - Styling
- `src/config.js` - API endpoint configuration

---

## Backend Implementation

### Service Class: `PredictionMarketsService`

**Location:** `backend/services/prediction_markets_service.py`

**Initialization:**
```python
class PredictionMarketsService:
    def __init__(self):
        self.cache_file = "prediction_markets_cache.json"
        self.cache_expiration_minutes = 10
        self.economic_keywords = [...]
        self.exclude_keywords = [...]
```

**Key Methods:**

1. **`_fetch_polymarket_markets()`**
   - Fetches markets from Polymarket CLOB API
   - Paginates through results (up to 5 pages, 1000 markets per page)
   - Returns raw market data as list of dictionaries
   - Handles API errors and timeouts

2. **`_filter_economic_markets(markets)`**
   - Filters markets for economic/forex relevance
   - Deduplicates by market ID
   - Applies keyword matching
   - Filters by date (excludes old resolved markets)
   - Assigns relevance scores
   - Returns top 10 most relevant markets

3. **`_extract_prices_from_tokens(tokens)`**
   - Extracts Yes/No prices from Polymarket tokens array
   - Normalizes prices to sum to 1.0
   - Returns tuple: (yes_price, no_price)

4. **`_normalize_market_data(market)`**
   - Converts Polymarket format to our standard format
   - Extracts key fields
   - Calculates resolved status
   - Returns normalized market dictionary

5. **`get_prediction_markets(force_refresh=False)`**
   - Main public method
   - Checks cache validity
   - Fetches fresh data if needed
   - Filters and normalizes markets
   - Saves to cache
   - Returns formatted result

### API Endpoint

**Location:** `backend/app.py`

**Route:** `/api/prediction-markets`

**Methods:** `GET`, `OPTIONS`

**Query Parameters:**
- `refresh` (optional): Force refresh cache (`?refresh=true`)

**Response Format:**
```json
{
  "status": "success",
  "data": {
    "markets": [
      {
        "id": "0x...",
        "platform": "polymarket",
        "question": "Will the Fed increase interest rates...",
        "yes_price": 0.65,
        "no_price": 0.35,
        "is_historical": true,
        "closed": true,
        "related_event": "FOMC Meeting",
        ...
      }
    ],
    "summary": {
      "total_markets": 10,
      "platforms": ["polymarket"],
      "last_updated": "2026-01-09T...",
      "cached": false
    }
  }
}
```

---

## Data Flow

### Step-by-Step Process

1. **User Opens Overview Page**
   - React component mounts
   - `usePredictionMarkets` hook initializes

2. **Frontend Hook Fetches Data**
   - `usePredictionMarkets.js` calls `/api/prediction-markets`
   - Sets loading state to `true`
   - Makes HTTP GET request

3. **Backend Receives Request**
   - Flask route handler processes request
   - Checks for `refresh` parameter
   - Imports and calls `prediction_markets_service`

4. **Service Checks Cache**
   - Loads cache file if exists
   - Checks if cache is valid (< 10 minutes old)
   - Returns cached data if valid (unless `force_refresh=True`)

5. **Service Fetches from Polymarket** (if cache invalid)
   - Calls `_fetch_polymarket_markets()`
   - Makes paginated requests to CLOB API
   - Collects up to 5000 markets

6. **Service Filters Markets**
   - Deduplicates by market ID
   - Filters for active markets (not archived)
   - Checks for economic keywords
   - Excludes false positives (sports, entertainment)
   - Filters by date (excludes old resolved markets, except highly relevant)
   - Assigns relevance scores
   - Limits to top 10

7. **Service Normalizes Data**
   - Extracts prices from tokens
   - Converts to standard format
   - Adds metadata (is_historical, related_event, etc.)

8. **Service Saves Cache**
   - Writes normalized markets to cache file
   - Updates cache timestamp

9. **Backend Returns JSON**
   - Formats response with status and data
   - Includes summary metadata

10. **Frontend Updates State**
    - Hook receives response
    - Updates markets state
    - Sets loading to `false`
    - Component re-renders with data

11. **Component Renders Markets**
    - Maps through markets array
    - Renders market cards with probability bars
    - Shows notice banner if all markets are historical
    - Displays badges and metadata

---

## Filtering Logic

### Keyword Matching

**Economic Keywords (High Relevance):**
- Federal Reserve terms: `"federal reserve"`, `"fed"`, `"fomc"`, `"interest rate"`, `"rate hike"`, `"rate cut"`
- Inflation terms: `"inflation"`, `"cpi"`, `"consumer price index"`
- GDP terms: `"gdp"`, `"gross domestic product"`
- Employment terms: `"employment"`, `"non-farm payrolls"`, `"nfp"`, `"unemployment"`
- Central banks: `"ecb"`, `"european central bank"`, `"bank of england"`, `"boe"`, `"bank of japan"`, `"boj"`
- General: `"central bank"`, `"monetary policy"`, `"policy decision"`

**Exclude Keywords (False Positives):**
- Entertainment: `"academy"`, `"oscar"`, `"award"`, `"movie"`, `"film"`, `"actor"`, `"actress"`
- Sports: `"sports"`, `"nba"`, `"nfl"`, `"ncaab"`, `"football"`, `"basketball"`

**Special Handling:**
- `"fed"` keyword uses regex word boundary (`\bfed\b`) to avoid matching "federal" in unrelated contexts
- Only matches "fed" as standalone word or in "federal reserve" context

### Market Filtering Criteria

**Inclusion Criteria:**
1. Market must be `active: true`
2. Market must not be `archived: true`
3. Market must match at least one economic keyword
4. Market must not match exclude keywords
5. For historical markets: Must have `relevance: "high"`

**Date Filtering:**
- **Active markets**: `accepting_orders: true` → Always included
- **Future markets**: Resolution date in future → Included
- **Recently resolved**: Closed within last 30 days → Included
- **Historical markets**: Closed > 30 days ago → Only included if `relevance: "high"`

**Deduplication:**
- Uses `condition_id` or `question_id` as unique identifier
- Tracks seen IDs in `seen_ids` set
- Skips markets with duplicate IDs

### Relevance Scoring

**High Relevance:**
- Fed/FOMC/interest rate keywords
- Inflation/CPI keywords
- Employment/NFP keywords
- Central bank keywords (ECB, BOE, BOJ)

**Medium Relevance:**
- GDP keywords
- General economic keywords

**Low Relevance:**
- Other economic-related keywords

### Sorting Priority

Markets are sorted by:
1. `accepting_orders` (active markets first)
2. `is_future` (future markets next)
3. `is_recently_resolved` (recently resolved)
4. `not is_historical` (non-historical preferred)
5. `relevance == "high"` (high relevance)
6. `relevance == "medium"` (medium relevance)
7. `days_until_resolution` (closer dates first)
8. Number of matched keywords

**Result:** Top 10 markets returned

---

## Frontend Implementation

### React Hook: `usePredictionMarkets`

**Location:** `src/hooks/usePredictionMarkets.js`

**State Variables:**
```javascript
const [markets, setMarkets] = useState(fallbackMarkets)
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)
const [lastUpdate, setLastUpdate] = useState(null)
```

**Returned Values:**
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
- Keeps existing data on transient errors

### Component: Prediction Markets Card

**Location:** `src/components/Overview.jsx`

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

**Key Variables Used:**
- `predictionMarkets` - Array of market objects from hook
- `predictionMarketsLoading` - Loading state
- `predictionMarketsError` - Error state
- `refreshPredictionMarkets` - Refresh function

**Market Rendering:**
- Maps through `predictionMarkets` array
- Extracts `yes_price` and `no_price` for each market
- Calculates percentages: `yesPercent = (yesPrice * 100).toFixed(0)`
- Determines if market is resolved: `isResolved = market.is_resolved || market.closed`
- Renders probability bars with dynamic widths
- Shows badges (Resolved, Active, Event type)
- Formats dates with year and resolution status

**Notice Banner Logic:**
```javascript
{predictionMarkets.every(m => m.is_historical || m.closed || m.is_resolved) && (
  <NoticeBanner />
)}
```
- Shows when ALL markets are historical/resolved
- Disappears automatically when active markets appear

---

## Data Structures

### Backend Market Object

**Raw Polymarket Format:**
```python
{
    "condition_id": "0x...",
    "question_id": "0x...",
    "question": "Will the Fed increase interest rates...",
    "description": "The FED interest rates are defined...",
    "active": True,
    "closed": True,
    "archived": False,
    "accepting_orders": False,
    "end_date_iso": "2023-02-01T00:00:00Z",
    "tokens": [
        {"outcome": "Yes", "price": 1.0, "winner": True},
        {"outcome": "No", "price": 0.0, "winner": False}
    ],
    "tags": ["All"],
    ...
}
```

**Normalized Format (Our Standard):**
```python
{
    "id": "0x...",                    # condition_id or question_id
    "platform": "polymarket",          # Always "polymarket"
    "question": "Will the Fed...",     # Market question
    "description": "The FED...",      # Truncated to 300 chars
    "category": "All",                 # From tags array
    "yes_price": 0.65,                 # Probability 0-1
    "no_price": 0.35,                  # Probability 0-1
    "liquidity": None,                 # Not available from CLOB API
    "volume": None,                    # Not available from CLOB API
    "resolution_date": "2023-02-01T00:00:00Z",
    "active": True,
    "closed": True,
    "accepting_orders": False,
    "is_resolved": True,               # Calculated (prices are 0.0 or 1.0)
    "is_future": False,                # Resolution date in future?
    "is_historical": True,             # Old resolved market
    "days_until_resolution": None,     # Days until resolution (if future)
    "relevance": "high",                # "high", "medium", "low"
    "related_event": "FOMC Meeting"     # Event type
}
```

### Frontend Market Object

**Received from API:**
```javascript
{
  id: "0x...",
  platform: "polymarket",
  question: "Will the Fed increase interest rates...",
  description: "The FED interest rates...",
  category: "All",
  yes_price: 0.65,
  no_price: 0.35,
  liquidity: null,
  volume: null,
  resolution_date: "2023-02-01T00:00:00Z",
  active: true,
  closed: true,
  accepting_orders: false,
  is_resolved: true,
  is_future: false,
  is_historical: true,
  days_until_resolution: null,
  relevance: "high",
  related_event: "FOMC Meeting"
}
```

**Computed in Component:**
```javascript
const yesPrice = market.yes_price || 0
const noPrice = market.no_price || 0
const yesPercent = (yesPrice * 100).toFixed(0)  // "65"
const noPercent = (noPrice * 100).toFixed(0)    // "35"
const isResolved = market.is_resolved || market.closed
```

---

## Caching Strategy

### Cache File

**Location:** `prediction_markets_cache.json` (in backend directory)

**Structure:**
```json
{
  "markets": [...],
  "timestamp": "2026-01-09T12:00:00+00:00"
}
```

### Cache Logic

**Cache Validity:**
- Cache expires after 10 minutes (`cache_expiration_minutes = 10`)
- Checked by comparing current time with cache timestamp
- Cache age calculated: `(now - cache_timestamp).total_seconds() < 600`

**Cache Usage:**
1. On request, check if cache exists and is valid
2. If valid and not forcing refresh → return cached data
3. If invalid or forcing refresh → fetch fresh data
4. After fetching → save to cache
5. On API failure → return stale cache if available (graceful degradation)

**Cache Benefits:**
- Reduces API calls to Polymarket
- Faster response times
- Shared cache across all users
- Fallback on API failures

---

## Error Handling

### Backend Error Handling

**Service Level:**
- API failures: Returns cached data if available
- Filtering failures: Logs error, returns empty array
- Price extraction failures: Returns `None` for prices
- Date parsing failures: Skips date filtering, includes market anyway

**API Endpoint Level:**
- Catches all exceptions
- Returns error response with status 500
- Includes error message in response
- Logs full traceback for debugging

**Error Response Format:**
```json
{
  "status": "error",
  "error": "Error message",
  "data": {
    "markets": [],
    "summary": {
      "total_markets": 0,
      "platforms": [],
      "last_updated": null
    }
  }
}
```

### Frontend Error Handling

**Hook Level:**
- Catches fetch errors
- Sets error state
- Keeps existing data on transient errors
- Only clears data if no markets exist

**Component Level:**
- Shows error state UI
- Displays error message
- Provides retry button
- Falls back to empty state if needed

**Error States:**
1. **Loading:** Spinner with "Loading prediction markets..."
2. **Error:** Error icon, message, and retry button
3. **Empty:** Empty icon and message
4. **Success:** Markets list with notice banner if all historical

---

## Frontend Variables

### Hook Variables (`usePredictionMarkets`)

**State:**
- `markets` - Current markets data object
  - `markets.markets` - Array of market objects
  - `markets.summary` - Summary metadata
- `loading` - Boolean, true while fetching
- `error` - String|null, error message if fetch fails
- `lastUpdate` - Date|null, timestamp of last successful fetch

**Computed:**
- `markets.markets || []` - Safe array access
- `markets.summary || {}` - Safe object access

### Component Variables (`Overview.jsx`)

**From Hook:**
```javascript
const {
  markets: predictionMarkets,           // Array of markets
  summary: predictionMarketsSummary,    // Summary object
  loading: predictionMarketsLoading,    // Boolean
  error: predictionMarketsError,        // String|null
  lastUpdate: predictionMarketsLastUpdate, // Date|null
  refresh: refreshPredictionMarkets      // Function
} = usePredictionMarkets()
```

**Computed in Render:**
```javascript
// Per market
const yesPrice = market.yes_price || 0
const noPrice = market.no_price || 0
const yesPercent = (yesPrice * 100).toFixed(0)
const noPercent = (noPrice * 100).toFixed(0)
const isResolved = market.is_resolved || market.closed

// Notice banner condition
const allHistorical = predictionMarkets.every(m => 
  m.is_historical || m.closed || m.is_resolved
)
```

**Date Formatting:**
```javascript
const date = new Date(market.resolution_date)
const now = new Date()
const isPast = date < now

// Format based on date
if (isPast || market.closed) {
  // "Resolved Feb 1, 2023"
} else if (daysUntil <= 7) {
  // "In 3 days"
} else {
  // "Feb 15, 2024"
}
```

---

## Styling Variables

### CSS Classes

**Card Container:**
- `.prediction-markets-card` - Main card wrapper
- `.prediction-markets-header` - Header section
- `.prediction-markets-content` - Content area (scrollable)

**States:**
- `.prediction-markets-loading` - Loading state container
- `.prediction-markets-error` - Error state container
- `.prediction-markets-empty` - Empty state container
- `.prediction-markets-notice` - Historical markets notice banner

**Market Items:**
- `.prediction-market-item` - Individual market card
- `.prediction-market-item.resolved` - Resolved market styling (reduced opacity)

**Market Elements:**
- `.market-header-row` - Question and badges row
- `.market-question` - Market question text
- `.market-badges` - Badge container
- `.market-event-badge` - Event type badge (FOMC Meeting, etc.)
- `.market-status-badge` - Status badge (Resolved, Active)
- `.market-status-badge.resolved` - Resolved badge styling
- `.market-status-badge.active` - Active badge styling

**Probability Display:**
- `.probability-bar-container` - Container for probability bar
- `.probability-bar` - Bar wrapper
- `.probability-fill` - Fill segment
- `.probability-fill.yes-fill` - Yes probability (green)
- `.probability-fill.no-fill` - No probability (red)
- `.probability-label` - Percentage label

**Metadata:**
- `.market-meta-row` - Metadata row
- `.market-meta-item` - Individual metadata item
- `.meta-label` - Label text
- `.meta-value` - Value text

### Color Scheme

**Primary Colors:**
- Blue theme: `rgba(59, 130, 246, ...)` - Primary blue
- Light blue: `#60a5fa`, `#93c5fd` - Accent blues
- Green (Yes): `rgba(34, 197, 94, ...)` - Yes probability
- Red (No): `rgba(239, 68, 68, ...)` - No probability
- Gray (Resolved): `rgba(107, 114, 128, ...)` - Resolved states

**Backgrounds:**
- Card: `linear-gradient(135deg, #0a1a2a 0%, #1a2a3a 25%, #2a3a4a 50%, ...)`
- Market item: `rgba(255, 255, 255, 0.03)`
- Resolved item: `rgba(255, 255, 255, 0.02)` with 75% opacity

---

## API Integration Details

### Polymarket CLOB API

**Endpoint:** `https://clob.polymarket.com/markets`

**Method:** GET

**Parameters:**
- `limit` (default: 1000) - Markets per page
- `cursor` (optional) - Pagination cursor

**Response:**
```json
{
  "data": [...],
  "next_cursor": "...",
  "limit": 1000,
  "count": 1000
}
```

**Rate Limiting:**
- No official rate limits documented
- We fetch 5 pages maximum (5000 markets)
- Cache for 10 minutes to reduce calls
- No authentication required

**Data Fields Used:**
- `condition_id` / `question_id` - Unique identifier
- `question` - Market question
- `description` - Market description
- `active` - Is market active
- `closed` - Is market closed
- `archived` - Is market archived
- `accepting_orders` - Is accepting new orders
- `end_date_iso` - Resolution date
- `tokens` - Array with outcomes and prices
- `tags` - Market categories

---

## Filtering Algorithm Details

### Step-by-Step Filtering Process

1. **Deduplication**
   ```python
   seen_ids = set()
   market_id = market.get("condition_id") or market.get("question_id")
   if market_id in seen_ids:
       continue
   seen_ids.add(market_id)
   ```

2. **Active Check**
   ```python
   if not market.get("active"):
       continue
   ```

3. **Archive Check**
   ```python
   if market.get("archived"):
       continue
   ```

4. **Date Analysis**
   ```python
   end_date = parse_date(market.get("end_date_iso"))
   is_future = end_date > now
   days_until_resolution = (end_date - now).days
   is_recently_resolved = (now - end_date).days <= 30 and market.closed
   is_historical = market.closed and not is_future and not is_recently_resolved
   ```

5. **Historical Filter**
   ```python
   if is_historical and not is_future and not is_recently_resolved:
       # Only include if highly relevant
       if relevance != "high":
           continue
   ```

6. **Exclude Keywords**
   ```python
   if any(exclude in text for exclude in exclude_keywords):
       continue
   ```

7. **Economic Keywords**
   ```python
   for keyword in economic_keywords:
       if keyword in text:
           matched_keywords.append(keyword)
           # Assign relevance based on keyword importance
   ```

8. **Relevance Check**
   ```python
   if not matched_keywords:
       continue  # Skip if no economic keywords matched
   ```

9. **Historical Relevance Check**
   ```python
   if is_historical and relevance != "high":
       continue  # Skip historical markets unless highly relevant
   ```

10. **Sorting & Limiting**
    ```python
    relevant_markets.sort(key=sorting_key, reverse=True)
    return relevant_markets[:10]
    ```

---

## Price Extraction Logic

### Token Structure

Polymarket returns tokens array:
```json
{
  "tokens": [
    {
      "token_id": "...",
      "outcome": "Yes",
      "price": 0.65,
      "winner": false
    },
    {
      "token_id": "...",
      "outcome": "No",
      "price": 0.35,
      "winner": false
    }
  ]
}
```

### Extraction Process

1. **Check for tokens**
   ```python
   if not tokens or len(tokens) < 2:
       return None, None
   ```

2. **Identify Yes/No outcomes**
   ```python
   for token in tokens:
       outcome = token.get("outcome", "").lower()
       price = token.get("price")
       
       if "yes" in outcome or "will" in outcome:
           yes_price = float(price)
       elif "no" in outcome:
           no_price = float(price)
   ```

3. **Fallback to first two tokens**
   ```python
   if yes_price is None and no_price is None:
       yes_price = float(tokens[0].get("price", 0))
       no_price = float(tokens[1].get("price", 0))
   ```

4. **Normalize to sum to 1.0**
   ```python
   total = yes_price + no_price
   if total > 0:
       yes_price = yes_price / total
       no_price = no_price / total
   ```

**Note:** For resolved markets, prices are typically 0.0 or 1.0 (final outcome).

---

## Caching Implementation

### Cache File Structure

**File:** `prediction_markets_cache.json`

**Location:** Backend directory (relative to service file)

**Format:**
```json
{
  "markets": [
    {
      "id": "...",
      "question": "...",
      ...
    }
  ],
  "timestamp": "2026-01-09T12:00:00+00:00"
}
```

### Cache Operations

**Load Cache:**
```python
def _load_cache(self):
    try:
        with open(self.cache_file, 'r') as f:
            data = json.load(f)
            self.cached_markets = data.get('markets', [])
            self.cache_timestamp = datetime.fromisoformat(
                data.get('timestamp').replace('Z', '+00:00')
            )
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        self.cached_markets = None
        self.cache_timestamp = None
```

**Save Cache:**
```python
def _save_cache(self, markets):
    with open(self.cache_file, 'w') as f:
        json.dump({
            'markets': markets,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, f, indent=2)
```

**Check Validity:**
```python
def _is_cache_valid(self):
    if not self.cached_markets or not self.cache_timestamp:
        return False
    
    age = datetime.now(timezone.utc) - self.cache_timestamp.replace(tzinfo=timezone.utc)
    return age.total_seconds() < (self.cache_expiration_minutes * 60)
```

---

## Frontend State Management

### Hook State Flow

```
Initial State
  ↓
loading: true
markets: fallbackMarkets
error: null
  ↓
useEffect triggers fetchMarkets()
  ↓
fetchMarkets() called
  ↓
loading: true (set)
error: null (cleared)
  ↓
HTTP GET /api/prediction-markets
  ↓
Success?
  ├─ Yes → Parse JSON
  │         ↓
  │      setMarkets(data.data)
  │      setLastUpdate(new Date())
  │      setLoading(false)
  │         ↓
  │      Component re-renders with markets
  │
  └─ No → Catch error
            ↓
         setError(err.message)
         setLoading(false)
            ↓
         Component shows error state
```

### Component Rendering Logic

```javascript
if (loading) {
  return <LoadingState />
}

if (error) {
  return <ErrorState />
}

if (markets.length === 0) {
  return <EmptyState />
}

// Check if all markets are historical
const allHistorical = markets.every(m => 
  m.is_historical || m.closed || m.is_resolved
)

return (
  <>
    {allHistorical && <NoticeBanner />}
    <MarketsList markets={markets} />
  </>
)
```

---

## Performance Considerations

### Backend Performance

**API Calls:**
- Fetches 5000 markets maximum (5 pages × 1000)
- Takes ~5-10 seconds to fetch all pages
- Cached for 10 minutes to reduce calls

**Filtering:**
- Processes up to 5000 markets
- Keyword matching is O(n×m) where n=markets, m=keywords
- Deduplication is O(n) with set lookup
- Sorting is O(n log n) for ~20 markets

**Optimization:**
- Early exits in filtering (skip if not active, archived, etc.)
- Limits to 10 markets after filtering
- Caches results to avoid repeated processing

### Frontend Performance

**Rendering:**
- Renders up to 10 market items
- Each item has probability bar with dynamic width
- Date formatting done per market (could be memoized)

**Optimization Opportunities:**
- Memoize date formatting
- Virtual scrolling if markets list grows
- Debounce refresh button clicks

---

## Error Scenarios & Handling

### Scenario 1: Polymarket API Down

**Backend:**
- Catches `requests.exceptions.RequestException`
- Returns cached data if available (even if stale)
- Logs error for monitoring
- Returns error response if no cache

**Frontend:**
- Receives error response
- Shows error state with retry button
- Keeps existing markets if available

### Scenario 2: No Markets Match Filters

**Backend:**
- Returns empty markets array
- Status: "success" (not an error)
- Summary shows `total_markets: 0`

**Frontend:**
- Shows empty state
- Message: "No active prediction markets"
- Subtext explains what will appear

### Scenario 3: All Markets Historical

**Backend:**
- Returns historical markets (if highly relevant)
- Marks with `is_historical: true`

**Frontend:**
- Detects all markets are historical
- Shows notice banner
- Renders markets with "Resolved" badges
- Markets displayed with reduced opacity

### Scenario 4: Cache File Corrupted

**Backend:**
- Catches `json.JSONDecodeError`
- Sets cache to None
- Fetches fresh data
- Creates new cache file

### Scenario 5: Date Parsing Failure

**Backend:**
- Catches date parsing exceptions
- Skips date-based filtering for that market
- Includes market anyway (graceful degradation)
- Logs warning

---

## Configuration

### Backend Configuration

**Service Configuration:**
```python
self.cache_expiration_minutes = 10  # Cache TTL
self.economic_keywords = [...]      # Keywords to match
self.exclude_keywords = [...]       # Keywords to exclude
```

**API Configuration:**
- Endpoint: `/api/prediction-markets`
- Methods: GET, OPTIONS
- CORS: Enabled for all origins
- Rate limiting: Handled by Flask limiter

### Frontend Configuration

**Endpoint Configuration:**
```javascript
// src/config.js
predictionMarkets: `${API_BASE_URL}/api/prediction-markets`
```

**Hook Configuration:**
- Auto-fetch on mount: Yes
- Refresh on error: Manual (retry button)
- Refresh interval: None (manual only)

---

## Future Improvements

### Short-term Enhancements

1. **Active Market Detection**
   - Query Polymarket for markets with `accepting_orders: true`
   - Filter by future resolution dates
   - Prioritize active markets over historical

2. **Real-time Price Updates**
   - Use Polymarket order book API for current prices
   - WebSocket connection for live updates
   - Polling fallback if WebSocket unavailable

3. **Better Date Filtering**
   - Filter for markets resolving in next 30 days
   - Show countdown timers for upcoming resolutions
   - Group by resolution timeframe

4. **Enhanced Filtering**
   - User-selectable filters (currency, event type)
   - Sort options (date, volume, probability)
   - Search functionality

### Long-term Enhancements

1. **Multiple Platform Support**
   - Add Kalshi integration
   - Aggregate data from multiple sources
   - Compare predictions across platforms

2. **Historical Analysis**
   - Track prediction accuracy over time
   - Show historical performance metrics
   - Compare predictions vs actual outcomes

3. **Integration with Other Features**
   - Link to Economic Calendar events
   - Compare with Market Sentiment card
   - Use in AI analysis prompts
   - Alert on significant prediction shifts

4. **Advanced Features**
   - User preferences (which markets to show)
   - Bookmark favorite markets
   - Share market predictions
   - Export market data

---

## Testing Recommendations

### Backend Testing

1. **Unit Tests:**
   - Test keyword matching logic
   - Test date filtering
   - Test price extraction
   - Test deduplication

2. **Integration Tests:**
   - Test API endpoint
   - Test cache behavior
   - Test error handling
   - Test with real Polymarket API

3. **Edge Cases:**
   - Empty API response
   - Malformed market data
   - Missing required fields
   - Very old markets
   - Future markets

### Frontend Testing

1. **Component Tests:**
   - Test loading states
   - Test error states
   - Test empty states
   - Test market rendering

2. **Hook Tests:**
   - Test data fetching
   - Test error handling
   - Test refresh function
   - Test state updates

3. **Integration Tests:**
   - Test full flow (fetch → render)
   - Test notice banner display
   - Test date formatting
   - Test probability bar rendering

---

## Troubleshooting Guide

### Issue: No Markets Displayed

**Possible Causes:**
1. All markets filtered out (too strict filtering)
2. API returning empty data
3. Cache issue
4. Frontend not receiving data

**Solutions:**
1. Check backend logs for filtering results
2. Test API endpoint directly: `curl http://localhost:5001/api/prediction-markets`
3. Clear cache and force refresh
4. Check browser console for errors
5. Verify hook is receiving data

### Issue: Duplicate Markets

**Possible Causes:**
1. Deduplication not working
2. Multiple API calls returning same data
3. Cache containing duplicates

**Solutions:**
1. Verify `seen_ids` set is working
2. Check market IDs are unique
3. Clear cache and refresh
4. Check if API is returning duplicates

### Issue: Wrong Markets Displayed

**Possible Causes:**
1. Keyword matching too broad
2. Exclude keywords not working
3. Relevance scoring incorrect

**Solutions:**
1. Review keyword matching logic
2. Check exclude keywords are applied
3. Verify relevance scoring
4. Adjust keyword lists if needed

### Issue: Prices Always 100%

**Possible Causes:**
1. Markets are resolved (historical)
2. Price extraction not working
3. Tokens array structure changed

**Solutions:**
1. Check if markets are `closed: true`
2. Verify price extraction logic
3. Inspect tokens array structure
4. Test with active markets if available

---

## Summary

The Prediction Markets card provides a comprehensive view of retail and institutional trader predictions for economic events. It fetches data from Polymarket, filters for relevance, and displays it in an intuitive format with probability bars and metadata.

**Key Strengths:**
- Robust filtering and deduplication
- Graceful error handling with cache fallback
- Clear visual distinction between active and historical markets
- Informative notice when only historical data available

**Current Limitations:**
- Only shows historical markets (Polymarket API limitation)
- No real-time price updates
- Limited to Polymarket platform
- Prices show as 0% or 100% for resolved markets

**Future Potential:**
- Real-time active market data
- Multi-platform aggregation
- Historical accuracy tracking
- Integration with other FXSentinel features

The implementation follows existing patterns in the codebase and integrates seamlessly with the Overview page design system.

