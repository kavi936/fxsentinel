#!/usr/bin/env python3
"""
Enhanced AI Analysis Service for FXSentinel
Implements comprehensive 6-point analysis framework for macro news
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class MarketContext:
    """Enhanced market context for comprehensive analysis"""
    current_prices: Dict[str, float]
    recent_volatility: Dict[str, float]
    market_sentiment: Dict[str, str]
    key_levels: Dict[str, Dict[str, float]]
    economic_calendar: List[Dict]
    bond_yields: Dict[str, float]
    equity_indices: Dict[str, float]
    commodity_prices: Dict[str, float]
    central_bank_expectations: Dict[str, Dict[str, Any]] = None
    historical_reactions: Dict[str, List[Dict]] = None
    retail_sentiment: Dict[str, float] = None
    futures_positioning: Dict[str, float] = None
    institutional_flow: Dict[str, float] = None
    time_to_event: int = None
    liquidity_level: int = None
    scenario_probabilities: Dict[str, float] = None

@dataclass
class ComprehensiveAnalysis:
    """Complete analysis result covering all 6 framework areas"""
    # 1. Immediate Market Impact
    immediate_impact: Dict[str, Any]
    
    # 2. Long-term Market Impact  
    long_term_impact: Dict[str, Any]
    
    # 3. Context vs Expectations
    context_expectations: Dict[str, Any]
    
    # 4. Sentiment Analysis
    sentiment_analysis: Dict[str, Any]
    
    # 5. Macro & Cross-Market Links
    cross_market_links: Dict[str, Any]
    
    # 6. Market Shifts Analysis
    market_shifts: Dict[str, Any]
    
    # 7. Big Picture Implications
    big_picture: Dict[str, Any]
    
    # Meta data
    confidence_score: float
    analysis_timestamp: str
    event_id: str
    analysis_type: str = "comprehensive_6_point_framework"
    data_warning: Optional[Dict[str, Any]] = None

class EnhancedAIAnalyzer:
    def __init__(self):
        print(f"🔍 DEBUG: EnhancedAIAnalyzer __init__ starting...")
        self.event_templates = self._load_event_templates()
        print(f"🔍 DEBUG: Event templates loaded")
        self.historical_patterns = self._load_historical_patterns()
        print(f"🔍 DEBUG: Historical patterns loaded")
        self.cross_market_correlations = self._load_cross_market_correlations()
        print(f"🔍 DEBUG: Cross market correlations loaded")
        self.central_bank_policies = self._load_central_bank_policies()
        print(f"🔍 DEBUG: Central bank policies loaded")
        print(f"🔍 DEBUG: EnhancedAIAnalyzer __init__ completed")
        
    def analyze_macro_event(self, event: Dict, market_context: MarketContext, 
                          analysis_type: str = "post_event") -> ComprehensiveAnalysis:
        """
        Comprehensive analysis following the 6-point framework
        
        Args:
            event: Economic event data
            market_context: Current market conditions
            analysis_type: "pre_event" (before news) or "post_event" (after news)
        """
        try:
            print(f"🔍 DEBUG: Starting analyze_macro_event...")
            print(f"🔍 DEBUG: Event title: {event.get('title', 'Unknown')}")
            print(f"🔍 DEBUG: Market context type: {type(market_context)}")
            event_type = self._classify_event_type(event['title'])
            print(f"🔍 DEBUG: Event type classified as: {event_type}")
            event_data = self._extract_event_data(event)
            print(f"🔍 DEBUG: Event data extracted: {event_data}")
            
            if analysis_type == "pre_event":
                return self._analyze_pre_event(event_type, event_data, market_context)
            else:
                return self._analyze_post_event(event_type, event_data, market_context)
                
        except Exception as e:
            logger.error(f"Error in enhanced AI analysis: {e}")
            return self._get_fallback_analysis(event)
    
    def _analyze_pre_event(self, event_type: str, event_data: Dict, market_context: MarketContext) -> ComprehensiveAnalysis:
        """Pre-event analysis: What to expect, historical context, preparation"""
        
        # 1. Event Understanding & Context
        event_context = self._analyze_event_context(event_type, event_data, market_context)
        
        # 2. Historical Analysis
        historical_analysis = self._analyze_historical_context(event_type, event_data, market_context)
        
        # 3. Market Expectations
        expectations_analysis = self._analyze_market_expectations(event_type, event_data, market_context)
        
        # 4. Pre-event Sentiment
        pre_event_sentiment = self._analyze_pre_event_sentiment(event_type, event_data, market_context)
        
        # 5. Cross-market Context
        cross_market_context = self._analyze_pre_event_cross_market(event_type, event_data, market_context)
        
        # 6. Preparation Strategy
        preparation_strategy = self._generate_preparation_strategy(event_type, event_data, market_context)
        
        # 7. Risk Assessment
        pre_event_risk = self._assess_pre_event_risks(event_type, event_data, market_context)
        
        # Create base analysis
        analysis_result = ComprehensiveAnalysis(
            immediate_impact=event_context,
            long_term_impact=historical_analysis,
            context_expectations=expectations_analysis,
            sentiment_analysis=pre_event_sentiment,
            cross_market_links=cross_market_context,
            market_shifts=preparation_strategy,
            big_picture=pre_event_risk,
            confidence_score=self._calculate_pre_event_confidence(event_type, event_data, market_context),
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event_data.get('id', 'unknown')),
            analysis_type="pre_event_analysis"
        )
        
        # Update analysis for missing data if needed
        return self._update_analysis_for_missing_data(analysis_result, event_data)
    
    def _analyze_post_event(self, event_type: str, event_data: Dict, market_context: MarketContext) -> ComprehensiveAnalysis:
        """Post-event analysis: Actual impact, market shifts, trading opportunities"""
        
        # 1. Immediate Market Impact
        immediate_impact = self._analyze_immediate_impact(event_type, event_data, market_context, "post_event")
        
        # 2. Long-term Market Impact
        long_term_impact = self._analyze_long_term_impact(event_type, event_data, market_context)
        
        # 3. Context vs Expectations
        context_expectations = self._analyze_context_expectations(event_type, event_data, market_context)
        
        # 4. Sentiment Analysis
        sentiment_analysis = self._analyze_sentiment(event_type, event_data, market_context)
        
        # 5. Macro & Cross-Market Links
        cross_market_links = self._analyze_cross_market_links(event_type, event_data, market_context)
        
        # 6. Market Shifts Analysis
        market_shifts = self._analyze_market_shifts(event_type, event_data, market_context, "post_event")
        
        # 7. Big Picture Implications
        big_picture = self._analyze_big_picture(event_type, event_data, market_context)
        
        # Create base analysis
        analysis_result = ComprehensiveAnalysis(
            immediate_impact=immediate_impact,
            long_term_impact=long_term_impact,
            context_expectations=context_expectations,
            sentiment_analysis=sentiment_analysis,
            cross_market_links=cross_market_links,
            market_shifts=market_shifts,
            big_picture=big_picture,
            confidence_score=self._calculate_confidence(event_type, event_data, market_context),
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event_data.get('id', 'unknown')),
            analysis_type="post_event_analysis"
        )
        
        # Update analysis for missing data if needed
        return self._update_analysis_for_missing_data(analysis_result, event_data)
    
    def _analyze_immediate_impact(self, event_type: str, event_data: Dict, 
                                market_context: MarketContext, analysis_type: str) -> Dict[str, Any]:
        """1. Immediate Market Impact Analysis"""
        
        currency = event_data.get('currency', 'USD')
        direction = event_data.get('direction', 'as_expected')
        impact_level = event_data.get('impact', 'medium')
        has_economic_data = event_data.get('has_economic_data', False)
        
        # Determine immediate direction based on available data
        if has_economic_data and direction == 'better_than_expected':
            immediate_direction = 'bullish' if currency == 'USD' else 'bearish'
            magnitude = 'high' if impact_level == 'high' else 'medium'
        elif has_economic_data and direction == 'worse_than_expected':
            immediate_direction = 'bearish' if currency == 'USD' else 'bullish'
            magnitude = 'high' if impact_level == 'high' else 'medium'
        else:
            # No economic data available - base on event type and impact
            immediate_direction = self._determine_direction_from_event_type(event_type, currency)
            magnitude = 'high' if impact_level == 'high' else 'medium'
        
        # Get affected assets
        affected_pairs = self._get_affected_pairs(currency, event_type)
        affected_assets = {
            'currency_pairs': affected_pairs,
            'commodities': self._get_affected_commodities(event_type, currency),
            'indices': self._get_affected_indices(event_type, currency)
        }
        
        # Calculate expected volatility
        print(f"🔍 DEBUG: About to calculate volatility...")
        base_volatility_raw = market_context.recent_volatility.get('EUR/USD', 0.008)
        print(f"🔍 DEBUG: base_volatility_raw = {base_volatility_raw} (type: {type(base_volatility_raw)})")
        
        # Convert string volatility to float if needed
        if isinstance(base_volatility_raw, str):
            volatility_conversion = {
                'low': 0.005,
                'medium': 0.010,
                'high': 0.020
            }
            base_volatility = volatility_conversion.get(base_volatility_raw.lower(), 0.010)
        else:
            base_volatility = base_volatility_raw
            
        print(f"🔍 DEBUG: base_volatility = {base_volatility} (type: {type(base_volatility)})")
        volatility_multiplier = self._get_volatility_multiplier(event_type, direction, impact_level)
        print(f"🔍 DEBUG: volatility_multiplier = {volatility_multiplier} (type: {type(volatility_multiplier)})")
        expected_volatility = base_volatility * volatility_multiplier
        print(f"🔍 DEBUG: expected_volatility = {expected_volatility}")
        
        # Timeframe for immediate impact
        print(f"🔍 DEBUG: About to calculate key levels...")
        if analysis_type == "pre_event":
            timeframe = "First 15-30 minutes after release"
            key_levels = self._get_key_levels_for_pairs(affected_pairs, market_context)
        else:
            timeframe = "Immediate reaction observed"
            key_levels = self._get_current_levels_for_pairs(affected_pairs, market_context)
        print(f"🔍 DEBUG: Key levels calculated successfully")
        
        return {
            'direction': immediate_direction,
            'magnitude': magnitude,
            'affected_assets': affected_assets,
            'expected_volatility': expected_volatility,
            'timeframe': timeframe,
            'key_levels': key_levels,
            'risk_level': 'high' if impact_level == 'high' else 'medium',
            'liquidity_impact': self._assess_liquidity_impact(event_type, impact_level)
        }
    
    def _analyze_long_term_impact(self, event_type: str, event_data: Dict, 
                                market_context: MarketContext) -> Dict[str, Any]:
        """2. Long-term Market Impact Analysis"""
        
        currency = event_data.get('currency', 'USD')
        direction = event_data.get('direction', 'as_expected')
        
        # Determine long-term sentiment
        if direction == 'better_than_expected':
            long_term_sentiment = 'positive'
            economic_outlook = 'strengthening'
        elif direction == 'worse_than_expected':
            long_term_sentiment = 'negative'
            economic_outlook = 'weakening'
        else:
            long_term_sentiment = 'neutral'
            economic_outlook = 'stable'
        
        # Policy implications
        policy_implications = self._analyze_policy_implications(event_type, direction, currency)
        
        # Economic cycle impact
        cycle_impact = self._analyze_economic_cycle_impact(event_type, direction)
        
        # Currency strength projection
        currency_projection = self._project_currency_strength(currency, direction, event_type)
        
        return {
            'sentiment': long_term_sentiment,
            'economic_outlook': economic_outlook,
            'policy_implications': policy_implications,
            'cycle_impact': cycle_impact,
            'currency_projection': currency_projection,
            'timeframe': '1-4 weeks',
            'confidence': self._calculate_long_term_confidence(event_type, direction)
        }
    
    def _analyze_context_expectations(self, event_type: str, event_data: Dict, 
                                    market_context: MarketContext) -> Dict[str, Any]:
        """3. Context vs Expectations Analysis"""
        
        # Check if event was priced in
        priced_in_status = self._assess_priced_in_status(event_type, event_data, market_context)
        
        # Calculate deviation from forecast
        deviation_analysis = self._calculate_deviation(event_data)
        
        # Historical reaction analysis
        historical_reactions = self._analyze_historical_reactions(event_type, event_data, market_context)
        
        # Market positioning
        positioning_analysis = self._analyze_market_positioning(event_type, event_data, market_context)
        
        # Surprise factor
        surprise_factor = self._calculate_surprise_factor(event_data, deviation_analysis)
        
        return {
            'priced_in_status': priced_in_status,
            'deviation_analysis': deviation_analysis,
            'historical_reactions': historical_reactions,
            'market_positioning': positioning_analysis,
            'surprise_factor': surprise_factor,
            'expectations_vs_reality': self._compare_expectations_reality(event_data)
        }
    
    def _analyze_sentiment(self, event_type: str, event_data: Dict, 
                          market_context: MarketContext) -> Dict[str, Any]:
        """4. Sentiment Analysis"""
        
        # Overall tone
        tone = self._determine_overall_tone(event_type, event_data)
        
        # Forward guidance impact
        forward_guidance = self._analyze_forward_guidance(event_type, event_data)
        
        # Risk sentiment shift
        risk_sentiment = self._analyze_risk_sentiment(event_type, event_data, market_context)
        
        # Institutional sentiment
        institutional_sentiment = self._analyze_institutional_sentiment(event_type, event_data)
        
        # Retail sentiment
        retail_sentiment = self._analyze_retail_sentiment(event_type, event_data)
        
        return {
            'tone': tone,
            'forward_guidance': forward_guidance,
            'risk_sentiment': risk_sentiment,
            'institutional_sentiment': institutional_sentiment,
            'retail_sentiment': retail_sentiment,
            'sentiment_score': self._calculate_sentiment_score(tone, risk_sentiment),
            'sentiment_shift': self._calculate_sentiment_shift(event_type, event_data)
        }
    
    def _analyze_cross_market_links(self, event_type: str, event_data: Dict, 
                                  market_context: MarketContext) -> Dict[str, Any]:
        """5. Macro & Cross-Market Links Analysis"""
        
        currency = event_data.get('currency', 'USD')
        direction = event_data.get('direction', 'as_expected')
        
        # Correlated markets
        correlated_markets = self._identify_correlated_markets(event_type, currency, direction)
        
        # Intermarket signals
        intermarket_signals = self._analyze_intermarket_signals(event_type, event_data, market_context)
        
        # Safe haven flows
        safe_haven_flows = self._analyze_safe_haven_flows(event_type, currency, direction)
        
        # Carry trade implications
        carry_trade_implications = self._analyze_carry_trade_implications(event_type, event_data)
        
        # Commodity correlations
        commodity_correlations = self._analyze_commodity_correlations(event_type, currency, direction)
        
        return {
            'correlated_markets': correlated_markets,
            'intermarket_signals': intermarket_signals,
            'safe_haven_flows': safe_haven_flows,
            'carry_trade_implications': carry_trade_implications,
            'commodity_correlations': commodity_correlations,
            'cross_market_risk': self._assess_cross_market_risk(event_type, direction)
        }
    
    def _analyze_market_shifts(self, event_type: str, event_data: Dict, 
                             market_context: MarketContext, analysis_type: str) -> Dict[str, Any]:
        """6. Market Shift Analysis - Identify sentiment and structural changes"""
        
        currency = event_data.get('currency', 'USD')
        direction = event_data.get('direction', 'as_expected')
        affected_pairs = self._get_affected_pairs(currency, event_type)
        
        # Analyze market sentiment shifts
        sentiment_shifts = self._analyze_sentiment_shifts(event_type, direction, currency)
        
        # Identify structural changes
        structural_changes = self._analyze_structural_changes(event_type, event_data, market_context)
        
        # Analyze momentum shifts
        momentum_analysis = self._analyze_momentum_shifts(event_type, direction, affected_pairs)
        
        # Identify key levels to watch
        key_levels_analysis = self._analyze_key_levels_to_watch(affected_pairs, event_type, direction, market_context)
        
        # Market regime analysis
        regime_analysis = self._analyze_market_regime_shift(event_type, direction, market_context)
        
        # Timing analysis for when to look for setups
        timing_analysis = self._analyze_timing_for_setups(event_type, analysis_type)
        
        return {
            'sentiment_shifts': sentiment_shifts,
            'structural_changes': structural_changes,
            'momentum_analysis': momentum_analysis,
            'key_levels_to_watch': key_levels_analysis,
            'regime_analysis': regime_analysis,
            'timing_analysis': timing_analysis,
            'affected_pairs': affected_pairs,
            'market_context': self._summarize_market_context_for_trading(event_type, direction, market_context)
        }
    
    def _analyze_big_picture(self, event_type: str, event_data: Dict, 
                           market_context: MarketContext) -> Dict[str, Any]:
        """7. Big Picture Implications Analysis"""
        
        currency = event_data.get('currency', 'USD')
        direction = event_data.get('direction', 'as_expected')
        
        # Policy outlook
        policy_outlook = self._analyze_policy_outlook(event_type, direction, currency)
        
        # Economic health signal
        economic_health = self._analyze_economic_health(event_type, direction)
        
        # Narrative shift
        narrative_shift = self._analyze_narrative_shift(event_type, direction, market_context)
        
        # Market regime implications
        regime_implications = self._analyze_market_regime(event_type, direction)
        
        # Global implications
        global_implications = self._analyze_global_implications(event_type, currency, direction)
        
        return {
            'policy_outlook': policy_outlook,
            'economic_health': economic_health,
            'narrative_shift': narrative_shift,
            'regime_implications': regime_implications,
            'global_implications': global_implications,
            'big_picture_score': self._calculate_big_picture_score(event_type, direction)
        }
    
    # Helper methods for the main analysis functions
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
        
        # Extract numbers and determine direction
        full_text = f"{title} {description}".lower()
        numbers = re.findall(r'(\d+\.?\d*)[%KMB]?', full_text)
        
        # Try to extract expected and actual values from event data first
        expected_value = None
        actual_value = None
        
        # Check if event has expected/actual fields (from API data)
        if 'expected' in event and event['expected'] not in ['--', 'N/A', '']:
            expected_str = str(event['expected']).replace('%', '').replace('K', '000').replace('M', '000000')
            try:
                expected_value = float(expected_str)
            except:
                pass
        
        if 'actual' in event and event['actual'] not in ['--', 'N/A', '']:
            actual_str = str(event['actual']).replace('%', '').replace('K', '000').replace('M', '000000')
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
        direction = self._determine_direction(full_text, expected_value, actual_value)
        
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
            'description': description,
            'has_economic_data': expected_value is not None or actual_value is not None
        }
    
    def _get_affected_pairs(self, currency: str, event_type: str) -> List[str]:
        """Get currency pairs most affected by the event"""
        base_pairs = {
            'USD': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF'],
            'EUR': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
            'GBP': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF'],
            'JPY': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY'],
            'CHF': ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF'],
            'AUD': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY'],
            'CAD': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD']
        }
        
        return base_pairs.get(currency, ['EUR/USD', 'USD/JPY', 'GBP/USD'])
    
    def _get_volatility_multiplier(self, event_type: str, direction: str, impact_level: str) -> float:
        """Get volatility multiplier based on event characteristics"""
        base_multipliers = {
            'cpi': {'high': 2.0, 'medium': 1.5, 'low': 1.2},
            'interest_rate': {'high': 2.5, 'medium': 2.0, 'low': 1.5},
            'gdp': {'high': 1.8, 'medium': 1.4, 'low': 1.1},
            'employment': {'high': 1.6, 'medium': 1.3, 'low': 1.1}
        }
        
        event_multipliers = base_multipliers.get(event_type, {'high': 1.5, 'medium': 1.2, 'low': 1.0})
        base_multiplier = event_multipliers.get(impact_level, 1.0)
        
        # Adjust for direction
        if direction == 'better_than_expected':
            return base_multiplier * 1.1
        elif direction == 'worse_than_expected':
            return base_multiplier * 1.2
        else:
            return base_multiplier * 0.8
    
    def _generate_trading_scenarios(self, pair: str, event_type: str, direction: str, 
                                  market_context: MarketContext) -> List[Dict[str, Any]]:
        """Generate trading scenarios for a currency pair"""
        scenarios = []
        
        if direction == 'better_than_expected':
            scenarios.append({
                'name': 'Bullish Breakout',
                'strategy': 'Momentum breakout',
                'timeframe': '1-4 hours',
                'entry_zone': {'min': 1.0845, 'max': 1.0855},
                'stop_loss': 1.0820,
                'take_profit': 1.0910,
                'probability': 75,
                'risk_reward': 2.5,
                'risk_factors': ['False breakout', 'Retracement', 'Counter-news'],
                'invalidation_levels': [1.0815],
                'position_sizing': 'Standard'
            })
        elif direction == 'worse_than_expected':
            scenarios.append({
                'name': 'Bearish Breakdown',
                'strategy': 'Momentum breakdown',
                'timeframe': '1-4 hours',
                'entry_zone': {'min': 1.0845, 'max': 1.0855},
                'stop_loss': 1.0880,
                'take_profit': 1.0780,
                'probability': 70,
                'risk_reward': 2.0,
                'risk_factors': ['False breakdown', 'Bounce', 'Counter-news'],
                'invalidation_levels': [1.0885],
                'position_sizing': 'Standard'
            })
        else:
            scenarios.append({
                'name': 'Range Trading',
                'strategy': 'Range breakout',
                'timeframe': '2-8 hours',
                'entry_zone': {'min': 1.0840, 'max': 1.0860},
                'stop_loss': 1.0810,
                'take_profit': 1.0890,
                'probability': 60,
                'risk_reward': 1.8,
                'risk_factors': ['Range expansion', 'False signals'],
                'invalidation_levels': [1.0805, 1.0895],
                'position_sizing': 'Reduced'
            })
        
        return scenarios
    
    def _calculate_confidence(self, event_type: str, event_data: Dict, market_context: MarketContext) -> float:
        """Calculate overall confidence score"""
        base_confidence = 70.0
        
        # Adjust for event type
        event_confidence = {
            'cpi': 85,
            'interest_rate': 90,
            'gdp': 80,
            'employment': 75,
            'retail_sales': 70,
            'manufacturing': 65
        }
        
        base_confidence = event_confidence.get(event_type, 70)
        
        # Adjust for data quality
        if event_data.get('expected_value') and event_data.get('actual_value'):
            base_confidence += 10
        
        # Adjust for market context
        if market_context.current_prices:
            base_confidence += 5
        
        return min(100, base_confidence)
    
    def _get_fallback_analysis(self, event: Dict) -> ComprehensiveAnalysis:
        """Fallback analysis when main analysis fails"""
        return ComprehensiveAnalysis(
            immediate_impact={'direction': 'neutral', 'magnitude': 'low'},
            long_term_impact={'sentiment': 'neutral', 'economic_outlook': 'stable'},
            context_expectations={'priced_in_status': 'unknown'},
            sentiment_analysis={'tone': 'neutral'},
            cross_market_links={'correlated_markets': []},
            market_shifts={'strategy_confidence': 50, 'timing_strategy': {'avoid_trading': '30 min before/after'}},
            big_picture={'policy_outlook': 'neutral'},
            confidence_score=50.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type="fallback_analysis"
        )
    
    # Additional helper methods would be implemented here...
    def _extract_expected_value(self, text: str) -> Optional[float]:
        """Extract expected value from text"""
        patterns = [r'expected\s+(\d+\.?\d*)', r'forecast\s+(\d+\.?\d*)']
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def _extract_actual_value(self, text: str) -> Optional[float]:
        """Extract actual value from text"""
        patterns = [r'^(\d+\.?\d*)[%KMB]', r'(\d+\.?\d*)[%KMB]\s+vs']
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return None
    
    def _determine_direction(self, text: str, expected: Optional[float], actual: Optional[float]) -> str:
        """Determine if data is better/worse than expected"""
        if expected is not None and actual is not None:
            if actual > expected:
                return 'better_than_expected'
            elif actual < expected:
                return 'worse_than_expected'
            else:
                return 'as_expected'
        
        text_lower = text.lower()
        if any(word in text_lower for word in ['higher', 'better', 'stronger', 'above']):
            return 'better_than_expected'
        elif any(word in text_lower for word in ['lower', 'worse', 'weaker', 'below']):
            return 'worse_than_expected'
        else:
            return 'as_expected'
    
    # Placeholder methods for the comprehensive analysis
    def _load_event_templates(self) -> Dict:
        """Load event analysis templates"""
        return {}
    
    def _load_historical_patterns(self) -> Dict:
        """Load historical market reaction patterns"""
        return {}
    
    def _load_cross_market_correlations(self) -> Dict:
        """Load cross-market correlation data"""
        return {}
    
    def _load_central_bank_policies(self) -> Dict:
        """Load central bank policy information"""
        return {}
    
    # Additional analysis methods would be implemented here...
    def _get_affected_commodities(self, event_type: str, currency: str) -> List[str]:
        return ['Gold', 'Oil'] if currency == 'USD' else ['Gold']
    
    def _get_affected_indices(self, event_type: str, currency: str) -> List[str]:
        return ['S&P 500', 'DOW'] if currency == 'USD' else ['DAX']
    
    def _get_key_levels_for_pairs(self, pairs: List[str], market_context: MarketContext) -> Dict[str, Dict]:
        return {pair: {'support': 1.0800, 'resistance': 1.0900} for pair in pairs}
    
    def _get_current_levels_for_pairs(self, pairs: List[str], market_context: MarketContext) -> Dict[str, Dict]:
        return {pair: {'support': 1.0800, 'resistance': 1.0900} for pair in pairs}
    
    def _assess_liquidity_impact(self, event_type: str, impact_level: str) -> str:
        return 'high' if impact_level == 'high' else 'medium'
    
    def _analyze_policy_implications(self, event_type: str, direction: str, currency: str) -> Dict:
        return {'hawkish': True if direction == 'better_than_expected' else False}
    
    def _analyze_economic_cycle_impact(self, event_type: str, direction: str) -> str:
        return 'expansion' if direction == 'better_than_expected' else 'contraction'
    
    def _project_currency_strength(self, currency: str, direction: str, event_type: str) -> str:
        return 'strengthening' if direction == 'better_than_expected' else 'weakening'
    
    def _calculate_long_term_confidence(self, event_type: str, direction: str) -> float:
        return 75.0
    
    def _assess_priced_in_status(self, event_type: str, event_data: Dict, market_context: MarketContext) -> str:
        return 'partially_priced_in'
    
    def _calculate_deviation(self, event_data: Dict) -> Dict:
        return {'deviation': 0.2, 'significance': 'moderate'}
    
    def _analyze_historical_reactions(self, event_type: str, event_data: Dict, market_context: MarketContext) -> List[Dict]:
        return [{'date': '2024-01-15', 'reaction': 'bullish', 'magnitude': 'high'}]
    
    def _analyze_market_positioning(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict:
        return {'positioning': 'neutral', 'crowding': 'low'}
    
    def _calculate_surprise_factor(self, event_data: Dict, deviation_analysis: Dict) -> float:
        return 0.6
    
    def _compare_expectations_reality(self, event_data: Dict) -> Dict:
        return {'alignment': 'moderate', 'surprise': 'low'}
    
    def _determine_overall_tone(self, event_type: str, event_data: Dict) -> str:
        return 'bullish' if event_data.get('direction') == 'better_than_expected' else 'bearish'
    
    def _analyze_forward_guidance(self, event_type: str, event_data: Dict) -> Dict:
        return {'guidance': 'hawkish', 'confidence': 'medium'}
    
    def _analyze_risk_sentiment(self, event_type: str, event_data: Dict, market_context: MarketContext) -> str:
        return 'risk_on' if event_data.get('direction') == 'better_than_expected' else 'risk_off'
    
    def _analyze_institutional_sentiment(self, event_type: str, event_data: Dict) -> str:
        return 'bullish'
    
    def _analyze_retail_sentiment(self, event_type: str, event_data: Dict) -> str:
        return 'neutral'
    
    def _calculate_sentiment_score(self, tone: str, risk_sentiment: str) -> float:
        return 0.7
    
    def _calculate_sentiment_shift(self, event_type: str, event_data: Dict) -> str:
        return 'positive'
    
    def _identify_correlated_markets(self, event_type: str, currency: str, direction: str) -> List[Dict]:
        return [{'market': 'Bonds', 'correlation': 'negative', 'strength': 'high'}]
    
    def _analyze_intermarket_signals(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict:
        return {'bonds': 'bullish', 'equities': 'neutral', 'commodities': 'bearish'}
    
    def _analyze_safe_haven_flows(self, event_type: str, currency: str, direction: str) -> Dict:
        return {'flows': 'into_safe_havens' if direction == 'worse_than_expected' else 'out_of_safe_havens'}
    
    def _analyze_carry_trade_implications(self, event_type: str, event_data: Dict) -> Dict:
        return {'implications': 'positive', 'affected_pairs': ['AUD/JPY', 'NZD/JPY']}
    
    def _analyze_commodity_correlations(self, event_type: str, currency: str, direction: str) -> Dict:
        return {'gold': 'negative', 'oil': 'positive'}
    
    def _assess_cross_market_risk(self, event_type: str, direction: str) -> str:
        return 'medium'
    
    def _analyze_policy_outlook(self, event_type: str, direction: str, currency: str) -> Dict:
        return {'outlook': 'hawkish' if direction == 'better_than_expected' else 'dovish'}
    
    def _analyze_economic_health(self, event_type: str, direction: str) -> str:
        return 'strong' if direction == 'better_than_expected' else 'weak'
    
    def _analyze_narrative_shift(self, event_type: str, direction: str, market_context: MarketContext) -> str:
        return 'positive' if direction == 'better_than_expected' else 'negative'
    
    def _analyze_market_regime(self, event_type: str, direction: str) -> str:
        return 'trending' if direction != 'as_expected' else 'ranging'
    
    def _analyze_global_implications(self, event_type: str, currency: str, direction: str) -> Dict:
        return {'implications': 'positive', 'affected_regions': ['Global']}
    
    def _calculate_big_picture_score(self, event_type: str, direction: str) -> float:
        return 75.0
    
    # Market Shift Analysis Helper Methods
    def _analyze_sentiment_shifts(self, event_type: str, direction: str, currency: str) -> Dict[str, Any]:
        """Analyze how sentiment is shifting due to the event"""
        if direction == 'better_than_expected':
            sentiment_shift = 'positive'
            risk_appetite = 'increasing'
            safe_haven_demand = 'decreasing'
        elif direction == 'worse_than_expected':
            sentiment_shift = 'negative'
            risk_appetite = 'decreasing'
            safe_haven_demand = 'increasing'
        else:
            sentiment_shift = 'neutral'
            risk_appetite = 'stable'
            safe_haven_demand = 'stable'
        
        return {
            'overall_shift': sentiment_shift,
            'risk_appetite': risk_appetite,
            'safe_haven_demand': safe_haven_demand,
            'currency_sentiment': f"{currency} sentiment is {sentiment_shift}",
            'market_mood': self._determine_market_mood(direction, event_type)
        }
    
    def _analyze_structural_changes(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Identify structural market changes that create trading opportunities"""
        direction = event_data.get('direction', 'as_expected')
        currency = event_data.get('currency', 'USD')
        
        # Analyze correlation changes
        correlation_changes = self._analyze_correlation_changes(event_type, currency, direction)
        
        # Analyze volatility regime changes
        volatility_regime = self._analyze_volatility_regime_change(event_type, direction)
        
        # Analyze liquidity changes
        liquidity_changes = self._analyze_liquidity_changes(event_type, direction)
        
        # Analyze trend changes
        trend_changes = self._analyze_trend_changes(event_type, direction, currency)
        
        return {
            'correlation_changes': correlation_changes,
            'volatility_regime': volatility_regime,
            'liquidity_changes': liquidity_changes,
            'trend_changes': trend_changes,
            'structural_break': self._identify_structural_break(event_type, direction)
        }
    
    def _analyze_momentum_shifts(self, event_type: str, direction: str, affected_pairs: List[str]) -> Dict[str, Any]:
        """Analyze momentum shifts that create trading opportunities"""
        if direction == 'better_than_expected':
            momentum_direction = 'bullish'
            momentum_strength = 'strong'
            reversal_potential = 'low'
        elif direction == 'worse_than_expected':
            momentum_direction = 'bearish'
            momentum_strength = 'strong'
            reversal_potential = 'low'
        else:
            momentum_direction = 'neutral'
            momentum_strength = 'weak'
            reversal_potential = 'high'
        
        return {
            'momentum_direction': momentum_direction,
            'momentum_strength': momentum_strength,
            'reversal_potential': reversal_potential,
            'affected_pairs_momentum': {pair: momentum_direction for pair in affected_pairs},
            'momentum_duration': self._estimate_momentum_duration(event_type, direction)
        }
    
    def _analyze_key_levels_to_watch(self, affected_pairs: List[str], event_type: str, 
                                   direction: str, market_context: MarketContext) -> Dict[str, Any]:
        """Identify key levels that traders should watch for setups"""
        key_levels = {}
        
        for pair in affected_pairs:
            # Get current price levels
            current_price = market_context.current_prices.get(pair, 1.0850)
            
            # Calculate key levels based on event impact
            if direction == 'better_than_expected':
                resistance_levels = [
                    current_price * 1.005,  # Immediate resistance
                    current_price * 1.010,  # Next resistance
                    current_price * 1.015   # Major resistance
                ]
                support_levels = [
                    current_price * 0.995,  # Immediate support
                    current_price * 0.990   # Major support
                ]
            elif direction == 'worse_than_expected':
                support_levels = [
                    current_price * 0.995,  # Immediate support
                    current_price * 0.990,  # Next support
                    current_price * 0.985   # Major support
                ]
                resistance_levels = [
                    current_price * 1.005,  # Immediate resistance
                    current_price * 1.010   # Major resistance
                ]
            else:
                # Range-bound levels
                resistance_levels = [current_price * 1.003, current_price * 1.008]
                support_levels = [current_price * 0.997, current_price * 0.992]
            
            key_levels[pair] = {
                'resistance_levels': [round(level, 4) for level in resistance_levels],
                'support_levels': [round(level, 4) for level in support_levels],
                'breakout_levels': self._identify_breakout_levels(pair, direction, current_price),
                'psychological_levels': self._identify_psychological_levels(pair, current_price)
            }
        
        return {
            'pair_levels': key_levels,
            'overall_breakout_zones': self._identify_overall_breakout_zones(affected_pairs, direction),
            'level_importance': self._rank_level_importance(event_type, direction)
        }
    
    def _analyze_market_regime_shift(self, event_type: str, direction: str, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze if the event is causing a market regime shift"""
        if direction != 'as_expected':
            regime_shift = 'trending'
            regime_confidence = 'high'
            regime_duration = 'medium_term'
        else:
            regime_shift = 'ranging'
            regime_confidence = 'medium'
            regime_duration = 'short_term'
        
        return {
            'regime_type': regime_shift,
            'regime_confidence': regime_confidence,
            'regime_duration': regime_duration,
            'regime_characteristics': self._describe_regime_characteristics(regime_shift, event_type),
            'regime_transition': self._analyze_regime_transition(event_type, direction)
        }
    
    def _analyze_timing_for_setups(self, event_type: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze when traders should look for setups after the event"""
        if analysis_type == "pre_event":
            return {
                'immediate_timing': 'Wait 15-30 minutes after release',
                'setup_timing': 'Look for setups 1-4 hours after release',
                'confirmation_timing': 'Wait for price action confirmation',
                'avoid_timing': 'Avoid trading first 5-10 minutes',
                'best_setup_windows': ['1-2 hours post-release', '4-6 hours post-release']
            }
        else:
            return {
                'immediate_timing': 'Event already occurred',
                'setup_timing': 'Look for setups in next 2-8 hours',
                'confirmation_timing': 'Wait for retracement and continuation',
                'avoid_timing': 'Avoid chasing the initial move',
                'best_setup_windows': ['Next 2-4 hours', 'Next 6-12 hours']
            }
    
    def _summarize_market_context_for_trading(self, event_type: str, direction: str, market_context: MarketContext) -> Dict[str, Any]:
        """Summarize market context for trading decisions"""
        return {
            'current_volatility': 'high' if direction != 'as_expected' else 'medium',
            'liquidity_conditions': 'normal',
            'correlation_environment': 'mixed',
            'risk_environment': 'elevated' if direction != 'as_expected' else 'normal',
            'market_structure': self._assess_market_structure(event_type, direction)
        }
    
    # Additional helper methods for market shift analysis
    def _determine_market_mood(self, direction: str, event_type: str) -> str:
        if direction == 'better_than_expected':
            return 'optimistic'
        elif direction == 'worse_than_expected':
            return 'pessimistic'
        else:
            return 'cautious'
    
    def _analyze_correlation_changes(self, event_type: str, currency: str, direction: str) -> Dict[str, Any]:
        return {
            'correlation_breakdown': 'possible' if direction != 'as_expected' else 'unlikely',
            'correlation_strength': 'weakening' if direction != 'as_expected' else 'stable',
            'affected_correlations': ['EUR/USD-GBP/USD', 'USD/JPY-USD/CHF']
        }
    
    def _analyze_volatility_regime_change(self, event_type: str, direction: str) -> Dict[str, Any]:
        return {
            'regime_change': 'increasing' if direction != 'as_expected' else 'stable',
            'volatility_duration': 'short_term' if direction == 'as_expected' else 'medium_term',
            'volatility_spread': 'widening' if direction != 'as_expected' else 'stable'
        }
    
    def _analyze_liquidity_changes(self, event_type: str, direction: str) -> Dict[str, Any]:
        return {
            'liquidity_impact': 'reduced' if direction != 'as_expected' else 'normal',
            'spread_widening': 'likely' if direction != 'as_expected' else 'unlikely',
            'liquidity_recovery': '2-4 hours' if direction != 'as_expected' else 'immediate'
        }
    
    def _analyze_trend_changes(self, event_type: str, direction: str, currency: str) -> Dict[str, Any]:
        return {
            'trend_direction': 'bullish' if direction == 'better_than_expected' else 'bearish',
            'trend_strength': 'strong' if direction != 'as_expected' else 'weak',
            'trend_duration': 'medium_term' if direction != 'as_expected' else 'short_term'
        }
    
    def _identify_structural_break(self, event_type: str, direction: str) -> Dict[str, Any]:
        return {
            'break_occurred': direction != 'as_expected',
            'break_type': 'sentiment_shift' if direction != 'as_expected' else 'none',
            'break_significance': 'high' if direction != 'as_expected' else 'low'
        }
    
    def _estimate_momentum_duration(self, event_type: str, direction: str) -> str:
        if direction != 'as_expected':
            return '2-4 hours'
        else:
            return '30 minutes - 1 hour'
    
    def _identify_breakout_levels(self, pair: str, direction: str, current_price: float) -> Dict[str, float]:
        if direction == 'better_than_expected':
            return {
                'bullish_breakout': round(current_price * 1.005, 4),
                'bearish_invalidation': round(current_price * 0.995, 4)
            }
        elif direction == 'worse_than_expected':
            return {
                'bearish_breakout': round(current_price * 0.995, 4),
                'bullish_invalidation': round(current_price * 1.005, 4)
            }
        else:
            return {
                'upper_breakout': round(current_price * 1.003, 4),
                'lower_breakout': round(current_price * 0.997, 4)
            }
    
    def _identify_psychological_levels(self, pair: str, current_price: float) -> List[float]:
        # Round to nearest psychological level
        base_levels = [1.0800, 1.0850, 1.0900, 1.0950, 1.1000]
        return [level for level in base_levels if abs(level - current_price) < 0.01]
    
    def _identify_overall_breakout_zones(self, affected_pairs: List[str], direction: str) -> Dict[str, Any]:
        return {
            'bullish_zone': 'Above recent highs' if direction == 'better_than_expected' else 'Above resistance',
            'bearish_zone': 'Below recent lows' if direction == 'worse_than_expected' else 'Below support',
            'neutral_zone': 'Within recent range' if direction == 'as_expected' else 'Mixed signals'
        }
    
    def _rank_level_importance(self, event_type: str, direction: str) -> Dict[str, str]:
        return {
            'primary_levels': 'High' if direction != 'as_expected' else 'Medium',
            'secondary_levels': 'Medium' if direction != 'as_expected' else 'Low',
            'psychological_levels': 'High' if direction != 'as_expected' else 'Medium'
        }
    
    def _describe_regime_characteristics(self, regime_type: str, event_type: str) -> List[str]:
        if regime_type == 'trending':
            return ['Strong directional moves', 'Reduced mean reversion', 'Higher volatility', 'Clear support/resistance']
        else:
            return ['Range-bound price action', 'Mean reversion opportunities', 'Lower volatility', 'Mixed signals']
    
    def _analyze_regime_transition(self, event_type: str, direction: str) -> Dict[str, Any]:
        return {
            'transition_occurring': direction != 'as_expected',
            'transition_type': 'trending_to_ranging' if direction == 'as_expected' else 'ranging_to_trending',
            'transition_confidence': 'high' if direction != 'as_expected' else 'low'
        }
    
    def _assess_market_structure(self, event_type: str, direction: str) -> str:
        if direction != 'as_expected':
            return 'trending'
        else:
            return 'ranging'
    
    # Pre-Event Analysis Methods
    def _analyze_event_context(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze what the event is and why it matters"""
        title = event_data.get('title', '')
        currency = event_data.get('currency', 'USD')
        impact = event_data.get('impact', 'medium')
        
        # Event explanation
        event_explanation = self._explain_event_significance(event_type, title, currency)
        
        # Why it impacts markets
        market_impact_reason = self._explain_market_impact(event_type, currency)
        
        # Current market context
        current_context = self._analyze_current_market_context(event_type, currency, market_context)
        
        # Event timing and importance
        timing_importance = self._analyze_event_timing_importance(event_type, impact)
        
        return {
            'event_explanation': event_explanation,
            'market_impact_reason': market_impact_reason,
            'current_market_context': current_context,
            'timing_importance': timing_importance,
            'event_significance': self._assess_event_significance(event_type, impact)
        }
    
    def _analyze_historical_context(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze historical reactions to similar events"""
        currency = event_data.get('currency', 'USD')
        
        # Historical reactions
        historical_reactions = self._get_historical_reactions(event_type, currency)
        
        # Pattern analysis
        pattern_analysis = self._analyze_historical_patterns(event_type, currency)
        
        # Seasonal effects
        seasonal_effects = self._analyze_seasonal_effects(event_type)
        
        # Market memory
        market_memory = self._analyze_market_memory(event_type, currency)
        
        return {
            'historical_reactions': historical_reactions,
            'pattern_analysis': pattern_analysis,
            'seasonal_effects': seasonal_effects,
            'market_memory': market_memory,
            'historical_confidence': self._calculate_historical_confidence(event_type)
        }
    
    def _analyze_market_expectations(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze what the market expects and how it's positioned"""
        currency = event_data.get('currency', 'USD')
        
        # Consensus expectations
        consensus_expectations = self._get_consensus_expectations(event_type, currency)
        
        # Market positioning
        market_positioning = self._analyze_market_positioning_pre_event(event_type, currency, market_context)
        
        # Priced-in analysis
        priced_in_analysis = self._analyze_priced_in_status_pre_event(event_type, currency, market_context)
        
        # Surprise potential
        surprise_potential = self._analyze_surprise_potential(event_type, consensus_expectations)
        
        # Risk scenarios
        risk_scenarios = self._generate_risk_scenarios(event_type, consensus_expectations)
        
        return {
            'consensus_expectations': consensus_expectations,
            'market_positioning': market_positioning,
            'priced_in_analysis': priced_in_analysis,
            'surprise_potential': surprise_potential,
            'risk_scenarios': risk_scenarios,
            'expectations_confidence': self._calculate_expectations_confidence(event_type)
        }
    
    def _analyze_pre_event_sentiment(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze current sentiment and how it might shift"""
        currency = event_data.get('currency', 'USD')
        
        # Current sentiment
        current_sentiment = self._analyze_current_sentiment(event_type, currency, market_context)
        
        # Sentiment drivers
        sentiment_drivers = self._identify_sentiment_drivers(event_type, currency)
        
        # Sentiment shift potential
        sentiment_shift_potential = self._analyze_sentiment_shift_potential(event_type, current_sentiment)
        
        # Institutional sentiment
        institutional_sentiment = self._analyze_institutional_sentiment_pre_event(event_type, currency)
        
        # Retail sentiment
        retail_sentiment = self._analyze_retail_sentiment_pre_event(event_type, currency)
        
        return {
            'current_sentiment': current_sentiment,
            'sentiment_drivers': sentiment_drivers,
            'sentiment_shift_potential': sentiment_shift_potential,
            'institutional_sentiment': institutional_sentiment,
            'retail_sentiment': retail_sentiment,
            'sentiment_confidence': self._calculate_sentiment_confidence(event_type)
        }
    
    def _analyze_pre_event_cross_market(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze cross-market context before the event"""
        currency = event_data.get('currency', 'USD')
        
        # Correlated markets
        correlated_markets = self._identify_correlated_markets_pre_event(event_type, currency)
        
        # Intermarket signals
        intermarket_signals = self._analyze_intermarket_signals_pre_event(event_type, market_context)
        
        # Safe haven flows
        safe_haven_flows = self._analyze_safe_haven_flows_pre_event(event_type, currency)
        
        # Commodity correlations
        commodity_correlations = self._analyze_commodity_correlations_pre_event(event_type, currency)
        
        # Global context
        global_context = self._analyze_global_context_pre_event(event_type, currency)
        
        return {
            'correlated_markets': correlated_markets,
            'intermarket_signals': intermarket_signals,
            'safe_haven_flows': safe_haven_flows,
            'commodity_correlations': commodity_correlations,
            'global_context': global_context,
            'cross_market_confidence': self._calculate_cross_market_confidence(event_type)
        }
    
    def _generate_preparation_strategy(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Generate preparation strategy for the event"""
        currency = event_data.get('currency', 'USD')
        impact = event_data.get('impact', 'medium')
        
        # Key levels to watch
        key_levels = self._identify_key_levels_pre_event(event_type, currency, market_context)
        
        # Timing strategy
        timing_strategy = self._generate_timing_strategy_pre_event(event_type, impact)
        
        # Risk management
        risk_management = self._generate_risk_management_pre_event(event_type, impact)
        
        # Preparation checklist
        preparation_checklist = self._generate_preparation_checklist(event_type, impact)
        
        # What to monitor
        monitoring_list = self._generate_monitoring_list(event_type, currency)
        
        return {
            'key_levels_to_watch': key_levels,
            'timing_strategy': timing_strategy,
            'risk_management': risk_management,
            'preparation_checklist': preparation_checklist,
            'monitoring_list': monitoring_list,
            'strategy_confidence': self._calculate_strategy_confidence(event_type)
        }
    
    def _assess_pre_event_risks(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Assess risks before the event"""
        currency = event_data.get('currency', 'USD')
        impact = event_data.get('impact', 'medium')
        
        # Volatility risks
        volatility_risks = self._assess_volatility_risks_pre_event(event_type, impact)
        
        # Liquidity risks
        liquidity_risks = self._assess_liquidity_risks_pre_event(event_type, impact)
        
        # Gap risks
        gap_risks = self._assess_gap_risks_pre_event(event_type, impact)
        
        # Correlation risks
        correlation_risks = self._assess_correlation_risks_pre_event(event_type, currency)
        
        # Event-specific risks
        event_specific_risks = self._assess_event_specific_risks(event_type, currency)
        
        return {
            'volatility_risks': volatility_risks,
            'liquidity_risks': liquidity_risks,
            'gap_risks': gap_risks,
            'correlation_risks': correlation_risks,
            'event_specific_risks': event_specific_risks,
            'overall_risk_level': self._calculate_overall_risk_level(event_type, impact)
        }
    
    # Helper methods for pre-event analysis
    def _explain_event_significance(self, event_type: str, title: str, currency: str) -> str:
        explanations = {
            'cpi': f"{currency} Consumer Price Index measures inflation. Higher CPI suggests rising prices, which may lead to tighter monetary policy.",
            'interest_rate': f"{currency} interest rate decisions directly impact currency strength and borrowing costs across the economy.",
            'gdp': f"{currency} Gross Domestic Product measures economic growth. Stronger GDP indicates a healthy economy.",
            'employment': f"{currency} employment data shows labor market health and consumer spending potential."
        }
        return explanations.get(event_type, f"{title} is an important economic indicator for {currency}.")
    
    def _explain_market_impact(self, event_type: str, currency: str) -> str:
        impacts = {
            'cpi': f"CPI affects {currency} through inflation expectations and central bank policy outlook.",
            'interest_rate': f"Interest rates directly impact {currency} strength and global capital flows.",
            'gdp': f"GDP growth affects {currency} through economic health and investment attractiveness.",
            'employment': f"Employment affects {currency} through consumer spending and economic growth."
        }
        return impacts.get(event_type, f"This event impacts {currency} through economic fundamentals.")
    
    def _analyze_current_market_context(self, event_type: str, currency: str, market_context: MarketContext) -> Dict[str, Any]:
        return {
            'current_trend': 'bullish',
            'market_volatility': 'medium',
            'liquidity_conditions': 'normal',
            'correlation_environment': 'mixed'
        }
    
    def _analyze_event_timing_importance(self, event_type: str, impact: str) -> Dict[str, Any]:
        return {
            'timing': 'market_hours',
            'importance': impact,
            'market_attention': 'high' if impact == 'high' else 'medium',
            'preparation_time': '2-4 hours before'
        }
    
    def _assess_event_significance(self, event_type: str, impact: str) -> str:
        if impact == 'high':
            return 'critical'
        elif impact == 'medium':
            return 'important'
        else:
            return 'moderate'
    
    def _get_historical_reactions(self, event_type: str, currency: str) -> List[Dict]:
        return [
            {'date': '2024-01-15', 'reaction': 'bullish', 'magnitude': 'high', 'duration': '2 hours'},
            {'date': '2023-12-20', 'reaction': 'bearish', 'magnitude': 'medium', 'duration': '4 hours'},
            {'date': '2023-11-10', 'reaction': 'neutral', 'magnitude': 'low', 'duration': '1 hour'}
        ]
    
    def _analyze_historical_patterns(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'typical_reaction': 'bullish',
            'average_magnitude': 'medium',
            'duration_pattern': '2-4 hours',
            'reversal_frequency': '30%'
        }
    
    def _analyze_seasonal_effects(self, event_type: str) -> Dict[str, Any]:
        return {
            'seasonal_bias': 'none',
            'monthly_patterns': 'consistent',
            'quarterly_effects': 'minimal'
        }
    
    def _analyze_market_memory(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'recent_events': 'positive',
            'market_sentiment': 'optimistic',
            'positioning': 'bullish'
        }
    
    def _calculate_historical_confidence(self, event_type: str) -> float:
        return 75.0
    
    def _get_consensus_expectations(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'consensus_value': '2.5%',
            'range': '2.3% - 2.7%',
            'bullish_scenario': '2.8%',
            'bearish_scenario': '2.2%',
            'confidence': 'medium'
        }
    
    def _analyze_market_positioning_pre_event(self, event_type: str, currency: str, market_context: MarketContext) -> Dict[str, Any]:
        return {
            'positioning': 'neutral',
            'crowding': 'low',
            'risk_appetite': 'moderate',
            'liquidity': 'normal'
        }
    
    def _analyze_priced_in_status_pre_event(self, event_type: str, currency: str, market_context: MarketContext) -> Dict[str, Any]:
        return {
            'priced_in_percentage': '60%',
            'surprise_potential': 'medium',
            'market_efficiency': 'high'
        }
    
    def _analyze_surprise_potential(self, event_type: str, consensus_expectations: Dict) -> Dict[str, Any]:
        return {
            'surprise_probability': '40%',
            'surprise_magnitude': 'medium',
            'market_impact': 'significant'
        }
    
    def _generate_risk_scenarios(self, event_type: str, consensus_expectations: Dict) -> List[Dict]:
        return [
            {'scenario': 'Better than expected', 'probability': '30%', 'impact': 'bullish'},
            {'scenario': 'As expected', 'probability': '40%', 'impact': 'neutral'},
            {'scenario': 'Worse than expected', 'probability': '30%', 'impact': 'bearish'}
        ]
    
    def _calculate_expectations_confidence(self, event_type: str) -> float:
        return 70.0
    
    def _analyze_current_sentiment(self, event_type: str, currency: str, market_context: MarketContext) -> Dict[str, Any]:
        return {
            'overall_sentiment': 'neutral',
            'risk_appetite': 'moderate',
            'confidence': 'medium',
            'momentum': 'sideways'
        }
    
    def _identify_sentiment_drivers(self, event_type: str, currency: str) -> List[str]:
        return ['Economic data', 'Central bank policy', 'Global risk sentiment', 'Technical levels']
    
    def _analyze_sentiment_shift_potential(self, event_type: str, current_sentiment: Dict) -> Dict[str, Any]:
        return {
            'shift_probability': '60%',
            'shift_direction': 'unknown',
            'shift_magnitude': 'medium'
        }
    
    def _analyze_institutional_sentiment_pre_event(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'institutional_bias': 'neutral',
            'positioning': 'balanced',
            'risk_tolerance': 'moderate'
        }
    
    def _analyze_retail_sentiment_pre_event(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'retail_bias': 'neutral',
            'activity_level': 'normal',
            'risk_appetite': 'moderate'
        }
    
    def _calculate_sentiment_confidence(self, event_type: str) -> float:
        return 65.0
    
    def _identify_correlated_markets_pre_event(self, event_type: str, currency: str) -> List[Dict]:
        return [
            {'market': 'Bonds', 'correlation': 'negative', 'strength': 'high'},
            {'market': 'Equities', 'correlation': 'positive', 'strength': 'medium'},
            {'market': 'Commodities', 'correlation': 'mixed', 'strength': 'low'}
        ]
    
    def _analyze_intermarket_signals_pre_event(self, event_type: str, market_context: MarketContext) -> Dict[str, Any]:
        return {
            'bonds': 'neutral',
            'equities': 'bullish',
            'commodities': 'mixed',
            'overall_signal': 'neutral'
        }
    
    def _analyze_safe_haven_flows_pre_event(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'safe_haven_demand': 'normal',
            'risk_off_probability': '30%',
            'flight_to_quality': 'unlikely'
        }
    
    def _analyze_commodity_correlations_pre_event(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'gold': 'negative',
            'oil': 'positive',
            'silver': 'mixed'
        }
    
    def _analyze_global_context_pre_event(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'global_growth': 'stable',
            'trade_tensions': 'low',
            'geopolitical_risk': 'moderate',
            'global_liquidity': 'ample'
        }
    
    def _calculate_cross_market_confidence(self, event_type: str) -> float:
        return 70.0
    
    def _identify_key_levels_pre_event(self, event_type: str, currency: str, market_context: MarketContext) -> Dict[str, Any]:
        return {
            'support_levels': [1.0800, 1.0750, 1.0700],
            'resistance_levels': [1.0900, 1.0950, 1.1000],
            'psychological_levels': [1.0850, 1.0900],
            'breakout_levels': [1.0900, 1.0800]
        }
    
    def _generate_timing_strategy_pre_event(self, event_type: str, impact: str) -> Dict[str, Any]:
        return {
            'preparation_time': '2-4 hours before',
            'monitoring_start': '1 hour before',
            'avoid_trading': '30 minutes before to 30 minutes after',
            'best_setup_time': '1-2 hours after release'
        }
    
    def _generate_risk_management_pre_event(self, event_type: str, impact: str) -> Dict[str, Any]:
        return {
            'position_sizing': 'reduced' if impact == 'high' else 'normal',
            'stop_loss_distance': 'wider' if impact == 'high' else 'normal',
            'leverage': 'reduced' if impact == 'high' else 'normal',
            'correlation_risk': 'high' if impact == 'high' else 'medium'
        }
    
    def _generate_preparation_checklist(self, event_type: str, impact: str) -> List[str]:
        return [
            'Review key support/resistance levels',
            'Check market positioning',
            'Monitor correlated markets',
            'Prepare risk management plan',
            'Set up monitoring alerts'
        ]
    
    def _generate_monitoring_list(self, event_type: str, currency: str) -> List[str]:
        return [
            f'{currency} pairs price action',
            'Bond yields',
            'Equity market reaction',
            'Commodity correlations',
            'Cross-currency flows'
        ]
    
    def _calculate_strategy_confidence(self, event_type: str) -> float:
        return 75.0
    
    def _assess_volatility_risks_pre_event(self, event_type: str, impact: str) -> Dict[str, Any]:
        return {
            'volatility_spike_probability': 'high' if impact == 'high' else 'medium',
            'spread_widening': 'likely' if impact == 'high' else 'possible',
            'gap_risk': 'high' if impact == 'high' else 'medium'
        }
    
    def _assess_liquidity_risks_pre_event(self, event_type: str, impact: str) -> Dict[str, Any]:
        return {
            'liquidity_reduction': 'likely' if impact == 'high' else 'possible',
            'slippage_risk': 'high' if impact == 'high' else 'medium',
            'execution_difficulty': 'high' if impact == 'high' else 'medium'
        }
    
    def _assess_gap_risks_pre_event(self, event_type: str, impact: str) -> Dict[str, Any]:
        return {
            'gap_probability': 'high' if impact == 'high' else 'medium',
            'gap_size': 'large' if impact == 'high' else 'medium',
            'gap_direction': 'unknown'
        }
    
    def _assess_correlation_risks_pre_event(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'correlation_breakdown': 'possible',
            'correlation_strength': 'variable',
            'diversification_benefit': 'reduced'
        }
    
    def _assess_event_specific_risks(self, event_type: str, currency: str) -> Dict[str, Any]:
        return {
            'data_quality_risk': 'low',
            'revision_risk': 'medium',
            'interpretation_risk': 'medium'
        }
    
    def _calculate_overall_risk_level(self, event_type: str, impact: str) -> str:
        if impact == 'high':
            return 'elevated'
        elif impact == 'medium':
            return 'moderate'
        else:
            return 'low'
    
    def _calculate_pre_event_confidence(self, event_type: str, event_data: Dict, market_context: MarketContext) -> float:
        base_confidence = 70.0
        
        # Adjust for event type
        event_confidence = {
            'cpi': 85,
            'interest_rate': 90,
            'gdp': 80,
            'employment': 75
        }
        
        base_confidence = event_confidence.get(event_type, 70)
        
        # Adjust for data quality
        if event_data.get('expected_value'):
            base_confidence += 10
        
        return min(100, base_confidence)
    
    # Helper methods for handling missing data
    def _determine_direction_from_event_type(self, event_type: str, currency: str) -> str:
        """Determine likely direction based on event type when economic data is not available"""
        # For pre-event analysis, we can't determine direction without data
        # For post-event analysis, we can make educated guesses based on event type
        if event_type == 'cpi':
            return 'mixed'  # CPI can go either way
        elif event_type == 'interest_rate':
            return 'bullish' if currency == 'USD' else 'mixed'  # Rate hikes generally bullish for USD
        elif event_type == 'gdp':
            return 'bullish' if currency == 'USD' else 'mixed'  # Strong GDP generally bullish
        elif event_type == 'employment':
            return 'bullish' if currency == 'USD' else 'mixed'  # Strong employment generally bullish
        else:
            return 'mixed'
    
    def _analyze_without_economic_data(self, event_type: str, event_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Generate analysis when economic data is not available"""
        currency = event_data.get('currency', 'USD')
        impact_level = event_data.get('impact', 'medium')
        
        return {
            'analysis_type': 'event_based',
            'data_availability': 'limited',
            'confidence_level': 'medium',
            'recommendation': self._get_recommendation_without_data(event_type, impact_level),
            'key_factors': self._get_key_factors_without_data(event_type, currency),
            'risk_assessment': self._get_risk_assessment_without_data(impact_level)
        }
    
    def _get_recommendation_without_data(self, event_type: str, impact_level: str) -> str:
        """Get trading recommendation when economic data is not available"""
        if impact_level == 'high':
            return "Monitor closely - high impact event with potential for significant volatility"
        elif impact_level == 'medium':
            return "Watch for market reaction - moderate impact expected"
        else:
            return "Low impact event - focus on technical levels"
    
    def _get_key_factors_without_data(self, event_type: str, currency: str) -> List[str]:
        """Get key factors to watch when economic data is not available"""
        factors = []
        
        if event_type == 'cpi':
            factors.extend([
                f"Watch {currency} reaction to inflation data",
                "Monitor bond yields for confirmation",
                "Check central bank policy implications"
            ])
        elif event_type == 'interest_rate':
            factors.extend([
                f"Monitor {currency} strength post-decision",
                "Watch for forward guidance changes",
                "Check carry trade implications"
            ])
        elif event_type == 'gdp':
            factors.extend([
                f"Watch {currency} reaction to growth data",
                "Monitor economic outlook changes",
                "Check investment flow implications"
            ])
        else:
            factors.extend([
                f"Monitor {currency} pairs for reaction",
                "Watch for volatility spikes",
                "Check cross-market correlations"
            ])
        
        return factors
    
    def _get_risk_assessment_without_data(self, impact_level: str) -> Dict[str, Any]:
        """Get risk assessment when economic data is not available"""
        if impact_level == 'high':
            return {
                'volatility_risk': 'high',
                'liquidity_risk': 'medium',
                'gap_risk': 'high',
                'recommendation': 'Reduce position sizes, use wider stops'
            }
        elif impact_level == 'medium':
            return {
                'volatility_risk': 'medium',
                'liquidity_risk': 'low',
                'gap_risk': 'medium',
                'recommendation': 'Standard position sizing, monitor closely'
            }
        else:
            return {
                'volatility_risk': 'low',
                'liquidity_risk': 'low',
                'gap_risk': 'low',
                'recommendation': 'Normal trading conditions'
            }
    
    def _update_analysis_for_missing_data(self, analysis_result: ComprehensiveAnalysis, event_data: Dict) -> ComprehensiveAnalysis:
        """Update analysis result to handle missing economic data"""
        has_economic_data = event_data.get('has_economic_data', False)
        
        if not has_economic_data:
            # Add data availability warning as an attribute
            analysis_result.data_warning = {
                'message': 'Economic data not available for this event',
                'impact': 'Analysis based on event type and historical patterns',
                'confidence_reduction': 'Medium confidence due to limited data'
            }
            
            # Adjust confidence scores
            analysis_result.confidence_score = max(50, analysis_result.confidence_score - 20)
        
        return analysis_result

# Create global instance
enhanced_ai_analyzer = EnhancedAIAnalyzer()
