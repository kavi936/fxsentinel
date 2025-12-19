#!/usr/bin/env python3
"""
GPT AI Analysis Service for FXSentinel
Implements comprehensive analysis framework with real GPT integration and data validation
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
import re

# Import our validation and market data services
from services.data_validator import economic_data_validator
from services.live_market_data import live_market_data_service

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
    recent_volatility: Dict[str, str]
    market_sentiment: Dict[str, str]
    key_levels: Dict[str, Dict[str, List[float]]]
    economic_calendar: List[Dict]
    bond_yields: Dict[str, float]
    equity_indices: Dict[str, float]
    commodity_prices: Dict[str, float]
    # New positioning data
    retail_sentiment: Dict[str, float] = None  # 0.0 to 1.0 (0% to 100% long)
    futures_positioning: Dict[str, int] = None  # Net long/short contracts
    institutional_flow: Dict[str, float] = None  # Net buying/selling in millions
    time_to_event: int = 3600  # seconds until event
    liquidity_level: int = 2  # 1=High, 2=Medium, 3=Low
    scenario_probabilities: Dict[str, float] = None  # Higher, Lower, In-line probabilities
    
    def __post_init__(self):
        # Set default values if None
        if self.retail_sentiment is None:
            self.retail_sentiment = {
                'EUR/USD': 0.65, 'USD/JPY': 0.35, 'GBP/USD': 0.50,
                'USD/CHF': 0.70, 'AUD/USD': 0.40, 'USD/CAD': 0.55
            }
        if self.futures_positioning is None:
            self.futures_positioning = {
                'EUR/USD': 15000, 'USD/JPY': -8000, 'GBP/USD': 5000,
                'USD/CHF': 12000, 'AUD/USD': -3000, 'USD/CAD': 2000
            }
        if self.institutional_flow is None:
            self.institutional_flow = {
                'EUR/USD': 25.5, 'USD/JPY': -15.2, 'GBP/USD': 8.7,
                'USD/CHF': 18.3, 'AUD/USD': -12.1, 'USD/CAD': 5.4
            }
        if self.scenario_probabilities is None:
            self.scenario_probabilities = {
                'higher': 0.30, 'lower': 0.50, 'inline': 0.20
            }

@dataclass
class GPTAnalysisResult:
    """Enhanced GPT analysis result with quick-scan elements and comprehensive analysis"""
    
    # Quick-scan elements (NEW)
    headline: str
    key_takeaway: str
    forward_scenarios: Dict[str, Any]
    
    # Comprehensive analysis (EXISTING)
    event_summary: Dict[str, Any]
    market_reaction: Dict[str, Any]
    implications_takeaways: Dict[str, Any]
    trading_plan: Dict[str, Any]
    big_picture: Dict[str, Any]
    
    # Enhanced positioning context (NEW)
    positioning_context: Dict[str, Any]
    next_catalysts: List[str]
    
    # Meta data
    confidence_score: float
    analysis_timestamp: str
    event_id: str
    analysis_type: str
    model_used: str
    cost_estimate: float
    cache_hit: bool = False
    definition_source: str = "gpt"
    
    # Data quality information
    data_quality: str = "unknown"
    validation_status: str = "unknown"
    market_data_source: str = "unknown"

class GPTAIAnalyzer:
    """Enhanced GPT AI analyzer with data validation and live market data"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("✅ GPT AI Analyzer initialized with OpenAI API")
            except Exception as e:
                logger.error(f"❌ Error initializing OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("⚠️ No OpenAI API key found - will use fallback analysis")
        
        # Rate limiting
        self.api_calls_this_hour = 0
        self.max_calls_per_hour = 50  # Conservative limit
        self.last_hour_reset = datetime.now()
        
        # Cost tracking
        self.total_cost = 0.0
        self.cost_estimates = {
            'gpt-4-turbo-preview': 0.03,  # $0.03 per 1K tokens
            'gpt-3.5-turbo': 0.002,       # $0.002 per 1K tokens
        }
        
        # Cache setup
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
                self.redis_client.ping()
                logger.info("✅ Redis cache initialized")
            except:
                self.redis_client = None
                logger.warning("⚠️ Redis not available, using in-memory cache")
        else:
            self.redis_client = None
            logger.warning("⚠️ Redis not available, using in-memory cache")
        
        # In-memory cache fallback
        self.memory_cache = {}
        self.cache_timestamps = {}
        
        # Economic indicators cache
        self.economic_indicators_cache = {}
        # Note: _load_economic_indicators_cache method removed - cache will be populated on demand
    
    def analyze_macro_event(self, event: Dict, market_context: MarketContext, 
                          analysis_type: str = "pre_event") -> GPTAnalysisResult:
        """
        Generate comprehensive GPT analysis for macro events with data validation
        
        Args:
            event: Economic event data (will be validated)
            market_context: Enhanced market context with positioning data
            analysis_type: "pre_event" or "post_event"
        """
        try:
            # Step 1: Validate event data
            logger.info(f"🔍 Validating event data: {event.get('title', 'Unknown')}")
            is_valid, validated_event, validation_errors = economic_data_validator.validate_event_data(event)
            
            if not is_valid:
                logger.warning(f"❌ Event data validation failed: {validation_errors}")
                return self._get_validation_failed_analysis(event, validation_errors, analysis_type)
            
            logger.info(f"✅ Event data validation passed: {validated_event.get('title', 'Unknown')}")
            
            # Step 2: Get live market data
            logger.info("🔄 Fetching live market data from TradingView")
            live_market_data = live_market_data_service.get_live_market_data()
            
            # Step 3: Create enhanced market context with live data
            enhanced_market_context = self._create_enhanced_market_context(market_context, live_market_data)
            
            # Step 4: Check cache
            cache_key = self._generate_cache_key(validated_event, analysis_type)
            cached_result = self._get_cached_analysis(cache_key)
            
            if cached_result:
                logger.info(f"✅ Cache hit for event {validated_event.get('id', 'unknown')}")
                cached_result.cache_hit = True
                cached_result.data_quality = "cached"
                cached_result.market_data_source = live_market_data.get('data_source', 'unknown')
                return cached_result
            
            # Step 5: Rate limiting check
            if not self._check_rate_limit():
                logger.warning("⚠️ Rate limit reached, using fallback analysis")
                return self._get_fallback_analysis(validated_event, analysis_type)
            
            # Step 6: Determine GPT model
            model = self._select_model(validated_event)
            
            # Step 7: Generate analysis with validated data and live market context
            analysis_result = self._generate_enhanced_gpt_analysis(
                validated_event, enhanced_market_context, analysis_type, model
            )
            
            # Step 8: Add data quality information
            analysis_result.data_quality = "validated"
            analysis_result.validation_status = "passed"
            analysis_result.market_data_source = live_market_data.get('data_source', 'unknown')
            
            # Step 9: Cache the result
            self._cache_analysis(cache_key, analysis_result)
            
            # Step 10: Update rate limiting
            self.api_calls_this_hour += 1
            
            logger.info(f"✅ Enhanced GPT analysis generated using {model}, cost: ${analysis_result.cost_estimate:.4f}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced GPT analysis: {e}")
            return self._get_error_fallback(event, analysis_type)
    
    def _create_enhanced_market_context(self, original_context: MarketContext, live_data: Dict) -> MarketContext:
        """Create enhanced market context with live TradingView data"""
        try:
            # Use live data when available, fallback to original context
            current_prices = live_data.get('current_prices', original_context.current_prices)
            recent_volatility = live_data.get('recent_volatility', original_context.recent_volatility)
            market_sentiment = live_data.get('market_sentiment', original_context.market_sentiment)
            key_levels = live_data.get('key_levels', original_context.key_levels)
            
            # Use live positioning data
            retail_sentiment = live_data.get('retail_sentiment', original_context.retail_sentiment)
            futures_positioning = live_data.get('futures_positioning', original_context.futures_positioning)
            institutional_flow = live_data.get('institutional_flow', original_context.institutional_flow)
            
            # Use live cross-market data
            bond_yields = live_data.get('bond_yields', original_context.bond_yields)
            equity_indices = live_data.get('equity_indices', original_context.equity_indices)
            commodity_prices = live_data.get('commodity_prices', original_context.commodity_prices)
            
            return MarketContext(
                current_prices=current_prices,
                recent_volatility=recent_volatility,
                market_sentiment=market_sentiment,
                key_levels=key_levels,
                economic_calendar=original_context.economic_calendar,
                bond_yields=bond_yields,
                equity_indices=equity_indices,
                commodity_prices=commodity_prices,
                retail_sentiment=retail_sentiment,
                futures_positioning=futures_positioning,
                institutional_flow=institutional_flow,
                time_to_event=original_context.time_to_event,
                liquidity_level=original_context.liquidity_level,
                scenario_probabilities=original_context.scenario_probabilities
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating enhanced market context: {e}")
            return original_context
    
    def _get_validation_failed_analysis(self, event: Dict, validation_errors: List[str], analysis_type: str) -> GPTAnalysisResult:
        """Generate analysis when event data validation fails"""
        logger.warning(f"❌ Using validation failed analysis for: {event.get('title', 'Unknown')}")
        
        return GPTAnalysisResult(
            headline=f"⚠️ Data Quality Issue - {event.get('title', 'Unknown Event')}",
            key_takeaway="Event data validation failed - analysis may be unreliable due to data quality issues.",
            forward_scenarios={
                "bullish": "❌ Cannot provide reliable scenarios due to data validation issues",
                "bearish": "❌ Cannot provide reliable scenarios due to data validation issues",
                "neutral": "❌ Cannot provide reliable scenarios due to data validation issues"
            },
            event_summary={
                "release": event.get('title', 'Unknown Event'),
                "outcome": "Data validation failed - event data quality issues detected",
                "previous": "Data unavailable",
                "expected": "Data unavailable",
                "actual": "Data unavailable"
            },
            market_reaction={
                "price_action": "Cannot provide reliable market reaction analysis due to data quality issues",
                "volatility": "Unknown",
                "reason": "Event data validation failed"
            },
            implications_takeaways={
                "economic_context": "Cannot provide reliable economic context due to data quality issues",
                "policy_implications": "Cannot provide reliable policy implications due to data quality issues",
                "market_bias": "Unknown",
                "risk_level": "High - data quality issues"
            },
            trading_plan={
                "best_approach": "Avoid trading based on this analysis due to data quality issues",
                "avoid_strategies": "All strategies - data quality issues detected",
                "key_levels": "Cannot provide reliable levels due to data quality issues",
                "position_sizing": "Not recommended due to data quality issues",
                "next_catalysts": "Focus on upcoming events with validated data"
            },
            big_picture={
                "economic_outlook": "Cannot provide reliable outlook due to data quality issues",
                "medium_term_direction": "Unknown",
                "policy_trajectory": "Cannot provide reliable trajectory due to data quality issues",
                "forward_focus": "Focus on events with validated data"
            },
            positioning_context={
                "retail_sentiment": "Unknown due to data quality issues",
                "institutional_flow": "Unknown due to data quality issues",
                "futures_positioning": "Unknown due to data quality issues",
                "market_bias": "Unknown due to data quality issues"
            },
            next_catalysts=[
                "Focus on upcoming events with validated data",
                "Monitor for data quality improvements",
                "Consider alternative data sources"
            ],
            confidence_score=10.0,  # Very low confidence due to data issues
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type=analysis_type,
            model_used="validation_failed",
            cost_estimate=0.0,
            data_quality="failed_validation",
            validation_status="failed",
            market_data_source="unknown"
        )
    
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
    
    def _get_fallback_analysis(self, event: Dict, analysis_type: str = "pre_event") -> GPTAnalysisResult:
        """Enhanced fallback analysis with specific, actionable content"""
        
        # Extract key data points
        event_title = event.get('title', 'Unknown Event')
        currency = event.get('currency', 'Unknown')
        previous = event.get('previous', 'N/A')
        expected = event.get('expected', 'N/A')
        actual = event.get('actual', 'N/A')
        
        # Determine if this is pre-event or post-event
        has_actual_data = actual not in ['N/A', 'TBD', '', None, '--', 'n/a', 'tbd']
        is_post_event = has_actual_data
        
        # Check if this is a qualitative event (speech, statement, etc.)
        if self._is_qualitative_event(event_title):
            return self._get_qualitative_event_fallback_analysis(event, is_post_event)
        
        # Generate specific analysis based on quantitative event type
        if 'non-farm' in event_title.lower() or 'nfp' in event_title.lower():
            return self._get_nfp_fallback_analysis(event, is_post_event)
        elif 'cpi' in event_title.lower() or 'consumer price' in event_title.lower():
            return self._get_cpi_fallback_analysis(event, is_post_event)
        elif 'interest rate' in event_title.lower() or 'fomc' in event_title.lower():
            return self._get_interest_rate_fallback_analysis(event, is_post_event)
        elif 'gdp' in event_title.lower():
            return self._get_gdp_fallback_analysis(event, is_post_event)
        elif 'employment' in event_title.lower() or 'unemployment' in event_title.lower():
            return self._get_employment_fallback_analysis(event, is_post_event)
        else:
            return self._get_generic_fallback_analysis(event, is_post_event)
    
    def _is_qualitative_event(self, title: str) -> bool:
        """Check if event is qualitative (speech, statement) vs quantitative (data release)"""
        qualitative_keywords = [
            'speech', 'speaks', 'testimony', 'testifies',
            'statement', 'press conference', 'meeting minutes',
            'announcement', 'decision', 'policy',
            'comments', 'remarks', 'interview',
            'summit', 'conference', 'hearing',
            'guidance', 'outlook'
        ]
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in qualitative_keywords)
    
    def _get_qualitative_event_fallback_analysis(self, event: Dict, is_post_event: bool) -> GPTAnalysisResult:
        """Fallback analysis for qualitative events (speeches, statements, announcements)"""
        event_title = event.get('title', 'Unknown Event')
        currency = event.get('currency', 'USD')
        impact = event.get('impact', 'medium')
        
        # Identify speaker/institution
        speaker = "Central Bank Official"
        if 'powell' in event_title.lower() or 'fed' in event_title.lower():
            speaker = "Federal Reserve Chair Powell"
            central_bank = "Federal Reserve"
        elif 'lagarde' in event_title.lower() or 'ecb' in event_title.lower():
            speaker = "ECB President Lagarde"
            central_bank = "European Central Bank"
        elif 'bailey' in event_title.lower() or 'boe' in event_title.lower():
            speaker = "BoE Governor Bailey"
            central_bank = "Bank of England"
        elif 'ueda' in event_title.lower() or 'boj' in event_title.lower():
            speaker = "BoJ Governor Ueda"
            central_bank = "Bank of Japan"
        else:
            central_bank = f"{currency} Central Bank"
        
        # Determine stance based on event timing
        stance = "Neutral"
        if is_post_event:
            stance_desc = "has spoken"
        else:
            stance_desc = "is scheduled to speak"
        
        return GPTAnalysisResult(
            headline=f"🎤 {speaker} {stance_desc.title()} - {currency} Volatility Expected",
            key_takeaway=f"{speaker} {stance_desc}, providing insights into {central_bank} policy direction. Expect heightened {currency} volatility and potential shifts in market sentiment based on tone and forward guidance.",
            forward_scenarios={
                "hawkish": f"🦅 Hawkish Tone: {speaker} signals tighter policy → {currency} strengthens. EUR/USD could test lower levels, USD/JPY higher.",
                "dovish": f"🕊️ Dovish Tone: {speaker} signals looser policy → {currency} weakens. EUR/USD could rally, USD/JPY lower.",
                "neutral": f"➡️ Balanced Tone: {speaker} maintains neutral stance → Range-bound trading in {currency} pairs with limited directional moves."
            },
            event_summary={
                "release": event_title,
                "type": "Qualitative Event - Speech/Statement",
                "speaker": speaker,
                "institution": central_bank,
                "focus": "Market will focus on tone, forward guidance, and policy hints",
                "data_type": "No quantitative data - sentiment and language analysis"
            },
            market_reaction={
                "price_action": f"{currency} pairs expected to show volatility based on {speaker}'s tone. Watch for hawkish (bullish {currency}) or dovish (bearish {currency}) language. Initial reaction within first 15-30 minutes.",
                "volatility": f"{impact.title()} volatility expected. Speeches can cause sharp moves if guidance changes or unexpected comments are made.",
                "reason": f"Central bank communications directly impact monetary policy expectations and currency valuations. {speaker}'s words can shift rate expectations and {currency} strength."
            },
            implications_takeaways={
                "economic_context": f"{central_bank} communications provide insight into policy makers' views on inflation, growth, and labor markets. This guides market expectations for future rate decisions.",
                "policy_implications": f"Watch for hints about future rate path. Hawkish language suggests potential rate hikes (bullish {currency}), dovish suggests rate cuts or holds (bearish {currency}).",
                "market_bias": f"Market bias will shift based on tone: Hawkish = Bullish {currency}, Dovish = Bearish {currency}, Neutral = Range-bound.",
                "risk_level": f"{impact.title()} risk - Speeches can cause unexpected volatility if {speaker} makes surprising statements or policy shifts."
            },
            trading_plan={
                "best_approach": f"Wait for initial reaction to {speaker}'s comments, then trade the follow-through. Avoid positioning heavily before the speech unless you have strong conviction.",
                "avoid_strategies": "Avoid large positions immediately before speech. Don't fight clear policy signals. Avoid overtrading on every word - focus on overall tone.",
                "key_levels": f"EUR/USD: Monitor 1.08-1.09 range. USD/JPY: Watch 148.0-149.0 levels. Breakouts indicate strong policy shift.",
                "position_sizing": f"Conservative sizing before speech, normal sizing after direction confirmed. Use wider stops during volatility.",
                "next_catalysts": f"Follow-up speeches, {central_bank} meeting minutes, next policy decision, economic data releases."
            },
            big_picture={
                "economic_outlook": f"{speaker}'s comments will shape market expectations for {currency} economic trajectory and {central_bank} policy path.",
                "medium_term_direction": f"{currency} medium-term direction depends on consistency of central bank messaging. Hawkish trend = sustained {currency} strength.",
                "policy_trajectory": f"{central_bank} policy path will be guided by economic data and official communications. {speaker}'s comments provide critical policy insights.",
                "forward_focus": f"Monitor for policy shifts, changes in inflation/growth outlook, and hints about future rate decisions. Watch for confirmation in subsequent data releases."
            },
            positioning_context={
                "retail_sentiment": f"Retail traders typically react emotionally to central bank speeches. Watch for overcrowded trades to fade.",
                "institutional_flow": f"Institutional investors position based on policy expectations. Large flows occur when {speaker} signals clear policy shifts.",
                "futures_positioning": f"Futures markets price in rate expectations. Speech can cause rapid repricing if guidance changes.",
                "market_bias": f"Current bias will shift based on {speaker}'s tone. Markets are sensitive to unexpected policy signals."
            },
            next_catalysts=[
                f"{central_bank} policy meeting and rate decision",
                f"Follow-up speeches and communications from {central_bank} officials",
                f"Economic data releases that influence {central_bank} policy (inflation, employment, growth)",
                f"Global central bank decisions and policy divergence"
            ],
            confidence_score=70.0,  # Lower confidence for qualitative events
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type="post_event" if is_post_event else "pre_event",
            model_used="qualitative_event_fallback",
            cost_estimate=0.0
        )
    
    def _get_nfp_fallback_analysis(self, event: Dict, is_post_event: bool) -> GPTAnalysisResult:
        """Specific NFP fallback analysis"""
        currency = event.get('currency', 'USD')
        previous = event.get('previous', 'N/A')
        expected = event.get('expected', 'N/A')
        actual = event.get('actual', 'N/A')
        
        if is_post_event and actual != 'N/A':
            # Post-event analysis
            try:
                actual_val = float(str(actual).replace(',', ''))
                expected_val = float(str(expected).replace(',', ''))
                previous_val = float(str(previous).replace(',', ''))
                
                if actual_val > expected_val:
                    bias = "Bullish"
                    sentiment = "Positive"
                    impact = "Strong"
                elif actual_val < expected_val:
                    bias = "Bearish"
                    sentiment = "Negative"
                    impact = "Strong"
                else:
                    bias = "Neutral"
                    sentiment = "Neutral"
                    impact = "Moderate"
            except:
                bias = "Neutral"
                sentiment = "Neutral"
                impact = "Moderate"
        else:
            # Pre-event analysis
            bias = "Neutral"
            sentiment = "Neutral"
            impact = "Moderate"
        
        return GPTAnalysisResult(
            headline=f"📊 Non-Farm Payrolls Analysis - {bias} Bias Expected",
            key_takeaway=f"NFP data {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show employment trends'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"✅ Strong NFP above {expected}: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"❌ Weak NFP below {expected}: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"➡️ NFP in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
            },
            event_summary={
                "release": f"Non-Farm Payrolls report for {event.get('date', 'Unknown')}",
                "outcome": f"NFP {('showed ' + bias.lower() + ' employment data') if is_post_event else 'expected to show employment trends'} with {impact.lower()} market impact.",
                "previous": previous,
                "expected": expected,
                "actual": actual if is_post_event else "Data pending"
            },
            market_reaction={
                "price_action": f"USD pairs expected to show {impact.lower()} volatility with {bias.lower()} bias. EUR/USD and USD/JPY primary movers.",
                "volatility": f"{impact} volatility expected with 15-25 pip movements on data surprises.",
                "reason": f"Employment data directly impacts Federal Reserve policy expectations and USD strength."
            },
            implications_takeaways={
                "economic_context": "NFP is the most important employment indicator, directly affecting economic growth and inflation expectations.",
                "policy_implications": f"{bias} employment data suggests {('hawkish' if bias == 'Bullish' else 'dovish' if bias == 'Bearish' else 'neutral')} Federal Reserve policy bias.",
                "market_bias": f"{bias} - Employment trends suggest {bias.lower()} USD outlook.",
                "risk_level": f"{impact} risk with potential for sharp USD movements."
            },
            trading_plan={
                "best_approach": f"Range trading with breakout potential. Monitor EUR/USD 1.08-1.09 and USD/JPY 148.0-149.0 levels.",
                "avoid_strategies": "Avoid aggressive positioning before data release. Use tight stops due to volatility.",
                "key_levels": "EUR/USD: 1.08 support, 1.09 resistance. USD/JPY: 148.0 support, 149.0 resistance.",
                "position_sizing": "Conservative position sizing recommended due to high volatility.",
                "next_catalysts": "Federal Reserve meetings, CPI data, and other employment indicators."
            },
            big_picture={
                "economic_outlook": f"Employment trends suggest {bias.lower()} economic conditions with implications for growth and inflation.",
                "medium_term_direction": f"USD likely to maintain {bias.lower()} bias based on employment trends.",
                "policy_trajectory": f"Federal Reserve policy trajectory influenced by employment data trends.",
                "forward_focus": "Monitor for follow-up employment data and Federal Reserve communications."
            },
            positioning_context={
                "retail_sentiment": f"Retail traders showing {sentiment.lower()} sentiment toward USD based on employment expectations.",
                "institutional_flow": "Institutional investors positioning for employment data impact on USD.",
                "futures_positioning": "Futures markets showing balanced positioning ahead of NFP release.",
                "market_bias": f"Overall market bias is {bias.lower()} for USD based on employment trends."
            },
            next_catalysts=[
                "Federal Reserve FOMC meetings",
                "CPI and PPI data releases",
                "Other employment indicators (ADP, Unemployment Rate)"
            ],
            confidence_score=75.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type="post_event" if is_post_event else "pre_event",
            model_used="enhanced_fallback",
            cost_estimate=0.0
        )
    
    def _get_cpi_fallback_analysis(self, event: Dict, is_post_event: bool) -> GPTAnalysisResult:
        """Specific CPI fallback analysis"""
        currency = event.get('currency', 'USD')
        previous = event.get('previous', 'N/A')
        expected = event.get('expected', 'N/A')
        actual = event.get('actual', 'N/A')
        
        if is_post_event and actual != 'N/A':
            # Post-event analysis
            try:
                actual_val = float(str(actual).replace(',', ''))
                expected_val = float(str(expected).replace(',', ''))
                previous_val = float(str(previous).replace(',', ''))
                
                if actual_val > expected_val:
                    bias = "Bullish"
                    sentiment = "Positive"
                    impact = "Strong"
                elif actual_val < expected_val:
                    bias = "Bearish"
                    sentiment = "Negative"
                    impact = "Strong"
                else:
                    bias = "Neutral"
                    sentiment = "Neutral"
                    impact = "Moderate"
            except:
                bias = "Neutral"
                sentiment = "Neutral"
                impact = "Moderate"
        else:
            # Pre-event analysis
            bias = "Neutral"
            sentiment = "Neutral"
            impact = "Moderate"
        
        return GPTAnalysisResult(
            headline=f"📊 Consumer Price Index Analysis - {bias} Bias Expected",
            key_takeaway=f"CPI data {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show inflation trends'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"✅ Strong CPI above {expected}: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"❌ Weak CPI below {expected}: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"➡️ CPI in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
            },
            event_summary={
                "release": f"Consumer Price Index report for {event.get('date', 'Unknown')}",
                "outcome": f"CPI {('showed ' + bias.lower() + ' inflation data') if is_post_event else 'expected to show inflation trends'} with {impact.lower()} market impact.",
                "previous": previous,
                "expected": expected,
                "actual": actual if is_post_event else "Data pending"
            },
            market_reaction={
                "price_action": f"USD pairs expected to show {impact.lower()} volatility with {bias.lower()} bias. EUR/USD and USD/JPY primary movers.",
                "volatility": f"{impact} volatility expected with 15-25 pip movements on data surprises.",
                "reason": f"Inflation data directly impacts Federal Reserve policy expectations and USD strength."
            },
            implications_takeaways={
                "economic_context": "CPI is the primary gauge of inflation, directly affecting Federal Reserve monetary policy decisions.",
                "policy_implications": f"{bias} inflation data suggests {('hawkish' if bias == 'Bullish' else 'dovish' if bias == 'Bearish' else 'neutral')} Federal Reserve policy bias.",
                "market_bias": f"{bias} - Inflation trends suggest {bias.lower()} USD outlook.",
                "risk_level": f"{impact} risk with potential for sharp USD movements."
            },
            trading_plan={
                "best_approach": f"Range trading with breakout potential. Monitor EUR/USD 1.08-1.09 and USD/JPY 148.0-149.0 levels.",
                "avoid_strategies": "Avoid aggressive positioning before data release. Use tight stops due to volatility.",
                "key_levels": "EUR/USD: 1.08 support, 1.09 resistance. USD/JPY: 148.0 support, 149.0 resistance.",
                "position_sizing": "Conservative position sizing recommended due to high volatility.",
                "next_catalysts": "Federal Reserve meetings, PPI data, and other inflation indicators."
            },
            big_picture={
                "economic_outlook": f"Inflation trends suggest {bias.lower()} economic conditions with implications for growth and monetary policy.",
                "medium_term_direction": f"USD likely to maintain {bias.lower()} bias based on inflation trends.",
                "policy_trajectory": f"Federal Reserve policy trajectory influenced by inflation data trends.",
                "forward_focus": "Monitor for follow-up inflation data and Federal Reserve communications."
            },
            positioning_context={
                "retail_sentiment": f"Retail traders showing {sentiment.lower()} sentiment toward USD based on inflation expectations.",
                "institutional_flow": "Institutional investors positioning for inflation data impact on USD.",
                "futures_positioning": "Futures markets showing balanced positioning ahead of CPI release.",
                "market_bias": f"Overall market bias is {bias.lower()} for USD based on inflation trends."
            },
            next_catalysts=[
                "Federal Reserve FOMC meetings",
                "PPI data releases",
                "Other inflation indicators (Core CPI, Personal Consumption Expenditures)"
            ],
            confidence_score=75.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type="post_event" if is_post_event else "pre_event",
            model_used="enhanced_fallback",
            cost_estimate=0.0
        )
    
    def _get_interest_rate_fallback_analysis(self, event: Dict, is_post_event: bool) -> GPTAnalysisResult:
        """Specific interest rate fallback analysis"""
        currency = event.get('currency', 'USD')
        previous = event.get('previous', 'N/A')
        expected = event.get('expected', 'N/A')
        actual = event.get('actual', 'N/A')
        
        if is_post_event and actual != 'N/A':
            # Post-event analysis
            try:
                actual_val = float(str(actual).replace(',', ''))
                expected_val = float(str(expected).replace(',', ''))
                previous_val = float(str(previous).replace(',', ''))
                
                if actual_val > expected_val:
                    bias = "Bullish"
                    sentiment = "Positive"
                    impact = "Strong"
                elif actual_val < expected_val:
                    bias = "Bearish"
                    sentiment = "Negative"
                    impact = "Strong"
                else:
                    bias = "Neutral"
                    sentiment = "Neutral"
                    impact = "Moderate"
            except:
                bias = "Neutral"
                sentiment = "Neutral"
                impact = "Moderate"
        else:
            # Pre-event analysis
            bias = "Neutral"
            sentiment = "Neutral"
            impact = "Moderate"
        
        return GPTAnalysisResult(
            headline=f"📊 Interest Rate Decision Analysis - {bias} Bias Expected",
            key_takeaway=f"Interest rate decision {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show policy stance'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"✅ Stronger than expected: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"❌ Weaker than expected: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"➡️ In line with expectations: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
            },
            event_summary={
                "release": f"Federal Open Market Committee (FOMC) decision for {event.get('date', 'Unknown')}",
                "outcome": f"FOMC decision {('indicated ' + bias.lower() + ' policy stance') if is_post_event else 'expected to indicate policy stance'} with {impact.lower()} market impact.",
                "previous": previous,
                "expected": expected,
                "actual": actual if is_post_event else "Data pending"
            },
            market_reaction={
                "price_action": f"USD pairs expected to show {impact.lower()} volatility with {bias.lower()} bias. EUR/USD and USD/JPY primary movers.",
                "volatility": f"{impact} volatility expected with 15-25 pip movements on data surprises.",
                "reason": f"Interest rate decisions directly impact Federal Reserve monetary policy and currency strength."
            },
            implications_takeaways={
                "economic_context": "Interest rate decisions are a key driver of currency valuations, affecting both short-term and long-term interest rates.",
                "policy_implications": f"{bias} interest rate decision suggests {('hawkish' if bias == 'Bullish' else 'dovish' if bias == 'Bearish' else 'neutral')} Federal Reserve policy bias.",
                "market_bias": f"{bias} - Interest rate decisions suggest {bias.lower()} USD outlook.",
                "risk_level": f"{impact} risk with potential for sharp USD movements."
            },
            trading_plan={
                "best_approach": f"Range trading with breakout potential. Monitor EUR/USD 1.08-1.09 and USD/JPY 148.0-149.0 levels.",
                "avoid_strategies": "Avoid aggressive positioning before data release. Use tight stops due to volatility.",
                "key_levels": "EUR/USD: 1.08 support, 1.09 resistance. USD/JPY: 148.0 support, 149.0 resistance.",
                "position_sizing": "Conservative position sizing recommended due to high volatility.",
                "next_catalysts": "Federal Reserve meetings, GDP data, and other economic indicators."
            },
            big_picture={
                "economic_outlook": f"Interest rate decisions suggest {bias.lower()} economic conditions with implications for growth and monetary policy.",
                "medium_term_direction": f"USD likely to maintain {bias.lower()} bias based on interest rate decisions.",
                "policy_trajectory": f"Federal Reserve policy trajectory influenced by interest rate decisions.",
                "forward_focus": "Monitor for follow-up interest rate decisions and Federal Reserve communications."
            },
            positioning_context={
                "retail_sentiment": f"Retail traders showing {sentiment.lower()} sentiment toward USD based on interest rate expectations.",
                "institutional_flow": "Institutional investors positioning for interest rate data impact on USD.",
                "futures_positioning": "Futures markets showing balanced positioning ahead of FOMC decision.",
                "market_bias": f"Overall market bias is {bias.lower()} for USD based on interest rate expectations."
            },
            next_catalysts=[
                "Federal Reserve FOMC meetings",
                "GDP data releases",
                "Other economic indicators (Employment, Inflation)"
            ],
            confidence_score=75.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type="post_event" if is_post_event else "pre_event",
            model_used="enhanced_fallback",
            cost_estimate=0.0
        )
    
    def _get_gdp_fallback_analysis(self, event: Dict, is_post_event: bool) -> GPTAnalysisResult:
        """Specific GDP fallback analysis"""
        currency = event.get('currency', 'USD')
        previous = event.get('previous', 'N/A')
        expected = event.get('expected', 'N/A')
        actual = event.get('actual', 'N/A')
        
        if is_post_event and actual != 'N/A':
            # Post-event analysis
            try:
                actual_val = float(str(actual).replace(',', ''))
                expected_val = float(str(expected).replace(',', ''))
                previous_val = float(str(previous).replace(',', ''))
                
                if actual_val > expected_val:
                    bias = "Bullish"
                    sentiment = "Positive"
                    impact = "Strong"
                elif actual_val < expected_val:
                    bias = "Bearish"
                    sentiment = "Negative"
                    impact = "Strong"
                else:
                    bias = "Neutral"
                    sentiment = "Neutral"
                    impact = "Moderate"
            except:
                bias = "Neutral"
                sentiment = "Neutral"
                impact = "Moderate"
        else:
            # Pre-event analysis
            bias = "Neutral"
            sentiment = "Neutral"
            impact = "Moderate"
        
        return GPTAnalysisResult(
            headline=f"📊 Gross Domestic Product Analysis - {bias} Bias Expected",
            key_takeaway=f"GDP data {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show economic growth'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"✅ Strong GDP above {expected}: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"❌ Weak GDP below {expected}: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"➡️ GDP in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
            },
            event_summary={
                "release": f"Gross Domestic Product report for {event.get('date', 'Unknown')}",
                "outcome": f"GDP {('showed ' + bias.lower() + ' economic growth') if is_post_event else 'expected to show economic growth'} with {impact.lower()} market impact.",
                "previous": previous,
                "expected": expected,
                "actual": actual if is_post_event else "Data pending"
            },
            market_reaction={
                "price_action": f"USD pairs expected to show {impact.lower()} volatility with {bias.lower()} bias. EUR/USD and USD/JPY primary movers.",
                "volatility": f"{impact} volatility expected with 15-25 pip movements on data surprises.",
                "reason": f"GDP data directly impacts Federal Reserve policy expectations and currency strength."
            },
            implications_takeaways={
                "economic_context": "GDP is the broadest measure of economic activity, directly affecting Federal Reserve policy decisions and currency strength.",
                "policy_implications": f"{bias} GDP growth suggests {('hawkish' if bias == 'Bullish' else 'dovish' if bias == 'Bearish' else 'neutral')} Federal Reserve policy bias.",
                "market_bias": f"{bias} - GDP growth suggests {bias.lower()} USD outlook.",
                "risk_level": f"{impact} risk with potential for sharp USD movements."
            },
            trading_plan={
                "best_approach": f"Range trading with breakout potential. Monitor EUR/USD 1.08-1.09 and USD/JPY 148.0-149.0 levels.",
                "avoid_strategies": "Avoid aggressive positioning before data release. Use tight stops due to volatility.",
                "key_levels": "EUR/USD: 1.08 support, 1.09 resistance. USD/JPY: 148.0 support, 149.0 resistance.",
                "position_sizing": "Conservative position sizing recommended due to high volatility.",
                "next_catalysts": "Federal Reserve meetings, employment data, and other economic indicators."
            },
            big_picture={
                "economic_outlook": f"GDP growth suggests {bias.lower()} economic conditions with implications for growth and monetary policy.",
                "medium_term_direction": f"USD likely to maintain {bias.lower()} bias based on GDP growth.",
                "policy_trajectory": f"Federal Reserve policy trajectory influenced by GDP data trends.",
                "forward_focus": "Monitor for follow-up GDP data and Federal Reserve communications."
            },
            positioning_context={
                "retail_sentiment": f"Retail traders showing {sentiment.lower()} sentiment toward USD based on GDP expectations.",
                "institutional_flow": "Institutional investors positioning for GDP data impact on USD.",
                "futures_positioning": "Futures markets showing balanced positioning ahead of GDP release.",
                "market_bias": f"Overall market bias is {bias.lower()} for USD based on GDP expectations."
            },
            next_catalysts=[
                "Federal Reserve FOMC meetings",
                "Employment data releases",
                "Other economic indicators (Unemployment Rate, Inflation)"
            ],
            confidence_score=75.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type="post_event" if is_post_event else "pre_event",
            model_used="enhanced_fallback",
            cost_estimate=0.0
        )
    
    def _get_employment_fallback_analysis(self, event: Dict, is_post_event: bool) -> GPTAnalysisResult:
        """Specific employment fallback analysis"""
        currency = event.get('currency', 'USD')
        previous = event.get('previous', 'N/A')
        expected = event.get('expected', 'N/A')
        actual = event.get('actual', 'N/A')
        
        if is_post_event and actual != 'N/A':
            # Post-event analysis
            try:
                actual_val = float(str(actual).replace(',', ''))
                expected_val = float(str(expected).replace(',', ''))
                previous_val = float(str(previous).replace(',', ''))
                
                if actual_val > expected_val:
                    bias = "Bullish"
                    sentiment = "Positive"
                    impact = "Strong"
                elif actual_val < expected_val:
                    bias = "Bearish"
                    sentiment = "Negative"
                    impact = "Strong"
                else:
                    bias = "Neutral"
                    sentiment = "Neutral"
                    impact = "Moderate"
            except:
                bias = "Neutral"
                sentiment = "Neutral"
                impact = "Moderate"
        else:
            # Pre-event analysis
            bias = "Neutral"
            sentiment = "Neutral"
            impact = "Moderate"
        
        return GPTAnalysisResult(
            headline=f"📊 Unemployment Rate Analysis - {bias} Bias Expected",
            key_takeaway=f"Unemployment rate {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show labor market trends'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"✅ Lower than expected: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"❌ Higher than expected: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"➡️ Unemployment rate in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
            },
            event_summary={
                "release": f"Unemployment Rate report for {event.get('date', 'Unknown')}",
                "outcome": f"Unemployment rate {('showed ' + bias.lower() + ' labor market trends') if is_post_event else 'expected to show labor market trends'} with {impact.lower()} market impact.",
                "previous": previous,
                "expected": expected,
                "actual": actual if is_post_event else "Data pending"
            },
            market_reaction={
                "price_action": f"USD pairs expected to show {impact.lower()} volatility with {bias.lower()} bias. EUR/USD and USD/JPY primary movers.",
                "volatility": f"{impact} volatility expected with 15-25 pip movements on data surprises.",
                "reason": f"Unemployment data directly impacts Federal Reserve policy expectations and currency strength."
            },
            implications_takeaways={
                "economic_context": "Unemployment data is a key indicator of labor market health, directly affecting Federal Reserve policy decisions and currency strength.",
                "policy_implications": f"{bias} unemployment data suggests {('hawkish' if bias == 'Bullish' else 'dovish' if bias == 'Bearish' else 'neutral')} Federal Reserve policy bias.",
                "market_bias": f"{bias} - Unemployment trends suggest {bias.lower()} USD outlook.",
                "risk_level": f"{impact} risk with potential for sharp USD movements."
            },
            trading_plan={
                "best_approach": f"Range trading with breakout potential. Monitor EUR/USD 1.08-1.09 and USD/JPY 148.0-149.0 levels.",
                "avoid_strategies": "Avoid aggressive positioning before data release. Use tight stops due to volatility.",
                "key_levels": "EUR/USD: 1.08 support, 1.09 resistance. USD/JPY: 148.0 support, 149.0 resistance.",
                "position_sizing": "Conservative position sizing recommended due to high volatility.",
                "next_catalysts": "Federal Reserve meetings, GDP data, and other economic indicators."
            },
            big_picture={
                "economic_outlook": f"Unemployment trends suggest {bias.lower()} economic conditions with implications for growth and monetary policy.",
                "medium_term_direction": f"USD likely to maintain {bias.lower()} bias based on unemployment trends.",
                "policy_trajectory": f"Federal Reserve policy trajectory influenced by unemployment data trends.",
                "forward_focus": "Monitor for follow-up unemployment data and Federal Reserve communications."
            },
            positioning_context={
                "retail_sentiment": f"Retail traders showing {sentiment.lower()} sentiment toward USD based on unemployment expectations.",
                "institutional_flow": "Institutional investors positioning for unemployment data impact on USD.",
                "futures_positioning": "Futures markets showing balanced positioning ahead of employment data release.",
                "market_bias": f"Overall market bias is {bias.lower()} for USD based on unemployment expectations."
            },
            next_catalysts=[
                "Federal Reserve FOMC meetings",
                "GDP data releases",
                "Other economic indicators (GDP, Inflation)"
            ],
            confidence_score=75.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type="post_event" if is_post_event else "pre_event",
            model_used="enhanced_fallback",
            cost_estimate=0.0
        )
    
    def _get_generic_fallback_analysis(self, event: Dict, is_post_event: bool) -> GPTAnalysisResult:
        """Generic fallback analysis for other economic indicators"""
        currency = event.get('currency', 'USD')
        event_title = event.get('title', 'Economic Event')
        impact = event.get('impact', 'medium')
        previous = event.get('previous', 'N/A')
        expected = event.get('expected', 'N/A')
        actual = event.get('actual', 'N/A')
        
        # Normalize empty values
        empty_values = ['N/A', 'TBD', '', None, '--', 'n/a', 'tbd', 'pending']
        if previous in empty_values:
            previous = 'N/A'
        if expected in empty_values:
            expected = 'N/A'
        if actual in empty_values:
            actual = 'N/A'
        
        # Determine if we have enough data for analysis
        has_data = previous != 'N/A' or expected != 'N/A' or actual != 'N/A'
        
        # If no data at all, provide event-type based analysis
        if not has_data:
            bias = "Neutral"
            sentiment = "Neutral"
            impact_str = "Moderate"
            data_note = f"Limited data available for {event_title}. Analysis based on event type and typical market impact."
        elif is_post_event and actual != 'N/A':
            # Post-event analysis with actual data
            try:
                actual_val = float(str(actual).replace(',', '').replace('%', ''))
                expected_val = float(str(expected).replace(',', '').replace('%', '')) if expected != 'N/A' else actual_val
                
                if actual_val > expected_val:
                    bias = "Bullish"
                    sentiment = "Positive"
                    impact_str = "Strong"
                elif actual_val < expected_val:
                    bias = "Bearish"
                    sentiment = "Negative"
                    impact_str = "Strong"
                else:
                    bias = "Neutral"
                    sentiment = "Neutral"
                    impact_str = "Moderate"
            except:
                # Can't parse numbers, default to neutral
                bias = "Neutral"
                sentiment = "Neutral"
                impact_str = "Moderate"
        else:
            # Pre-event analysis or missing actual data
            bias = "Neutral"
            sentiment = "Neutral"
            impact_str = "Moderate"
        
        # Create appropriate headline and takeaway based on data availability
        if not has_data:
            headline_text = f"📊 {event_title} - Market Impact Analysis"
            takeaway_text = data_note
        else:
            headline_text = f"📊 {event_title} - {bias} Bias Expected"
            takeaway_text = f"Economic data {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show economic trends'} with {impact_str.lower()} {currency} impact."
        
        return GPTAnalysisResult(
            headline=headline_text,
            key_takeaway=takeaway_text,
            forward_scenarios={
                "bullish": f"✅ Stronger than expected: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"❌ Weaker than expected: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"➡️ Economic data in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
            },
            event_summary={
                "release": f"{event_title} - {event.get('date', 'Unknown')}",
                "outcome": f"{event_title} {('showed ' + bias.lower() + ' economic trends') if is_post_event else 'expected to show economic trends'} with {impact_str.lower()} market impact.",
                "previous": previous,
                "expected": expected,
                "actual": actual if is_post_event else "Data pending",
                "data_availability": "Full data" if has_data else "Limited data"
            },
            market_reaction={
                "price_action": f"{currency} pairs expected to show {impact_str.lower()} volatility with {bias.lower()} bias. Primary movers based on {currency} exposure.",
                "volatility": f"{impact_str} volatility expected with potential price movements based on event impact.",
                "reason": f"{event_title} impacts {currency} through economic fundamentals and policy expectations."
            },
            implications_takeaways={
                "economic_context": f"{event_title} is a key driver of {currency} valuations through economic fundamentals.",
                "policy_implications": f"{bias} data suggests {('hawkish' if bias == 'Bullish' else 'dovish' if bias == 'Bearish' else 'neutral')} central bank policy bias for {currency}.",
                "market_bias": f"{bias} - Economic trends suggest {bias.lower()} {currency} outlook.",
                "risk_level": f"{impact_str} risk with potential {currency} movements based on data surprise factor."
            },
            trading_plan={
                "best_approach": f"Range trading with breakout potential. Monitor EUR/USD 1.08-1.09 and USD/JPY 148.0-149.0 levels.",
                "avoid_strategies": "Avoid aggressive positioning before data release. Use tight stops due to volatility.",
                "key_levels": "EUR/USD: 1.08 support, 1.09 resistance. USD/JPY: 148.0 support, 149.0 resistance.",
                "position_sizing": "Conservative position sizing recommended due to high volatility.",
                "next_catalysts": "Federal Reserve meetings, employment data, and other economic indicators."
            },
            big_picture={
                "economic_outlook": f"Economic data suggests {bias.lower()} economic conditions with implications for growth and monetary policy.",
                "medium_term_direction": f"USD likely to maintain {bias.lower()} bias based on economic trends.",
                "policy_trajectory": f"Federal Reserve policy trajectory influenced by economic data trends.",
                "forward_focus": "Monitor for follow-up economic data and Federal Reserve communications."
            },
            positioning_context={
                "retail_sentiment": f"Retail traders showing {sentiment.lower()} sentiment toward USD based on economic expectations.",
                "institutional_flow": "Institutional investors positioning for economic data impact on USD.",
                "futures_positioning": "Futures markets showing balanced positioning ahead of economic release.",
                "market_bias": f"Overall market bias is {bias.lower()} for USD based on economic expectations."
            },
            next_catalysts=[
                "Federal Reserve FOMC meetings",
                "Employment data releases",
                "Other economic indicators (Unemployment Rate, Inflation)"
            ],
            confidence_score=75.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type="post_event" if is_post_event else "pre_event",
            model_used="enhanced_fallback",
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

    def _select_model(self, event: Dict) -> str:
        """Select appropriate GPT model based on event characteristics"""
        # For now, use GPT-3.5-turbo for cost efficiency
        # Could be enhanced to use GPT-4 for high-impact events
        impact = event.get('impact', 'medium').lower()
        
        if impact == 'high':
            return 'gpt-4-turbo-preview'  # Use GPT-4 for high-impact events
        else:
            return 'gpt-3.5-turbo'  # Use GPT-3.5 for medium/low impact events
    
    def _get_error_fallback(self, event: Dict, analysis_type: str = "pre_event") -> GPTAnalysisResult:
        """Generate fallback analysis when GPT API fails"""
        return self._get_fallback_analysis(event, analysis_type)
    
    def _generate_enhanced_gpt_analysis(self, event: Dict, market_context: MarketContext, 
                                      analysis_type: str, model: str) -> GPTAnalysisResult:
        """Generate enhanced GPT analysis with real API calls"""
        try:
            if not self.client:
                logger.warning("OpenAI client not available, using fallback")
                return self._get_fallback_analysis(event, analysis_type)
            
            # Prepare the prompt for GPT
            prompt = self._create_analysis_prompt(event, market_context, analysis_type)
            
            # Make API call to OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional forex market analyst with deep expertise in economic events and their market impact."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse the response
            gpt_response = response.choices[0].message.content
            
            # Convert GPT response to structured analysis
            analysis_result = self._parse_gpt_response(gpt_response, event, analysis_type, model)
            
            # Calculate cost estimate
            cost_estimate = self._calculate_cost_estimate(response.usage, model)
            analysis_result.cost_estimate = cost_estimate
            self.total_cost += cost_estimate
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in GPT analysis: {e}")
            return self._get_fallback_analysis(event, analysis_type)
    
    def _create_analysis_prompt(self, event: Dict, market_context: MarketContext, analysis_type: str) -> str:
        """Create a comprehensive prompt for GPT analysis"""
        event_title = event.get('title', 'Unknown Event')
        currency = event.get('currency', 'USD')
        impact = event.get('impact', 'medium')
        previous = event.get('previous', 'N/A')
        expected = event.get('expected', 'N/A')
        actual = event.get('actual', 'N/A')
        
        prompt = f"""
Analyze the following economic event and provide comprehensive market analysis:

EVENT DETAILS:
- Title: {event_title}
- Currency: {currency}
- Impact Level: {impact}
- Previous: {previous}
- Expected: {expected}
- Actual: {actual}
- Analysis Type: {analysis_type}

MARKET CONTEXT:
- Current Prices: {market_context.current_prices}
- Market Sentiment: {market_context.market_sentiment}
- Bond Yields: {market_context.bond_yields}
- Equity Indices: {market_context.equity_indices}

IMPORTANT: For forward_scenarios, provide specific probability percentages for each scenario (bullish, bearish, neutral). 
The probabilities should sum to approximately 100% and reflect the likelihood of each outcome based on the event data, 
market context, and historical patterns. Include key price levels and reasoning for each scenario.

Please provide analysis in the following JSON format:
{{
    "headline": "Compelling headline summarizing the key takeaway",
    "key_takeaway": "Main insight in 1-2 sentences",
    "forward_scenarios": {{
        "bullish": "Bullish scenario description with specific probability percentage (e.g., '60% probability: Above key resistance at [level], target [level]. Reason: [driver]')",
        "bearish": "Bearish scenario description with specific probability percentage (e.g., '30% probability: Below key support at [level], target [level]. Reason: [driver]')", 
        "neutral": "Neutral scenario description with specific probability percentage (e.g., '10% probability: Range trading between [level] and [level] if no breakout')"
    }},
    "event_summary": {{
        "release": "Event description",
        "outcome": "What happened vs expectations",
        "previous": "{previous}",
        "expected": "{expected}",
        "actual": "{actual}"
    }},
    "market_reaction": {{
        "price_action": "Expected price action",
        "volatility": "Volatility expectations",
        "reason": "Why this reaction is expected"
    }},
    "implications_takeaways": {{
        "economic_context": "Economic implications",
        "policy_implications": "Central bank policy implications",
        "market_bias": "Overall market bias",
        "risk_level": "Risk assessment"
    }},
    "trading_plan": {{
        "best_approach": "Recommended trading approach",
        "avoid_strategies": "Strategies to avoid",
        "key_levels": "Important price levels",
        "position_sizing": "Position sizing recommendations",
        "next_catalysts": "Upcoming events to watch"
    }},
    "big_picture": {{
        "economic_outlook": "Economic outlook implications",
        "medium_term_direction": "Medium-term market direction",
        "policy_trajectory": "Policy trajectory implications",
        "forward_focus": "What to focus on going forward"
    }},
    "positioning_context": {{
        "retail_sentiment": "Retail trader sentiment",
        "institutional_flow": "Institutional flow analysis",
        "market_bias": "Overall market bias"
    }},
    "next_catalysts": [
        "Upcoming event 1",
        "Upcoming event 2",
        "Upcoming event 3"
    ]
}}

Provide sophisticated, professional analysis that would be valuable for forex traders.
"""
        return prompt
    
    def _parse_gpt_response(self, gpt_response: str, event: Dict, analysis_type: str, model: str) -> GPTAnalysisResult:
        """Parse GPT response into structured analysis"""
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', gpt_response, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                # Fallback if no JSON found
                analysis_data = self._create_fallback_analysis_data(gpt_response, event)
            
            return GPTAnalysisResult(
                headline=analysis_data.get('headline', f"Analysis for {event.get('title', 'Unknown Event')}"),
                key_takeaway=analysis_data.get('key_takeaway', 'Market analysis completed'),
                forward_scenarios=analysis_data.get('forward_scenarios', {}),
                event_summary=analysis_data.get('event_summary', {}),
                market_reaction=analysis_data.get('market_reaction', {}),
                implications_takeaways=analysis_data.get('implications_takeaways', {}),
                trading_plan=analysis_data.get('trading_plan', {}),
                big_picture=analysis_data.get('big_picture', {}),
                positioning_context=analysis_data.get('positioning_context', {}),
                next_catalysts=analysis_data.get('next_catalysts', []),
                confidence_score=85.0,  # High confidence for GPT analysis
                analysis_timestamp=datetime.now().isoformat(),
                event_id=str(event.get('id', 'unknown')),
                analysis_type=analysis_type,
                model_used=model,
                cost_estimate=0.0  # Will be set by caller
            )
            
        except Exception as e:
            logger.error(f"Error parsing GPT response: {e}")
            return self._get_fallback_analysis(event, analysis_type)
    
    def _create_fallback_analysis_data(self, gpt_response: str, event: Dict) -> Dict:
        """Create fallback analysis data from raw GPT response"""
        return {
            'headline': f"GPT Analysis: {event.get('title', 'Unknown Event')}",
            'key_takeaway': gpt_response[:200] + "..." if len(gpt_response) > 200 else gpt_response,
            'forward_scenarios': {
                'bullish': 'Analysis suggests potential bullish scenario',
                'bearish': 'Analysis suggests potential bearish scenario',
                'neutral': 'Analysis suggests neutral scenario'
            },
            'event_summary': {
                'release': event.get('title', 'Unknown Event'),
                'outcome': 'GPT analysis completed',
                'previous': event.get('previous', 'N/A'),
                'expected': event.get('expected', 'N/A'),
                'actual': event.get('actual', 'N/A')
            },
            'market_reaction': {
                'price_action': 'GPT analysis suggests market reaction',
                'volatility': 'Moderate volatility expected',
                'reason': 'Based on GPT analysis'
            },
            'implications_takeaways': {
                'economic_context': 'GPT analysis of economic implications',
                'policy_implications': 'GPT analysis of policy implications',
                'market_bias': 'Neutral',
                'risk_level': 'Medium'
            },
            'trading_plan': {
                'best_approach': 'Monitor market reaction',
                'avoid_strategies': 'Avoid aggressive positioning',
                'key_levels': 'Monitor key support/resistance levels',
                'position_sizing': 'Conservative sizing recommended',
                'next_catalysts': ['Monitor upcoming events']
            },
            'big_picture': {
                'economic_outlook': 'GPT analysis of economic outlook',
                'medium_term_direction': 'Monitor for direction',
                'policy_trajectory': 'GPT analysis of policy trajectory',
                'forward_focus': 'Monitor market developments'
            },
            'positioning_context': {
                'retail_sentiment': 'Mixed',
                'institutional_flow': 'Monitor institutional flows',
                'futures_positioning': 'Balanced',
                'market_bias': 'Neutral'
            },
            'next_catalysts': ['Monitor upcoming economic events']
        }
    
    def _calculate_cost_estimate(self, usage, model: str) -> float:
        """Calculate cost estimate for API usage"""
        if not usage:
            return 0.0
        
        # Cost per 1K tokens
        costs = {
            'gpt-4-turbo-preview': 0.03,
            'gpt-3.5-turbo': 0.002
        }
        
        cost_per_1k = costs.get(model, 0.002)
        total_tokens = usage.total_tokens if hasattr(usage, 'total_tokens') else 0
        return (total_tokens / 1000) * cost_per_1k

# Global instance creation removed - let app.py create its own instance
