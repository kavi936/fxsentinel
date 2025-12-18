# Google Sheets Integration - Step-by-Step Setup Guide

## Overview

This guide explains how to connect FXSentinel to Google Sheets so you can update economic indicator data directly in a spreadsheet without code changes.

## Architecture

```
Google Sheets (Your Data)
    ↓
Backend Service (Python)
    ↓
API Endpoint (/api/economy-indicators)
    ↓
Frontend (React)
```

## Step 1: Google Cloud Setup (One-Time, ~15 minutes)

### 1.1 Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Click "Select a project" → "New Project"
3. Name: `FXSentinel` (or any name)
4. Click "Create"

### 1.2 Enable Google Sheets API
1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it → Click "Enable"

### 1.3 Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Service account name: `fxsentinel-sheets-reader`
4. Click "Create and Continue"
5. Skip role assignment → Click "Done"
6. Click on the created service account
7. Go to "Keys" tab → "Add Key" → "Create new key"
8. Choose "JSON" → Click "Create"
9. **Save the downloaded JSON file securely** (you'll need it)

### 1.4 Get Service Account Email
- In the service account details, copy the email (looks like: `fxsentinel-sheets-reader@your-project.iam.gserviceaccount.com`)
- You'll need this to share your Google Sheet

## Step 2: Create Google Sheet Structure

### 2.1 Create Your Spreadsheet
1. Go to https://sheets.google.com
2. Create a new spreadsheet
3. Name it: "FXSentinel Economic Indicators"

### 2.2 Sheet Structure
Create separate sheets (tabs) for each economy:
- **US_Indicators** (for United States)
- **EUR_Indicators** (for European Union)
- **GBP_Indicators** (for United Kingdom)
- **JPY_Indicators** (for Japan)

### 2.3 Column Structure (Same as CSV)
Each sheet should have these columns:
```
| indicator_country | indicator_name | unit | current value | date_of_release | release_value |
|-------------------|----------------|------|---------------|-----------------|---------------|
| US                | Interest Rate  | %    | 3.75          | December 10...  | 3.75          |
|                   |                |      |               | November 30...  | 3.75          |
|                   |                |      |               | ...             | ...           |
```

### 2.4 Share Sheet with Service Account
1. In your Google Sheet, click "Share" (top right)
2. Paste the service account email (from Step 1.4)
3. Set permission to "Viewer" (read-only is enough)
4. Click "Send"

## Step 3: Backend Implementation

### 3.1 Install Dependencies
```bash
cd backend
pip install gspread google-auth
```

### 3.2 Store Credentials
**Option A: Environment Variable (Recommended for Production)**
```bash
# In Railway/Vercel, add as secret:
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account",...}'
GOOGLE_SHEETS_SPREADSHEET_ID='your-spreadsheet-id-from-url'
```

**Option B: File Path (For Local Development)**
```bash
# .env file
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
```

**How to get Spreadsheet ID:**
- From Google Sheets URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit`
- Copy the part between `/d/` and `/edit`

### 3.3 Create Service File
Create `backend/services/google_sheets_service.py`:

```python
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from typing import Dict, Optional
from datetime import datetime, timedelta

class GoogleSheetsService:
    def __init__(self):
        # Get credentials from environment
        creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
        creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self.cache_ttl = int(os.getenv('GOOGLE_SHEETS_CACHE_TTL', '300'))  # 5 minutes
        self.cache = {}
        self.cache_timestamps = {}
        self.client = None
        
        # Authenticate
        if creds_json:
            # From environment variable (JSON string)
            creds_dict = json.loads(creds_json)
            scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            self.client = gspread.authorize(creds)
        elif creds_path:
            # From file path
            scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            creds = Credentials.from_service_account_file(creds_path, scopes=scope)
            self.client = gspread.authorize(creds)
        else:
            raise ValueError("Either GOOGLE_SHEETS_CREDENTIALS_JSON or GOOGLE_SHEETS_CREDENTIALS_PATH must be set")
    
    def get_economy_indicators(self, country_code: str) -> Optional[Dict]:
        """
        Fetch economic indicators for a specific country from Google Sheets
        
        Args:
            country_code: Country code (US, EUR, GBP, JPY)
        
        Returns:
            Dictionary with indicators data in the same format as economyIndicators.json
        """
        cache_key = f"indicators_{country_code}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            # Open spreadsheet
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            # Get the sheet for this country (e.g., "US_Indicators")
            sheet_name = f"{country_code}_Indicators"
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                print(f"Sheet '{sheet_name}' not found")
                return None
            
            # Get all records (assumes first row is headers)
            records = worksheet.get_all_records()
            
            if not records:
                return None
            
            # Transform data to expected format
            indicators = self._transform_sheet_data(records, country_code)
            
            # Cache result
            self.cache[cache_key] = indicators
            self.cache_timestamps[cache_key] = datetime.now()
            
            return indicators
            
        except Exception as e:
            print(f"Error fetching from Google Sheets: {e}")
            return None
    
    def _transform_sheet_data(self, records: list, country_code: str) -> Dict:
        """
        Transform Google Sheets rows to the format expected by the frontend
        
        This mimics what the CSV parser does
        """
        from datetime import datetime
        
        # Group records by indicator_name
        indicators_dict = {}
        
        for record in records:
            indicator_name = record.get('indicator_name', '').strip()
            if not indicator_name:
                continue
            
            # Map indicator names to IDs (same logic as CSV parser)
            indicator_id = self._get_indicator_id(indicator_name)
            
            if indicator_id not in indicators_dict:
                indicators_dict[indicator_id] = {
                    'history': [],
                    'current_value': record.get('current value', ''),
                    'as_of': record.get('date_of_release', ''),
                    'unit': record.get('unit', '%'),
                    'indicator_name': indicator_name
                }
            
            # Add historical data point
            date_str = record.get('date_of_release', '').strip('"').strip()
            value_str = record.get('release_value', '').strip()
            
            if date_str and value_str:
                try:
                    # Parse date (handles "December 10, 2025", "Q3, 2025", etc.)
                    iso_date = self._parse_date(date_str)
                    value = float(value_str.replace('€', '').replace('¥', '').replace('$', '').replace('T', '').replace('B', '').replace('K', '').strip())
                    
                    indicators_dict[indicator_id]['history'].append({
                        'date': iso_date,
                        'value': value
                    })
                except (ValueError, AttributeError):
                    pass
        
        # Convert to final format
        result = {}
        for indicator_id, data in indicators_dict.items():
            # Sort by date
            data['history'].sort(key=lambda x: x['date'])
            
            # Format current value
            latest = data['history'][-1] if data['history'] else None
            current_value = latest['value'] if latest else float(data['current_value']) if data['current_value'] else 0
            
            # Format based on unit
            unit = data['unit'].upper()
            if 'K' in unit:
                current_value_str = f"{current_value:.0f}K"
            elif 'T' in unit or 'B' in unit:
                # Determine currency symbol
                symbol = '€' if country_code == 'EUR' else '¥' if country_code == 'JPY' else '£' if country_code == 'GBP' else ''
                prefix = '+' if current_value >= 0 else ''
                suffix = 'T' if 'T' in unit else 'B'
                current_value_str = f"{prefix}{symbol}{current_value:.2f}{suffix}"
            else:
                current_value_str = f"{current_value}%"
            
            result[indicator_id] = {
                'currentValue': current_value_str,
                'asOf': latest['date'] if latest else data['as_of'],
                'chartData': [item['value'] for item in data['history']],
                'chartDates': [item['date'] for item in data['history']],
                'source': self._get_source(country_code),
                'sourceUrl': self._get_source_url(country_code, indicator_id),
                'notes': f"{data['indicator_name']} - {data['unit']}",
                'unit': data['unit'],
                'frequency': 'Monthly',
                'nextRelease': 'TBD',
                'description': self._get_description(indicator_id, country_code)
            }
        
        return result
    
    def _get_indicator_id(self, indicator_name: str) -> str:
        """Map indicator name to ID (same logic as CSV parser)"""
        name_lower = indicator_name.lower()
        if 'core inflation' in name_lower:
            return 'core-inflation-YoY'
        elif 'inflation' in name_lower:
            return 'inflation-YoY' if 'YoY' in name_lower else 'inflation'
        elif 'unemployment' in name_lower:
            return 'unemployment'
        elif 'non farm' in name_lower or 'nonfarm' in name_lower or 'payroll' in name_lower:
            return 'nonfarm-payrolls'
        elif 'gdp' in name_lower:
            return 'gdp-growth'
        elif 'interest' in name_lower or ('rate' in name_lower and 'gdp' not in name_lower and 'unemployment' not in name_lower):
            return 'interest-rate'
        elif 'wage' in name_lower:
            return 'wage-growth'
        elif 'current account' in name_lower or 'trade balance' in name_lower:
            return 'current-account' if 'current account' in name_lower else 'trade-balance'
        else:
            return 'interest-rate'  # Default
    
    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats to ISO format"""
        from datetime import datetime
        import re
        
        date_str = date_str.strip('"').strip()
        
        # Try full date: "December 10, 2025"
        try:
            dt = datetime.strptime(date_str, '%B %d, %Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        # Try month-year: "October, 2025"
        try:
            dt = datetime.strptime(date_str, '%B, %Y')
            return dt.strftime('%Y-%m-01')
        except ValueError:
            pass
        
        # Try quarter: "Q3, 2025"
        try:
            match = re.match(r'Q(\d), (\d{4})', date_str)
            if match:
                quarter = int(match.group(1))
                year = int(match.group(2))
                quarter_months = {1: 2, 2: 5, 3: 8, 4: 11}
                month = quarter_months[quarter]
                return f'{year}-{month:02d}-15'
        except (ValueError, AttributeError):
            pass
        
        return date_str  # Return as-is if can't parse
    
    def _get_source(self, country_code: str) -> str:
        """Get data source name for country"""
        sources = {
            'US': 'Federal Reserve',
            'EUR': 'European Central Bank',
            'GBP': 'Bank of England',
            'JPY': 'Bank of Japan'
        }
        return sources.get(country_code, 'Official Source')
    
    def _get_source_url(self, country_code: str, indicator_id: str) -> str:
        """Get source URL for indicator"""
        # Return appropriate URLs based on country and indicator
        return 'https://example.com'  # Update with actual URLs
    
    def _get_description(self, indicator_id: str, country_code: str) -> str:
        """Get description for indicator"""
        # Return appropriate descriptions
        return f"{indicator_id} description"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        timestamp = self.cache_timestamps.get(cache_key)
        if not timestamp:
            return False
        return (datetime.now() - timestamp).total_seconds() < self.cache_ttl

```

### 3.4 Add API Endpoint
In `backend/app.py`, add:

```python
from services.google_sheets_service import GoogleSheetsService

# Initialize service
google_sheets_service = GoogleSheetsService()

@app.route('/api/economy-indicators/<country_code>', methods=['GET'])
def get_economy_indicators(country_code):
    """Get economic indicators for a country from Google Sheets"""
    try:
        indicators = google_sheets_service.get_economy_indicators(country_code.upper())
        
        if indicators:
            return jsonify({
                "status": "success",
                "country": country_code.upper(),
                "indicators": indicators,
                "source": "google_sheets",
                "cached": google_sheets_service._is_cache_valid(f"indicators_{country_code.upper()}")
            }), 200
        else:
            # Fallback to static JSON
            return jsonify({
                "status": "error",
                "message": "No data found, using fallback"
            }), 404
    except Exception as e:
        print(f"Error in API endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
```

## Step 4: Frontend Integration

### 4.1 Update Economies.jsx
Modify the data fetching to use API first, fallback to JSON:

```javascript
// At the top of Economies.jsx
import economyIndicatorsData from '../data/economyIndicators.json'; // Fallback

// Add state for API data
const [apiIndicatorsData, setApiIndicatorsData] = useState({});
const [useApiData, setUseApiData] = useState(true);

// Add useEffect to fetch from API
useEffect(() => {
  const fetchIndicators = async () => {
    try {
      const response = await fetch(`/api/economy-indicators/${selectedEconomy}`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setApiIndicatorsData({
            [selectedEconomy]: { indicators: data.indicators }
          });
          setUseApiData(true);
          return;
        }
      }
    } catch (error) {
      console.error('Error fetching from API, using fallback:', error);
    }
    // Fallback to static JSON
    setUseApiData(false);
  };
  
  fetchIndicators();
}, [selectedEconomy]);

// Update economyData useMemo to use API data if available
const economyData = useMemo(() => {
  // ... existing baseData ...
  
  // Use API data if available, otherwise use static JSON
  const indicatorsSource = useApiData ? apiIndicatorsData : economyIndicatorsData;
  
  // Merge logic (same as before, but use indicatorsSource)
  Object.keys(indicatorsSource).forEach((countryCode) => {
    // ... existing merge logic ...
  });
  
  return mergedData;
}, [useApiData, apiIndicatorsData]);
```

## Step 5: Testing

### 5.1 Test Locally
1. Set environment variables
2. Run backend: `python backend/app.py`
3. Test endpoint: `curl http://localhost:5000/api/economy-indicators/US`
4. Check frontend loads data correctly

### 5.2 Deploy to Production
1. Add environment variables to Railway/Vercel
2. Deploy backend
3. Test API endpoint
4. Verify frontend works

## Step 6: Daily Workflow

### How to Update Data:
1. Open Google Sheet
2. Find the economy sheet (e.g., "US_Indicators")
3. Add new row with latest data
4. Save (auto-saves)
5. **That's it!** Data appears in app within 5 minutes (cache TTL)

### Example Update:
```
| indicator_country | indicator_name | unit | current value | date_of_release | release_value |
|-------------------|----------------|------|---------------|-----------------|---------------|
| US                | Interest Rate  | %    | 3.75          | December 10...  | 3.75          |
|                   |                |      |               | December 20...  | 3.50          | ← Add new row
```

## Troubleshooting

### Issue: "Permission denied"
- **Solution**: Make sure you shared the sheet with the service account email

### Issue: "Sheet not found"
- **Solution**: Check sheet name matches exactly (e.g., "US_Indicators" not "US Indicators")

### Issue: "Rate limit exceeded"
- **Solution**: Increase cache TTL (e.g., 15 minutes instead of 5)

### Issue: Data not updating
- **Solution**: Clear cache or wait for TTL to expire

## Benefits Summary

✅ **Real-time updates** - Changes appear within minutes  
✅ **Easy editing** - No code knowledge needed  
✅ **Version history** - Google Sheets tracks all changes  
✅ **Collaboration** - Multiple people can edit  
✅ **No deployment** - Data updates don't require code changes  
✅ **Reliable** - Google's infrastructure handles uptime  

## Next Steps

1. Set up Google Cloud project (15 min)
2. Create Google Sheet with proper structure (30 min)
3. Implement backend service (2-3 hours)
4. Test locally (30 min)
5. Deploy to production (30 min)

**Total time: ~4-5 hours for full implementation**

