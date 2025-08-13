#!/usr/bin/env python3
"""
Technical Analysis Service for FXSentinel
Uses free data sources and mathematical patterns for forex analysis
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class TechnicalSignal:
    """Technical analysis signal"""
    pair: str
    signal_type: str  # 'buy', 'sell', 'hold'
    strength: float  # 0.0 to 1.0
    timeframe: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    indicators: Dict[str, Any]
    pattern: Optional[str] = None

@dataclass
class SupportResistance:
    """Support and resistance levels"""
    pair: str
    support_levels: List[float]
    resistance_levels: List[float]
    current_price: float
    strength: Dict[str, float]  # strength of each level

class TechnicalAnalyzer:
    def __init__(self):
        self.indicators = {}
        self.patterns = {}
        self.timeframes = ['1h', '4h', '1d']
        
    def analyze_pair(self, pair: str, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive technical analysis for a currency pair"""
        try:
            if price_data.empty:
                return self._get_default_analysis(pair)
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(price_data)
            
            # Identify patterns
            patterns = self._identify_patterns(price_data)
            
            # Find support and resistance
            support_resistance = self._find_support_resistance(price_data, pair)
            
            # Generate signals
            signals = self._generate_signals(pair, indicators, patterns, support_resistance)
            
            # Calculate overall sentiment
            sentiment = self._calculate_sentiment(indicators, patterns)
            
            return {
                'pair': pair,
                'timestamp': datetime.now().isoformat(),
                'indicators': indicators,
                'patterns': patterns,
                'support_resistance': support_resistance,
                'signals': signals,
                'sentiment': sentiment,
                'summary': self._generate_summary(sentiment, patterns, signals)
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {pair}: {e}")
            return self._get_default_analysis(pair)
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators"""
        indicators = {}
        
        # Ensure we have required columns
        if 'close' not in data.columns:
            data['close'] = data['price'] if 'price' in data.columns else data.iloc[:, -1]
        
        if 'high' not in data.columns:
            data['high'] = data['close']
        
        if 'low' not in data.columns:
            data['low'] = data['close']
        
        if 'volume' not in data.columns:
            data['volume'] = 1000  # Default volume
        
        # Moving Averages
        indicators['sma_20'] = self._calculate_sma(data['close'], 20)
        indicators['sma_50'] = self._calculate_sma(data['close'], 50)
        indicators['ema_12'] = self._calculate_ema(data['close'], 12)
        indicators['ema_26'] = self._calculate_ema(data['close'], 26)
        
        # RSI
        indicators['rsi'] = self._calculate_rsi(data['close'], 14)
        
        # MACD
        macd_line, signal_line, histogram = self._calculate_macd(data['close'])
        indicators['macd'] = {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        }
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(data['close'])
        indicators['bollinger_bands'] = {
            'upper': bb_upper,
            'middle': bb_middle,
            'lower': bb_lower
        }
        
        # Stochastic
        k_percent, d_percent = self._calculate_stochastic(data)
        indicators['stochastic'] = {
            'k_percent': k_percent,
            'd_percent': d_percent
        }
        
        # ATR (Average True Range)
        indicators['atr'] = self._calculate_atr(data)
        
        return indicators
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return prices.iloc[-1]
        return prices.rolling(window=period).mean().iloc[-1]
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices.iloc[-1]
        return prices.ewm(span=period).mean().iloc[-1]
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[float, float, float]:
        """Calculate MACD"""
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        signal_line = self._calculate_ema(pd.Series([macd_line]), 9)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            current_price = prices.iloc[-1]
            return current_price * 1.02, current_price, current_price * 0.98
        
        sma = prices.rolling(window=period).mean().iloc[-1]
        std = prices.rolling(window=period).std().iloc[-1]
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return upper_band, sma, lower_band
    
    def _calculate_stochastic(self, data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator"""
        if len(data) < k_period:
            return 50.0, 50.0
        
        lowest_low = data['low'].rolling(window=k_period).min()
        highest_high = data['high'].rolling(window=k_period).max()
        
        k_percent = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent.iloc[-1], d_percent.iloc[-1]
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(data) < 2:
            return 0.001
        
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean().iloc[-1]
        
        return atr
    
    def _identify_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify chart patterns"""
        patterns = []
        
        if len(data) < 20:
            return patterns
        
        # Double Top/Bottom
        double_top = self._identify_double_top(data)
        if double_top:
            patterns.append(double_top)
        
        double_bottom = self._identify_double_bottom(data)
        if double_bottom:
            patterns.append(double_bottom)
        
        # Head and Shoulders
        head_shoulders = self._identify_head_shoulders(data)
        if head_shoulders:
            patterns.append(head_shoulders)
        
        # Triangle patterns
        triangle = self._identify_triangle(data)
        if triangle:
            patterns.append(triangle)
        
        # Flag patterns
        flag = self._identify_flag(data)
        if flag:
            patterns.append(flag)
        
        return patterns
    
    def _identify_double_top(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Identify double top pattern"""
        if len(data) < 20:
            return None
        
        prices = data['close'].values
        highs = []
        
        # Find local highs
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i-1] and prices[i] > prices[i-2] and \
               prices[i] > prices[i+1] and prices[i] > prices[i+2]:
                highs.append((i, prices[i]))
        
        if len(highs) < 2:
            return None
        
        # Check for double top
        for i in range(len(highs) - 1):
            h1_idx, h1_price = highs[i]
            h2_idx, h2_price = highs[i+1]
            
            # Check if peaks are similar in height and separated by a trough
            price_diff = abs(h1_price - h2_price) / h1_price
            if price_diff < 0.02:  # Within 2%
                # Check for trough between peaks
                trough_idx = (h1_idx + h2_idx) // 2
                trough_price = prices[trough_idx]
                
                if trough_price < min(h1_price, h2_price) * 0.95:  # 5% below peaks
                    return {
                        'pattern': 'double_top',
                        'confidence': 0.7,
                        'target': trough_price * 0.95,  # 5% below trough
                        'description': 'Bearish reversal pattern'
                    }
        
        return None
    
    def _identify_double_bottom(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Identify double bottom pattern"""
        if len(data) < 20:
            return None
        
        prices = data['close'].values
        lows = []
        
        # Find local lows
        for i in range(2, len(prices) - 2):
            if prices[i] < prices[i-1] and prices[i] < prices[i-2] and \
               prices[i] < prices[i+1] and prices[i] < prices[i+2]:
                lows.append((i, prices[i]))
        
        if len(lows) < 2:
            return None
        
        # Check for double bottom
        for i in range(len(lows) - 1):
            l1_idx, l1_price = lows[i]
            l2_idx, l2_price = lows[i+1]
            
            # Check if troughs are similar in height and separated by a peak
            price_diff = abs(l1_price - l2_price) / l1_price
            if price_diff < 0.02:  # Within 2%
                # Check for peak between troughs
                peak_idx = (l1_idx + l2_idx) // 2
                peak_price = prices[peak_idx]
                
                if peak_price > max(l1_price, l2_price) * 1.05:  # 5% above troughs
                    return {
                        'pattern': 'double_bottom',
                        'confidence': 0.7,
                        'target': peak_price * 1.05,  # 5% above peak
                        'description': 'Bullish reversal pattern'
                    }
        
        return None
    
    def _identify_head_shoulders(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Identify head and shoulders pattern"""
        # Simplified implementation
        if len(data) < 30:
            return None
        
        prices = data['close'].values[-30:]  # Last 30 periods
        
        # Look for three peaks with middle peak higher
        peaks = []
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i-1] and prices[i] > prices[i-2] and \
               prices[i] > prices[i+1] and prices[i] > prices[i+2]:
                peaks.append((i, prices[i]))
        
        if len(peaks) >= 3:
            # Check if middle peak is higher
            left_shoulder, head, right_shoulder = peaks[-3:]
            
            if head[1] > left_shoulder[1] and head[1] > right_shoulder[1]:
                # Check if shoulders are at similar levels
                shoulder_diff = abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1]
                if shoulder_diff < 0.03:  # Within 3%
                    return {
                        'pattern': 'head_shoulders',
                        'confidence': 0.6,
                        'target': min(left_shoulder[1], right_shoulder[1]) * 0.95,
                        'description': 'Bearish reversal pattern'
                    }
        
        return None
    
    def _identify_triangle(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Identify triangle patterns"""
        if len(data) < 20:
            return None
        
        prices = data['close'].values[-20:]
        highs = []
        lows = []
        
        # Find highs and lows
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i-1] and prices[i] > prices[i-2] and \
               prices[i] > prices[i+1] and prices[i] > prices[i+2]:
                highs.append((i, prices[i]))
            elif prices[i] < prices[i-1] and prices[i] < prices[i-2] and \
                 prices[i] < prices[i+1] and prices[i] < prices[i+2]:
                lows.append((i, prices[i]))
        
        if len(highs) >= 2 and len(lows) >= 2:
            # Check for converging lines
            high_slope = (highs[-1][1] - highs[0][1]) / (highs[-1][0] - highs[0][0])
            low_slope = (lows[-1][1] - lows[0][1]) / (lows[-1][0] - lows[0][0])
            
            if abs(high_slope) < 0.001 and abs(low_slope) < 0.001:
                return {
                    'pattern': 'rectangle',
                    'confidence': 0.5,
                    'target': prices[-1] * 1.02,
                    'description': 'Consolidation pattern'
                }
            elif high_slope < 0 and low_slope > 0:
                return {
                    'pattern': 'symmetrical_triangle',
                    'confidence': 0.6,
                    'target': prices[-1] * 1.03,
                    'description': 'Continuation pattern'
                }
        
        return None
    
    def _identify_flag(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Identify flag patterns"""
        if len(data) < 15:
            return None
        
        prices = data['close'].values
        recent_trend = (prices[-1] - prices[-10]) / prices[-10]
        
        if abs(recent_trend) > 0.02:  # 2% move
            # Check for consolidation after trend
            recent_volatility = np.std(prices[-5:]) / prices[-1]
            if recent_volatility < 0.005:  # Low volatility
                return {
                    'pattern': 'flag',
                    'confidence': 0.5,
                    'target': prices[-1] * (1 + recent_trend * 0.5),
                    'description': 'Continuation pattern'
                }
        
        return None
    
    def _find_support_resistance(self, data: pd.DataFrame, pair: str) -> SupportResistance:
        """Find support and resistance levels"""
        if len(data) < 20:
            current_price = data['close'].iloc[-1] if 'close' in data.columns else data.iloc[-1, -1]
            return SupportResistance(
                pair=pair,
                support_levels=[current_price * 0.99],
                resistance_levels=[current_price * 1.01],
                current_price=current_price,
                strength={'support': 0.5, 'resistance': 0.5}
            )
        
        prices = data['close'].values
        current_price = prices[-1]
        
        # Find local highs and lows
        highs = []
        lows = []
        
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i-1] and prices[i] > prices[i-2] and \
               prices[i] > prices[i+1] and prices[i] > prices[i+2]:
                highs.append(prices[i])
            elif prices[i] < prices[i-1] and prices[i] < prices[i-2] and \
                 prices[i] < prices[i+1] and prices[i] < prices[i+2]:
                lows.append(prices[i])
        
        # Cluster nearby levels
        resistance_levels = self._cluster_levels(highs, current_price, 'above')
        support_levels = self._cluster_levels(lows, current_price, 'below')
        
        # Calculate strength
        support_strength = self._calculate_level_strength(support_levels, prices)
        resistance_strength = self._calculate_level_strength(resistance_levels, prices)
        
        return SupportResistance(
            pair=pair,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            current_price=current_price,
            strength={'support': support_strength, 'resistance': resistance_strength}
        )
    
    def _cluster_levels(self, levels: List[float], current_price: float, position: str) -> List[float]:
        """Cluster nearby price levels"""
        if not levels:
            return []
        
        # Sort levels
        levels = sorted(levels)
        
        # Cluster levels within 0.5% of each other
        clusters = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] < 0.005:
                current_cluster.append(level)
            else:
                clusters.append(np.mean(current_cluster))
                current_cluster = [level]
        
        clusters.append(np.mean(current_cluster))
        
        # Filter levels based on position relative to current price
        if position == 'above':
            return [level for level in clusters if level > current_price * 1.001]
        else:
            return [level for level in clusters if level < current_price * 0.999]
    
    def _calculate_level_strength(self, levels: List[float], prices: np.ndarray) -> float:
        """Calculate strength of support/resistance levels"""
        if not levels:
            return 0.0
        
        # Count touches of each level
        touches = 0
        for level in levels:
            for price in prices:
                if abs(price - level) / level < 0.002:  # Within 0.2%
                    touches += 1
        
        # Normalize strength
        strength = min(1.0, touches / (len(levels) * 5))
        return strength
    
    def _generate_signals(self, pair: str, indicators: Dict, patterns: List, 
                         support_resistance: SupportResistance) -> List[TechnicalSignal]:
        """Generate trading signals based on technical analysis"""
        signals = []
        current_price = support_resistance.current_price
        
        # RSI signals
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            signals.append(TechnicalSignal(
                pair=pair,
                signal_type='buy',
                strength=0.7,
                timeframe='4h',
                entry_price=current_price,
                stop_loss=current_price * 0.995,
                take_profit=current_price * 1.01,
                confidence=0.6,
                indicators={'rsi': rsi},
                pattern='oversold'
            ))
        elif rsi > 70:
            signals.append(TechnicalSignal(
                pair=pair,
                signal_type='sell',
                strength=0.7,
                timeframe='4h',
                entry_price=current_price,
                stop_loss=current_price * 1.005,
                take_profit=current_price * 0.99,
                confidence=0.6,
                indicators={'rsi': rsi},
                pattern='overbought'
            ))
        
        # Moving average signals
        sma_20 = indicators.get('sma_20', current_price)
        sma_50 = indicators.get('sma_50', current_price)
        
        if current_price > sma_20 > sma_50:
            signals.append(TechnicalSignal(
                pair=pair,
                signal_type='buy',
                strength=0.6,
                timeframe='1d',
                entry_price=current_price,
                stop_loss=sma_50,
                take_profit=current_price * 1.015,
                confidence=0.5,
                indicators={'sma_20': sma_20, 'sma_50': sma_50},
                pattern='golden_cross'
            ))
        elif current_price < sma_20 < sma_50:
            signals.append(TechnicalSignal(
                pair=pair,
                signal_type='sell',
                strength=0.6,
                timeframe='1d',
                entry_price=current_price,
                stop_loss=sma_50,
                take_profit=current_price * 0.985,
                confidence=0.5,
                indicators={'sma_20': sma_20, 'sma_50': sma_50},
                pattern='death_cross'
            ))
        
        # Pattern signals
        for pattern in patterns:
            if pattern['pattern'] in ['double_bottom', 'flag']:
                signals.append(TechnicalSignal(
                    pair=pair,
                    signal_type='buy',
                    strength=pattern['confidence'],
                    timeframe='4h',
                    entry_price=current_price,
                    stop_loss=current_price * 0.995,
                    take_profit=pattern['target'],
                    confidence=pattern['confidence'],
                    indicators={},
                    pattern=pattern['pattern']
                ))
            elif pattern['pattern'] in ['double_top', 'head_shoulders']:
                signals.append(TechnicalSignal(
                    pair=pair,
                    signal_type='sell',
                    strength=pattern['confidence'],
                    timeframe='4h',
                    entry_price=current_price,
                    stop_loss=current_price * 1.005,
                    take_profit=pattern['target'],
                    confidence=pattern['confidence'],
                    indicators={},
                    pattern=pattern['pattern']
                ))
        
        return signals
    
    def _calculate_sentiment(self, indicators: Dict, patterns: List) -> Dict[str, Any]:
        """Calculate overall technical sentiment"""
        sentiment_score = 0
        bullish_signals = 0
        bearish_signals = 0
        
        # RSI sentiment
        rsi = indicators.get('rsi', 50)
        if rsi < 40:
            sentiment_score += 0.3
            bullish_signals += 1
        elif rsi > 60:
            sentiment_score -= 0.3
            bearish_signals += 1
        
        # Moving average sentiment
        sma_20 = indicators.get('sma_20', 0)
        sma_50 = indicators.get('sma_50', 0)
        if sma_20 > sma_50:
            sentiment_score += 0.2
            bullish_signals += 1
        else:
            sentiment_score -= 0.2
            bearish_signals += 1
        
        # Pattern sentiment
        for pattern in patterns:
            if pattern['pattern'] in ['double_bottom', 'flag']:
                sentiment_score += 0.2
                bullish_signals += 1
            elif pattern['pattern'] in ['double_top', 'head_shoulders']:
                sentiment_score -= 0.2
                bearish_signals += 1
        
        # Determine overall sentiment
        if sentiment_score > 0.3:
            overall_sentiment = 'bullish'
        elif sentiment_score < -0.3:
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'sentiment': overall_sentiment,
            'score': sentiment_score,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'confidence': min(1.0, (bullish_signals + bearish_signals) / 5.0)
        }
    
    def _generate_summary(self, sentiment: Dict, patterns: List, signals: List) -> str:
        """Generate summary of technical analysis"""
        sentiment_text = sentiment['sentiment']
        confidence = sentiment['confidence']
        
        summary = f"Technical analysis shows {sentiment_text} sentiment with {confidence:.1%} confidence. "
        
        if patterns:
            pattern_names = [p['pattern'] for p in patterns]
            summary += f"Identified patterns: {', '.join(pattern_names)}. "
        
        if signals:
            buy_signals = len([s for s in signals if s.signal_type == 'buy'])
            sell_signals = len([s for s in signals if s.signal_type == 'sell'])
            summary += f"Generated {buy_signals} buy and {sell_signals} sell signals. "
        
        return summary
    
    def _get_default_analysis(self, pair: str) -> Dict[str, Any]:
        """Return default analysis when data is insufficient"""
        return {
            'pair': pair,
            'timestamp': datetime.now().isoformat(),
            'indicators': {},
            'patterns': [],
            'support_resistance': SupportResistance(
                pair=pair,
                support_levels=[],
                resistance_levels=[],
                current_price=1.0,
                strength={'support': 0.0, 'resistance': 0.0}
            ),
            'signals': [],
            'sentiment': {
                'sentiment': 'neutral',
                'score': 0.0,
                'bullish_signals': 0,
                'bearish_signals': 0,
                'confidence': 0.0
            },
            'summary': 'Insufficient data for technical analysis'
        }

# Create global instance
technical_analyzer = TechnicalAnalyzer()
