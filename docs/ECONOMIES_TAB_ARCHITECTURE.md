# Economies Tab - Complete Architecture & Functionality Guide

## Overview

The Economies tab is a comprehensive economic indicators dashboard that displays real-time economic data for four major economies (US, EUR, GBP, JPY) with interactive charts, detailed professional briefs, and seamless data integration from Google Sheets.

---

## Architecture Overview

### Component Structure

```
Economies (Main Component)
├── Central Bank Rates Section
├── Economy Selector & Holistic Scan Button
└── EconomyDetails (Sub-component)
    ├── Indicator Cards Grid (3x2 layout)
    ├── Modal Overlay System
    └── Holistic Scan Section (placeholder)
```

---

## Data Flow & Sources

### 1. **Data Sources (Priority Order)**

The system uses a **three-tier data source strategy**:

1. **Google Sheets API** (Primary - when available)
   - Fetched via backend API endpoint: `/api/economy-indicators/<country_code>`
   - Real-time data from your Google Spreadsheet
   - Cached for 5 minutes to reduce API calls

2. **Local JSON File** (Fallback)
   - `src/data/economyIndicators.json`
   - Static backup data
   - Used when API is unavailable or fails

3. **Placeholder Data** (Base Structure)
   - Hardcoded in `Economies.jsx` component
   - Provides structure and professional descriptions
   - Always merged with real data

### 2. **Data Merging Logic**

The `mergeIndicatorData()` function combines:

**From Placeholder:**
- Professional descriptions
- Card structure
- Default chart labels
- Indicator metadata

**From Real Data (Google Sheets/JSON):**
- Current values
- Historical chart data (all data points)
- Chart dates
- Source information
- Unit, frequency, next release dates

**Merge Priority:**
- Descriptions: Real data if >50 chars, otherwise placeholder
- Current values: Real data always takes priority
- Chart data: Real data replaces placeholder
- Metadata: Real data preferred, placeholder as fallback

---

## Component Breakdown

### Main Component: `Economies`

**Responsibilities:**
- Manages economy selection state
- Handles API data fetching
- Tracks which countries have been loaded
- Renders central bank rates section
- Provides economy selector UI

**Key State:**
```javascript
- selectedEconomy: 'US' | 'EUR' | 'GBP' | 'JPY'
- apiIndicatorsData: {} // Fetched from Google Sheets
- useApiData: {} // Tracks which countries use API vs JSON
- fetchedCountriesRef: Set // Prevents duplicate API calls
```

**API Fetching Logic:**
1. When `selectedEconomy` changes, triggers `useEffect`
2. Checks if country already fetched (prevents duplicates)
3. Attempts to fetch from Google Sheets API (5-second timeout)
4. On success: Stores in `apiIndicatorsData` state
5. On failure: Falls back to local JSON file
6. Marks country as fetched to prevent re-requests

### Sub-Component: `EconomyDetails`

**Responsibilities:**
- Renders indicator cards in 3x2 grid
- Manages card expansion (modal system)
- Handles chart rendering and interactions
- Displays professional content sections

**Key State:**
```javascript
- expandedIndicatorId: null | indicatorId
- loadingIndicatorId: null | indicatorId
- chartHover: { index, x, y, value, date } | null
```

**Data Processing:**
1. Receives `apiIndicatorsData` and `useApiData` as props
2. Uses `useMemo` to merge placeholder + real data
3. Creates `economyData` object with all indicators
4. Safely accesses data with fallbacks

---

## Indicator Cards System

### Card Structure

Each indicator card displays:
- **Header**: Title + Current Value
- **Description**: Professional brief (always visible)
- **Mini Chart**: Last 8 data points (collapsed view)
- **Chart Label**: Date range (e.g., "Jan 2024 - Dec 2025")

### Card Layout (3x2 Grid)

**Row 1:**
- Federal Funds Rate / Interest Rate
- Inflation YoY
- Core Inflation YoY

**Row 2:**
- GDP Growth
- Unemployment Rate
- Non-Farm Payrolls / Current Account / Wage Growth

### Card Interaction

**Click Behavior:**
1. User clicks card → `toggleIndicatorCard(indicatorId)`
2. Sets `loadingIndicatorId` → Shows spinner
3. Sets `expandedIndicatorId` → Opens modal
4. After 600ms → Clears loading spinner

**Keyboard Support:**
- `Enter` or `Space` → Expands card
- `Escape` → Closes modal (via close button)

---

## Modal Overlay System

### Why Modal Instead of Inline Expansion?

**Problem with Inline:**
- Cards expanding inline caused grid reflow
- Other cards shifted position (confusing UX)
- Layout became messy

**Solution:**
- Modal overlay keeps grid stable
- Focused view of expanded content
- Better for detailed information display

### Modal Structure

```
Modal Overlay (dark backdrop, blur effect)
└── Modal Content (scrollable container)
    ├── Close Button (red X, top-right)
    ├── Header (Title + Current Value)
    ├── Description
    ├── Full Chart (all data points, 400px height)
    └── Expanded Content Sections
        ├── Key Insights
        ├── Indicator Overview
        ├── How It's Measured
        ├── Currency & Market Impact
        ├── Current Policy Context (if available)
        └── What This Means for Traders (if available)
```

### Modal Chart Features

**Enhanced Display:**
- All historical data points (not just 8)
- Increased height (400px vs 160px)
- More detailed X-axis labels (month names)
- Thinner line strokes for professional look
- Crosshair on hover (vertical + horizontal lines)
- Tooltip with value, date, trend, percentage change

---

## Chart Rendering System

### Data Normalization

**Purpose:** Convert real-world values to SVG coordinates (0-100 range)

**Process:**
1. Extract all original values from `chartDataOriginal`
2. Find min/max values
3. Calculate range
4. Normalize to 10-90 range (for better visibility)
5. Formula: `((value - min) / range) * 80 + 10`

**Why 10-90?**
- Leaves padding at top/bottom
- Prevents clipping of data points
- Better visual appearance

### Chart Types

**Default State (Collapsed):**
- Shows last 8 data points
- Compact date range label
- 160px height
- Simplified X-axis (years only)

**Expanded State (Modal):**
- Shows ALL data points
- Detailed date labels (month names)
- 400px height
- Full X-axis with month labels
- Crosshair interaction

### Chart Features

**Line Rendering:**
- **Monotone Cubic Interpolation**: Smooth, professional curves
- **Multi-layer Rendering**: Base glow layer + crisp main line
- **Gradient Fill**: Area under curve with opacity

**Grid Lines:**
- Dynamic horizontal lines aligned with Y-axis intervals
- Transparent, thin, professional appearance
- 5 evenly spaced intervals

**Y-Axis Labels:**
- Calculated from actual data range
- Always 5 intervals with clean rounding
- Formatted as percentages (e.g., "3.5%")
- Positioned correctly using normalization math

**X-Axis Labels:**
- Default: Years only (e.g., "2024", "2025")
- Expanded: Month names (e.g., "Jan 2024", "Feb", "Mar")
- Positioned at first occurrence of each year/month

**Reference Lines:**
- **2% Target Line**: For inflation indicators (Fed/BoJ/ECB/BoE target)
- **0% Zero Line**: For charts with negative values
- Both use same normalization math for accurate positioning

**Hover Interaction:**
- Tooltip shows: Value, Date, Index, Trend (↑/↓), % Change
- Crosshair: Vertical + horizontal lines
- Dynamic positioning to avoid edge clipping
- Calculates trend from previous data point

---

## Professional Content System

### Content Sources

**1. Indicator Details Dictionary** (`indicatorDetails`)
- Pre-written professional briefs
- Sections: Overview, Measurement, Impact, Context, Trader Implications
- Stored in component for US indicators

**2. Placeholder Descriptions**
- Short descriptions in card default state
- Full descriptions in expanded modal
- Updated to match JSON file descriptions

**3. Dynamic Content Rendering**
- `renderHighlightedText()`: Parses `[[text]]` markers for red underline
- `renderParagraphs()`: Splits text by `\n\n` for paragraph breaks
- `getIndicatorInsights()`: Returns key insights array
- `getIndicatorDetails()`: Returns structured content sections

### Content Highlighting

**Syntax:** `[[text to highlight]]`
**Rendering:** Red underline style
**Purpose:** Emphasize important information

**Example:**
```
The [[Federal Funds Rate]] is the primary tool...
```
Renders as: "The <span style="color: red; text-decoration: underline">Federal Funds Rate</span> is..."

---

## Caching System

### Backend Caching

**Google Sheets Service Cache:**
- TTL: 5 minutes (300 seconds) - configurable via `GOOGLE_SHEETS_CACHE_TTL`
- In-memory cache: `self.cache` dictionary
- Timestamps: `self.cache_timestamps` dictionary
- Cache key format: `indicators_{country_code}`

**Cache Validation:**
- Checks if cache exists
- Checks if timestamp is within TTL
- Returns cached data if valid
- Fetches fresh data if expired

**Cache Bypass:**
- Add `?refresh=true` to API URL
- Clears cache for that country
- Forces fresh fetch from Google Sheets

### Frontend Caching

**Fetched Countries Tracking:**
- `fetchedCountriesRef`: Set of country codes
- Prevents duplicate API calls
- Persists for component lifetime
- Cleared on page refresh

**Force Refresh:**
- Add `?refresh=true` to page URL
- Bypasses `fetchedCountriesRef` check
- Forces re-fetch from API

---

## Data Transformation Pipeline

### Google Sheets → Frontend

**1. Backend Service (`google_sheets_service.py`):**
```
Google Sheets Row
  ↓
get_all_records() → List of Dicts
  ↓
_transform_sheet_data() → Indicator Dict
  ↓
get_economy_indicators() → All Indicators Dict
  ↓
Cache (if valid) or Return
```

**2. API Endpoint (`/api/economy-indicators/<country>`):**
```
Google Sheets Service
  ↓
JSON Response:
{
  "status": "success",
  "country": "US",
  "indicators": { ... },
  "source": "google_sheets",
  "cached": true/false,
  "timestamp": "2025-12-19T..."
}
```

**3. Frontend (`Economies.jsx`):**
```
API Response
  ↓
setApiIndicatorsData()
  ↓
useMemo: mergeIndicatorData()
  ↓
economyData[selectedEconomy]
  ↓
Rendered Cards
```

### Data Format Transformation

**Google Sheets Format:**
```
indicator_country | indicator_name | unit | current value | date_of_release | release_value
```

**Transformed Format:**
```json
{
  "interest-rate": {
    "currentValue": "3.75%",
    "chartData": [5.5, 5.5, 3.75],
    "chartDates": ["2024-01-31", "2025-12-10"],
    "description": "...",
    "source": "...",
    "unit": "%",
    "frequency": "8 meetings per year"
  }
}
```

---

## Error Handling & Fallbacks

### API Failure Scenarios

**1. Network Error:**
- 5-second timeout via `AbortController`
- Falls back to local JSON
- Logs warning to console

**2. API Error Response:**
- Non-200 status code
- Falls back to local JSON
- Logs status code

**3. Missing Data:**
- No indicators found in Google Sheets
- Falls back to local JSON
- Uses placeholder descriptions

**4. Config Unavailable:**
- Missing `config.endpoints.economyIndicators`
- Falls back to local JSON immediately
- No API attempt made

### Data Access Safety

**Safe Data Access:**
```javascript
// Multiple fallback levels
data = economyData[selectedEconomy] 
    || economyData.US 
    || economyData['US'];

// Error boundaries
try {
  // Data access
} catch (err) {
  // Display error UI
}
```

---

## User Interactions

### Economy Selection

**Process:**
1. User selects economy from dropdown
2. `setSelectedEconomy(newValue)` triggers
3. `useEffect` detects change
4. Checks if already fetched
5. Fetches from API (or uses cache)
6. Merges with placeholder data
7. Re-renders cards with new data

### Card Expansion

**Process:**
1. User clicks card
2. `toggleIndicatorCard(indicatorId)` called
3. Loading spinner appears
4. Modal opens with backdrop
5. Expanded chart renders (all data points)
6. Content sections display
7. User can scroll within modal
8. Click outside or X button closes

### Chart Hover

**Process:**
1. Mouse moves over chart
2. `handleChartHover()` calculates position
3. Finds nearest data point
4. Calculates trend (vs previous point)
5. Calculates percentage change
6. Positions tooltip (avoids edges)
7. Renders crosshair lines
8. Mouse leave → clears hover state

### Holistic Scan Button

**Process:**
1. User clicks "Holistic Scan" button
2. `handleScrollToAnalysis()` called
3. Scrolls to `analysisRef` element
4. Shows placeholder "Coming soon" section

---

## Performance Optimizations

### 1. **Memoization**
- `economyData` computed with `useMemo`
- Only recalculates when `apiIndicatorsData` or `useApiData` changes
- Prevents unnecessary re-renders

### 2. **Caching**
- Backend: 5-minute cache reduces Google Sheets API calls
- Frontend: Prevents duplicate API requests per country

### 3. **Lazy Loading**
- Data fetched only when economy selected
- Not all countries loaded at once

### 4. **Chart Data Optimization**
- Default: Only 8 points rendered
- Expanded: All points rendered (only when modal open)

### 5. **Debouncing**
- Chart hover calculations optimized
- Tooltip positioning cached

---

## Styling & Responsive Design

### CSS Architecture

**File:** `src/components/Economies.css` (1384 lines)

**Key Features:**
- Responsive breakpoints for mobile/tablet/desktop
- Custom scrollbars for modal content
- Smooth animations and transitions
- Professional gradient overlays
- Grid layout with CSS Grid

### Responsive Breakpoints

- **Desktop**: Full 3x2 grid, 400px modal charts
- **Tablet**: Adjusted spacing, 300px modal charts
- **Mobile**: Stacked layout, optimized touch targets

---

## Future Enhancements (Placeholder)

### Holistic Scan Section

**Current State:**
- Placeholder section at bottom
- "Coming soon" text
- Scroll-to functionality

**Planned:**
- GPT-powered analysis
- Cross-indicator insights
- Market context integration
- Trading implications

---

## Summary

The Economies tab is a sophisticated, data-driven component that:

1. **Fetches** real-time data from Google Sheets via backend API
2. **Merges** real data with professional placeholder content
3. **Displays** indicators in an interactive 3x2 grid
4. **Renders** professional charts with smooth curves and interactions
5. **Provides** detailed modal views with comprehensive content
6. **Handles** errors gracefully with multiple fallback layers
7. **Optimizes** performance through caching and memoization
8. **Supports** responsive design across all devices

The architecture is designed for scalability, maintainability, and excellent user experience, with clear separation of concerns between data fetching, processing, and presentation.

