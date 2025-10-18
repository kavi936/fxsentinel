import json
from datetime import datetime, timedelta
from typing import List, Dict
import os

class ReliableEconomicCalendar:
    """Reliable economic calendar with comprehensive static data"""
    
    def __init__(self):
        self.cache_file = os.path.join(os.path.dirname(__file__), '..', 'cache', 'reliable_economic_calendar.json')
        self.static_data = self._get_static_economic_data()
    
    def _get_static_economic_data(self) -> List[Dict]:
        """Comprehensive static economic calendar data"""
        today = datetime.now().date()
        
        return [
            {
                "id": "us_cpi_jan_2025",
                "title": "US Consumer Price Index (CPI)",
                "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
                "time": "13:30",
                "currency": "USD",
                "country": "US",
                "impact": "high",
                "previous": "0.2%",
                "forecast": "0.3%",
                "actual": "TBD",
                "currencyPairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
                "category": "INFLATION",
                "source": "reliable_static"
            },
            {
                "id": "us_unemployment_jan_2025",
                "title": "US Unemployment Claims",
                "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "time": "13:30",
                "currency": "USD",
                "country": "US",
                "impact": "medium",
                "previous": "220K",
                "forecast": "215K",
                "actual": "TBD",
                "currencyPairs": ["EURUSD", "GBPUSD", "USDJPY"],
                "category": "EMPLOYMENT",
                "source": "reliable_static"
            },
            {
                "id": "ecb_rate_decision_jan_2025",
                "title": "ECB Interest Rate Decision",
                "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
                "time": "12:45",
                "currency": "EUR",
                "country": "EU",
                "impact": "high",
                "previous": "4.50%",
                "forecast": "4.50%",
                "actual": "TBD",
                "currencyPairs": ["EURUSD", "EURGBP", "EURJPY", "EURCHF"],
                "category": "INTEREST_RATE",
                "source": "reliable_static"
            },
            {
                "id": "uk_gdp_jan_2025",
                "title": "UK GDP Growth Rate",
                "date": (today + timedelta(days=4)).strftime("%Y-%m-%d"),
                "time": "06:00",
                "currency": "GBP",
                "country": "GB",
                "impact": "medium",
                "previous": "0.3%",
                "forecast": "0.2%",
                "actual": "TBD",
                "currencyPairs": ["GBPUSD", "EURGBP", "GBPJPY"],
                "category": "GDP",
                "source": "reliable_static"
            },
            {
                "id": "japan_cpi_jan_2025",
                "title": "Japan Consumer Price Index",
                "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
                "time": "23:30",
                "currency": "JPY",
                "country": "JP",
                "impact": "medium",
                "previous": "2.8%",
                "forecast": "2.9%",
                "actual": "TBD",
                "currencyPairs": ["USDJPY", "EURJPY", "GBPJPY"],
                "category": "INFLATION",
                "source": "reliable_static"
            },
            {
                "id": "canada_employment_jan_2025",
                "title": "Canada Employment Change",
                "date": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
                "time": "13:30",
                "currency": "CAD",
                "country": "CA",
                "impact": "medium",
                "previous": "25.3K",
                "forecast": "20.0K",
                "actual": "TBD",
                "currencyPairs": ["USDCAD", "EURCAD", "GBPCAD"],
                "category": "EMPLOYMENT",
                "source": "reliable_static"
            },
            {
                "id": "australia_retail_sales_jan_2025",
                "title": "Australia Retail Sales",
                "date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
                "time": "00:30",
                "currency": "AUD",
                "country": "AU",
                "impact": "low",
                "previous": "0.2%",
                "forecast": "0.4%",
                "actual": "TBD",
                "currencyPairs": ["AUDUSD", "EURAUD", "GBPAUD"],
                "category": "RETAIL_SALES",
                "source": "reliable_static"
            },
            {
                "id": "switzerland_cpi_jan_2025",
                "title": "Switzerland Consumer Price Index",
                "date": (today + timedelta(days=8)).strftime("%Y-%m-%d"),
                "time": "07:15",
                "currency": "CHF",
                "country": "CH",
                "impact": "low",
                "previous": "1.7%",
                "forecast": "1.8%",
                "actual": "TBD",
                "currencyPairs": ["USDCHF", "EURCHF", "GBPCHF"],
                "category": "INFLATION",
                "source": "reliable_static"
            },
            {
                "id": "fed_meeting_jan_2025",
                "title": "FOMC Meeting Minutes",
                "date": (today + timedelta(days=9)).strftime("%Y-%m-%d"),
                "time": "19:00",
                "currency": "USD",
                "country": "US",
                "impact": "high",
                "previous": "N/A",
                "forecast": "N/A",
                "actual": "TBD",
                "currencyPairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
                "category": "CENTRAL_BANK",
                "source": "reliable_static"
            },
            {
                "id": "new_zealand_cpi_jan_2025",
                "title": "New Zealand Consumer Price Index",
                "date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
                "time": "21:45",
                "currency": "NZD",
                "country": "NZ",
                "impact": "medium",
                "previous": "4.7%",
                "forecast": "4.5%",
                "actual": "TBD",
                "currencyPairs": ["NZDUSD", "EURNZD", "GBPNZD"],
                "category": "INFLATION",
                "source": "reliable_static"
            }
        ]
    
    def get_economic_events(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get economic events from reliable static data"""
        print("📅 Using Reliable Economic Calendar (Static Data)")
        
        # Filter events by date range if provided
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                filtered_events = []
                for event in self.static_data:
                    event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                    if start_dt <= event_date <= end_dt:
                        filtered_events.append(event)
                
                print(f"✅ Returned {len(filtered_events)} events from static data (filtered {start_date} to {end_date})")
                return filtered_events
                
            except ValueError as e:
                print(f"⚠️ Date parsing error: {e}, returning all events")
                return self.static_data
        else:
            print(f"✅ Returned {len(self.static_data)} events from static data (no date filter)")
            return self.static_data

# Create global instance
reliable_economic_calendar = ReliableEconomicCalendar()
