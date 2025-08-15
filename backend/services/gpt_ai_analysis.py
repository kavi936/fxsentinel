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

# Check if Redis is available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

@dataclass
class MarketContext:
    """Enhanced market context with positioning data"""
    current_prices: Dict[str, float]
    recent_volatility: Dict[str, float]
    market_sentiment: Dict[str, str]
    key_levels: Dict[str, Dict[str, float]]
    economic_calendar: List[Dict]
    bond_yields: Dict[str, float]
    equity_indices: Dict[str, float]
    commodity_prices: Dict[str, float]
    # New positioning data
    retail_sentiment: Dict[str, float]  # 0.0 to 1.0 (0% to 100% long)
    futures_positioning: Dict[str, int]  # Net long/short contracts
    institutional_flow: Dict[str, float]  # Net buying/selling in millions
    time_to_event: int  # seconds until event
    liquidity_level: int  # 1=High, 2=Medium, 3=Low
    scenario_probabilities: Dict[str, float]  # Higher, Lower, In-line probabilities

@dataclass
class GPTAnalysisResult:
    """Streamlined GPT analysis result with optimized structure"""
    # Event summary
    event_summary: Dict[str, Any]
    
    # Market reaction
    market_reaction: Dict[str, Any]
    
    # Implications and takeaways (merged from context_and_implications and key_takeaways)
    implications_takeaways: Dict[str, Any]
    
    # Trading plan (merged from trading_strategy and trading_framework)
    trading_plan: Dict[str, Any]
    
    # Big picture (merged from big_picture and big_picture_implications)
    big_picture: Dict[str, Any]
    
    # Meta data
    confidence_score: float
    analysis_timestamp: str
    event_id: str
    analysis_type: str
    model_used: str
    cost_estimate: float
    cache_hit: bool = False
    definition_source: str = "internal"  # internal, cached_ai, ai_fallback

class GPTAIAnalyzer:
    def __init__(self):
        # Configure OpenAI - initialize client lazily to avoid startup errors
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if not self.api_key:
            print("🔍 WARNING: OPENAI_API_KEY not found in environment variables!")
            print("🔍 This will cause GPT analysis to fail and use fallback content.")
        else:
            print(f"🔍 OpenAI API Key found: {self.api_key[:10]}...{self.api_key[-4:]}")
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                print(f"🔍 GPT Analyzer initialized with API key: VALID")
            except Exception as e:
                print(f"🔍 Error initializing OpenAI client: {e}")
                self.client = None
        
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
        
        # Enhanced economic indicators cache
        self.economic_indicators_cache = self._load_economic_indicators_cache()
        
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
    
    def _load_economic_indicators_cache(self) -> Dict[str, Any]:
        """Load economic indicators cache from file"""
        cache_file = 'economic_indicators_cache.json'
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                print(f"✅ Loaded {len(cache)} cached economic indicators")
                return cache
            else:
                print("ℹ️ No economic indicators cache found, starting fresh")
                return {}
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
            return {}
    
    def _save_economic_indicators_cache(self):
        """Save economic indicators cache to file"""
        cache_file = 'economic_indicators_cache.json'
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.economic_indicators_cache, f, indent=2)
            print(f"✅ Saved {len(self.economic_indicators_cache)} economic indicators to cache")
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
    
    def analyze_macro_event(self, event: Dict, market_context: MarketContext, 
                          analysis_type: str = "pre_event") -> GPTAnalysisResult:
        """
        Generate comprehensive GPT analysis for macro events with enhanced inputs
        
        Args:
            event: Economic event data (normalized format)
            market_context: Enhanced market context with positioning data
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
            
            # Generate analysis with enhanced inputs
            analysis_result = self._generate_enhanced_gpt_analysis(event, market_context, analysis_type, model)
            
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
    
    def _generate_enhanced_gpt_analysis(self, event: Dict, market_context: MarketContext, 
                                      analysis_type: str, model: str) -> GPTAnalysisResult:
        """Generate enhanced analysis using GPT with all new inputs"""
        
        # Build the enhanced prompt
        prompt = self._build_enhanced_analysis_prompt(event, market_context, analysis_type)
        
        try:
            # Check if OpenAI client is available
            if not self.client:
                print(f"🚨🚨🚨 GPT CLIENT NOT AVAILABLE - EASY TO FIND 🚨🚨🚨")
                print(f"🚨 API Key available: {'YES' if self.api_key else 'NO'}")
                print(f"🚨 Client initialized: {'NO'}")
                print(f"🚨🚨🚨 END CLIENT CHECK 🚨🚨🚨")
                raise Exception("OpenAI client not initialized - API key may be missing")
            
            # Make GPT API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior market analyst specializing in universal economic event analysis for ANY currency, asset, or market. Write for professional traders with 3+ years experience. Use clear, insightful, yet concise tone. Focus on actionable insights and risk management. Provide universal analysis that works for any economic event, any currency, and any market. Provide analysis in the exact JSON structure requested."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=2500,  # Increased for enhanced analysis
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            response_content = response.choices[0].message.content
            print(f"🚨🚨🚨 RAW GPT RESPONSE - EASY TO FIND 🚨🚨🚨")
            print(f"🚨 Response Content: {response_content[:500]}...")
            print(f"🚨 Response Length: {len(response_content)}")
            print(f"🚨🚨🚨 END RAW RESPONSE 🚨🚨🚨")
            
            try:
                analysis_data = json.loads(response_content)
            except json.JSONDecodeError as e:
                print(f"🚨🚨🚨 JSON PARSE ERROR - EASY TO FIND 🚨🚨🚨")
                print(f"🚨 Error: {e}")
                print(f"🚨 Response Content: {response_content}")
                print(f"🚨🚨🚨 END JSON ERROR 🚨🚨🚨")
                raise Exception(f"Failed to parse GPT response as JSON: {e}")
            
            # Calculate cost estimate
            tokens_used = response.usage.total_tokens
            cost_estimate = (tokens_used / 1000) * self.cost_estimates.get(model, 0.01)
            self.total_cost += cost_estimate
            
            # Create streamlined analysis result
            result = GPTAnalysisResult(
                event_summary=analysis_data.get('event_summary', {
                    "release": event.get('title', 'Unknown Event'),
                    "outcome": "Analysis based on expected vs previous data",
                    "previous": event.get('previous', 'N/A'),
                    "expected": event.get('expected', 'N/A'),
                    "actual": event.get('actual', 'N/A')
                }),
                market_reaction=analysis_data.get('market_reaction', {
                    "price_action": f"Expected price movements in {event.get('currency', 'Unknown')} pairs will depend on the actual data versus expectations.",
                    "volatility": "Medium volatility expected around the release",
                    "reason": "Market reaction will be driven by the comparison between actual and expected data"
                }),
                implications_takeaways=analysis_data.get('implications_takeaways', {
                    "economic_context": "Economic context analysis based on the indicator type and current conditions",
                    "policy_implications": "Policy implications will depend on the data outcome",
                    "market_positioning": "Market positioning analysis based on current sentiment",
                    "event_bias": "Neutral - depends on actual vs expected data",
                    "sentiment": "Market sentiment will shift based on surprise factor",
                    "risk_level": "Medium - typical volatility around economic releases"
                }),
                trading_plan=analysis_data.get('trading_plan', {
                    "best_approach": "Range trading with breakout potential based on surprise factor",
                    "key_levels": "Monitor key support and resistance levels around current price",
                    "position_sizing": "Conservative position sizing due to potential volatility",
                    "avoid_strategies": "Avoid aggressive positioning before data release",
                    "next_catalysts": "Focus on upcoming central bank meetings and related economic data",
                    "support_levels": ["Key support levels to be determined"],
                    "resistance_levels": ["Key resistance levels to be determined"],
                    "best_setup": "Range trading with breakout potential",
                    "position_sizing_risk": "Conservative"
                }),
                big_picture=analysis_data.get('big_picture', {
                    "economic_outlook": f"The data will provide insights into {event.get('currency', 'Unknown')} economic health",
                    "policy_trajectory": "Central bank policy trajectory will be influenced by the data outcome",
                    "medium_term_direction": f"Medium-term {event.get('currency', 'Unknown')} direction will depend on policy implications",
                    "forward_focus": "Monitor for follow-up data releases and central bank communications",
                    "policy_impact": "Policy implications will be determined by the data outcome",
                    "risk_assessment": "Medium"
                }),
                confidence_score=analysis_data.get('confidence_score', 75.0),
                analysis_timestamp=datetime.now().isoformat(),
                event_id=str(event.get('id', 'unknown')),
                analysis_type=analysis_type,
                model_used=model,
                cost_estimate=cost_estimate
            )
            
            logger.info(f"✅ Enhanced GPT analysis generated using {model}, cost: ${cost_estimate:.4f}")
            print(f"🚨🚨🚨 ENHANCED GPT ANALYSIS SUCCESS - EASY TO FIND 🚨🚨🚨")
            print(f"🚨 Model Used: {model}")
            print(f"🚨 Event: {event.get('title', 'Unknown')}")
            print(f"🚨 Cost: ${cost_estimate:.4f}")
            print(f"🚨 Analysis Sections: {len(analysis_data)}")
            print(f"🚨🚨🚨 END SUCCESS MESSAGE 🚨🚨🚨")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced GPT API call failed: {e}")
            print(f"🔍 Enhanced GPT API Call Error Details: {str(e)}")
            print(f"🔍 Error Type: {type(e).__name__}")
            if hasattr(e, 'response'):
                print(f"🔍 Response Status: {e.response.status_code}")
                print(f"🔍 Response Text: {e.response.text}")
            raise
    
    def _build_enhanced_analysis_prompt(self, event: Dict, market_context: MarketContext, 
                                      analysis_type: str) -> str:
        """Build the enhanced analysis prompt based on event type"""
        
        if analysis_type == "pre_event":
            return self._build_enhanced_pre_event_prompt(event, market_context)
        else:
            return self._build_enhanced_post_event_prompt(event, market_context)
    
    def _build_enhanced_pre_event_prompt(self, event: Dict, market_context: MarketContext) -> str:
        """Build the ultimate enhanced pre-event analysis prompt combining best practices"""
        
        # Get economic context using hybrid approach
        economic_context = self.get_economic_indicator_context(event.get('title', 'Unknown Event'))
        
        prompt = f"""
You are an experienced Forex strategist providing professional, data-driven market analysis for retail traders. 
Your goal: Deliver clear, insightful analysis that explains cause-and-effect logic, market expectations, and risk scenarios in a structured format. 
Do NOT give explicit trade signals or recommendations. Instead, provide educational insights, scenario-based reasoning, and actionable frameworks for understanding market dynamics.

**CRITICAL: Focus your analysis specifically on {event.get('currency', 'Unknown')} currency pairs and the relevant central bank (e.g., Fed for USD, BoE for GBP, ECB for EUR, BoJ for JPY).**

---

### 📌 Event Details:
Title: {event.get('title', 'Unknown Event')}
Currency: {event.get('currency', 'Unknown')}
Impact Level: {event.get('impact', 'Medium')}
Expected: {event.get('expected', 'Not specified')}
Previous: {event.get('previous', 'Not specified')}
Actual: N/A (Pre-Event Analysis)
Date & Time: {event.get('date', 'Not specified')} {event.get('time', 'Not specified')}

### 📌 Market Context:
Current Prices: {json.dumps(market_context.current_prices, indent=2)}
Recent Volatility: {json.dumps(market_context.recent_volatility, indent=2)}
Market Sentiment: {json.dumps(market_context.market_sentiment, indent=2)}
Key Technical Levels: {json.dumps(market_context.key_levels, indent=2)}

### 📌 Enhanced Market Positioning:
Retail Sentiment: {json.dumps(market_context.retail_sentiment, indent=2)}
Futures Positioning: {json.dumps(market_context.futures_positioning, indent=2)}
Institutional Flow: {json.dumps(market_context.institutional_flow, indent=2)}
Time to Event: {market_context.time_to_event} seconds
Liquidity Level: {market_context.liquidity_level} (1=High, 2=Medium, 3=Low)

### 📌 Cross-Market Context:
Bond Yields: {json.dumps(market_context.bond_yields, indent=2)}
Equity Indices: {json.dumps(market_context.equity_indices, indent=2)}
Commodities: {json.dumps(market_context.commodity_prices, indent=2)}

### 📌 Scenario Probabilities:
Higher than Expected: {market_context.scenario_probabilities.get('higher', 0.30):.1%}
Lower than Expected: {market_context.scenario_probabilities.get('lower', 0.50):.1%}
In Line with Expectations: {market_context.scenario_probabilities.get('inline', 0.20):.1%}

### 📌 Economic Knowledge:
{economic_context}

### 📌 Universal Event Analysis Framework:
The system provides comprehensive analysis for ANY economic event, currency, or asset:

**Universal Event Summary:**
- Event name, currency/asset, release date/time, previous/expected/actual values
- Deviation assessment: above, below, or in line with expectations
- Economic significance and market implications

**Universal Market Reaction:**
- Price action with quantified ranges (pips for FX, points for indices)
- Volatility assessment (low/medium/high) with specific reasoning
- Movement explanation based on deviation, market bias, and sentiment

**Universal Implications & Takeaways:**
- Economic context: why the number matters for the economy
- Policy implications: central bank impact and rate expectations
- Market bias: bullish, bearish, or neutral with clear reasoning
- Risk level: trader-appropriate risk assessment (low/medium/high)

**Universal Trading Plan:**
- Actionable strategies based on deviation type
- Key support/resistance levels and position sizing
- Risk management guidelines and strategies to avoid
- Market condition-appropriate recommendations

**Universal Medium-Term Outlook:**
- Trend assessment based on deviation strength
- Policy trajectory and macroeconomic risks
- Forward focus: upcoming catalysts and events to watch
- Range-bound vs directional guidance

**Universal Deviation Handling:**
- Above expectations: bullish potential with overshooting risks
- Below expectations: bearish potential with accelerated sell-off risks
- In line with expectations: stability focus with range-bound trading

### 📌 Currency-Specific Analysis Requirements:
- **Currency Focus**: Analyze specifically for {event.get('currency', 'Unknown')} currency pairs
- **Central Bank**: Consider the relevant central bank's policy stance and reaction function
- **Currency Pairs**: Focus on {event.get('currency', 'Unknown')}/USD, EUR/{event.get('currency', 'Unknown')}, {event.get('currency', 'Unknown')}/JPY, etc.
- **Country Context**: Consider the specific economic conditions and policy environment for the {event.get('currency', 'Unknown')} country

### 📌 Historical Context:
Compare to last 3 similar releases and typical market reactions for this type of economic indicator.

### 📌 Analysis Type:
Pre-Event Analysis

---

## ✅ UNIVERSAL OUTPUT REQUIREMENTS:
Provide analysis in **JSON** with the following universal structure for ANY economic event, currency, or asset:

{{
  "event_summary": {{
    "release": "{event.get('title', 'Unknown Event')}",
    "date_time": "{event.get('date', 'Not specified')} {event.get('time', 'Not specified')}",
    "previous": "{event.get('previous', 'N/A')}",
    "expected": "{event.get('expected', 'N/A')}",
    "actual": "{event.get('actual', 'N/A')}",
    "outcome": "Universal assessment: 'Above expectations → Bullish', 'Below expectations → Bearish', 'In line with expectations → Neutral'. Include economic significance."
  }},
  
  "market_reaction": {{
    "price_action": "Universal price action description for {event.get('currency', 'Unknown')} with quantified ranges (pips for FX, points for indices). Include movement patterns and key levels.",
    "volatility": "Universal volatility assessment (Low/Medium/High) with specific reasoning based on deviation magnitude and market conditions.",
    "reason": "Universal explanation of market reaction based on deviation from expectations, market bias, and sentiment."
  }},
  
  "implications_takeaways": {{
    "economic_context": "Universal economic context: why this data matters for the economy, growth, inflation, and employment.",
    "policy_implications": "Universal policy impact: how this affects central bank decisions, rate expectations, and monetary policy trajectory.",
    "market_bias": "Universal market bias: Bullish/Bearish/Neutral with clear reasoning based on deviation.",
    "risk_level": "Universal risk assessment (Low/Medium/High) with trader-appropriate guidance."
  }},
  
  "trading_plan": {{
    "best_approach": "Universal trading strategy based on deviation: range trading for neutral, breakout for strong deviations, fade for extreme moves.",
    "avoid_strategies": "Universal risk management: what strategies to avoid under current market conditions.",
    "key_levels": "Universal support/resistance levels and key zones to watch.",
    "position_sizing": "Universal position sizing recommendations based on volatility and risk level.",
    "next_catalysts": "Universal forward focus: upcoming events and catalysts that could shift direction."
  }},
  
  "big_picture": {{
    "economic_outlook": "Universal economic outlook based on data deviation and broader economic context.",
    "medium_term_direction": "Universal medium-term direction: range-bound for minor deviations, directional for strong deviations.",
    "policy_trajectory": "Universal policy trajectory and central bank implications.",
    "forward_focus": "Universal forward focus: macro risks, upcoming catalysts, and events to monitor."
  }},
  
  "confidence_score": 85
}}

---

### ✅ Additional Rules:
- Keep each section **under 150 words**, concise but data-driven.
- Always use **actual figures from input** (expected vs previous).
- Mention **surprise potential** and if the market has priced in expectations.
- Provide historical comparison where relevant (e.g., last release impact).
- Tone: **Professional, analytical, educational**.
- Use **specific numbers and data points** from the market context provided.
- Consider **market positioning data** (retail sentiment, futures positioning, institutional flow).
- Factor in **time to event** and **liquidity conditions**.
- **CRITICAL**: Focus analysis specifically on {event.get('currency', 'Unknown')} currency pairs and the relevant central bank.
- **CRITICAL**: Mention specific {event.get('currency', 'Unknown')} currency pairs (e.g., {event.get('currency', 'Unknown')}/USD, EUR/{event.get('currency', 'Unknown')}, {event.get('currency', 'Unknown')}/JPY).
- **CRITICAL**: Consider the specific central bank's policy stance and reaction function.
"""
        return prompt
    
    def get_economic_indicator_context(self, event_title: str) -> str:
        """Enhanced hybrid approach: hardcoded patterns → cached AI → AI fallback"""
        title_lower = event_title.lower()
        
        # Step 1: Try hardcoded patterns (fastest)
        context = self._get_hardcoded_context(title_lower)
        if context:
            return context
        
        # Step 2: Try cached AI definitions
        cached_context = self._get_cached_context(title_lower)
        if cached_context:
            return cached_context
        
        # Step 3: Use AI fallback and cache result
        ai_context = self._get_ai_fallback_context(event_title)
        self._cache_context(title_lower, ai_context)
        return ai_context
    
    def _get_cached_context(self, title_lower: str) -> Optional[str]:
        """Get context from cached AI definitions"""
        # Check for exact match first
        if title_lower in self.economic_indicators_cache:
            cache_entry = self.economic_indicators_cache[title_lower]
            # Check if cache entry is not expired (30 days for AI-generated)
            created_date = datetime.fromisoformat(cache_entry.get('created_date', '2024-01-01'))
            if (datetime.now() - created_date).days < 30:
                print(f"✅ Using cached AI definition for: {title_lower}")
                return cache_entry.get('definition', '')
        
        # Check for partial matches
        for key, cache_entry in self.economic_indicators_cache.items():
            if key in title_lower or title_lower in key:
                created_date = datetime.fromisoformat(cache_entry.get('created_date', '2024-01-01'))
                if (datetime.now() - created_date).days < 30:
                    print(f"✅ Using cached AI definition (partial match) for: {title_lower}")
                    return cache_entry.get('definition', '')
        
        return None
    
    def _cache_context(self, indicator_key: str, context: str):
        """Cache AI-generated context for future use"""
        cache_entry = {
            "definition": context,
            "source": "openai_fallback",
            "created_date": datetime.now().isoformat(),
            "usage_count": 1
        }
        
        self.economic_indicators_cache[indicator_key] = cache_entry
        self._save_economic_indicators_cache()
        print(f"💾 Cached new AI definition for: {indicator_key}")
    
    def _get_ai_fallback_context(self, event_title: str) -> str:
        """Use AI to generate context for unknown economic indicators"""
        try:
            # Check if we have GPT available
            if not self.client:
                print(f"⚠️ GPT not available for indicator identification, using fallback for: {event_title}")
                return self._get_fallback_context(event_title)
            
            # Create a simple prompt to identify the economic indicator
            prompt = f"Explain what '{event_title}' is for forex traders in 2 sentences. Focus on what it measures and how it typically affects currency markets. Be concise and specific."
            
            # Make a quick GPT call
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for identification
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert economic analyst specializing in forex markets."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=100,  # Keep it short
                response_format={"type": "text"}
            )
            
            context = response.choices[0].message.content.strip()
            print(f"🤖 AI generated definition for '{event_title}': {context[:100]}...")
            
            return context
            
        except Exception as e:
            print(f"❌ Error in AI indicator identification for '{event_title}': {e}")
            return self._get_fallback_context(event_title)
    
    def _get_hardcoded_context(self, title_lower: str) -> str:
        """Get context using hardcoded patterns (fast)"""
        if 'ppi' in title_lower or 'producer price' in title_lower:
            return """
PPI (Producer Price Index) measures the average change over time in the selling prices received by domestic producers for their output. It's a leading indicator of consumer inflation because producers often pass on cost increases to consumers. Higher PPI suggests future CPI increases, which can influence Federal Reserve policy decisions. PPI is particularly important for USD as it affects inflation expectations and interest rate outlook.
"""
        elif 'cpi' in title_lower or 'consumer price' in title_lower:
            return """
CPI (Consumer Price Index) measures the average change over time in the prices paid by urban consumers for a market basket of consumer goods and services. It's the primary gauge of inflation and directly influences Federal Reserve monetary policy decisions. Higher CPI typically leads to expectations of tighter monetary policy, which strengthens the USD. CPI is crucial for forex markets as it affects interest rate expectations.
"""
        elif 'non-farm' in title_lower or 'nfp' in title_lower:
            return """
Non-Farm Payrolls (NFP) measures the change in the number of employed people during the previous month, excluding the farming industry. It's the most important employment indicator and a key driver of Federal Reserve policy decisions. Strong NFP numbers suggest economic strength and potential inflationary pressures, which can lead to higher interest rates and a stronger USD. Weak NFP numbers suggest economic weakness and potential dovish policy.
"""
        elif 'employment' in title_lower and 'unemployment' not in title_lower:
            return """
Employment data measures the number of people employed in the economy. Strong employment growth suggests economic strength and potential inflationary pressures, which can lead to higher interest rates and a stronger currency. Weak employment growth suggests economic weakness and potential policy accommodation, which can weaken the currency. Employment data is closely watched by central banks for monetary policy decisions.
"""
        elif 'gdp' in title_lower:
            return """
GDP (Gross Domestic Product) measures the total value of all goods and services produced within a country's borders. It's the broadest measure of economic activity and a key indicator of economic health. Higher GDP growth suggests economic strength and can lead to stronger currency valuations. GDP data influences central bank policy decisions and market sentiment about economic prospects.
"""
        elif 'retail sales' in title_lower or 'retail' in title_lower and 'sales' in title_lower:
            return """
Retail Sales measures the total receipts at stores that sell merchandise and related services to final consumers. It's a key indicator of consumer spending, which accounts for about 70% of economic activity. Strong retail sales suggest robust consumer demand and economic strength, which can strengthen the currency. Weak retail sales suggest economic weakness and potential dovish policy responses.
"""
        elif 'manufacturing' in title_lower or 'ism' in title_lower or 'industrial output' in title_lower or 'manufacturing output' in title_lower:
            return """
Manufacturing indicators measure the health of the manufacturing sector, which is a key component of economic activity. Strong manufacturing data suggests economic strength and potential inflationary pressures. Weak manufacturing data suggests economic weakness and potential policy accommodation. Manufacturing data affects currency valuations through its impact on economic growth expectations.
"""
        elif 'fomc' in title_lower or ('interest rate' in title_lower and 'decision' in title_lower):
            return """
Interest rate decisions by central banks are the most important drivers of currency valuations. The Federal Open Market Committee (FOMC) sets the federal funds rate, which influences all other interest rates in the economy. Higher interest rates typically strengthen a currency by making it more attractive to investors seeking yield. Lower interest rates typically weaken a currency by reducing its yield appeal. Interest rate decisions also affect inflation expectations and economic growth outlook.
"""
        elif 'unemployment' in title_lower or 'jobless' in title_lower or 'unemployment claims' in title_lower:
            return """
Unemployment data measures the percentage of the labor force that is unemployed and actively seeking employment. Lower unemployment rates suggest economic strength and potential inflationary pressures, which can lead to higher interest rates and a stronger currency. Higher unemployment rates suggest economic weakness and potential policy accommodation, which can weaken the currency. Unemployment data is closely watched by central banks for monetary policy decisions. For GBP events, focus on Bank of England policy implications and GBP currency pairs. For USD events, focus on Federal Reserve policy and USD pairs. For EUR events, focus on ECB policy and EUR pairs.
"""
        elif 'housing' in title_lower or 'home sales' in title_lower or 'construction' in title_lower or 'building permits' in title_lower or 'housing permits' in title_lower:
            return """
Housing market indicators measure the health of the residential real estate sector, which is a significant component of economic activity. Strong housing data suggests robust consumer confidence and economic strength, which can strengthen the currency. Weak housing data suggests economic weakness and potential policy accommodation. Housing data affects currency valuations through its impact on economic growth and consumer spending.
"""
        elif 'trade balance' in title_lower or 'current account' in title_lower or 'exports' in title_lower or 'imports' in title_lower or 'trade deficit' in title_lower or 'trade surplus' in title_lower:
            return """
Trade balance data measures the difference between a country's exports and imports. A trade surplus (exports > imports) typically strengthens the currency as it indicates strong external demand and economic competitiveness. A trade deficit (imports > exports) typically weakens the currency as it indicates reliance on foreign goods and potential capital outflows. Trade data affects currency valuations through its impact on economic balance and international competitiveness.
"""
        elif 'consumer confidence' in title_lower or 'sentiment' in title_lower or 'consumer spending' in title_lower or 'personal consumption' in title_lower:
            return """
Consumer confidence and sentiment indicators measure how optimistic consumers are about the economy and their personal financial situation. High consumer confidence suggests strong consumer spending and economic growth, which can strengthen the currency. Low consumer confidence suggests weak consumer spending and economic weakness, which can weaken the currency. Consumer sentiment affects currency valuations through its impact on consumer spending and economic growth.
"""
        elif 'industrial production' in title_lower or 'capacity utilization' in title_lower or 'industrial output' in title_lower:
            return """
Industrial production measures the output of the manufacturing, mining, and utilities sectors. High industrial production suggests strong economic activity and potential inflationary pressures, which can lead to higher interest rates and a stronger currency. Low industrial production suggests economic weakness and potential policy accommodation, which can weaken the currency. Industrial production affects currency valuations through its impact on economic growth and inflation.
"""
        elif 'pmi' in title_lower or 'purchasing managers' in title_lower:
            return """
Purchasing Managers Index (PMI) measures the economic health of the manufacturing and services sectors. PMI values above 50 indicate expansion, while values below 50 indicate contraction. High PMI readings suggest economic strength and potential inflationary pressures, which can strengthen the currency. Low PMI readings suggest economic weakness and potential policy accommodation, which can weaken the currency. PMI data affects currency valuations through its impact on economic growth expectations.
"""
        elif 'inflation' in title_lower or 'price index' in title_lower:
            return """
Inflation indicators measure the rate at which prices for goods and services are rising. Higher inflation typically leads to expectations of tighter monetary policy to curb price increases, which can strengthen the currency. Lower inflation typically leads to expectations of accommodative monetary policy to stimulate growth, which can weaken the currency. Inflation data is crucial for central bank policy decisions and currency valuations.
"""
        
        return None  # No hardcoded pattern matched
    
    def _get_gpt_identified_context(self, event_title: str) -> str:
        """Use GPT to identify the economic indicator type and provide context"""
        try:
            # Check if we have GPT available
            if not self.client:
                print(f"⚠️ GPT not available for indicator identification, using fallback for: {event_title}")
                return self._get_fallback_context(event_title)
            
            # Create a simple prompt to identify the economic indicator
            prompt = f"""
You are an expert in economic indicators and forex markets. 

Given this economic event title: "{event_title}"

Please identify what type of economic indicator this is and provide a brief explanation (2-3 sentences) of:
1. What this indicator measures
2. Why it matters for currency markets
3. How it typically affects currency valuations

**IMPORTANT**: Focus on the specific currency and central bank implications. For example:
- GBP events: Focus on Bank of England policy and GBP currency pairs
- USD events: Focus on Federal Reserve policy and USD currency pairs  
- EUR events: Focus on ECB policy and EUR currency pairs
- JPY events: Focus on Bank of Japan policy and JPY currency pairs

Respond in a clear, concise format suitable for forex traders.

Examples:
- "PPI (Producer Price Index) measures producer-level inflation and is a leading indicator for consumer inflation. Higher PPI suggests future CPI increases, which can influence Federal Reserve policy decisions and strengthen the USD."
- "Retail Sales measures consumer spending patterns and accounts for 70% of economic activity. Strong retail sales suggest economic strength and can strengthen the currency, while weak sales suggest economic weakness."
"""
            
            # Make a quick GPT call
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for identification
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert economic analyst specializing in forex markets."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=150,  # Keep it short
                response_format={"type": "text"}
            )
            
            context = response.choices[0].message.content.strip()
            print(f"🤖 GPT identified indicator type for '{event_title}': {context[:100]}...")
            
            return context
            
        except Exception as e:
            print(f"❌ Error in GPT indicator identification for '{event_title}': {e}")
            return self._get_fallback_context(event_title)
    
    def _get_fallback_context(self, event_title: str) -> str:
        """Fallback context when no pattern matches and GPT is unavailable"""
        return f"""
This economic indicator ({event_title}) provides important insights into economic activity and can influence currency valuations through its impact on economic growth, inflation expectations, and central bank policy decisions. The specific relationship between this data and currency movement depends on the indicator's characteristics and current market conditions. Traders should monitor the actual data release and market reaction for specific trading opportunities.
"""
    
    def _build_enhanced_pre_event_prompt(self, event: Dict, market_context: MarketContext) -> str:
        """Build enhanced pre-event analysis prompt with new structure"""
        
        # Get economic context using hybrid approach
        economic_context = self.get_economic_indicator_context(event.get('title', 'Unknown Event'))
        
        prompt = f"""
You are a senior forex market analyst specializing in macroeconomic events. Write for professional forex traders with 3+ years experience. Use clear, insightful, yet concise tone. Focus on actionable insights and risk management.

EVENT DETAILS:
- Title: {event.get('title', 'Unknown Event')}
- Currency: {event.get('currency', 'Unknown')}
- Impact Level: {event.get('impact', 'Medium')}
- Expected: {event.get('expected', 'Not specified')}
- Previous: {event.get('previous', 'Not specified')}
- Time: {event.get('time', 'Not specified')}
- Date: {event.get('date', 'Not specified')}
- Time_to_Event: {market_context.time_to_event} seconds
- Liquidity_Level: {market_context.liquidity_level}

MARKET CONTEXT:
Current Prices: {market_context.current_prices}
Recent Volatility: {market_context.recent_volatility}
Market Sentiment: {market_context.market_sentiment}
Key Technical Levels: {market_context.key_levels}

MARKET POSITIONING:
Retail Sentiment: {market_context.retail_sentiment}
Futures Positioning: {market_context.futures_positioning}
Institutional Flow: {market_context.institutional_flow}

SCENARIO PROBABILITIES:
Higher_than_Expected: {market_context.scenario_probabilities.get('higher', 0.30)}
Lower_than_Expected: {market_context.scenario_probabilities.get('lower', 0.50)}
In_Line: {market_context.scenario_probabilities.get('inline', 0.20)}

ECONOMIC KNOWLEDGE:
{economic_context}

ANALYSIS REQUIREMENTS:
1. Use the exact JSON structure provided below
2. Keep each section under specified word limits
3. Include key numbers, historical examples, and specific reasoning
4. Compare to last 3 similar releases
5. Provide probability-weighted scenarios
6. Focus on actionable insights and risk management
7. Avoid specific trade recommendations

OUTPUT FORMAT:
{{
  "event_summary": {{
    "release": "string (detailed event title with context)",
    "outcome": "string (comprehensive assessment of actual vs expected vs previous with surprise factor analysis)",
    "previous": "string (previous value)",
    "expected": "string (expected value)", 
    "actual": "string (actual value)"
  }},
  "market_reaction": {{
    "price_action": "string (max 150 words - detailed expected price movements with specific pairs, pip ranges, and technical context)",
    "volatility": "string (max 100 words - comprehensive volatility outlook with specific levels and timing)",
    "reason": "string (max 150 words - detailed explanation of market reaction drivers including policy implications and sentiment)"
  }},
  "implications_takeaways": {{
    "economic_context": "string (max 200 words - detailed economic significance with historical context, trend analysis, and sector implications)",
    "policy_implications": "string (max 150 words - comprehensive central bank impact with specific policy expectations and rate implications)",
    "market_positioning": "string (max 150 words - detailed current market sentiment with institutional vs retail positioning)",
    "event_bias": "string (max 100 words - detailed bullish/bearish/neutral assessment with specific reasoning)",
    "sentiment": "string (max 150 words - comprehensive market sentiment shift with risk appetite implications)",
    "risk_level": "string (max 100 words - detailed risk assessment with specific volatility and correlation risks)"
  }},
  "trading_plan": {{
    "best_approach": "string (max 150 words - detailed recommended trading approach with specific strategies and timing)",
    "key_levels": "string (max 150 words - comprehensive support/resistance analysis with specific price levels and zones)",
    "position_sizing": "string (max 100 words - detailed position sizing guidance with risk parameters)",
    "avoid_strategies": "string (max 150 words - comprehensive list of what to avoid with specific reasoning)",
    "next_catalysts": "string (max 150 words - detailed upcoming events with specific dates and expected impact)",
    "support_levels": ["string (specific price levels)"],
    "resistance_levels": ["string (specific price levels)"],
    "best_setup": "string (max 100 words - detailed optimal setup timing with specific entry conditions)",
    "position_sizing_risk": "string (max 100 words - comprehensive risk management guidelines)"
  }},
  "big_picture": {{
    "economic_outlook": "string (max 200 words - detailed economic health implications with growth and inflation outlook)",
    "policy_trajectory": "string (max 150 words - comprehensive central bank policy outlook with rate path expectations)",
    "medium_term_direction": "string (max 150 words - detailed medium-term trends with specific timeframes)",
    "forward_focus": "string (max 150 words - comprehensive forward monitoring with specific events and indicators)",
    "policy_impact": "string (max 150 words - detailed policy implications with specific central bank actions)",
    "risk_assessment": "string (max 100 words - comprehensive overall risk assessment with multiple risk factors)"
  }},
  "confidence_score": 85
}}

ANALYSIS REQUIREMENTS:
1. **ACCURACY FIRST** - Only state specific price levels, pip ranges, or market reactions if you have actual data. Otherwise use conditional language like "typically", "usually", or "expected to"
2. **AVOID REDUNDANCY** - Each section should have unique value. Don't repeat the same points across multiple sections
3. **CURRENT CATALYSTS** - Focus on relevant upcoming events (CPI, central bank meetings, GDP). Avoid outdated references like Brexit unless specifically relevant
4. **CONSOLIDATED SECTIONS** - Merge related concepts. Trading Plan should include key levels, position sizing, and strategy in one cohesive section
5. **MARKET CONTEXT** - Explain why this indicator matters for the currency and central bank policy
6. **HISTORICAL CONTEXT** - Compare to recent releases and typical market reactions
7. **ACTIONABLE INSIGHTS** - Give traders specific things to watch and monitor
8. **PROFESSIONAL LANGUAGE** - Write like a senior forex analyst for institutional clients
9. **VOLATILITY EXPECTATIONS** - Provide realistic volatility outlook with timing
10. **BIG TAKEAWAYS** - Summarize key points for quick trader reference without repetition

Provide analysis that is educational, actionable, and helps traders understand market dynamics while managing risk effectively.
"""
        return prompt
    
    def _build_enhanced_post_event_prompt(self, event: Dict, market_context: MarketContext) -> str:
        """Build the ultimate enhanced post-event analysis prompt combining best practices"""
        
        # Get economic context using hybrid approach
        economic_context = self.get_economic_indicator_context(event.get('title', 'Unknown Event'))
        
        prompt = f"""
You are an experienced Forex strategist providing professional, data-driven market analysis for retail traders. 
Your goal: Deliver clear, insightful analysis that explains cause-and-effect logic, market reactions, and forward-looking scenarios in a structured format. 
Do NOT give explicit trade signals or recommendations. Instead, provide educational insights, scenario-based reasoning, and actionable frameworks for understanding market dynamics.

---

### 📌 Event Details:
Title: {event.get('title', 'Unknown Event')}
Currency: {event.get('currency', 'Unknown')}
Impact Level: {event.get('impact', 'Medium')}
Actual: {event.get('actual', 'Not released')}
Expected: {event.get('expected', 'Not specified')}
Previous: {event.get('previous', 'Not specified')}
Date & Time: {event.get('date', 'Not specified')} {event.get('time', 'Not specified')}

### 📌 Market Context:
Current Prices: {json.dumps(market_context.current_prices, indent=2)}
Recent Volatility: {json.dumps(market_context.recent_volatility, indent=2)}
Market Sentiment: {json.dumps(market_context.market_sentiment, indent=2)}
Key Technical Levels: {json.dumps(market_context.key_levels, indent=2)}

### 📌 Enhanced Market Positioning:
Retail Sentiment: {json.dumps(market_context.retail_sentiment, indent=2)}
Futures Positioning: {json.dumps(market_context.futures_positioning, indent=2)}
Institutional Flow: {json.dumps(market_context.institutional_flow, indent=2)}
Time to Event: {market_context.time_to_event} seconds
Liquidity Level: {market_context.liquidity_level} (1=High, 2=Medium, 3=Low)

### 📌 Cross-Market Context:
Bond Yields: {json.dumps(market_context.bond_yields, indent=2)}
Equity Indices: {json.dumps(market_context.equity_indices, indent=2)}
Commodities: {json.dumps(market_context.commodity_prices, indent=2)}

### 📌 Economic Knowledge:
{economic_context}

### 📌 Historical Context:
Compare to last 3 similar releases and typical market reactions for this type of economic indicator.

### 📌 Analysis Type:
Post-Event Analysis

---

## ✅ OUTPUT REQUIREMENTS:
Provide analysis in **JSON** with the following keys, each containing **detailed, professional paragraphs**:

{{
  "event_summary": {{
    "release": "Detailed event title with comprehensive context and timing",
    "outcome": "Comprehensive assessment of actual vs expected vs previous with detailed surprise factor analysis and market implications",
    "previous": "Previous value from the data",
    "expected": "Expected value from the data",
    "actual": "Actual value from the data"
  }},
  
  "market_reaction": {{
    "price_action": "Detailed actual price movements observed with specific pairs, pip ranges, technical context, and expected continuation patterns (max 150 words)",
    "volatility": "Comprehensive volatility patterns observed with specific levels, timing, and correlation effects (max 100 words)",
    "reason": "Detailed explanation of why the market reacted as it did including policy implications, sentiment drivers, and technical factors (max 150 words)"
  }},
  
  "implications_takeaways": {{
    "economic_context": "Detailed economic significance with historical context, trend analysis, sector implications, and growth/inflation outlook (max 200 words)",
    "policy_implications": "Comprehensive impact on central bank policy expectations with specific rate implications and monetary policy outlook (max 150 words)",
    "market_positioning": "Detailed current market sentiment with institutional vs retail positioning, risk appetite, and flow dynamics (max 150 words)",
    "event_bias": "Detailed bullish/bearish/neutral assessment with specific reasoning and confidence levels (max 100 words)",
    "sentiment": "Comprehensive market sentiment shift with risk appetite implications and forward-looking sentiment outlook (max 150 words)",
    "risk_level": "Detailed risk assessment with specific volatility, correlation, and liquidity risks (max 100 words)"
  }},
  
  "trading_plan": {{
    "best_approach": "Detailed recommended trading approach with specific strategies, timing, and entry/exit considerations (max 150 words)",
    "key_levels": "Comprehensive support and resistance analysis with specific price levels, zones, and breakout potential (max 150 words)",
    "position_sizing": "Detailed position sizing guidance with specific risk parameters and correlation considerations (max 100 words)",
    "avoid_strategies": "Comprehensive list of what trading strategies to avoid with specific reasoning and risk factors (max 150 words)",
    "next_catalysts": "Detailed upcoming events to monitor with specific dates, expected impact, and market focus areas (max 150 words)",
    "support_levels": ["Specific price levels with technical context"],
    "resistance_levels": ["Specific price levels with technical context"],
    "best_setup": "Detailed optimal setup timing with specific entry conditions and monitoring requirements (max 100 words)",
    "position_sizing_risk": "Comprehensive risk management guidelines with specific parameters and monitoring points (max 100 words)"
  }},
  
  "big_picture": {{
    "economic_outlook": "Detailed economic health implications with growth and inflation outlook, sector analysis, and economic cycle positioning (max 200 words)",
    "policy_trajectory": "Comprehensive central bank policy outlook with specific rate path expectations and monetary policy narrative (max 150 words)",
    "medium_term_direction": "Detailed medium-term trend implications with specific timeframes and key drivers (max 150 words)",
    "forward_focus": "Comprehensive forward monitoring with specific events, indicators, and market catalysts to watch (max 150 words)",
    "policy_impact": "Detailed policy implications with specific central bank actions and monetary policy shifts (max 150 words)",
    "risk_assessment": "Comprehensive overall risk assessment with multiple risk factors and scenario analysis (max 100 words)"
  }},
  
  "confidence_score": 85
}}

ANALYSIS REQUIREMENTS:
1. **ACCURACY FIRST** - Only state specific price levels, pip ranges, or market reactions if you have actual data. Otherwise use conditional language like "typically", "usually", or "expected to"
2. **AVOID REDUNDANCY** - Each section should have unique value. Don't repeat the same points across multiple sections
3. **CURRENT CATALYSTS** - Focus on relevant upcoming events (CPI, central bank meetings, GDP). Avoid outdated references like Brexit unless specifically relevant
4. **CONSOLIDATED SECTIONS** - Merge related concepts. Trading Plan should include key levels, position sizing, and strategy in one cohesive section
5. **MARKET CONTEXT** - Explain why this indicator matters for the currency and central bank policy
6. **HISTORICAL CONTEXT** - Compare to recent releases and typical market reactions
7. **ACTIONABLE INSIGHTS** - Give traders specific things to watch and monitor
8. **PROFESSIONAL LANGUAGE** - Write like a senior forex analyst for institutional clients
9. **VOLATILITY EXPECTATIONS** - Provide realistic volatility outlook with timing
10. **BIG TAKEAWAYS** - Summarize key points for quick trader reference without repetition

---

### ✅ Additional Rules:
- Keep each section **under 150 words**, concise but data-driven.
- Always use **actual figures from input** (actual vs expected vs previous).
- Analyze the **surprise factor** and market reaction to the actual result.
- Provide historical comparison where relevant (e.g., last release impact).
- Tone: **Professional, analytical, educational**.
- Use **specific numbers and data points** from the market context provided.
- Consider **market positioning data** (retail sentiment, futures positioning, institutional flow).
- Factor in **time to event** and **liquidity conditions**.
- Focus on **forward-looking implications** and next moves.
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
        """Generate meaningful fallback analysis when GPT is unavailable"""
        logger.warning("Using enhanced fallback analysis")
        print(f"🚨🚨🚨 ENHANCED FALLBACK ANALYSIS USED - EASY TO FIND 🚨🚨🚨")
        print(f"🚨 Event: {event.get('title', 'Unknown')}")
        print(f"🚨 Analysis Type: {analysis_type}")
        print(f"🚨🚨🚨 END FALLBACK MESSAGE 🚨🚨🚨")
        
        # Get specific economic indicator context using hybrid approach
        event_title = event.get('title', 'Unknown Event')
        economic_context = self.get_economic_indicator_context(event_title)
        
        # Determine if this is pre-event or post-event
        has_actual = 'actual' in event and event.get('actual') and event.get('actual') != 'Not released'
        
        # Create meaningful analysis based on actual data
        currency = event.get('currency', 'Unknown')
        event_title = event.get('title', 'Unknown Event')
        
        # Analyze the actual data vs expected vs previous
        previous = event.get('previous', 'N/A')
        expected = event.get('expected', 'N/A')
        actual = event.get('actual', 'N/A')
        
        # Determine the outcome based on actual data
        outcome = self._analyze_data_outcome(previous, expected, actual, event_title)
        
        # Generate currency-specific analysis
        currency_analysis = self._generate_universal_analysis(currency, event_title, outcome)
        
        return GPTAnalysisResult(
            event_summary={
                "release": event_title,
                "outcome": outcome,
                "previous": previous,
                "expected": expected,
                "actual": actual
            },
            market_reaction={
                "price_action": currency_analysis['price_action'],
                "volatility": currency_analysis['volatility'],
                "reason": currency_analysis['reason']
            },
            implications_takeaways={
                "economic_context": f"{economic_context.strip()} {currency_analysis['economic_context']}",
                "policy_implications": currency_analysis['policy_implications'],
                "market_positioning": currency_analysis['market_positioning'],
                "event_bias": currency_analysis['event_bias'],
                "sentiment": currency_analysis['sentiment'],
                "risk_level": currency_analysis['risk_level']
            },
            trading_plan={
                "best_approach": currency_analysis['best_approach'],
                "key_levels": currency_analysis['key_levels'],
                "position_sizing": currency_analysis['position_sizing'],
                "avoid_strategies": currency_analysis['avoid_strategies'],
                "next_catalysts": currency_analysis['next_catalysts'],
                "support_levels": currency_analysis['support_levels'],
                "resistance_levels": currency_analysis['resistance_levels'],
                "best_setup": "Range trading with breakout potential",
                "position_sizing_risk": "Conservative position sizing recommended"
            },
            big_picture={
                "economic_outlook": currency_analysis['economic_outlook'],
                "policy_trajectory": currency_analysis['policy_trajectory'],
                "medium_term_direction": currency_analysis['medium_term_direction'],
                "forward_focus": currency_analysis['forward_focus'],
                "policy_impact": currency_analysis['policy_implications'],
                "risk_assessment": currency_analysis['risk_level']
            },
            confidence_score=currency_analysis['confidence_score'],
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type=analysis_type,
            model_used="enhanced_fallback",
            cost_estimate=0.0
        )
    
    def _analyze_data_outcome(self, previous: str, expected: str, actual: str, event_title: str) -> str:
        """Analyze the actual data outcome vs expected vs previous"""
        try:
            # Convert to float for comparison (handle percentage signs)
            prev_val = float(str(previous).replace('%', '').replace(',', ''))
            exp_val = float(str(expected).replace('%', '').replace(',', ''))
            act_val = float(str(actual).replace('%', '').replace(',', ''))
            
            # Determine the outcome
            if abs(act_val - exp_val) < 0.01:  # Within 0.01 tolerance
                if abs(act_val - prev_val) < 0.01:
                    return f"Data came in exactly as expected at {actual}, unchanged from previous. This confirms market expectations and is neutral for the currency."
                else:
                    return f"Data came in as expected at {actual} but changed from previous {previous}. This meets expectations but shows economic change."
            elif act_val > exp_val:
                return f"Data came in worse than expected: {actual} vs {expected} expected. This is bearish for the currency as it suggests economic weakness."
            else:
                return f"Data came in better than expected: {actual} vs {expected} expected. This is bullish for the currency as it suggests economic strength."
                
        except (ValueError, TypeError):
            # If we can't parse the numbers, provide generic analysis
            if actual == expected:
                return f"Data came in as expected at {actual}. This confirms market expectations."
            else:
                return f"Data came in at {actual} vs {expected} expected. Market reaction will depend on the surprise factor."
    
    def _generate_universal_analysis(self, currency: str, event_title: str, outcome: str) -> Dict:
        """Generate universal analysis for ANY economic event, currency, or asset"""
        
        # Comprehensive central bank mapping for all major and emerging market currencies
        central_bank_map = {
            # Major Currencies
            'USD': 'Federal Reserve',
            'GBP': 'Bank of England', 
            'EUR': 'European Central Bank',
            'JPY': 'Bank of Japan',
            'AUD': 'Reserve Bank of Australia',
            'CAD': 'Bank of Canada',
            'CHF': 'Swiss National Bank',
            'NZD': 'Reserve Bank of New Zealand',
            
            # Emerging Market Currencies
            'CNY': 'People\'s Bank of China',
            'INR': 'Reserve Bank of India',
            'BRL': 'Central Bank of Brazil',
            'RUB': 'Central Bank of Russia',
            'ZAR': 'South African Reserve Bank',
            'MXN': 'Bank of Mexico',
            'TRY': 'Central Bank of Turkey',
            'KRW': 'Bank of Korea',
            'SGD': 'Monetary Authority of Singapore',
            'HKD': 'Hong Kong Monetary Authority',
            'SEK': 'Sveriges Riksbank',
            'NOK': 'Norges Bank',
            'DKK': 'Danmarks Nationalbank',
            'PLN': 'National Bank of Poland',
            'CZK': 'Czech National Bank',
            'HUF': 'Hungarian National Bank',
            'RON': 'National Bank of Romania',
            'BGN': 'Bulgarian National Bank',
            'HRK': 'Croatian National Bank',
            'ILS': 'Bank of Israel',
            'EGP': 'Central Bank of Egypt',
            'NGN': 'Central Bank of Nigeria',
            'KES': 'Central Bank of Kenya',
            'GHS': 'Bank of Ghana',
            'UGX': 'Bank of Uganda',
            'TZS': 'Bank of Tanzania',
            'ZMW': 'Bank of Zambia',
            'MWK': 'Reserve Bank of Malawi',
            'BWP': 'Bank of Botswana',
            'NAD': 'Bank of Namibia',
            'MUR': 'Bank of Mauritius',
            'SCR': 'Central Bank of Seychelles',
            'MAD': 'Bank Al-Maghrib',
            'TND': 'Central Bank of Tunisia',
            'DZD': 'Bank of Algeria',
            'LYD': 'Central Bank of Libya',
            'SDG': 'Central Bank of Sudan',
            'ETB': 'National Bank of Ethiopia',
            'SOS': 'Central Bank of Somalia',
            'DJF': 'Central Bank of Djibouti',
            'KMF': 'Central Bank of Comoros',
            'MGA': 'Central Bank of Madagascar',
            'XOF': 'Central Bank of West African States',
            'XAF': 'Bank of Central African States',
            'XPF': 'Institut d\'émission d\'outre-mer',
            'CLP': 'Central Bank of Chile',
            'COP': 'Bank of the Republic',
            'PEN': 'Central Reserve Bank of Peru',
            'UYU': 'Central Bank of Uruguay',
            'PYG': 'Central Bank of Paraguay',
            'BOB': 'Central Bank of Bolivia',
            'ARS': 'Central Bank of Argentina',
            'VES': 'Central Bank of Venezuela',
            'GTQ': 'Bank of Guatemala',
            'HNL': 'Central Bank of Honduras',
            'NIO': 'Central Bank of Nicaragua',
            'CRC': 'Central Bank of Costa Rica',
            'PAB': 'National Bank of Panama',
            'DOP': 'Central Bank of Dominican Republic',
            'JMD': 'Bank of Jamaica',
            'TTD': 'Central Bank of Trinidad and Tobago',
            'BBD': 'Central Bank of Barbados',
            'XCD': 'Eastern Caribbean Central Bank',
            'THB': 'Bank of Thailand',
            'MYR': 'Bank Negara Malaysia',
            'IDR': 'Bank Indonesia',
            'PHP': 'Bangko Sentral ng Pilipinas',
            'VND': 'State Bank of Vietnam',
            'BDT': 'Bangladesh Bank',
            'PKR': 'State Bank of Pakistan',
            'LKR': 'Central Bank of Sri Lanka',
            'NPR': 'Nepal Rastra Bank',
            'MMK': 'Central Bank of Myanmar',
            'KHR': 'National Bank of Cambodia',
            'LAK': 'Bank of the Lao PDR',
            'MNT': 'Bank of Mongolia',
            'KZT': 'National Bank of Kazakhstan',
            'UZS': 'Central Bank of Uzbekistan',
            'TJS': 'National Bank of Tajikistan',
            'KGS': 'National Bank of Kyrgyz Republic',
            'TMT': 'Central Bank of Turkmenistan',
            'AZN': 'Central Bank of Azerbaijan',
            'GEL': 'National Bank of Georgia',
            'AMD': 'Central Bank of Armenia',
            'BYN': 'National Bank of Belarus',
            'MDL': 'National Bank of Moldova',
            'UAH': 'National Bank of Ukraine',
            'RSD': 'National Bank of Serbia',
            'BAM': 'Central Bank of Bosnia and Herzegovina',
            'ALL': 'Bank of Albania',
            'MKD': 'National Bank of North Macedonia',
            'MNT': 'Bank of Mongolia',
            'KHR': 'National Bank of Cambodia',
            'LAK': 'Bank of the Lao PDR',
            'VND': 'State Bank of Vietnam',
            'BDT': 'Bangladesh Bank',
            'PKR': 'State Bank of Pakistan',
            'LKR': 'Central Bank of Sri Lanka',
            'NPR': 'Nepal Rastra Bank',
            'MMK': 'Central Bank of Myanmar',
            'KHR': 'National Bank of Cambodia',
            'LAK': 'Bank of the Lao PDR',
            'MNT': 'Bank of Mongolia',
            'KZT': 'National Bank of Kazakhstan',
            'UZS': 'Central Bank of Uzbekistan',
            'TJS': 'National Bank of Tajikistan',
            'KGS': 'National Bank of Kyrgyz Republic',
            'TMT': 'Central Bank of Turkmenistan',
            'AZN': 'Central Bank of Azerbaijan',
            'GEL': 'National Bank of Georgia',
            'AMD': 'Central Bank of Armenia',
            'BYN': 'National Bank of Belarus',
            'MDL': 'National Bank of Moldova',
            'UAH': 'National Bank of Ukraine',
            'RSD': 'National Bank of Serbia',
            'BAM': 'Central Bank of Bosnia and Herzegovina',
            'ALL': 'Bank of Albania',
            'MKD': 'National Bank of North Macedonia'
        }
        
        central_bank = central_bank_map.get(currency, 'Central Bank')
        
        # Comprehensive currency pair mapping for all currencies
        currency_pairs_map = {
            'USD': f"USD/JPY, EUR/USD, GBP/USD, USD/CHF, USD/CAD, AUD/USD, USD/CNY, USD/INR, USD/BRL, USD/RUB, USD/ZAR, USD/MXN, USD/TRY, USD/KRW, USD/SGD, USD/HKD, USD/SEK, USD/NOK, USD/DKK, USD/PLN, USD/CZK, USD/HUF, USD/RON, USD/BGN, USD/HRK, USD/ILS, USD/EGP, USD/NGN, USD/KES, USD/GHS, USD/UGX, USD/TZS, USD/ZMW, USD/MWK, USD/BWP, USD/NAD, USD/MUR, USD/SCR, USD/MAD, USD/TND, USD/DZD, USD/LYD, USD/SDG, USD/ETB, USD/SOS, USD/DJF, USD/KMF, USD/MGA, USD/XOF, USD/XAF, USD/XPF, USD/CLP, USD/COP, USD/PEN, USD/UYU, USD/PYG, USD/BOB, USD/ARS, USD/VES, USD/GTQ, USD/HNL, USD/NIO, USD/CRC, USD/PAB, USD/DOP, USD/JMD, USD/TTD, USD/BBD, USD/XCD, USD/THB, USD/MYR, USD/IDR, USD/PHP, USD/VND, USD/BDT, USD/PKR, USD/LKR, USD/NPR, USD/MMK, USD/KHR, USD/LAK, USD/MNT, USD/KZT, USD/UZS, USD/TJS, USD/KGS, USD/TMT, USD/AZN, USD/GEL, USD/AMD, USD/BYN, USD/MDL, USD/UAH, USD/RSD, USD/BAM, USD/ALL, USD/MKD",
            'GBP': f"GBP/USD, EUR/GBP, GBP/JPY, GBP/CHF, GBP/AUD, GBP/CAD, GBP/NZD, GBP/CNY, GBP/INR, GBP/BRL, GBP/RUB, GBP/ZAR, GBP/MXN, GBP/TRY, GBP/KRW, GBP/SGD, GBP/HKD, GBP/SEK, GBP/NOK, GBP/DKK, GBP/PLN, GBP/CZK, GBP/HUF, GBP/RON, GBP/BGN, GBP/HRK, GBP/ILS, GBP/EGP, GBP/NGN, GBP/KES, GBP/GHS, GBP/UGX, GBP/TZS, GBP/ZMW, GBP/MWK, GBP/BWP, GBP/NAD, GBP/MUR, GBP/SCR, GBP/MAD, GBP/TND, GBP/DZD, GBP/LYD, GBP/SDG, GBP/ETB, GBP/SOS, GBP/DJF, GBP/KMF, GBP/MGA, GBP/XOF, GBP/XAF, GBP/XPF, GBP/CLP, GBP/COP, GBP/PEN, GBP/UYU, GBP/PYG, GBP/BOB, GBP/ARS, GBP/VES, GBP/GTQ, GBP/HNL, GBP/NIO, GBP/CRC, GBP/PAB, GBP/DOP, GBP/JMD, GBP/TTD, GBP/BBD, GBP/XCD, GBP/THB, GBP/MYR, GBP/IDR, GBP/PHP, GBP/VND, GBP/BDT, GBP/PKR, GBP/LKR, GBP/NPR, GBP/MMK, GBP/KHR, GBP/LAK, GBP/MNT, GBP/KZT, GBP/UZS, GBP/TJS, GBP/KGS, GBP/TMT, GBP/AZN, GBP/GEL, GBP/AMD, GBP/BYN, GBP/MDL, GBP/UAH, GBP/RSD, GBP/BAM, GBP/ALL, GBP/MKD",
            'EUR': f"EUR/USD, EUR/GBP, EUR/JPY, EUR/CHF, EUR/AUD, EUR/CAD, EUR/NZD, EUR/CNY, EUR/INR, EUR/BRL, EUR/RUB, EUR/ZAR, EUR/MXN, EUR/TRY, EUR/KRW, EUR/SGD, EUR/HKD, EUR/SEK, EUR/NOK, EUR/DKK, EUR/PLN, EUR/CZK, EUR/HUF, EUR/RON, EUR/BGN, EUR/HRK, EUR/ILS, EUR/EGP, EUR/NGN, EUR/KES, EUR/GHS, EUR/UGX, EUR/TZS, EUR/ZMW, EUR/MWK, EUR/BWP, EUR/NAD, EUR/MUR, EUR/SCR, EUR/MAD, EUR/TND, EUR/DZD, EUR/LYD, EUR/SDG, EUR/ETB, EUR/SOS, EUR/DJF, EUR/KMF, EUR/MGA, EUR/XOF, EUR/XAF, EUR/XPF, EUR/CLP, EUR/COP, EUR/PEN, EUR/UYU, EUR/PYG, EUR/BOB, EUR/ARS, EUR/VES, EUR/GTQ, EUR/HNL, EUR/NIO, EUR/CRC, EUR/PAB, EUR/DOP, EUR/JMD, EUR/TTD, EUR/BBD, EUR/XCD, EUR/THB, EUR/MYR, EUR/IDR, EUR/PHP, EUR/VND, EUR/BDT, EUR/PKR, EUR/LKR, EUR/NPR, EUR/MMK, EUR/KHR, EUR/LAK, EUR/MNT, EUR/KZT, EUR/UZS, EUR/TJS, EUR/KGS, EUR/TMT, EUR/AZN, EUR/GEL, EUR/AMD, EUR/BYN, EUR/MDL, EUR/UAH, EUR/RSD, EUR/BAM, EUR/ALL, EUR/MKD",
            'JPY': f"USD/JPY, EUR/JPY, GBP/JPY, AUD/JPY, CAD/JPY, CHF/JPY, NZD/JPY, CNY/JPY, INR/JPY, BRL/JPY, RUB/JPY, ZAR/JPY, MXN/JPY, TRY/JPY, KRW/JPY, SGD/JPY, HKD/JPY, SEK/JPY, NOK/JPY, DKK/JPY, PLN/JPY, CZK/JPY, HUF/JPY, RON/JPY, BGN/JPY, HRK/JPY, ILS/JPY, EGP/JPY, NGN/JPY, KES/JPY, GHS/JPY, UGX/JPY, TZS/JPY, ZMW/JPY, MWK/JPY, BWP/JPY, NAD/JPY, MUR/JPY, SCR/JPY, MAD/JPY, TND/JPY, DZD/JPY, LYD/JPY, SDG/JPY, ETB/JPY, SOS/JPY, DJF/JPY, KMF/JPY, MGA/JPY, XOF/JPY, XAF/JPY, XPF/JPY, CLP/JPY, COP/JPY, PEN/JPY, UYU/JPY, PYG/JPY, BOB/JPY, ARS/JPY, VES/JPY, GTQ/JPY, HNL/JPY, NIO/JPY, CRC/JPY, PAB/JPY, DOP/JPY, JMD/JPY, TTD/JPY, BBD/JPY, XCD/JPY, THB/JPY, MYR/JPY, IDR/JPY, PHP/JPY, VND/JPY, BDT/JPY, PKR/JPY, LKR/JPY, NPR/JPY, MMK/JPY, KHR/JPY, LAK/JPY, MNT/JPY, KZT/JPY, UZS/JPY, TJS/JPY, KGS/JPY, TMT/JPY, AZN/JPY, GEL/JPY, AMD/JPY, BYN/JPY, MDL/JPY, UAH/JPY, RSD/JPY, BAM/JPY, ALL/JPY, MKD/JPY"
        }
        
        # Get primary pairs for the currency
        primary_pairs = currency_pairs_map.get(currency, f"{currency}/USD, EUR/{currency}, {currency}/JPY")
        
        # Determine impact based on outcome with more nuanced analysis
        if 'bullish' in outcome.lower() or 'better than expected' in outcome.lower() or 'stronger' in outcome.lower():
            bias = 'Bullish'
            sentiment = 'Positive'
            impact = 'Medium'
            volatility_level = 'Medium'
            directional_bias = f'Bullish for {currency}'
        elif 'bearish' in outcome.lower() or 'worse than expected' in outcome.lower() or 'weaker' in outcome.lower():
            bias = 'Bearish'
            sentiment = 'Negative'
            impact = 'Medium'
            volatility_level = 'Medium'
            directional_bias = f'Bearish for {currency}'
        else:
            bias = 'Neutral'
            sentiment = 'Neutral'
            impact = 'Low'
            volatility_level = 'Low'
            directional_bias = f'Neutral for {currency}'
        
        # Universal economic analysis for ANY event type
        economic_context = f"This {event_title} data provides critical insights into {currency} economic health, growth prospects, and monetary policy implications. The current reading indicates {bias.lower()} economic conditions, which affects {central_bank} policy expectations, currency valuation, and capital flow dynamics. Economic indicators directly influence rate expectations and currency strength."
        policy_implications = f"This data significantly influences {central_bank} policy expectations and interest rate outlook. {bias} economic conditions suggest {('hawkish' if bias == 'Bullish' else 'dovish' if bias == 'Bearish' else 'neutral')} policy bias, affecting the currency's yield appeal and capital flows. {central_bank} considers this data when setting monetary policy."
        price_action = f"Economic data releases typically cause movement in {currency} pairs, with {primary_pairs} expected to show {volatility_level.lower()} volatility. The {bias.lower()} reading suggests potential {bias.lower()} bias for {currency}, with trading opportunities around key technical levels and support/resistance zones."
        
        # Dynamic volatility assessment based on currency and event type
        if currency in ['USD', 'EUR', 'GBP', 'JPY']:
            base_pip_range = "10-15"
            spike_pip_range = "20-25"
        elif currency in ['AUD', 'CAD', 'CHF', 'NZD']:
            base_pip_range = "8-12"
            spike_pip_range = "15-20"
        elif currency in ['CNY', 'INR', 'BRL', 'RUB', 'ZAR', 'MXN', 'TRY', 'KRW']:
            base_pip_range = "15-25"
            spike_pip_range = "30-40"
        else:
            base_pip_range = "10-20"
            spike_pip_range = "20-30"
        
        return {
            'price_action': price_action,
            'volatility': f"{volatility_level} volatility typically expected around this type of release, with {currency} pairs usually showing moderate movement unless there's a significant surprise factor. Expected {base_pip_range} pip movement range for {currency} pairs, with brief spikes to {spike_pip_range} pips on data surprises",
            'reason': f"Market reaction driven by {central_bank} policy expectations and economic implications, with technical levels providing additional context for price action",
            'economic_context': economic_context,
            'policy_implications': policy_implications,
            'market_positioning': f"Current market positioning shows {sentiment.lower()} sentiment toward {currency}, with institutional flows likely to be influenced by the {bias.lower()} data outcome and {central_bank} policy implications",
            'event_bias': f"{bias} - {('Strong economic performance suggests currency strength' if bias == 'Bullish' else 'Economic weakness suggests currency pressure' if bias == 'Bearish' else 'Market remains neutral, awaiting new data. {currency} likely to trade within established range until new data arrives. Tactical approach: Buy near support levels, sell near resistance, with tight stops for quick exits')}",
            'sentiment': f"Market sentiment: {sentiment} toward {currency} based on economic data and policy implications",
            'risk_level': f"{impact} risk - {volatility_level.lower()} volatility expected with potential correlation risks across {currency} pairs",
            'best_approach': f"Range trading with breakout potential based on {bias.lower()} data outcome, focusing on key technical levels and {central_bank} policy implications. Practical approach: Buy near support levels, sell near resistance, with breakout trades on significant data surprises. Conservative position sizing recommended due to {volatility_level.lower()} volatility expectations",
            'avoid_strategies': f"Avoid aggressive positioning before data release and during high volatility periods, particularly around {central_bank} policy-sensitive events",
            'key_levels': f"Monitor key support and resistance levels around current price action, with broader context levels for short-term and wider range trading. Include immediate levels (primary) and slightly broader zones (secondary) for comprehensive analysis. Focus on breakout potential at key levels with secondary support/resistance zones for wider context",
            'next_catalysts': f"{central_bank} meetings and key economic releases",
            'economic_outlook': f"The data provides critical insights into {currency} economic health, growth prospects, and monetary policy trajectory with {bias.lower()} implications",
            'policy_trajectory': f"{central_bank} policy trajectory will be influenced by the {bias.lower()} data outcome, affecting rate expectations and currency valuation",
            'medium_term_direction': f"Range-bound outlook unless new catalysts emerge. {currency} likely to maintain current range with potential for gradual shifts based on upcoming data and policy developments. {primary_pairs} expected to remain range-bound with {base_pip_range} pip movements, with breakout potential on significant data surprises. Traders should position for range-bound trading with breakout potential on significant data surprises, focusing on key support/resistance levels for entry and exit decisions",
            'forward_focus': f"Monitor for follow-up data releases, {central_bank} communications, and policy shifts that could impact {currency} valuation",
            'policy_impact': f"Significant influence on {central_bank} policy expectations with potential {('hawkish' if bias == 'Bullish' else 'dovish' if bias == 'Bearish' else 'neutral')} policy bias",
            'risk_assessment': f"{impact} risk level with {volatility_level.lower()} volatility expected and potential correlation risks across {currency} pairs",
            'support_levels': [f"Key support levels for {currency} pairs around current consolidation zones"],
            'resistance_levels': [f"Key resistance levels for {currency} pairs with breakout potential on {bias.lower()} confirmation"],
            'best_setup': f"Range trading with breakout potential based on {bias.lower()} data outcome",
            'position_sizing_risk': f"Conservative position sizing recommended due to {volatility_level.lower()} volatility expectations. Suggest 0.5-1% of account per trade for low volatility, 1-2% for moderate volatility, with tighter stops around key support/resistance levels",
            'confidence_score': 75.0
        }
    
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

# Global instance - create safely
try:
    gpt_ai_analyzer = GPTAIAnalyzer()
except Exception as e:
    print(f"🔍 Error creating GPT analyzer instance: {e}")
    # Create a minimal instance that will use fallback
    gpt_ai_analyzer = None
