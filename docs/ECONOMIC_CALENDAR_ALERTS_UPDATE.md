# Economic Calendar Alerts - Updated for Hybrid Calendar
**Date**: January 2, 2026  
**Change**: Updated alert system to use hybrid_economic_calendar instead of Finnhub API

---

## Summary

The alert system has been updated to work with the **hybrid economic calendar** (curated ForexFactory data) instead of the Finnhub API, which is no longer being used.

---

## What Changed

### Before ❌
- Alert processor used `finnhub_calendar.get_economic_calendar()`
- Required Finnhub API key
- API was returning 403 Forbidden errors
- No calendar alerts were being sent

### After ✅
- Alert processor uses `hybrid_economic_calendar.get_economic_events()`
- Uses curated ForexFactory data (no API key needed)
- Works with the same data source as the frontend
- Calendar alerts will now work correctly

---

## How It Works Now

### 1. Event Structure

Events from hybrid calendar have this structure:
```python
{
    'id': 'hybrid_123456',
    'title': 'Fed Chair Powell Speaks',
    'date': '2026-01-02',  # or 'Mon, Oct 13'
    'time': '16:20 UTC',
    'currency': 'USD',
    'impact': 'high',  # 'high', 'medium', 'low'
    'status': 'upcoming',  # 'upcoming', 'today', 'completed'
    'previous': 'N/A',
    'expected': 'TBD',
    'actual': 'TBD',
    'currencyPairs': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
    'raw_data': {
        'date': '2026-01-02',
        'time': '16:20 UTC'
    }
}
```

### 2. Alert Timing

Alerts are sent at three intervals before high-impact events:
- **2 hours before** (115-120 minutes)
- **1 hour before** (55-60 minutes)
- **10 minutes before** (8-10 minutes)

### 3. Event Filtering

Only events that meet these criteria trigger alerts:
- `impact == 'high'`
- `status in ['upcoming', 'today']`
- Event is in the future (not in the past)
- Within one of the alert timing windows

### 4. Date/Time Parsing

The system handles two date formats:
- **YYYY-MM-DD**: `"2026-01-02"` (from hybrid calendar formatted output)
- **Day, Month DD**: `"Mon, Oct 13"` (from curated events)

Time format is always: `"HH:MM UTC"` (e.g., `"16:20 UTC"`)

---

## Code Changes

### File: `backend/services/unified_alert_processor.py`

#### Changed: `_check_economic_calendar_alerts()`
- **Before**: Used `finnhub_calendar.get_economic_calendar()`
- **After**: Uses `hybrid_economic_calendar.get_economic_events(start_date, end_date)`
- **Updated**: Date/time parsing to handle hybrid calendar formats

#### Changed: `_send_economic_alert_to_user()`
- **Before**: Parsed date/time assuming Finnhub format
- **After**: Parses date/time handling both YYYY-MM-DD and "Mon, Oct 13" formats

---

## How Calendar Events Are Stored

### Source: `backend/services/hybrid_economic_calendar.py`

Events are stored as a curated list in the `_get_curated_events()` method:

```python
{
    'title': 'Fed Chair Powell Speaks',
    'date': 'Tue, Oct 14',  # Day, Month DD format
    'time': '16:20 UTC',     # HH:MM UTC format
    'currency': 'USD',
    'impact': 'high',
    'actual': 'TBD',
    'forecast': 'N/A',
    'previous': 'N/A'
}
```

### Event Formatting

The `_format_event()` method converts curated events to the standard format:
- Parses date from "Mon, Oct 13" to "YYYY-MM-DD"
- Adds status (upcoming/today/completed)
- Generates currency pairs
- Adds raw_data for alert processing

---

## Alert Flow

1. **Periodic Check** (every 5 minutes)
   - Unified processor calls `_check_economic_calendar_alerts()`
   - Gets events from hybrid calendar for next 7 days

2. **Event Filtering**
   - Filters for `impact == 'high'` and `status in ['upcoming', 'today']`
   - Parses date/time for each event

3. **Timing Check**
   - Calculates minutes until event
   - Checks if within alert windows (2h, 1h, 10min)

4. **Alert Sending**
   - For each matching event, calls `_send_economic_alert()`
   - Gets all users with alerts enabled
   - Processes users in parallel
   - Sends alerts via Telegram

5. **Deduplication**
   - Uses persistent deduplication to prevent duplicate alerts
   - Checks per-user and per-event timing

---

## Testing

To verify calendar alerts are working:

1. **Check unified processor is running**:
   ```python
   from services.unified_alert_processor import get_unified_processor
   processor = get_unified_processor()
   print(processor.get_status())
   ```

2. **Check events are available**:
   ```python
   from services.hybrid_economic_calendar import hybrid_economic_calendar
   events = hybrid_economic_calendar.get_economic_events()
   print(f"Found {len(events)} events")
   ```

3. **Check for upcoming high-impact events**:
   ```python
   high_impact = [e for e in events if e.get('impact') == 'high' and e.get('status') in ['upcoming', 'today']]
   print(f"Found {len(high_impact)} high-impact upcoming events")
   ```

4. **Monitor logs**:
   - Look for "Checking for economic calendar alerts..."
   - Look for "Sending economic alert for: ..."
   - Look for "Triggered X economic calendar alerts"

---

## Expected Behavior

### When Alerts Should Be Sent

- **High-impact events** (Fed speeches, NFP, CPI, etc.)
- **Within timing windows** (2h, 1h, 10min before)
- **Status is upcoming or today**
- **Event is in the future**

### When Alerts Should NOT Be Sent

- Low or medium impact events
- Events in the past
- Events more than 2 hours away
- Events already sent (deduplication)

---

## Summary

✅ **Updated**: Alert processor now uses hybrid_economic_calendar  
✅ **Fixed**: Date/time parsing for hybrid calendar formats  
✅ **Working**: Calendar alerts will now function correctly  
✅ **No API Key**: No longer requires Finnhub API key  

The alert system is now fully integrated with the hybrid economic calendar and will send alerts for upcoming high-impact events at the correct timing intervals.

