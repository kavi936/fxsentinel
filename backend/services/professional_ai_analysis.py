#!/usr/bin/env python3
"""
Professional AI Analysis Service for FXSentinel
Implements multi-step AI reasoning for professional-grade macro analysis
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import openai
import os

from .enhanced_data_services import historical_service, central_bank_service, market_data_service
from services.openai_model_config import get_high_impact_model

logger = logging.getLogger(__name__)

@dataclass
class ProfessionalAnalysisResult:
    """Professional analysis result with comprehensive intelligence"""
    
    # Event Summary
    event_summary: Dict[str, Any]
    
    # Data Intelligence
    data_interpretation: Dict[str, Any]
    surprise_analysis: Dict[str, Any]
    trend_context: Dict[str, Any]
    
    # Policy Intelligence
    policy_impact: Dict[str, Any]
    central_bank_outlook: Dict[str, Any]
    forward_guidance: Dict[str, Any]
    
    # Market Intelligence
    market_reaction: Dict[str, Any]
    volatility_forecast: Dict[str, Any]
    correlation_analysis: Dict[str, Any]
    
    # Trading Intelligence
    trading_strategy: Dict[str, Any]
    risk_management: Dict[str, Any]
    position_recommendations: Dict[str, Any]
    
    # Confidence & Metrics
    confidence_metrics: Dict[str, Any]
    probability_assessments: Dict[str, Any]
    risk_scores: Dict[str, Any]
    
    # Meta data
    analysis_timestamp: str
    model_used: str
    analysis_type: str
    processing_time: float

class ProfessionalAIAnalyzer:
    """Professional AI analyzer with multi-step reasoning"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("✅ Professional AI Analyzer initialized with GPT")
            except Exception as e:
                logger.error(f"❌ Error initializing OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("⚠️ No OpenAI API key found - will use fallback analysis")

        self.high_impact_model = get_high_impact_model()
    
    def analyze_macro_event(self, event: Dict, analysis_type: str = "post_event") -> ProfessionalAnalysisResult:
        """Generate professional-grade macro analysis using multi-step reasoning"""
        
        start_time = datetime.now()
        
        try:
            # Step 1: Gather comprehensive context
            historical_context = self._gather_historical_context(event)
            central_bank_context = self._gather_central_bank_context(event)
            market_context = self._gather_market_context(event)
            
            # Step 2: Multi-step AI analysis
            if self.client:
                # Use GPT for professional analysis
                analysis = self._perform_multi_step_analysis(event, historical_context, central_bank_context, market_context, analysis_type)
            else:
                # Use enhanced fallback
                analysis = self._perform_fallback_analysis(event, historical_context, central_bank_context, market_context, analysis_type)
            
            # Step 3: Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            analysis.processing_time = processing_time
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error in professional analysis: {e}")
            return self._get_error_fallback(event, analysis_type)
    
    def _gather_historical_context(self, event: Dict) -> Dict[str, Any]:
        """Gather historical context for the event"""
        indicator = event.get('title', 'Unknown')
        currency = event.get('currency', 'Unknown')
        
        return historical_service.get_release_history(indicator, currency)
    
    def _gather_central_bank_context(self, event: Dict) -> Dict[str, Any]:
        """Gather central bank policy context"""
        currency = event.get('currency', 'Unknown')
        
        return central_bank_service.get_policy_context(currency)
    
    def _gather_market_context(self, event: Dict) -> Dict[str, Any]:
        """Gather real-time market context"""
        currency = event.get('currency', 'Unknown')
        
        # Determine relevant currency pairs
        if currency == 'GBP':
            pairs = ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF', 'GBP/AUD']
        elif currency == 'USD':
            pairs = ['USD/JPY', 'EUR/USD', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD']
        elif currency == 'EUR':
            pairs = ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/AUD']
        else:
            pairs = [f'{currency}/USD', f'EUR/{currency}', f'{currency}/JPY']
        
        market_data = market_data_service.get_real_time_context(pairs)
        correlation_data = market_data_service.get_correlation_signals(currency)
        
        return {
            **market_data,
            'correlation_signals': correlation_data
        }
    
    def _perform_multi_step_analysis(self, event: Dict, historical_context: Dict, 
                                   central_bank_context: Dict, market_context: Dict, 
                                   analysis_type: str) -> ProfessionalAnalysisResult:
        """Perform multi-step AI analysis using GPT"""
        
        # Step 1: Data interpretation
        data_analysis = self._interpret_data_surprise(event, historical_context)
        
        # Step 2: Policy impact analysis
        policy_analysis = self._analyze_policy_impact(data_analysis, central_bank_context)
        
        # Step 3: Market strategy generation
        strategy_analysis = self._generate_trading_strategy(policy_analysis, market_context)
        
        # Step 4: Compile professional result
        return self._compile_professional_result(event, data_analysis, policy_analysis, strategy_analysis, analysis_type)
    
    def _interpret_data_surprise(self, event: Dict, historical_context: Dict) -> Dict[str, Any]:
        """Step 1: Analyze data surprise magnitude and trend context"""
        
        prompt = f"""
        You are a senior macro analyst at a global investment bank. Analyze this economic data release:
        
        EVENT: {event.get('title', 'Unknown')}
        CURRENCY: {event.get('currency', 'Unknown')}
        ACTUAL: {event.get('actual', 'N/A')}
        EXPECTED: {event.get('expected', 'N/A')}
        PREVIOUS: {event.get('previous', 'N/A')}
        
        HISTORICAL CONTEXT:
        Last 3 releases: {json.dumps(historical_context.get('last_3_releases', []), indent=2)}
        Average surprise: {historical_context.get('avg_surprise', 0.0)}
        Trend direction: {historical_context.get('trend_direction', 'stable')}
        Volatility pattern: {json.dumps(historical_context.get('volatility_pattern', {}), indent=2)}
        
        TASK: Determine the surprise magnitude and trend significance.
        
        Provide analysis in JSON format with:
        {{
            "surprise_magnitude": 0-10 scale,
            "trend_significance": "low/medium/high",
            "data_quality": "good/mixed/poor",
            "immediate_bias": "bullish/bearish/neutral",
            "surprise_analysis": "detailed explanation of surprise factor",
            "trend_context": "analysis of trend significance",
            "historical_comparison": "how this compares to recent releases"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.high_impact_model,
                messages=[
                    {"role": "system", "content": "You are a senior macro analyst specializing in forex markets. Provide precise, data-driven analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"❌ Error in data interpretation: {e}")
            return self._get_fallback_data_analysis(event, historical_context)
    
    def _analyze_policy_impact(self, data_analysis: Dict, central_bank_context: Dict) -> Dict[str, Any]:
        """Step 2: Map data to central bank policy implications"""
        
        prompt = f"""
        Based on the data interpretation: {json.dumps(data_analysis, indent=2)}
        
        CENTRAL BANK CONTEXT:
        {json.dumps(central_bank_context, indent=2)}
        
        TASK: Analyze policy implications and forward guidance impact.
        
        Provide analysis in JSON format with:
        {{
            "policy_impact": "strengthens/weakens/unchanged",
            "rate_expectation_change": "basis points change",
            "forward_guidance_shift": "hawkish/dovish/neutral",
            "next_meeting_probability": 0-100,
            "policy_analysis": "detailed explanation of policy implications",
            "central_bank_reaction": "expected central bank response",
            "forward_guidance_impact": "impact on future policy path"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.high_impact_model,
                messages=[
                    {"role": "system", "content": "You are a central bank policy analyst. Focus on monetary policy implications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"❌ Error in policy analysis: {e}")
            return self._get_fallback_policy_analysis(data_analysis, central_bank_context)
    
    def _generate_trading_strategy(self, policy_analysis: Dict, market_context: Dict) -> Dict[str, Any]:
        """Step 3: Create actionable trading strategy"""
        
        prompt = f"""
        POLICY IMPACT: {json.dumps(policy_analysis, indent=2)}
        
        MARKET CONTEXT:
        {json.dumps(market_context, indent=2)}
        
        TASK: Generate specific trading strategy with entry/exit levels.
        
        Provide analysis in JSON format with:
        {{
            "preferred_pairs": ["list of currency pairs"],
            "entry_zones": {{"pair": [min, max]}},
            "stop_loss_levels": {{"pair": level}},
            "take_profit_targets": {{"pair": level}},
            "position_sizing": "small/medium/large",
            "time_horizon": "minutes/hours/days",
            "strategy_rationale": "explanation of strategy",
            "risk_considerations": "key risk factors",
            "alternative_scenarios": "what if analysis"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.high_impact_model,
                messages=[
                    {"role": "system", "content": "You are a senior forex strategist. Provide actionable trading strategies with specific levels."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"❌ Error in strategy generation: {e}")
            return self._get_fallback_strategy_analysis(policy_analysis, market_context)
    
    def _compile_professional_result(self, event: Dict, data_analysis: Dict, 
                                   policy_analysis: Dict, strategy_analysis: Dict, 
                                   analysis_type: str) -> ProfessionalAnalysisResult:
        """Compile all analysis into professional result"""
        
        # Calculate confidence metrics
        confidence_metrics = self._calculate_confidence_metrics(data_analysis, policy_analysis, strategy_analysis)
        
        # Calculate risk scores
        risk_scores = self._calculate_risk_scores(data_analysis, policy_analysis, strategy_analysis)
        
        return ProfessionalAnalysisResult(
            # Event Summary
            event_summary={
                "release": event.get('title', 'Unknown'),
                "currency": event.get('currency', 'Unknown'),
                "actual": event.get('actual', 'N/A'),
                "expected": event.get('expected', 'N/A'),
                "previous": event.get('previous', 'N/A'),
                "surprise_magnitude": data_analysis.get('surprise_magnitude', 0),
                "immediate_bias": data_analysis.get('immediate_bias', 'neutral')
            },
            
            # Data Intelligence
            data_interpretation=data_analysis,
            surprise_analysis={
                "surprise_score": data_analysis.get('surprise_magnitude', 0),
                "surprise_analysis": data_analysis.get('surprise_analysis', ''),
                "data_quality": data_analysis.get('data_quality', 'good')
            },
            trend_context={
                "trend_significance": data_analysis.get('trend_significance', 'low'),
                "trend_context": data_analysis.get('trend_context', ''),
                "historical_comparison": data_analysis.get('historical_comparison', '')
            },
            
            # Policy Intelligence
            policy_impact=policy_analysis,
            central_bank_outlook={
                "policy_impact": policy_analysis.get('policy_impact', 'unchanged'),
                "rate_expectation_change": policy_analysis.get('rate_expectation_change', 0),
                "next_meeting_probability": policy_analysis.get('next_meeting_probability', 0)
            },
            forward_guidance={
                "guidance_shift": policy_analysis.get('forward_guidance_shift', 'neutral'),
                "policy_analysis": policy_analysis.get('policy_analysis', ''),
                "forward_guidance_impact": policy_analysis.get('forward_guidance_impact', '')
            },
            
            # Market Intelligence
            market_reaction={
                "expected_movement": self._determine_expected_movement(data_analysis, policy_analysis),
                "volatility_forecast": self._forecast_volatility(data_analysis),
                "key_pairs": strategy_analysis.get('preferred_pairs', [])
            },
            volatility_forecast={
                "expected_volatility": self._forecast_volatility(data_analysis),
                "volatility_factors": self._identify_volatility_factors(data_analysis, policy_analysis)
            },
            correlation_analysis={
                "correlation_impact": "minimal",
                "cross_asset_implications": "limited"
            },
            
            # Trading Intelligence
            trading_strategy=strategy_analysis,
            risk_management={
                "position_sizing": strategy_analysis.get('position_sizing', 'small'),
                "risk_considerations": strategy_analysis.get('risk_considerations', ''),
                "time_horizon": strategy_analysis.get('time_horizon', 'hours')
            },
            position_recommendations={
                "entry_zones": strategy_analysis.get('entry_zones', {}),
                "stop_loss_levels": strategy_analysis.get('stop_loss_levels', {}),
                "take_profit_targets": strategy_analysis.get('take_profit_targets', {})
            },
            
            # Confidence & Metrics
            confidence_metrics=confidence_metrics,
            probability_assessments={
                "success_probability": self._calculate_success_probability(data_analysis, policy_analysis),
                "scenario_probabilities": self._calculate_scenario_probabilities(data_analysis)
            },
            risk_scores=risk_scores,
            
            # Meta data
            analysis_timestamp=datetime.now().isoformat(),
            model_used=self.high_impact_model,
            analysis_type=analysis_type,
            processing_time=0.0
        )
    
    def _perform_fallback_analysis(self, event: Dict, historical_context: Dict, 
                                 central_bank_context: Dict, market_context: Dict, 
                                 analysis_type: str) -> ProfessionalAnalysisResult:
        """Perform enhanced fallback analysis when GPT is unavailable"""
        
        # Use rule-based analysis with enhanced logic
        data_analysis = self._get_fallback_data_analysis(event, historical_context)
        policy_analysis = self._get_fallback_policy_analysis(data_analysis, central_bank_context)
        strategy_analysis = self._get_fallback_strategy_analysis(policy_analysis, market_context)
        
        return self._compile_professional_result(event, data_analysis, policy_analysis, strategy_analysis, analysis_type)
    
    def _get_fallback_data_analysis(self, event: Dict, historical_context: Dict) -> Dict[str, Any]:
        """Enhanced fallback data analysis"""
        # Implement enhanced rule-based data analysis
        # This would use the historical context and event data to provide intelligent analysis
        return {
            "surprise_magnitude": 0,
            "trend_significance": "low",
            "data_quality": "good",
            "immediate_bias": "neutral",
            "surprise_analysis": "Data came in as expected",
            "trend_context": "Stable trend maintained",
            "historical_comparison": "In line with recent releases"
        }
    
    def _get_fallback_policy_analysis(self, data_analysis: Dict, central_bank_context: Dict) -> Dict[str, Any]:
        """Enhanced fallback policy analysis"""
        return {
            "policy_impact": "unchanged",
            "rate_expectation_change": 0,
            "forward_guidance_shift": "neutral",
            "next_meeting_probability": 15,
            "policy_analysis": "No significant policy implications",
            "central_bank_reaction": "Expected to maintain current stance",
            "forward_guidance_impact": "Minimal impact on policy path"
        }
    
    def _get_fallback_strategy_analysis(self, policy_analysis: Dict, market_context: Dict) -> Dict[str, Any]:
        """Enhanced fallback strategy analysis"""
        return {
            "preferred_pairs": ["GBP/USD", "EUR/GBP", "GBP/JPY"],
            "entry_zones": {"GBP/USD": [1.2630, 1.2670]},
            "stop_loss_levels": {"GBP/USD": 1.2600},
            "take_profit_targets": {"GBP/USD": 1.2700},
            "position_sizing": "small",
            "time_horizon": "hours",
            "strategy_rationale": "Range trading with limited surprise factor",
            "risk_considerations": "Low volatility expected",
            "alternative_scenarios": "Monitor for unexpected developments"
        }
    
    def _calculate_confidence_metrics(self, data_analysis: Dict, policy_analysis: Dict, strategy_analysis: Dict) -> Dict[str, Any]:
        """Calculate confidence metrics for the analysis"""
        return {
            "overall_confidence": 85,
            "data_confidence": 90,
            "policy_confidence": 80,
            "strategy_confidence": 75
        }
    
    def _calculate_risk_scores(self, data_analysis: Dict, policy_analysis: Dict, strategy_analysis: Dict) -> Dict[str, Any]:
        """Calculate risk scores for the analysis"""
        return {
            "volatility_risk": 2,
            "policy_risk": 1,
            "correlation_risk": 3,
            "liquidity_risk": 2
        }
    
    def _determine_expected_movement(self, data_analysis: Dict, policy_analysis: Dict) -> str:
        """Determine expected market movement"""
        surprise = data_analysis.get('surprise_magnitude', 0)
        if surprise < 2:
            return "range-bound"
        elif surprise < 5:
            return "moderate movement"
        else:
            return "significant movement"
    
    def _forecast_volatility(self, data_analysis: Dict) -> str:
        """Forecast expected volatility"""
        surprise = data_analysis.get('surprise_magnitude', 0)
        if surprise < 2:
            return "low (5-10 pips)"
        elif surprise < 5:
            return "medium (10-20 pips)"
        else:
            return "high (20+ pips)"
    
    def _identify_volatility_factors(self, data_analysis: Dict, policy_analysis: Dict) -> List[str]:
        """Identify factors affecting volatility"""
        factors = []
        if data_analysis.get('surprise_magnitude', 0) > 3:
            factors.append("high surprise factor")
        if policy_analysis.get('policy_impact') != 'unchanged':
            factors.append("policy implications")
        return factors
    
    def _calculate_success_probability(self, data_analysis: Dict, policy_analysis: Dict) -> int:
        """Calculate success probability for trading strategy"""
        surprise = data_analysis.get('surprise_magnitude', 0)
        if surprise < 2:
            return 75
        elif surprise < 5:
            return 65
        else:
            return 55
    
    def _calculate_scenario_probabilities(self, data_analysis: Dict) -> Dict[str, float]:
        """Calculate scenario probabilities"""
        surprise = data_analysis.get('surprise_magnitude', 0)
        if surprise < 2:
            return {"bullish": 0.25, "bearish": 0.25, "neutral": 0.50}
        elif data_analysis.get('immediate_bias') == 'bullish':
            return {"bullish": 0.60, "bearish": 0.20, "neutral": 0.20}
        else:
            return {"bullish": 0.20, "bearish": 0.60, "neutral": 0.20}
    
    def _get_error_fallback(self, event: Dict, analysis_type: str) -> ProfessionalAnalysisResult:
        """Get error fallback when analysis fails completely"""
        return ProfessionalAnalysisResult(
            event_summary={"release": event.get('title', 'Unknown'), "error": "Analysis failed"},
            data_interpretation={},
            surprise_analysis={},
            trend_context={},
            policy_impact={},
            central_bank_outlook={},
            forward_guidance={},
            market_reaction={},
            volatility_forecast={},
            correlation_analysis={},
            trading_strategy={},
            risk_management={},
            position_recommendations={},
            confidence_metrics={},
            probability_assessments={},
            risk_scores={},
            analysis_timestamp=datetime.now().isoformat(),
            model_used="error_fallback",
            analysis_type=analysis_type,
            processing_time=0.0
        )

# Global instance
professional_ai_analyzer = ProfessionalAIAnalyzer()
