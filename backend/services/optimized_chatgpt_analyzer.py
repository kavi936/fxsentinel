#!/usr/bin/env python3
"""
Optimized ChatGPT Analyzer
Uses smart caching and model selection to minimize costs while maximizing quality
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
import os
from datetime import datetime

from .smart_chatgpt_cache import smart_cache
from .professional_analysis_template import professional_template

logger = logging.getLogger(__name__)

class OptimizedChatGPTAnalyzer:
    """Optimized ChatGPT analyzer with smart caching and cost management"""
    
    def __init__(self):
        self.client = None
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ Optimized ChatGPT Analyzer initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("⚠️ No OpenAI API key found")
        
        # Model selection configuration
        self.model_config = {
            'high_impact': {
                'model': 'gpt-4-turbo-preview',
                'cost_per_1k_tokens': 0.03,  # Input
                'cost_per_1k_output': 0.06,   # Output
                'max_tokens': 2000,
                'description': 'High-impact events (CPI, NFP, Rate decisions)'
            },
            'medium_impact': {
                'model': 'gpt-3.5-turbo',
                'cost_per_1k_tokens': 0.0015,
                'cost_per_1k_output': 0.002,
                'max_tokens': 1500,
                'description': 'Medium-impact events (Retail Sales, Manufacturing)'
            },
            'low_impact': {
                'model': 'gpt-3.5-turbo',
                'cost_per_1k_tokens': 0.0015,
                'cost_per_1k_output': 0.002,
                'max_tokens': 1000,
                'description': 'Low-impact events (Minor indicators)'
            }
        }
        
        # High-impact event keywords
        self.high_impact_keywords = [
            'cpi', 'inflation', 'consumer price index',
            'non-farm payrolls', 'nfp', 'employment',
            'interest rate', 'fed', 'ecb', 'boj', 'boe', 'rba', 'boc', 'snb',
            'gdp', 'gross domestic product',
            'fomc', 'monetary policy', 'rate decision'
        ]
        
        # Medium-impact event keywords
        self.medium_impact_keywords = [
            'retail sales', 'manufacturing', 'pmi', 'industrial production',
            'trade balance', 'current account', 'housing', 'building permits',
            'consumer confidence', 'business confidence', 'wages', 'earnings'
        ]
        
        # Cost tracking
        self.total_cost = 0.0
        self.total_requests = 0
        self.cache_hits = 0
    
    def analyze_event(self, event: Dict, analysis_type: str = "post_event") -> Dict:
        """Analyze economic event with smart caching and model selection"""
        
        # First, try to get from cache
        cached_analysis = smart_cache.get_cached_analysis(event, analysis_type)
        if cached_analysis:
            self.cache_hits += 1
            logger.info(f"✅ Cache hit for {event.get('title', 'Unknown')}")
            return cached_analysis
        
        # No cache hit - determine impact level and select model
        impact_level = self._determine_impact_level(event)
        model_config = self.model_config[impact_level]
        
        logger.info(f"🔍 Analyzing {event.get('title', 'Unknown')} with {model_config['model']} ({impact_level} impact)")
        
        # Create optimized prompt
        prompt = self._create_optimized_prompt(event, impact_level, analysis_type)
        
        # Call ChatGPT API
        try:
            response = self._call_chatgpt_api(prompt, model_config)
            
            # Parse and structure the response (includes professional template transformation)
            analysis = self._parse_and_structure_response(response, event, impact_level)
            
            # Cache the analysis for future use (after template transformation)
            smart_cache.cache_analysis(event, analysis, analysis_type)
            
            # Track costs
            self._track_costs(prompt, response, model_config)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ ChatGPT API call failed: {e}")
            return self._get_fallback_analysis(event, impact_level)
    
    def _determine_impact_level(self, event: Dict) -> str:
        """Determine the impact level of an event"""
        title_lower = event.get('title', '').lower()
        
        # Check for high-impact keywords
        if any(keyword in title_lower for keyword in self.high_impact_keywords):
            return 'high_impact'
        
        # Check for medium-impact keywords
        elif any(keyword in title_lower for keyword in self.medium_impact_keywords):
            return 'medium_impact'
        
        # Default to low impact
        else:
            return 'low_impact'
    
    def _create_optimized_prompt(self, event: Dict, impact_level: str, analysis_type: str) -> str:
        """Create optimized prompt based on impact level"""
        
        if impact_level == 'high_impact':
            return self._create_high_impact_prompt(event, analysis_type)
        elif impact_level == 'medium_impact':
            return self._create_medium_impact_prompt(event, analysis_type)
        else:
            return self._create_low_impact_prompt(event, analysis_type)
    
    def _create_high_impact_prompt(self, event: Dict, analysis_type: str) -> str:
        """Create comprehensive prompt for high-impact events"""
        return f"""
You are a senior macro analyst specializing in forex markets. Provide a comprehensive analysis for this high-impact economic event.

EVENT: {event.get('title', 'Unknown')}
CURRENCY: {event.get('currency', 'Unknown')}
ACTUAL: {event.get('actual', 'N/A')}
EXPECTED: {event.get('expected', 'N/A')}
PREVIOUS: {event.get('previous', 'N/A')}
ANALYSIS TYPE: {analysis_type}

Provide a detailed JSON response with the following structure:

{{
    "event_summary": {{
        "release": "Event name",
        "currency": "Currency code",
        "actual": "Actual value",
        "expected": "Expected value", 
        "previous": "Previous value",
        "surprise_magnitude": "minimal/small/medium/large",
        "immediate_bias": "bullish/bearish/neutral"
    }},
    "economic_significance": {{
        "what_it_measures": "What this indicator measures",
        "economic_implications": "What this data tells us about the economy",
        "policy_relevance": "Why central banks care about this data"
    }},
    "policy_implications": {{
        "central_bank_impact": "How this affects central bank policy",
        "rate_expectations": "Impact on interest rate expectations",
        "forward_guidance": "Implications for central bank communications"
    }},
    "market_reaction": {{
        "expected_movement": "Expected price movement description",
        "volatility_forecast": "Expected volatility level",
        "duration": "How long the impact will last",
        "key_pairs": ["Primary currency pairs affected"],
        "correlation_effects": "Cross-market correlations"
    }},
    "trading_strategy": {{
        "entry_zones": ["Specific entry levels"],
        "stop_loss": ["Stop loss levels"],
        "take_profit": ["Take profit targets"],
        "position_sizing": "Recommended position size",
        "time_horizon": "Trading time horizon"
    }},
    "risk_assessment": {{
        "volatility_risk": "1-10 scale",
        "policy_risk": "1-10 scale", 
        "liquidity_risk": "1-10 scale",
        "confidence_level": "0-100 percentage",
        "key_risks": ["Main risk factors"]
    }}
}}

Focus on actionable insights for professional forex traders. Be specific with levels and timeframes.
"""
    
    def _create_medium_impact_prompt(self, event: Dict, analysis_type: str) -> str:
        """Create balanced prompt for medium-impact events"""
        return f"""
You are a forex analyst. Analyze this medium-impact economic event:

EVENT: {event.get('title', 'Unknown')}
CURRENCY: {event.get('currency', 'Unknown')}
ACTUAL: {event.get('actual', 'N/A')}
EXPECTED: {event.get('expected', 'N/A')}
PREVIOUS: {event.get('previous', 'N/A')}

Provide JSON response:

{{
    "event_summary": {{
        "release": "Event name",
        "currency": "Currency code", 
        "actual": "Actual value",
        "expected": "Expected value",
        "previous": "Previous value",
        "surprise_magnitude": "minimal/small/medium/large",
        "immediate_bias": "bullish/bearish/neutral"
    }},
    "economic_context": "What this data means for the economy",
    "policy_impact": "How this affects central bank policy",
    "market_reaction": {{
        "expected_movement": "Expected price movement",
        "volatility": "low/medium/high",
        "key_pairs": ["Affected currency pairs"]
    }},
    "trading_approach": {{
        "entry_zones": ["Entry levels"],
        "stop_loss": ["Stop levels"],
        "take_profit": ["Target levels"]
    }},
    "risk_level": "low/medium/high"
}}

Provide practical trading insights.
"""
    
    def _create_low_impact_prompt(self, event: Dict, analysis_type: str) -> str:
        """Create concise prompt for low-impact events"""
        return f"""
Analyze this economic event for forex traders:

{event.get('title', 'Unknown')} - {event.get('currency', 'Unknown')}
Actual: {event.get('actual', 'N/A')}, Expected: {event.get('expected', 'N/A')}, Previous: {event.get('previous', 'N/A')}

Provide JSON:

{{
    "event_summary": {{
        "release": "Event name",
        "currency": "Currency code",
        "actual": "Actual value", 
        "expected": "Expected value",
        "previous": "Previous value",
        "bias": "bullish/bearish/neutral"
    }},
    "market_impact": "Expected market reaction",
    "key_pairs": ["Affected pairs"],
    "trading_levels": {{
        "entry": ["Entry zones"],
        "stop": ["Stop loss"],
        "target": ["Take profit"]
    }},
    "volatility": "low/medium/high"
}}

Keep it concise and actionable.
"""
    
    def _call_chatgpt_api(self, prompt: str, model_config: Dict) -> str:
        """Call ChatGPT API with the specified model"""
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        try:
            response = self.client.chat.completions.create(
                model=model_config['model'],
                messages=[
                    {"role": "system", "content": "You are a professional forex analyst. Provide accurate, actionable analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=model_config['max_tokens'],
                temperature=0.3,  # Lower temperature for more consistent analysis
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ ChatGPT API call failed: {e}")
            raise
    
    def _parse_and_structure_response(self, response: str, event: Dict, impact_level: str) -> Dict:
        """Parse and structure the ChatGPT response"""
        try:
            # Parse JSON response
            analysis = json.loads(response)
            
            # Apply professional template transformation
            professional_analysis = professional_template.transform_analysis(analysis, event)
            
            # Debug: Log the professional analysis
            logger.info(f"🔧 Professional analysis generated: {list(professional_analysis.keys())}")
            
            # Merge professional analysis with original analysis
            analysis.update(professional_analysis)
            
            # Debug: Log the final analysis keys
            logger.info(f"🔧 Final analysis keys: {list(analysis.keys())}")
            
            # Update metadata (preserve template metadata)
            if 'metadata' not in analysis:
                analysis['metadata'] = {}
            
            analysis['metadata'].update({
                'model_used': self.model_config[impact_level]['model'],
                'impact_level': impact_level,
                'analysis_timestamp': datetime.now().isoformat(),
                'cache_status': 'fresh',
                'template_applied': True
            })
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse ChatGPT response: {e}")
            logger.error(f"Response: {response}")
            return self._get_fallback_analysis(event, impact_level)
    
    def _get_fallback_analysis(self, event: Dict, impact_level: str) -> Dict:
        """Get fallback analysis when ChatGPT fails"""
        logger.warning(f"⚠️ Using fallback analysis for {event.get('title', 'Unknown')}")
        
        return {
            "event_summary": {
                "release": event.get('title', 'Unknown'),
                "currency": event.get('currency', 'Unknown'),
                "actual": event.get('actual', 'N/A'),
                "expected": event.get('expected', 'N/A'),
                "previous": event.get('previous', 'N/A'),
                "surprise_magnitude": "unknown",
                "immediate_bias": "neutral"
            },
            "economic_significance": {
                "what_it_measures": "Economic indicator analysis",
                "economic_implications": "Data provides insights into economic health",
                "policy_relevance": "May influence central bank policy decisions"
            },
            "market_reaction": {
                "expected_movement": "Market reaction depends on surprise factor",
                "volatility_forecast": "medium",
                "key_pairs": [f"{event.get('currency', 'USD')}/USD"]
            },
            "trading_strategy": {
                "entry_zones": ["Monitor current levels"],
                "stop_loss": ["Use appropriate risk management"],
                "take_profit": ["Set targets based on volatility"],
                "position_sizing": "Conservative sizing recommended",
                "time_horizon": "Short-term"
            },
            "risk_assessment": {
                "volatility_risk": 5,
                "policy_risk": 5,
                "liquidity_risk": 5,
                "confidence_level": 50,
                "key_risks": ["Market uncertainty"]
            },
            "metadata": {
                "model_used": "fallback",
                "impact_level": impact_level,
                "analysis_timestamp": datetime.now().isoformat(),
                "cache_status": "fallback"
            }
        }
    
    def _track_costs(self, prompt: str, response: str, model_config: Dict):
        """Track API costs"""
        input_tokens = len(prompt.split()) * 1.3  # Approximate token count
        output_tokens = len(response.split()) * 1.3
        
        input_cost = (input_tokens / 1000) * model_config['cost_per_1k_tokens']
        output_cost = (output_tokens / 1000) * model_config['cost_per_1k_output']
        
        total_cost = input_cost + output_cost
        
        self.total_cost += total_cost
        self.total_requests += 1
        
        logger.info(f"💰 API Cost: ${total_cost:.4f} ({model_config['model']})")
    
    def get_cost_statistics(self) -> Dict[str, Any]:
        """Get cost and performance statistics"""
        cache_stats = smart_cache.get_cache_statistics()
        
        return {
            'total_requests': self.total_requests,
            'cache_hits': self.cache_hits,
            'api_calls': self.total_requests - self.cache_hits,
            'total_cost': round(self.total_cost, 4),
            'average_cost_per_request': round(self.total_cost / self.total_requests if self.total_requests > 0 else 0, 4),
            'cache_hit_rate': round((self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0, 2),
            'cache_statistics': cache_stats,
            'cost_savings': round(cache_stats['cost_saved'], 2)
        }
    
    def pre_cache_popular_events(self, events: List[Dict]):
        """Pre-cache popular events to improve hit rates"""
        logger.info(f"🔄 Pre-caching {len(events)} popular events")
        
        for event in events:
            try:
                # Analyze and cache each event
                analysis = self.analyze_event(event, "post_event")
                logger.info(f"✅ Pre-cached: {event.get('title', 'Unknown')}")
            except Exception as e:
                logger.error(f"❌ Failed to pre-cache {event.get('title', 'Unknown')}: {e}")

# Global instance
optimized_chatgpt_analyzer = OptimizedChatGPTAnalyzer()
