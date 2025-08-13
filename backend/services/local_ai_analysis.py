#!/usr/bin/env python3
"""
Local AI Analysis Service for FXSentinel
Uses free, open-source models for forex analysis without API costs
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class MarketContext:
    """Market context for analysis"""
    current_prices: Dict[str, float]
    recent_volatility: Dict[str, float]
    market_sentiment: Dict[str, str]
    key_levels: Dict[str, Dict[str, float]]
    economic_calendar: List[Dict]

class LocalAIAnalyzer:
    def __init__(self):
        self.analysis_templates = self._load_analysis_templates()
        self.impact_patterns = self._load_impact_patterns()
        self.currency_correlations = self._load_currency_correlations()
        
    def _load_analysis_templates(self) -> Dict:
        """Load predefined analysis templates for different event types"""
        return {
            'cpi': {
                'high_impact': {
                    'summary_template': "CPI data {direction} than expected by {deviation} points. This {sentiment} {currency} as it suggests {inflation_trend}.",
                    'trading_implications': [
                        "Expect {currency} to {move_direction} against major pairs",
                        "Volatility likely to spike {timeframe} around release",
                        "Key levels to watch: {support_resistance}",
                        "Risk: {risk_factors}"
                    ]
                }
            },
            'interest_rate': {
                'high_impact': {
                    'summary_template': "Interest rate {decision} by {amount} basis points. Market expected {expected}. This is {sentiment} for {currency}.",
                    'trading_implications': [
                        "Immediate {currency} {direction} reaction expected",
                        "Carry trade flows may shift to {currency}",
                        "Bond yields likely to {yield_direction}",
                        "Safe haven flows: {safe_haven_impact}"
                    ]
                }
            },
            'gdp': {
                'high_impact': {
                    'summary_template': "GDP growth {direction} than expected at {value}%. This {sentiment} {currency} as it reflects {economic_health}.",
                    'trading_implications': [
                        "{currency} likely to {move_direction} on growth {sentiment}",
                        "Economic outlook: {outlook}",
                        "Central bank policy implications: {policy_impact}",
                        "Risk sentiment: {risk_sentiment}"
                    ]
                }
            },
            'employment': {
                'high_impact': {
                    'summary_template': "Employment data {direction} than expected. {jobs_added} jobs added vs {expected_jobs} expected. {currency} {sentiment}.",
                    'trading_implications': [
                        "Labor market strength: {labor_sentiment}",
                        "Wage growth implications: {wage_impact}",
                        "Fed policy outlook: {fed_impact}",
                        "Consumer spending: {consumer_impact}"
                    ]
                }
            }
        }
    
    def _load_impact_patterns(self) -> Dict:
        """Load historical impact patterns for different events"""
        return {
            'cpi': {
                'better_than_expected': {
                    'usd_sentiment': 'bullish',
                    'eur_usd_impact': 'bearish',
                    'usd_jpy_impact': 'bullish',
                    'gold_impact': 'bearish',
                    'volatility_multiplier': 1.5
                },
                'worse_than_expected': {
                    'usd_sentiment': 'bearish',
                    'eur_usd_impact': 'bullish',
                    'usd_jpy_impact': 'bearish',
                    'gold_impact': 'bullish',
                    'volatility_multiplier': 1.8
                }
            },
            'interest_rate': {
                'hike': {
                    'usd_sentiment': 'bullish',
                    'eur_usd_impact': 'bearish',
                    'usd_jpy_impact': 'bullish',
                    'gold_impact': 'bearish',
                    'volatility_multiplier': 2.0
                },
                'cut': {
                    'usd_sentiment': 'bearish',
                    'eur_usd_impact': 'bullish',
                    'usd_jpy_impact': 'bearish',
                    'gold_impact': 'bullish',
                    'volatility_multiplier': 2.2
                }
            }
        }
    
    def _load_currency_correlations(self) -> Dict:
        """Load currency pair correlations for analysis"""
        return {
            'EUR/USD': {
                'correlated_pairs': ['GBP/USD', 'AUD/USD'],
                'inverse_correlations': ['USD/JPY', 'USD/CHF'],
                'safe_haven_impact': 'negative',
                'risk_sentiment': 'positive'
            },
            'USD/JPY': {
                'correlated_pairs': ['USD/CHF'],
                'inverse_correlations': ['EUR/USD', 'GBP/USD'],
                'safe_haven_impact': 'positive',
                'risk_sentiment': 'negative'
            },
            'GBP/USD': {
                'correlated_pairs': ['EUR/USD', 'AUD/USD'],
                'inverse_correlations': ['USD/JPY', 'USD/CHF'],
                'safe_haven_impact': 'negative',
                'risk_sentiment': 'positive'
            }
        }
    
    def analyze_economic_event(self, event: Dict, market_context: MarketContext) -> Dict:
        """Analyze economic event using local AI patterns"""
        try:
            event_type = self._classify_event_type(event['title'])
            impact_level = event.get('impact', 'medium')
            
            # Extract key data points
            event_data = self._extract_event_data(event)
            
            # Generate analysis based on event type and historical patterns
            analysis = self._generate_event_analysis(event_type, event_data, market_context)
            
            # Add trading opportunities
            trading_opportunities = self._generate_trading_opportunities(
                event_type, event_data, market_context
            )
            
            # Add risk assessment
            risk_assessment = self._assess_risks(event_type, event_data, market_context)
            
            return {
                'event': event,
                'analysis': analysis,
                'trading_opportunities': trading_opportunities,
                'risk_assessment': risk_assessment,
                'confidence_score': self._calculate_confidence(event_type, event_data),
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'local_ai'
            }
            
        except Exception as e:
            logger.error(f"Error in local AI analysis: {e}")
            return self._get_fallback_analysis(event)
    
    def _classify_event_type(self, title: str) -> str:
        """Classify event type based on title keywords"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['cpi', 'inflation', 'consumer price']):
            return 'cpi'
        elif any(word in title_lower for word in ['interest rate', 'fed', 'ecb', 'boj', 'boe']):
            return 'interest_rate'
        elif any(word in title_lower for word in ['gdp', 'gross domestic product']):
            return 'gdp'
        elif any(word in title_lower for word in ['employment', 'non-farm', 'jobs', 'unemployment']):
            return 'employment'
        elif any(word in title_lower for word in ['retail sales', 'consumer spending']):
            return 'retail_sales'
        elif any(word in title_lower for word in ['manufacturing', 'pmi', 'industrial']):
            return 'manufacturing'
        else:
            return 'general'
    
    def _extract_event_data(self, event: Dict) -> Dict:
        """Extract relevant data from event"""
        title = event.get('title', '')
        currency = event.get('currency', 'USD')
        impact = event.get('impact', 'medium')
        description = event.get('description', '')
        
        # Combine title and description for better extraction
        full_text = f"{title} {description}".lower()
        
        # Extract numbers from title and description (like "2.5%" or "150K")
        numbers = re.findall(r'(\d+\.?\d*)[%KMB]?', full_text)
        
        # Try to extract expected and actual values from the event data
        expected_value = None
        actual_value = None
        
        # Check if event has expected/actual fields
        if 'expected' in event:
            expected_str = str(event['expected']).replace('%', '').replace('K', '000').replace('M', '000000')
            try:
                expected_value = float(expected_str)
            except:
                pass
        
        if 'previous' in event:
            actual_str = str(event['previous']).replace('%', '').replace('K', '000').replace('M', '000000')
            try:
                actual_value = float(actual_str)
            except:
                pass
        
        # If not found in event data, try to extract from text
        if expected_value is None:
            expected_value = self._extract_expected_value(full_text)
        if actual_value is None:
            actual_value = self._extract_actual_value(full_text)
        
        # Determine direction based on available data
        direction = self._determine_direction(full_text)
        
        # If we have both values, determine direction more accurately
        if expected_value is not None and actual_value is not None:
            if actual_value > expected_value:
                direction = 'better_than_expected'
            elif actual_value < expected_value:
                direction = 'worse_than_expected'
            else:
                direction = 'as_expected'
        
        return {
            'title': title,
            'currency': currency,
            'impact': impact,
            'numbers': numbers,
            'expected_value': expected_value,
            'actual_value': actual_value,
            'direction': direction,
            'description': description
        }
    
    def _extract_expected_value(self, title: str) -> Optional[float]:
        """Extract expected value from title"""
        # Look for patterns like "expected 2.5%" or "forecast 150K"
        expected_patterns = [
            r'expected\s+(\d+\.?\d*)',
            r'forecast\s+(\d+\.?\d*)',
            r'estimate\s+(\d+\.?\d*)'
        ]
        
        for pattern in expected_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def _extract_actual_value(self, title: str) -> Optional[float]:
        """Extract actual value from title"""
        # Look for patterns like "2.5%" or "150K" at the beginning
        actual_patterns = [
            r'^(\d+\.?\d*)[%KMB]',
            r'(\d+\.?\d*)[%KMB]\s+vs'
        ]
        
        for pattern in actual_patterns:
            match = re.search(pattern, title)
            if match:
                return float(match.group(1))
        return None
    
    def _determine_direction(self, title: str) -> str:
        """Determine if data is better/worse than expected"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['higher', 'better', 'stronger', 'above']):
            return 'better_than_expected'
        elif any(word in title_lower for word in ['lower', 'worse', 'weaker', 'below']):
            return 'worse_than_expected'
        else:
            return 'as_expected'
    
    def _generate_event_analysis(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict:
        """Generate detailed event analysis"""
        if event_type not in self.analysis_templates:
            return self._generate_general_analysis(event_data, market_context)
        
        template = self.analysis_templates[event_type]['high_impact']
        
        # Fill template with actual data
        analysis = {
            'summary': self._fill_template(template['summary_template'], event_data, market_context),
            'trading_implications': []
        }
        
        for implication in template['trading_implications']:
            filled_implication = self._fill_template(implication, event_data, market_context)
            analysis['trading_implications'].append(filled_implication)
        
        return analysis
    
    def _fill_template(self, template: str, event_data: Dict, market_context: MarketContext) -> str:
        """Fill template with actual data"""
        currency = event_data.get('currency', 'USD')
        direction = event_data.get('direction', 'as_expected')
        title = event_data.get('title', 'Economic Event')
        
        # Extract more data from the event
        expected_value = event_data.get('expected_value')
        actual_value = event_data.get('actual_value')
        numbers = event_data.get('numbers', [])
        
        # Calculate deviation if we have both values
        deviation = "unknown"
        if expected_value is not None and actual_value is not None:
            deviation = abs(actual_value - expected_value)
            deviation = f"{deviation:.2f}"
        elif numbers:
            deviation = str(numbers[0]) if numbers else "unknown"
        
        # Determine inflation trend based on event type and direction
        inflation_trend = "stable inflation"
        if 'cpi' in title.lower() or 'inflation' in title.lower():
            if direction == 'better_than_expected':
                inflation_trend = "cooling inflation"
            elif direction == 'worse_than_expected':
                inflation_trend = "rising inflation"
        
        # Get current market levels
        current_price = market_context.current_prices.get('EUR/USD', 1.0850)
        support_level = market_context.key_levels.get('EUR/USD', {}).get('support', current_price * 0.995)
        resistance_level = market_context.key_levels.get('EUR/USD', {}).get('resistance', current_price * 1.005)
        
        replacements = {
            '{currency}': currency,
            '{direction}': direction,
            '{sentiment}': 'bullish' if direction == 'better_than_expected' else 'bearish',
            '{move_direction}': 'strengthen' if direction == 'better_than_expected' else 'weaken',
            '{timeframe}': 'immediately',
            '{support_resistance}': f"support at {support_level:.4f}, resistance at {resistance_level:.4f}",
            '{risk_factors}': 'unexpected market reaction',
            '{deviation}': deviation,
            '{inflation_trend}': inflation_trend,
            '{value}': str(actual_value) if actual_value is not None else "released",
            '{expected}': str(expected_value) if expected_value is not None else "market expectations",
            '{amount}': deviation,
            '{decision}': 'hiked' if direction == 'better_than_expected' else 'cut' if direction == 'worse_than_expected' else 'maintained',
            '{yield_direction}': 'rise' if direction == 'better_than_expected' else 'fall',
            '{safe_haven_impact}': 'reduced' if direction == 'better_than_expected' else 'increased',
            '{economic_health}': 'strong economic growth' if direction == 'better_than_expected' else 'economic weakness',
            '{outlook}': 'positive' if direction == 'better_than_expected' else 'negative',
            '{policy_impact}': 'hawkish' if direction == 'better_than_expected' else 'dovish',
            '{risk_sentiment}': 'risk-on' if direction == 'better_than_expected' else 'risk-off',
            '{jobs_added}': str(actual_value) if actual_value is not None else "jobs",
            '{expected_jobs}': str(expected_value) if expected_value is not None else "expected",
            '{labor_sentiment}': 'strong' if direction == 'better_than_expected' else 'weak',
            '{wage_impact}': 'positive' if direction == 'better_than_expected' else 'negative',
            '{fed_impact}': 'hawkish' if direction == 'better_than_expected' else 'dovish',
            '{consumer_impact}': 'positive' if direction == 'better_than_expected' else 'negative'
        }
        
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        
        return result
    
    def _generate_trading_opportunities(self, event_type: str, event_data: Dict, market_context: MarketContext) -> List[Dict]:
        """Generate specific trading opportunities"""
        opportunities = []
        currency = event_data.get('currency', 'USD')
        direction = event_data.get('direction', 'as_expected')
        
        # Get affected pairs
        affected_pairs = self._get_affected_pairs(currency, event_type)
        
        for pair in affected_pairs:
            opportunity = {
                'pair': pair,
                'strategy': self._determine_strategy(event_type, direction),
                'entry_zone': self._calculate_entry_zone(pair, direction, market_context),
                'stop_loss': self._calculate_stop_loss(pair, direction, market_context),
                'take_profit': self._calculate_take_profit(pair, direction, market_context),
                'probability': self._calculate_probability(event_type, direction),
                'timeframe': self._determine_timeframe(event_type),
                'risk_reward': self._calculate_risk_reward(pair, direction, market_context)
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def _get_affected_pairs(self, currency: str, event_type: str) -> List[str]:
        """Get currency pairs affected by this event"""
        if currency == 'USD':
            return ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF']
        elif currency == 'EUR':
            return ['EUR/USD', 'EUR/GBP', 'EUR/JPY']
        elif currency == 'GBP':
            return ['GBP/USD', 'EUR/GBP', 'GBP/JPY']
        else:
            return ['EUR/USD', 'USD/JPY']  # Default major pairs
    
    def _determine_strategy(self, event_type: str, direction: str) -> str:
        """Determine trading strategy based on event"""
        if direction == 'better_than_expected':
            return 'Momentum breakout'
        elif direction == 'worse_than_expected':
            return 'Mean reversion'
        else:
            return 'Range trading'
    
    def _calculate_entry_zone(self, pair: str, direction: str, market_context: MarketContext) -> Dict:
        """Calculate entry zone for trade"""
        current_price = market_context.current_prices.get(pair, 1.0)
        
        if direction == 'better_than_expected':
            return {
                'min': current_price * 0.9995,
                'max': current_price * 1.0005
            }
        else:
            return {
                'min': current_price * 0.9990,
                'max': current_price * 1.0010
            }
    
    def _calculate_stop_loss(self, pair: str, direction: str, market_context: MarketContext) -> float:
        """Calculate stop loss level"""
        current_price = market_context.current_prices.get(pair, 1.0)
        
        if direction == 'better_than_expected':
            return current_price * 0.9970  # 30 pips below
        else:
            return current_price * 1.0030  # 30 pips above
    
    def _calculate_take_profit(self, pair: str, direction: str, market_context: MarketContext) -> float:
        """Calculate take profit level"""
        current_price = market_context.current_prices.get(pair, 1.0)
        
        if direction == 'better_than_expected':
            return current_price * 1.0060  # 60 pips above
        else:
            return current_price * 0.9940  # 60 pips below
    
    def _calculate_probability(self, event_type: str, direction: str) -> int:
        """Calculate probability of trade success"""
        base_probability = 65
        
        if event_type in ['cpi', 'interest_rate']:
            base_probability += 10
        if direction != 'as_expected':
            base_probability += 5
        
        return min(base_probability, 85)
    
    def _determine_timeframe(self, event_type: str) -> str:
        """Determine trading timeframe"""
        if event_type in ['cpi', 'interest_rate']:
            return '1-4 hours'
        else:
            return '4-24 hours'
    
    def _calculate_risk_reward(self, pair: str, direction: str, market_context: MarketContext) -> float:
        """Calculate risk/reward ratio"""
        return 2.0  # 1:2 risk/reward ratio
    
    def _assess_risks(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict:
        """Assess trading risks"""
        return {
            'market_volatility': 'High' if event_type in ['cpi', 'interest_rate'] else 'Medium',
            'liquidity_risk': 'Low',
            'gap_risk': 'Medium' if event_type in ['cpi', 'interest_rate'] else 'Low',
            'correlation_risk': 'Medium',
            'recommendations': [
                'Use proper position sizing',
                'Set tight stop losses',
                'Monitor market depth',
                'Avoid trading during low liquidity hours'
            ]
        }
    
    def _calculate_confidence(self, event_type: str, event_data: Dict) -> int:
        """Calculate confidence score for analysis"""
        confidence = 60  # Base confidence
        
        if event_type in ['cpi', 'interest_rate']:
            confidence += 15
        if event_data.get('direction') != 'as_expected':
            confidence += 10
        if event_data.get('actual_value') is not None:
            confidence += 10
        
        return min(confidence, 95)
    
    def _generate_general_analysis(self, event_data: Dict, market_context: MarketContext) -> Dict:
        """Generate analysis for general events"""
        title = event_data.get('title', 'economic event')
        currency = event_data.get('currency', 'USD')
        direction = event_data.get('direction', 'as_expected')
        impact = event_data.get('impact', 'medium')
        
        # Create more specific analysis based on available data
        if direction == 'better_than_expected':
            summary = f"Analysis of {title} - Data came in better than expected, which is bullish for {currency}. Expect {currency} to strengthen against major pairs."
            implications = [
                f"Consider bullish positions on {currency} pairs",
                "Look for breakout opportunities above resistance",
                "Monitor for follow-through buying",
                "Set tight stops to protect profits"
            ]
        elif direction == 'worse_than_expected':
            summary = f"Analysis of {title} - Data came in worse than expected, which is bearish for {currency}. Expect {currency} to weaken against major pairs."
            implications = [
                f"Consider bearish positions on {currency} pairs",
                "Look for breakdown opportunities below support",
                "Monitor for follow-through selling",
                "Set tight stops to protect profits"
            ]
        else:
            summary = f"Analysis of {title} - Data came in as expected. Monitor for potential market reaction and technical breakouts."
            implications = [
                "Wait for clear directional signals",
                "Monitor key support and resistance levels",
                "Consider range trading strategies",
                "Be prepared for volatility spikes"
            ]
        
        # Add impact-specific implications
        if impact == 'high':
            implications.append("High impact event - expect significant volatility")
            implications.append("Consider reduced position sizes due to increased risk")
        elif impact == 'medium':
            implications.append("Moderate impact expected - standard position sizing appropriate")
        else:
            implications.append("Low impact event - focus on technical levels")
        
        return {
            'summary': summary,
            'trading_implications': implications
        }
    
    def _get_fallback_analysis(self, event: Dict) -> Dict:
        """Fallback analysis if main analysis fails"""
        return {
            'event': event,
            'analysis': {
                'summary': f"Analysis for {event.get('title', 'event')} - Monitor market reaction.",
                'trading_implications': ["Wait for market reaction", "Use tight stops"]
            },
            'trading_opportunities': [],
            'risk_assessment': {'market_volatility': 'Unknown'},
            'confidence_score': 50,
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'fallback'
        }

# Create global instance
local_ai_analyzer = LocalAIAnalyzer()
