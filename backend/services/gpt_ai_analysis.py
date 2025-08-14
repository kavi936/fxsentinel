#!/usr/bin/env python3
"""
GPT AI Analysis Service for FXSentinel
Implements comprehensive 8-point analysis framework with real GPT integration
"""

import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import openai
import os
from dataclasses import dataclass
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
import pickle

logger = logging.getLogger(__name__)

@dataclass
class MarketContext:
    """Market context for GPT analysis"""
    current_prices: Dict[str, float]
    recent_volatility: Dict[str, float]
    market_sentiment: Dict[str, str]
    key_levels: Dict[str, Dict[str, float]]
    economic_calendar: List[Dict]
    bond_yields: Dict[str, float]
    equity_indices: Dict[str, float]
    commodity_prices: Dict[str, float]

@dataclass
class GPTAnalysisResult:
    """Complete GPT analysis result"""
    # 1. General Overview
    general_overview: Dict[str, Any]
    
    # 2. Immediate Market Impact
    immediate_impact: Dict[str, Any]
    
    # 3. Long-term Market Impact
    long_term_impact: Dict[str, Any]
    
    # 4. Context vs Expectations
    context_expectations: Dict[str, Any]
    
    # 5. Sentiment Analysis
    sentiment_analysis: Dict[str, Any]
    
    # 6. Macro & Cross-Market Links
    cross_market_links: Dict[str, Any]
    
    # 7. Trading Strategy Framework
    trading_framework: Dict[str, Any]
    
    # 8. Big Picture Implications
    big_picture: Dict[str, Any]
    
    # Meta data
    confidence_score: float
    analysis_timestamp: str
    event_id: str
    analysis_type: str
    model_used: str
    cost_estimate: float
    cache_hit: bool = False

class GPTAIAnalyzer:
    def __init__(self):
        # Configure OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("🔍 WARNING: OPENAI_API_KEY not found in environment variables!")
            print("🔍 This will cause GPT analysis to fail and use fallback content.")
        else:
            print(f"🔍 OpenAI API Key found: {api_key[:10]}...{api_key[-4:]}")
        
        self.client = openai.OpenAI(api_key=api_key)
        print(f"🔍 GPT Analyzer initialized with API key: {'VALID' if api_key else 'MISSING'}")
        
        # Initialize Redis for caching (optional - falls back to in-memory)
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Redis cache connected")
            except:
                logger.warning("⚠️ Redis not available, using in-memory cache")
                self.redis_client = None
        else:
            logger.info("ℹ️ Redis not installed, using in-memory cache")
        
        # In-memory cache fallback
        self.memory_cache = {}
        self.cache_timestamps = {}
        
        # Rate limiting
        self.api_calls_this_hour = 0
        self.last_hour_reset = datetime.now()
        self.max_calls_per_hour = 50
        
        # Cost tracking
        self.total_cost = 0.0
        self.cost_estimates = {
            'gpt-4-turbo': 0.03,  # per 1K tokens
            'gpt-3.5-turbo': 0.002  # per 1K tokens
        }
        
        # Event impact mapping for model selection
        self.high_impact_events = [
            'cpi', 'inflation', 'non-farm payrolls', 'nfp', 'employment',
            'interest rate', 'fomc', 'ecb', 'boj', 'boe', 'gdp',
            'retail sales', 'manufacturing', 'unemployment'
        ]
    
    def analyze_macro_event(self, event: Dict, market_context: MarketContext, 
                          analysis_type: str = "pre_event") -> GPTAnalysisResult:
        """
        Generate comprehensive GPT analysis for macro events
        
        Args:
            event: Economic event data
            market_context: Current market conditions
            analysis_type: "pre_event" or "post_event"
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(event, analysis_type)
            cached_result = self._get_cached_analysis(cache_key)
            
            if cached_result:
                logger.info(f"✅ Cache hit for event {event.get('id', 'unknown')}")
                cached_result.cache_hit = True
                return cached_result
            
            # Rate limiting check
            if not self._check_rate_limit():
                logger.warning("⚠️ Rate limit reached, using fallback analysis")
                print(f"🚨🚨🚨 RATE LIMIT TRIGGERED - EASY TO FIND 🚨🚨🚨")
                print(f"🚨 Calls this hour: {self.api_calls_this_hour}/{self.max_calls_per_hour}")
                print(f"🚨 Event: {event.get('title', 'Unknown')}")
                print(f"🚨🚨🚨 END RATE LIMIT MESSAGE 🚨🚨🚨")
                return self._get_fallback_analysis(event, analysis_type)
            
            # Determine which GPT model to use
            model = self._select_model(event)
            
            # Generate analysis
            analysis_result = self._generate_gpt_analysis(event, market_context, analysis_type, model)
            
            # Cache the result
            self._cache_analysis(cache_key, analysis_result)
            
            # Update rate limiting
            self.api_calls_this_hour += 1
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error in GPT analysis: {e}")
            print(f"🚨🚨🚨 GPT ANALYSIS FAILED - EASY TO FIND 🚨🚨🚨")
            print(f"🚨 Error Message: {str(e)}")
            print(f"🚨 Error Type: {type(e).__name__}")
            print(f"🚨 Event: {event.get('title', 'Unknown')}")
            print(f"🚨 Analysis Type: {analysis_type}")
            if hasattr(e, 'response'):
                print(f"🚨 API Response Status: {e.response.status_code}")
                print(f"🚨 API Response Text: {e.response.text}")
            print(f"🚨🚨🚨 END GPT ANALYSIS FAILURE 🚨🚨🚨")
            return self._get_fallback_analysis(event, analysis_type)
    
    def _select_model(self, event: Dict) -> str:
        """Select appropriate GPT model based on event importance"""
        event_title = event.get('title', '').lower()
        event_type = event.get('type', '').lower()
        
        # Check if this is a high-impact event
        is_high_impact = any(keyword in event_title or keyword in event_type 
                           for keyword in self.high_impact_events)
        
        # Check impact level
        impact_level = event.get('impact', 'medium').lower()
        
        if is_high_impact or impact_level == 'high':
            return 'gpt-4-turbo'
        else:
            return 'gpt-3.5-turbo'
    
    def _generate_gpt_analysis(self, event: Dict, market_context: MarketContext, 
                             analysis_type: str, model: str) -> GPTAnalysisResult:
        """Generate analysis using GPT"""
        
        # Build the prompt
        prompt = self._build_analysis_prompt(event, market_context, analysis_type)
        
        try:
            # Make GPT API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior forex market analyst specializing in macroeconomic events. Provide analysis in the exact JSON structure requested."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            analysis_data = json.loads(response.choices[0].message.content)
            
            # Calculate cost estimate
            tokens_used = response.usage.total_tokens
            cost_estimate = (tokens_used / 1000) * self.cost_estimates.get(model, 0.01)
            self.total_cost += cost_estimate
            
            # Create analysis result
            result = GPTAnalysisResult(
                general_overview=analysis_data.get('general_overview', {}),
                immediate_impact=analysis_data.get('immediate_impact', {}),
                long_term_impact=analysis_data.get('long_term_impact', {}),
                context_expectations=analysis_data.get('context_expectations', {}),
                sentiment_analysis=analysis_data.get('sentiment_analysis', {}),
                cross_market_links=analysis_data.get('cross_market_links', {}),
                trading_framework=analysis_data.get('trading_framework', {}),
                big_picture=analysis_data.get('big_picture', {}),
                confidence_score=analysis_data.get('confidence_score', 75.0),
                analysis_timestamp=datetime.now().isoformat(),
                event_id=str(event.get('id', 'unknown')),
                analysis_type=analysis_type,
                model_used=model,
                cost_estimate=cost_estimate
            )
            
            logger.info(f"✅ GPT analysis generated using {model}, cost: ${cost_estimate:.4f}")
            print(f"🚨🚨🚨 GPT ANALYSIS SUCCESS - EASY TO FIND 🚨🚨🚨")
            print(f"🚨 Model Used: {model}")
            print(f"🚨 Event: {event.get('title', 'Unknown')}")
            print(f"🚨 Cost: ${cost_estimate:.4f}")
            print(f"🚨 Event Explanation Length: {len(analysis_data.get('general_overview', {}).get('event_explanation', ''))}")
            print(f"🚨🚨🚨 END SUCCESS MESSAGE 🚨🚨🚨")
            return result
            
        except Exception as e:
            logger.error(f"❌ GPT API call failed: {e}")
            print(f"🔍 GPT API Call Error Details: {str(e)}")
            print(f"🔍 Error Type: {type(e).__name__}")
            if hasattr(e, 'response'):
                print(f"🔍 Response Status: {e.response.status_code}")
                print(f"🔍 Response Text: {e.response.text}")
            raise
    
    def _build_analysis_prompt(self, event: Dict, market_context: MarketContext, 
                             analysis_type: str) -> str:
        """Build the analysis prompt based on event type"""
        
        if analysis_type == "pre_event":
            return self._build_pre_event_prompt(event, market_context)
        else:
            return self._build_post_event_prompt(event, market_context)
    
    def _build_pre_event_prompt(self, event: Dict, market_context: MarketContext) -> str:
        """Build pre-event analysis prompt"""
        
        prompt = f"""
You are a senior forex market analyst specializing in macroeconomic events. Provide comprehensive, detailed analysis in long paragraphs with professional insights.

EVENT DETAILS:
- Title: {event.get('title', 'Unknown Event')}
- Currency: {event.get('currency', 'Unknown')}
- Impact Level: {event.get('impact', 'Medium')}
- Expected: {event.get('expected', 'Not specified')}
- Previous: {event.get('previous', 'Not specified')}
- Time: {event.get('time', 'Not specified')}
- Date: {event.get('date', 'Not specified')}

CURRENT MARKET CONTEXT:
- EUR/USD: {market_context.current_prices.get('EUR/USD', 'N/A')}
- USD/JPY: {market_context.current_prices.get('USD/JPY', 'N/A')}
- GBP/USD: {market_context.current_prices.get('GBP/USD', 'N/A')}
- Market Sentiment: {market_context.market_sentiment}

Please provide comprehensive pre-event analysis in the following JSON structure with detailed, long paragraphs:

{{
  "general_overview": {{
    "event_explanation": "Detailed explanation of what this economic indicator measures, why it matters for currency markets, and how it's calculated. Write in long, professional paragraphs with specific details about the indicator's significance.",
    "market_logic": "Comprehensive explanation of the relationship between the data and currency movement. Include specific reasoning like 'Higher than expected = Bullish for USD because it suggests higher inflation, potentially prompting the Federal Reserve to raise interest rates to curb inflation.' Write in detailed paragraphs.",
    "impact_level": "High/Medium/Low",
    "measurement_method": "Detailed explanation of how this data is calculated and reported"
  }},
  "immediate_impact": {{
    "direction": "Up/Down/Sideways",
    "magnitude": "Low/Medium/High volatility expected",
    "affected_pairs": ["Primary currency pairs that will be most affected"],
    "confidence": 85,
    "duration": "Expected duration of immediate impact (minutes/hours)",
    "detailed_analysis": "Comprehensive analysis of immediate market reaction including specific pip movements, volatility expectations, and key drivers of the reaction. Write in long, detailed paragraphs with professional insights."
  }},
  "long_term_impact": {{
    "trend_implications": "Detailed analysis of how this event affects longer-term trends with specific timeframes and market implications. Write in long, professional paragraphs.",
    "structural_changes": "Comprehensive explanation of policy implications and economic narrative shifts. Include specific central bank implications and market story changes.",
    "time_horizon": "Time horizon for long-term impact"
  }},
  "context_expectations": {{
    "priced_in_percentage": 60,
    "surprise_potential": "Low/Medium/High",
    "historical_context": "Detailed analysis of how similar events performed in the past with specific examples and market reactions. Write in long, professional paragraphs.",
    "market_positioning": "Comprehensive analysis of current market positioning and what this means for the upcoming event."
  }},
  "sentiment_analysis": {{
    "overall_tone": "Bullish/Bearish/Neutral",
    "risk_appetite": "Detailed analysis of impact on risk appetite with specific market implications. Write in long, professional paragraphs.",
    "forward_guidance": "Comprehensive analysis of impact on future expectations and market sentiment shifts."
  }},
  "cross_market_links": {{
    "bond_markets": "Detailed analysis of impact on bond yields and fixed income markets with specific yield curve implications. Write in long, professional paragraphs.",
    "equity_markets": "Comprehensive analysis of impact on stock markets with specific sector implications.",
    "commodities": "Detailed analysis of impact on gold, oil, and other commodities with specific price implications.",
    "safe_haven_flows": "Comprehensive analysis of impact on USD/JPY and safe haven currencies with specific flow implications."
  }},
  "trading_framework": {{
    "key_levels": {{
      "support": ["Key support levels to watch"],
      "resistance": ["Key resistance levels to watch"]
    }},
    "timing": {{
      "avoid_trading": "When to avoid trading (e.g., 30 min before to 30 min after)",
      "best_setup": "Optimal setup timing",
      "monitoring_start": "When to start monitoring"
    }},
    "risk_management": {{
      "position_sizing": "Conservative/Normal/Aggressive",
      "correlation_risk": "Low/Medium/High"
    }}
  }},
  "big_picture": {{
    "policy_implications": "Central bank policy implications",
    "economic_health": "Impact on economic growth and inflation",
    "narrative_shift": "How this changes the market story",
    "risk_level": "Low/Medium/High"
  }},
  "confidence_score": 85
}}

Provide analysis that is educational and helps traders understand the market dynamics, not specific trade recommendations.
"""
        return prompt
    
    def _build_post_event_prompt(self, event: Dict, market_context: MarketContext) -> str:
        """Build post-event analysis prompt"""
        
        prompt = f"""
You are a senior forex market analyst specializing in macroeconomic events. The event has just occurred and we have the actual results. Provide comprehensive, detailed analysis in long paragraphs with professional insights.

EVENT DETAILS:
- Title: {event.get('title', 'Unknown Event')}
- Currency: {event.get('currency', 'Unknown')}
- Actual: {event.get('actual', 'Not released')}
- Expected: {event.get('expected', 'Not specified')}
- Previous: {event.get('previous', 'Not specified')}

CURRENT MARKET CONTEXT:
- EUR/USD: {market_context.current_prices.get('EUR/USD', 'N/A')}
- USD/JPY: {market_context.current_prices.get('USD/JPY', 'N/A')}
- GBP/USD: {market_context.current_prices.get('GBP/USD', 'N/A')}

Please provide comprehensive post-event analysis in the following JSON structure with detailed, long paragraphs:

{{
  "general_overview": {{
    "event_explanation": "Detailed explanation of what this economic indicator measures and why it matters for currency markets. Write in long, professional paragraphs with specific details about the indicator's significance.",
    "market_logic": "Comprehensive explanation of the relationship between the actual data and currency movement. Include specific reasoning about why the actual result is bullish/bearish for the currency. Write in detailed paragraphs.",
    "impact_level": "High/Medium/Low",
    "measurement_method": "Detailed explanation of how this data is calculated and reported"
  }},
  "immediate_impact": {{
    "direction": "Up/Down/Sideways",
    "magnitude": "Low/Medium/High volatility expected",
    "affected_pairs": ["Primary currency pairs that were most affected"],
    "confidence": 85,
    "duration": "Expected duration of immediate impact (minutes/hours)",
    "detailed_analysis": "Comprehensive analysis of the actual market reaction including specific pip movements, volatility patterns, and key drivers of the reaction. Write in long, detailed paragraphs with professional insights about what actually happened."
  }},
  "long_term_impact": {{
    "trend_implications": "Detailed analysis of how this actual result affects longer-term trends with specific timeframes and market implications. Write in long, professional paragraphs.",
    "structural_changes": "Comprehensive explanation of policy implications and economic narrative shifts based on the actual result. Include specific central bank implications and market story changes.",
    "time_horizon": "Time horizon for long-term impact"
  }},
  "context_expectations": {{
    "priced_in_percentage": 60,
    "surprise_potential": "Low/Medium/High",
    "historical_context": "Detailed analysis of how this actual result compares to historical reactions and similar events. Write in long, professional paragraphs.",
    "market_positioning": "Comprehensive analysis of how the actual result affected market positioning and what this means going forward."
  }},
  "sentiment_analysis": {{
    "overall_tone": "Bullish/Bearish/Neutral",
    "risk_appetite": "Detailed analysis of impact on risk appetite with specific market implications based on the actual result. Write in long, professional paragraphs.",
    "forward_guidance": "Comprehensive analysis of impact on future expectations and market sentiment shifts based on the actual data."
  }},
  "cross_market_links": {{
    "bond_markets": "Detailed analysis of impact on bond yields and fixed income markets with specific yield curve implications based on the actual result. Write in long, professional paragraphs.",
    "equity_markets": "Comprehensive analysis of impact on stock markets with specific sector implications based on the actual data.",
    "commodities": "Detailed analysis of impact on gold, oil, and other commodities with specific price implications based on the actual result.",
    "safe_haven_flows": "Comprehensive analysis of impact on USD/JPY and safe haven currencies with specific flow implications based on the actual data."
  }},
  "trading_framework": {{
    "key_levels": {{
      "support": ["Key support levels to watch based on actual result"],
      "resistance": ["Key resistance levels to watch based on actual result"]
    }},
    "timing": {{
      "avoid_trading": "When to avoid trading based on actual volatility",
      "best_setup": "Optimal setup timing based on actual market reaction",
      "monitoring_start": "When to start monitoring based on actual result"
    }},
    "risk_management": {{
      "position_sizing": "Conservative/Normal/Aggressive based on actual volatility",
      "correlation_risk": "Low/Medium/High based on actual market reaction"
    }}
  }},
  "big_picture": {{
    "policy_implications": "Central bank policy implications based on actual result",
    "economic_health": "Impact on economic growth and inflation based on actual data",
    "narrative_shift": "How this actual result changes the market story",
    "risk_level": "Low/Medium/High based on actual market reaction"
  }},
  "confidence_score": 85
}}

Provide analysis that is educational and helps traders understand the market dynamics based on the actual results, not specific trade recommendations. Focus on what actually happened versus expectations and what this means going forward.
"""
        return prompt
    
    def _generate_cache_key(self, event: Dict, analysis_type: str) -> str:
        """Generate cache key for analysis"""
        event_data = f"{event.get('id', '')}_{event.get('title', '')}_{analysis_type}"
        return hashlib.md5(event_data.encode()).hexdigest()
    
    def _get_cached_analysis(self, cache_key: str) -> Optional[GPTAnalysisResult]:
        """Get cached analysis if available"""
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(f"gpt_analysis:{cache_key}")
                if cached_data:
                    return pickle.loads(cached_data.encode('latin1'))
            else:
                # In-memory cache
                if cache_key in self.memory_cache:
                    timestamp = self.cache_timestamps.get(cache_key, 0)
                    # Cache for 1 hour for pre-event, 24 hours for post-event
                    cache_duration = 3600 if 'pre_event' in cache_key else 86400
                    if time.time() - timestamp < cache_duration:
                        return self.memory_cache[cache_key]
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None
    
    def _cache_analysis(self, cache_key: str, analysis: GPTAnalysisResult):
        """Cache analysis result"""
        try:
            if self.redis_client:
                # Cache for 1 hour for pre-event, 24 hours for post-event
                cache_duration = 3600 if 'pre_event' in cache_key else 86400
                self.redis_client.setex(
                    f"gpt_analysis:{cache_key}",
                    cache_duration,
                    pickle.dumps(analysis).decode('latin1')
                )
            else:
                # In-memory cache
                self.memory_cache[cache_key] = analysis
                self.cache_timestamps[cache_key] = time.time()
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        
        # Reset counter if hour has passed
        if (now - self.last_hour_reset).total_seconds() > 3600:
            self.api_calls_this_hour = 0
            self.last_hour_reset = now
        
        return self.api_calls_this_hour < self.max_calls_per_hour
    
    def _get_fallback_analysis(self, event: Dict, analysis_type: str) -> GPTAnalysisResult:
        """Generate fallback analysis when GPT is unavailable"""
        logger.warning("Using fallback analysis")
        print(f"🚨🚨🚨 FALLBACK ANALYSIS USED - EASY TO FIND 🚨🚨🚨")
        print(f"🚨 Event: {event.get('title', 'Unknown')}")
        print(f"🚨 Analysis Type: {analysis_type}")
        print(f"🚨🚨🚨 END FALLBACK MESSAGE 🚨🚨🚨")
        
        return GPTAnalysisResult(
            general_overview={
                "event_explanation": f"Analysis for {event.get('title', 'Unknown Event')}",
                "market_logic": "Higher than expected typically bullish for the currency",
                "impact_level": event.get('impact', 'Medium'),
                "measurement_method": "Standard economic measurement"
            },
            immediate_impact={
                "direction": "Sideways",
                "magnitude": "Medium",
                "affected_pairs": ["EUR/USD", "USD/JPY"],
                "confidence": 60,
                "duration": "1-2 hours"
            },
            long_term_impact={
                "trend_implications": "Monitor for trend continuation or reversal",
                "structural_changes": "Watch for policy implications",
                "time_horizon": "1-2 weeks"
            },
            context_expectations={
                "priced_in_percentage": 50,
                "surprise_potential": "Medium",
                "historical_context": "Similar events have shown mixed results",
                "market_positioning": "Neutral positioning"
            },
            sentiment_analysis={
                "overall_tone": "Neutral",
                "risk_appetite": "No significant change expected",
                "forward_guidance": "Monitor for guidance changes"
            },
            cross_market_links={
                "bond_markets": "Monitor bond yield reactions",
                "equity_markets": "Watch for equity market correlation",
                "commodities": "Monitor commodity market impact",
                "safe_haven_flows": "Watch safe haven currency flows"
            },
            trading_framework={
                "key_levels": {
                    "support": ["Key support levels"],
                    "resistance": ["Key resistance levels"]
                },
                "timing": {
                    "avoid_trading": "30 minutes around release",
                    "best_setup": "1-2 hours after release",
                    "monitoring_start": "1 hour before release"
                },
                "risk_management": {
                    "position_sizing": "Normal",
                    "correlation_risk": "Medium"
                }
            },
            big_picture={
                "policy_implications": "Monitor for policy implications",
                "economic_health": "Assess economic health impact",
                "narrative_shift": "Watch for narrative changes",
                "risk_level": "Medium"
            },
            confidence_score=60.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type=analysis_type,
            model_used="fallback",
            cost_estimate=0.0
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_cost": self.total_cost,
            "api_calls_this_hour": self.api_calls_this_hour,
            "max_calls_per_hour": self.max_calls_per_hour,
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "last_reset": self.last_hour_reset.isoformat()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # This is a simplified calculation
        return 0.0  # Would need to track actual hits/misses

# Global instance
gpt_ai_analyzer = GPTAIAnalyzer()
