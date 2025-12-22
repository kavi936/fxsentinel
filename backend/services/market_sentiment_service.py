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
        self.vix_cache_expiration_minutes = 10  # Cache VIX for 10 minutes to avoid rate limits
        
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
                else:
                    self.vix_cache = None
                    self.vix_cache_timestamp = None
                
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
                self.current_sentiment = self._calculate_market_sentiment()
                self.sentiment_timestamp = datetime.now(timezone.utc)
                self._save_cache()
            else:
                logger.info(f"Using cached sentiment data (age: {(datetime.now(timezone.utc) - self.sentiment_timestamp).total_seconds() / 60:.1f} minutes)")
            
            # Return formatted data for frontend
            return self._format_for_frontend(self.current_sentiment)
            
        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            return self._get_fallback_sentiment()
    
    def _calculate_market_sentiment(self) -> MarketSentiment:
        """Calculate comprehensive market sentiment"""
        logger.info("Calculating fresh market sentiment...")
        
        # Check market status first
        market_status = self._check_market_status()
        
        # Get market conditions
        market_conditions = self._calculate_market_conditions()
        
        # Get pairs sentiment
        pairs_sentiment = self._calculate_pairs_sentiment()
        
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
    
    def _calculate_market_conditions(self) -> List[MarketCondition]:
        """Calculate market conditions (volatility, risk appetite, correlation)"""
        try:
            # Get forex price data for calculations
            from app import get_tradingview_prices
            forex_data = get_tradingview_prices()
            
            if not forex_data:
                return self._get_default_market_conditions()
            
            # Calculate volatility environment
            volatility = self._calculate_volatility(forex_data)
            
            # Calculate risk appetite
            risk_appetite = self._calculate_risk_appetite(forex_data)
            
            # Calculate market correlation
            correlation = self._calculate_market_correlation(forex_data)
            
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
                ),
                MarketCondition(
                    name="Market Correlation",
                    value=correlation['level'],
                    percentage=correlation['percentage'],
                    detail=correlation['description'],
                    trend=correlation['trend']
                )
            ]
            
        except Exception as e:
            logger.error(f"Error calculating market conditions: {e}")
            return self._get_default_market_conditions()
    
    def _fetch_real_vix(self) -> Optional[Dict[str, float]]:
        """Fetch real VIX data from Yahoo Finance using yfinance library with caching"""
        # Check if we have valid cached VIX data
        if self._is_vix_cache_valid():
            logger.info(f"✅ Using cached VIX data: {self.vix_cache['vix']:.2f} ({self.vix_cache['change']:+.2f})")
            return self.vix_cache
        
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
                    logger.info("Using expired VIX cache as fallback")
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
            print(f"⚠️ DEBUG: Rate limit error from yfinance")
            # Use cached data even if expired when rate limited
            if self.vix_cache:
                logger.info("Using cached VIX data due to rate limit")
                return self.vix_cache
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
    
    def _calculate_volatility(self, forex_data: Dict) -> Dict[str, Any]:
        """Calculate volatility environment from forex data and real VIX"""
        try:
            # First, try to fetch real VIX data
            vix_data = self._fetch_real_vix()
            print(f"🔍 DEBUG: _calculate_volatility - vix_data received: {vix_data}")
            
            if vix_data:
                # Use real VIX data
                vix_value = vix_data['vix']
                vix_change = vix_data['change']
                print(f"✅ DEBUG: Using real VIX data - Value: {vix_value}, Change: {vix_change}")
                
                # Determine volatility level based on real VIX
                if vix_value >= 25:
                    level = 'high'
                    percentage = 75
                elif vix_value >= 15:
                    level = 'medium'
                    percentage = 50
                else:
                    level = 'low'
                    percentage = 25
                
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
            
            # Determine volatility level
            if avg_volatility > 0.15:
                level = 'high'
                percentage = 75
                vix = 20.0
            elif avg_volatility > 0.08:
                level = 'medium'
                percentage = 50
                vix = 15.0
            else:
                level = 'low'
                percentage = 25
                vix = 10.0
            
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
        """Calculate risk appetite from currency flows"""
        try:
            # Analyze safe haven vs risk currencies
            safe_havens = ['USDJPY', 'USDCHF']  # JPY and CHF are safe havens
            risk_currencies = ['AUDUSD', 'NZDUSD']  # AUD and NZD are risk currencies
            
            safe_haven_changes = []
            risk_currency_changes = []
            
            for pair, data in forex_data.items():
                if 'change' in data:
                    if pair in safe_havens:
                        safe_haven_changes.append(data['change'])
                    elif pair in risk_currencies:
                        risk_currency_changes.append(data['change'])
            
            # Calculate risk appetite based on relative performance
            if safe_haven_changes and risk_currency_changes:
                avg_safe = np.mean(safe_haven_changes)
                avg_risk = np.mean(risk_currency_changes)
                
                # If safe havens are stronger, risk appetite is low
                if avg_safe > avg_risk:
                    level = 'low'
                    percentage = 30
                    safe_havens_str = 'JPY, CHF'
                elif avg_risk > avg_safe:
                    level = 'high'
                    percentage = 70
                    safe_havens_str = 'None'
                else:
                    level = 'medium'
                    percentage = 50
                    safe_havens_str = 'JPY'
            else:
                level = 'medium'
                percentage = 50
                safe_havens_str = 'JPY, CHF'
            
            return {
                'level': level,
                'percentage': percentage,
                'safe_havens': safe_havens_str,
                'trend': 'stable'
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk appetite: {e}")
            return {'level': 'medium', 'percentage': 50, 'safe_havens': 'JPY, CHF', 'trend': 'stable'}
    
    def _calculate_market_correlation(self, forex_data: Dict) -> Dict[str, Any]:
        """Calculate market correlation between currency pairs"""
        try:
            # Calculate correlation between major pairs
            pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
            changes = []
            
            for pair in pairs:
                if pair in forex_data and 'change' in forex_data[pair]:
                    changes.append(forex_data[pair]['change'])
            
            if len(changes) >= 2:
                # Calculate correlation coefficient
                correlation_matrix = np.corrcoef(changes)
                avg_correlation = np.mean(np.abs(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)]))
                
                if avg_correlation > 0.7:
                    level = 'high'
                    percentage = 80
                    description = 'Pairs moving together'
                elif avg_correlation > 0.4:
                    level = 'medium'
                    percentage = 50
                    description = 'Mixed correlation'
                else:
                    level = 'low'
                    percentage = 20
                    description = 'Pairs moving independently'
            else:
                level = 'medium'
                percentage = 50
                description = 'Pairs moving independently'
            
            return {
                'level': level,
                'percentage': percentage,
                'description': description,
                'trend': 'stable'
            }
            
        except Exception as e:
            logger.error(f"Error calculating market correlation: {e}")
            return {'level': 'medium', 'percentage': 50, 'description': 'Pairs moving independently', 'trend': 'stable'}
    
    def _calculate_pairs_sentiment(self) -> List[PairSentiment]:
        """Calculate sentiment for individual currency pairs"""
        try:
            from app import get_tradingview_prices
            forex_data = get_tradingview_prices()
            
            if not forex_data:
                return self._get_default_pairs_sentiment()
            
            pairs_sentiment = []
            major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
            
            for pair in major_pairs:
                if pair in forex_data:
                    data = forex_data[pair]
                    
                    # Use changePercent for more accurate sentiment calculation
                    price_change_percent = data.get('changePercent', 0)
                    price_change = data.get('change', 0)
                    

                    
                    # Calculate sentiment from percentage change (more realistic thresholds)
                    if price_change_percent > 0.1:  # 0.1% change
                        sentiment = 'bullish'
                        percentage = min(85, 50 + abs(price_change_percent) * 50)
                    elif price_change_percent < -0.1:  # -0.1% change
                        sentiment = 'bearish'
                        percentage = max(15, 50 - abs(price_change_percent) * 50)
                    else:
                        sentiment = 'neutral'
                        percentage = 50
                    
                    # Calculate RSI (more realistic calculation)
                    # RSI should be based on relative strength, not just price change
                    if price_change_percent > 0.2:
                        rsi = min(100, 70 + (price_change_percent - 0.2) * 100)
                    elif price_change_percent < -0.2:
                        rsi = max(0, 30 + (price_change_percent + 0.2) * 100)
                    else:
                        rsi = 50 + (price_change_percent * 100)
                    
                    # Calculate volatility (more realistic)
                    volatility = abs(price_change_percent) * 10  # Scale down for more realistic values
                    
                    pairs_sentiment.append(PairSentiment(
                        pair=pair,
                        sentiment=sentiment,
                        percentage=percentage,
                        price_change=price_change_percent,  # Use percentage for display
                        rsi=rsi,
                        volatility=volatility
                    ))
            
            return pairs_sentiment
            
        except Exception as e:
            logger.error(f"Error calculating pairs sentiment: {e}")
            return self._get_default_pairs_sentiment()
    
    def _get_market_drivers(self) -> List[MarketDriver]:
        """Get current market drivers from news and events"""
        try:
            # This would integrate with your news sentiment analysis
            # For now, return some realistic drivers
            return [
                MarketDriver(
                    title="Fed Policy Expectations",
                    description="Market pricing in potential rate cuts in 2024",
                    impact="high",
                    sentiment="positive",
                    source="Economic Calendar",
                    timestamp=datetime.now(timezone.utc).isoformat()
                ),
                MarketDriver(
                    title="ECB Policy Divergence",
                    description="ECB maintaining higher rates while Fed signals cuts",
                    impact="medium",
                    sentiment="negative",
                    source="News Analysis",
                    timestamp=datetime.now(timezone.utc).isoformat()
                ),
                MarketDriver(
                    title="Risk Sentiment Shift",
                    description="Global markets showing improved risk appetite",
                    impact="medium",
                    sentiment="positive",
                    source="Market Analysis",
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
    
    def _format_for_frontend(self, sentiment: MarketSentiment) -> Dict[str, Any]:
        """Format sentiment data for frontend consumption"""
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
            'vix': vix_data  # Add VIX as separate field for easier access
        }
    
    def _get_default_market_conditions(self) -> List[MarketCondition]:
        """Get default market conditions when data is unavailable"""
        return [
            MarketCondition("Volatility Environment", "medium", 50, "VIX: 15.0 (+0.0)", "stable"),
            MarketCondition("Risk Appetite", "medium", 50, "Safe Havens: JPY, CHF", "stable"),
            MarketCondition("Market Correlation", "medium", 50, "Pairs moving independently", "stable")
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
                {'name': 'Risk Appetite', 'value': 'medium', 'percentage': 50, 'detail': 'Safe Havens: JPY, CHF', 'trend': 'stable'},
                {'name': 'Market Correlation', 'value': 'medium', 'percentage': 50, 'detail': 'Pairs moving independently', 'trend': 'stable'}
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
            'market_status': 'open'
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
            'market_status': market_status['market_status']
        }

# Global instance
market_sentiment_service = MarketSentimentService()
