"""
Google Sheets Service for fetching economic indicator data
"""
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        """
        Initialize Google Sheets service using environment variables
        Expects:
        - GOOGLE_SHEETS_CREDENTIALS_JSON: JSON string of service account credentials
        - GOOGLE_SHEETS_SPREADSHEET_ID: ID of the Google Spreadsheet
        - GOOGLE_SHEETS_CACHE_TTL: Cache TTL in seconds (default: 300 = 5 minutes)
        """
        # Get credentials from environment variable (JSON string)
        creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self.cache_ttl = int(os.getenv('GOOGLE_SHEETS_CACHE_TTL', '30'))  # 30 seconds default (was 5 minutes)
        self.cache = {}
        self.cache_timestamps = {}
        self.client = None
        
        if not creds_json:
            logger.warning("GOOGLE_SHEETS_CREDENTIALS_JSON not set - Google Sheets service disabled")
            return
        
        if not self.spreadsheet_id:
            logger.warning("GOOGLE_SHEETS_SPREADSHEET_ID not set - Google Sheets service disabled")
            return
        
        try:
            # Parse JSON string from environment variable
            creds_dict = json.loads(creds_json)
            scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            self.client = gspread.authorize(creds)
            logger.info("✅ Google Sheets service initialized successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GOOGLE_SHEETS_CREDENTIALS_JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
    
    def is_available(self) -> bool:
        """Check if service is available (credentials and client initialized)"""
        return self.client is not None and self.spreadsheet_id is not None
    
    def get_economy_indicators(self, country_code: str) -> Optional[Dict]:
        """
        Fetch economic indicators for a specific country from Google Sheets
        
        Args:
            country_code: Country code (US, EUR, GBP, JPY)
        
        Returns:
            Dictionary with indicators data in the same format as economyIndicators.json
            Returns None if service unavailable or error occurs
        """
        if not self.is_available():
            return None
        
        cache_key = f"indicators_{country_code}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Returning cached data for {country_code}")
            return self.cache[cache_key]
        
        try:
            # Open spreadsheet
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            # Map country codes to tab name prefixes
            country_prefixes = {
                'US': 'US',
                'EUR': 'EUR',
                'GBP': 'UK',  # UK in sheets, GBP in code
                'JPY': 'JP'   # JP in sheets, JPY in code
            }
            
            prefix = country_prefixes.get(country_code)
            if not prefix:
                logger.warning(f"Unknown country code: {country_code}")
                return None
            
            # Get all worksheets and filter by prefix
            all_worksheets = spreadsheet.worksheets()
            country_sheets = [ws for ws in all_worksheets if ws.title.startswith(prefix)]
            
            # Exclude "Copy of" tabs
            country_sheets = [ws for ws in country_sheets if not ws.title.startswith('Copy of')]
            
            if not country_sheets:
                logger.warning(f"No sheets found for country code: {country_code} (prefix: {prefix})")
                return None
            
            # Collect all indicators from all sheets for this country
            all_indicators = {}
            
            for worksheet in country_sheets:
                logger.debug(f"Processing sheet: {worksheet.title}")
                try:
                    # Get all records (assumes first row is headers)
                    records = worksheet.get_all_records()
                    
                    if not records:
                        logger.debug(f"No records found in sheet '{worksheet.title}'")
                        continue
                    
                    # Transform data for this sheet
                    sheet_indicators = self._transform_sheet_data(records, country_code)
                    
                    # Merge into all_indicators (sheet_indicators is a dict with indicator_id as key)
                    for indicator_id, indicator_data in sheet_indicators.items():
                        all_indicators[indicator_id] = indicator_data
                        
                except Exception as e:
                    logger.warning(f"Error processing sheet '{worksheet.title}': {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if not all_indicators:
                logger.warning(f"No indicators extracted for {country_code}")
                return None
            
            # Cache result
            self.cache[cache_key] = all_indicators
            self.cache_timestamps[cache_key] = datetime.now()
            
            logger.info(f"✅ Successfully fetched {len(all_indicators)} indicators for {country_code}")
            return all_indicators
            
        except Exception as e:
            logger.error(f"Error fetching from Google Sheets for {country_code}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _transform_sheet_data(self, records: List[Dict], country_code: str) -> Dict:
        """
        Transform Google Sheets rows to the format expected by the frontend
        
        This mimics what the CSV parser does - first row has metadata, subsequent rows are historical data
        """
        if not records:
            return {}
        
        # Get metadata from first record (row 2 in sheet, after header)
        first_record = records[0]
        indicator_name_val = first_record.get('indicator_name', '')
        indicator_name = str(indicator_name_val).strip() if indicator_name_val else ''
        
        if not indicator_name:
            logger.warning("No indicator_name found in first record")
            return {}
        
        # Map indicator names to IDs (same logic as CSV parser)
        indicator_id = self._get_indicator_id(indicator_name)
        
        # Get metadata
        current_value = first_record.get('current value', '')
        as_of = first_record.get('date_of_release', '')
        unit = first_record.get('unit', '%')
        
        # Collect all historical data points
        history = []
        seen_dates = set()
        
        # Process first record (current value)
        first_date_val = first_record.get('date_of_release', '')
        first_value_val = first_record.get('release_value', '')
        
        if first_date_val and first_value_val:
            date_str = str(first_date_val).strip('"').strip()
            value_str = str(first_value_val).strip()
            
            if date_str and value_str:
                try:
                    iso_date = self._parse_date(date_str)
                    if iso_date and iso_date not in seen_dates:
                        value_clean = value_str.replace('€', '').replace('¥', '').replace('$', '').replace('£', '').replace('T', '').replace('B', '').replace('K', '').strip()
                        value = float(value_clean)
                        history.append({'date': iso_date, 'value': value})
                        seen_dates.add(iso_date)
                except (ValueError, AttributeError) as e:
                    logger.debug(f"Skipping invalid first data point: {date_str}={value_str}, error: {e}")
        
        # Process subsequent records (historical data)
        for record in records[1:]:
            date_val = record.get('date_of_release', '')
            value_val = record.get('release_value', '')
            
            # Handle both string and numeric types
            date_str = str(date_val).strip('"').strip() if date_val else ''
            value_str = str(value_val).strip() if value_val else ''
            
            if date_str and value_str:
                try:
                    # Parse date (handles "December 10, 2025", "Q3, 2025", etc.)
                    iso_date = self._parse_date(date_str)
                    if not iso_date or iso_date in seen_dates:
                        continue
                    
                    # Clean value string (remove currency symbols, units)
                    value_clean = value_str.replace('€', '').replace('¥', '').replace('$', '').replace('£', '').replace('T', '').replace('B', '').replace('K', '').strip()
                    value = float(value_clean)
                    
                    history.append({
                        'date': iso_date,
                        'value': value
                    })
                    seen_dates.add(iso_date)
                except (ValueError, AttributeError) as e:
                    logger.debug(f"Skipping invalid data point: {date_str}={value_str}, error: {e}")
                    pass
        
        # Convert to final format
        if not history:
            return {}
        
        # Sort by date
        history.sort(key=lambda x: x['date'])
        
        # Get latest value
        latest = history[-1]
        current_value_num = latest['value']
        
        # Format current value based on unit
        unit_upper = str(unit).upper()
        if 'K' in unit_upper:
            current_value_str = f"{current_value_num:.0f}K"
        elif 'T' in unit_upper or 'B' in unit_upper:
            # Determine currency symbol
            symbol = '€' if country_code == 'EUR' else '¥' if country_code == 'JPY' else '£' if country_code == 'GBP' else ''
            prefix = '+' if current_value_num >= 0 else ''
            suffix = 'T' if 'T' in unit_upper else 'B'
            current_value_str = f"{prefix}{symbol}{current_value_num:.2f}{suffix}"
        else:
            current_value_str = f"{current_value_num}%"
        
        result = {
            indicator_id: {
                'currentValue': current_value_str,
                'asOf': latest['date'],
                'chartData': [item['value'] for item in history],
                'chartDates': [item['date'] for item in history],
                'source': self._get_source(country_code),
                'sourceUrl': self._get_source_url(country_code, indicator_id),
                'notes': f"{indicator_name} - {unit}",
                'unit': unit,
                'frequency': 'Monthly',
                'nextRelease': 'TBD',
                'description': self._get_description(indicator_id, country_code)
            }
        }
        
        return result
    
    def _get_indicator_id(self, indicator_name: str) -> str:
        """Map indicator name to ID (same logic as CSV parser)"""
        name_lower = indicator_name.lower()
        if 'core inflation' in name_lower:
            return 'core-inflation-YoY'
        elif 'inflation' in name_lower:
            return 'inflation-YoY' if 'YoY' in name_lower or 'yoy' in name_lower else 'inflation'
        elif 'unemployment' in name_lower:
            return 'unemployment'
        elif 'non farm' in name_lower or 'nonfarm' in name_lower or 'payroll' in name_lower:
            return 'nonfarm-payrolls'
        elif 'gdp' in name_lower:
            return 'gdp-growth'
        elif 'interest' in name_lower or ('rate' in name_lower and 'gdp' not in name_lower and 'unemployment' not in name_lower and 'inflation' not in name_lower):
            return 'interest-rate'
        elif 'wage' in name_lower:
            return 'wage-growth'
        elif 'current account' in name_lower:
            return 'current-account'
        elif 'trade balance' in name_lower:
            return 'trade-balance'
        else:
            return 'interest-rate'  # Default
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats to ISO format"""
        if not date_str:
            return None
            
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
        
        # Try alternative month-year: "October 2025"
        try:
            dt = datetime.strptime(date_str, '%B %Y')
            return dt.strftime('%Y-%m-01')
        except ValueError:
            pass
        
        # Try quarter: "Q3, 2025"
        try:
            match = re.match(r'Q(\d),?\s*(\d{4})', date_str)
            if match:
                quarter = int(match.group(1))
                year = int(match.group(2))
                quarter_months = {1: 2, 2: 5, 3: 8, 4: 11}  # Feb, May, Aug, Nov
                month = quarter_months[quarter]
                return f'{year}-{month:02d}-15'
        except (ValueError, AttributeError):
            pass
        
        return None
    
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
        urls = {
            'US': {
                'interest-rate': 'https://www.federalreserve.gov/releases/h15/',
                'inflation-YoY': 'https://www.bls.gov/cpi/',
                'core-inflation-YoY': 'https://www.bls.gov/cpi/',
                'gdp-growth': 'https://www.bea.gov/data/gdp/gross-domestic-product',
                'unemployment': 'https://www.bls.gov/news.release/empsit.htm',
                'nonfarm-payrolls': 'https://www.bls.gov/news.release/empsit.htm'
            },
            'EUR': {
                'interest-rate': 'https://www.ecb.europa.eu/stats/policy_and_exchange_rates/key_ecb_interest_rates/html/index.en.html',
                'inflation': 'https://ec.europa.eu/eurostat/web/hicp',
                'core-inflation-YoY': 'https://ec.europa.eu/eurostat/web/hicp',
                'gdp-growth': 'https://ec.europa.eu/eurostat/web/national-accounts/data/main-tables',
                'unemployment': 'https://ec.europa.eu/eurostat/web/lfs/data/main-tables',
                'current-account': 'https://www.ecb.europa.eu/stats/balance_of_payments_and_external/html/index.en.html'
            },
            'GBP': {
                'interest-rate': 'https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate',
                'inflation': 'https://www.ons.gov.uk/economy/inflationandpriceindices',
                'core-inflation-YoY': 'https://www.ons.gov.uk/economy/inflationandpriceindices',
                'gdp-growth': 'https://www.ons.gov.uk/economy/grossdomesticproductgdp',
                'unemployment': 'https://www.ons.gov.uk/employmentandlabourmarket/peoplenotinwork/unemployment',
                'wage-growth': 'https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours'
            },
            'JPY': {
                'interest-rate': 'https://www.boj.or.jp/en/mopo/',
                'inflation': 'https://www.stat.go.jp/english/data/cpi/',
                'core-inflation-YoY': 'https://www.stat.go.jp/english/data/cpi/',
                'gdp-growth': 'https://www.esri.cao.go.jp/en/sna/',
                'unemployment': 'https://www.stat.go.jp/english/data/roudou/',
                'current-account': 'https://www.mof.go.jp/'
            }
        }
        return urls.get(country_code, {}).get(indicator_id, 'https://example.com')
    
    def _get_description(self, indicator_id: str, country_code: str) -> str:
        """Get description for indicator"""
        descriptions = {
            'interest-rate': {
                'US': 'Federal Funds Rate - The primary monetary policy tool set by the Federal Open Market Committee (FOMC).',
                'EUR': 'Main Refinancing Rate - The primary monetary policy tool set by the European Central Bank (ECB).',
                'GBP': 'Bank Rate - The primary monetary policy tool set by the Bank of England (BoE).',
                'JPY': 'Policy Interest Rate - The primary monetary policy tool set by the Bank of Japan (BoJ).'
            },
            'inflation': {
                'US': 'Consumer Price Index Year-over-Year - Measures the annual percentage change in prices for a basket of consumer goods and services.',
                'EUR': 'Harmonized Index of Consumer Prices (HICP) - The official measure of inflation for the eurozone.',
                'GBP': 'Consumer Price Index (CPI) Year-over-Year - The official measure of inflation for the United Kingdom.',
                'JPY': 'Consumer Price Index (CPI) Year-over-Year - Measures the annual change in consumer prices in Japan.'
            },
            'core-inflation-YoY': {
                'US': 'Core Inflation Year-over-Year - Measures the annual change in consumer prices excluding volatile food and energy components.',
                'EUR': 'Core HICP Year-over-Year - Measures the annual change in consumer prices excluding volatile food, energy, alcohol, and tobacco.',
                'GBP': 'Core CPI Year-over-Year - Measures the annual change in consumer prices excluding volatile food, energy, alcohol, and tobacco.',
                'JPY': 'Core Inflation Year-over-Year - Measures the annual change in consumer prices excluding volatile food and energy components.'
            }
        }
        return descriptions.get(indicator_id, {}).get(country_code, f'{indicator_id} description')
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        timestamp = self.cache_timestamps.get(cache_key)
        if not timestamp:
            return False
        return (datetime.now() - timestamp).total_seconds() < self.cache_ttl

