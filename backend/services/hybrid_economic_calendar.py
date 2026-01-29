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
                'actual': 'TBD',
                'forecast': '-0.7B',
                'previous': '-0.6B'
            },
            {
                'title': 'Unemployment Claims',
                'date': 'Thu, Jan 29',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '202K',
                'previous': '200K'
            },
            {
                'title': 'Revised Nonfarm Productivity q/q',
                'date': 'Thu, Jan 29',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '4.9%',
                'previous': '4.9%'
            },
            {
                'title': 'Revised Unit Labor Costs q/q',
                'date': 'Thu, Jan 29',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '-1.9%',
                'previous': '-1.9%'
            },
            {
                'title': 'Trade Balance',
                'date': 'Thu, Jan 29',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '-44.5B',
                'previous': '-29.4B'
            },
            {
                'title': 'Factory Orders m/m',
                'date': 'Thu, Jan 29',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.5%',
                'previous': '-1.3%'
            },
            {
                'title': 'Final Wholesale Inventories m/m',
                'date': 'Thu, Jan 29',
                'time': '15:00 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Natural Gas Storage',
                'date': 'Thu, Jan 29',
                'time': '15:30 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': 'N/A',
                'previous': '-120B'
            },
            {
                'title': 'Tokyo Core CPI y/y',
                'date': 'Thu, Jan 29',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '2.2%',
                'previous': '2.3%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Thu, Jan 29',
                'time': '23:30 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '2.6%',
                'previous': '2.6%'
            },
            {
                'title': 'Prelim Industrial Production m/m',
                'date': 'Thu, Jan 29',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '-0.4%',
                'previous': '-2.6%'
            },
            {
                'title': 'Retail Sales y/y',
                'date': 'Thu, Jan 29',
                'time': '23:50 UTC',
                'currency': 'JPY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.7%',
                'previous': '1.0%'
            },
            {
                'title': 'PPI q/q',
                'date': 'Thu, Jan 29',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '1.1%',
                'previous': '1.0%'
            },
            {
                'title': 'Private Sector Credit m/m',
                'date': 'Thu, Jan 29',
                'time': '00:30 UTC',
                'currency': 'AUD',
                'impact': 'low',
                'actual': 'TBD',
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
                'actual': 'TBD',
                'forecast': '-4.5%',
                'previous': '-8.5%'
            },
            {
                'title': 'French Consumer Spending m/m',
                'date': 'Fri, Jan 30',
                'time': '06:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '-0.4%',
                'previous': '-0.3%'
            },
            {
                'title': 'French Flash GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '06:30 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.5%'
            },
            {
                'title': 'German Import Prices m/m',
                'date': 'Fri, Jan 30',
                'time': '07:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '-0.4%',
                'previous': '0.5%'
            },
            {
                'title': 'German Prelim CPI m/m',
                'date': 'Fri, Jan 30',
                'time': '07:29 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.0%',
                'previous': '0.0%'
            },
            {
                'title': 'French Prelim Private Payrolls q/q',
                'date': 'Fri, Jan 30',
                'time': '07:45 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.1%',
                'previous': '-0.1%'
            },
            {
                'title': 'KOF Economic Barometer',
                'date': 'Fri, Jan 30',
                'time': '08:00 UTC',
                'currency': 'CHF',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '103.2',
                'previous': '103.4'
            },
            {
                'title': 'Spanish Flash CPI y/y',
                'date': 'Fri, Jan 30',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '2.4%',
                'previous': '2.9%'
            },
            {
                'title': 'Spanish Flash GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '08:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.6%',
                'previous': '0.6%'
            },
            {
                'title': 'German Unemployment Change',
                'date': 'Fri, Jan 30',
                'time': '08:55 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '5K',
                'previous': '3K'
            },
            {
                'title': 'German Prelim GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'medium',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.0%'
            },
            {
                'title': 'Italian Prelim GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '09:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.0%'
            },
            {
                'title': 'M4 Money Supply m/m',
                'date': 'Fri, Jan 30',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.3%',
                'previous': '0.8%'
            },
            {
                'title': 'Mortgage Approvals',
                'date': 'Fri, Jan 30',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '65K',
                'previous': '65K'
            },
            {
                'title': 'Net Lending to Individuals m/m',
                'date': 'Fri, Jan 30',
                'time': '09:30 UTC',
                'currency': 'GBP',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '6.1B',
                'previous': '6.6B'
            },
            {
                'title': 'Italian Monthly Unemployment Rate',
                'date': 'Fri, Jan 30',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '5.8%',
                'previous': '5.7%'
            },
            {
                'title': 'Prelim Flash GDP q/q',
                'date': 'Fri, Jan 30',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Unemployment Rate',
                'date': 'Fri, Jan 30',
                'time': '10:00 UTC',
                'currency': 'EUR',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '6.3%',
                'previous': '6.3%'
            },
            {
                'title': 'GDP m/m',
                'date': 'Fri, Jan 30',
                'time': '13:30 UTC',
                'currency': 'CAD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.1%',
                'previous': '-0.3%'
            },
            {
                'title': 'Core PPI m/m',
                'date': 'Fri, Jan 30',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.3%',
                'previous': '0.0%'
            },
            {
                'title': 'PPI m/m',
                'date': 'Fri, Jan 30',
                'time': '13:30 UTC',
                'currency': 'USD',
                'impact': 'high',
                'actual': 'TBD',
                'forecast': '0.2%',
                'previous': '0.2%'
            },
            {
                'title': 'Chicago PMI',
                'date': 'Fri, Jan 30',
                'time': '14:45 UTC',
                'currency': 'USD',
                'impact': 'low',
                'actual': 'TBD',
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
                'actual': 'TBD',
                'forecast': '50.2',
                'previous': '50.1'
            },
            {
                'title': 'Non-Manufacturing PMI',
                'date': 'Fri, Jan 30',
                'time': '01:30 UTC',
                'currency': 'CNY',
                'impact': 'low',
                'actual': 'TBD',
                'forecast': '50.8',
                'previous': '50.2'
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

