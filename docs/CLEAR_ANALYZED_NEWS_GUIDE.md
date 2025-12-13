# Clear Analyzed News History Guide

This guide explains how to clear the analyzed news history in the FXSentinel system.

## Overview

The FXSentinel system stores three types of data related to news analysis:

1. **Analysis History** (`analysis_history.json`) - Records of all AI analyses performed
2. **News Cache** (`news_cache.json`) - Current cached news items (2-hour duration)
3. **News History** (`news_history.json`) - Historical news items (last 100 items)

## Methods to Clear Data

### Method 1: Python Script (Recommended)

Use the `clear_analyzed_news.py` script for the most comprehensive control.

#### Basic Usage

```bash
# Show current statistics without clearing
python3 clear_analyzed_news.py --stats

# Clear all data (will prompt for confirmation)
python3 clear_analyzed_news.py

# Clear only analysis history
python3 clear_analyzed_news.py --type analysis

# Clear only news cache
python3 clear_analyzed_news.py --type news_cache

# Clear only news history
python3 clear_analyzed_news.py --type news_history

# Clear all data without confirmation prompt
python3 clear_analyzed_news.py --confirm
```

#### Command Line Options

- `--type`: Type of data to clear
  - `analysis`: Only clear analysis history
  - `news_cache`: Only clear current news cache
  - `news_history`: Only clear news history
  - `all`: Clear all data (default)
- `--confirm`: Skip confirmation prompt
- `--stats`: Show current statistics without clearing

#### Example Output

```
🗑️  Clear Analyzed News History
==================================================
🧹 Will clear: ALL DATA (Analysis History + News Cache + News History)

📈 Current Statistics:
------------------------------
📊 Analysis History: 15 analyses
💰 Total Cost: $0.0450
📊 Average Confidence: 78.5%
📰 News Cache: 12 items (age: 0:45:23)
📚 News History: 45 items

⚠️  WARNING: This action cannot be undone!

❓ Are you sure you want to clear the all data? (yes/no): yes

🔄 Clearing all data...

✅ Analysis history cleared successfully
✅ News cache cleared successfully
✅ News history cleared successfully

📋 Operation Summary:
------------------------------
✅ Successfully cleared: analysis_history, news_cache, news_history

🎉 Clear operation completed at 2024-01-15 14:30:25
```

### Method 2: API Endpoint

Use the REST API endpoint for programmatic access.

#### Endpoint

```
POST /api/clear-analysis-history
```

#### Request Body

```json
{
  "type": "all",
  "confirm": true
}
```

#### Response

```json
{
  "success": true,
  "cleared_items": ["analysis_history", "news_cache", "news_history"],
  "errors": [],
  "timestamp": "2024-01-15T14:30:25.123456"
}
```

#### Example Usage

```python
import requests

# Clear all data
response = requests.post('http://localhost:5001/api/clear-analysis-history', 
                        json={"type": "all", "confirm": True})

# Clear only analysis history
response = requests.post('http://localhost:5001/api/clear-analysis-history', 
                        json={"type": "analysis", "confirm": True})

print(response.json())
```

### Method 3: Direct File Deletion

Manually delete the JSON files (not recommended for production).

```bash
# Navigate to backend directory
cd backend

# Remove analysis history
rm analysis_history.json

# Remove news cache
rm news_cache.json

# Remove news history
rm news_history.json
```

## Data Types Explained

### Analysis History (`analysis_history.json`)

Contains records of all AI analyses performed on news items:

```json
[
  {
    "news_id": "123456789",
    "news_title": "US CPI Data Release",
    "news_source": "Reuters",
    "analyzed_at": "2024-01-15T14:30:00",
    "analysis_type": "gpt_enhanced",
    "confidence": 85,
    "immediate_reaction": "bullish_usd",
    "cost": 0.003,
    "analysis_data": {
      "news_impact": "...",
      "trading_implications": "...",
      "key_pairs": ["EUR/USD", "USD/JPY"],
      "volatility": "high",
      "timeframe": "1-4 hours"
    }
  }
]
```

### News Cache (`news_cache.json`)

Contains currently cached news items (2-hour duration):

```json
{
  "timestamp": "2024-01-15T14:30:00",
  "news_count": 12,
  "news": [
    {
      "id": 123456789,
      "title": "US CPI Data Release",
      "summary": "Consumer Price Index...",
      "source": "Reuters",
      "url": "https://...",
      "published_at": "2024-01-15T13:30:00",
      "impact": "High",
      "currency_pairs": ["EUR/USD", "USD/JPY"]
    }
  ]
}
```

### News History (`news_history.json`)

Contains historical news items (last 100 items):

```json
[
  {
    "id": 123456789,
    "title": "US CPI Data Release",
    "summary": "Consumer Price Index...",
    "source": "Reuters",
    "url": "https://...",
    "published_at": "2024-01-15T13:30:00",
    "impact": "High",
    "currency_pairs": ["EUR/USD", "USD/JPY"],
    "cached_at": "2024-01-15T14:30:00",
    "type": "RSS_FEED"
  }
]
```

## Safety Features

### Confirmation Prompts

The Python script includes confirmation prompts to prevent accidental data loss:

```
⚠️  WARNING: This action cannot be undone!

❓ Are you sure you want to clear the all data? (yes/no):
```

### Statistics Display

Before clearing, the script shows current statistics:

```
📊 Analysis History: 15 analyses
💰 Total Cost: $0.0450
📊 Average Confidence: 78.5%
📰 News Cache: 12 items (age: 0:45:23)
📚 News History: 45 items
```

### Error Handling

The script includes comprehensive error handling:

- File permission errors
- Import errors
- Network errors (for API calls)
- Invalid parameters

## Testing

Use the test script to verify functionality:

```bash
python3 test_clear_analyzed_news.py
```

This will:
1. Show current statistics
2. Test clearing analysis history (with confirmation)
3. Test clearing all data (auto-confirm)
4. Optionally test the API endpoint

## Best Practices

### When to Clear Data

- **Development/Testing**: Clear frequently to test with fresh data
- **Production**: Clear sparingly, typically only when:
  - Storage space is limited
  - Data becomes outdated
  - Performance issues arise
  - Privacy concerns require data removal

### Backup Before Clearing

Consider backing up data before clearing:

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup files
cp backend/analysis_history.json backups/$(date +%Y%m%d)/
cp backend/news_cache.json backups/$(date +%Y%m%d)/
cp backend/news_history.json backups/$(date +%Y%m%d)/
```

### Monitoring

Monitor the impact of clearing data:

- Check application performance
- Verify new analyses are being created
- Monitor storage usage
- Review user feedback

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Check file permissions
   ls -la backend/*.json
   
   # Fix permissions if needed
   chmod 644 backend/*.json
   ```

2. **Import Errors**
   ```bash
   # Make sure you're in the project root
   pwd
   ls -la clear_analyzed_news.py
   
   # Check Python path
   python3 -c "import sys; print(sys.path)"
   ```

3. **API Connection Errors**
   ```bash
   # Check if backend is running
   curl http://localhost:5001/api/news-history
   
   # Check backend logs
   tail -f backend/app.log
   ```

### Getting Help

If you encounter issues:

1. Check the error messages in the script output
2. Verify file permissions and paths
3. Ensure the backend server is running (for API calls)
4. Review the logs in the backend directory

## Conclusion

The clear analyzed news functionality provides flexible options for managing data storage in the FXSentinel system. Use the Python script for interactive control, the API endpoint for programmatic access, or direct file deletion for manual operations. Always consider the impact of clearing data and ensure you have proper backups when needed.
