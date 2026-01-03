# BRICS News Telegram Channel Integration

## Overview

Added BRICS News Telegram channel (`@bricsnews`) as a news source for the live news feed system. BRICS News focuses on political and geopolitical news from BRICS countries (Brazil, Russia, India, China, South Africa) and related nations like Venezuela, which can have significant macroeconomic implications for forex traders, particularly those trading Dollar and Gold.

## Changes Made

### 1. Telegram Channel Addition

**File**: `backend/services/telegram_sync_wrapper.py`

Added `'bricsnews'` to the list of target channels:
```python
target_channel_names = ['WatcherGuru', 'bricsnews']
```

The system will now fetch messages from both channels:
- **WatcherGuru**: Forex-focused news
- **BRICS News**: Geopolitical and macroeconomic news from BRICS countries

### 2. Enhanced Forex Filter Keywords

**File**: `backend/services/enhanced_forex_filter.py`

Added BRICS-specific keywords to ensure relevant geopolitical news is captured:

**Positive Keywords** (line 47-49):
- `'brics'` - BRICS organization
- `'venezuela'`, `'venezuelan'` - Venezuela-related news
- `'brazil'`, `'russia'`, `'russian'`, `'india'`, `'indian'` - BRICS countries
- `'south africa'`, `'south african'` - South Africa
- `'attack'`, `'conflict'`, `'crisis'`, `'instability'` - Geopolitical events

**High Impact Keywords** (line 127-130):
- Added `'brics'`, `'venezuela'`, `'attack'`, `'conflict'`, `'crisis'`, `'instability'` to high-impact keywords

**Forex Relevant Terms** (line 200-202):
- Added BRICS-related terms to forex-relevant terms list

## How It Works

### News Fetching Process

1. **Channel Access**: The Telegram sync wrapper attempts to access `@bricsnews` channel using the same session-isolated approach as WatcherGuru
2. **Message Retrieval**: Fetches up to 20 recent messages from the channel
3. **Filtering**: Uses the enhanced forex filter to determine if messages are forex-relevant
4. **Parsing**: Converts relevant messages into news items with:
   - Title and summary
   - Impact level (high/medium/low)
   - Currency pairs (if detected)
   - Source: "Telegram - bricsnews"
   - Published timestamp

### Filtering Logic

The enhanced forex filter will include BRICS News messages if they contain:

**Geopolitical Keywords** (already in filter):
- `'geopolitical'`, `'geopolitics'`, `'diplomatic'`, `'sanctions'`

**BRICS-Specific Keywords** (newly added):
- `'brics'`, `'venezuela'`, `'attack'`, `'conflict'`, `'crisis'`, `'instability'`

**Commodity Keywords** (already in filter):
- `'gold'`, `'silver'`, `'oil'`, `'commodity'` - These are particularly relevant for BRICS news

**Economic Impact Keywords**:
- Any mention of Dollar, USD, or economic indicators
- Trade-related terms
- Market sentiment indicators

### Example: Venezuela Attack News

A message like "Venezuela reports attack on oil facilities" would be captured because:
1. Contains `'venezuela'` (newly added keyword)
2. Contains `'attack'` (newly added keyword)
3. Contains `'oil'` (existing commodity keyword)
4. Geopolitical events affecting oil can impact Dollar and Gold markets

### Impact Level Detection

BRICS News messages will be classified as:
- **High Impact**: If they contain critical keywords like `'crisis'`, `'attack'`, `'conflict'`, `'sanctions'`, or mention `'gold'`, `'dollar'`, `'inflation'`
- **Medium Impact**: If they contain geopolitical terms or economic indicators
- **Low Impact**: General BRICS-related news without strong market-moving keywords

## Integration Points

### News Aggregation

BRICS News is integrated into the existing news aggregation flow:

1. **Backend API** (`/api/news` endpoint):
   - Fetches from RSS feeds, alternative sources, and Telegram channels
   - BRICS News is included in the Telegram fetch
   - Messages are merged with other news sources

2. **Persistent Cache**:
   - BRICS News items are cached in Firebase alongside other news
   - Survives app restarts and deployments

3. **Frontend Display**:
   - BRICS News items appear in the Live News Feed card
   - Filtered by impact level (All/High/Medium/Low)
   - Can be analyzed using AI analysis feature

### Alert System

BRICS News items can trigger alerts if they:
- Are classified as high-impact
- Match user alert preferences
- Contain relevant currency pairs

## Testing

To test the BRICS News integration:

1. **Check Telegram Access**:
   ```python
   # The channel should be accessible via Telegram client
   # Channel: @bricsnews (https://t.me/bricsnews)
   ```

2. **Verify News Fetching**:
   - Check backend logs for "Fetched X messages from bricsnews"
   - Verify messages appear in `/api/news` response

3. **Test Filtering**:
   - Messages with BRICS keywords should be included
   - Messages without forex relevance should be filtered out

## Benefits

1. **Broader News Coverage**: Captures geopolitical events that impact forex markets
2. **Dollar & Gold Trading**: BRICS news often affects safe-haven assets (Gold) and Dollar strength
3. **Early Warning**: Political events in BRICS countries can signal market movements
4. **Comprehensive Analysis**: AI analysis can assess macroeconomic implications of BRICS events

## Channel Information

- **Channel Name**: BRICS News
- **Telegram Handle**: @bricsnews
- **URL**: https://t.me/bricsnews
- **Subscribers**: 138,007+ (as of integration)
- **Focus**: Real-time BRICS coverage, geopolitical events, macroeconomic news

## Notes

- The channel is public and accessible via Telegram user account (not bot token)
- Uses the same session-isolated approach as WatcherGuru to prevent session corruption
- Filtering ensures only forex-relevant news is included
- Geopolitical news is weighted as high-impact due to market-moving potential

