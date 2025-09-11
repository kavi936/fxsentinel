# Economic Calendar Data Extraction Guide

## 🎯 Overview

This guide explains how to extract and cache all available economic calendar data from your Finnhub API before it expires, allowing you to continue development without the $300/month cost.

## 🚀 Quick Start

### 1. Run the Data Extraction

```bash
cd backend
python3 run_data_extraction.py
```

The script will:
- Check your Finnhub API key
- Show current database statistics
- Offer extraction options (Quick/Standard/Comprehensive/Custom)
- Extract and store all available data
- Provide final statistics

### 2. Test the System

```bash
cd backend
python3 test_data_extraction.py
```

This will verify that:
- API connection works
- Data extraction works
- Cached service works
- Fallback functionality works

## 📊 What Gets Extracted

### Data Types
- **Economic Events**: CPI, GDP, employment data, etc.
- **Central Bank Events**: Interest rate decisions, speeches, etc.
- **Market Events**: PMI, retail sales, manufacturing data, etc.

### Data Fields
- Event title and description
- Date and time (UTC)
- Currency and country
- Impact level (high/medium/low)
- Previous, expected, and actual values
- Event type classification

### Date Ranges
- **Quick**: 3 months historical + 3 months future
- **Standard**: 12 months historical + 6 months future  
- **Comprehensive**: 24 months historical + 12 months future
- **Custom**: Your choice of date ranges

## 🗄️ Database Structure

The system creates a SQLite database (`economic_calendar.db`) with:

### Tables
- `economic_events`: Main events table with all economic data
- `extraction_log`: Tracks what data has been extracted

### Indexes
- Date-based queries (fast date range lookups)
- Currency-based queries (filter by currency)
- Impact-based queries (filter by impact level)
- Event type queries (filter by event type)

## 🔄 How It Works

### 1. Data Extraction Process
```
API Request → Data Validation → Database Storage → Deduplication
```

### 2. Fallback System
```
API Available → Use Live Data
API Unavailable → Use Cached Data
No Cache → Return Empty (with warning)
```

### 3. Rate Limiting
- 1 second delay between API requests
- Respects Finnhub API limits
- Prevents rate limit errors

## 🛠️ Technical Details

### Files Created
- `backend/services/economic_data_extractor.py` - Main extraction logic
- `backend/services/cached_economic_calendar.py` - Cached data service
- `backend/run_data_extraction.py` - User-friendly extraction script
- `backend/test_data_extraction.py` - Test suite
- `economic_calendar.db` - SQLite database (created during extraction)

### Integration Points
- Updated `finnhub_calendar.py` to use cached data as fallback
- Existing API endpoints automatically use cached data when API fails
- No changes needed to frontend code

## 📈 Usage Examples

### Extract Data
```python
from services.economic_data_extractor import EconomicDataExtractor

extractor = EconomicDataExtractor()
results = extractor.extract_comprehensive_data(
    historical_months=12, 
    future_months=6
)
```

### Use Cached Data
```python
from services.cached_economic_calendar import CachedEconomicCalendarService

cached_service = CachedEconomicCalendarService()
events = cached_service.get_economic_calendar('2024-01-01', '2024-01-07')
```

### Get Statistics
```python
stats = cached_service.get_cache_statistics()
print(f"Total events: {stats['total_events']}")
print(f"Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
```

## 🔍 Monitoring and Maintenance

### Check Database Status
```python
from services.economic_data_extractor import EconomicDataExtractor

extractor = EconomicDataExtractor()
stats = extractor.get_database_stats()
```

### Search Events
```python
cached_service = CachedEconomicCalendarService()
events = cached_service.search_events("CPI")
high_impact = cached_service.get_high_impact_events(days_ahead=7)
```

### Update Cache
Simply run the extraction script again - it will:
- Skip duplicate events
- Add new events
- Update existing events with new data

## ⚠️ Important Notes

### API Key Expiration
- Extract data **before** your API key expires
- The system will automatically use cached data after expiration
- No code changes needed - it's completely transparent

### Data Quality
- Demo API may have limitations (fewer events, wrong years)
- Paid API provides more comprehensive data
- System filters out obviously fake/placeholder events

### Storage Requirements
- SQLite database grows with more data
- Typical size: 1-10 MB for comprehensive extraction
- Database is stored in the backend directory

## 🚨 Troubleshooting

### Common Issues

#### "API key not configured"
- Check your `.env` file has `FINNHUB_API_KEY=your_key_here`
- Restart your terminal/IDE after adding the key

#### "No events found"
- Demo API may have limited data
- Try different date ranges
- Check if your API key is valid

#### "Cache not available"
- Run the extraction script first
- Check if `economic_calendar.db` exists in backend directory
- Verify database has data (not empty)

#### "Database locked"
- Close any applications using the database
- Wait a few seconds and try again
- Check file permissions

### Getting Help

1. **Check logs**: The scripts provide detailed logging
2. **Run tests**: Use `test_data_extraction.py` to diagnose issues
3. **Verify API key**: Test with a simple API call
4. **Check database**: Verify the SQLite file exists and has data

## 💡 Best Practices

### Before API Expiration
1. **Extract comprehensive data** (24 months historical + 12 months future)
2. **Test the fallback system** to ensure it works
3. **Verify data quality** by checking a few events manually
4. **Document the extraction date** for future reference

### After API Expiration
1. **Monitor cache usage** to see how often fallback is used
2. **Plan for data updates** when you find a cheaper provider
3. **Consider data freshness** - some events may become outdated

### Long-term Strategy
1. **Find cheaper alternatives** to Finnhub ($300/month is expensive)
2. **Consider free sources** like Forex Factory, Investing.com
3. **Build data partnerships** with other financial data providers
4. **Implement incremental updates** when you get a new API

## 🎉 Success Indicators

You'll know the system is working when:
- ✅ Extraction script completes without errors
- ✅ Test suite passes all tests
- ✅ API endpoints return data even without API key
- ✅ Database contains thousands of events
- ✅ Date range covers past and future events
- ✅ Multiple currencies are represented

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Run the test script to identify problems
3. Check the logs for specific error messages
4. Verify your API key is valid and has remaining quota

The system is designed to be robust and self-healing, but proper setup is crucial for success.
