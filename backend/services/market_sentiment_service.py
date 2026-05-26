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
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
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
    percentage: float  # 0-100: 50=flat; maps daily % vs GAUGE_CAP_PCT (see _calculate_pairs_sentiment)
    price_change: float
    rsi: float  # 0-100 impulse from daily move (serialized also as 'impulse')
    volatility: float  # abs(daily % move); serialized also as 'daily_abs_move_pct'
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
    # Tier A: cross-asset + rates from same TradingView quote map as ticker
    cross_asset_strip: List[Dict[str, Any]] = field(default_factory=list)
    rates_snapshot: Dict[str, Any] = field(default_factory=dict)

class MarketSentimentService:
    """Main market sentiment calculation service"""

    # Bump when market_conditions shape or Risk Appetite detail format changes.
    SENTIMENT_CACHE_VERSION = 2
    
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
                cache_version = data.get("cache_version", 1)
                if cache_version != self.SENTIMENT_CACHE_VERSION:
                    logger.info(
                        "Sentiment cache version %s != %s; discarding stale snapshot",
                        cache_version,
                        self.SENTIMENT_CACHE_VERSION,
                    )
                    self.last_reset_date = data.get("last_reset_date")
                    self.current_sentiment = None
                    self.sentiment_timestamp = None
                    return
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
                'cache_version': self.SENTIMENT_CACHE_VERSION,
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
            
            # Calendar context only — do not short-circuit on weekends; crypto/commodities/indices
            # still move and we serve the same live-style snapshot as weekdays.
            market_status = self._check_market_status()
            if market_status.get('market_status') == 'weekend':
                logger.info("Weekend: still computing full sentiment from TradingView (multi-asset).")
            
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
            
            self._refresh_risk_appetite_condition_if_needed()
            
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
        
        # Get market conditions (pass full quote map + VIX for composite risk appetite)
        market_conditions = self._calculate_market_conditions(forex_data, vix_data)

        # Tier A strip (same quote map as ticker) — cross-asset row below Market Conditions
        cross_asset, rates_snap = self._build_tier_a_data(forex_data)
        
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
            # Never mark closed here: same live snapshot Sat/Sun as rest of week (FX 24/5; other assets move).
            is_market_closed=False,
            market_status=market_status['market_status'],
            cross_asset_strip=cross_asset,
            rates_snapshot=rates_snap,
        )
    
    def _build_tier_a_data(self, quotes: Optional[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Cross-asset daily % moves + bond yields from merged TradingView quotes (Tier A)."""
        try:
            from services.tradingview_instruments import instrument_by_id
            by_id = instrument_by_id()
        except Exception:
            by_id = {}

        def _f(x: Any) -> Optional[float]:
            if x is None:
                return None
            try:
                return float(x)
            except (TypeError, ValueError):
                return None

        def _strip_item(inst_id: str) -> Dict[str, Any]:
            inst = by_id.get(inst_id, {})
            label = inst.get("label", inst_id)
            dec = int(inst.get("decimals", 2))
            row = (quotes or {}).get(inst_id)
            if not row:
                return {"id": inst_id, "label": label, "change_percent": None, "decimals": dec, "missing": True}
            return {
                "id": inst_id,
                "label": label,
                "change_percent": _f(row.get("changePercent")),
                "decimals": dec,
                "missing": False,
                "category": row.get("category", ""),
            }

        cross_ids = ("SPX", "IXIC", "BTCUSDT", "GOLD", "USOIL")
        cross_asset = [_strip_item(i) for i in cross_ids]

        def _yield_bond(inst_id: str) -> Dict[str, Any]:
            inst = by_id.get(inst_id, {})
            label = inst.get("label", inst_id)
            dec = int(inst.get("decimals", 3))
            row = (quotes or {}).get(inst_id)
            if not row:
                return {"id": inst_id, "label": label, "yield": None, "change_percent": None, "decimals": dec, "missing": True}
            return {
                "id": inst_id,
                "label": label,
                "yield": _f(row.get("price")),
                "change_percent": _f(row.get("changePercent")),
                "decimals": dec,
                "missing": False,
            }

        us10 = _yield_bond("US10Y")
        de10 = _yield_bond("DE10Y")
        us02 = _yield_bond("US02Y")

        us10_ch = us10.get("change_percent")
        de10_ch = de10.get("change_percent")
        spread_diff: Optional[float] = None
        if us10_ch is not None and de10_ch is not None:
            spread_diff = float(us10_ch) - float(de10_ch)

        us02_ch = us02.get("change_percent")
        curve_hint: Optional[str] = None
        curve_detail = ""
        if us02_ch is not None and us10_ch is not None:
            shift = float(us10_ch) - float(us02_ch)
            if shift > 0.03:
                curve_hint = "steepening"
                curve_detail = "Long-end yields up vs front (session move)."
            elif shift < -0.03:
                curve_hint = "flattening"
                curve_detail = "Front yields up vs long end (session move)."
            else:
                curve_hint = "neutral"
                curve_detail = "2Y vs 10Y moves broadly aligned."

        rates_snapshot: Dict[str, Any] = {
            "yields": [us10, de10],
            "us_minus_de_change_percent": spread_diff,
            "yield_curve_us": {
                "change_2y": us02_ch,
                "change_10y": us10_ch,
                "hint": curve_hint,
                "hint_detail": curve_detail,
            },
        }
        return cross_asset, rates_snapshot

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
            
            # Composite macro risk appetite (FX, equities, vol, crypto, commodities, rates)
            risk_appetite = self._calculate_risk_appetite(forex_data, vix_data)
            
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
                    detail=risk_appetite.get('detail_macro')
                    or (
                        f"Safe havens: {risk_appetite['safe_havens']} · "
                        f"Risk FX: {risk_appetite['risk_fx']}"
                    ),
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
    
    def _quote_change_percent(self, forex_data: Dict[str, Any], pair: str) -> Optional[float]:
        """Daily % change for a pair from TradingView row (changePercent or change/price)."""
        if not forex_data or pair not in forex_data:
            return None
        row = forex_data[pair]
        try:
            if "changePercent" in row and row["changePercent"] is not None:
                return float(row["changePercent"])
            if "change" in row and "price" in row:
                price = float(row["price"])
                if price != 0:
                    return (float(row["change"]) / price) * 100.0
        except (TypeError, ValueError, KeyError):
            return None
        return None

    # Typical session |move| (%) for normalizing risk-on scores; tune from tape behaviour.
    _RISK_TYPICAL_MOVE_PCT: Dict[str, float] = {
        "USDJPY": 0.35,
        "USDCHF": 0.30,
        "AUDUSD": 0.40,
        "NZDUSD": 0.45,
        "USDCAD": 0.35,
        "EURUSD": 0.35,
        "GBPUSD": 0.40,
        "SPX": 0.80,
        "IXIC": 1.00,
        "DJI": 0.75,
        "VIX": 3.00,
        "BTCUSDT": 2.00,
        "ETHUSDT": 2.50,
        "GOLD": 0.60,
        "USOIL": 1.20,
        "US10Y": 0.08,
    }

    # Pillar weights (sum = 1.0) for composite risk appetite (Option A — single headline index).
    _RISK_PILLAR_WEIGHTS: Dict[str, float] = {
        "fx_haven": 0.22,
        "fx_beta": 0.18,
        "equities": 0.25,
        "vol": 0.15,
        "crypto": 0.10,
        "commodities": 0.07,
        "rates": 0.03,
    }

    def _typical_move_pct(self, inst_id: str) -> float:
        return self._RISK_TYPICAL_MOVE_PCT.get(inst_id, 0.50)

    def _signed_risk_score(
        self,
        quotes: Optional[Dict[str, Any]],
        inst_id: str,
        *,
        invert: bool = False,
    ) -> Optional[float]:
        """Map session % change to [-1, +1] risk-on score (+1 = risk-on)."""
        ch = self._quote_change_percent(quotes, inst_id)
        if ch is None:
            return None
        ref = self._typical_move_pct(inst_id)
        if ref <= 0:
            return None
        signed = float(ch) / ref
        if invert:
            signed = -signed
        return float(np.clip(signed, -1.0, 1.0))

    def _mean_optional_scores(self, scores: List[Optional[float]]) -> Optional[float]:
        valid = [s for s in scores if s is not None]
        if not valid:
            return None
        return float(np.mean(valid))

    def _rates_regime_score(
        self, quotes: Optional[Dict[str, Any]]
    ) -> Optional[float]:
        """Growth risk-on vs flight-to-quality from equities + US10Y session moves."""
        spx = self._signed_risk_score(quotes, "SPX")
        us10 = self._signed_risk_score(quotes, "US10Y")
        if spx is None or us10 is None:
            return None
        if spx < -0.2 and us10 < -0.2:
            return -0.5
        if spx > 0.2 and us10 > 0.2:
            return 0.5
        return 0.0

    def _vix_risk_score(
        self,
        quotes: Optional[Dict[str, Any]],
        vix_data: Optional[Dict[str, float]],
    ) -> Optional[float]:
        """Vol pillar: VIX down = risk-on. Prefer TradingView VIX %; fallback to Yahoo level change."""
        tv = self._signed_risk_score(quotes, "VIX", invert=True)
        if tv is not None:
            return tv
        if not vix_data:
            return None
        try:
            vix_level = float(vix_data.get("vix") or 0)
            change = float(vix_data.get("change") or 0)
            prev = vix_data.get("previous_close")
            if prev and float(prev) > 0:
                ch_pct = (change / float(prev)) * 100.0
            elif vix_level > 0:
                ch_pct = (change / vix_level) * 100.0
            else:
                return None
            ref = self._typical_move_pct("VIX")
            return float(np.clip(-ch_pct / ref, -1.0, 1.0))
        except (TypeError, ValueError):
            return None

    def _active_safe_havens_from_scores(
        self, quotes: Optional[Dict[str, Any]]
    ) -> str:
        """JPY/CHF bid labels when USD legs show haven strength."""
        tags: List[str] = []
        jpy = self._signed_risk_score(quotes, "USDJPY")
        chf = self._signed_risk_score(quotes, "USDCHF")
        if jpy is not None and jpy < -0.15:
            tags.append("JPY")
        if chf is not None and chf < -0.15:
            tags.append("CHF")
        return ", ".join(tags) if tags else "None"

    def _is_legacy_risk_appetite_detail(self, detail: Optional[str]) -> bool:
        """Detect pre–plain-English detail strings still stored in disk/memory cache."""
        if not detail or not str(detail).strip():
            return True
        d = str(detail).strip()
        if d.startswith(
            (
                "Risk-on mood",
                "Slightly risk-on",
                "Mixed macro tone",
                "Slightly risk-off",
                "Risk-off mood",
            )
        ):
            return False
        return True

    def _refresh_risk_appetite_condition_if_needed(self) -> None:
        """Recompute Risk Appetite row when cache holds an old shorthand detail string."""
        if not self.current_sentiment:
            return

        conditions: Any
        if isinstance(self.current_sentiment, dict):
            conditions = self.current_sentiment.get("market_conditions") or []
        else:
            conditions = self.current_sentiment.market_conditions

        risk_row = None
        for c in conditions:
            name = c.get("name") if isinstance(c, dict) else c.name
            if name == "Risk Appetite":
                risk_row = c
                break
        if risk_row is None:
            return

        detail = risk_row.get("detail") if isinstance(risk_row, dict) else risk_row.detail
        if not self._is_legacy_risk_appetite_detail(detail):
            return

        logger.info("Refreshing Risk Appetite detail (legacy cache copy detected)")
        try:
            from app import get_tradingview_prices

            quotes = get_tradingview_prices() or {}
        except Exception as e:
            logger.warning(f"Could not fetch quotes for Risk Appetite refresh: {e}")
            quotes = {}

        vix_data = self._fetch_real_vix()
        ra = self._calculate_risk_appetite(quotes, vix_data)
        new_detail = ra.get("detail_macro") or detail

        if isinstance(risk_row, dict):
            risk_row["value"] = ra["level"]
            risk_row["percentage"] = ra["percentage"]
            risk_row["detail"] = new_detail
            risk_row["trend"] = ra.get("trend", "stable")
        else:
            idx = conditions.index(risk_row)
            conditions[idx] = MarketCondition(
                name="Risk Appetite",
                value=ra["level"],
                percentage=ra["percentage"],
                detail=new_detail,
                trend=ra.get("trend", "stable"),
            )

        self._save_cache()

    def _risk_appetite_headline(self, percentage: float) -> str:
        """One-line summary for the Risk Appetite detail (50 = neutral on the bar)."""
        pct = round(percentage)
        if percentage >= 66:
            return f"Risk-on mood ({pct} on the index; 50 is neutral)."
        if percentage >= 56:
            return f"Slightly risk-on ({pct}; 50 is neutral)."
        if percentage >= 45:
            return f"Mixed macro tone ({pct}; 50 is neutral)."
        if percentage >= 34:
            return f"Slightly risk-off ({pct}; 50 is neutral)."
        return f"Risk-off mood ({pct} on the index; 50 is neutral)."

    def _risk_appetite_driver_phrases(
        self,
        pillars: Dict[str, Optional[float]],
        *,
        safe_havens_str: str,
        risk_fx_str: str,
    ) -> List[str]:
        """Plain-language driver lines ordered by pillar impact on the composite."""
        candidates: List[Tuple[float, str]] = []

        def _add(key: str, weight: float, up: str, down: str, thr: float = 0.12) -> None:
            v = pillars.get(key)
            if v is None:
                return
            if v > thr:
                candidates.append((abs(v) * weight, up))
            elif v < -thr:
                candidates.append((abs(v) * weight, down))

        _add("equities", 0.25, "Equities are up on the session.", "Equities are down on the session.")
        _add(
            "fx_haven",
            0.22,
            "JPY and CHF are weak vs USD—little haven buying in FX.",
            (
                f"Haven currencies are firm ({safe_havens_str})."
                if safe_havens_str != "None"
                else "JPY and/or CHF are firm (haven-style FX bid)."
            ),
            0.15,
        )
        beta_up = (
            f"Commodity FX is firm vs USD ({risk_fx_str} in the lead)."
            if risk_fx_str != "—"
            else "Commodity FX is firm vs USD (AUD, NZD, CAD area)."
        )
        _add("fx_beta", 0.18, beta_up, "Commodity FX is soft vs USD.")
        _add(
            "vol",
            0.15,
            "Volatility is easing (VIX lower).",
            "Volatility is rising (VIX higher).",
        )
        _add("crypto", 0.10, "Crypto is up.", "Crypto is down.")
        _add(
            "commodities",
            0.07,
            "Oil-led commodities are higher (growth tilt).",
            "Gold is firmer, which often leans defensive.",
            0.15,
        )

        rates = pillars.get("rates")
        if rates is not None and rates <= -0.4:
            candidates.append((0.03 * 0.5, "Yields and equities both weaker—flight-to-quality tone."))
        elif rates is not None and rates >= 0.4:
            candidates.append((0.03 * 0.5, "Yields and equities both up—growth-style risk-on."))

        if not candidates:
            return ["Session moves are small across drivers; nothing stands out."]

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [phrase for _, phrase in candidates[:4]]

    def _format_risk_appetite_detail_user(
        self,
        percentage: float,
        pillars: Dict[str, Optional[float]],
        *,
        safe_havens_str: str,
        risk_fx_str: str,
    ) -> str:
        """User-facing condition detail: headline plus top driver sentences."""
        headline = self._risk_appetite_headline(percentage)
        drivers = self._risk_appetite_driver_phrases(
            pillars,
            safe_havens_str=safe_havens_str,
            risk_fx_str=risk_fx_str,
        )
        return f"{headline} {' '.join(drivers)}"

    def _risk_fx_summary(self, forex_data: Optional[Dict[str, Any]]) -> str:
        """Which commodity-beta G10s look bid vs USD from ticker pairs (AUDUSD, NZDUSD, USDCAD)."""
        if not forex_data:
            return "—"
        thr = 0.05
        tags: List[str] = []
        ch = self._quote_change_percent(forex_data, "AUDUSD")
        if ch is not None and ch > thr:
            tags.append("AUD")
        ch = self._quote_change_percent(forex_data, "NZDUSD")
        if ch is not None and ch > thr:
            tags.append("NZD")
        ch = self._quote_change_percent(forex_data, "USDCAD")
        if ch is not None and ch < -thr:
            tags.append("CAD")
        return ", ".join(sorted(set(tags))) if tags else "—"

    def _calculate_risk_appetite(
        self,
        quotes: Optional[Dict[str, Any]],
        vix_data: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Composite macro risk appetite from FX, equities, vol, crypto, commodities, and rates.

        Score in [-1, 1] is a weighted mean of pillar risk-on scores; 50 = neutral on the 0–100 bar.
        Uses the same TradingView quote map as the ticker (plus optional Yahoo VIX fallback).
        """
        default = {
            "level": "medium",
            "percentage": 50.0,
            "safe_havens": "None",
            "risk_fx": self._risk_fx_summary(quotes),
            "detail_macro": (
                "Mixed macro tone (50; 50 is neutral). "
                "Session moves are small across drivers; nothing stands out."
            ),
            "trend": "stable",
        }
        try:
            if not quotes:
                logger.warning("⚠️ No quote data for risk appetite, using neutral default")
                return default

            fx_haven = self._mean_optional_scores([
                self._signed_risk_score(quotes, "USDJPY"),
                self._signed_risk_score(quotes, "USDCHF"),
            ])
            fx_beta = self._mean_optional_scores([
                self._signed_risk_score(quotes, "AUDUSD"),
                self._signed_risk_score(quotes, "NZDUSD"),
                self._signed_risk_score(quotes, "USDCAD", invert=True),
            ])
            equities = self._mean_optional_scores([
                self._signed_risk_score(quotes, "SPX"),
                self._signed_risk_score(quotes, "IXIC"),
            ])
            vol = self._vix_risk_score(quotes, vix_data)
            crypto = self._mean_optional_scores([
                self._signed_risk_score(quotes, "BTCUSDT"),
                self._signed_risk_score(quotes, "ETHUSDT"),
            ])
            oil = self._signed_risk_score(quotes, "USOIL")
            gold = self._signed_risk_score(quotes, "GOLD", invert=True)
            if oil is not None and gold is not None:
                commodities = 0.6 * oil + 0.4 * gold
            else:
                commodities = oil if oil is not None else gold
            rates = self._rates_regime_score(quotes)

            pillars: Dict[str, Optional[float]] = {
                "fx_haven": fx_haven,
                "fx_beta": fx_beta,
                "equities": equities,
                "vol": vol,
                "crypto": crypto,
                "commodities": commodities,
                "rates": rates,
            }

            weighted: List[Tuple[float, float]] = []
            for name, score in pillars.items():
                if score is None:
                    continue
                w = self._RISK_PILLAR_WEIGHTS.get(name, 0.0)
                if w > 0:
                    weighted.append((w, float(score)))

            if not weighted:
                logger.warning("⚠️ No risk appetite pillars available, using neutral default")
                return default

            total_w = sum(w for w, _ in weighted)
            risk_on_score = sum(w * s for w, s in weighted) / total_w
            percentage = float(np.clip(50.0 + 50.0 * risk_on_score, 0.0, 100.0))

            if percentage >= 66.0:
                level = "high"
            elif percentage >= 33.0:
                level = "medium"
            else:
                level = "low"

            safe_havens_str = self._active_safe_havens_from_scores(quotes)
            risk_fx_str = self._risk_fx_summary(quotes)
            detail_macro = self._format_risk_appetite_detail_user(
                percentage,
                pillars,
                safe_havens_str=safe_havens_str,
                risk_fx_str=risk_fx_str,
            )

            logger.info(
                f"✅ Risk Appetite: {level.upper()} ({percentage:.1f}%) "
                f"composite={risk_on_score:.3f} pillars={{{', '.join(f'{k}:{v:.2f}' for k, v in pillars.items() if v is not None)}}}"
            )

            return {
                "level": level,
                "percentage": percentage,
                "safe_havens": safe_havens_str,
                "risk_fx": risk_fx_str,
                "detail_macro": detail_macro,
                "trend": "stable",
            }

        except Exception as e:
            logger.error(f"❌ Error calculating risk appetite: {e}")
            import traceback
            traceback.print_exc()
            return default
    
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
                    
                    # Sentiment labels (thresholds unchanged)
                    if price_change_percent > 0.1:
                        sentiment = 'bullish'
                    elif price_change_percent < -0.1:
                        sentiment = 'bearish'
                    else:
                        sentiment = 'neutral'

                    # Bar position 0–100: 50 = flat; maps linearly from daily % in [-cap, +cap]
                    # (keep in sync with DAILY_CHANGE_GAUGE_CAP_PCT in src/utils/dailyChangeGauge.js)
                    GAUGE_CAP_PCT = 1.15
                    t = float(np.clip(price_change_percent / GAUGE_CAP_PCT, -1.0, 1.0))
                    percentage = 50.0 + t * 50.0
                    
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
                    logger.info(
                        f"✅ Calculated sentiment for {pair}: change={price_change_percent:.4f}%, "
                        f"impulse={rsi:.1f}, daily_abs_move%={volatility:.2f}"
                    )
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
        """Short educational themes (not a live news/calendar feed)."""
        try:
            return [
                MarketDriver(
                    title="Policy and yield spreads",
                    description="Central banks rarely move in lockstep. Relative rates and expectations often drive G10 trends more than a single data point.",
                    impact="medium",
                    sentiment="neutral",
                    source="",
                    timestamp=datetime.now(timezone.utc).isoformat()
                ),
                MarketDriver(
                    title="Risk tone and safe havens",
                    description="When risk assets struggle, flows often favour USD, JPY, and CHF in different mixes. When appetite returns, higher-beta FX can lead.",
                    impact="medium",
                    sentiment="neutral",
                    source="",
                    timestamp=datetime.now(timezone.utc).isoformat()
                ),
                MarketDriver(
                    title="Geopolitics and commodities",
                    description="Shocks can dominate short-term price action. Energy and key commodities often spill into AUD, CAD, NOK and broader volatility.",
                    impact="medium",
                    sentiment="neutral",
                    source="",
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
            if len(conditions) >= 2 and len(pairs) >= 4:
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
            pairs = result.get('pairs_sentiment')
            if pairs:
                enriched = []
                for p in pairs:
                    p2 = dict(p)
                    if 'impulse' not in p2 and p2.get('rsi') is not None:
                        p2['impulse'] = p2['rsi']
                    if 'daily_abs_move_pct' not in p2 and p2.get('volatility') is not None:
                        p2['daily_abs_move_pct'] = p2['volatility']
                    enriched.append(p2)
                result['pairs_sentiment'] = enriched
            if 'cross_asset_strip' not in result:
                result['cross_asset_strip'] = []
            if 'rates_snapshot' not in result:
                result['rates_snapshot'] = {}
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
                    'impulse': p.rsi,
                    'daily_abs_move_pct': p.volatility,
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
            'fng': None,  # Filled in get_market_sentiment() from _fetch_fear_greed_index()
            'cross_asset_strip': getattr(sentiment, 'cross_asset_strip', None) or [],
            'rates_snapshot': getattr(sentiment, 'rates_snapshot', None) or {},
        }
    
    def _get_default_market_conditions(self) -> List[MarketCondition]:
        """Get default market conditions when data is unavailable"""
        return [
            MarketCondition("Volatility Environment", "medium", 50, "VIX: 15.0 (+0.0)", "stable"),
            MarketCondition(
                "Risk Appetite",
                "medium",
                50,
                "Mixed macro tone (50; 50 is neutral). "
                "Session moves are small across drivers; nothing stands out.",
                "stable",
            ),
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
                {
                    'name': 'Risk Appetite',
                    'value': 'medium',
                    'percentage': 50,
                    'detail': (
                        'Mixed macro tone (50; 50 is neutral). '
                        'Session moves are small across drivers; nothing stands out.'
                    ),
                    'trend': 'stable',
                },
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
            'fng': None,
            'cross_asset_strip': [],
            'rates_snapshot': {},
        }
    
    def _get_market_closed_sentiment(self) -> Dict[str, Any]:
        """Legacy stub when FX was treated as fully closed (e.g. weekends). Main API no longer uses this for weekends."""
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
            'fng': self._fetch_fear_greed_index(),
            'cross_asset_strip': [],
            'rates_snapshot': {},
        }

# Global instance
market_sentiment_service = MarketSentimentService()
