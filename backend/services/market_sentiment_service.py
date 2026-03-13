#!/usr/bin/env python3
"""
Market Sentiment Service for FXSentinel
Calculates real-time market sentiment from multiple sources
Resets daily for fresh trading sessions
"""

import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class MarketCondition:
    """Market condition data structure"""
    name: str
    value: str  # 'high', 'medium', 'low'
    percentage: float  # 0-100
    detail: str
    trend: str  # 'increasing', 'decreasing', 'stable'

@dataclass
class PairSentiment:
    """Individual pair sentiment data"""
    pair: str
    sentiment: str  # 'bullish', 'bearish', 'neutral'
    percentage: float  # 0-100
    price_change: float
    rsi: float
    volatility: float
    support: Optional[float] = None
    resistance: Optional[float] = None

@dataclass
class MarketDriver:
    """Market driver information"""
    title: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    sentiment: str  # 'positive', 'negative', 'neutral'
    source: str
    timestamp: str

@dataclass
class MarketSentiment:
    """Complete market sentiment data"""
    timestamp: str
    trading_day: str
    market_conditions: List[MarketCondition]
    pairs_sentiment: List[PairSentiment]
    market_drivers: List[MarketDriver]
    market_outlook: str
    confidence_score: float
    data_sources: List[str]
    is_market_closed: bool = False
    market_status: str = "open"  # "open", "closed", "weekend", "holiday"

class MarketSentimentService:
    """Main market sentiment calculation service"""
    
    def __init__(self):
        self.cache_file = "market_sentiment_cache.json"
        self.last_reset_date = None
        self.current_sentiment = None
        self.sentiment_timestamp = None  # Track when sentiment was last calculated
        self.cache_expiration_minutes = 15  # Recalculate every 15 minutes
        
        # VIX cache
        self.vix_cache = None
        self.vix_cache_timestamp = None
        self.vix_cache_expiration_minutes = 30  # Cache VIX for 30 minutes to avoid rate limits (increased due to Yahoo rate limiting)
        
        # Initialize sentiment cache
        self._load_cache()
        self._check_daily_reset()
    
    def _load_cache(self):
        """Load cached sentiment data and VIX cache"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                self.last_reset_date = data.get('last_reset_date')
                self.current_sentiment = data.get('current_sentiment')
                sentiment_timestamp_str = data.get('sentiment_timestamp')
                if sentiment_timestamp_str:
                    self.sentiment_timestamp = datetime.fromisoformat(sentiment_timestamp_str.replace('Z', '+00:00'))
                else:
                    self.sentiment_timestamp = None
                
                # Load VIX cache
                vix_cache_data = data.get('vix_cache')
                if vix_cache_data:
                    self.vix_cache = vix_cache_data.get('data')
                    vix_timestamp_str = vix_cache_data.get('timestamp')
                    if vix_timestamp_str:
                        self.vix_cache_timestamp = datetime.fromisoformat(vix_timestamp_str.replace('Z', '+00:00'))
                    else:
                        self.vix_cache_timestamp = None
                    print(f"🔍 DEBUG: Loaded VIX cache from file: {self.vix_cache}")
                else:
                    self.vix_cache = None
                    self.vix_cache_timestamp = None
                    print(f"🔍 DEBUG: No VIX cache in file, will try to extract from sentiment if available")
                
                logger.info(f"Loaded sentiment cache from {self.last_reset_date}")
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("No sentiment cache found, starting fresh")
            self.last_reset_date = None
            self.current_sentiment = None
            self.sentiment_timestamp = None
            self.vix_cache = None
            self.vix_cache_timestamp = None
    
    def _save_cache(self):
        """Save sentiment data and VIX cache"""
        try:
            data = {
                'last_reset_date': self.last_reset_date,
                'current_sentiment': asdict(self.current_sentiment) if self.current_sentiment else None,
                'sentiment_timestamp': self.sentiment_timestamp.isoformat() if self.sentiment_timestamp else None,
                'vix_cache': {
                    'data': self.vix_cache,
                    'timestamp': self.vix_cache_timestamp.isoformat() if self.vix_cache_timestamp else None
                } if self.vix_cache else None
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sentiment cache: {e}")
    
    def _is_vix_cache_valid(self) -> bool:
        """Check if VIX cache is still valid"""
        if not self.vix_cache or not self.vix_cache_timestamp:
            return False
        
        current_time = datetime.now(timezone.utc)
        time_diff = current_time - self.vix_cache_timestamp
        
        # Check if cache is older than expiration time
        if time_diff.total_seconds() > (self.vix_cache_expiration_minutes * 60):
            logger.info(f"VIX cache expired. Last updated: {self.vix_cache_timestamp}, Age: {time_diff.total_seconds() / 60:.1f} minutes")
            return False
        
        return True
    
    def _check_daily_reset(self):
        """Check if we need to reset for a new trading day"""
        current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        if self.last_reset_date != current_date:
            logger.info(f"New trading day detected: {current_date}, resetting sentiment data")
            self._reset_daily_data()
            self.last_reset_date = current_date
            self._save_cache()
    
    def _check_market_status(self) -> Dict[str, Any]:
        """Check if markets are currently open or closed"""
        current_time = datetime.now(timezone.utc)
        
        # Check if it's weekend
        is_weekend = current_time.weekday() >= 5  # Saturday = 5, Sunday = 6
        
        if is_weekend:
            return {
                'is_market_closed': True,
                'market_status': 'weekend',
                'message': 'Markets are closed for the weekend'
            }
        
        # Check if it's during market hours (simplified - forex markets are open 24/5)
        # But we can check for optimal trading hours
        hour = current_time.hour
        
        # Major forex sessions:
        # Asian session: 00:00-09:00 UTC
        # London session: 08:00-17:00 UTC  
        # New York session: 13:00-22:00 UTC
        
        if 0 <= hour <= 23:  # Forex markets are open 24/5
            return {
                'is_market_closed': False,
                'market_status': 'open',
                'message': 'Markets are open'
            }
        else:
            return {
                'is_market_closed': True,
                'market_status': 'closed',
                'message': 'Markets are closed'
            }
    
    def _reset_daily_data(self):
        """Reset sentiment data for new trading day"""
        self.current_sentiment = None
        self.sentiment_timestamp = None
        logger.info("Daily sentiment data reset completed")
    
    def _is_cache_expired(self) -> bool:
        """Check if cached sentiment data has expired"""
        if not self.current_sentiment or not self.sentiment_timestamp:
            return True
        
        current_time = datetime.now(timezone.utc)
        time_diff = current_time - self.sentiment_timestamp
        expiration_minutes = self.cache_expiration_minutes
        
        # Check if cache is older than expiration time
        if time_diff.total_seconds() > (expiration_minutes * 60):
            logger.info(f"Sentiment cache expired. Last updated: {self.sentiment_timestamp}, Age: {time_diff.total_seconds() / 60:.1f} minutes")
            return True
        
        return False
    
    def _fetch_fear_greed_index(self) -> Optional[Dict[str, Any]]:
        """Fetch Crypto Fear & Greed Index from Alternative.me (no API key). Used as macro risk proxy."""
        try:
            resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if not data or "data" not in data or not data["data"]:
                return None
            item = data["data"][0]
            value = int(item.get("value", 0))
            classification = item.get("value_classification", "Unknown")
            result = {"value": max(0, min(100, value)), "classification": classification}
            logger.info(f"✅ Crypto Fear & Greed: {result['value']} ({result['classification']})")
            return result
        except Exception as e:
            logger.warning(f"⚠️ Fear & Greed index fetch failed: {e}")
            return None
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """Get current market sentiment data"""
        try:
            # Check for daily reset
            self._check_daily_reset()
            
            # Check market status first
            market_status = self._check_market_status()
            
            # If markets are closed, return market closed sentiment
            if market_status['is_market_closed']:
                logger.info(f"Markets are {market_status['market_status']}, returning market closed sentiment")
                return self._get_market_closed_sentiment()
            
            # Check if cache is expired or doesn't exist
            if not self.current_sentiment or self._is_cache_expired():
                logger.info("Calculating fresh market sentiment (cache expired or missing)")
                try:
                    self.current_sentiment = self._calculate_market_sentiment()
                    self.sentiment_timestamp = datetime.now(timezone.utc)
                    self._save_cache()
                    logger.info("✅ Successfully calculated and cached fresh sentiment data")
                except Exception as calc_error:
                    logger.error(f"❌ Failed to calculate fresh sentiment: {calc_error}")
                    # If we have cached data, use it even if expired (better than defaults)
                    if self.current_sentiment:
                        logger.warning("⚠️ Using expired cache data due to calculation failure (better than defaults)")
                    else:
                        logger.error("❌ No cached data available, returning fallback defaults")
                        return self._get_fallback_sentiment()
            else:
                logger.info(f"Using cached sentiment data (age: {(datetime.now(timezone.utc) - self.sentiment_timestamp).total_seconds() / 60:.1f} minutes)")
            
            # Return formatted data for frontend and attach Fear & Greed index
            result = self._format_for_frontend(self.current_sentiment)
            result["fng"] = self._fetch_fear_greed_index()
            return result
            
        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            import traceback
            traceback.print_exc()
            # Try to use cached data if available
            if self.current_sentiment:
                logger.warning("⚠️ Using cached sentiment data due to error (better than defaults)")
                result = self._format_for_frontend(self.current_sentiment)
                result["fng"] = self._fetch_fear_greed_index()
                return result
            fallback = self._get_fallback_sentiment()
            fallback["fng"] = self._fetch_fear_greed_index()
            return fallback
    
    def _calculate_market_sentiment(self) -> MarketSentiment:
        """Calculate comprehensive market sentiment"""
        logger.info("Calculating fresh market sentiment...")
        
        # Check market status first
        market_status = self._check_market_status()
        
        # Get forex data once and reuse it (avoids redundant API calls)
        from app import get_tradingview_prices
        logger.info("🔍 Fetching forex data from TradingView...")
        forex_data = get_tradingview_prices()
        
        if not forex_data:
            logger.error("❌ Failed to fetch forex data from TradingView - cannot calculate sentiment")
            # Don't return defaults - raise an exception so we can use cached data if available
            raise ValueError("Failed to fetch forex data from TradingView API")
        
        logger.info(f"✅ Successfully fetched {len(forex_data)} pairs from TradingView")
        
        # Fetch VIX data once and reuse it
        vix_data = self._fetch_real_vix()
        
        # Get market conditions (pass forex_data and vix_data to avoid fetching again)
        market_conditions = self._calculate_market_conditions(forex_data, vix_data)
        
        # Get pairs sentiment (pass forex_data to avoid fetching again)
        pairs_sentiment = self._calculate_pairs_sentiment(forex_data)
        
        # Verify we got real data, not defaults
        if pairs_sentiment:
            first_pair = pairs_sentiment[0]
            is_default = (first_pair.price_change == 0.0 and 
                         first_pair.rsi == 50.0 and 
                         first_pair.volatility == 10.0)
            if is_default:
                logger.warning("⚠️ Calculated pairs sentiment contains default values - this should not happen")
            else:
                logger.info(f"✅ Calculated pairs sentiment with real values (e.g., {first_pair.pair}: {first_pair.price_change:.4f}%)")
        
        # Get market drivers
        market_drivers = self._get_market_drivers()
        
        # Generate market outlook
        market_outlook = self._generate_market_outlook(market_conditions, pairs_sentiment, market_drivers)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(market_conditions, pairs_sentiment)
        
        return MarketSentiment(
            timestamp=datetime.now(timezone.utc).isoformat(),
            trading_day=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            market_conditions=market_conditions,
            pairs_sentiment=pairs_sentiment,
            market_drivers=market_drivers,
            market_outlook=market_outlook,
            confidence_score=confidence_score,
            data_sources=['TradingView', 'News Analysis', 'Technical Indicators'],
            is_market_closed=market_status['is_market_closed'],
            market_status=market_status['market_status']
        )
    
    def _calculate_market_conditions(self, forex_data: Optional[Dict] = None, vix_data: Optional[Dict[str, float]] = None) -> List[MarketCondition]:
        """Calculate market conditions (volatility, risk appetite)
        
        Args:
            forex_data: Pre-fetched forex data (optional, will fetch if not provided)
            vix_data: Pre-fetched VIX data (optional, will fetch if not provided)
        """
        try:
            # Get forex price data if not provided
            if forex_data is None:
                from app import get_tradingview_prices
                forex_data = get_tradingview_prices()
            
            if not forex_data:
                return self._get_default_market_conditions()
            
            # Fetch VIX data if not provided
            if vix_data is None:
                vix_data = self._fetch_real_vix()
            
            # Calculate volatility environment (pass VIX data to avoid fetching again)
            volatility = self._calculate_volatility(forex_data, vix_data)
            
            # Calculate risk appetite
            risk_appetite = self._calculate_risk_appetite(forex_data)
            
            return [
                MarketCondition(
                    name="Volatility Environment",
                    value=volatility['level'],
                    percentage=volatility['percentage'],
                    detail=f"VIX: {volatility['vix']:.1f} ({volatility['change']:+.1f})",
                    trend=volatility['trend']
                ),
                MarketCondition(
                    name="Risk Appetite",
                    value=risk_appetite['level'],
                    percentage=risk_appetite['percentage'],
                    detail=f"Safe Havens: {risk_appetite['safe_havens']}",
                    trend=risk_appetite['trend']
                )
            ]
            
        except Exception as e:
            logger.error(f"Error calculating market conditions: {e}")
            return self._get_default_market_conditions()
    
    def _fetch_vix_from_alpha_vantage(self) -> Optional[Dict[str, float]]:
        """Fetch VIX data from Alpha Vantage API"""
        try:
            # Try to get Alpha Vantage key from app module or use the provided key
            alpha_vantage_key = None
            try:
                # Try to import the function from app module
                import sys
                if 'app' in sys.modules:
                    from app import get_next_alpha_vantage_key
                    alpha_vantage_key = get_next_alpha_vantage_key()
            except (ImportError, AttributeError):
                pass
            
            # Fallback to environment variable or hardcoded key
            if not alpha_vantage_key:
                import os
                alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY') or 'ST66PYRS63MNI1HM'
            
            if not alpha_vantage_key:
                logger.warning("⚠️ Alpha Vantage API key not available")
                return None
            
            logger.debug("🔍 Fetching VIX from Alpha Vantage API...")
            
            # Alpha Vantage TIME_SERIES_DAILY endpoint for VIX
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=^VIX&apikey={alpha_vantage_key}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"❌ Alpha Vantage API error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"⚠️ Alpha Vantage API rate limit: {data['Note']}")
                return None
            
            # Parse the time series data
            if 'Time Series (Daily)' not in data:
                logger.warning("⚠️ Alpha Vantage response missing Time Series data")
                return None
            
            time_series = data['Time Series (Daily)']
            
            if not time_series:
                logger.warning("⚠️ Alpha Vantage returned empty time series")
                return None
            
            # Get the most recent date (first key in the sorted dict)
            dates = sorted(time_series.keys(), reverse=True)
            if len(dates) < 2:
                logger.warning("⚠️ Alpha Vantage returned insufficient data points")
                return None
            
            # Get current and previous day data
            current_date = dates[0]
            previous_date = dates[1]
            
            current_data = time_series[current_date]
            previous_data = time_series[previous_date]
            
            # Extract closing prices
            current_price = float(current_data['4. close'])
            previous_price = float(previous_data['4. close'])
            change = current_price - previous_price
            
            if current_price > 0:
                vix_data = {
                    'vix': current_price,
                    'change': change,
                    'previous_close': previous_price
                }
                
                # Cache the VIX data
                self.vix_cache = vix_data
                self.vix_cache_timestamp = datetime.now(timezone.utc)
                self._save_cache()
                
                logger.info(f"✅ Successfully fetched VIX from Alpha Vantage: {current_price:.2f} ({change:+.2f})")
                return vix_data
            
            logger.warning("⚠️ Invalid VIX price from Alpha Vantage (price <= 0)")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Alpha Vantage API request failed: {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            logger.warning(f"⚠️ Error parsing Alpha Vantage VIX data: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching VIX from Alpha Vantage: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fetch_real_vix(self) -> Optional[Dict[str, float]]:
        """Fetch real VIX data from Alpha Vantage (primary) or Yahoo Finance (fallback) with caching"""
        # Check if we have valid cached VIX data
        if self._is_vix_cache_valid():
            logger.info(f"✅ Using cached VIX data: {self.vix_cache['vix']:.2f} ({self.vix_cache['change']:+.2f})")
            print(f"✅ DEBUG: Using valid cached VIX: {self.vix_cache}")
            return self.vix_cache
        
        # If cache exists but expired, check if it's recent enough to use (within 2 hours)
        # This helps when APIs are rate limiting
        if self.vix_cache and self.vix_cache_timestamp:
            current_time = datetime.now(timezone.utc)
            time_diff = current_time - self.vix_cache_timestamp
            hours_old = time_diff.total_seconds() / 3600
            
            if hours_old < 2:  # Use cache if less than 2 hours old
                logger.info(f"⚠️ VIX cache expired but recent ({hours_old:.1f} hours old). Using cached data to avoid rate limits.")
                print(f"⚠️ DEBUG: Using expired but recent cache ({hours_old:.1f}h old): {self.vix_cache}")
                return self.vix_cache
        
        # Try Alpha Vantage first
        alpha_vantage_vix = self._fetch_vix_from_alpha_vantage()
        if alpha_vantage_vix:
            return alpha_vantage_vix
        
        # Fallback to Yahoo Finance
        try:
            import yfinance as yf
            from yfinance.exceptions import YFRateLimitError
            
            logger.info("🔄 Fetching fresh VIX data from Yahoo Finance...")
            print(f"🔍 DEBUG: Attempting to fetch VIX from yfinance...")
            
            # Fetch VIX data using yfinance (ticker symbol: ^VIX)
            vix_ticker = yf.Ticker("^VIX")
            print(f"🔍 DEBUG: VIX ticker created: {vix_ticker}")
            
            # Get recent history for change calculation (2 days to get current and previous)
            hist = vix_ticker.history(period="2d")
            print(f"🔍 DEBUG: VIX history fetched - Empty: {hist.empty}, Length: {len(hist)}")
            
            if hist.empty or len(hist) < 1:
                logger.warning("⚠️ No VIX history data available from yfinance")
                print(f"⚠️ DEBUG: VIX history is empty or has no data")
                # Try to use cached data even if expired as fallback
                if self.vix_cache:
                    logger.info(f"Using expired VIX cache as fallback: {self.vix_cache['vix']:.2f}")
                    print(f"🔍 DEBUG: Using expired cache: {self.vix_cache}")
                    return self.vix_cache
                print(f"❌ DEBUG: No VIX cache available, returning None")
                return None
            
            # Get current price (most recent close)
            current_price = float(hist['Close'].iloc[-1])
            print(f"🔍 DEBUG: Current VIX price: {current_price}")
            
            # Calculate change from previous close
            if len(hist) >= 2:
                previous_close = float(hist['Close'].iloc[-2])
                change = current_price - previous_close
                print(f"🔍 DEBUG: Previous close: {previous_close}, Change: {change}")
            else:
                # If only one day of data, try to get previous close from info
                try:
                    info = vix_ticker.info
                    previous_close = info.get('previousClose', current_price)
                    change = current_price - previous_close
                    print(f"🔍 DEBUG: Using info previousClose: {previous_close}, Change: {change}")
                except Exception as e:
                    # If info fetch fails, assume no change
                    previous_close = current_price
                    change = 0.0
                    print(f"⚠️ DEBUG: Failed to get previousClose from info: {e}, assuming no change")
            
            if current_price > 0:
                vix_data = {
                    'vix': current_price,
                    'change': change,
                    'previous_close': previous_close
                }
                
                # Cache the VIX data
                self.vix_cache = vix_data
                self.vix_cache_timestamp = datetime.now(timezone.utc)
                self._save_cache()
                
                logger.info(f"✅ Successfully fetched and cached VIX data: {current_price:.2f} ({change:+.2f})")
                print(f"✅ DEBUG: VIX data cached successfully: {vix_data}")
                return vix_data
            
            logger.warning("⚠️ Invalid VIX price data from yfinance (price <= 0)")
            print(f"⚠️ DEBUG: Invalid VIX price: {current_price}")
            # Try to use cached data even if expired as fallback
            if self.vix_cache:
                logger.info("Using expired VIX cache as fallback")
                return self.vix_cache
            return None
            
        except ImportError:
            logger.error("❌ yfinance library not installed. Install with: pip install yfinance")
            print(f"❌ DEBUG: yfinance not installed")
            # Try to use cached data as fallback
            if self.vix_cache:
                logger.info("Using cached VIX data as fallback")
                return self.vix_cache
            return None
        except YFRateLimitError:
            logger.warning("⚠️ Yahoo Finance rate limit reached. Using cached VIX data if available.")
            print(f"⚠️ DEBUG: Rate limit error from yfinance - Yahoo Finance is rate limiting requests")
            print(f"⚠️ DEBUG: This is common with yfinance. Using cached data or fallback.")
            # Use cached data even if expired when rate limited (extend cache validity)
            if self.vix_cache:
                logger.info(f"✅ Using cached VIX data due to rate limit: {self.vix_cache['vix']:.2f} ({self.vix_cache['change']:+.2f})")
                print(f"✅ DEBUG: Returning cached VIX: {self.vix_cache}")
                # Extend cache timestamp to prevent immediate retry
                self.vix_cache_timestamp = datetime.now(timezone.utc)
                return self.vix_cache
            logger.warning("⚠️ No cached VIX data available. Will use fallback calculation.")
            print(f"⚠️ DEBUG: No cache available, will fall back to forex-based calculation")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching VIX data from yfinance: {e}")
            print(f"❌ DEBUG: Exception fetching VIX: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Try to use cached data as fallback
            if self.vix_cache:
                logger.info("Using cached VIX data due to error")
                return self.vix_cache
            return None
    
    def _calculate_volatility(self, forex_data: Dict, vix_data: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Calculate volatility environment from forex data and real VIX
        
        Args:
            forex_data: Dictionary of forex pair data
            vix_data: Pre-fetched VIX data (optional, will fetch if not provided)
        """
        try:
            # Use provided VIX data or fetch if not provided
            if vix_data is None:
                vix_data = self._fetch_real_vix()
            print(f"🔍 DEBUG: _calculate_volatility - vix_data received: {vix_data}")
            
            if vix_data:
                # Use real VIX data
                vix_value = vix_data['vix']
                vix_change = vix_data['change']
                print(f"✅ DEBUG: Using real VIX data - Value: {vix_value}, Change: {vix_change}")
                
                # Continuous volatility percentage (0-100): VIX 0 → 0%, VIX 50 → 100%, linear scale
                VIX_SCALE = 50.0
                percentage = float(np.clip((vix_value / VIX_SCALE) * 100.0, 0, 100))
                # Derive level from percentage for display/color
                if percentage >= 66:
                    level = 'high'
                elif percentage >= 33:
                    level = 'medium'
                else:
                    level = 'low'
                
                # Determine trend
                if vix_change > 1.0:
                    trend = 'increasing'
                elif vix_change < -1.0:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
                
                return {
                    'level': level,
                    'percentage': percentage,
                    'vix': vix_value,
                    'change': vix_change,
                    'trend': trend
                }
            
            # Fallback: Calculate from forex volatility if VIX API fails
            logger.warning("⚠️ Using fallback VIX calculation from forex volatility (yfinance fetch failed)")
            print(f"⚠️ DEBUG: Falling back to forex-based VIX calculation")
            volatilities = []
            for pair_data in forex_data.values():
                if 'change' in pair_data:
                    volatilities.append(abs(pair_data['change']))
            
            if not volatilities:
                return {'level': 'medium', 'percentage': 50, 'vix': 15.0, 'change': 0.0, 'trend': 'stable'}
            
            avg_volatility = np.mean(volatilities)
            # Map forex-based volatility to approximate VIX scale (e.g. 0.2 daily % → ~20 VIX) for percentage
            vix_approx = min(50, avg_volatility * 100)  # daily % to rough VIX scale
            vix = max(10.0, min(30.0, 10.0 + vix_approx))
            percentage = float(np.clip((vix / 50.0) * 100.0, 0, 100))
            if percentage >= 66:
                level = 'high'
            elif percentage >= 33:
                level = 'medium'
            else:
                level = 'low'
            
            return {
                'level': level,
                'percentage': percentage,
                'vix': vix,
                'change': np.random.uniform(-2, 2),  # Simulated VIX change
                'trend': 'stable'
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return {'level': 'medium', 'percentage': 50, 'vix': 15.0, 'change': 0.0, 'trend': 'stable'}
    
    def _calculate_risk_appetite(self, forex_data: Dict) -> Dict[str, Any]:
        """Calculate risk appetite based on daily percentage movement of safe haven currencies"""
        try:
            logger.debug("🔍 DEBUG: Starting risk appetite calculation...")
            logger.debug(f"🔍 DEBUG: Available forex pairs: {list(forex_data.keys()) if forex_data else 'None'}")
            
            # Safe haven currency pairs - these strengthen during risk-off
            # Note: For USD pairs, we look at JPY/CHF strengthening (USD weakening)
            # For EUR/GBP pairs with JPY/CHF, we look at JPY/CHF strengthening
            safe_haven_pairs = {
                'USDJPY': 'JPY',  # JPY strengthening = USDJPY down
                'USDCHF': 'CHF',  # CHF strengthening = USDCHF down
                'EURJPY': 'JPY',  # JPY strengthening = EURJPY down
                'GBPJPY': 'JPY',  # JPY strengthening = GBPJPY down
                'EURCHF': 'CHF',  # CHF strengthening = EURCHF down
                'GBPCHF': 'CHF'   # CHF strengthening = GBPCHF down
            }
            
            safe_haven_percentages = []
            active_safe_havens = []
            pair_details = []
            
            for pair, currency in safe_haven_pairs.items():
                if pair in forex_data:
                    pair_data = forex_data[pair]
                    logger.debug(f"🔍 DEBUG: {pair} data keys: {list(pair_data.keys())}")
                    
                    # Check for changePercent (preferred) or calculate from change and price
                    if 'changePercent' in pair_data:
                        change_percent = pair_data['changePercent']
                        logger.debug(f"🔍 DEBUG: {pair} - changePercent: {change_percent}")
                    elif 'change' in pair_data and 'price' in pair_data:
                        # Calculate percentage change if not provided
                        change_abs = pair_data['change']
                        price = pair_data['price']
                        if price != 0:
                            change_percent = (change_abs / price) * 100
                            logger.debug(f"🔍 DEBUG: {pair} - calculated changePercent: {change_percent:.4f}% (from change: {change_abs}, price: {price})")
                        else:
                            logger.warning(f"⚠️ {pair} has zero price, skipping")
                            continue
                    else:
                        logger.warning(f"⚠️ {pair} missing changePercent or change/price data")
                        continue
                    
                    # For USD pairs: negative changePercent = JPY/CHF strengthening (risk-off)
                    # For EUR/GBP pairs: negative changePercent = JPY/CHF strengthening (risk-off)
                    # We want to measure how much JPY/CHF is strengthening (negative changePercent)
                    # So we take the absolute value of negative changes (safe haven strengthening)
                    
                    if pair.startswith('USD'):
                        # For USDJPY/USDCHF: negative changePercent = JPY/CHF strengthening (risk-off)
                        # We want to capture JPY/CHF strengthening, so use absolute value of negative changes
                        if change_percent < 0:
                            # JPY/CHF is strengthening (risk-off signal)
                            movement = abs(change_percent)
                        else:
                            # USD is strengthening (risk-on, safe havens weakening)
                            movement = 0  # Don't count USD strengthening as safe haven movement
                    else:
                        # For EURJPY/GBPJPY/EURCHF/GBPCHF: negative changePercent = JPY/CHF strengthening
                        if change_percent < 0:
                            # JPY/CHF is strengthening (risk-off signal)
                            movement = abs(change_percent)
                        else:
                            # EUR/GBP strengthening vs JPY/CHF (risk-on)
                            movement = 0  # Don't count as safe haven movement
                    
                    safe_haven_percentages.append(movement)
                    pair_details.append(f"{pair}: {change_percent:.4f}% -> safe haven movement: {movement:.4f}%")
                    
                    if movement > 0.05:  # Significant safe haven strengthening (>0.05%)
                        active_safe_havens.append(currency)
                        logger.debug(f"🔍 DEBUG: {pair} ({currency}) showing safe haven strength: {movement:.4f}%")
            
            logger.debug(f"🔍 DEBUG: Pair details: {pair_details}")
            logger.debug(f"🔍 DEBUG: Safe haven percentages collected: {safe_haven_percentages}")
            logger.debug(f"🔍 DEBUG: Active safe havens: {active_safe_havens}")
            
            if not safe_haven_percentages:
                logger.warning("⚠️ No safe haven percentage data available, using default")
                return {'level': 'medium', 'percentage': 50, 'safe_havens': 'JPY, CHF', 'trend': 'stable'}
            
            # Calculate average daily percentage movement of safe havens
            avg_safe_haven_movement = np.mean(safe_haven_percentages)
            logger.debug(f"🔍 DEBUG: Average safe haven movement: {avg_safe_haven_movement:.4f}%")
            
            # Continuous risk appetite percentage (0-100): 0% safe-haven movement = 100% risk appetite,
            # high safe-haven movement = low risk appetite. Scale: 0.5% movement → 0%, 0% → 100%.
            RISK_OFF_THRESHOLD = 0.5  # avg movement >= 0.5% treated as full risk-off (0% appetite)
            raw_pct = 100.0 - (avg_safe_haven_movement / RISK_OFF_THRESHOLD) * 100.0
            percentage = float(np.clip(raw_pct, 0, 100))
            
            # Derive level from continuous percentage for display/color (same buckets, now from accurate %)
            if percentage >= 66:
                level = 'high'
            elif percentage >= 33:
                level = 'medium'
            else:
                level = 'low'
            
            safe_havens_str = ', '.join(set(active_safe_havens)) if active_safe_havens else 'JPY, CHF'
            if not safe_havens_str and percentage < 80:
                safe_havens_str = 'JPY, CHF'
            if level == 'high' and not active_safe_havens:
                safe_havens_str = 'None'
            logger.info(f"✅ Risk Appetite: {level.upper()} ({percentage:.1f}%) - Safe haven movement: {avg_safe_haven_movement:.4f}%")
            
            result = {
                'level': level,
                'percentage': percentage,
                'safe_havens': safe_havens_str if safe_havens_str else 'JPY, CHF',
                'trend': 'stable'
            }
            logger.debug(f"🔍 DEBUG: Risk appetite result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error calculating risk appetite: {e}")
            import traceback
            traceback.print_exc()
            return {'level': 'medium', 'percentage': 50, 'safe_havens': 'JPY, CHF', 'trend': 'stable'}
    
    def _calculate_pairs_sentiment(self, forex_data: Optional[Dict] = None) -> List[PairSentiment]:
        """Calculate sentiment for individual currency pairs
        
        Args:
            forex_data: Pre-fetched forex data (optional, will fetch if not provided)
        """
        try:
            # Get forex data if not provided
            if forex_data is None:
                logger.info("🔍 Fetching forex data from TradingView API...")
                from app import get_tradingview_prices
                forex_data = get_tradingview_prices()
                logger.info(f"🔍 TradingView API returned: {forex_data is not None}, Type: {type(forex_data)}")
                if forex_data:
                    logger.info(f"✅ Received {len(forex_data)} pairs from TradingView")
                    logger.info(f"   Pairs: {list(forex_data.keys())}")
                else:
                    logger.warning("⚠️ TradingView API returned None or empty data")
            
            if not forex_data:
                logger.warning("⚠️ No forex data available, returning default pairs sentiment")
                return self._get_default_pairs_sentiment()
            
            pairs_sentiment = []
            major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
            
            logger.info(f"🔍 Calculating sentiment for major pairs: {major_pairs}")
            logger.info(f"🔍 Available pairs in forex_data: {list(forex_data.keys())}")
            
            for pair in major_pairs:
                if pair in forex_data:
                    data = forex_data[pair]
                    
                    # Get price and change data
                    current_price = data.get('price', 0)
                    price_change_abs = data.get('change', 0)
                    
                    # Calculate changePercent if not provided
                    if 'changePercent' in data:
                        price_change_percent = data['changePercent']
                    elif current_price > 0:
                        # Calculate from absolute change and price
                        price_change_percent = (price_change_abs / current_price) * 100
                    else:
                        price_change_percent = 0
                    
                    # Calculate sentiment from percentage change
                    if price_change_percent > 0.1:  # 0.1% change
                        sentiment = 'bullish'
                        percentage = min(85, 50 + abs(price_change_percent) * 50)
                    elif price_change_percent < -0.1:  # -0.1% change
                        sentiment = 'bearish'
                        percentage = max(15, 50 - abs(price_change_percent) * 50)
                    else:
                        sentiment = 'neutral'
                        percentage = 50
                    
                    # Calculate RSI (simplified momentum-based RSI)
                    # RSI formula: 100 - (100 / (1 + RS))
                    # RS = Average Gain / Average Loss
                    # Since we only have daily change, we use a momentum approximation
                    # Strong positive momentum = higher RSI, strong negative = lower RSI
                    # RSI ranges: 0-30 (oversold), 30-50 (bearish), 50-70 (bullish), 70-100 (overbought)
                    
                    if price_change_percent > 0.5:
                        # Very strong bullish momentum (>0.5%) - Overbought territory
                        rsi = min(100, 75 + (price_change_percent - 0.5) * 25)  # 75-100 range
                    elif price_change_percent > 0.2:
                        # Strong bullish momentum (0.2-0.5%) - Bullish
                        rsi = 65 + (price_change_percent - 0.2) * 33.33  # 65-75 range
                    elif price_change_percent > 0.1:
                        # Moderate bullish momentum (0.1-0.2%) - Weak bullish
                        rsi = 55 + (price_change_percent - 0.1) * 100  # 55-65 range
                    elif price_change_percent > -0.1:
                        # Neutral range (-0.1% to 0.1%) - Neutral
                        rsi = 45 + (price_change_percent + 0.1) * 50  # 40-50 range (centered at 45)
                    elif price_change_percent > -0.2:
                        # Moderate bearish momentum (-0.2% to -0.1%) - Weak bearish
                        rsi = 35 + (price_change_percent + 0.2) * 100  # 35-45 range
                    elif price_change_percent > -0.5:
                        # Strong bearish momentum (-0.5% to -0.2%) - Bearish
                        rsi = 20 + (price_change_percent + 0.5) * 50  # 20-35 range
                    else:
                        # Very strong bearish momentum (<-0.5%) - Oversold territory
                        rsi = max(0, 20 + (price_change_percent + 0.5) * 40)  # 0-20 range
                    
                    # Clamp RSI to valid range
                    rsi = max(0, min(100, rsi))
                    
                    # Calculate volatility (annualized volatility approximation)
                    # Volatility = standard deviation of returns
                    # Since we only have daily change, we approximate as:
                    # Daily volatility = abs(changePercent)
                    # Annualized volatility ≈ daily_volatility × sqrt(252 trading days)
                    # For display, we show daily volatility percentage
                    daily_volatility = abs(price_change_percent)
                    # Scale to show as percentage (already a percentage, so just use it)
                    volatility = daily_volatility
                    
                    pairs_sentiment.append(PairSentiment(
                        pair=pair,
                        sentiment=sentiment,
                        percentage=percentage,
                        price_change=price_change_percent,  # Percentage value (e.g., 0.15 for 0.15%)
                        rsi=rsi,
                        volatility=volatility
                    ))
                    logger.info(f"✅ Calculated sentiment for {pair}: change={price_change_percent:.4f}%, RSI={rsi:.1f}, Vol={volatility:.2f}%")
                else:
                    logger.warning(f"⚠️ Pair {pair} not found in forex_data, skipping")
            
            if not pairs_sentiment:
                logger.warning("⚠️ No pairs sentiment calculated, returning defaults")
                return self._get_default_pairs_sentiment()
            
            logger.info(f"✅ Successfully calculated sentiment for {len(pairs_sentiment)} pairs")
            return pairs_sentiment
            
        except Exception as e:
            logger.error(f"Error calculating pairs sentiment: {e}")
            import traceback
            traceback.print_exc()
            return self._get_default_pairs_sentiment()
    
    def _get_market_drivers(self) -> List[MarketDriver]:
        """Get current market drivers from news and events"""
        try:
            # Updated market drivers based on current market dynamics
            return [
                MarketDriver(
                    title="Monetary Policy Divergence & Interest Rate Differentials",
                    description="As global inflation normalizes, major central banks are entering different phases of the policy cycle. The Federal Reserve is expected to gradually ease policy, while others (notably the Bank of Japan) are exiting ultra-loose stances, and some (BoE/ECB) remain cautious due to sticky inflation. These differences in policy direction directly shape capital flows and yield attractiveness across currencies. Impact on Forex Markets: Narrowing US yield advantage → structural USD weakness over time. Reduced carry appeal → USD/JPY volatility and downside bias. Policy divergence → trend opportunities in G10 FX via rate spreads.",
                    impact="high",
                    sentiment="neutral",
                    source="Central Bank Policy Analysis",
                    timestamp=datetime.now(timezone.utc).isoformat()
                ),
                MarketDriver(
                    title="Global Growth Divergence & Risk Sentiment",
                    description="Economic growth prospects are diverging across regions. While developed economies face slower, late-cycle growth, select emerging markets and Asia continue to show stronger structural momentum. This divergence drives risk-on vs risk-off capital allocation, influencing demand for higher-beta currencies versus safe havens. Impact on Forex Markets: Risk-on periods → EM FX and high-beta currencies outperform. Risk-off shocks → JPY, CHF, and USD strengthen. FX trends increasingly driven by relative growth expectations, not absolute growth.",
                    impact="high",
                    sentiment="neutral",
                    source="Economic Growth Analysis",
                    timestamp=datetime.now(timezone.utc).isoformat()
                ),
                MarketDriver(
                    title="Geopolitics, Trade Policy & Commodity Volatility",
                    description="Geopolitical tensions, trade fragmentation, and energy supply risks remain elevated heading into 2026. These factors introduce non-linear shocks to FX markets, often overriding fundamentals in the short term. Commodity prices, in particular, act as transmission mechanisms into currency markets. Impact on Forex Markets: Heightened uncertainty → safe-haven demand spikes. Commodity swings → AUD, CAD, NOK highly sensitive. Increased headline risk → higher FX volatility and regime shifts.",
                    impact="high",
                    sentiment="neutral",
                    source="Geopolitical & Commodity Analysis",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            ]
            
        except Exception as e:
            logger.error(f"Error getting market drivers: {e}")
            return []
    
    def _generate_market_outlook(self, conditions: List[MarketCondition], 
                               pairs: List[PairSentiment], 
                               drivers: List[MarketDriver]) -> str:
        """Generate market outlook summary"""
        try:
            # Analyze overall market tone
            bullish_pairs = sum(1 for p in pairs if p.sentiment == 'bullish')
            bearish_pairs = sum(1 for p in pairs if p.sentiment == 'bearish')
            
            volatility = next((c for c in conditions if c.name == "Volatility Environment"), None)
            risk_appetite = next((c for c in conditions if c.name == "Risk Appetite"), None)
            
            outlook_parts = []
            
            if bullish_pairs > bearish_pairs:
                outlook_parts.append("Overall market sentiment is moderately bullish")
            elif bearish_pairs > bullish_pairs:
                outlook_parts.append("Overall market sentiment is moderately bearish")
            else:
                outlook_parts.append("Market sentiment is mixed across major pairs")
            
            if volatility and volatility.value == 'high':
                outlook_parts.append("with elevated volatility expected")
            elif volatility and volatility.value == 'low':
                outlook_parts.append("with low volatility conditions")
            
            if risk_appetite and risk_appetite.value == 'high':
                outlook_parts.append("Risk appetite is strong, favoring commodity currencies")
            elif risk_appetite and risk_appetite.value == 'low':
                outlook_parts.append("Risk-off sentiment favoring safe haven currencies")
            
            outlook_parts.append("Key focus on upcoming economic data releases and central bank commentary.")
            
            return " ".join(outlook_parts)
            
        except Exception as e:
            logger.error(f"Error generating market outlook: {e}")
            return "Market sentiment analysis is currently updating. Please check back shortly."
    
    def _calculate_confidence_score(self, conditions: List[MarketCondition], 
                                  pairs: List[PairSentiment]) -> float:
        """Calculate confidence score for sentiment analysis"""
        try:
            # Base confidence on data quality and consistency
            base_confidence = 0.8
            
            # Adjust based on data availability
            if len(conditions) >= 3 and len(pairs) >= 4:
                data_quality_bonus = 0.1
            else:
                data_quality_bonus = 0.0
            
            # Adjust based on sentiment consistency
            if pairs:
                sentiment_consistency = 1.0 - (np.std([p.percentage for p in pairs]) / 100)
                consistency_bonus = sentiment_consistency * 0.1
            else:
                consistency_bonus = 0.0
            
            confidence = base_confidence + data_quality_bonus + consistency_bonus
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.7
    
    def _format_for_frontend(self, sentiment) -> Dict[str, Any]:
        """Format sentiment data for frontend consumption
        
        Args:
            sentiment: Can be either a MarketSentiment object or a dict (from cache)
        """
        # Handle both MarketSentiment object and dict (from cache)
        if isinstance(sentiment, dict):
            # Already a dict, just extract VIX and return
            market_conditions = sentiment.get('market_conditions', [])
            volatility_condition = next(
                (c for c in market_conditions if c.get('name') == 'Volatility Environment'),
                None
            )
            
            # Extract VIX data if available
            vix_data = sentiment.get('vix')
            if not vix_data and volatility_condition:
                detail = volatility_condition.get('detail', '')
                import re
                vix_match = re.match(r'VIX:\s*([\d.]+)\s*\(([+-]?[\d.]+)\)', detail)
                if vix_match:
                    try:
                        vix_value = float(vix_match.group(1))
                        vix_change = float(vix_match.group(2))
                        vix_data = {
                            'value': vix_value,
                            'change': vix_change,
                            'level': 'low' if vix_value < 15 else 'medium' if vix_value < 25 else 'high'
                        }
                    except (ValueError, IndexError):
                        pass
            
            # Return the dict as-is, but ensure vix field is set
            result = sentiment.copy()
            if vix_data:
                result['vix'] = vix_data
            return result
        
        # Handle MarketSentiment object
        # Extract VIX data from volatility condition for easier frontend access
        vix_data = None
        volatility_condition = next(
            (c for c in sentiment.market_conditions if c.name == 'Volatility Environment'),
            None
        )
        
        print(f"🔍 DEBUG: _format_for_frontend - volatility_condition: {volatility_condition}")
        
        if volatility_condition and volatility_condition.detail:
            print(f"🔍 DEBUG: Parsing VIX from detail string: '{volatility_condition.detail}'")
            # Parse VIX from detail string: "VIX: 15.0 (+0.0)"
            import re
            vix_match = re.match(r'VIX:\s*([\d.]+)\s*\(([+-]?[\d.]+)\)', volatility_condition.detail)
            if vix_match:
                try:
                    vix_value = float(vix_match.group(1))
                    vix_change = float(vix_match.group(2))
                    vix_data = {
                        'value': vix_value,
                        'change': vix_change,
                        'level': 'low' if vix_value < 15 else 'medium' if vix_value < 25 else 'high'
                    }
                    print(f"✅ DEBUG: Successfully parsed VIX data: {vix_data}")
                    logger.info(f"✅ Extracted VIX data for frontend: {vix_value:.2f} ({vix_change:+.2f})")
                except (ValueError, IndexError) as e:
                    logger.warning(f"⚠️ Failed to parse VIX data from detail: {volatility_condition.detail}, Error: {e}")
                    print(f"❌ DEBUG: Failed to parse VIX: {e}")
            else:
                print(f"⚠️ DEBUG: VIX regex did not match detail string: '{volatility_condition.detail}'")
        else:
            print(f"⚠️ DEBUG: No volatility condition or detail found")
        
        print(f"🔍 DEBUG: Final vix_data being sent to frontend: {vix_data}")
        
        return {
            'timestamp': sentiment.timestamp,
            'trading_day': sentiment.trading_day,
            'market_conditions': [
                {
                    'name': c.name,
                    'value': c.value,
                    'percentage': c.percentage,
                    'detail': c.detail,
                    'trend': c.trend
                } for c in sentiment.market_conditions
            ],
            'pairs_sentiment': [
                {
                    'pair': p.pair,
                    'sentiment': p.sentiment,
                    'percentage': p.percentage,
                    'price_change': p.price_change,
                    'rsi': p.rsi,
                    'volatility': p.volatility,
                    'support': p.support,
                    'resistance': p.resistance
                } for p in sentiment.pairs_sentiment
            ],
            'market_drivers': [
                {
                    'title': d.title,
                    'description': d.description,
                    'impact': d.impact,
                    'sentiment': d.sentiment,
                    'source': d.source,
                    'timestamp': d.timestamp
                } for d in sentiment.market_drivers
            ],
            'market_outlook': sentiment.market_outlook,
            'confidence_score': sentiment.confidence_score,
            'data_sources': sentiment.data_sources,
            'is_market_closed': sentiment.is_market_closed,
            'market_status': sentiment.market_status,
            'vix': vix_data,  # Add VIX as separate field for easier access
            'fng': None  # Filled in get_market_sentiment() from _fetch_fear_greed_index()
        }
    
    def _get_default_market_conditions(self) -> List[MarketCondition]:
        """Get default market conditions when data is unavailable"""
        return [
            MarketCondition("Volatility Environment", "medium", 50, "VIX: 15.0 (+0.0)", "stable"),
            MarketCondition("Risk Appetite", "medium", 50, "Safe Havens: JPY, CHF", "stable")
        ]
    
    def _get_default_pairs_sentiment(self) -> List[PairSentiment]:
        """Get default pairs sentiment when data is unavailable"""
        return [
            PairSentiment("EURUSD", "neutral", 50, 0.0, 50.0, 10.0),
            PairSentiment("GBPUSD", "neutral", 50, 0.0, 50.0, 10.0),
            PairSentiment("USDJPY", "neutral", 50, 0.0, 50.0, 10.0),
            PairSentiment("USDCHF", "neutral", 50, 0.0, 50.0, 10.0)
        ]
    
    def _get_fallback_sentiment(self) -> Dict[str, Any]:
        """Get fallback sentiment data when calculation fails"""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'trading_day': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'market_conditions': [
                {'name': 'Volatility Environment', 'value': 'medium', 'percentage': 50, 'detail': 'VIX: 15.0 (+0.0)', 'trend': 'stable'},
                {'name': 'Risk Appetite', 'value': 'medium', 'percentage': 50, 'detail': 'Safe Havens: JPY, CHF', 'trend': 'stable'}
            ],
            'pairs_sentiment': [
                {'pair': 'EURUSD', 'sentiment': 'neutral', 'percentage': 50, 'price_change': 0.0, 'rsi': 50.0, 'volatility': 10.0},
                {'pair': 'GBPUSD', 'sentiment': 'neutral', 'percentage': 50, 'price_change': 0.0, 'rsi': 50.0, 'volatility': 10.0},
                {'pair': 'USDJPY', 'sentiment': 'neutral', 'percentage': 50, 'price_change': 0.0, 'rsi': 50.0, 'volatility': 10.0},
                {'pair': 'USDCHF', 'sentiment': 'neutral', 'percentage': 50, 'price_change': 0.0, 'rsi': 50.0, 'volatility': 10.0}
            ],
            'market_drivers': [],
            'market_outlook': 'Market sentiment analysis is currently updating. Please check back shortly.',
            'confidence_score': 0.5,
            'data_sources': ['Fallback'],
            'is_market_closed': False,
            'market_status': 'open',
            'fng': None
        }
    
    def _get_market_closed_sentiment(self) -> Dict[str, Any]:
        """Get sentiment data when markets are closed"""
        market_status = self._check_market_status()
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'trading_day': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'market_conditions': [
                {
                    'name': 'Market Status',
                    'value': 'closed',
                    'percentage': 0,
                    'detail': market_status['message'],
                    'trend': 'stable'
                },
                {
                    'name': 'Last Session',
                    'value': 'completed',
                    'percentage': 100,
                    'detail': 'Previous trading session data',
                    'trend': 'stable'
                },
                {
                    'name': 'Next Opening',
                    'value': 'pending',
                    'percentage': 0,
                    'detail': 'Markets will reopen on next trading day',
                    'trend': 'stable'
                }
            ],
            'pairs_sentiment': [
                {
                    'pair': 'EURUSD',
                    'sentiment': 'neutral',
                    'percentage': 50,
                    'price_change': 0.0,
                    'rsi': 50.0,
                    'volatility': 0.0
                },
                {
                    'pair': 'GBPUSD',
                    'sentiment': 'neutral',
                    'percentage': 50,
                    'price_change': 0.0,
                    'rsi': 50.0,
                    'volatility': 0.0
                },
                {
                    'pair': 'USDJPY',
                    'sentiment': 'neutral',
                    'percentage': 50,
                    'price_change': 0.0,
                    'rsi': 50.0,
                    'volatility': 0.0
                },
                {
                    'pair': 'USDCHF',
                    'sentiment': 'neutral',
                    'percentage': 50,
                    'price_change': 0.0,
                    'rsi': 50.0,
                    'volatility': 0.0
                }
            ],
            'market_drivers': [
                {
                    'title': 'Markets Closed',
                    'description': market_status['message'],
                    'impact': 'low',
                    'sentiment': 'neutral',
                    'source': 'System',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            ],
            'market_outlook': f"Markets are currently {market_status['market_status']}. Live sentiment analysis will resume when markets reopen.",
            'confidence_score': 1.0,
            'data_sources': ['System Status'],
            'is_market_closed': True,
            'market_status': market_status['market_status'],
            'fng': self._fetch_fear_greed_index()
        }

# Global instance
market_sentiment_service = MarketSentimentService()
