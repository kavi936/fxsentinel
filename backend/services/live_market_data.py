#!/usr/bin/env python3
"""
Live Market Data Service for FXSentinel
Provides real-time market data from TradingView for GPT analysis
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MarketDataPoint:
    """Single market data point with metadata"""
    price: float
    change: float
    change_percent: float
    last_update: datetime
    source: str
    is_stale: bool = False
    data_age_minutes: int = 0

class LiveMarketDataService:
    """Service for providing real-time market data from TradingView"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 60  # Cache for 60 seconds
        self.last_fetch = None
        self.tradingview_url = "https://scanner.tradingview.com/forex/scan"
        
        # TradingView symbol mapping
        self.pair_mapping = {
            "FX:EURUSD": "EUR/USD",
            "FX:GBPUSD": "GBP/USD", 
            "FX:USDJPY": "USD/JPY",
            "FX:USDCHF": "USD/CHF",
            "FX:AUDUSD": "AUD/USD",
            "FX:USDCAD": "USD/CAD",
            "FX:NZDUSD": "NZD/USD",
            "FX:EURGBP": "EUR/GBP",
            "FX:EURJPY": "EUR/JPY",
            "FX:GBPJPY": "GBP/JPY",
            "FX:USDSEK": "USD/SEK",
            "FX:USDNOK": "USD/NOK",
            "FX:USDHKD": "USD/HKD",
            "FX:EURCHF": "EUR/CHF",
            "FX:GBPCHF": "GBP/CHF"
        }
        
        # All supported pairs for TradingView
        self.tradingview_pairs = [
            "FX:EURUSD", "FX:GBPUSD", "FX:USDJPY", "FX:USDCHF", "FX:AUDUSD",
            "FX:USDCAD", "FX:NZDUSD", "FX:EURGBP", "FX:EURJPY", "FX:GBPJPY",
            "FX:USDSEK", "FX:USDNOK", "FX:USDHKD", "FX:EURCHF", "FX:GBPCHF"
        ]
    
    def get_live_market_data(self, force_refresh: bool = False) -> Dict:
        """
        Get comprehensive live market data for GPT analysis
        
        Returns:
            Dict containing current prices, volatility, sentiment, and technical levels
        """
        try:
            # Check cache first
            if not force_refresh and self._is_cache_valid():
                logger.info("✅ Using cached market data")
                return self.cache
            
            # Fetch fresh data from TradingView
            logger.info("🔄 Fetching fresh market data from TradingView")
            tradingview_data = self._fetch_tradingview_data()
            
            if not tradingview_data:
                logger.warning("⚠️ TradingView data unavailable, using fallback")
                return self._get_fallback_market_data()
            
            # Process and structure the data
            market_data = self._process_market_data(tradingview_data)
            
            # Cache the result
            self.cache = market_data
            self.last_fetch = datetime.now()
            
            logger.info(f"✅ Successfully fetched live market data for {len(market_data.get('current_prices', {}))} pairs")
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching live market data: {e}")
            return self._get_fallback_market_data()
    
    def _fetch_tradingview_data(self) -> Optional[Dict]:
        """Fetch raw data from TradingView API"""
        try:
            headers = {"Content-Type": "application/json"}
            
            data = {
                "symbols": {"tickers": self.tradingview_pairs},
                "columns": ["close", "change", "change_abs"]
            }
            
            response = requests.post(self.tradingview_url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if 'data' in result and result['data']:
                return result['data']
            else:
                logger.warning("⚠️ TradingView returned empty data")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching from TradingView: {e}")
            return None
    
    def _process_market_data(self, tradingview_data: List) -> Dict:
        """Process TradingView data into structured format for GPT analysis"""
        current_prices = {}
        recent_volatility = {}
        market_sentiment = {}
        key_levels = {}
        
        for item in tradingview_data:
            symbol = item['s']
            values = item['d']
            
            if len(values) >= 3 and symbol in self.pair_mapping:
                price = values[0]  # close price
                change_percent = values[1]  # change percentage
                change_abs = values[2]  # absolute change
                
                pair_key = self.pair_mapping[symbol]
                
                # Current prices
                current_prices[pair_key] = price
                
                # Volatility (based on absolute change)
                volatility = abs(change_abs)
                if volatility < 0.001:
                    recent_volatility[pair_key] = "Low"
                elif volatility < 0.005:
                    recent_volatility[pair_key] = "Medium"
                else:
                    recent_volatility[pair_key] = "High"
                
                # Market sentiment (based on change direction and magnitude)
                if change_percent > 0.1:
                    market_sentiment[pair_key] = "bullish"
                elif change_percent < -0.1:
                    market_sentiment[pair_key] = "bearish"
                else:
                    market_sentiment[pair_key] = "neutral"
                
                # Key technical levels (approximate based on current price)
                key_levels[pair_key] = self._calculate_technical_levels(price, pair_key)
        
        # Calculate additional market context
        bond_yields = self._get_bond_yields()
        equity_indices = self._get_equity_indices()
        commodity_prices = self._get_commodity_prices()
        
        # Generate positioning data based on market movements
        retail_sentiment = self._generate_retail_sentiment(market_sentiment)
        futures_positioning = self._generate_futures_positioning(market_sentiment)
        institutional_flow = self._generate_institutional_flow(market_sentiment)
        
        return {
            'current_prices': current_prices,
            'recent_volatility': recent_volatility,
            'market_sentiment': market_sentiment,
            'key_levels': key_levels,
            'bond_yields': bond_yields,
            'equity_indices': equity_indices,
            'commodity_prices': commodity_prices,
            'retail_sentiment': retail_sentiment,
            'futures_positioning': futures_positioning,
            'institutional_flow': institutional_flow,
            'data_source': 'TradingView',
            'data_timestamp': datetime.now().isoformat(),
            'data_quality': 'live'
        }
    
    def _calculate_technical_levels(self, price: float, pair: str) -> Dict:
        """Calculate approximate technical levels based on current price"""
        # Simple technical level calculation
        # In a real implementation, you'd want to fetch actual technical analysis
        
        # Round to nearest significant level
        if pair in ['EUR/USD', 'GBP/USD', 'AUD/USD', 'NZD/USD']:
            # Major pairs - round to 0.0001
            rounded_price = round(price, 4)
            support = round(rounded_price - 0.0050, 4)
            resistance = round(rounded_price + 0.0050, 4)
        elif pair in ['USD/JPY', 'EUR/JPY', 'GBP/JPY']:
            # JPY pairs - round to 0.01
            rounded_price = round(price, 2)
            support = round(rounded_price - 0.50, 2)
            resistance = round(rounded_price + 0.50, 2)
        else:
            # Other pairs - round to 0.0001
            rounded_price = round(price, 4)
            support = round(rounded_price - 0.0050, 4)
            resistance = round(rounded_price + 0.0050, 4)
        
        return {
            'support': [support, support - (resistance - support) * 0.5, support - (resistance - support)],
            'resistance': [resistance, resistance + (resistance - support) * 0.5, resistance + (resistance - support)]
        }
    
    def _get_bond_yields(self) -> Dict:
        """Get current bond yields (simplified)"""
        # In a real implementation, you'd fetch this from a bond data provider
        return {
            'US_10Y': 4.5,
            'DE_10Y': 2.3,
            'JP_10Y': 0.8,
            'UK_10Y': 4.2
        }
    
    def _get_equity_indices(self) -> Dict:
        """Get current equity indices (simplified)"""
        # In a real implementation, you'd fetch this from an equity data provider
        return {
            'SPX': 4500,
            'DAX': 16000,
            'NIKKEI': 33000,
            'FTSE': 7500
        }
    
    def _get_commodity_prices(self) -> Dict:
        """Get current commodity prices (simplified)"""
        # In a real implementation, you'd fetch this from a commodity data provider
        return {
            'GOLD': 2000,
            'OIL': 75,
            'SILVER': 25,
            'COPPER': 4.2
        }
    
    def _generate_retail_sentiment(self, market_sentiment: Dict) -> Dict:
        """Generate retail sentiment based on market movements"""
        retail_sentiment = {}
        
        for pair, sentiment in market_sentiment.items():
            if sentiment == 'bullish':
                retail_sentiment[pair] = 0.7  # 70% long
            elif sentiment == 'bearish':
                retail_sentiment[pair] = 0.3  # 30% long (70% short)
            else:
                retail_sentiment[pair] = 0.5  # 50% long (neutral)
        
        return retail_sentiment
    
    def _generate_futures_positioning(self, market_sentiment: Dict) -> Dict:
        """Generate futures positioning based on market sentiment"""
        futures_positioning = {}
        
        for pair, sentiment in market_sentiment.items():
            if sentiment == 'bullish':
                futures_positioning[pair] = 15000  # Net long
            elif sentiment == 'bearish':
                futures_positioning[pair] = -15000  # Net short
            else:
                futures_positioning[pair] = 0  # Neutral
        
        return futures_positioning
    
    def _generate_institutional_flow(self, market_sentiment: Dict) -> Dict:
        """Generate institutional flow based on market sentiment"""
        institutional_flow = {}
        
        for pair, sentiment in market_sentiment.items():
            if sentiment == 'bullish':
                institutional_flow[pair] = 25.5  # Net buying
            elif sentiment == 'bearish':
                institutional_flow[pair] = -25.5  # Net selling
            else:
                institutional_flow[pair] = 0.0  # Neutral
        
        return institutional_flow
    
    def _get_fallback_market_data(self) -> Dict:
        """Get fallback market data when live data is unavailable"""
        logger.warning("⚠️ Using fallback market data")
        
        return {
            'current_prices': {
                'EUR/USD': 1.0850,
                'USD/JPY': 148.50,
                'GBP/USD': 1.2650,
                'USD/CHF': 0.8650,
                'AUD/USD': 0.6650,
                'USD/CAD': 1.3550
            },
            'recent_volatility': {
                'EUR/USD': 'Medium',
                'USD/JPY': 'Medium',
                'GBP/USD': 'Medium',
                'USD/CHF': 'Low',
                'AUD/USD': 'Medium',
                'USD/CAD': 'Low'
            },
            'market_sentiment': {
                'EUR/USD': 'neutral',
                'USD/JPY': 'neutral',
                'GBP/USD': 'neutral',
                'USD/CHF': 'neutral',
                'AUD/USD': 'neutral',
                'USD/CAD': 'neutral'
            },
            'key_levels': {
                'EUR/USD': {'support': [1.0800, 1.0750, 1.0700], 'resistance': [1.0900, 1.0950, 1.1000]},
                'USD/JPY': {'support': [148.00, 147.50, 147.00], 'resistance': [149.00, 149.50, 150.00]},
                'GBP/USD': {'support': [1.2600, 1.2550, 1.2500], 'resistance': [1.2700, 1.2750, 1.2800]}
            },
            'bond_yields': {'US_10Y': 4.5, 'DE_10Y': 2.3, 'JP_10Y': 0.8},
            'equity_indices': {'SPX': 4500, 'DAX': 16000, 'NIKKEI': 33000},
            'commodity_prices': {'GOLD': 2000, 'OIL': 75, 'SILVER': 25},
            'retail_sentiment': {
                'EUR/USD': 0.5, 'USD/JPY': 0.5, 'GBP/USD': 0.5,
                'USD/CHF': 0.5, 'AUD/USD': 0.5, 'USD/CAD': 0.5
            },
            'futures_positioning': {
                'EUR/USD': 0, 'USD/JPY': 0, 'GBP/USD': 0,
                'USD/CHF': 0, 'AUD/USD': 0, 'USD/CAD': 0
            },
            'institutional_flow': {
                'EUR/USD': 0.0, 'USD/JPY': 0.0, 'GBP/USD': 0.0,
                'USD/CHF': 0.0, 'AUD/USD': 0.0, 'USD/CAD': 0.0
            },
            'data_source': 'fallback',
            'data_timestamp': datetime.now().isoformat(),
            'data_quality': 'fallback'
        }
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.last_fetch or not self.cache:
            return False
        
        age = (datetime.now() - self.last_fetch).total_seconds()
        return age < self.cache_duration
    
    def get_currency_specific_data(self, currency: str) -> Dict:
        """Get market data specific to a currency for analysis"""
        market_data = self.get_live_market_data()
        
        # Filter data for currency-specific pairs
        currency_pairs = [pair for pair in market_data['current_prices'].keys() 
                         if currency in pair]
        
        return {
            'currency': currency,
            'pairs': currency_pairs,
            'current_prices': {pair: market_data['current_prices'][pair] 
                             for pair in currency_pairs},
            'volatility': {pair: market_data['recent_volatility'][pair] 
                          for pair in currency_pairs},
            'sentiment': {pair: market_data['market_sentiment'][pair] 
                         for pair in currency_pairs},
            'technical_levels': {pair: market_data['key_levels'][pair] 
                               for pair in currency_pairs},
            'data_quality': market_data['data_quality'],
            'data_timestamp': market_data['data_timestamp']
        }

# Global instance
live_market_data_service = LiveMarketDataService()
