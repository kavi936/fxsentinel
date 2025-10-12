# Weekly Economic Calendar Update Guide

## Overview
Your economic calendar now uses **curated ForexFactory data** that you update manually once per week. This takes **5 minutes** and ensures accurate, real-time events.

## When to Update
- **Every Monday morning** (covers the week ahead)
- **Or when major events are announced** (Fed meetings, ECB decisions, etc.)

## Step-by-Step Instructions

### 1. Go to ForexFactory Calendar
Visit: https://www.forexfactory.com/calendar

### 2. Filter for High-Impact Events
- Set filter to show **HIGH impact events only** (red dots)
- Select **This Week** + **Next Week** (14 days total)
- Focus on major currencies: **USD, EUR, GBP, JPY, CAD, AUD, NZD, CHF**

### 3. Copy Event Data
For each HIGH-impact event, note:
- **Title** (e.g., "US Non-Farm Payrolls")
- **Date** (e.g., "Friday, November 1, 2025")
- **Time** (in EST, we'll convert to UTC)
- **Currency** (USD, EUR, GBP, etc.)
- **Previous**, **Forecast**, **Actual** values

### 4. Update the Calendar File
Open: `/Users/kavi/Desktop/fxsentinel/backend/services/hybrid_economic_calendar.py`

Find the `_get_curated_events` method (around line 77)

Replace the events list with your new data:

```python
events = [
    {
        'title': 'US Non-Farm Payrolls',
        'date': 'Fri, Nov 1',
        'time': '12:30 UTC',  # 08:30 EST + 5 hours = 13:30 UTC
        'currency': 'USD',
        'impact': 'high',
        'alpha_vantage_function': 'NONFARM_PAYROLL',
        'category': 'EMPLOYMENT',
        'description': 'Number of new jobs created',
        'actual': 'TBD',
        'forecast': '150K',
        'previous': '254K'
    },
    # Add more events...
]
```

### 5. Time Conversion: EST to UTC
ForexFactory shows times in **EST** (Eastern Standard Time)
- **EST to UTC**: Add 5 hours
- **EDT to UTC** (Daylight Saving): Add 4 hours

Examples:
- 08:30 EST = 13:30 UTC
- 10:00 EST = 15:00 UTC
- 14:00 EST = 19:00 UTC

### 6. Test Your Changes
Run this command:
```bash
cd /Users/kavi/Desktop/fxsentinel
python3 -c "from backend.services.hybrid_economic_calendar import hybrid_economic_calendar; events = hybrid_economic_calendar.get_economic_events(); print(f'✅ Found {len(events)} events')"
```

Should show: `✅ Found XX events`

### 7. Restart Your Backend
```bash
# If running locally
# Ctrl+C to stop, then restart

# If on Railway (automatic)
git add backend/services/hybrid_economic_calendar.py
git commit -m "Update economic calendar for [date range]"
git push origin main
```

## Event Categories Reference

### High-Impact US Events
- **Non-Farm Payrolls (NFP)** - First Friday of month
- **CPI (Consumer Price Index)** - Monthly, ~13th
- **FOMC Interest Rate Decision** - Every 6 weeks
- **Retail Sales** - Monthly, ~15th
- **GDP Growth Rate** - Quarterly
- **Fed Chair Powell Speaks** - Various
- **FOMC Meeting Minutes** - 3 weeks after meeting

### High-Impact EUR Events
- **ECB Interest Rate Decision** - Every 6 weeks
- **ECB President Lagarde Speaks** - Various
- **German Industrial Production** - Monthly
- **Eurogroup Meetings** - Monthly

### High-Impact GBP Events
- **BOE Interest Rate Decision** - Monthly
- **BOE Governor Bailey Speaks** - Various
- **UK Construction PMI** - Monthly
- **UK Employment Change** - Monthly

### High-Impact Others
- **RBA Cash Rate** (AUD) - Monthly
- **BOC Interest Rate** (CAD) - Every 6 weeks
- **RBNZ Official Cash Rate** (NZD) - Every 6 weeks

## Tips for Fast Updates

1. **Focus on HIGH impact only** - Skip medium/low events
2. **Copy 15-20 events** - Covers 2 weeks adequately
3. **Use previous week's format** - Just change dates/values
4. **Don't overthink forecasts** - If not available, use "TBD" or "N/A"
5. **Speeches can use N/A** for all values - That's normal

## Example Update Session (5 minutes)

```
1. Open ForexFactory → Filter HIGH impact → This week + Next week
2. Copy 15-20 events to notepad
3. Open hybrid_economic_calendar.py
4. Update events list (copy-paste format from previous entries)
5. Convert EST times to UTC (+5 hours)
6. Save file
7. Test: python3 -c "..."
8. Done! ✅
```

## What if I Miss a Week?

No problem! The calendar will continue showing old events. Just update when you can. Events in the past will automatically be filtered out by the frontend.

## Need Help?

Check the existing events in `hybrid_economic_calendar.py` - they show the exact format needed. Just copy-paste and change the values.

---

**Last Updated**: October 11, 2025
**Current Data Coverage**: October 10-17, 2025 (18 events)

