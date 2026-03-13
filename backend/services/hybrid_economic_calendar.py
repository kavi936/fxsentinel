"""
Hybrid Economic Calendar
Combines curated event schedule with AlphaVantage historical data
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class HybridEconomicCalendar:
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY_1', 'J9NZPOVTZCE1U80M')
        self.cache_file = os.path.join(os.path.dirname(__file__), '..', 'cache', 'hybrid_calendar_cache.json')
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour for AlphaVantage data
        self._load_cache()
        print("🚀 Hybrid Economic Calendar initialized")
    
    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
    
    def get_economic_events(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get economic events from curated calendar with AlphaVantage historical data
        
        Returns:
            List of economic calendar events with real dates and historical values
        """
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"📅 Fetching hybrid calendar for {start_date} to {end_date}")
        
        # Get curated events
        all_events = self._get_curated_events()
        
        # Enrich with AlphaVantage data
        enriched_events = []
        for event in all_events:
            # Check if event is in date range
            try:
                event_date_obj = datetime.strptime(event['date'], '%a, %b %d')
                event_date_obj = event_date_obj.replace(year=datetime.now().year)
                event_date_str = event_date_obj.strftime('%Y-%m-%d')
                
                if start_date <= event_date_str <= end_date:
                    # Enrich with AlphaVantage data
                    enriched_event = self._enrich_with_alpha_vantage(event)
                    enriched_events.append(enriched_event)
            except Exception as e:
                print(f"⚠️ Error processing event {event.get('title')}: {e}")
                continue
        
        print(f"✅ Returning {len(enriched_events)} enriched events")
        return enriched_events
    
    def _get_curated_events(self) -> List[Dict]:
        """
        Curated economic calendar with REAL upcoming events from ForexFactory
        Last Updated: December 28, 2025
        Source: ForexFactory Calendar JSON Export
        Coverage: October 5 - January 9, 2026
        """
        events = [
            # SUNDAY, OCTOBER 5
            {
                'title': 'MI Inflation Gauge m/m',
                'date': 'Sun, Oct 5',
                'time': '00:00 UTC',  # 20:00 EST + 4 hours
                'currency': 'AUD',
                'impact': 'medium',
                'actual': '0.4%',
                'forecast': 'N/A',
                'previous': '-0.3%'
            },
            {
                'title': 'ANZ Commodity Prices m/m',
                'date': 'Sun, Oct 5',
                'time': '00:00 UTC',
                'currency': 'NZD',
                'impact': 'medium',
                'actual': '-1.1%',
                'forecast': 'N/A',
                'previous': '0.7%'
            },
            
            # MONDAY, OCTOBER 6
            {
                'title': 'Unemployment Rate',
                'date': 'Mon, Oct 6',
                'time': '07:00 UTC',  # 03:00 EST + 4
                'currency': 'CHF',
                'impact': 'medium',
                'actual': '3.0%',
                'forecast': '2.9%',
                'previous': '2.9%'
            },
            {
                'title': 'Sentix Investor Confidence',
                'date': 'Mon, Oct 6',
                'time': '08:30 UTC',  # 04:30 EST + 4
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '-5.4',
                'forecast': '-7.5',
                'previous': '-9.2'
            },
            {
                'title': 'Construction PMI',
                'date': 'Mon, Oct 6',
                'time': '08:30 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': '46.2',
                'forecast': '46.1',
                'previous': '45.5'
            },
            {
                'title': 'Housing Equity Withdrawal q/q',
                'date': 'Mon, Oct 6',
                'time': '08:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-16.1B',
                'forecast': '-4.5B',
                'previous': '-4.9B'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Mon, Oct 6',
                'time': '09:00 UTC',  # 05:00 EST + 4
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '0.1%',
                'forecast': '0.1%',
                'previous': '-0.4%'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Mon, Oct 6',
                'time': '15:00 UTC',  # 11:00 EST + 4
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Mon, Oct 6',
                'time': '17:00 UTC',  # 13:00 EST + 4
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'NZIER Business Confidence',
                'date': 'Mon, Oct 6',
                'time': '21:00 UTC',  # 17:00 EST + 4
                'currency': 'NZD',
                'impact': 'medium',
                'actual': '18',
                'forecast': 'N/A',
                'previous': '22'
            },
            {
                'title': 'FOMC Member Schmid Speaks',
                'date': 'Mon, Oct 6',
                'time': '21:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Westpac Consumer Sentiment',
                'date': 'Mon, Oct 6',
                'time': '22:57 UTC',  # 18:57 EST + 4
                'currency': 'AUD',
                'impact': 'medium',
                'actual': '-3.5%',
                'forecast': 'N/A',
                'previous': '-3.1%'
            },
            {
                'title': 'Household Spending y/y',
                'date': 'Mon, Oct 6',
                'time': '23:30 UTC',  # 19:30 EST + 4
                'currency': 'JPY',
                'impact': 'medium',
                'actual': '2.3%',
                'forecast': '1.4%',
                'previous': '1.4%'
            },
            {
                'title': 'ANZ Job Advertisements m/m',
                'date': 'Tue, Oct 7',
                'time': '00:30 UTC',  # 20:30 EST + 4 (next day UTC)
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-3.3%',
                'forecast': 'N/A',
                'previous': '-0.3%'
            },
            {
                'title': '30-y Bond Auction',
                'date': 'Tue, Oct 7',
                'time': '03:35 UTC',  # 23:35 EST + 4 (next day UTC)
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.25|3.4',
                'forecast': 'N/A',
                'previous': '3.26|3.3'
            },
            
            # TUESDAY, OCTOBER 7
            {
                'title': 'Official Cash Rate',
                'date': 'Wed, Oct 8',
                'time': '01:00 UTC',  # 21:00 EST + 4 (next day UTC)
                'currency': 'NZD',
                'impact': 'high',
                'actual': '2.50%',
                'forecast': '2.75%',
                'previous': '3.00%'
            },
            {
                'title': 'RBNZ Rate Statement',
                'date': 'Wed, Oct 8',
                'time': '01:00 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            
            # THURSDAY, OCTOBER 9
            {
                'title': 'RBA Gov Bullock Speaks',
                'date': 'Thu, Oct 9',
                'time': '22:00 UTC',  # 18:00 EST + 4
                'currency': 'AUD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Bank Lending y/y',
                'date': 'Thu, Oct 9',
                'time': '23:50 UTC',  # 19:50 EST + 4
                'currency': 'JPY',
                'impact': 'medium',
                'actual': '3.8%',
                'forecast': '3.7%',
                'previous': '3.5%'
            },
            {
                'title': 'PPI y/y',
                'date': 'Thu, Oct 9',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'medium',
                'actual': '2.7%',
                'forecast': '2.5%',
                'previous': '2.7%'
            },
            
            # FRIDAY, OCTOBER 10
            {
                'title': 'Employment Change',
                'date': 'Fri, Oct 10',
                'time': '12:30 UTC',  # 08:30 EST + 4
                'currency': 'CAD',
                'impact': 'high',
                'actual': '60.4K',
                'forecast': '2.8K',
                'previous': '-65.5K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Oct 10',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '7.1%',
                'forecast': '7.2%',
                'previous': '7.1%'
            },
            {
                'title': 'FOMC Member Goolsbee Speaks',
                'date': 'Fri, Oct 10',
                'time': '13:45 UTC',  # 09:45 EST + 4
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Prelim UoM Consumer Sentiment',
                'date': 'Fri, Oct 10',
                'time': '14:00 UTC',  # 10:00 EST + 4
                'currency': 'USD',
                'impact': 'high',
                'actual': '55.0',
                'forecast': '54.1',
                'previous': '55.1'
            },
            {
                'title': 'Prelim UoM Inflation Expectations',
                'date': 'Fri, Oct 10',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '4.6%',
                'forecast': 'N/A',
                'previous': '4.7%'
            },
            
            # MONDAY, OCTOBER 13 (From ForexFactory JSON Export)
            {
                'title': 'Monetary Policy Meeting Minutes',
                'date': 'Mon, Oct 13',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            
            # TUESDAY, OCTOBER 14 (From ForexFactory JSON Export)
            {
                'title': 'Average Earnings Index 3m/y',
                'date': 'Tue, Oct 14',
                'time': '06:00 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '4.7%',
                'previous': '4.7%'
            },
            {
                'title': 'Claimant Count Change',
                'date': 'Tue, Oct 14',
                'time': '06:00 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '10.3K',
                'previous': '17.4K'
            },
            {
                'title': 'German ZEW Economic Sentiment',
                'date': 'Tue, Oct 14',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '41.2',
                'previous': '37.3'
            },
            {
                'title': 'Fed Chair Powell Speaks',
                'date': 'Tue, Oct 14',
                'time': '16:20 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Tue, Oct 14',
                'time': '17:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CPI y/y',
                'date': 'Tue, Oct 14',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '-0.2%',
                'previous': '-0.4%'
            },
            {
                'title': 'PPI y/y',
                'date': 'Tue, Oct 14',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '-2.3%',
                'previous': '-2.9%'
            },
            
            # WEDNESDAY, OCTOBER 15 (From ForexFactory JSON Export)
            {
                'title': 'New Loans',
                'date': 'Wed, Oct 15',
                'time': '09:03 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '1490B',
                'previous': '590B'
            },
            {
                'title': 'Empire State Manufacturing Index',
                'date': 'Wed, Oct 15',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '-1.8',
                'previous': '-8.7'
            },
            {
                'title': 'RBA Gov Bullock Speaks',
                'date': 'Wed, Oct 15',
                'time': '19:45 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Employment Change',
                'date': 'Thu, Oct 16',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '20.5K',
                'previous': '-5.4K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Thu, Oct 16',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '4.3%',
                'previous': '4.2%'
            },
            
            # THURSDAY, OCTOBER 16 (From ForexFactory JSON Export)
            {
                'title': 'GDP m/m',
                'date': 'Thu, Oct 16',
                'time': '06:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.1%',
                'previous': '0.0%'
            },
            {
                'title': 'Philly Fed Manufacturing Index',
                'date': 'Thu, Oct 16',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '8.6',
                'previous': '23.2'
            },
            {
                'title': 'FOMC Member Waller Speaks',
                'date': 'Thu, Oct 16',
                'time': '13:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Thu, Oct 16',
                'time': '16:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOC Gov Macklem Speaks',
                'date': 'Thu, Oct 16',
                'time': '17:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            
            # SATURDAY, OCTOBER 18 (From ForexFactory JSON Export)
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Sat, Oct 18',
                'time': '13:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Sat, Oct 18',
                'time': '13:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            
            # MONDAY, OCTOBER 20
            {
                'title': 'CPI q/q',
                'date': 'Sun, Oct 20',
                'time': '21:45 UTC',  # 3:15 IST - 5:30 (previous day UTC)
                'currency': 'NZD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.8%',
                'previous': '0.5%'
            },
            
            # TUESDAY, OCTOBER 21
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Tue, Oct 21',
                'time': '11:00 UTC',  # 16:30 IST - 5:30
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CPI m/m',
                'date': 'Tue, Oct 21',
                'time': '12:30 UTC',  # 18:00 IST - 5:30
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '-0.1%',
                'previous': '-0.1%'
            },
            {
                'title': 'Median CPI y/y',
                'date': 'Tue, Oct 21',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '3.0%',
                'previous': '3.1%'
            },
            {
                'title': 'Trimmed CPI y/y',
                'date': 'Tue, Oct 21',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '3.0%',
                'previous': '3.0%'
            },
            {
                'title': 'Common CPI y/y',
                'date': 'Tue, Oct 21',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '2.6%',
                'previous': '2.5%'
            },
            {
                'title': 'Core CPI m/m',
                'date': 'Tue, Oct 21',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '0.0%'
            },
            
            # WEDNESDAY, OCTOBER 22
            {
                'title': 'Trade Balance',
                'date': 'Tue, Oct 22',
                'time': '23:50 UTC',  # 5:20 IST - 5:30 (previous day UTC)
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '-0.09T',
                'previous': '-0.15T'
            },
            {
                'title': 'CPI y/y',
                'date': 'Wed, Oct 22',
                'time': '06:00 UTC',  # 11:30 IST - 5:30
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '4.0%',
                'previous': '3.8%'
            },
            {
                'title': 'Core CPI y/y',
                'date': 'Wed, Oct 22',
                'time': '06:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '3.7%',
                'previous': '3.6%'
            },
            
            # THURSDAY, OCTOBER 23
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Thu, Oct 23',
                'time': '12:30 UTC',  # 18:00 IST - 5:30
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '1.5%',
                'previous': '-1.2%'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Thu, Oct 23',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '1.0%',
                'previous': '-0.8%'
            },
            
            # FRIDAY, OCTOBER 24
            {
                'title': 'German Flash Manufacturing PMI',
                'date': 'Fri, Oct 24',
                'time': '07:30 UTC',  # 13:00 IST - 5:30
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '49.6',
                'previous': '49.5'
            },
            {
                'title': 'German Flash Services PMI',
                'date': 'Fri, Oct 24',
                'time': '07:30 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '51.1',
                'previous': '51.5'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Fri, Oct 24',
                'time': '08:30 UTC',  # 14:00 IST - 5:30
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '46.9',
                'previous': '46.2'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Fri, Oct 24',
                'time': '08:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '51.4',
                'previous': '50.8'
            },
            {
                'title': 'NHPI m/m',
                'date': 'Fri, Oct 24',
                'time': '12:30 UTC',  # 18:00 IST - 5:30
                'currency': 'CAD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '-0.3%'
            },
            {
                'title': 'Core CPI m/m',
                'date': 'Fri, Oct 24',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.3%',
                'previous': '0.3%'
            },
            {
                'title': 'CPI m/m',
                'date': 'Fri, Oct 24',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.4%',
                'previous': '0.4%'
            },
            {
                'title': 'CPI y/y',
                'date': 'Fri, Oct 24',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '2.9%'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Fri, Oct 24',
                'time': '13:45 UTC',  # 19:15 IST - 5:30
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '51.9',
                'previous': '52.0'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Fri, Oct 24',
                'time': '13:45 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '53.5',
                'previous': '54.2'
            },

            # MONDAY, NOVEMBER 10 (From ForexFactory JSON Export)
            {
                'title': 'Inflation Expectations q/q',
                'date': 'Mon, Nov 10',
                'time': '01:00 UTC',
                'currency': 'NZD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '2.28%'
            },

            # TUESDAY, NOVEMBER 11 (From ForexFactory JSON Export)
            {
                'title': 'Claimant Count Change',
                'date': 'Tue, Nov 11',
                'time': '06:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '20.3K',
                'previous': '25.8K'
            },
            {
                'title': 'Average Earnings Index 3m/y',
                'date': 'Tue, Nov 11',
                'time': '06:00 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '5.0%',
                'previous': '5.0%'
            },

            # WEDNESDAY, NOVEMBER 12 (From ForexFactory JSON Export)
            {
                'title': 'FOMC Member Waller Speaks',
                'date': 'Wed, Nov 12',
                'time': '14:20 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Employment Change',
                'date': 'Wed, Nov 12',
                'time': '23:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '20.3K',
                'previous': '14.9K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Wed, Nov 12',
                'time': '23:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '4.4%',
                'previous': '4.5%'
            },

            # THURSDAY, NOVEMBER 13 (From ForexFactory JSON Export)
            {
                'title': 'GDP m/m',
                'date': 'Thu, Nov 13',
                'time': '06:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.0%',
                'previous': '0.1%'
            },
            {
                'title': 'Prelim GDP q/q',
                'date': 'Thu, Nov 13',
                'time': '06:00 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.3%'
            },
            {
                'title': 'Core CPI m/m',
                'date': 'Thu, Nov 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.3%',
                'previous': '0.2%'
            },
            {
                'title': 'CPI m/m',
                'date': 'Thu, Nov 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.3%'
            },
            {
                'title': 'CPI y/y',
                'date': 'Thu, Nov 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '3.0%'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Nov 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # FRIDAY, NOVEMBER 14 (From ForexFactory JSON Export)
            {
                'title': 'Core PPI m/m',
                'date': 'Fri, Nov 14',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Fri, Nov 14',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'PPI m/m',
                'date': 'Fri, Nov 14',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Fri, Nov 14',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # MONDAY, DECEMBER 08 (From ForexFactory JSON Export)
            {
                'title': 'Cash Rate',
                'date': 'Mon, Dec 08',
                'time': '03:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '3.60%',
                'previous': '3.60%'
            },
            {
                'title': 'RBA Rate Statement',
                'date': 'Mon, Dec 08',
                'time': '03:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RBA Press Conference',
                'date': 'Mon, Dec 08',
                'time': '04:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # TUESDAY, DECEMBER 09 (From ForexFactory JSON Export)
            {
                'title': 'BOJ Gov Ueda Speaks',
                'date': 'Tue, Dec 09',
                'time': '09:00 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Dec 09',
                'time': '13:15 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '-13.5K'
            },
            {
                'title': 'Monetary Policy Report Hearings',
                'date': 'Tue, Dec 09',
                'time': '14:15 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'JOLTS Job Openings',
                'date': 'Tue, Dec 09',
                'time': '14:59 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '7.23M'
            },
            {
                'title': 'JOLTS Job Openings',
                'date': 'Tue, Dec 09',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '7.14M',
                'previous': '7.66M'
            },
            {
                'title': 'RBNZ Gov Breman Speaks',
                'date': 'Tue, Dec 09',
                'time': '20:45 UTC',
                'currency': 'NZD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'President Trump Speaks',
                'date': 'Tue, Dec 09',
                'time': '23:10 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CPI y/y',
                'date': 'Tue, Dec 09',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.7%',
                'previous': '0.2%'
            },
            {
                'title': 'PPI y/y',
                'date': 'Tue, Dec 09',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '-2.0%',
                'previous': '-2.1%'
            },

            # WEDNESDAY, DECEMBER 10 (From ForexFactory JSON Export)
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Wed, Dec 10',
                'time': '10:55 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Employment Cost Index q/q',
                'date': 'Wed, Dec 10',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.9%',
                'previous': '0.9%'
            },
            {
                'title': 'BOC Rate Statement',
                'date': 'Wed, Dec 10',
                'time': '14:45 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Overnight Rate',
                'date': 'Wed, Dec 10',
                'time': '14:45 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '2.25%',
                'previous': '2.25%'
            },
            {
                'title': 'BOC Press Conference',
                'date': 'Wed, Dec 10',
                'time': '15:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Federal Funds Rate',
                'date': 'Wed, Dec 10',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '3.75%',
                'previous': '4.00%'
            },
            {
                'title': 'FOMC Economic Projections',
                'date': 'Wed, Dec 10',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Statement',
                'date': 'Wed, Dec 10',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Press Conference',
                'date': 'Wed, Dec 10',
                'time': '19:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Employment Change',
                'date': 'Wed, Dec 10',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '20.0K',
                'previous': '42.2K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Wed, Dec 10',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '4.4%',
                'previous': '4.3%'
            },

            # THURSDAY, DECEMBER 11 (From ForexFactory JSON Export)
            {
                'title': 'SNB Monetary Policy Assessment',
                'date': 'Thu, Dec 11',
                'time': '08:30 UTC',
                'currency': 'CHF',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'SNB Policy Rate',
                'date': 'Thu, Dec 11',
                'time': '08:30 UTC',
                'currency': 'CHF',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.00%',
                'previous': '0.00%'
            },
            {
                'title': 'SNB Press Conference',
                'date': 'Thu, Dec 11',
                'time': '09:00 UTC',
                'currency': 'CHF',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Thu, Dec 11',
                'time': '09:50 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Thu, Dec 11',
                'time': '10:00 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Dec 11',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '220K',
                'previous': '191K'
            },

            # FRIDAY, DECEMBER 12 (From ForexFactory JSON Export)
            {
                'title': 'GDP m/m',
                'date': 'Fri, Dec 12',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.1%',
                'previous': '-0.1%'
            },

            # MONDAY, DECEMBER 15 (From ForexFactory JSON Export)
            {
                'title': 'CPI m/m',
                'date': 'Mon, Dec 15',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.1%',
                'previous': '0.2%'
            },
            {
                'title': 'Median CPI y/y',
                'date': 'Mon, Dec 15',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '2.9%',
                'previous': '2.9%'
            },
            {
                'title': 'Trimmed CPI y/y',
                'date': 'Mon, Dec 15',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '2.9%',
                'previous': '3.0%'
            },
            {
                'title': 'Common CPI y/y',
                'date': 'Mon, Dec 15',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '2.8%',
                'previous': '2.7%'
            },
            {
                'title': 'Empire State Manufacturing Index',
                'date': 'Mon, Dec 15',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '9.8',
                'previous': '18.7'
            },

            # TUESDAY, DECEMBER 16 (From ForexFactory JSON Export)
            {
                'title': 'Claimant Count Change',
                'date': 'Tue, Dec 16',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '22.3K',
                'previous': '29.0K'
            },
            {
                'title': 'Average Earnings Index 3m/y',
                'date': 'Tue, Dec 16',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '4.4%',
                'previous': '4.8%'
            },
            {
                'title': 'French Flash Manufacturing PMI',
                'date': 'Tue, Dec 16',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '48.0',
                'previous': '47.8'
            },
            {
                'title': 'French Flash Services PMI',
                'date': 'Tue, Dec 16',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '51.1',
                'previous': '50.8'
            },
            {
                'title': 'German Flash Manufacturing PMI',
                'date': 'Tue, Dec 16',
                'time': '08:30 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '48.6',
                'previous': '48.4'
            },
            {
                'title': 'German Flash Services PMI',
                'date': 'Tue, Dec 16',
                'time': '08:30 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '53.0',
                'previous': '52.7'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Tue, Dec 16',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '50.3',
                'previous': '50.2'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Tue, Dec 16',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '51.7',
                'previous': '50.5'
            },
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Dec 16',
                'time': '13:20 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '4.8K'
            },
            {
                'title': 'Average Hourly Earnings m/m',
                'date': 'Tue, Dec 16',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.3%',
                'previous': '0.2%'
            },
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Tue, Dec 16',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.3%'
            },
            {
                'title': 'Non-Farm Employment Change',
                'date': 'Tue, Dec 16',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '50K',
                'previous': '119K'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Tue, Dec 16',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Tue, Dec 16',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '4.5%',
                'previous': '4.4%'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Tue, Dec 16',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '52.3',
                'previous': '51.9'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Tue, Dec 16',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '54.0',
                'previous': '55.0'
            },
            {
                'title': 'BOC Gov Macklem Speaks',
                'date': 'Tue, Dec 16',
                'time': '17:45 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # WEDNESDAY, DECEMBER 17 (From ForexFactory JSON Export)
            {
                'title': 'CPI y/y',
                'date': 'Wed, Dec 17',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '3.5%',
                'previous': '3.6%'
            },
            {
                'title': 'German ifo Business Climate',
                'date': 'Wed, Dec 17',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '88.1',
                'previous': '88.1'
            },
            {
                'title': 'FOMC Member Waller Speaks',
                'date': 'Wed, Dec 17',
                'time': '13:15 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'GDP q/q',
                'date': 'Wed, Dec 17',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.8%',
                'previous': '-0.9%'
            },

            # THURSDAY, DECEMBER 18 (From ForexFactory JSON Export)
            {
                'title': 'BOJ Policy Rate',
                'date': 'Thu, Dec 18',
                'time': '03:30 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '<0.75%',
                'previous': '<0.50%'
            },
            {
                'title': 'Monetary Policy Statement',
                'date': 'Thu, Dec 18',
                'time': '03:30 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Monetary Policy Summary',
                'date': 'Thu, Dec 18',
                'time': '12:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'MPC Official Bank Rate Votes',
                'date': 'Thu, Dec 18',
                'time': '12:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0-5-4',
                'previous': '0-4-5'
            },
            {
                'title': 'Official Bank Rate',
                'date': 'Thu, Dec 18',
                'time': '12:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '3.75%',
                'previous': '4.00%'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Thu, Dec 18',
                'time': '12:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Main Refinancing Rate',
                'date': 'Thu, Dec 18',
                'time': '13:15 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '2.15%',
                'previous': '2.15%'
            },
            {
                'title': 'Monetary Policy Statement',
                'date': 'Thu, Dec 18',
                'time': '13:15 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CPI y/y',
                'date': 'Thu, Dec 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '3.0%'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Dec 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '224K',
                'previous': '236K'
            },
            {
                'title': 'Philly Fed Manufacturing Index',
                'date': 'Thu, Dec 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '3.2',
                'previous': '-1.7'
            },
            {
                'title': 'Core CPI m/m',
                'date': 'Thu, Dec 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '0.2%'
            },
            {
                'title': 'CPI m/m',
                'date': 'Thu, Dec 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '0.3%'
            },
            {
                'title': 'ECB Press Conference',
                'date': 'Thu, Dec 18',
                'time': '13:45 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # FRIDAY, DECEMBER 19 (From ForexFactory JSON Export)
            {
                'title': 'BOJ Press Conference',
                'date': 'Fri, Dec 19',
                'time': '06:30 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Fri, Dec 19',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.4%',
                'previous': '-1.1%'
            },
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Fri, Dec 19',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.0%',
                'previous': '0.2%'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Fri, Dec 19',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.0%',
                'previous': '-0.7%'
            },
            {
                'title': 'Existing Home Sales',
                'date': 'Fri, Dec 19',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '4.15M',
                'previous': '4.10M'
            },
            {
                'title': 'Revised UoM Consumer Sentiment',
                'date': 'Fri, Dec 19',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '53.3',
                'previous': '53.3'
            },

            # TUESDAY, DECEMBER 23 (From ForexFactory JSON Export)
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Dec 23',
                'time': '13:20 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '11.5K',
                'forecast': 'N/A',
                'previous': '16.3K'
            },
            {
                'title': 'GDP m/m',
                'date': 'Tue, Dec 23',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '-0.3',
                'forecast': '-0.3%',
                'previous': '0.2%'
            },
            {
                'title': 'Prelim GDP q/q',
                'date': 'Tue, Dec 23',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '4.3',
                'forecast': '3.2%',
                'previous': '3.8%'
            },
            {
                'title': 'Core Durable Goods Orders m/m',
                'date': 'Tue, Dec 23',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '0.2',
                'forecast': '-1.4%',
                'previous': '0.6%'
            },
            {
                'title': 'Durable Goods Orders m/m',
                'date': 'Tue, Dec 23',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '-2.2',
                'forecast': '-1.5%',
                'previous': '0.7%'
            },
            {
                'title': 'Prelim GDP Price Index q/q',
                'date': 'Tue, Dec 23',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '3.8',
                'forecast': '2.7%',
                'previous': '2.1%'
            },
            {
                'title': 'CB Consumer Confidence',
                'date': 'Tue, Dec 23',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '89.1',
                'forecast': '91.7',
                'previous': '88.7'
            },
            {
                'title': 'Richmond Manufacturing Index',
                'date': 'Tue, Dec 23',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '-7',
                'forecast': '-7',
                'previous': '-15'
            },

            # WEDNESDAY, DECEMBER 24 (From ForexFactory JSON Export)
            {
                'title': 'BOJ Gov Ueda Speaks',
                'date': 'Wed, Dec 24',
                'time': '04:59 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Wed, Dec 24',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '214K',
                'forecast': '220K',
                'previous': '224K'
            },

            # SUNDAY, DECEMBER 28 (From ForexFactory JSON Export - New Year's Week)
            {
                'title': 'BOJ Summary of Opinions',
                'date': 'Sun, Dec 28',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # MONDAY, DECEMBER 29 (From ForexFactory JSON Export - New Year's Week)
            {
                'title': 'Pending Home Sales m/m',
                'date': 'Mon, Dec 29',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.9%',
                'previous': '1.9%'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Mon, Dec 29',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '-2.0M',
                'previous': '-1.3M'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Mon, Dec 29',
                'time': '17:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '-169B',
                'previous': '-167B'
            },

            # TUESDAY, DECEMBER 30 (From ForexFactory JSON Export - New Year's Week)
            {
                'title': 'Manufacturing PMI',
                'date': 'Tue, Dec 30',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '49.4',
                'previous': '49.2'
            },
            {
                'title': 'Non-Manufacturing PMI',
                'date': 'Tue, Dec 30',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '49.8',
                'previous': '49.5'
            },
            {
                'title': 'RatingDog Manufacturing PMI',
                'date': 'Tue, Dec 30',
                'time': '01:45 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '49.7',
                'previous': '49.9'
            },
            {
                'title': 'KOF Economic Barometer',
                'date': 'Tue, Dec 30',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '101.5',
                'previous': '101.7'
            },
            {
                'title': 'Spanish Flash CPI y/y',
                'date': 'Tue, Dec 30',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '2.9%',
                'previous': '3.0%'
            },
            {
                'title': 'HPI m/m',
                'date': 'Tue, Dec 30',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.1%',
                'previous': '0.0%'
            },
            {
                'title': 'S&P/CS Composite-20 HPI y/y',
                'date': 'Tue, Dec 30',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '1.1%',
                'previous': '1.4%'
            },
            {
                'title': 'Chicago PMI',
                'date': 'Tue, Dec 30',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '39.6',
                'previous': '36.3'
            },
            {
                'title': 'FOMC Meeting Minutes',
                'date': 'Tue, Dec 30',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Tue, Dec 30',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # WEDNESDAY, DECEMBER 31 (From ForexFactory JSON Export - New Year's Week)
            {
                'title': 'Unemployment Claims',
                'date': 'Wed, Dec 31',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '215K',
                'previous': '214K'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Wed, Dec 31',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Wed, Dec 31',
                'time': '17:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # FRIDAY, JANUARY 02 (From ForexFactory JSON Export - New Year's Week)
            {
                'title': 'Nationwide HPI m/m',
                'date': 'Fri, Jan 02',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.1%',
                'previous': '0.3%'
            },
            {
                'title': 'Spanish Manufacturing PMI',
                'date': 'Fri, Jan 02',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '51.2',
                'previous': '51.5'
            },
            {
                'title': 'Italian Manufacturing PMI',
                'date': 'Fri, Jan 02',
                'time': '08:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '50.1',
                'previous': '50.6'
            },
            {
                'title': 'French Final Manufacturing PMI',
                'date': 'Fri, Jan 02',
                'time': '08:50 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '50.6',
                'previous': '50.6'
            },
            {
                'title': 'German Final Manufacturing PMI',
                'date': 'Fri, Jan 02',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '47.7',
                'previous': '47.7'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Fri, Jan 02',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '49.2',
                'previous': '49.2'
            },
            {
                'title': 'M3 Money Supply y/y',
                'date': 'Fri, Jan 02',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '2.7%',
                'previous': '2.8%'
            },
            {
                'title': 'Private Loans y/y',
                'date': 'Fri, Jan 02',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '2.8%',
                'previous': '2.8%'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Fri, Jan 02',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '51.2',
                'previous': '51.2'
            },
            {
                'title': 'Manufacturing PMI',
                'date': 'Fri, Jan 02',
                'time': '14:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '48.4'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Fri, Jan 02',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '51.8',
                'previous': '51.8'
            },

            # SATURDAY, JANUARY 03 (From ForexFactory JSON Export - New Year's Week)
            {
                'title': 'FOMC Member Paulson Speaks',
                'date': 'Sat, Jan 03',
                'time': '15:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Paulson Speaks',
                'date': 'Sat, Jan 03',
                'time': '19:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # SUNDAY, JANUARY 04 (From ForexFactory JSON Export - Week of Jan 4)
            {
                'title': 'FOMC Member Kashkari Speaks',
                'date': 'Sun, Jan 04',
                'time': '17:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Sun, Jan 04',
                'time': '00:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '49.8',
                'previous': '49.7'
            },
            {
                'title': 'RatingDog Services PMI',
                'date': 'Sun, Jan 04',
                'time': '01:45 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '52.0',
                'previous': '52.1'
            },

            # MONDAY, JANUARY 05 (From ForexFactory JSON Export - Week of Jan 4)
            {
                'title': 'Retail Sales y/y',
                'date': 'Mon, Jan 05',
                'time': '07:30 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '2.3%',
                'forecast': '2.5%',
                'previous': '2.7%'
            },
            {
                'title': 'Spanish Unemployment Change',
                'date': 'Mon, Jan 05',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-16.3K',
                'forecast': '5.7K',
                'previous': '-18.8K'
            },
            {
                'title': 'Manufacturing PMI',
                'date': 'Mon, Jan 05',
                'time': '08:30 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '45.8',
                'forecast': '49.7',
                'previous': '49.7'
            },
            {
                'title': 'M4 Money Supply m/m',
                'date': 'Mon, Jan 05',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.8%',
                'forecast': '-0.1%',
                'previous': '-0.2%'
            },
            {
                'title': 'Mortgage Approvals',
                'date': 'Mon, Jan 05',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '65K',
                'forecast': '64K',
                'previous': '65K'
            },
            {
                'title': 'Net Lending to Individuals m/m',
                'date': 'Mon, Jan 05',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '6.6B',
                'forecast': '5.2B',
                'previous': '5.4B'
            },
            {
                'title': 'ISM Manufacturing PMI',
                'date': 'Mon, Jan 05',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '47.9',
                'forecast': '48.3',
                'previous': '48.2'
            },
            {
                'title': 'ISM Manufacturing Prices',
                'date': 'Mon, Jan 05',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '58.5',
                'forecast': '59.0',
                'previous': '58.5'
            },
            {
                'title': 'Wards Total Vehicle Sales',
                'date': 'Mon, Jan 05',
                'time': '15:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '16.0M',
                'forecast': '15.7M',
                'previous': '15.6M'
            },
            {
                'title': 'Monetary Base y/y',
                'date': 'Mon, Jan 05',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-9.8',
                'forecast': '-8.0%',
                'previous': '-8.5%'
            },
            {
                'title': 'BRC Retail Sales Monitor y/y',
                'date': 'Mon, Jan 05',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.6%',
                'previous': '1.2%'
            },
            {
                'title': '10-y Bond Auction',
                'date': 'Mon, Jan 05',
                'time': '03:35 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '1.87|3.6'
            },

            # TUESDAY, JANUARY 06 (From ForexFactory JSON Export - Week of Jan 4)
            {
                'title': 'German Prelim CPI m/m',
                'date': 'Tue, Jan 06',
                'time': '07:29 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '0.0%',
                'forecast': '0.3%',
                'previous': '-0.2%'
            },
            {
                'title': 'French Prelim CPI m/m',
                'date': 'Tue, Jan 06',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.2%',
                'previous': '-0.1%'
            },
            {
                'title': 'Spanish Services PMI',
                'date': 'Tue, Jan 06',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '57.1',
                'forecast': '54.7',
                'previous': '55.6'
            },
            {
                'title': 'Italian Services PMI',
                'date': 'Tue, Jan 06',
                'time': '08:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '51.5%',
                'forecast': '54.1',
                'previous': '55.0'
            },
            {
                'title': 'French Final Services PMI',
                'date': 'Tue, Jan 06',
                'time': '08:50 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '50.1',
                'forecast': '50.3',
                'previous': '50.2'
            },
            {
                'title': 'German Final Services PMI',
                'date': 'Tue, Jan 06',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '52.7%',
                'forecast': '52.6',
                'previous': '52.6'
            },
            {
                'title': 'Final Services PMI',
                'date': 'Tue, Jan 06',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '52.4',
                'forecast': '52.6',
                'previous': '52.6'
            },
            {
                'title': 'Final Services PMI',
                'date': 'Tue, Jan 06',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '51.4',
                'forecast': '52.1',
                'previous': '52.1'
            },
            {
                'title': 'FOMC Member Barkin Speaks',
                'date': 'Tue, Jan 06',
                'time': '13:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Final Services PMI',
                'date': 'Tue, Jan 06',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '52.9',
                'previous': '52.9'
            },
            {
                'title': 'GDT Price Index',
                'date': 'Tue, Jan 06',
                'time': '15:50 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '-4.4%'
            },
            {
                'title': 'President Trump Speaks',
                'date': 'Tue, Jan 06',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Tue, Jan 06',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CPI m/m',
                'date': 'Wed, Jan 07',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '0.0%',
                'forecast': '0.1%',
                'previous': '0.0%'
            },
            {
                'title': 'CPI y/y',
                'date': 'Wed, Jan 07',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '3.4%',
                'forecast': '3.7%',
                'previous': '3.8%'
            },
            {
                'title': 'Trimmed Mean CPI m/m',
                'date': 'Wed, Jan 07',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '0.3%',
                'forecast': '0.2%',
                'previous': '1.0%'
            },
            {
                'title': 'Building Approvals m/m',
                'date': 'Tue, Jan 06',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '15.2%',
                'forecast': '1.9%',
                'previous': '-6.1%'
            },

            # WEDNESDAY, JANUARY 07 (From ForexFactory JSON Export - Week of Jan 4)
            {
                'title': 'German Retail Sales m/m',
                'date': 'Wed, Jan 07',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.6%',
                'forecast': '0.2%',
                'previous': '-0.3%'
            },
            {
                'title': 'Foreign Currency Reserves',
                'date': 'Wed, Jan 07',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '727B'
            },
            {
                'title': 'German Unemployment Change',
                'date': 'Wed, Jan 07',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3K',
                'forecast': '5K',
                'previous': '1K'
            },
            {
                'title': 'Construction PMI',
                'date': 'Wed, Jan 07',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '40.1',
                'forecast': '42.7',
                'previous': '39.4'
            },
            {
                'title': 'Housing Equity Withdrawal q/q',
                'date': 'Wed, Jan 07',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-10.9B',
                'forecast': '-8.7B',
                'previous': '-16.1B'
            },
            {
                'title': 'Core CPI Flash Estimate y/y',
                'date': 'Wed, Jan 07',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '2.3%',
                'forecast': '2.4%',
                'previous': '2.4%'
            },
            {
                'title': 'CPI Flash Estimate y/y',
                'date': 'Wed, Jan 07',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '2.0%',
                'forecast': '2.0%',
                'previous': '2.2%'
            },
            {
                'title': 'Italian Prelim CPI m/m',
                'date': 'Wed, Jan 07',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.1%',
                'previous': '-0.2%'
            },
            {
                'title': 'German 10-y Bond Auction',
                'date': 'Wed, Jan 07',
                'time': '10:42 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '2.83|1.3',
                'forecast': 'N/A',
                'previous': '2.67|2.0'
            },
            {
                'title': 'ADP Non-Farm Employment Change',
                'date': 'Wed, Jan 07',
                'time': '13:15 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '41K',
                'forecast': '47K',
                'previous': '-29K'
            },
            {
                'title': 'Ivey PMI',
                'date': 'Wed, Jan 07',
                'time': '15:00 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '51.9',
                'forecast': '49.5',
                'previous': '48.4'
            },
            {
                'title': 'ISM Services PMI',
                'date': 'Wed, Jan 07',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '54.4',
                'forecast': '52.2',
                'previous': '52.6'
            },
            {
                'title': 'JOLTS Job Openings',
                'date': 'Wed, Jan 07',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '7.15M',
                'forecast': '7.61M',
                'previous': '7.67M'
            },
            {
                'title': 'Factory Orders m/m',
                'date': 'Wed, Jan 07',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-1.3%',
                'forecast': '-1.1%',
                'previous': '0.2%'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Wed, Jan 07',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-3.8M',
                'forecast': 'N/A',
                'previous': '-1.9M'
            },
            {
                'title': 'FOMC Member Bowman Speaks',
                'date': 'Wed, Jan 07',
                'time': '18:10 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Average Cash Earnings y/y',
                'date': 'Wed, Jan 07',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '0.5%',
                'forecast': '2.3%',
                'previous': '2.6%'
            },
            {
                'title': 'Goods Trade Balance',
                'date': 'Wed, Jan 07',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '2.94B',
                'forecast': '5.55B',
                'previous': '4.39B'
            },
            {
                'title': '30-y Bond Auction',
                'date': 'Wed, Jan 07',
                'time': '03:35 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.45|3.1',
                'forecast': 'N/A',
                'previous': '3.43|4.0'
            },

            # THURSDAY, JANUARY 08 (From ForexFactory JSON Export - Week of Jan 4)
            {
                'title': 'Consumer Confidence',
                'date': 'Thu, Jan 08',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '37.2',
                'forecast': '37.8',
                'previous': '37.5'
            },
            {
                'title': 'German Factory Orders m/m',
                'date': 'Thu, Jan 08',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '5.6%',
                'forecast': '-0.9%',
                'previous': '1.5%'
            },
            {
                'title': 'Halifax HPI m/m',
                'date': 'Thu, Jan 08',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-0.6%',
                'forecast': '0.1%',
                'previous': '0.0%'
            },
            {
                'title': 'CPI m/m',
                'date': 'Thu, Jan 08',
                'time': '07:30 UTC',
                'currency': 'CHF',
                'impact': 'high',
                'actual': '0.0%',
                'forecast': '0.0%',
                'previous': '-0.2%'
            },
            {
                'title': 'French Trade Balance',
                'date': 'Thu, Jan 08',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-4.2B',
                'forecast': '-4.3B',
                'previous': '-3.9B'
            },
            {
                'title': 'Summary of Monetary Policy Discussions',
                'date': 'Thu, Jan 08',
                'time': '08:30 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Italian Monthly Unemployment Rate',
                'date': 'Thu, Jan 08',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '5.7%',
                'forecast': '6.0%',
                'previous': '6.0%'
            },
            {
                'title': 'PPI m/m',
                'date': 'Thu, Jan 08',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.5%',
                'forecast': '0.4%',
                'previous': '0.1%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Thu, Jan 08',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '6.3%',
                'forecast': '6.4%',
                'previous': '6.4%'
            },
            {
                'title': 'Spanish 10-y Bond Auction',
                'date': 'Thu, Jan 08',
                'time': '10:03 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'French 10-y Bond Auction',
                'date': 'Thu, Jan 08',
                'time': '10:18 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Challenger Job Cuts y/y',
                'date': 'Thu, Jan 08',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-8.3%',
                'forecast': 'N/A',
                'previous': '23.5%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Jan 08',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-0.6B',
                'forecast': '-1.5B',
                'previous': '0.2B'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Jan 08',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '208K',
                'forecast': '216K',
                'previous': '199K'
            },
            {
                'title': 'Prelim Nonfarm Productivity q/q',
                'date': 'Thu, Jan 08',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '4.9%',
                'forecast': '3.7%',
                'previous': '2.4%'
            },
            {
                'title': 'Prelim Unit Labor Costs q/q',
                'date': 'Thu, Jan 08',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-1.9%',
                'forecast': '0.5%',
                'previous': '1.6%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Jan 08',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-29.4B',
                'forecast': '-58.5B',
                'previous': '-52.8B'
            },
            {
                'title': 'Final Wholesale Inventories m/m',
                'date': 'Thu, Jan 08',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.5%'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Jan 08',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-119B',
                'forecast': 'N/A',
                'previous': '-38B'
            },
            {
                'title': 'Consumer Credit m/m',
                'date': 'Thu, Jan 08',
                'time': '20:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '4.2B',
                'forecast': '10.3B',
                'previous': '9.2B'
            },
            {
                'title': 'Household Spending y/y',
                'date': 'Thu, Jan 08',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.9%',
                'forecast': '-1.0%',
                'previous': '-3.0%'
            },
            {
                'title': 'CPI y/y',
                'date': 'Thu, Jan 08',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': '0.8%',
                'forecast': '0.8%',
                'previous': '0.7%'
            },
            {
                'title': 'PPI y/y',
                'date': 'Thu, Jan 08',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': '-1.9%',
                'forecast': '-1.5%',
                'previous': '-2.2%'
            },

            # FRIDAY, JANUARY 09 (From ForexFactory JSON Export - Week of Jan 4)
            {
                'title': 'Leading Indicators',
                'date': 'Fri, Jan 09',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '110.5%',
                'forecast': '110.4%',
                'previous': '110.0%'
            },
            {
                'title': 'German Industrial Production m/m',
                'date': 'Fri, Jan 09',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.8%',
                'forecast': '-0.5%',
                'previous': '1.8%'
            },
            {
                'title': 'German Trade Balance',
                'date': 'Fri, Jan 09',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '13.1B',
                'forecast': '16.3B',
                'previous': '16.9B'
            },
            {
                'title': 'French Consumer Spending m/m',
                'date': 'Fri, Jan 09',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.3%',
                'forecast': '-0.1%',
                'previous': '0.4%'
            },
            {
                'title': 'French Industrial Production m/m',
                'date': 'Fri, Jan 09',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': '-0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Jan 09',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '3.0%',
                'forecast': '3.0%',
                'previous': '3.0%'
            },
            {
                'title': 'Italian Retail Sales m/m',
                'date': 'Fri, Jan 09',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.3%',
                'previous': '0.5%'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Fri, Jan 09',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.5%',
                'forecast': '0.1%',
                'previous': '0.0%'
            },
            {
                'title': 'Building Permits',
                'date': 'Fri, Jan 09',
                'time': '13:29 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.42M',
                'forecast': 'N/A',
                'previous': '1.31M'
            },
            {
                'title': 'Housing Starts',
                'date': 'Fri, Jan 09',
                'time': '13:29 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.31M',
                'forecast': 'N/A',
                'previous': '1.31M'
            },
            {
                'title': 'Employment Change',
                'date': 'Fri, Jan 09',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '8.2K',
                'forecast': '-1.8K',
                'previous': '53.6K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Jan 09',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '6.8%',
                'forecast': '6.7%',
                'previous': '6.5%'
            },
            {
                'title': 'Average Hourly Earnings m/m',
                'date': 'Fri, Jan 09',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.1%'
            },
            {
                'title': 'Non-Farm Employment Change',
                'date': 'Fri, Jan 09',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '50K',
                'forecast': '57K',
                'previous': '56K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Jan 09',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '4.4%',
                'forecast': '4.5%',
                'previous': '4.6%'
            },
            {
                'title': 'Building Permits',
                'date': 'Fri, Jan 09',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.41M',
                'forecast': '1.35M',
                'previous': '1.42M'
            },
            {
                'title': 'Housing Starts',
                'date': 'Fri, Jan 09',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.25M',
                'forecast': '1.33M',
                'previous': '1.31M'
            },
            {
                'title': 'Prelim UoM Consumer Sentiment',
                'date': 'Fri, Jan 09',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '54.0',
                'forecast': '53.5',
                'previous': '52.9'
            },
            {
                'title': 'Prelim UoM Inflation Expectations',
                'date': 'Fri, Jan 09',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '4.2%',
                'forecast': 'N/A',
                'previous': '4.2%'
            },
            {
                'title': 'FOMC Member Barkin Speaks',
                'date': 'Fri, Jan 09',
                'time': '18:35 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

             # SUNDAY, JANUARY 11 From ForexFactory JSON Export - Week of Jan 11

            {
                'title': 'ANZ Job Advertisements m/m',
                'date': 'Sun, Jan 11',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-0.5%',
                'forecast': 'N/A',
                'previous': '-0.8%'
            },
            {
                'title': 'Household Spending m/m',
                'date': 'Sun, Jan 11',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '1.0%',
                'forecast': '0.6%',
                'previous': '1.3%'
            },

            # MONDAY, JANUARY 12
            {
                'title': 'SECO Consumer Climate',
                'date': 'Mon, Jan 12',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '-31',
                'forecast': '-33',
                'previous': '-34'
            },
            {
                'title': 'Sentix Investor Confidence',
                'date': 'Mon, Jan 12',
                'time': '09:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-1.8',
                'forecast': '-5.1',
                'previous': '-6.2'
            },
            {
                'title': 'FOMC Member Barkin Speaks',
                'date': 'Mon, Jan 12',
                'time': '17:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': '10-y Bond Auction',
                'date': 'Mon, Jan 12',
                'time': '18:01 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '4.18|2.6'
            },
            {
                'title': 'NZIER Business Confidence',
                'date': 'Mon, Jan 12',
                'time': '21:00 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '48',
                'forecast': 'N/A',
                'previous': '18'
            },
            {
                'title': 'FOMC Member Williams Speaks',
                'date': 'Mon, Jan 12',
                'time': '23:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Westpac Consumer Sentiment',
                'date': 'Mon, Jan 12',
                'time': '23:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-1.7%',
                'forecast': 'N/A',
                'previous': '-9.0%'
            },
            {
                'title': 'Bank Lending y/y',
                'date': 'Mon, Jan 12',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '4.4%',
                'forecast': '4.1%',
                'previous': '4.2%'
            },
            {
                'title': 'Current Account',
                'date': 'Mon, Jan 12',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.14T',
                'forecast': '3.04T',
                'previous': '2.48T'
            },
            {
                'title': 'BRC Retail Sales Monitor y/y',
                'date': 'Mon, Jan 12',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '1.0%',
                'forecast': '0.6%',
                'previous': '1.2%'
            },

            # TUESDAY, JANUARY 13
            {
                'title': 'Economy Watchers Sentiment',
                'date': 'Tue, Jan 13',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '48.6',
                'forecast': '48.8',
                'previous': '48.7'
            },
            {
                'title': 'French Gov Budget Balance',
                'date': 'Tue, Jan 13',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-155.4B',
                'forecast': 'N/A',
                'previous': '-136.2B'
            },
            {
                'title': 'M2 Money Supply y/y',
                'date': 'Tue, Jan 13',
                'time': '09:03 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '8.0%',
                'previous': '8.0%'
            },
            {
                'title': 'New Loans',
                'date': 'Tue, Jan 13',
                'time': '09:03 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '450B',
                'previous': '390B'
            },
            {
                'title': 'NFIB Small Business Index',
                'date': 'Tue, Jan 13',
                'time': '11:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '99.5',
                'forecast': '99.5',
                'previous': '99.0'
            },
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Jan 13',
                'time': '13:20 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '11.8K',
                'forecast': 'N/A',
                'previous': '11.5K'
            },
            {
                'title': 'Building Permits m/m',
                'date': 'Tue, Jan 13',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-13.1%',
                'forecast': 'N/A',
                'previous': '14.9%'
            },
            {
                'title': 'Core CPI m/m',
                'date': 'Tue, Jan 13',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.2%',
                'forecast': '0.3%',
                'previous': '0.2%'
            },
            {
                'title': 'CPI m/m',
                'date': 'Tue, Jan 13',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.3%'
            },
            {
                'title': 'CPI y/y',
                'date': 'Tue, Jan 13',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '2.7%',
                'forecast': '2.7%',
                'previous': '2.7%'
            },
            {
                'title': 'New Home Sales',
                'date': 'Tue, Jan 13',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '738K',
                'forecast': '715K',
                'previous': '718K'
            },
            {
                'title': 'FOMC Member Musalem Speaks',
                'date': 'Tue, Jan 13',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'New Home Sales',
                'date': 'Tue, Jan 13',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '800K'
            },
            {
                'title': 'RCM/TIPP Economic Optimism',
                'date': 'Tue, Jan 13',
                'time': '15:10 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '47.2',
                'forecast': '48.2',
                'previous': '47.9'
            },
            {
                'title': '30-y Bond Auction',
                'date': 'Tue, Jan 13',
                'time': '18:01 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '4.77|2.4'
            },
            {
                'title': 'Federal Budget Balance',
                'date': 'Tue, Jan 13',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '-173.3B'
            },
            {
                'title': 'FOMC Member Barkin Speaks',
                'date': 'Tue, Jan 13',
                'time': '21:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Tue, Jan 13',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Building Consents m/m',
                'date': 'Tue, Jan 13',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '2.8%',
                'forecast': 'N/A',
                'previous': '-0.9%'
            },
            {
                'title': 'M2 Money Stock y/y',
                'date': 'Tue, Jan 13',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '1.7%',
                'forecast': '1.9%',
                'previous': '1.8%'
            },
            {
                'title': 'ANZ Commodity Prices m/m',
                'date': 'Tue, Jan 13',
                'time': '00:00 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '-2.1%',
                'forecast': 'N/A',
                'previous': '-1.6%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Tue, Jan 13',
                'time': '03:03 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '809B',
                'forecast': '820B',
                'previous': '793B'
            },
            {
                'title': 'USD-Denominated Trade Balance',
                'date': 'Tue, Jan 13',
                'time': '03:04 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '114.1B',
                'forecast': '114.2B',
                'previous': '111.7B'
            },

            # WEDNESDAY, JANUARY 14
            {
                'title': 'Prelim Machine Tool Orders y/y',
                'date': 'Wed, Jan 14',
                'time': '06:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '10.6%',
                'forecast': 'N/A',
                'previous': '14.2%'
            },
            {
                'title': 'MPC Member Taylor Speaks',
                'date': 'Wed, Jan 14',
                'time': '08:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': '10-y Bond Auction',
                'date': 'Wed, Jan 14',
                'time': '10:33 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '4.46|3.3',
                'forecast': 'N/A',
                'previous': '4.61|3.1'
            },
            {
                'title': 'German 30-y Bond Auction',
                'date': 'Wed, Jan 14',
                'time': '10:34 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.45|2.1',
                'forecast': 'N/A',
                'previous': '3.26|1.3'
            },
            {
                'title': 'Core PPI m/m',
                'date': 'Wed, Jan 14',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.0%',
                'forecast': '0.2%',
                'previous': '0.3%'
            },
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Wed, Jan 14',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.5%',
                'forecast': '0.4%',
                'previous': '0.2%'
            },
            {
                'title': 'PPI m/m',
                'date': 'Wed, Jan 14',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.1'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Wed, Jan 14',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.6%',
                'forecast': '0.5%',
                'previous': '-0.1%'
            },
            {
                'title': 'Current Account',
                'date': 'Wed, Jan 14',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-226B',
                'forecast': '-240B',
                'previous': '-249B'
            },
            {
                'title': 'Core PPI m/m',
                'date': 'Wed, Jan 14',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '0.3%',
                'forecast': 'N/A',
                'previous': '0.1%'
            },
            {
                'title': 'PPI m/m',
                'date': 'Wed, Jan 14',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '0.1%',
                'forecast': 'N/A',
                'previous': '0.3%'
            },
            {
                'title': 'FOMC Member Paulson Speaks',
                'date': 'Wed, Jan 14',
                'time': '14:50 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Business Inventories m/m',
                'date': 'Wed, Jan 14',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.2%'
            },
            {
                'title': 'Existing Home Sales',
                'date': 'Wed, Jan 14',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '4.35M',
                'forecast': '4.24M',
                'previous': '4.13M'
            },
            {
                'title': 'FOMC Member Miran Speaks',
                'date': 'Wed, Jan 14',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'MPC Member Ramsden Speaks',
                'date': 'Wed, Jan 14',
                'time': '15:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Wed, Jan 14',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '-3.8M'
            },
            {
                'title': 'FOMC Member Kashkari Speaks',
                'date': 'Wed, Jan 14',
                'time': '17:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Beige Book',
                'date': 'Wed, Jan 14',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Williams Speaks',
                'date': 'Wed, Jan 14',
                'time': '19:10 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'PPI y/y',
                'date': 'Wed, Jan 14',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.4%',
                'forecast': '2.4%',
                'previous': '2.7%'
            },
            {
                'title': 'MI Inflation Expectations',
                'date': 'Wed, Jan 14',
                'time': '00:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '4.6%',
                'forecast': 'N/A',
                'previous': '4.7%'
            },
            {
                'title': 'RICS House Price Balance',
                'date': 'Wed, Jan 14',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-14%',
                'forecast': '-15%',
                'previous': '-16%'
            },

            # THURSDAY, JANUARY 15
            {
                'title': 'German WPI m/m',
                'date': 'Thu, Jan 15',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': '0.2%',
                'previous': '0.3%'
            },
            {
                'title': 'GDP m/m',
                'date': 'Thu, Jan 15',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '0.3%',
                'forecast': '0.0%',
                'previous': '-0.1%'
            },
            {
                'title': 'Construction Output m/m',
                'date': 'Thu, Jan 15',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-1.3%',
                'forecast': '0.0%',
                'previous': '-0.6%'
            },
            {
                'title': 'Goods Trade Balance',
                'date': 'Thu, Jan 15',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-23.7B',
                'forecast': '-20.4B',
                'previous': '-22.5B'
            },
            {
                'title': 'Index of Services 3m/3m',
                'date': 'Thu, Jan 15',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.0%',
                'previous': '0.0%'
            },
            {
                'title': 'Industrial Production m/m',
                'date': 'Thu, Jan 15',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '1.1%',
                'forecast': '0.1%',
                'previous': '1.1%'
            },
            {
                'title': 'Manufacturing Production m/m',
                'date': 'Thu, Jan 15',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '2.1%',
                'forecast': '0.5%',
                'previous': '0.5%'
            },
            {
                'title': 'Foreign Direct Investment ytd/y',
                'date': 'Thu, Jan 15',
                'time': '07:02 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '-7.5%'
            },
            {
                'title': 'French Final CPI m/m',
                'date': 'Thu, Jan 15',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.1%',
                'previous': '0.1%'
            },
            {
                'title': 'ECB Economic Bulletin',
                'date': 'Thu, Jan 15',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Italian Industrial Production m/m',
                'date': 'Thu, Jan 15',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '1.5%',
                'forecast': '0.5%',
                'previous': '-1.0%'
            },
            {
                'title': 'BOE Credit Conditions Survey',
                'date': 'Thu, Jan 15',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Industrial Production m/m',
                'date': 'Thu, Jan 15',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.7%',
                'forecast': '0.0%',
                'previous': '0.8%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Jan 15',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '10.7B',
                'forecast': '15.2B',
                'previous': '14.0B'
            },
            {
                'title': 'Spanish 10-y Bond Auction',
                'date': 'Thu, Jan 15',
                'time': '10:03 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Italian Trade Balance',
                'date': 'Thu, Jan 15',
                'time': '11:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '5.08B',
                'forecast': '5.22B',
                'previous': '4.16B'
            },
            {
                'title': 'Manufacturing Sales m/m',
                'date': 'Thu, Jan 15',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-1.2%',
                'forecast': '-1.1%',
                'previous': '-1.0%'
            },
            {
                'title': 'Wholesale Sales m/m',
                'date': 'Thu, Jan 15',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-1.8%',
                'forecast': '0.1%',
                'previous': '0.1%'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Jan 15',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '198K',
                'forecast': '210K',
                'previous': '208K'
            },
            {
                'title': 'Empire State Manufacturing Index',
                'date': 'Thu, Jan 15',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '7.7',
                'forecast': '1.1',
                'previous': '-3.9'
            },
            {
                'title': 'Philly Fed Manufacturing Index',
                'date': 'Thu, Jan 15',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '12.6',
                'forecast': '-2.9%',
                'previous': '-10.2'
            },
            {
                'title': 'Import Prices m/m',
                'date': 'Thu, Jan 15',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.4%',
                'forecast': '-0.2%',
                'previous': '0.0%'
            },
            {
                'title': 'FOMC Member Bostic Speaks',
                'date': 'Thu, Jan 15',
                'time': '13:35 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Jan 15',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-71B',
                'forecast': '-89B',
                'previous': '-119B'
            },
            {
                'title': 'FOMC Member Barkin Speaks',
                'date': 'Thu, Jan 15',
                'time': '17:40 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'TIC Long-Term Purchases',
                'date': 'Thu, Jan 15',
                'time': '21:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '220.2B',
                'forecast': 'N/A',
                'previous': '17.5B'
            },
            {
                'title': 'BusinessNZ Manufacturing Index',
                'date': 'Thu, Jan 15',
                'time': '21:30 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '56.1',
                'forecast': 'N/A',
                'previous': '51.4'
            },
            {
                'title': 'FPI m/m',
                'date': 'Thu, Jan 15',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '-0.3%',
                'forecast': 'N/A',
                'previous': '-0.4%'
            },

            # FRIDAY, JANUARY 16
            {
                'title': 'German Final CPI m/m',
                'date': 'Fri, Jan 16',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.0%',
                'forecast': '0.0%',
                'previous': '0.0%'
            },
            {
                'title': 'Housing Starts',
                'date': 'Fri, Jan 16',
                'time': '13:15 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '282K',
                'forecast': '255K',
                'previous': '254K'
            },
            {
                'title': 'Foreign Securities Purchases',
                'date': 'Fri, Jan 16',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '16.33B',
                'forecast': 'N/A',
                'previous': '46.62B'
            },
            {
                'title': 'Capacity Utilization Rate',
                'date': 'Fri, Jan 16',
                'time': '14:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '76.3%',
                'forecast': '76.1%',
                'previous': '76.0%'
            },
            {
                'title': 'Industrial Production m/m',
                'date': 'Fri, Jan 16',
                'time': '14:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'CB Leading Index m/m',
                'date': 'Fri, Jan 16',
                'time': '14:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': 'N/A',
                'previous': '0.0%'
            },
            {
                'title': 'NAHB Housing Market Index',
                'date': 'Fri, Jan 16',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '37',
                'forecast': 'N/A',
                'previous': '39'
            },
            {
                'title': 'CB Leading Index m/m',
                'date': 'Fri, Jan 16',
                'time': '15:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': 'N/A',
                'previous': '0.3%'
            },
            {
                'title': 'FOMC Member Jefferson Speaks',
                'date': 'Fri, Jan 16',
                'time': '20:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # SATURDAY, JANUARY 17
            {
                'title': 'French Final CPI m/m',
                'date': 'Sat, Jan 17',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.0%',
                'forecast': '0.0%',
                'previous': '0.0%'
            },

            # SUNDAY, JANUARY 18
            
            {
                'title': 'Core Machinery Orders m/m',
                'date': 'Sun, Jan 18',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-11.0&',
                'forecast': '-5.2%',
                'previous': '7.0%'
            },
            {
                'title': 'MI Inflation Gauge m/m',
                'date': 'Sun, Jan 18',
                'time': '00:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '1.0%',
                'forecast': 'N/A',
                'previous': '0.3%'
            },
            {
                'title': 'Rightmove HPI m/m',
                'date': 'Sun, Jan 18',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '2.8%',
                'forecast': 'N/A',
                'previous': '-1.8%'
            },
            {
                'title': 'New Home Prices m/m',
                'date': 'Sun, Jan 18',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '-0.37%',
                'forecast': 'N/A',
                'previous': '-0.39%'
            },
            {
                'title': 'Fixed Asset Investment ytd/y',
                'date': 'Sun, Jan 18',
                'time': '02:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '-3.8%',
                'forecast': '-3.1%',
                'previous': '-2.6%'
            },
            {
                'title': 'GDP q/y',
                'date': 'Sun, Jan 18',
                'time': '02:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '4.5%',
                'forecast': '4.5%',
                'previous': '4.8%'
            },
            {
                'title': 'Industrial Production y/y',
                'date': 'Sun, Jan 18',
                'time': '02:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '5.2%',
                'forecast': '5.1%',
                'previous': '4.8%'
            },
            {
                'title': 'NBS Press Conference',
                'date': 'Sun, Jan 18',
                'time': '02:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Retail Sales y/y',
                'date': 'Sun, Jan 18',
                'time': '02:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '0.9%',
                'forecast': '1.1%',
                'previous': '1.3%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Sun, Jan 18',
                'time': '02:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '5.1%',
                'forecast': '5.2%',
                'previous': '5.1%'
            },
            {
                'title': 'Revised Industrial Production m/m',
                'date': 'Sun, Jan 18',
                'time': '04:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-2.75',
                'forecast': '-2.6%',
                'previous': '-2.6%'
            },
            {
                'title': 'Tertiary Industry Activity m/m',
                'date': 'Sun, Jan 18',
                'time': '04:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': '0.0%',
                'previous': '0.9%'
            },

            # MONDAY, JANUARY 19
            {
                'title': 'Foreign Direct Investment ytd/y',
                'date': 'Mon, Jan 19',
                'time': '07:02 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '-7.5%'
            },
            {
                'title': 'WEF Annual Meetings',
                'date': 'Mon, Jan 19',
                'time': '09:15 UTC',
                'currency': 'All',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Final Core CPI y/y',
                'date': 'Mon, Jan 19',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '2.3%',
                'forecast': '2.3%',
                'previous': '2.3%'
            },
            {
                'title': 'Final CPI y/y',
                'date': 'Mon, Jan 19',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '1.9%',
                'forecast': '2.0%',
                'previous': '2.0%'
            },
            {
                'title': 'Eurogroup Meetings',
                'date': 'Mon, Jan 19',
                'time': '10:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CPI m/m',
                'date': 'Mon, Jan 19',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '-0.2%',
                'forecast': '-0.4%',
                'previous': '0.1%'
            },
            {
                'title': 'Median CPI y/y',
                'date': 'Mon, Jan 19',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '2.5%',
                'forecast': '2.7%',
                'previous': '2.8%'
            },
            {
                'title': 'Trimmed CPI y/y',
                'date': 'Mon, Jan 19',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '2.7%',
                'forecast': '2.7%',
                'previous': '2.9%'
            },
            {
                'title': 'Common CPI y/y',
                'date': 'Mon, Jan 19',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '2.85',
                'forecast': '2.8%',
                'previous': '2.8%'
            },
            {
                'title': 'Core CPI m/m',
                'date': 'Mon, Jan 19',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-0.4%',
                'forecast': 'N/A',
                'previous': '-0.1%'
            },
            {
                'title': 'BOC Business Outlook Survey',
                'date': 'Mon, Jan 19',
                'time': '15:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BusinessNZ Services Index',
                'date': 'Mon, Jan 19',
                'time': '21:30 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '51.5',
                'forecast': 'N/A',
                'previous': '46.9'
            },
            {
                'title': '1-y Loan Prime Rate',
                'date': 'Mon, Jan 19',
                'time': '01:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '3.00%',
                'forecast': '3.00%',
                'previous': '3.00%'
            },
            {
                'title': '5-y Loan Prime Rate',
                'date': 'Mon, Jan 19',
                'time': '01:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '3.5%',
                'forecast': '3.50%',
                'previous': '3.50%'
            },

            # TUESDAY, JANUARY 20
            {
                'title': 'German PPI m/m',
                'date': 'Tue, Jan 20',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': '-0.1%',
                'previous': '0.0%'
            },
            {
                'title': 'Claimant Count Change',
                'date': 'Tue, Jan 20',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '17.9K',
                'forecast': '18.8K',
                'previous': '20.1K'
            },
            {
                'title': 'Average Earnings Index 3m/y',
                'date': 'Tue, Jan 20',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': '4.7%',
                'forecast': '4.6%',
                'previous': '4.7%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Tue, Jan 20',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '5.1%',
                'forecast': '5.0%',
                'previous': '5.1%'
            },
            {
                'title': 'PPI m/m',
                'date': 'Tue, Jan 20',
                'time': '07:30 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': '0.2%',
                'previous': '-0.5%'
            },
            {
                'title': 'Current Account',
                'date': 'Tue, Jan 20',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '8.6B',
                'forecast': '20.3B',
                'previous': '25.7B'
            },
            {
                'title': 'WEF Annual Meetings',
                'date': 'Tue, Jan 20',
                'time': '09:15 UTC',
                'currency': 'All',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Tue, Jan 20',
                'time': '09:45 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'German ZEW Economic Sentiment',
                'date': 'Tue, Jan 20',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '59.6',
                'forecast': '49.9',
                'previous': '45.8'
            },
            {
                'title': 'ZEW Economic Sentiment',
                'date': 'Tue, Jan 20',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '40.8',
                'forecast': '35.6',
                'previous': '33.7'
            },
            {
                'title': 'ECOFIN Meetings',
                'date': 'Tue, Jan 20',
                'time': '10:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Jan 20',
                'time': '13:20 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '8.0K',
                'forecast': 'N/A',
                'previous': '11.3K'
            },
            {
                'title': 'GDT Price Index',
                'date': 'Tue, Jan 20',
                'time': '15:50 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '1.5%',
                'forecast': 'N/A',
                'previous': '6.3%'
            },
            {
                'title': 'SNB Chairman Schlegel Speaks',
                'date': 'Tue, Jan 20',
                'time': '16:30 UTC',
                'currency': 'CHF',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Tue, Jan 20',
                'time': '16:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'MI Leading Index m/m',
                'date': 'Tue, Jan 20',
                'time': '23:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': 'N/A',
                'previous': '0.0%'
            },

            # WEDNESDAY, JANUARY 21
            {
                'title': 'CPI y/y',
                'date': 'Wed, Jan 21',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '3.4%',
                'forecast': '3.3%',
                'previous': '3.2%'
            },
            {
                'title': 'Core CPI y/y',
                'date': 'Wed, Jan 21',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '3.2%',
                'forecast': '3.3%',
                'previous': '3.2%'
            },
            {
                'title': 'PPI Input m/m',
                'date': 'Wed, Jan 21',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': '-0.1%',
                'previous': '0.5%'
            },
            {
                'title': 'PPI Output m/m',
                'date': 'Wed, Jan 21',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.0%',
                'forecast': '0.1%',
                'previous': '0.1%'
            },
            {
                'title': 'RPI y/y',
                'date': 'Wed, Jan 21',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '4.2%',
                'forecast': '4.1%',
                'previous': '3.8%'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Wed, Jan 21',
                'time': '07:30 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'WEF Annual Meetings',
                'date': 'Wed, Jan 21',
                'time': '09:15 UTC',
                'currency': 'All',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'HPI y/y',
                'date': 'Wed, Jan 21',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '2.5%',
                'forecast': '1.8%',
                'previous': '1.7%'
            },
            {
                'title': 'German 30-y Bond Auction',
                'date': 'Wed, Jan 21',
                'time': '10:34 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.49|2.4',
                'forecast': 'N/A',
                'previous': '3.45|2.1'
            },
            {
                'title': 'CBI Industrial Order Expectations',
                'date': 'Wed, Jan 21',
                'time': '11:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-30',
                'forecast': '-33',
                'previous': '-32'
            },
            {
                'title': 'IPPI m/m',
                'date': 'Wed, Jan 21',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-0.6%',
                'forecast': '0.2%',
                'previous': '0.9%'
            },
            {
                'title': 'RMPI m/m',
                'date': 'Wed, Jan 21',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '0.5%',
                'forecast': '-0.9%',
                'previous': '0.3%'
            },
            {
                'title': 'President Trump Speaks',
                'date': 'Wed, Jan 21',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Pending Home Sales m/m',
                'date': 'Wed, Jan 21',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '-2.6%',
                'previous': '3.3%'
            },
            {
                'title': 'Construction Spending m/m',
                'date': 'Wed, Jan 21',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-0.6%',
                'forecast': '0.1%',
                'previous': 'N/A'
            },
            {
                'title': 'Construction Spending m/m',
                'date': 'Wed, Jan 21',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.5%',
                'forecast': 'N/A',
                'previous': '0.2%'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Wed, Jan 21',
                'time': '16:45 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Wed, Jan 21',
                'time': '18:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Wed, Jan 21',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Visitor Arrivals m/m',
                'date': 'Wed, Jan 21',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '0.8%',
                'forecast': 'N/A',
                'previous': '0.6%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Wed, Jan 21',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-0.21T',
                'forecast': '-0.04T',
                'previous': '0.01T'
            },
            {
                'title': 'Employment Change',
                'date': 'Wed, Jan 21',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '65.2K',
                'forecast': '26.5K',
                'previous': '-28.7K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Wed, Jan 21',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '4.1%',
                'forecast': '4.4%',
                'previous': '4.3%'
            },

            # THURSDAY, JANUARY 22
            {
                'title': 'Public Sector Net Borrowing',
                'date': 'Thu, Jan 22',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '11.6B',
                'forecast': '13.5B',
                'previous': '11.7B'
            },
            {
                'title': 'WEF Annual Meetings',
                'date': 'Thu, Jan 22',
                'time': '09:15 UTC',
                'currency': 'All',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'German Buba Monthly Report',
                'date': 'Thu, Jan 22',
                'time': '11:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CBI Realized Sales',
                'date': 'Thu, Jan 22',
                'time': '11:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-17',
                'forecast': '-35',
                'previous': '-44'
            },
            {
                'title': 'ECB Monetary Policy Meeting Accounts',
                'date': 'Thu, Jan 22',
                'time': '12:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'NHPI m/m',
                'date': 'Thu, Jan 22',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': '-0.2%',
                'previous': '0.0%'
            },
            {
                'title': 'Core PCE Price Index m/m',
                'date': 'Thu, Jan 22',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': 'N/A'
            },
            {
                'title': 'Final GDP q/q',
                'date': 'Thu, Jan 22',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '4.4%',
                'forecast': '4.3%',
                'previous': '4.3%'
            },
            {
                'title': 'Final GDP Price Index q/q',
                'date': 'Thu, Jan 22',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '3.8%',
                'forecast': '3.8%',
                'previous': '3.8%'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Jan 22',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '200K',
                'forecast': '203K',
                'previous': '198K'
            },
            {
                'title': 'Personal Income m/m',
                'date': 'Thu, Jan 22',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.4%',
                'previous': 'N/A'
            },
            {
                'title': 'Personal Spending m/m',
                'date': 'Thu, Jan 22',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.5%',
                'forecast': '0.5%',
                'previous': 'N/A'
            },
            {
                'title': 'Core PCE Price Index m/m',
                'date': 'Thu, Jan 22',
                'time': '13:40 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '0.2%'
            },
            {
                'title': 'Personal Income m/m',
                'date': 'Thu, Jan 22',
                'time': '13:40 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '0.4%'
            },
            {
                'title': 'Personal Spending m/m',
                'date': 'Thu, Jan 22',
                'time': '13:40 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '0.3%'
            },
            {
                'title': 'Consumer Confidence',
                'date': 'Thu, Jan 22',
                'time': '15:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-12',
                'forecast': '-13',
                'previous': '-15'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Jan 22',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-120B',
                'forecast': 'N/A',
                'previous': '-71B'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Thu, Jan 22',
                'time': '17:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '3.6M',
                'forecast': 'N/A',
                'previous': '3.4M'
            },
            {
                'title': 'CPI q/q',
                'date': 'Thu, Jan 22',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': '0.6%',
                'forecast': '0.5%',
                'previous': '1.0%'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Thu, Jan 22',
                'time': '22:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '52.4',
                'forecast': 'N/A',
                'previous': '52.2'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Thu, Jan 22',
                'time': '22:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '56.0',
                'forecast': 'N/A',
                'previous': '51.0'
            },
            {
                'title': 'National Core CPI y/y',
                'date': 'Thu, Jan 22',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.4%',
                'forecast': '2.4%',
                'previous': '3.0%'
            },
            {
                'title': 'GfK Consumer Confidence',
                'date': 'Thu, Jan 22',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-16',
                'forecast': '-16',
                'previous': '-17'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Fri, Jan 23',
                'time': '00:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '51.5',
                'forecast': '50.1',
                'previous': '49.7'
            },
            {
                'title': 'BOJ Policy Rate',
                'date': 'Fri, Jan 23',
                'time': '03:30 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': '<0.75%',
                'forecast': '<0.75%',
                'previous': '<0.75%'
            },
            {
                'title': 'Monetary Policy Statement',
                'date': 'Fri, Jan 23',
                'time': '03:30 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOJ Outlook Report',
                'date': 'Fri, Jan 23',
                'time': '03:31 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # FRIDAY, JANUARY 23
            {
                'title': 'BOJ Press Conference',
                'date': 'Fri, Jan 23',
                'time': '06:30 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Fri, Jan 23',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '0.4%',
                'forecast': '0.0%',
                'previous': '-0.1%'
            },
            {
                'title': 'French Flash Manufacturing PMI',
                'date': 'Fri, Jan 23',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '51.0',
                'forecast': '50.4',
                'previous': '50.6'
            },
            {
                'title': 'French Flash Services PMI',
                'date': 'Fri, Jan 23',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '47.9',
                'forecast': '50.4',
                'previous': '50.2'
            },
            {
                'title': 'German Flash Manufacturing PMI',
                'date': 'Fri, Jan 23',
                'time': '08:30 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': '48.7',
                'forecast': '47.6',
                'previous': '47.7'
            },
            {
                'title': 'German Flash Services PMI',
                'date': 'Fri, Jan 23',
                'time': '08:30 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': '53.3',
                'forecast': '52.5',
                'previous': '52.6'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Fri, Jan 23',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '49.4',
                'forecast': '49.2',
                'previous': '49.2'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Fri, Jan 23',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '51.9',
                'forecast': '52.6',
                'previous': '52.6'
            },
            {
                'title': 'WEF Annual Meetings',
                'date': 'Fri, Jan 23',
                'time': '09:15 UTC',
                'currency': 'All',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Fri, Jan 23',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '51.6',
                'forecast': '50.6',
                'previous': '51.2'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Fri, Jan 23',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '54.3',
                'forecast': '51.7',
                'previous': '52.1'
            },
            {
                'title': 'MPC Member Greene Speaks',
                'date': 'Fri, Jan 23',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Fri, Jan 23',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Fri, Jan 23',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '1.7%',
                'forecast': '1.2%',
                'previous': '-0.6%'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Fri, Jan 23',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '1.3%',
                'forecast': '1.2%',
                'previous': '-0.2%'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Fri, Jan 23',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '51.9',
                'forecast': '52.1',
                'previous': '51.8'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Fri, Jan 23',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '52.5',
                'forecast': '52.8',
                'previous': '52.9'
            },
            {
                'title': 'Revised UoM Consumer Sentiment',
                'date': 'Fri, Jan 23',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '56.4',
                'forecast': '54.0',
                'previous': '54.0'
            },
            {
                'title': 'Revised UoM Inflation Expectations',
                'date': 'Fri, Jan 23',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '4.0%',
                'forecast': 'N/A',
                'previous': '4.2%'
            },

            # MONDAY, JANUARY 26
            
            {
                'title': 'German ifo Business Climate',
                'date': 'Mon, Jan 26',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '87.6',
                'forecast': '88.3',
                'previous': '87.6'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Mon, Jan 26',
                'time': '11:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Mon, Jan 26',
                'time': '13:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Core Durable Goods Orders m/m',
                'date': 'Mon, Jan 26',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '0.5%',
                'forecast': '0.3%',
                'previous': '0.1%'
            },
            {
                'title': 'Durable Goods Orders m/m',
                'date': 'Mon, Jan 26',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '5.3',
                'forecast': '3.1%',
                'previous': '-2.1%'
            },
            {
                'title': 'Belgian NBB Business Climate',
                'date': 'Mon, Jan 26',
                'time': '14:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-8.8',
                'forecast': '-10.2',
                'previous': '-11.9'
            },
            {
                'title': 'SPPI y/y',
                'date': 'Mon, Jan 26',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.6%',
                'forecast': '2.5%',
                'previous': '2.7%'
            },
            {
                'title': 'BRC Shop Price Index y/y',
                'date': 'Mon, Jan 26',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '1.5%',
                'forecast': '0.7%',
                'previous': '0.6%'
            },
            {
                'title': 'NAB Business Confidence',
                'date': 'Mon, Jan 26',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '3',
                'forecast': 'N/A',
                'previous': '1'
            },
            {
                'title': 'Credit Card Spending y/y',
                'date': 'Mon, Jan 26',
                'time': '02:00 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '-0.3%',
                'forecast': 'N/A',
                'previous': '4.7%'
            },

            # TUESDAY, JANUARY 27
            {
                'title': 'BOJ Core CPI y/y',
                'date': 'Tue, Jan 27',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '1.9%',
                'forecast': '2.0%',
                'previous': '2.2%'
            },
            {
                'title': 'Spanish Unemployment Rate',
                'date': 'Tue, Jan 27',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '9.9%',
                'forecast': '10.6%',
                'previous': '10.5%'
            },
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Jan 27',
                'time': '13:20 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '7.8K',
                'forecast': 'N/A',
                'previous': '8.0K'
            },
            {
                'title': 'President Trump Speaks',
                'date': 'Tue, Jan 27',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'HPI m/m',
                'date': 'Tue, Jan 27',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.6%',
                'forecast': '0.3%',
                'previous': '0.4%'
            },
            {
                'title': 'S&P/CS Composite-20 HPI y/y',
                'date': 'Tue, Jan 27',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.4%',
                'forecast': '1.2%',
                'previous': '1.3%'
            },
            {
                'title': 'CB Consumer Confidence',
                'date': 'Tue, Jan 27',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '84.5',
                'forecast': '90.1',
                'previous': '89.1'
            },
            {
                'title': 'Richmond Manufacturing Index',
                'date': 'Tue, Jan 27',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '-6',
                'forecast': '-5',
                'previous': '-7'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Tue, Jan 27',
                'time': '17:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Tue, Jan 27',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Monetary Policy Meeting Minutes',
                'date': 'Tue, Jan 27',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CPI m/m',
                'date': 'Tue, Jan 27',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '1.0%',
                'forecast': '0.7%',
                'previous': '0.0%'
            },
            {
                'title': 'CPI y/y',
                'date': 'Tue, Jan 27',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '3.8%',
                'forecast': '3.5%',
                'previous': '3.4%'
            },
            {
                'title': 'Trimmed Mean CPI m/m',
                'date': 'Tue, Jan 27',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '0.2%',
                'forecast': '0.4%',
                'previous': '0.3%'
            },

            # WEDNESDAY, JANUARY 28
            {
                'title': 'German GfK Consumer Climate',
                'date': 'Wed, Jan 28',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-24.1',
                'forecast': '-25.7',
                'previous': '-26.9'
            },
            {
                'title': 'UBS Economic Expectations',
                'date': 'Wed, Jan 28',
                'time': '09:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '-4.7',
                'forecast': 'N/A',
                'previous': '6.2'
            },
            {
                'title': 'German 10-y Bond Auction',
                'date': 'Wed, Jan 28',
                'time': '10:42 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '2.85|1.7',
                'forecast': 'N/A',
                'previous': '2.83|1.3'
            },
            {
                'title': 'CB Leading Index m/m',
                'date': 'Wed, Jan 28',
                'time': '14:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': 'N/A',
                'previous': '-0.3%'
            },
            {
                'title': 'BOC Monetary Policy Report',
                'date': 'Wed, Jan 28',
                'time': '14:45 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOC Rate Statement',
                'date': 'Wed, Jan 28',
                'time': '14:45 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Overnight Rate',
                'date': 'Wed, Jan 28',
                'time': '14:45 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '2.25%',
                'forecast': '2.25%',
                'previous': '2.25%'
            },
            {
                'title': 'BOC Press Conference',
                'date': 'Wed, Jan 28',
                'time': '15:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Wed, Jan 28',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-2.3M',
                'forecast': 'N/A',
                'previous': '3.6M'
            },
            {
                'title': 'Federal Funds Rate',
                'date': 'Wed, Jan 28',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '3.75%',
                'forecast': '3.75%',
                'previous': '3.75%'
            },
            {
                'title': 'FOMC Statement',
                'date': 'Wed, Jan 28',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Press Conference',
                'date': 'Wed, Jan 28',
                'time': '19:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Trade Balance',
                'date': 'Wed, Jan 28',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '52M',
                'forecast': '40M',
                'previous': '-335M'
            },
            {
                'title': 'ANZ Business Confidence',
                'date': 'Wed, Jan 28',
                'time': '00:00 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '64.1',
                'forecast': 'N/A',
                'previous': '73.6'
            },
            {
                'title': 'Import Prices q/q',
                'date': 'Wed, Jan 28',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '0.9%',
                'forecast': '-0.2%',
                'previous': '-0.4%'
            },

            # THURSDAY, JANUARY 29
            {
                'title': 'Consumer Confidence',
                'date': 'Thu, Jan 29',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '37.9',
                'forecast': '37.1',
                'previous': '37.2'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Jan 29',
                'time': '07:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '4.85B',
                'previous': '3.84B'
            },
            {
                'title': 'M3 Money Supply y/y',
                'date': 'Thu, Jan 29',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '2.8%',
                'forecast': '3.0%',
                'previous': '3.0%'
            },
            {
                'title': 'Private Loans y/y',
                'date': 'Thu, Jan 29',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.0%',
                'forecast': '2.9%',
                'previous': '2.9%'
            },
            {
                'title': 'Italian 10-y Bond Auction',
                'date': 'Thu, Jan 29',
                'time': '10:33 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Jan 29',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-2.2B',
                'forecast': '-0.7B',
                'previous': '-0.4B'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Jan 29',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '209K',
                'forecast': '202K',
                'previous': '200K'
            },
            {
                'title': 'Revised Nonfarm Productivity q/q',
                'date': 'Thu, Jan 29',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '4.9%',
                'forecast': '4.9%',
                'previous': '4.9%'
            },
            {
                'title': 'Revised Unit Labor Costs q/q',
                'date': 'Thu, Jan 29',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-1.9%',
                'forecast': '-1.9%',
                'previous': '-1.9%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Jan 29',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-56.8B',
                'forecast': '-44.5B',
                'previous': '-29.4B'
            },
            {
                'title': 'Factory Orders m/m',
                'date': 'Thu, Jan 29',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '2.7%',
                'forecast': '0.5%',
                'previous': '-1.3%'
            },
            {
                'title': 'Final Wholesale Inventories m/m',
                'date': 'Thu, Jan 29',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Jan 29',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-242B',
                'forecast': '-237B',
                'previous': '-120B'
            },
            {
                'title': 'Tokyo Core CPI y/y',
                'date': 'Thu, Jan 29',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'medium',
                'actual': '2.0%',
                'forecast': '2.2%',
                'previous': '2.3%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Thu, Jan 29',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.6%',
                'forecast': '2.6%',
                'previous': '2.6%'
            },
            {
                'title': 'Prelim Industrial Production m/m',
                'date': 'Thu, Jan 29',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': '-0.4%',
                'previous': '-2.6%'
            },
            {
                'title': 'Retail Sales y/y',
                'date': 'Thu, Jan 29',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-0.9%',
                'forecast': '0.7%',
                'previous': '1.0%'
            },
            {
                'title': 'PPI q/q',
                'date': 'Thu, Jan 29',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '0.8%',
                'forecast': '1.1%',
                'previous': '1.0%'
            },
            {
                'title': 'Private Sector Credit m/m',
                'date': 'Thu, Jan 29',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '0.8%',
                'forecast': '0.6%',
                'previous': '0.6%'
            },

            # FRIDAY, JANUARY 30
            {
                'title': 'Housing Starts y/y',
                'date': 'Fri, Jan 30',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-1.3%',
                'forecast': '-4.5%',
                'previous': '-8.5%'
            },
            {
                'title': 'French Consumer Spending m/m',
                'date': 'Fri, Jan 30',
                'time': '06:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.6%',
                'forecast': '-0.4%',
                'previous': '-0.3%'
            },
            {
                'title': 'French Flash GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '06:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.5%'
            },
            {
                'title': 'German Import Prices m/m',
                'date': 'Fri, Jan 30',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': '-0.4%',
                'previous': '0.5%'
            },
            {
                'title': 'German Prelim CPI m/m',
                'date': 'Fri, Jan 30',
                'time': '07:29 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '0.1%',
                'forecast': '0.0%',
                'previous': '0.0%'
            },
            {
                'title': 'French Prelim Private Payrolls q/q',
                'date': 'Fri, Jan 30',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': '0.1%',
                'previous': '-0.1%'
            },
            {
                'title': 'KOF Economic Barometer',
                'date': 'Fri, Jan 30',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '102.5',
                'forecast': '103.2',
                'previous': '103.4'
            },
            {
                'title': 'Spanish Flash CPI y/y',
                'date': 'Fri, Jan 30',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '2.4%',
                'forecast': '2.4%',
                'previous': '2.9%'
            },
            {
                'title': 'Spanish Flash GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.8%',
                'forecast': '0.6%',
                'previous': '0.6%'
            },
            {
                'title': 'German Unemployment Change',
                'date': 'Fri, Jan 30',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0K',
                'forecast': '5K',
                'previous': '3K'
            },
            {
                'title': 'German Prelim GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '0.3%',
                'forecast': '0.2%',
                'previous': '0.0%'
            },
            {
                'title': 'Italian Prelim GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.2%',
                'previous': '0.0%'
            },
            {
                'title': 'M4 Money Supply m/m',
                'date': 'Fri, Jan 30',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.8%'
            },
            {
                'title': 'Mortgage Approvals',
                'date': 'Fri, Jan 30',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '61K',
                'forecast': '65K',
                'previous': '65K'
            },
            {
                'title': 'Net Lending to Individuals m/m',
                'date': 'Fri, Jan 30',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '6.1B',
                'forecast': '6.1B',
                'previous': '6.6B'
            },
            {
                'title': 'Italian Monthly Unemployment Rate',
                'date': 'Fri, Jan 30',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '5.6%',
                'forecast': '5.8%',
                'previous': '5.6%'
            },
            {
                'title': 'Prelim Flash GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.2%',
                'previous': '0.3%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Jan 30',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '6.2%',
                'forecast': '6.3%',
                'previous': '6.3%'
            },
            {
                'title': 'GDP m/m',
                'date': 'Fri, Jan 30',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '0.0%',
                'forecast': '0.1%',
                'previous': '-0.3%'
            },
            {
                'title': 'Core PPI m/m',
                'date': 'Fri, Jan 30',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.7%',
                'forecast': '0.3%',
                'previous': '0.0%'
            },
            {
                'title': 'PPI m/m',
                'date': 'Fri, Jan 30',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.5%',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Chicago PMI',
                'date': 'Fri, Jan 30',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '54.0',
                'forecast': '43.3',
                'previous': '43.5'
            },
            {
                'title': 'FOMC Member Musalem Speaks',
                'date': 'Fri, Jan 30',
                'time': '17:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Manufacturing PMI',
                'date': 'Fri, Jan 30',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': '49.3',
                'forecast': '50.2',
                'previous': '50.1'
            },
            {
                'title': 'Non-Manufacturing PMI',
                'date': 'Fri, Jan 30',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '49.4',
                'forecast': '50.8',
                'previous': '50.2'
            },


            # SUNDAY, FEBRUARY 01
            {
                'title': 'BOJ Summary of Opinions',
                'date': 'Sun, Feb 01',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'MI Inflation Gauge m/m',
                'date': 'Sun, Feb 01',
                'time': '00:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '1.0%'
            },
            {
                'title': 'ANZ Job Advertisements m/m',
                'date': 'Sun, Feb 01',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '-0.5%'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Sun, Feb 01',
                'time': '00:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '51.5',
                'previous': '51.5'
            },
            {
                'title': 'RatingDog Manufacturing PMI',
                'date': 'Sun, Feb 01',
                'time': '01:45 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '50.1',
                'previous': '50.1'
            },

            # MONDAY, FEBRUARY 02
            {
                'title': 'Commodity Prices y/y',
                'date': 'Mon, Feb 02',
                'time': '05:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '2.6%',
                'forecast': 'N/A',
                'previous': '-3.2%'
            },
            {
                'title': 'German Retail Sales m/m',
                'date': 'Mon, Feb 02',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '-0.1%',
                'previous': '-0.6%'
            },
            {
                'title': 'Nationwide HPI m/m',
                'date': 'Mon, Feb 02',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '-0.4%'
            },
            {
                'title': 'Retail Sales y/y',
                'date': 'Mon, Feb 02',
                'time': '07:30 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '2.9%',
                'forecast': '2.5%',
                'previous': '2.3%'
            },
            {
                'title': 'Spanish Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '49.2',
                'forecast': '49.9',
                'previous': '49.6'
            },
            {
                'title': 'Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '08:30 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '48.8',
                'forecast': '47.2',
                'previous': '45.8'
            },
            {
                'title': 'Italian Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '08:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '48.1',
                'forecast': '48.5',
                'previous': '47.9'
            },
            {
                'title': 'French Final Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '08:50 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '51.2',
                'forecast': '51.0',
                'previous': '51.0'
            },
            {
                'title': 'German Final Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '49.1',
                'forecast': '48.7',
                'previous': '48.7'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '49.5',
                'forecast': '49.4',
                'previous': '49.4'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '51.8',
                'forecast': '51.6',
                'previous': '51.6'
            },
            {
                'title': 'MPC Member Breeden Speaks',
                'date': 'Mon, Feb 02',
                'time': '11:45 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '14:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '50.4',
                'forecast': 'N/A',
                'previous': '48.6'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '52.4',
                'forecast': '51.9',
                'previous': '51.9'
            },
            {
                'title': 'ISM Manufacturing PMI',
                'date': 'Mon, Feb 02',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '52.6',
                'forecast': '48.5',
                'previous': '47.9'
            },
            {
                'title': 'ISM Manufacturing Prices',
                'date': 'Mon, Feb 02',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '59.0',
                'forecast': '59.3',
                'previous': '58.5'
            },
            {
                'title': 'FOMC Member Bostic Speaks',
                'date': 'Mon, Feb 02',
                'time': '17:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Loan Officer Survey',
                'date': 'Mon, Feb 02',
                'time': '19:03 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Building Consents m/m',
                'date': 'Mon, Feb 02',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '-4.6%	',
                'forecast': 'N/A',
                'previous': '2.7%'
            },
            {
                'title': 'Monetary Base y/y',
                'date': 'Mon, Feb 02',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-9.5%',
                'forecast': '-10.2%',
                'previous': '-9.8%'
            },
            {
                'title': 'Building Approvals m/m',
                'date': 'Mon, Feb 02',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-14.9%',
                'forecast': '-6.4%',
                'previous': '15.2%'
            },
            {
                'title': 'Cash Rate',
                'date': 'Tue, Feb 03',
                'time': '03:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '3.85%',
                'forecast': '3.85%',
                'previous': '3.60%'
            },
            {
                'title': 'RBA Monetary Policy Statement',
                'date': 'Tue, Feb 03',
                'time': '03:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RBA Rate Statement',
                'date': 'Tue, Feb 03',
                'time': '03:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': '10-y Bond Auction',
                'date': 'Mon, Feb 02',
                'time': '03:35 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.25|3.0',
                'forecast': 'N/A',
                'previous': '2.10|3.3'
            },
            {
                'title': 'RBA Press Conference',
                'date': 'Tue, Feb 03',
                'time': '04:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # TUESDAY, FEBRUARY 03
            {
                'title': 'French Gov Budget Balance',
                'date': 'Tue, Feb 03',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-124.7B',
                'forecast': 'N/A',
                'previous': '-155.4B'
            },
            {
                'title': 'French Prelim CPI m/m',
                'date': 'Tue, Feb 03',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.3%',
                'forecast': '-0.1%',
                'previous': '0.1%'
            },
            {
                'title': 'Spanish Unemployment Change',
                'date': 'Tue, Feb 03',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '30.4K',
                'forecast': '10.5K',
                'previous': '-16.3K'
            },
            {
                'title': '10-y Bond Auction',
                'date': 'Tue, Feb 03',
                'time': '10:33 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '4.59|3.6',
                'forecast': 'N/A',
                'previous': '4.46|3.3'
            },
            {
                'title': 'FOMC Member Barkin Speaks',
                'date': 'Tue, Feb 03',
                'time': '13:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Bowman Speaks',
                'date': 'Tue, Feb 03',
                'time': '14:40 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RCM/TIPP Economic Optimism',
                'date': 'Tue, Feb 03',
                'time': '15:10 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '48.8',
                'forecast': '47.9',
                'previous': '47.2'
            },
            {
                'title': 'Wards Total Vehicle Sales',
                'date': 'Tue, Feb 03',
                'time': '15:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '14.9M',
                'forecast': '15.4M',
                'previous': '16.0M'
            },
            {
                'title': 'GDT Price Index',
                'date': 'Tue, Feb 03',
                'time': '15:50 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '6.7%',
                'forecast': 'N/A',
                'previous': '1.5%'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Tue, Feb 03',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Employment Change q/q',
                'date': 'Tue, Feb 03',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': '0.5%',
                'forecast': '0.3%',
                'previous': '0.0%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Tue, Feb 03',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': '5.4%',
                'forecast': '5.3%',
                'previous': '5.3%'
            },
            {
                'title': 'Labor Cost Index q/q',
                'date': 'Tue, Feb 03',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '0.4%',
                'forecast': '0.5%',
                'previous': '0.5%'
            },
            {
                'title': 'ANZ Commodity Prices m/m',
                'date': 'Tue, Feb 03',
                'time': '00:00 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '2.0%',
                'forecast': 'N/A',
                'previous': '-2.1%'
            },
            {
                'title': 'RatingDog Services PMI',
                'date': 'Tue, Feb 03',
                'time': '01:45 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '52.3',
                'forecast': '51.9',
                'previous': '52.0'
            },

            # WEDNESDAY, FEBRUARY 04
            {
                'title': 'RBA Assist Gov Jones Speaks',
                'date': 'Wed, Feb 04',
                'time': '05:10 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Spanish Services PMI',
                'date': 'Wed, Feb 04',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '53.5',
                'forecast': '57.0',
                'previous': '57.1'
            },
            
            {
                'title': 'Italian Services PMI',
                'date': 'Wed, Feb 04',
                'time': '08:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '52.9',
                'forecast': '51.6',
                'previous': '51.5'
            },
            {
                'title': 'French Final Services PMI',
                'date': 'Wed, Feb 04',
                'time': '08:50 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '48.4',
                'forecast': '48.0',
                'previous': '47.9'
            },
            {
                'title': 'German Final Services PMI',
                'date': 'Wed, Feb 04',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '52.4',
                'forecast': '53.3',
                'previous': '53.3'
            },
            {
                'title': 'Final Services PMI',
                'date': 'Wed, Feb 04',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '51.6',
                'forecast': '51.9',
                'previous': '51.9'
            },
            {
                'title': 'Final Services PMI',
                'date': 'Wed, Feb 04',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '54.0',
                'forecast': '54.1',
                'previous': '54.3'
            },
            {
                'title': 'Core CPI Flash Estimate y/y',
                'date': 'Wed, Feb 04',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '2.2%',
                'forecast': '2.2%',
                'previous': '2.3%'
            },
            {
                'title': 'CPI Flash Estimate y/y',
                'date': 'Wed, Feb 04',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '1.7%',
                'forecast': '1.8%',
                'previous': '1.9%'
            },
            {
                'title': 'PPI m/m',
                'date': 'Wed, Feb 04',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.3%	',
                'forecast': '-0.2%',
                'previous': '0.7%'
            },
            {
                'title': 'Italian Prelim CPI m/m',
                'date': 'Wed, Feb 04',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.4%',
                'forecast': '0.3%',
                'previous': '0.2%'
            },
            {
                'title': 'ADP Non-Farm Employment Change',
                'date': 'Wed, Feb 04',
                'time': '13:15 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '22K',
                'forecast': '48K',
                'previous': '37K'
            },
            {
                'title': 'Final Services PMI',
                'date': 'Wed, Feb 04',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '52.7',
                'forecast': '52.5',
                'previous': '52.5'
            },
            {
                'title': 'ISM Services PMI',
                'date': 'Wed, Feb 04',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '53.8',
                'forecast': '53.6',
                'previous': '54.4'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Wed, Feb 04',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-3.5M',
                'forecast': 'N/A',
                'previous': '-2.3M'
            },
            {
                'title': 'FOMC Member Cook Speaks',
                'date': 'Wed, Feb 04',
                'time': '23:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Goods Trade Balance',
                'date': 'Wed, Feb 04',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '3.37B',
                'forecast': '3.45B',
                'previous': '2.94B'
            },
            
            {
                'title': '30-y Bond Auction',
                'date': 'Wed, Feb 04',
                'time': '03:35 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.62|3.6',
                'forecast': 'N/A',
                'previous': '3.45|3.1'
            },

            # THURSDAY, FEBRUARY 05
            {
                'title': 'German Factory Orders m/m',
                'date': 'Thu, Feb 05',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '7.8%',
                'forecast': '-1.3%',
                'previous': '5.6%'
            },
            {
                'title': 'French Industrial Production m/m',
                'date': 'Thu, Feb 05',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.7%',
                'forecast': '0.1%',
                'previous': '-0.1%'
            },
            {
                'title': 'Italian Retail Sales m/m',
                'date': 'Thu, Feb 05',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.8%',
                'forecast': '0.4%',
                'previous': '0.5%'
            },
            {
                'title': 'Construction PMI',
                'date': 'Thu, Feb 05',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '46.4',
                'forecast': '42.0',
                'previous': '40.1'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Thu, Feb 05',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.5%',
                'forecast': '-0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Spanish 10-y Bond Auction',
                'date': 'Thu, Feb 05',
                'time': '10:03 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.22|2.4',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'French 10-y Bond Auction',
                'date': 'Thu, Feb 05',
                'time': '10:18 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.45|2.4',
                'forecast': 'N/A',
                'previous': '3.53|2.0'
            },
            {
                'title': 'BOE Monetary Policy Report',
                'date': 'Thu, Feb 05',
                'time': '12:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Monetary Policy Summary',
                'date': 'Thu, Feb 05',
                'time': '12:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'MPC Official Bank Rate Votes',
                'date': 'Thu, Feb 05',
                'time': '12:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '0-4-5',
                'forecast': '0-2-7',
                'previous': '0-5-4'
            },
            {
                'title': 'Official Bank Rate',
                'date': 'Thu, Feb 05',
                'time': '12:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '3.75%',
                'forecast': '3.75%',
                'previous': '3.75%'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Thu, Feb 05',
                'time': '12:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Challenger Job Cuts y/y',
                'date': 'Thu, Feb 05',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '117.8%',
                'forecast': 'N/A',
                'previous': '-8.3%'
            },
            {
                'title': 'Main Refinancing Rate',
                'date': 'Thu, Feb 05',
                'time': '13:15 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': '2.15%',
                'forecast': '2.15%',
                'previous': '2.15%'
            },
            {
                'title': 'Monetary Policy Statement',
                'date': 'Thu, Feb 05',
                'time': '13:15 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Feb 05',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '231K',
                'forecast': '213K',
                'previous': '209K'
            },
            {
                'title': 'ECB Press Conference',
                'date': 'Thu, Feb 05',
                'time': '13:45 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'JOLTS Job Openings',
                'date': 'Thu, Feb 05',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '6.54M',
                'forecast': '7.25M',
                'previous': '7.15M'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Feb 05',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-360B',
                'forecast': 'N/A',
                'previous': '-242B'
            },
            {
                'title': 'FOMC Member Bostic Speaks',
                'date': 'Thu, Feb 05',
                'time': '15:50 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOC Gov Macklem Speaks',
                'date': 'Thu, Feb 05',
                'time': '17:25 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RBA Gov Bullock Speaks',
                'date': 'Thu, Feb 05',
                'time': '22:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Household Spending y/y',
                'date': 'Thu, Feb 05',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-2.6%',
                'forecast': '-0.3%',
                'previous': '2.9%'
            },

            # FRIDAY, FEBRUARY 06
            {
                'title': 'Leading Indicators',
                'date': 'Fri, Feb 06',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '110.2%',
                'forecast': '109.8%',
                'previous': '110.5%'
            },
            {
                'title': 'German Industrial Production m/m',
                'date': 'Fri, Feb 06',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-1.9%',
                'forecast': '-0.3%',
                'previous': '0.8%'
            },
            {
                'title': 'German Trade Balance',
                'date': 'Fri, Feb 06',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '17.1B',
                'forecast': '14.5B',
                'previous': '13.1B'
            },
            {
                'title': 'Halifax HPI m/m',
                'date': 'Fri, Feb 06',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.7%',
                'forecast': '0.2%',
                'previous': '-0.6%'
            },
            {
                'title': 'French Trade Balance',
                'date': 'Fri, Feb 06',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-4.8B',
                'forecast': '-4.1B',
                'previous': '-4.2B'
            },
            {
                'title': 'Foreign Currency Reserves',
                'date': 'Fri, Feb 06',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '712B',
                'forecast': 'N/A',
                'previous': '725B'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Feb 06',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '2.9%',
                'forecast': '3.0%',
                'previous': '3.0%'
            },
            {
                'title': 'MPC Member Pill Speaks',
                'date': 'Fri, Feb 06',
                'time': '12:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Employment Change',
                'date': 'Fri, Feb 06',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '-24.8K',
                'forecast': '7.2K',
                'previous': '8.2K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Feb 06',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '6.5%',
                'forecast': '6.8%',
                'previous': '6.8%'
            },
            {
                'title': 'Ivey PMI',
                'date': 'Fri, Feb 06',
                'time': '15:00 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '50.9',
                'forecast': '49.7',
                'previous': '51.9'
            },
            {
                'title': 'Prelim UoM Consumer Sentiment',
                'date': 'Fri, Feb 06',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '57.3',
                'forecast': '55.4',
                'previous': '56.4'
            },
            {
                'title': 'Prelim UoM Inflation Expectations',
                'date': 'Fri, Feb 06',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '3.5%',
                'forecast': 'N/A',
                'previous': '4.0%'
            },
            {
                'title': 'FOMC Member Jefferson Speaks',
                'date': 'Fri, Feb 06',
                'time': '17:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Consumer Credit m/m',
                'date': 'Fri, Feb 06',
                'time': '20:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '24.0B',
                'forecast': '8.5B',
                'previous': '4.7B'
            },

            # SUNDAY, FEBRUARY 08

            {
                'title': 'Lower House Elections',
                'date': 'Sun, Feb 08',
                'time': '06:00 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Sun, Feb 08',
                'time': '06:40 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Average Cash Earnings y/y',
                'date': 'Sun, Feb 08',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.4%',
                'forecast': '3.0%',
                'previous': '1.7%'
            },
            {
                'title': 'Bank Lending y/y',
                'date': 'Sun, Feb 08',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '4.5%',
                'forecast': '4.5%',
                'previous': '4.3%'
            },
            {
                'title': 'Current Account',
                'date': 'Sun, Feb 08',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.70T',
                'forecast': '2.95T',
                'previous': '3.14T'
            },
            {
                'title': 'Household Spending m/m',
                'date': 'Sun, Feb 08',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-0.4%',
                'forecast': '0.2%',
                'previous': '1.0%'
            },

            # MONDAY, FEBRUARY 09
            {
                'title': 'Economy Watchers Sentiment',
                'date': 'Mon, Feb 09',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '47.6',
                'forecast': '49.1',
                'previous': '48.6'
            },
            {
                'title': 'SECO Consumer Climate',
                'date': 'Mon, Feb 09',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '-30',
                'forecast': '-30',
                'previous': '-31'
            },
            
            {
                'title': 'Sentix Investor Confidence',
                'date': 'Mon, Feb 09',
                'time': '09:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-30',
                'forecast': '-0.2',
                'previous': '-1.8'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Mon, Feb 09',
                'time': '16:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Waller Speaks',
                'date': 'Mon, Feb 09',
                'time': '18:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'MPC Member Mann Speaks',
                'date': 'Mon, Feb 09',
                'time': '19:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Bostic Speaks',
                'date': 'Mon, Feb 09',
                'time': '20:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'MPC Member Mann Speaks',
                'date': 'Mon, Feb 09',
                'time': '22:15 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Westpac Consumer Sentiment',
                'date': 'Mon, Feb 09',
                'time': '23:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-2.6%',
                'forecast': 'N/A',
                'previous': '-1.7%'
            },
            {
                'title': 'M2 Money Stock y/y',
                'date': 'Mon, Feb 09',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '1.6%',
                'forecast': '1.8%',
                'previous': '1.7%'
            },
            {
                'title': 'BRC Retail Sales Monitor y/y',
                'date': 'Mon, Feb 09',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '2.3%',
                'forecast': '1.2%',
                'previous': '1.0%'
            },
            {
                'title': 'NAB Business Confidence',
                'date': 'Mon, Feb 09',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '3',
                'forecast': 'N/A',
                'previous': '2'
            },

            # TUESDAY, FEBRUARY 10
            {
                'title': 'Prelim Machine Tool Orders y/y',
                'date': 'Tue, Feb 10',
                'time': '06:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '25.3%',
                'forecast': 'N/A',
                'previous': '10.9%'
            },
            {
                'title': 'NFIB Small Business Index',
                'date': 'Tue, Feb 10',
                'time': '11:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '99.3',
                'forecast': '99.8',
                'previous': '99.5'
            },
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Feb 10',
                'time': '13:20 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '7.8K'
            },
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Tue, Feb 10',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.0%',
                'forecast': '0.4%',
                'previous': '0.5%'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Tue, Feb 10',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.0%',
                'forecast': '0.4%',
                'previous': '0.6%'
            },
            {
                'title': 'Employment Cost Index q/q',
                'date': 'Tue, Feb 10',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '0.7%',
                'forecast': '0.8%',
                'previous': '0.8%'
            },
            {
                'title': 'Import Prices m/m',
                'date': 'Tue, Feb 10',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.1%',
                'previous': '0.4%'
            },
            {
                'title': 'Business Inventories m/m',
                'date': 'Tue, Feb 10',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'FOMC Member Hammack Speaks',
                'date': 'Tue, Feb 10',
                'time': '17:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Logan Speaks',
                'date': 'Tue, Feb 10',
                'time': '18:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Tue, Feb 10',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RBA Deputy Gov Hauser Speaks',
                'date': 'Tue, Feb 10',
                'time': '01:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CPI y/y',
                'date': 'Tue, Feb 10',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': '0.2%',
                'forecast': '0.4%',
                'previous': '0.8%'
            },
            {
                'title': 'PPI y/y',
                'date': 'Tue, Feb 10',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': '-1.4%',
                'forecast': '-1.5%',
                'previous': '-1.9%'
            },
            {
                'title': 'NAB Quarterly Business Confidence',
                'date': 'Tue, Feb 10',
                'time': '04:59 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '2'
            },

            # WEDNESDAY, FEBRUARY 11
            {
                'title': 'Italian Industrial Production m/m',
                'date': 'Wed, Feb 11',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.4%',
                'forecast': '-0.4%',
                'previous': '1.5%'
            },
            {
                'title': 'German 30-y Bond Auction',
                'date': 'Wed, Feb 11',
                'time': '10:34 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.47|1.6',
                'forecast': 'N/A',
                'previous': '3.49|2.4'
            },
            {
                'title': 'Building Permits m/m',
                'date': 'Wed, Feb 11',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '6.8%',
                'forecast': 'N/A',
                'previous': '-13.2%'
            },
            {
                'title': 'Average Hourly Earnings m/m',
                'date': 'Wed, Feb 11',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.4%',
                'forecast': '0.3%',
                'previous': '0.1%'
            },
            {
                'title': 'Non-Farm Employment Change',
                'date': 'Wed, Feb 11',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '130K',
                'forecast': '70K',
                'previous': '48K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Wed, Feb 11',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '4.3%',
                'forecast': '4.4%',
                'previous': '4.3%'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Wed, Feb 11',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '8.5M',
                'forecast': 'N/A',
                'previous': '-3.5M'
            },
            {
                'title': '10-y Bond Auction',
                'date': 'Wed, Feb 11',
                'time': '18:01 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '4.17|2.6'
            },
            {
                'title': 'BOC Summary of Deliberations',
                'date': 'Wed, Feb 11',
                'time': '18:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Federal Budget Balance',
                'date': 'Wed, Feb 11',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-94.6B',
                'forecast': 'N/A',
                'previous': '-144.7B'
            },
            {
                'title': 'PPI y/y',
                'date': 'Wed, Feb 11',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '	2.3%',
                'forecast': '2.3%',
                'previous': '2.4%'
            },
            {
                'title': 'MI Inflation Expectations',
                'date': 'Wed, Feb 11',
                'time': '00:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '5.0%	',
                'forecast': 'N/A',
                'previous': '4.6%'
            },
            {
                'title': 'RICS House Price Balance',
                'date': 'Wed, Feb 11',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-10%	',
                'forecast': '-11%',
                'previous': '-13%'
            },
            {
                'title': 'RBA Assist Gov Hunter Speaks',
                'date': 'Wed, Feb 11',
                'time': '04:45 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # THURSDAY, FEBRUARY 12
            {
                'title': 'GDP m/m',
                'date': 'Thu, Feb 12',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '0.1%',
                'forecast': '0.1%',
                'previous': '0.3%'
            },
            {
                'title': 'Prelim GDP q/q',
                'date': 'Thu, Feb 12',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': '0.1%',
                'forecast': '0.2%',
                'previous': '0.1%'
            },
            {
                'title': 'Construction Output m/m',
                'date': 'Thu, Feb 12',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-0.5%',
                'forecast': '0.6%',
                'previous': '-0.8%'
            },
            {
                'title': 'Goods Trade Balance',
                'date': 'Thu, Feb 12',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-22.7B',
                'forecast': '-22.0B',
                'previous': '-23.7B'
            },
            {
                'title': 'Index of Services 3m/3m',
                'date': 'Thu, Feb 12',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.0%',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Industrial Production m/m',
                'date': 'Thu, Feb 12',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-0.9%',
                'forecast': '0.0%',
                'previous': '1.1%'
            },
            {
                'title': 'Manufacturing Production m/m',
                'date': 'Thu, Feb 12',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-0.5%',
                'forecast': '-0.1%',
                'previous': '2.1%'
            },
            {
                'title': 'Prelim Business Investment q/q',
                'date': 'Thu, Feb 12',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-2.7%',
                'forecast': '0.2%',
                'previous': '-0.3%'
            },
            
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Feb 12',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '227K',
                'forecast': '222K',
                'previous': '231K'
            },
            {
                'title': 'Gov Council Member Rogers Speaks',
                'date': 'Thu, Feb 12',
                'time': '13:45 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CB Leading Index m/m',
                'date': 'Thu, Feb 12',
                'time': '14:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.0%	',
                'forecast': 'N/A',
                'previous': '-0.1%'
            },
            {
                'title': 'Existing Home Sales',
                'date': 'Thu, Feb 12',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '3.91M',
                'forecast': '4.22M',
                'previous': '4.35M'
            },
            {
                'title': 'CB Leading Index m/m',
                'date': 'Thu, Feb 12',
                'time': '15:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': 'N/A',
                'previous': '0.3%'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Feb 12',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-249B',
                'forecast': 'N/A',
                'previous': '-360B'
            },
            {
                'title': '30-y Bond Auction',
                'date': 'Thu, Feb 12',
                'time': '18:01 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '4.75|2.7',
                'forecast': 'N/A',
                'previous': '4.83|2.4'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Thu, Feb 12',
                'time': '19:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BusinessNZ Manufacturing Index',
                'date': 'Thu, Feb 12',
                'time': '21:30 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '55.2',
                'forecast': 'N/A',
                'previous': '56.1'
            },
            {
                'title': 'Visitor Arrivals m/m',
                'date': 'Thu, Feb 12',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '1.7%',
                'forecast': 'N/A',
                'previous': '0.8%'
            },
            {
                'title': 'FOMC Member Logan Speaks',
                'date': 'Thu, Feb 12',
                'time': '00:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Miran Speaks',
                'date': 'Thu, Feb 12',
                'time': '00:05 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'New Home Prices m/m',
                'date': 'Thu, Feb 12',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '-0.37%',
                'forecast': 'N/A',
                'previous': '-0.37%'
            },
            {
                'title': 'Inflation Expectations q/q',
                'date': 'Thu, Feb 12',
                'time': '02:00 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '2.37%',
                'forecast': 'N/A',
                'previous': '2.28%'
            },

            # FRIDAY, FEBRUARY 13
            {
                'title': 'German WPI m/m',
                'date': 'Fri, Feb 13',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.9%',
                'forecast': '0.1%',
                'previous': '-0.2%'
            },
            {
                'title': 'CPI m/m',
                'date': 'Fri, Feb 13',
                'time': '07:30 UTC',
                'currency': 'CHF',
                'impact': 'high',
                'actual': '-0.1%',
                'forecast': '0.0%',
                'previous': '0.0%'
            },
            {
                'title': 'Flash Employment Change q/q',
                'date': 'Fri, Feb 13',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.1%',
                'previous': '0.1%'
            },
            {
                'title': 'Flash GDP q/q',
                'date': 'Fri, Feb 13',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.3%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Fri, Feb 13',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '11.6B',
                'forecast': '10.2B',
                'previous': '10.7B'
            },
            {
                'title': 'MPC Member Pill Speaks',
                'date': 'Fri, Feb 13',
                'time': '12:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Core CPI m/m',
                'date': 'Fri, Feb 13',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.2%'
            },
            {
                'title': 'CPI m/m',
                'date': 'Fri, Feb 13',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.2%',
                'forecast': '0.3%',
                'previous': '0.3%'
            },
            {
                'title': 'CPI y/y',
                'date': 'Fri, Feb 13',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '2.4%',
                'forecast': '2.5%',
                'previous': '2.7%'
            },

            # SUNDAY, FEBRUARY 15

            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Sun, Feb 15',
                'time': '09:30 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'BusinessNZ Services Index',
                'date': 'Sun, Feb 15',
                'time': '21:30 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '50.9	',
                'forecast': 'N/A',
                'previous': '51.5'
            },
            {
                'title': 'Prelim GDP Price Index y/y',
                'date': 'Sun, Feb 15',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.4%',
                'forecast': '3.2%',
                'previous': '3.4%'
            },
            {
                'title': 'Prelim GDP q/q',
                'date': 'Sun, Feb 15',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '0.1%	',
                'forecast': '0.4%',
                'previous': '-0.6%'
            },
            {
                'title': 'Rightmove HPI m/m',
                'date': 'Sun, Feb 15',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.0%	',
                'forecast': 'N/A',
                'previous': '2.8%'
            },
            {
                'title': 'Revised Industrial Production m/m',
                'date': 'Sun, Feb 15',
                'time': '04:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': '-0.1%',
                'previous': '-0.1%'
            },

            # MONDAY, FEBRUARY 16
            {
                'title': 'Industrial Production m/m',
                'date': 'Mon, Feb 16',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-1.4%',
                'forecast': '-1.5%',
                'previous': '0.3%'
            },
            {
                'title': 'Eurogroup Meetings',
                'date': 'Mon, Feb 16',
                'time': '10:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Housing Starts',
                'date': 'Mon, Feb 16',
                'time': '13:15 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '238K',
                'forecast': '266K',
                'previous': '281K'
            },
            {
                'title': 'FOMC Member Bowman Speaks',
                'date': 'Mon, Feb 16',
                'time': '13:25 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Manufacturing Sales m/m',
                'date': 'Mon, Feb 16',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '0.6%',
                'forecast': '0.5%',
                'previous': '-1.3%'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Mon, Feb 16',
                'time': '17:40 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FPI m/m',
                'date': 'Mon, Feb 16',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '2.5%',
                'forecast': 'N/A',
                'previous': '-0.3%'
            },
            {
                'title': 'Monetary Policy Meeting Minutes',
                'date': 'Mon, Feb 16',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Tertiary Industry Activity m/m',
                'date': 'Mon, Feb 16',
                'time': '04:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-0.5%',
                'forecast': '-0.3%',
                'previous': '-0.4%'
            },

            # TUESDAY, FEBRUARY 17
            {
                'title': 'German Final CPI m/m',
                'date': 'Tue, Feb 17',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.1%',
                'previous': '0.1%'
            },
            {
                'title': 'Claimant Count Change',
                'date': 'Tue, Feb 17',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '28.6K',
                'forecast': '22.8K',
                'previous': '2.7K'
            },
            {
                'title': 'Average Earnings Index 3m/y',
                'date': 'Tue, Feb 17',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': '4.2%',
                'forecast': '4.6%',
                'previous': '4.6%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Tue, Feb 17',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '5.2%',
                'forecast': '5.1%',
                'previous': '5.1%'
            },
            {
                'title': 'Italian Trade Balance',
                'date': 'Tue, Feb 17',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '6.04B',
                'forecast': '4.75B',
                'previous': '5.08B'
            },
            {
                'title': 'ZEW Economic Sentiment',
                'date': 'Tue, Feb 17',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '39.4',
                'forecast': '45.2',
                'previous': '40.8'
            },
            {
                'title': 'German ZEW Economic Sentiment',
                'date': 'Tue, Feb 17',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '58.3',
                'forecast': '65.2',
                'previous': '59.6'
            },
            {
                'title': 'ECOFIN Meetings',
                'date': 'Tue, Feb 17',
                'time': '10:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Feb 17',
                'time': '13:20 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '10.3K',
                'forecast': 'N/A',
                'previous': '7.8K'
            },
            {
                'title': 'CPI m/m',
                'date': 'Tue, Feb 17',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '0.0%',
                'forecast': '0.1%',
                'previous': '-0.2%'
            },
            {
                'title': 'Median CPI y/y',
                'date': 'Tue, Feb 17',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '2.5%',
                'forecast': '2.5%',
                'previous': '2.6%'
            },
            {
                'title': 'Trimmed CPI y/y',
                'date': 'Tue, Feb 17',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '2.4%',
                'forecast': '2.6%',
                'previous': '2.7%'
            },
            {
                'title': 'Common CPI y/y',
                'date': 'Tue, Feb 17',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '2.7%',
                'forecast': '2.8%',
                'previous': '2.8%'
            },
            {
                'title': 'Core CPI m/m',
                'date': 'Tue, Feb 17',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': 'N/A',
                'previous': '-0.4%'
            },
            {
                'title': 'Foreign Securities Purchases',
                'date': 'Tue, Feb 17',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-5.57B',
                'forecast': 'N/A',
                'previous': '16.33B'
            },
            {
                'title': 'Wholesale Sales m/m',
                'date': 'Tue, Feb 17',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '2.0%',
                'forecast': '1.9%',
                'previous': '-1.8%'
            },
            {
                'title': 'Empire State Manufacturing Index',
                'date': 'Tue, Feb 17',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '7.1',
                'forecast': '8.5',
                'previous': '7.7'
            },
            {
                'title': 'Cleveland Fed Inflation Expectations',
                'date': 'Tue, Feb 17',
                'time': '14:48 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '3.3%'
            },
            {
                'title': 'NAHB Housing Market Index',
                'date': 'Tue, Feb 17',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '38',
                'previous': '37'
            },
            {
                'title': 'GDT Price Index',
                'date': 'Tue, Feb 17',
                'time': '15:50 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '3.6%',
                'forecast': 'N/A',
                'previous': '6.7%'
            },
            {
                'title': 'FOMC Member Barr Speaks',
                'date': 'Tue, Feb 17',
                'time': '17:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Daly Speaks',
                'date': 'Tue, Feb 17',
                'time': '19:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'PPI Input q/q',
                'date': 'Tue, Feb 17',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '-0.5%',
                'forecast': '0.5%',
                'previous': '0.2%'
            },
            {
                'title': 'PPI Output q/q',
                'date': 'Tue, Feb 17',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.7%',
                'previous': '0.6%'
            },
            {
                'title': 'MI Leading Index m/m',
                'date': 'Tue, Feb 17',
                'time': '23:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': 'N/A',
                'previous': '0.1%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Tue, Feb 17',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '0.46T',
                'forecast': '-0.16T',
                'previous': '-0.06T'
            },
            {
                'title': 'Wage Price Index q/q',
                'date': 'Tue, Feb 17',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'medium',
                'actual': '0.8%',
                'forecast': '0.8%',
                'previous': '0.8%'
            },
            {
                'title': 'Official Cash Rate',
                'date': 'Tue, Feb 17',
                'time': '01:00 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': '2.25%',
                'forecast': '2.25%',
                'previous': '2.25%'
            },
            {
                'title': 'RBNZ Monetary Policy Statement',
                'date': 'Tue, Feb 17',
                'time': '01:00 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RBNZ Rate Statement',
                'date': 'Tue, Feb 17',
                'time': '01:00 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RBNZ Press Conference',
                'date': 'Tue, Feb 17',
                'time': '02:00 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'NAB Quarterly Business Confidence',
                'date': 'Tue, Feb 17',
                'time': '04:59 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '2'
            },

            # WEDNESDAY, FEBRUARY 18
            {
                'title': 'CPI y/y',
                'date': 'Wed, Feb 18',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '3.0%',
                'forecast': '3.0%',
                'previous': '3.4%'
            },
            {
                'title': 'Core CPI y/y',
                'date': 'Wed, Feb 18',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '3.1%',
                'forecast': '3.0%',
                'previous': '3.2%'
            },
            {
                'title': 'PPI Input m/m',
                'date': 'Wed, Feb 18',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.4%',
                'forecast': '0.4%',
                'previous': '-0.5%'
            },
            {
                'title': 'PPI Output m/m',
                'date': 'Wed, Feb 18',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.0%',
                'forecast': '0.2%',
                'previous': '-0.1%'
            },
            {
                'title': 'RPI y/y',
                'date': 'Wed, Feb 18',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '3.8%',
                'forecast': '3.8%',
                'previous': '4.2%'
            },
            {
                'title': 'French Final CPI m/m',
                'date': 'Wed, Feb 18',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.3%',
                'forecast': '-0.3%',
                'previous': '-0.3%'
            },
            {
                'title': 'HPI y/y',
                'date': 'Wed, Feb 18',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '2.4%',
                'forecast': '2.3%',
                'previous': '2.8%'
            },
            {
                'title': 'German 10-y Bond Auction',
                'date': 'Wed, Feb 18',
                'time': '10:42 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '	2.73|1.5',
                'forecast': 'N/A',
                'previous': '2.85|1.7'
            },
            {
                'title': 'Core Durable Goods Orders m/m',
                'date': 'Wed, Feb 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '0.9%',
                'forecast': '0.3%',
                'previous': '0.4%'
            },
            {
                'title': 'Durable Goods Orders m/m',
                'date': 'Wed, Feb 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '-1.4%',
                'forecast': '-1.8%',
                'previous': '5.4%'
            },
            {
                'title': 'Building Permits',
                'date': 'Wed, Feb 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.45M',
                'forecast': '1.42M',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Bowman Speaks',
                'date': 'Wed, Feb 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Housing Starts',
                'date': 'Wed, Feb 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.40M',
                'forecast': '1.33M',
                'previous': 'N/A'
            },
            {
                'title': 'Building Permits',
                'date': 'Wed, Feb 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.45M',
                'forecast': 'N/A',
                'previous': '1.41M'
            },
            {
                'title': 'Housing Starts',
                'date': 'Wed, Feb 18',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.40M',
                'forecast': 'N/A',
                'previous': '1.25M'
            },
            {
                'title': 'Capacity Utilization Rate',
                'date': 'Wed, Feb 18',
                'time': '14:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '76.2%',
                'forecast': '76.4%',
                'previous': '75.7%'
            },
            {
                'title': 'Industrial Production m/m',
                'date': 'Wed, Feb 18',
                'time': '14:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '	0.7%',
                'forecast': '0.4%',
                'previous': '0.2%'
            },
            {
                'title': 'FOMC Meeting Minutes',
                'date': 'Wed, Feb 18',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'TIC Long-Term Purchases',
                'date': 'Wed, Feb 18',
                'time': '21:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '28.0B',
                'forecast': '125.8B',
                'previous': '220.2B'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Wed, Feb 18',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Core Machinery Orders m/m',
                'date': 'Wed, Feb 18',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '19.1%',
                'forecast': '5.1%',
                'previous': '-11.0%'
            },
            {
                'title': 'Employment Change',
                'date': 'Wed, Feb 18',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '17.8K',
                'forecast': '20.1K',
                'previous': '68.5K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Wed, Feb 18',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '4.1%',
                'forecast': '4.2%',
                'previous': '4.1%'
            },

            # THURSDAY, FEBRUARY 19
            {
                'title': 'Current Account',
                'date': 'Thu, Feb 19',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '14.6B',
                'forecast': '9.2B',
                'previous': '8.9B'
            },
            {
                'title': 'ECB Economic Bulletin',
                'date': 'Thu, Feb 19',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Spanish 10-y Bond Auction',
                'date': 'Thu, Feb 19',
                'time': '10:03 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.17|2.5',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'German Buba Monthly Report',
                'date': 'Thu, Feb 19',
                'time': '11:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CBI Industrial Order Expectations',
                'date': 'Thu, Feb 19',
                'time': '11:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-28',
                'forecast': '-27',
                'previous': '-30'
            },
            {
                'title': 'FOMC Member Bostic Speaks',
                'date': 'Thu, Feb 19',
                'time': '13:20 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'NHPI m/m',
                'date': 'Thu, Feb 19',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-0.4%',
                'forecast': '0.1%',
                'previous': '-0.2%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Feb 19',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-1.3B',
                'forecast': '-2.0B',
                'previous': '-2.6B'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Feb 19',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '206K',
                'forecast': '229K',
                'previous': '229K'
            },
            {
                'title': 'Philly Fed Manufacturing Index',
                'date': 'Thu, Feb 19',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '16.3',
                'forecast': '7.8',
                'previous': '12.6'
            },
            {
                'title': 'FOMC Member Bowman Speaks',
                'date': 'Thu, Feb 19',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Goods Trade Balance',
                'date': 'Thu, Feb 19',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-98.5B',
                'forecast': '-85.7B',
                'previous': '-82.8B'
            },
            {
                'title': 'Prelim Wholesale Inventories m/m',
                'date': 'Thu, Feb 19',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.1%',
                'previous': '0.2%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Feb 19',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-70.3B',
                'forecast': '-55.2B',
                'previous': '-53.8B'
            },
            {
                'title': 'FOMC Member Kashkari Speaks',
                'date': 'Thu, Feb 19',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Consumer Confidence',
                'date': 'Thu, Feb 19',
                'time': '15:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-12',
                'forecast': '-12',
                'previous': '-12'
            },
            {
                'title': 'Pending Home Sales m/m',
                'date': 'Thu, Feb 19',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '-0.8%',
                'forecast': '2.4%',
                'previous': '-7.4%'
            },
            {
                'title': 'CB Leading Index m/m',
                'date': 'Thu, Feb 19',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': '-0.3%',
                'previous': '-0.3%'
            },
            {
                'title': 'FOMC Member Goolsbee Speaks',
                'date': 'Thu, Feb 19',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Feb 19',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-144B',
                'forecast': 'N/A',
                'previous': '-249B'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Thu, Feb 19',
                'time': '17:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '	-9.0M',
                'forecast': 'N/A',
                'previous': '8.5M'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Feb 19',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '-519M',
                'forecast': '-745M',
                'previous': '-88M'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Thu, Feb 19',
                'time': '22:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '51.5',
                'forecast': 'N/A',
                'previous': '52.3'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Thu, Feb 19',
                'time': '22:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '52.2',
                'forecast': 'N/A',
                'previous': '56.3'
            },
            {
                'title': 'RBNZ Gov Breman Speaks',
                'date': 'Thu, Feb 19',
                'time': '23:00 UTC',
                'currency': 'NZD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'National Core CPI y/y',
                'date': 'Thu, Feb 19',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.0%',
                'forecast': '2.0%',
                'previous': '2.4%'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Thu, Feb 19',
                'time': '00:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Thu, Feb 19',
                'time': '00:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '52.8',
                'forecast': '51.3',
                'previous': '51.5'
            },

            # FRIDAY, FEBRUARY 20
            {
                'title': 'German PPI m/m',
                'date': 'Fri, Feb 20',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.6%',
                'forecast': '0.3%',
                'previous': '-0.2%'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Fri, Feb 20',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '1.8%',
                'forecast': '0.2%',
                'previous': '0.4%'
            },
            {
                'title': 'Public Sector Net Borrowing',
                'date': 'Fri, Feb 20',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-30.4B',
                'forecast': '-23.3B',
                'previous': '13.4B'
            },
            {
                'title': 'French Flash Manufacturing PMI',
                'date': 'Fri, Feb 20',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '49.9',
                'forecast': '51.0',
                'previous': '51.2'
            },
            {
                'title': 'French Flash Services PMI',
                'date': 'Fri, Feb 20',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '49.6',
                'forecast': '49.1',
                'previous': '48.4'
            },
            {
                'title': 'German Flash Manufacturing PMI',
                'date': 'Fri, Feb 20',
                'time': '08:30 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': '	50.7',
                'forecast': '49.6',
                'previous': '49.1'
            },
            {
                'title': 'German Flash Services PMI',
                'date': 'Fri, Feb 20',
                'time': '08:30 UTC',
                'currency': 'EUR',
                'impact': 'high',
                'actual': '53.4',
                'forecast': '52.5',
                'previous': '52.4'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Fri, Feb 20',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '50.8',
                'forecast': '50.0',
                'previous': '49.4'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Fri, Feb 20',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '51.8',
                'forecast': '51.9',
                'previous': '51.9'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Fri, Feb 20',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '52.0',
                'forecast': '51.5',
                'previous': '51.6'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Fri, Feb 20',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '53.9',
                'forecast': '53.4',
                'previous': '54.3'
            },
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Fri, Feb 20',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '0.1%',
                'forecast': '0.1%',
                'previous': '1.7%'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Fri, Feb 20',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '-0.4%',
                'forecast': '-0.4%',
                'previous': '1.3%'
            },
            {
                'title': 'IPPI m/m',
                'date': 'Fri, Feb 20',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '2.7%',
                'forecast': '0.2%',
                'previous': '-0.6%'
            },
            {
                'title': 'RMPI m/m',
                'date': 'Fri, Feb 20',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '7.7%',
                'forecast': '0.6%',
                'previous': '0.5%'
            },
            {
                'title': 'Advance GDP q/q',
                'date': 'Fri, Feb 20',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '1.4%',
                'forecast': '2.8%',
                'previous': '3.0%'
            },
            {
                'title': 'Core PCE Price Index m/m',
                'date': 'Fri, Feb 20',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.4%',
                'forecast': '0.3%',
                'previous': '0.2%'
            },
            {
                'title': 'Advance GDP Price Index q/q',
                'date': 'Fri, Feb 20',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '3.6%',
                'forecast': '3.2%',
                'previous': '2.0%'
            },
            {
                'title': 'Personal Income m/m',
                'date': 'Fri, Feb 20',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.3%'
            },
            {
                'title': 'Personal Spending m/m',
                'date': 'Fri, Feb 20',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.4%',
                'forecast': '0.4%',
                'previous': '0.5%'
            },
            {
                'title': 'Flash Manufacturing PMI',
                'date': 'Fri, Feb 20',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '51.2',
                'forecast': '52.1',
                'previous': '51.9'
            },
            {
                'title': 'Flash Services PMI',
                'date': 'Fri, Feb 20',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '52.3',
                'forecast': '52.8',
                'previous': '52.5'
            },
            {
                'title': 'FOMC Member Bostic Speaks',
                'date': 'Fri, Feb 20',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'New Home Sales',
                'date': 'Fri, Feb 20',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '745K',
                'forecast': '735K',
                'previous': 'N/A'
            },
            {
                'title': 'Revised UoM Consumer Sentiment',
                'date': 'Fri, Feb 20',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '56.6',
                'forecast': '56.9',
                'previous': '57.3'
            },
            {
                'title': 'Revised UoM Inflation Expectations',
                'date': 'Fri, Feb 20',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '3.4%',
                'forecast': 'N/A',
                'previous': '3.5%'
            },
            {
                'title': 'New Home Sales',
                'date': 'Fri, Feb 20',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '745K',
                'forecast': '736K',
                'previous': '737K'
            },
            {
                'title': 'FOMC Member Logan Speaks',
                'date': 'Fri, Feb 20',
                'time': '18:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # SUNDAY, FEBRUARY 22
            
            {
                'title': 'Retail Sales q/q',
                'date': 'Sun, Feb 22',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'medium',
                'actual': '0.9%',
                'forecast': '0.6%',
                'previous': '1.9%'
            },
            {
                'title': 'Core Retail Sales q/q',
                'date': 'Sun, Feb 22',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '1.5%',
                'forecast': '0.4%',
                'previous': '1.2%'
            },
            {
                'title': 'Credit Card Spending y/y',
                'date': 'Sun, Feb 22',
                'time': '02:00 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '1.0%',
                'forecast': 'N/A',
                'previous': '-0.2%'
            },

            # MONDAY, FEBRUARY 23
            {
                'title': 'PPI m/m',
                'date': 'Mon, Feb 23',
                'time': '07:30 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': '0.1%',
                'previous': '-0.2%'
            },
            {
                'title': 'German ifo Business Climate',
                'date': 'Mon, Feb 23',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '88.6',
                'forecast': '88.4',
                'previous': '87.6'
            },
            {
                'title': 'MPC Member Taylor Speaks',
                'date': 'Mon, Feb 23',
                'time': '11:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Waller Speaks',
                'date': 'Mon, Feb 23',
                'time': '13:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Belgian NBB Business Climate',
                'date': 'Mon, Feb 23',
                'time': '14:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-13.7',
                'forecast': '-7.5',
                'previous': '-8.8'
            },
            {
                'title': 'Factory Orders m/m',
                'date': 'Mon, Feb 23',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-0.7%',
                'forecast': '-0.4%',
                'previous': '2.7%'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Mon, Feb 23',
                'time': '17:30 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': '1-y Loan Prime Rate',
                'date': 'Mon, Feb 23',
                'time': '01:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '3.00%',
                'forecast': '3.00%',
                'previous': '3.00%'
            },
            {
                'title': '5-y Loan Prime Rate',
                'date': 'Mon, Feb 23',
                'time': '01:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '3.50%',
                'forecast': '3.50%',
                'previous': '3.50%'
            },

            # TUESDAY, FEBRUARY 24
            {
                'title': 'Foreign Direct Investment ytd/y',
                'date': 'Tue, Feb 24',
                'time': '07:02 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '-9.5%'
            },
            {
                'title': 'CBI Realized Sales',
                'date': 'Tue, Feb 24',
                'time': '11:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-43',
                'forecast': '-26',
                'previous': '-17'
            },
            {
                'title': 'FOMC Member Goolsbee Speaks',
                'date': 'Tue, Feb 24',
                'time': '13:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Feb 24',
                'time': '13:20 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '12.8K',
                'forecast': 'N/A',
                'previous': '10.3K'
            },
            {
                'title': 'FOMC Member Bostic Speaks',
                'date': 'Tue, Feb 24',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Collins Speaks',
                'date': 'Tue, Feb 24',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'HPI m/m',
                'date': 'Tue, Feb 24',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.3%',
                'previous': '0.6%'
            },
            {
                'title': 'S&P/CS Composite-20 HPI y/y',
                'date': 'Tue, Feb 24',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.4%',
                'forecast': '1.3%',
                'previous': '1.4%'
            },
            {
                'title': 'Monetary Policy Report Hearings',
                'date': 'Tue, Feb 24',
                'time': '14:15 UTC',
                'currency': 'GBP',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Waller Speaks',
                'date': 'Tue, Feb 24',
                'time': '14:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Cook Speaks',
                'date': 'Tue, Feb 24',
                'time': '14:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'CB Consumer Confidence',
                'date': 'Tue, Feb 24',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '91.2',
                'forecast': '87.6',
                'previous': '84.5'
            },
            {
                'title': 'Richmond Manufacturing Index',
                'date': 'Tue, Feb 24',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '-10',
                'forecast': '-4',
                'previous': '-6'
            },
            {
                'title': 'Final Wholesale Inventories m/m',
                'date': 'Tue, Feb 24',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'FOMC Member Barkin Speaks',
                'date': 'Tue, Feb 24',
                'time': '20:20 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Collins Speaks',
                'date': 'Tue, Feb 24',
                'time': '20:20 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Tue, Feb 24',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'SPPI y/y',
                'date': 'Tue, Feb 24',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.6%',
                'forecast': '2.6%',
                'previous': '2.6%'
            },
            {
                'title': 'CPI m/m',
                'date': 'Wed, Feb 25',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '0.4%',
                'forecast': 'N/A',
                'previous': '1.0%'
            },
            {
                'title': 'CPI y/y',
                'date': 'Wed, Feb 25',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '3.8%',
                'forecast': '3.7%',
                'previous': '3.8%'
            },
            {
                'title': 'Trimmed Mean CPI m/m',
                'date': 'Wed, Feb 25',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '0.3%',
                'forecast': '0.4%',
                'previous': '0.2%'
            },
            {
                'title': 'Construction Work Done q/q',
                'date': 'Wed, Feb 25',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': '1.2%',
                'previous': '0.1%'
            },
            {
                'title': 'President Trump Speaks',
                'date': 'Wed, Feb 25',
                'time': '02:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'NAB Quarterly Business Confidence',
                'date': 'Tue, Feb 24',
                'time': '04:59 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '2'
            },

            # WEDNESDAY, FEBRUARY 25
            {
                'title': 'BOJ Core CPI y/y',
                'date': 'Wed, Feb 25',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '1.7%',
                'forecast': '1.9%',
                'previous': '1.9%'
            },
            {
                'title': 'German Final GDP q/q',
                'date': 'Wed, Feb 25',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.3%'
            },
            {
                'title': 'German GfK Consumer Climate',
                'date': 'Wed, Feb 25',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-24.7',
                'forecast': '-22.9',
                'previous': '-24.1'
            },
            {
                'title': 'RBA Gov Bullock Speaks',
                'date': 'Wed, Feb 25',
                'time': '08:40 UTC',
                'currency': 'AUD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'UBS Economic Expectations',
                'date': 'Wed, Feb 25',
                'time': '09:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '9.8',
                'forecast': 'N/A',
                'previous': '-4.7'
            },
            {
                'title': 'Final Core CPI y/y',
                'date': 'Wed, Feb 25',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '2.2%',
                'forecast': '2.2%',
                'previous': '2.2%'
            },
            {
                'title': 'Final CPI y/y',
                'date': 'Wed, Feb 25',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '1.7%',
                'forecast': '1.7%',
                'previous': '1.7%'
            },
            {
                'title': 'Corporate Profits q/q',
                'date': 'Wed, Feb 25',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-1.6%',
                'forecast': 'N/A',
                'previous': '7.6%'
            },
            {
                'title': 'CB Leading Index m/m',
                'date': 'Wed, Feb 25',
                'time': '14:00 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '-0.3%',
                'forecast': 'N/A',
                'previous': '0.0%'
            },
            {
                'title': 'FOMC Member Barkin Speaks',
                'date': 'Wed, Feb 25',
                'time': '14:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Wed, Feb 25',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '16.0M',
                'forecast': 'N/A',
                'previous': '-9.0M'
            },
            {
                'title': 'FOMC Member Schmid Speaks',
                'date': 'Wed, Feb 25',
                'time': '16:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Musalem Speaks',
                'date': 'Wed, Feb 25',
                'time': '18:20 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ANZ Business Confidence',
                'date': 'Wed, Feb 25',
                'time': '00:00 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '59.2',
                'forecast': 'N/A',
                'previous': '64.1'
            },
            {
                'title': 'Private Capital Expenditure q/q',
                'date': 'Wed, Feb 25',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '0.4%',
                'forecast': '-0.1%',
                'previous': '6.4%'
            },
            {
                'title': 'RBA Bulletin',
                'date': 'Wed, Feb 25',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # THURSDAY, FEBRUARY 26
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Thu, Feb 26',
                'time': '08:30 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'M3 Money Supply y/y',
                'date': 'Thu, Feb 26',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.3%',
                'forecast': '2.9%',
                'previous': '2.8%'
            },
            {
                'title': 'Private Loans y/y',
                'date': 'Thu, Feb 26',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.0%',
                'forecast': '3.1%',
                'previous': '3.0%'
            },
            {
                'title': 'MPC Member Lombardelli Speaks',
                'date': 'Thu, Feb 26',
                'time': '09:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Italian 10-y Bond Auction',
                'date': 'Thu, Feb 26',
                'time': '10:33 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.31|1.5',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Current Account',
                'date': 'Thu, Feb 26',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-0.7B',
                'forecast': '-5.4B',
                'previous': '-5.3B'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Feb 26',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '212K',
                'forecast': '216K',
                'previous': '208K'
            },
            {
                'title': 'FOMC Member Bowman Speaks',
                'date': 'Thu, Feb 26',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Feb 26',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-52B',
                'forecast': 'N/A',
                'previous': '-144B'
            },
            {
                'title': 'Tokyo Core CPI y/y',
                'date': 'Thu, Feb 26',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'medium',
                'actual': '1.8%',
                'forecast': '1.7%',
                'previous': '2.0%'
            },
            {
                'title': 'Prelim Industrial Production m/m',
                'date': 'Thu, Feb 26',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.2%',
                'forecast': '5.5%',
                'previous': '-0.1%'
            },
            {
                'title': 'Retail Sales y/y',
                'date': 'Thu, Feb 26',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '1.8%',
                'forecast': '0.2%',
                'previous': '-0.9%'
            },
            {
                'title': 'GfK Consumer Confidence',
                'date': 'Thu, Feb 26',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-19',
                'forecast': '-15',
                'previous': '-16'
            },
            {
                'title': 'Private Sector Credit m/m',
                'date': 'Thu, Feb 26',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '0.5%',
                'forecast': '0.7%',
                'previous': '0.8%'
            },

            # FRIDAY, FEBRUARY 27
            {
                'title': 'Housing Starts y/y',
                'date': 'Fri, Feb 27',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-0.4%',
                'forecast': '-2.0%',
                'previous': '-1.3%'
            },
            {
                'title': 'German Import Prices m/m',
                'date': 'Fri, Feb 27',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '1.1%',
                'forecast': '0.6%',
                'previous': '-0.1%'
            },
            {
                'title': 'German Prelim CPI m/m',
                'date': 'Fri, Feb 27',
                'time': '07:29 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.5%',
                'previous': '0.1%'
            },
            {
                'title': 'French Consumer Spending m/m',
                'date': 'Fri, Feb 27',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.5%',
                'forecast': '0.3%',
                'previous': '-0.5%'
            },
            {
                'title': 'French Final Private Payrolls q/q',
                'date': 'Fri, Feb 27',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': '0.0%',
                'previous': '-0.1%'
            },
            {
                'title': 'French Prelim CPI m/m',
                'date': 'Fri, Feb 27',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.7%',
                'forecast': '0.5%',
                'previous': '-0.3%'
            },
            {
                'title': 'French Prelim GDP q/q',
                'date': 'Fri, Feb 27',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'GDP q/q',
                'date': 'Fri, Feb 27',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.2%',
                'previous': '-0.4%'
            },
            {
                'title': 'KOF Economic Barometer',
                'date': 'Fri, Feb 27',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '104.2',
                'forecast': '102.9',
                'previous': '103.3'
            },
            {
                'title': 'Spanish Flash CPI y/y',
                'date': 'Fri, Feb 27',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '2.3%',
                'forecast': '2.2%',
                'previous': '2.3%'
            },
            {
                'title': 'German Unemployment Change',
                'date': 'Fri, Feb 27',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '1K',
                'forecast': '2K',
                'previous': '1K'
            },
            {
                'title': 'MPC Member Pill Speaks',
                'date': 'Fri, Feb 27',
                'time': '13:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'GDP m/m',
                'date': 'Fri, Feb 27',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': '0.2%',
                'forecast': '0.1%',
                'previous': '0.0%'
            },
            {
                'title': 'Core PPI m/m',
                'date': 'Fri, Feb 27',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.8%',
                'forecast': '0.3%',
                'previous': '0.7%'
            },
            {
                'title': 'PPI m/m',
                'date': 'Fri, Feb 27',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.5%',
                'forecast': '0.3%',
                'previous': '0.5%'
            },
            {
                'title': 'Chicago PMI',
                'date': 'Fri, Feb 27',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '57.7',
                'forecast': '52.4',
                'previous': '54.0'
            },
            {
                'title': 'Construction Spending m/m',
                'date': 'Fri, Feb 27',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.2%',
                'previous': '-0.2%'
            },
            {
                'title': 'Construction Spending m/m',
                'date': 'Fri, Feb 27',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': 'N/A',
                'previous': '-0.1%'
            },

             # SUNDAY, MARCH 01

            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Sun, Mar 01',
                'time': '15:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'MI Inflation Gauge m/m',
                'date': 'Sun, Mar 01',
                'time': '00:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-0.2%',
                'forecast': 'N/A',
                'previous': '0.2%'
            },
            {
                'title': 'ANZ Job Advertisements m/m',
                'date': 'Sun, Mar 01',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '3.2%',
                'forecast': 'N/A',
                'previous': '5.2%'
            },
            {
                'title': 'Company Operating Profits q/q',
                'date': 'Sun, Mar 01',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '	5.8%',
                'forecast': '1.8%',
                'previous': '1.5%'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Sun, Mar 01',
                'time': '00:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '53.0',
                'forecast': '52.8',
                'previous': '52.8'
            },

            # MONDAY, MARCH 02
            {
                'title': 'Commodity Prices y/y',
                'date': 'Mon, Mar 02',
                'time': '05:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '3.4%',
                'forecast': 'N/A',
                'previous': '2.8%'
            },
            {
                'title': 'German Retail Sales m/m',
                'date': 'Mon, Mar 02',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.9%',
                'forecast': '0.0%',
                'previous': '1.2%'
            },
            {
                'title': 'Nationwide HPI m/m',
                'date': 'Mon, Mar 02',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.2%',
                'previous': '0.3%'
            },
            {
                'title': 'Retail Sales y/y',
                'date': 'Mon, Mar 02',
                'time': '07:30 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '-1.1%',
                'forecast': '2.7%',
                'previous': '2.8%'
            },
            {
                'title': 'Spanish Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '50.0',
                'forecast': '49.9',
                'previous': '49.2'
            },
            {
                'title': 'Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '08:30 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '47.4',
                'forecast': '49.8',
                'previous': '48.8'
            },
            {
                'title': 'Italian Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '08:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '50.6',
                'forecast': '49.1',
                'previous': '48.1'
            },
            {
                'title': 'French Final Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '08:50 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '50.1',
                'forecast': '49.9',
                'previous': '49.9'
            },
            {
                'title': 'German Final Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '50.9',
                'forecast': '50.7',
                'previous': '50.7'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '50.8',
                'forecast': '50.8',
                'previous': '50.8'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '51.7',
                'forecast': '52.0',
                'previous': '52.0'
            },
            {
                'title': 'M4 Money Supply m/m',
                'date': 'Mon, Mar 02',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-0.1%	',
                'forecast': '0.2%',
                'previous': '0.4%'
            },
            {
                'title': 'Mortgage Approvals',
                'date': 'Mon, Mar 02',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '60K',
                'forecast': '62K',
                'previous': '61K'
            },
            {
                'title': 'Net Lending to Individuals m/m',
                'date': 'Mon, Mar 02',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '5.9B',
                'forecast': '6.2B',
                'previous': '6.1B'
            },
            
            {
                'title': 'RBA Assist Gov Hunter Speaks',
                'date': 'Mon, Mar 02',
                'time': '12:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'MPC Member Taylor Speaks',
                'date': 'Mon, Mar 02',
                'time': '12:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Gov Council Member Kozicki Speaks',
                'date': 'Mon, Mar 02',
                'time': '14:00 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Mon, Mar 02',
                'time': '14:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Mon, Mar 02',
                'time': '14:10 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '14:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '51.0',
                'forecast': 'N/A',
                'previous': '50.4'
            },
            {
                'title': 'Final Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '51.6',
                'forecast': '51.2',
                'previous': '51.2'
            },
            {
                'title': 'ISM Manufacturing PMI',
                'date': 'Mon, Mar 02',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '52.4',
                'forecast': '51.7',
                'previous': '52.6'
            },
            {
                'title': 'ISM Manufacturing Prices',
                'date': 'Mon, Mar 02',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': '70.5',
                'forecast': '60.6',
                'previous': '59.0'
            },
            {
                'title': 'MPC Member Ramsden Speaks',
                'date': 'Mon, Mar 02',
                'time': '15:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RBA Gov Bullock Speaks',
                'date': 'Mon, Mar 02',
                'time': '21:10 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Building Consents m/m',
                'date': 'Mon, Mar 02',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '1.9%',
                'forecast': 'N/A',
                'previous': '-4.5%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Mon, Mar 02',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.7%	',
                'forecast': '2.6%',
                'previous': '2.6%'
            },
            {
                'title': 'Capital Spending q/y',
                'date': 'Mon, Mar 02',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '6.5%',
                'forecast': '3.1%',
                'previous': '2.9%'
            },
            {
                'title': 'Monetary Base y/y',
                'date': 'Mon, Mar 02',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-10.6%',
                'forecast': '-10.2%',
                'previous': '-9.5%'
            },
            {
                'title': 'BRC Shop Price Index y/y',
                'date': 'Tue, Mar 03',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '1.1%',
                'forecast': '1.4%',
                'previous': '1.5%'
            },
            {
                'title': 'Building Approvals m/m',
                'date': 'Tue, Mar 03',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-7.2%',
                'forecast': '5.7%',
                'previous': '-14.9%'
            },
            {
                'title': 'Current Account',
                'date': 'Tue, Mar 03',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-21.1B',
                'forecast': '-16.5B',
                'previous': '-16.6B'
            },
            {
                'title': '10-y Bond Auction',
                'date': 'Tue, Mar 03',
                'time': '03:35 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.12|3.3',
                'forecast': 'N/A',
                'previous': '2.25|3.0'
            },
            {
                'title': 'BOJ Gov Ueda Speaks',
                'date': 'Tue, Mar 03',
                'time': '04:00 UTC',
                'currency': 'JPY',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # TUESDAY, MARCH 03
            {
                'title': 'French Gov Budget Balance',
                'date': 'Tue, Mar 03',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-9.7B',
                'forecast': 'N/A',
                'previous': '-124.7B'
            },
            {
                'title': 'Spanish Unemployment Change',
                'date': 'Tue, Mar 03',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.6K',
                'forecast': '37.5K',
                'previous': '30.4K'
            },
            {
                'title': 'Core CPI Flash Estimate y/y',
                'date': 'Tue, Mar 03',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '2.4%',
                'forecast': '2.2%',
                'previous': '2.2%'
            },
            {
                'title': 'CPI Flash Estimate y/y',
                'date': 'Tue, Mar 03',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': '1.9%',
                'forecast': '1.7%',
                'previous': '1.7%'
            },
            {
                'title': 'Italian Prelim CPI m/m',
                'date': 'Tue, Mar 03',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.8%',
                'forecast': '0.3%',
                'previous': '0.4%'
            },
            {
                'title': 'Annual Budget Release',
                'date': 'Tue, Mar 03',
                'time': '12:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Williams Speaks',
                'date': 'Tue, Mar 03',
                'time': '14:55 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RCM/TIPP Economic Optimism',
                'date': 'Tue, Mar 03',
                'time': '15:10 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '47.5',
                'forecast': '50.1',
                'previous': '48.8'
            },
            {
                'title': 'Wards Total Vehicle Sales',
                'date': 'Tue, Mar 03',
                'time': '15:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '15.8M',
                'forecast': '15.2B',
                'previous': '14.9M'
            },
            {
                'title': 'GDT Price Index',
                'date': 'Tue, Mar 03',
                'time': '15:50 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '5.7%',
                'forecast': 'N/A',
                'previous': '3.6%'
            },
            {
                'title': 'FOMC Member Kashkari Speaks',
                'date': 'Tue, Mar 03',
                'time': '16:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Tue, Mar 03',
                'time': '21:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Overseas Trade Index q/q',
                'date': 'Tue, Mar 03',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '3.7%',
                'forecast': '-0.2%',
                'previous': '-2.1%'
            },
            {
                'title': 'ANZ Commodity Prices m/m',
                'date': 'Tue, Mar 03',
                'time': '00:00 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '4.2%',
                'forecast': 'N/A',
                'previous': '2.0%'
            },
            {
                'title': 'GDP q/q',
                'date': 'Tue, Mar 03',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'high',
                'actual': '0.8%',
                'forecast': '0.7%',
                'previous': '0.5%'
            },
            {
                'title': 'Manufacturing PMI',
                'date': 'Tue, Mar 03',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '49.0',
                'forecast': '49.1',
                'previous': '49.3'
            },
            {
                'title': 'Non-Manufacturing PMI',
                'date': 'Tue, Mar 03',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '49.5',
                'forecast': '49.7',
                'previous': '49.4'
            },
            {
                'title': 'RatingDog Manufacturing PMI',
                'date': 'Tue, Mar 03',
                'time': '01:45 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '52.1',
                'forecast': '50.0',
                'previous': '50.3'
            },
            {
                'title': 'RatingDog Services PMI',
                'date': 'Tue, Mar 03',
                'time': '01:45 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '56.7',
                'forecast': '52.4',
                'previous': '52.3'
            },

            # WEDNESDAY, MARCH 04
            {
                'title': 'Consumer Confidence',
                'date': 'Wed, Mar 04',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '40.0',
                'forecast': '38.1',
                'previous': '37.9'
            },
            {
                'title': 'CPI m/m',
                'date': 'Wed, Mar 04',
                'time': '07:30 UTC',
                'currency': 'CHF',
                'impact': 'medium',
                'actual': '0.6%',
                'forecast': '0.5%',
                'previous': '-0.1%'
            },
            {
                'title': 'Spanish Services PMI',
                'date': 'Wed, Mar 04',
                'time': '08:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '51.9',
                'forecast': '52.9',
                'previous': '53.5'
            },
            {
                'title': 'Italian Services PMI',
                'date': 'Wed, Mar 04',
                'time': '08:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '52.3',
                'forecast': '52.5',
                'previous': '52.9'
            },
            {
                'title': 'French Final Services PMI',
                'date': 'Wed, Mar 04',
                'time': '08:50 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '49.6',
                'forecast': '49.6',
                'previous': '49.6'
            },
            {
                'title': 'German Final Services PMI',
                'date': 'Wed, Mar 04',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '53.5',
                'forecast': '53.4',
                'previous': '53.4'
            },
            {
                'title': 'Gov Board Member Martin Speaks',
                'date': 'Wed, Mar 04',
                'time': '09:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Final Services PMI',
                'date': 'Wed, Mar 04',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '51.9',
                'forecast': '51.8',
                'previous': '51.8'
            },
            {
                'title': 'Italian Monthly Unemployment Rate',
                'date': 'Wed, Mar 04',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '5.1%',
                'forecast': '5.6%',
                'previous': '5.5%'
            },
            {
                'title': 'Final Services PMI',
                'date': 'Wed, Mar 04',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '53.9',
                'forecast': '53.9',
                'previous': '53.9'
            },
            {
                'title': 'PPI m/m',
                'date': 'Wed, Mar 04',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.7%',
                'forecast': '0.2%',
                'previous': '-0.3%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Wed, Mar 04',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '6.1%',
                'forecast': '6.2%',
                'previous': '6.2%'
            },
            {
                'title': 'ADP Non-Farm Employment Change',
                'date': 'Wed, Mar 04',
                'time': '13:15 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '63K',
                'forecast': '49K',
                'previous': '11K'
            },
            {
                'title': 'Labor Productivity q/q',
                'date': 'Wed, Mar 04',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': '-0.1%',
                'previous': '1.1%'
            },
            {
                'title': 'Final Services PMI',
                'date': 'Wed, Mar 04',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '51.7',
                'forecast': '52.3',
                'previous': '52.3'
            },
            {
                'title': 'ISM Services PMI',
                'date': 'Wed, Mar 04',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '56.1',
                'forecast': '53.5',
                'previous': '53.8'
            },
            {
                'title': 'BOC Gov Macklem Speaks',
                'date': 'Wed, Mar 04',
                'time': '15:30 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Wed, Mar 04',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '3.5M',
                'forecast': 'N/A',
                'previous': '16.0M'
            },
            {
                'title': 'Beige Book',
                'date': 'Wed, Mar 04',
                'time': '19:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Goods Trade Balance',
                'date': 'Wed, Mar 04',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '2.63B',
                'forecast': '3.89B',
                'previous': '3.37B'
            },
            {
                'title': 'Household Spending m/m',
                'date': 'Wed, Mar 04',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.4%',
                'previous': '-0.5%'
            },
            {
                'title': '30-y Bond Auction',
                'date': 'Wed, Mar 04',
                'time': '03:35 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.40|3.7',
                'forecast': 'N/A',
                'previous': '3.62|3.6'
            },
        

            # THURSDAY, MARCH 05
            {
                'title': 'French Industrial Production m/m',
                'date': 'Thu, Mar 05',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.5%',
                'forecast': '0.4%',
                'previous': '-0.5%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Thu, Mar 05',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '3.0%',
                'forecast': '2.9%',
                'previous': '2.9%'
            },
            {
                'title': 'Italian Retail Sales m/m',
                'date': 'Thu, Mar 05',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.6%',
                'forecast': '0.2%',
                'previous': '-0.7%'
            },
            {
                'title': 'Construction PMI',
                'date': 'Thu, Mar 05',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '44.5',
                'forecast': '47.1',
                'previous': '46.4'
            },
            {
                'title': 'German Buba President Nagel Speaks',
                'date': 'Thu, Mar 05',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Thu, Mar 05',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '	-0.1%',
                'forecast': '0.2%',
                'previous': '0.1%'
            },
            {
                'title': 'French 10-y Bond Auction',
                'date': 'Thu, Mar 05',
                'time': '10:18 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '3.39|2.2',
                'forecast': 'N/A',
                'previous': '3.45|2.4'
            },
            {
                'title': 'ECB Monetary Policy Meeting Accounts',
                'date': 'Thu, Mar 05',
                'time': '12:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Challenger Job Cuts y/y',
                'date': 'Thu, Mar 05',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-71.9%',
                'forecast': 'N/A',
                'previous': '117.8%'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Mar 05',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '213K',
                'forecast': '215K',
                'previous': '213K'
            },
            {
                'title': 'Import Prices m/m',
                'date': 'Thu, Mar 05',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Prelim Nonfarm Productivity q/q',
                'date': 'Thu, Mar 05',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '2.8%',
                'forecast': '1.7%',
                'previous': '5.2%'
            },
            {
                'title': 'Prelim Unit Labor Costs q/q',
                'date': 'Thu, Mar 05',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '2.8%',
                'forecast': '2.1%',
                'previous': '-1.8%'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Mar 05',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-132B',
                'forecast': 'N/A',
                'previous': '-52B'
            },
            {
                'title': 'ECB President Lagarde Speaks',
                'date': 'Thu, Mar 05',
                'time': '17:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },

            # FRIDAY, MARCH 06
            {
                'title': 'German Factory Orders m/m',
                'date': 'Fri, Mar 06',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '-3.8%',
                'previous': '7.8%'
            },
            {
                'title': 'Halifax HPI m/m',
                'date': 'Fri, Mar 06',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.4%',
                'previous': '0.8%'
            },
            {
                'title': 'Foreign Currency Reserves',
                'date': 'Fri, Mar 06',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '710B',
                'forecast': 'N/A',
                'previous': '712B'
            },
            {
                'title': 'Final Employment Change q/q',
                'date': 'Fri, Mar 06',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Revised GDP q/q',
                'date': 'Fri, Mar 06',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.3%',
                'previous': '0.3%'
            },
            {
                'title': 'Average Hourly Earnings m/m',
                'date': 'Fri, Mar 06',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.4%',
                'forecast': '0.3%',
                'previous': '0.4%'
            },
            {
                'title': 'Core Retail Sales m/m',
                'date': 'Fri, Mar 06',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.0%',
                'forecast': '0.0%',
                'previous': '0.0%'
            },
            {
                'title': 'Non-Farm Employment Change',
                'date': 'Fri, Mar 06',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '-92K',
                'forecast': '58K',
                'previous': '126K'
            },
            {
                'title': 'Retail Sales m/m',
                'date': 'Fri, Mar 06',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '-0.2%',
                'forecast': '-0.3%',
                'previous': '0.0%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Mar 06',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '4.4%',
                'forecast': '4.3%',
                'previous': '4.3%'
            },
            {
                'title': 'Ivey PMI',
                'date': 'Fri, Mar 06',
                'time': '15:00 UTC',
                'currency': 'CAD',
                'impact': 'medium',
                'actual': '56.6',
                'forecast': '51.2',
                'previous': '50.9'
            },
            {
                'title': 'Business Inventories m/m',
                'date': 'Fri, Mar 06',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.2%',
                'previous': '0.0%'
            },
            {
                'title': 'FOMC Member Daly Speaks',
                'date': 'Fri, Mar 06',
                'time': '17:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Paulson Speaks',
                'date': 'Fri, Mar 06',
                'time': '17:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'RBA Deputy Gov Hauser Speaks',
                'date': 'Fri, Mar 06',
                'time': '18:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'FOMC Member Hammack Speaks',
                'date': 'Fri, Mar 06',
                'time': '18:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Consumer Credit m/m',
                'date': 'Fri, Mar 06',
                'time': '20:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '13.3B',
                'previous': '24.0B'
            },

            # SUNDAY, MARCH 08
            {
                'title': 'Average Cash Earnings y/y',
                'date': 'Sun, Mar 08',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.0%',
                'forecast': '2.5%',
                'previous': '2.4%'
            },
            {
                'title': 'Bank Lending y/y',
                'date': 'Sun, Mar 08',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '4.5%',
                'forecast': '4.4%',
                'previous': '4.4%'
            },
            {
                'title': 'Current Account',
                'date': 'Sun, Mar 08',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.15T',
                'forecast': '3.19T',
                'previous': '2.70T'
            },
            {
                'title': 'CPI y/y',
                'date': 'Mon, Mar 09',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': '1.3%',
                'forecast': '0.9%',
                'previous': '0.2%'
            },
            {
                'title': 'PPI y/y',
                'date': 'Mon, Mar 09',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'medium',
                'actual': '-0.9%',
                'forecast': '-1.1%',
                'previous': '-1.4%'
            },

            # MONDAY, MARCH 09
            {
                'title': 'Leading Indicators',
                'date': 'Mon, Mar 09',
                'time': '05:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '112.4%',
                'forecast': '113.0%',
                'previous': '111.0%'
            },
            {
                'title': 'Economy Watchers Sentiment',
                'date': 'Mon, Mar 09',
                'time': '06:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '48.9',
                'forecast': '48.1',
                'previous': '47.6'
            },
            {
                'title': 'German Factory Orders m/m',
                'date': 'Mon, Mar 09',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-11.1%',
                'forecast': '-4.2%',
                'previous': '6.4%'
            },
            {
                'title': 'German Industrial Production m/m',
                'date': 'Mon, Mar 09',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.5%',
                'forecast': '1.0%',
                'previous': '-1.0%'
            },
            {
                'title': 'SECO Consumer Climate',
                'date': 'Mon, Mar 09',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': '-30',
                'forecast': '-29',
                'previous': '-30'
            },
            {
                'title': 'Sentix Investor Confidence',
                'date': 'Mon, Mar 09',
                'time': '09:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-3.1',
                'forecast': '-3.1',
                'previous': '4.2'
            },
            {
                'title': 'Eurogroup Meetings',
                'date': 'Mon, Mar 09',
                'time': '10:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Westpac Consumer Sentiment',
                'date': 'Mon, Mar 09',
                'time': '23:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '1.2%',
                'forecast': 'N/A',
                'previous': '-2.6%'
            },
            {
                'title': 'Household Spending y/y',
                'date': 'Mon, Mar 09',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '-1.0%',
                'forecast': '2.3%',
                'previous': '-2.6%'
            },
            {
                'title': 'Final GDP Price Index y/y',
                'date': 'Mon, Mar 09',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.4%',
                'forecast': '3.4%',
                'previous': '3.4%'
            },
            {
                'title': 'Final GDP q/q',
                'date': 'Mon, Mar 09',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.1%'
            },
            {
                'title': 'M2 Money Stock y/y',
                'date': 'Mon, Mar 09',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '1.7%',
                'forecast': '1.5%',
                'previous': '1.6%'
            },
            {
                'title': 'BRC Retail Sales Monitor y/y',
                'date': 'Mon, Mar 09',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.7%',
                'forecast': '2.1%',
                'previous': '2.3%'
            },
            {
                'title': 'NAB Business Confidence',
                'date': 'Mon, Mar 09',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '-1',
                'forecast': 'N/A',
                'previous': '4'
            },
            {
                'title': 'Trade Balance',
                'date': 'Mon, Mar 09',
                'time': '03:03 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '1503B',
                'forecast': '950B',
                'previous': '809B'
            },
            {
                'title': 'USD-Denominated Trade Balance',
                'date': 'Mon, Mar 09',
                'time': '03:04 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': '213.6B',
                'forecast': '175.0B',
                'previous': '114.1B'
            },

            # TUESDAY, MARCH 10
            {
                'title': 'Prelim Machine Tool Orders y/y',
                'date': 'Tue, Mar 10',
                'time': '06:00 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '	24.2%',
                'forecast': 'N/A',
                'previous': '25.3%'
            },
            {
                'title': 'German Trade Balance',
                'date': 'Tue, Mar 10',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '21.2B',
                'forecast': '15.6B',
                'previous': '17.4B'
            },
            {
                'title': 'French Trade Balance',
                'date': 'Tue, Mar 10',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-1.8B',
                'forecast': '-4.6B',
                'previous': '-4.3B'
            },
            {
                'title': 'M2 Money Supply y/y',
                'date': 'Tue, Mar 10',
                'time': '08:03 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '8.9%',
                'previous': '9.0%'
            },
            {
                'title': 'New Loans',
                'date': 'Wed, Mar 11',
                'time': '08:03 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '890B',
                'previous': '4710B'
            },
            {
                'title': 'ECOFIN Meetings',
                'date': 'Tue, Mar 10',
                'time': '09:15 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'NFIB Small Business Index',
                'date': 'Tue, Mar 10',
                'time': '10:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '98.8',
                'forecast': '99.8',
                'previous': '99.3'
            },
            {
                'title': 'ADP Weekly Employment Change',
                'date': 'Tue, Mar 10',
                'time': '12:15 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '15.5K',
                'forecast': 'N/A',
                'previous': '12.8K'
            },
            {
                'title': 'Existing Home Sales',
                'date': 'Tue, Mar 10',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '4.09M',
                'forecast': '3.89M',
                'previous': '4.02M'
            },
            {
                'title': 'API Weekly Statistical Bulletin',
                'date': 'Tue, Mar 10',
                'time': '20:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'PPI y/y',
                'date': 'Tue, Mar 10',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '2.0%',
                'forecast': '2.2%',
                'previous': '2.3%'
            },

            # WEDNESDAY, MARCH 11
            {
                'title': 'German Final CPI m/m',
                'date': 'Wed, Mar 11',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'German 10-y Bond Auction',
                'date': 'Wed, Mar 11',
                'time': '10:42 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '2.89|1.2',
                'forecast': 'N/A',
                'previous': '2.73|1.5'
            },
            {
                'title': 'Core CPI m/m',
                'date': 'Wed, Mar 11',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.2%',
                'forecast': '0.2%',
                'previous': '0.3%'
            },
            {
                'title': 'CPI m/m',
                'date': 'Wed, Mar 11',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '0.3%',
                'forecast': '0.3%',
                'previous': '0.2%'
            },
            {
                'title': 'CPI y/y',
                'date': 'Wed, Mar 11',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '2.4%',
                'forecast': '2.4%',
                'previous': '2.4%'
            },
            {
                'title': 'FOMC Member Bowman Speaks',
                'date': 'Wed, Mar 11',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': 'Crude Oil Inventories',
                'date': 'Wed, Mar 11',
                'time': '14:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '3.8M',
                'forecast': 'N/A',
                'previous': '3.5M'
            },
            {
                'title': '10-y Bond Auction',
                'date': 'Wed, Mar 11',
                'time': '17:01 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '4.22|2.4',
                'forecast': 'N/A',
                'previous': '4.18|2.4'
            },
            {
                'title': 'Federal Budget Balance',
                'date': 'Wed, Mar 11',
                'time': '18:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-307.5B',
                'forecast': 'N/A',
                'previous': '-94.6B'
            },
            {
                'title': 'Manufacturing Sales q/q',
                'date': 'Wed, Mar 11',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '0.6%',
                'forecast': 'N/A',
                'previous': '2.7%'
            },
            {
                'title': 'BSI Manufacturing Index',
                'date': 'Wed, Mar 11',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': '3.8',
                'forecast': '5.3',
                'previous': '4.7'
            },
            {
                'title': 'MI Inflation Expectations',
                'date': 'Wed, Mar 11',
                'time': '00:00 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': '5.2%',
                'forecast': 'N/A',
                'previous': '5.0%'
            },
            {
                'title': 'RICS House Price Balance',
                'date': 'Wed, Mar 11',
                'time': '00:01 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-12%',
                'forecast': '-9%',
                'previous': '-10%'
            },

            # THURSDAY, MARCH 12
            {
                'title': 'Italian Quarterly Unemployment Rate',
                'date': 'Thu, Mar 12',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '5.6%',
                'forecast': '6.1%',
                'previous': '6.0%'
            },
            {
                'title': 'BOE Gov Bailey Speaks',
                'date': 'Thu, Mar 12',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            
            {
                'title': 'Building Permits m/m',
                'date': 'Thu, Mar 12',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '4.8%',
                'forecast': '-0.6%',
                'previous': '6.1%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Mar 12',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-3.6B',
                'forecast': '-1.2B',
                'previous': '-1.3B'
            },
            {
                'title': 'Wholesale Sales m/m',
                'date': 'Thu, Mar 12',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': '-1.0%',
                'forecast': '-0.6%',
                'previous': '1.8%'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Mar 12',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': '213K',
                'forecast': '216K',
                'previous': '214K'
            },
            {
                'title': 'Building Permits',
                'date': 'Thu, Mar 12',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.38M',
                'forecast': '1.41M',
                'previous': '1.45M'
            },
            {
                'title': 'Goods Trade Balance',
                'date': 'Thu, Mar 12',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-80.8B',
                'forecast': 'N/A',
                'previous': '-98.5B'
            },
            {
                'title': 'Housing Starts',
                'date': 'Thu, Mar 12',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '1.49M',
                'forecast': '1.34M',
                'previous': '1.39M'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Mar 12',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-54.5B',
                'forecast': '-66.1B',
                'previous': '-72.9B'
            },
            {
                'title': 'CB Leading Index m/m',
                'date': 'Thu, Mar 12',
                'time': '13:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.0%',
                'forecast': 'N/A',
                'previous': '0.0%'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Mar 12',
                'time': '14:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '-38B',
                'forecast': 'N/A',
                'previous': '-132B'
            },
            {
                'title': 'FOMC Member Bowman Speaks',
                'date': 'Thu, Mar 12',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': 'N/A'
            },
            {
                'title': '30-y Bond Auction',
                'date': 'Thu, Mar 12',
                'time': '17:01 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': '4.87|2.5',
                'forecast': 'N/A',
                'previous': '4.75|2.7'
            },
            {
                'title': 'BusinessNZ Manufacturing Index',
                'date': 'Thu, Mar 12',
                'time': '21:30 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '55.0',
                'forecast': 'N/A',
                'previous': '55.1'
            },
            {
                'title': 'Visitor Arrivals m/m',
                'date': 'Thu, Mar 12',
                'time': '21:45 UTC',
                'currency': 'NZD',
                'impact': 'low',
                'actual': '0.9%',
                'forecast': 'N/A',
                'previous': '1.6%'
            },
            

            # FRIDAY, MARCH 13
            {
                'title': 'German WPI m/m',
                'date': 'Fri, Mar 13',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.6%',
                'forecast': '0.4%',
                'previous': '0.9%'
            },
            {
                'title': 'GDP m/m',
                'date': 'Fri, Mar 13',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'high',
                'actual': '0.0%',
                'forecast': '0.2%',
                'previous': '0.1%'
            },
            {
                'title': 'Construction Output m/m',
                'date': 'Fri, Mar 13',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.0%',
                'previous': '-0.5%'
            },
            {
                'title': 'Goods Trade Balance',
                'date': 'Fri, Mar 13',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-14.4B',
                'forecast': '-22.1B',
                'previous': '-22.7B'
            },
            {
                'title': 'Index of Services 3m/3m',
                'date': 'Fri, Mar 13',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.2%',
                'forecast': '0.3%',
                'previous': '0.0%'
            },
            {
                'title': 'Industrial Production m/m',
                'date': 'Fri, Mar 13',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '-0.1%',
                'forecast': '0.3%',
                'previous': '-0.9%'
            },
            {
                'title': 'Manufacturing Production m/m',
                'date': 'Fri, Mar 13',
                'time': '07:00 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': '0.1%',
                'forecast': '0.3%',
                'previous': '-0.5%'
            },
            {
                'title': 'French Final CPI m/m',
                'date': 'Fri, Mar 13',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '0.6%',
                'forecast': '0.7%',
                'previous': '0.7%'
            },
            {
                'title': 'Italian Industrial Production m/m',
                'date': 'Fri, Mar 13',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': '-0.6%',
                'forecast': '0.4%',
                'previous': '-0.4%'
            },
            {
                'title': 'Consumer Inflation Expectations',
                'date': 'Fri, Mar 13',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '3.5%'
            },
            {
                'title': 'Industrial Production m/m',
                'date': 'Fri, Mar 13',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.5%',
                'previous': '-1.4%'
            },
            {
                'title': 'Employment Change',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '11.1K',
                'previous': '-24.8K'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '6.6%',
                'previous': '6.5%'
            },
            {
                'title': 'Capacity Utilization Rate',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '78.4%',
                'previous': '78.5%'
            },
            {
                'title': 'Manufacturing Sales m/m',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'CAD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '-3.2%',
                'previous': '0.6%'
            },
            {
                'title': 'Core PCE Price Index m/m',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.4%',
                'previous': '0.4%'
            },
            {
                'title': 'Prelim GDP q/q',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '1.4%',
                'previous': '1.4%'
            },
            {
                'title': 'Core Durable Goods Orders m/m',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.4%',
                'previous': '0.9%'
            },
            {
                'title': 'Durable Goods Orders m/m',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.5%',
                'previous': '-1.4%'
            },
            {
                'title': 'Prelim GDP Price Index q/q',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '3.6%',
                'previous': '3.6%'
            },
            {
                'title': 'Personal Income m/m',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.4%',
                'previous': '0.3%'
            },
            {
                'title': 'Personal Spending m/m',
                'date': 'Fri, Mar 13',
                'time': '12:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.3%',
                'previous': '0.4%'
            },
            {
                'title': 'JOLTS Job Openings',
                'date': 'Fri, Mar 13',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '6.84M',
                'previous': '6.54M'
            },
            {
                'title': 'Prelim UoM Consumer Sentiment',
                'date': 'Fri, Mar 13',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '55.9',
                'previous': '57.3'
            },
            {
                'title': 'Prelim UoM Inflation Expectations',
                'date': 'Fri, Mar 13',
                'time': '14:00 UTC',
                'currency': 'USD',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '3.5%'
            },
        ]
        
        return events
    
    def _enrich_with_alpha_vantage(self, event: Dict) -> Dict:
        """Enrich event with historical data from AlphaVantage or use provided values"""
        
        # Check if event already has actual/forecast/previous values from ForexFactory
        if 'actual' in event and 'forecast' in event and 'previous' in event:
            return self._format_event(event,
                                    previous=event.get('previous', 'N/A'),
                                    forecast=event.get('forecast', 'TBD'),
                                    actual=event.get('actual', 'TBD'))
        
        av_function = event.get('alpha_vantage_function')
        
        if not av_function:
            # No AlphaVantage data available, use placeholder
            return self._format_event(event, previous='N/A', forecast='TBD', actual='TBD')
        
        # Check cache
        cache_key = f"av_{av_function}"
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if datetime.now().timestamp() - cache_data['timestamp'] < self.cache_ttl:
                data = cache_data['data']
                return self._format_event(event, 
                                         previous=data.get('previous', 'N/A'),
                                         forecast=data.get('forecast', 'TBD'),
                                         actual='TBD')
        
        # Fetch from AlphaVantage
        try:
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': av_function,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                second_latest = data['data'][1] if len(data['data']) > 1 else None
                
                previous_value = latest.get('value', 'N/A')
                second_value = second_latest.get('value', 'N/A') if second_latest else 'N/A'
                
                # Format values based on indicator type
                previous_formatted = self._format_value(av_function, previous_value)
                
                # Generate simple forecast (average of last 2 values or slight change)
                try:
                    if isinstance(previous_value, (int, float)) and second_value != 'N/A':
                        avg = (float(previous_value) + float(second_value)) / 2
                        forecast = self._format_value(av_function, avg)
                    else:
                        forecast = previous_formatted
                except:
                    forecast = 'TBD'
                
                # Cache the result
                self.cache[cache_key] = {
                    'data': {'previous': previous_formatted, 'forecast': forecast},
                    'timestamp': datetime.now().timestamp()
                }
                self._save_cache()
                
                return self._format_event(event, previous=previous_formatted, 
                                         forecast=forecast, actual='TBD')
            else:
                return self._format_event(event, previous='N/A', forecast='TBD', actual='TBD')
                
        except Exception as e:
            print(f"⚠️ AlphaVantage error for {av_function}: {e}")
            return self._format_event(event, previous='N/A', forecast='TBD', actual='TBD')
    
    def _format_value(self, function: str, value) -> str:
        """Format value based on indicator type"""
        if value == 'N/A' or value is None:
            return 'N/A'
        
        try:
            num_value = float(value)
            
            # CPI, inflation - show as index value
            if function in ['CPI', 'INFLATION']:
                return f"{num_value:.1f}"
            
            # Rates - show as percentage
            elif function in ['UNEMPLOYMENT', 'FEDERAL_FUNDS_RATE']:
                return f"{num_value:.1f}%"
            
            # Payroll - show in thousands
            elif function == 'NONFARM_PAYROLL':
                return f"{int(num_value)}K"
            
            # Retail sales, durables - show in millions
            elif function in ['RETAIL_SALES', 'DURABLES']:
                return f"${num_value/1000:.1f}B"
            
            # GDP - show as percentage
            elif function == 'REAL_GDP':
                return f"{num_value:.1f}%"
            
            else:
                return str(num_value)
        except:
            return str(value)
    
    def _get_currency_pairs(self, currency: str) -> List[str]:
        """Generate relevant currency pairs based on the event's currency"""
        currency = currency.upper()
        
        # Forex pair conventions (base/quote order)
        # USD pairs: EURUSD, GBPUSD, AUDUSD, NZDUSD (USD as quote)
        # USD pairs: USDJPY, USDCHF, USDCAD (USD as base)
        # Cross pairs: EURGBP, EURJPY, GBPJPY, etc.
        
        pairs = []
        
        if currency == 'USD':
            # For USD events, show major USD pairs
            pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
        elif currency == 'EUR':
            # For EUR events, show EUR pairs
            pairs = ['EURUSD', 'EURGBP', 'EURJPY', 'EURCHF']
        elif currency == 'GBP':
            # For GBP events, show GBP pairs
            pairs = ['GBPUSD', 'GBPEUR', 'GBPJPY', 'GBPCHF']
        elif currency == 'JPY':
            # For JPY events, show JPY pairs
            pairs = ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY']
        elif currency == 'AUD':
            # For AUD events, show AUD pairs
            pairs = ['AUDUSD', 'AUDJPY', 'AUDNZD', 'AUDCAD']
        elif currency == 'CAD':
            # For CAD events, show CAD pairs
            pairs = ['USDCAD', 'EURCAD', 'GBPCAD', 'AUDCAD']
        elif currency == 'CHF':
            # For CHF events, show CHF pairs
            pairs = ['USDCHF', 'EURCHF', 'GBPCHF', 'AUDCHF']
        elif currency == 'NZD':
            # For NZD events, show NZD pairs
            pairs = ['NZDUSD', 'NZDAUD', 'NZDJPY', 'NZDCAD']
        elif currency == 'CNY':
            # For CNY events, show CNY pairs
            pairs = ['USDCNY', 'EURCNY', 'GBPCNY', 'JPYCNY']
        else:
            # Default: create pairs with major currencies
            major_currencies = ['USD', 'EUR', 'GBP', 'JPY']
            for other_curr in major_currencies:
                if len(pairs) >= 4:
                    break
                if other_curr == currency:
                    continue
                # Follow forex convention: smaller currency code first (alphabetical)
                if currency < other_curr:
                    pairs.append(f"{currency}{other_curr}")
                else:
                    pairs.append(f"{other_curr}{currency}")
        
        return pairs[:4]  # Return max 4 pairs
    
    def _format_event(self, base_event: Dict, previous: str, forecast: str, actual: str) -> Dict:
        """Format event into standard calendar format"""
        # Parse the date to get YYYY-MM-DD format for frontend
        date_str = base_event['date']
        try:
            # Parse "Mon, Oct 13" format
            event_date = datetime.strptime(date_str, '%a, %b %d')
            event_date = event_date.replace(year=datetime.now().year)
            date_yyyy_mm_dd = event_date.strftime('%Y-%m-%d')
        except:
            date_yyyy_mm_dd = datetime.now().strftime('%Y-%m-%d')
        
        # Determine country from currency
        country_map = {
            'USD': 'US', 'EUR': 'EU', 'GBP': 'GB', 'JPY': 'JP',
            'AUD': 'AU', 'CAD': 'CA', 'CHF': 'CH', 'NZD': 'NZ', 'CNY': 'CN'
        }
        
        # Get the event currency
        event_currency = base_event.get('currency', 'USD')
        
        # Generate dynamic currency pairs based on the event's currency
        currency_pairs = self._get_currency_pairs(event_currency)
        
        return {
            'id': f"hybrid_{hash(base_event['title'])}",
            'title': base_event['title'],
            'date': date_yyyy_mm_dd,  # YYYY-MM-DD format for frontend filtering
            'time': base_event['time'],
            'country': country_map.get(event_currency, 'US'),
            'currency': event_currency,
            'impact': base_event.get('impact', 'medium'),
            'previous': previous,
            'expected': forecast,
            'actual': actual,
            'source': 'Hybrid Calendar',
            'status': self._get_status(base_event['date']),
            'type': base_event.get('category', 'Economic Indicator'),
            'currencyPairs': currency_pairs,
            'description': base_event.get('description', ''),
            'raw_data': {
                'date': date_yyyy_mm_dd,
                'time': base_event['time']
            }
        }
    
    def _get_status(self, date_str: str) -> str:
        """Determine event status from date"""
        try:
            event_date = datetime.strptime(date_str, '%a, %b %d')
            event_date = event_date.replace(year=datetime.now().year)
            today = datetime.now()
            
            if event_date.date() < today.date():
                return 'completed'
            elif event_date.date() == today.date():
                return 'today'
            else:
                return 'upcoming'
        except:
            return 'upcoming'
    
    def clear_cache(self):
        """Clear AlphaVantage cache"""
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        print("🗑️ Hybrid calendar cache cleared")

# Global instance
hybrid_economic_calendar = HybridEconomicCalendar()

