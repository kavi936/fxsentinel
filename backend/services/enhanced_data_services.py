#!/usr/bin/env python3
"""
Enhanced Data Services for Professional AI Analysis
Provides historical context, central bank intelligence, and real-time market data
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import os

logger = logging.getLogger(__name__)

class HistoricalDataService:
    """Service for historical economic data and market reactions"""
    
    def __init__(self):
        self.historical_cache = {}
        self.surprise_calculations = {}
        
    def get_release_history(self, indicator: str, currency: str) -> Dict[str, Any]:
        """Get last 6 releases with market reactions"""
        
        # Mock historical data - in production, this would come from APIs
        historical_data = {
            'unemployment': {
                'GBP': [
                    {'date': '2024-01-15', 'actual': '4.7%', 'expected': '4.7%', 'previous': '4.7%', 'market_reaction': 'neutral', 'gbp_usd_move': 0.0005},
                    {'date': '2024-01-08', 'actual': '4.8%', 'expected': '4.7%', 'previous': '4.7%', 'market_reaction': 'bearish', 'gbp_usd_move': -0.0020},
                    {'date': '2024-01-01', 'actual': '4.6%', 'expected': '4.8%', 'previous': '4.8%', 'market_reaction': 'bullish', 'gbp_usd_move': 0.0030},
                    {'date': '2023-12-25', 'actual': '4.7%', 'expected': '4.7%', 'previous': '4.6%', 'market_reaction': 'neutral', 'gbp_usd_move': 0.0002},
                    {'date': '2023-12-18', 'actual': '4.9%', 'expected': '4.7%', 'previous': '4.7%', 'market_reaction': 'bearish', 'gbp_usd_move': -0.0040},
                    {'date': '2023-12-11', 'actual': '4.5%', 'expected': '4.8%', 'previous': '4.9%', 'market_reaction': 'bullish', 'gbp_usd_move': 0.0050}
                ],
                'USD': [
                    {'date': '2024-01-15', 'actual': '3.7%', 'expected': '3.7%', 'previous': '3.7%', 'market_reaction': 'neutral', 'usd_jpy_move': 0.0003},
                    {'date': '2024-01-08', 'actual': '3.8%', 'expected': '3.7%', 'previous': '3.7%', 'market_reaction': 'bearish', 'usd_jpy_move': -0.0015},
                    {'date': '2024-01-01', 'actual': '3.6%', 'expected': '3.8%', 'previous': '3.8%', 'market_reaction': 'bullish', 'usd_jpy_move': 0.0025}
                ]
            },
            'cpi': {
                'GBP': [
                    {'date': '2024-01-15', 'actual': '4.0%', 'expected': '4.1%', 'previous': '4.2%', 'market_reaction': 'bullish', 'gbp_usd_move': 0.0030},
                    {'date': '2024-01-08', 'actual': '4.3%', 'expected': '4.0%', 'previous': '4.0%', 'market_reaction': 'bearish', 'gbp_usd_move': -0.0040},
                    {'date': '2024-01-01', 'actual': '3.8%', 'expected': '4.3%', 'previous': '4.3%', 'market_reaction': 'bullish', 'gbp_usd_move': 0.0050}
                ]
            }
        }
        
        indicator_lower = indicator.lower()
        if 'unemployment' in indicator_lower:
            key = 'unemployment'
        elif 'cpi' in indicator_lower or 'inflation' in indicator_lower:
            key = 'cpi'
        else:
            key = 'unemployment'  # Default fallback
        
        releases = historical_data.get(key, {}).get(currency, [])
        
        return {
            'last_6_releases': releases[:6],
            'last_3_releases': releases[:3],
            'avg_surprise': self._calculate_average_surprise(releases),
            'trend_direction': self._calculate_trend_direction(releases),
            'volatility_pattern': self._calculate_volatility_pattern(releases),
            'market_reaction_pattern': self._calculate_market_reaction_pattern(releases)
        }
    
    def _calculate_average_surprise(self, releases: List[Dict]) -> float:
        """Calculate average surprise magnitude"""
        if not releases:
            return 0.0
        
        surprises = []
        for release in releases:
            try:
                actual = float(str(release['actual']).replace('%', ''))
                expected = float(str(release['expected']).replace('%', ''))
                surprise = abs(actual - expected)
                surprises.append(surprise)
            except (ValueError, TypeError):
                continue
        
        return sum(surprises) / len(surprises) if surprises else 0.0
    
    def _calculate_trend_direction(self, releases: List[Dict]) -> str:
        """Calculate trend direction from recent releases"""
        if len(releases) < 3:
            return 'stable'
        
        try:
            recent_values = []
            for release in releases[:3]:
                value = float(str(release['actual']).replace('%', ''))
                recent_values.append(value)
            
            if recent_values[0] < recent_values[1] < recent_values[2]:
                return 'improving'
            elif recent_values[0] > recent_values[1] > recent_values[2]:
                return 'deteriorating'
            else:
                return 'stable'
        except (ValueError, TypeError):
            return 'stable'
    
    def _calculate_volatility_pattern(self, releases: List[Dict]) -> Dict[str, Any]:
        """Calculate typical volatility around releases"""
        if not releases:
            return {'avg_move': 0.0, 'volatility_level': 'low'}
        
        moves = [abs(release.get('gbp_usd_move', 0)) for release in releases]
        avg_move = sum(moves) / len(moves)
        
        if avg_move > 0.003:
            volatility_level = 'high'
        elif avg_move > 0.001:
            volatility_level = 'medium'
        else:
            volatility_level = 'low'
        
        return {
            'avg_move': avg_move,
            'volatility_level': volatility_level,
            'max_move': max(moves) if moves else 0.0,
            'min_move': min(moves) if moves else 0.0
        }
    
    def _calculate_market_reaction_pattern(self, releases: List[Dict]) -> Dict[str, Any]:
        """Calculate typical market reaction patterns"""
        if not releases:
            return {'bullish_count': 0, 'bearish_count': 0, 'neutral_count': 0}
        
        reactions = [release.get('market_reaction', 'neutral') for release in releases]
        bullish_count = reactions.count('bullish')
        bearish_count = reactions.count('bearish')
        neutral_count = reactions.count('neutral')
        
        return {
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count,
            'dominant_reaction': max(set(reactions), key=reactions.count) if reactions else 'neutral'
        }

class CentralBankService:
    """Service for central bank intelligence and policy context"""
    
    def __init__(self):
        self.policy_cache = {}
        self.rate_probabilities = {}
        
    def get_policy_context(self, currency: str) -> Dict[str, Any]:
        """Get latest central bank policy context"""
        
        # Mock central bank data - in production, this would come from APIs
        central_bank_data = {
            'GBP': {
                'central_bank': 'Bank of England',
                'current_rate': 5.25,
                'policy_stance': 'cautious',
                'next_meeting': '2024-02-01',
                'rate_probabilities': {
                    'hold': 0.70,
                    'hike_25bps': 0.25,
                    'cut_25bps': 0.05
                },
                'latest_statements': [
                    'BoE maintains cautious stance on inflation',
                    'Rate cuts not expected until mid-2024',
                    'Focus on wage growth and services inflation'
                ],
                'key_concerns': ['wage growth', 'services inflation', 'economic growth'],
                'forward_guidance': 'Data-dependent approach, no pre-commitment to rate path'
            },
            'USD': {
                'central_bank': 'Federal Reserve',
                'current_rate': 5.50,
                'policy_stance': 'data-dependent',
                'next_meeting': '2024-01-31',
                'rate_probabilities': {
                    'hold': 0.85,
                    'hike_25bps': 0.10,
                    'cut_25bps': 0.05
                },
                'latest_statements': [
                    'Fed signals potential rate cuts in 2024',
                    'Inflation moving toward 2% target',
                    'Labor market remains strong'
                ],
                'key_concerns': ['inflation', 'employment', 'economic growth'],
                'forward_guidance': 'Higher for longer approach, data-dependent decisions'
            },
            'EUR': {
                'central_bank': 'European Central Bank',
                'current_rate': 4.50,
                'policy_stance': 'hawkish',
                'next_meeting': '2024-01-25',
                'rate_probabilities': {
                    'hold': 0.90,
                    'hike_25bps': 0.08,
                    'cut_25bps': 0.02
                },
                'latest_statements': [
                    'ECB maintains restrictive stance',
                    'Inflation remains above target',
                    'Economic growth concerns mounting'
                ],
                'key_concerns': ['inflation', 'economic growth', 'geopolitical risks'],
                'forward_guidance': 'Restrictive policy stance maintained'
            }
        }
        
        return central_bank_data.get(currency, {
            'central_bank': 'Central Bank',
            'current_rate': 0.0,
            'policy_stance': 'neutral',
            'next_meeting': 'Unknown',
            'rate_probabilities': {'hold': 1.0},
            'latest_statements': [],
            'key_concerns': [],
            'forward_guidance': 'Data-dependent approach'
        })
    
    def get_rate_expectations(self, currency: str) -> Dict[str, Any]:
        """Get market-implied rate expectations"""
        policy_context = self.get_policy_context(currency)
        
        return {
            'current_rate': policy_context['current_rate'],
            'next_meeting_probabilities': policy_context['rate_probabilities'],
            'policy_stance': policy_context['policy_stance'],
            'next_meeting_date': policy_context['next_meeting'],
            'forward_guidance': policy_context['forward_guidance']
        }

class MarketDataService:
    """Service for real-time market data and context"""
    
    def __init__(self):
        self.price_cache = {}
        self.volatility_cache = {}
        
    def get_real_time_context(self, currency_pairs: List[str]) -> Dict[str, Any]:
        """Get live market context for currency pairs"""
        
        # Mock real-time data - in production, this would come from live APIs
        current_prices = {
            'GBP/USD': 1.2650,
            'EUR/USD': 1.0850,
            'USD/JPY': 148.50,
            'EUR/GBP': 0.8575,
            'GBP/JPY': 187.85,
            'USD/CHF': 0.8650,
            'AUD/USD': 0.6650,
            'USD/CAD': 1.3550
        }
        
        volatility_data = {
            'GBP/USD': {'current': 0.010, 'avg_24h': 0.008, 'trend': 'increasing'},
            'EUR/USD': {'current': 0.008, 'avg_24h': 0.007, 'trend': 'stable'},
            'USD/JPY': {'current': 0.012, 'avg_24h': 0.011, 'trend': 'decreasing'},
            'EUR/GBP': {'current': 0.006, 'avg_24h': 0.005, 'trend': 'stable'}
        }
        
        sentiment_data = {
            'GBP/USD': {'sentiment': 'bearish', 'strength': 0.6},
            'EUR/USD': {'sentiment': 'neutral', 'strength': 0.4},
            'USD/JPY': {'sentiment': 'bullish', 'strength': 0.7},
            'EUR/GBP': {'sentiment': 'neutral', 'strength': 0.3}
        }
        
        key_levels = {
            'GBP/USD': {
                'support': [1.2600, 1.2550, 1.2500],
                'resistance': [1.2700, 1.2750, 1.2800],
                'pivot': 1.2650
            },
            'EUR/USD': {
                'support': [1.0800, 1.0750, 1.0700],
                'resistance': [1.0900, 1.0950, 1.1000],
                'pivot': 1.0850
            },
            'USD/JPY': {
                'support': [148.00, 147.50, 147.00],
                'resistance': [149.00, 149.50, 150.00],
                'pivot': 148.50
            }
        }
        
        return {
            'current_prices': {pair: current_prices.get(pair, 0.0) for pair in currency_pairs},
            'volatility': {pair: volatility_data.get(pair, {'current': 0.0, 'avg_24h': 0.0, 'trend': 'stable'}) for pair in currency_pairs},
            'sentiment': {pair: sentiment_data.get(pair, {'sentiment': 'neutral', 'strength': 0.5}) for pair in currency_pairs},
            'key_levels': {pair: key_levels.get(pair, {'support': [], 'resistance': [], 'pivot': 0.0}) for pair in currency_pairs},
            'market_hours': {
                'london_open': True,
                'new_york_open': True,
                'tokyo_open': False,
                'liquidity_level': 'high'
            }
        }
    
    def get_correlation_signals(self, currency: str) -> Dict[str, Any]:
        """Get correlation signals for the currency"""
        
        correlation_data = {
            'GBP': {
                'equity_correlation': 0.3,  # Positive correlation with UK stocks
                'bond_correlation': -0.4,   # Negative correlation with UK bonds
                'commodity_correlation': 0.1,  # Low correlation with commodities
                'risk_sentiment': 'risk_on',  # GBP tends to be risk-on
                'safe_haven_status': False
            },
            'USD': {
                'equity_correlation': -0.2,  # Negative correlation with US stocks
                'bond_correlation': 0.6,     # Positive correlation with US bonds
                'commodity_correlation': -0.3,  # Negative correlation with commodities
                'risk_sentiment': 'risk_off',  # USD tends to be risk-off
                'safe_haven_status': True
            },
            'EUR': {
                'equity_correlation': 0.2,   # Low positive correlation with EU stocks
                'bond_correlation': -0.3,    # Negative correlation with EU bonds
                'commodity_correlation': 0.0,  # No correlation with commodities
                'risk_sentiment': 'neutral',  # EUR is neutral
                'safe_haven_status': False
            }
        }
        
        return correlation_data.get(currency, {
            'equity_correlation': 0.0,
            'bond_correlation': 0.0,
            'commodity_correlation': 0.0,
            'risk_sentiment': 'neutral',
            'safe_haven_status': False
        })

# Global instances
historical_service = HistoricalDataService()
central_bank_service = CentralBankService()
market_data_service = MarketDataService()
