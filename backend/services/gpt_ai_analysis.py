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
from services.economy_context_service import economy_context_service
from services.central_bank_ai_context import get_context_for_currency
from services.analysis_context_pack import (
    build_calendar_context_pack_section,
    calendar_forward_scenarios_json_spec,
    is_analysis_context_pack_enabled,
)
from services.analysis_actionable_conditionals import ACTIONABLE_PROMPT_RULES
from services.analysis_personalization import build_prompt_personalization_block
from services.relevant_market_context import build_relevant_market_context_block
from services.openai_model_config import (
    MODEL_COST_PER_1K_TOKENS,
    estimate_cost_from_usage,
    select_model_for_event,
)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
import pickle

logger = logging.getLogger(__name__)

# Bump this when prompt logic/output conventions change (e.g., bold emphasis, new injected context).
# This ensures cached analyses don't mask prompt updates during testing.
PROMPT_VERSION = "2026-05-26-phase-f-regime-vs-event-v1"

# Event type mapping for indicator filtering (Approach 4) - legacy, title-only.
# Kept for test script and fallback; currency-aware mapping uses TITLE_KEYWORD_TO_CONCEPT + CONCEPT_TO_INDICATORS_BY_CURRENCY.
EVENT_TYPE_MAPPING = {
    'employment': ['unemployment', 'nonfarm-payrolls'],
    'inflation': ['inflation-YoY', 'core-inflation-YoY'],
    'gdp': ['gdp-growth'],
    'interest-rate': ['interest-rate'],
    'unemployment': ['unemployment'],
    'cpi': ['inflation-YoY', 'core-inflation-YoY'],
    'nfp': ['unemployment', 'nonfarm-payrolls'],
    'adp': ['unemployment', 'nonfarm-payrolls'],
    'payrolls': ['unemployment', 'nonfarm-payrolls'],
    'fund rate': ['interest-rate'],
    'refinancing rate': ['interest-rate'],
    'rate decision': ['interest-rate'],
    'fomc': ['interest-rate'],
    'ecb main': ['interest-rate'],
    'boe rate': ['interest-rate'],
    'boj rate': ['interest-rate'],
}

# Currency-aware mapping: event title keywords -> concept; then concept -> indicator IDs per economy.
# Indicator IDs must match src/data/economyIndicators.json per economy (US: inflation-YoY, EUR/GBP/JPY: inflation; US: nonfarm-payrolls, others no NFP).
# Order: longer phrases first so "nonfarm payrolls" matches before "payrolls".
TITLE_KEYWORD_TO_CONCEPT = [
    ('nonfarm payrolls', 'employment'), ('nonfarm payroll', 'employment'),
    ('core cpi', 'inflation'), ('core inflation', 'inflation'),
    ('federal funds rate', 'rate'), ('refinancing rate', 'rate'), ('fund rate', 'rate'),
    ('rate decision', 'rate'), ('rate statement', 'rate'), ('official cash rate', 'rate'), ('cash rate', 'rate'), ('overnight rate', 'rate'),
    ('ecb main', 'rate'), ('ecb president', 'rate'), ('fomc', 'rate'), ('fed chair', 'rate'), ('fomc member', 'rate'),
    ('boe rate', 'rate'), ('boe gov', 'rate'), ('boj rate', 'rate'), ('boj gov', 'rate'),
    ('current account', 'current_account'), ('trade balance', 'current_account'),
    ('average earnings', 'wage_growth'), ('earnings index', 'wage_growth'), ('wage growth', 'wage_growth'), ('wage ', 'wage_growth'),
    ('claimant count', 'employment'), ('employment change', 'employment'), ('employment cost', 'employment'),
    ('unemployment rate', 'employment'), ('unemployment claims', 'employment'), ('unemployment', 'employment'),
    ('payrolls', 'employment'), ('payroll', 'employment'), ('adp', 'employment'), ('jolts', 'employment'), ('employment', 'employment'),
    ('inflation', 'inflation'), ('cpi', 'inflation'),
    ('gdp growth', 'gdp'), ('gdp m/m', 'gdp'), ('gdp q/q', 'gdp'), ('prelim gdp', 'gdp'), ('gdp', 'gdp'),
]

# Per-economy indicator IDs (from economyIndicators.json). Only these 4 economies have AI economy context.
CONCEPT_TO_INDICATORS_BY_CURRENCY = {
    'US': {
        'inflation': ['inflation-YoY', 'core-inflation-YoY'],
        'employment': ['unemployment', 'nonfarm-payrolls'],
        'gdp': ['gdp-growth'],
        'rate': ['interest-rate'],
        'current_account': [],
        'wage_growth': [],
    },
    'EUR': {
        'inflation': ['inflation', 'core-inflation-YoY'],
        'employment': ['unemployment'],
        'gdp': ['gdp-growth'],
        'rate': ['interest-rate'],
        'current_account': ['current-account'],
        'wage_growth': [],
    },
    'GBP': {
        'inflation': ['inflation', 'core-inflation-YoY'],
        'employment': ['unemployment'],
        'gdp': ['gdp-growth'],
        'rate': ['interest-rate'],
        'current_account': [],
        'wage_growth': ['wage-growth'],
    },
    'JPY': {
        'inflation': ['inflation', 'core-inflation-YoY'],
        'employment': ['unemployment'],
        'gdp': ['gdp-growth'],
        'rate': ['interest-rate'],
        'current_account': ['current-account'],
        'wage_growth': [],
    },
}

# Policy targets for central banks (Approach 6)
POLICY_TARGETS = {
    'USD': {
        'inflation': 2.0,  # Fed target
        'unemployment': 4.0,  # Fed's "natural rate"
        'central_bank': 'Federal Reserve'
    },
    'EUR': {
        'inflation': 2.0,  # ECB target
        'unemployment': None,
        'central_bank': 'European Central Bank'
    },
    'GBP': {
        'inflation': 2.0,  # BoE target
        'unemployment': None,
        'central_bank': 'Bank of England'
    },
    'JPY': {
        'inflation': 2.0,  # BoJ target
        'unemployment': None,
        'central_bank': 'Bank of Japan'
    }
}

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
        # Don't set default values for positioning data - keep as None if not provided
        # This prevents using inaccurate/estimated data
        # Only set scenario_probabilities if None (this is event-specific, not market data)
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

    # Edge vs data confidence (finalize attaches data_confidence_score)
    analysis_confidence: str = "Medium"
    edge_confidence_reason: str = ""
    assumptions: Optional[List[str]] = None

    def __post_init__(self):
        if self.assumptions is None:
            object.__setattr__(self, "assumptions", [])

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
        self.cost_estimates = dict(MODEL_COST_PER_1K_TOKENS)
        
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
    
    def analyze_macro_event(
        self,
        event: Dict,
        market_context: MarketContext,
        analysis_type: str = "pre_event",
        user_info: Dict = None,
        personalization: Dict = None,
    ) -> GPTAnalysisResult:
        """
        Generate comprehensive GPT analysis for macro events with data validation
        
        Args:
            event: Economic event data (will be validated)
            market_context: Enhanced market context with positioning data
            analysis_type: "pre_event" or "post_event"
            user_info: Optional dict with user_id, user_email, user_name for OpenAI usage tracking
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
            cached_result = self._get_cached_analysis(cache_key, analysis_type)
            
            if cached_result:
                # Track user even for cached results (for internal analytics)
                # Note: Cached results don't make OpenAI API calls, so they won't appear in OpenAI usage dashboard
                # but we still track internally who requested them
                if user_info:
                    user_identifier = user_info.get('user_email') or user_info.get('user_id')
                    logger.info(f"✅ Cache hit for event {validated_event.get('id', 'unknown')} (requested by: {user_identifier})")
                    # Track cached usage
                    try:
                        from services.ai_usage_tracker import ai_usage_tracker
                        ai_usage_tracker.track_analysis_usage(
                            user_info=user_info,
                            analysis_type=analysis_type,
                            event_id=validated_event.get('id'),
                            model_used=cached_result.model_used,
                            cost_estimate=0.0,  # Cached = no cost
                            cache_hit=True
                        )
                    except Exception as e:
                        logger.debug(f"Usage tracking failed (non-critical): {e}")
                else:
                    logger.info(f"✅ Cache hit for event {validated_event.get('id', 'unknown')} (anonymous)")
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
                validated_event,
                enhanced_market_context,
                analysis_type,
                model,
                user_info=user_info,
                personalization=personalization,
            )
            
            # Step 8: Add data quality information (do not label fallback as "validated")
            if (analysis_result.model_used or "").startswith("enhanced_fallback"):
                analysis_result.data_quality = "fallback"
                analysis_result.validation_status = "passed"
            else:
                analysis_result.data_quality = "validated"
                analysis_result.validation_status = "passed"
            analysis_result.market_data_source = live_market_data.get('data_source', 'unknown')
            
            # Step 9: Cache the result
            self._cache_analysis(cache_key, analysis_result, analysis_type)
            
            # Step 10: Track usage for analytics
            if user_info:
                try:
                    from services.ai_usage_tracker import ai_usage_tracker
                    ai_usage_tracker.track_analysis_usage(
                        user_info=user_info,
                        analysis_type=analysis_type,
                        event_id=validated_event.get('id'),
                        model_used=model,
                        cost_estimate=analysis_result.cost_estimate,
                        cache_hit=False
                    )
                except Exception as e:
                    logger.debug(f"Usage tracking failed (non-critical): {e}")
            
            # Step 11: Update rate limiting
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
            # Only use real, accurate data - ignore None values (inaccurate/estimated data)
            current_prices = live_data.get('current_prices') or original_context.current_prices
            recent_volatility = live_data.get('recent_volatility') or original_context.recent_volatility
            market_sentiment = live_data.get('market_sentiment') or original_context.market_sentiment
            
            # Key levels - use None if not available (inaccurate calculations removed)
            key_levels = live_data.get('key_levels') if live_data.get('key_levels') is not None else original_context.key_levels
            
            # Positioning data - keep as None if not available (estimated data removed)
            retail_sentiment = live_data.get('retail_sentiment') if live_data.get('retail_sentiment') is not None else original_context.retail_sentiment
            futures_positioning = live_data.get('futures_positioning') if live_data.get('futures_positioning') is not None else original_context.futures_positioning
            institutional_flow = live_data.get('institutional_flow') if live_data.get('institutional_flow') is not None else original_context.institutional_flow
            
            # Cross-market data - keep as None if not available (fallback values removed)
            bond_yields = live_data.get('bond_yields') if live_data.get('bond_yields') is not None else original_context.bond_yields
            equity_indices = live_data.get('equity_indices') if live_data.get('equity_indices') is not None else original_context.equity_indices
            commodity_prices = live_data.get('commodity_prices') if live_data.get('commodity_prices') is not None else original_context.commodity_prices
            
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
            headline=f"Data Quality Issue - {event.get('title', 'Unknown Event')}",
            key_takeaway="Event data validation failed - analysis may be unreliable due to data quality issues.",
            forward_scenarios={
                "bullish": "Cannot provide reliable scenarios due to data validation issues",
                "bearish": "Cannot provide reliable scenarios due to data validation issues",
                "neutral": "Cannot provide reliable scenarios due to data validation issues"
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
        # Include PROMPT_VERSION + model so prompt/model changes invalidate cached analyses.
        model_id = select_model_for_event(event)
        event_data = (
            f"{PROMPT_VERSION}_{model_id}_{event.get('id', '')}_"
            f"{event.get('title', '')}_{analysis_type}"
        )
        return hashlib.md5(event_data.encode()).hexdigest()
    
    def _get_cached_analysis(self, cache_key: str, analysis_type: str) -> Optional[GPTAnalysisResult]:
        """Get cached analysis if available"""
        try:
            # Cache for 1 hour for pre-event, 24 hours for post-event
            analysis_type_norm = (analysis_type or "").lower().replace("-", "_")
            is_pre_event = analysis_type_norm.startswith("pre")
            cache_duration = 3600 if is_pre_event else 86400

            if self.redis_client:
                cached_data = self.redis_client.get(f"gpt_analysis:{cache_key}")
                if cached_data:
                    return pickle.loads(cached_data.encode('latin1'))
            else:
                # In-memory cache
                if cache_key in self.memory_cache:
                    timestamp = self.cache_timestamps.get(cache_key, 0)
                    if time.time() - timestamp < cache_duration:
                        return self.memory_cache[cache_key]
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None
    
    def _cache_analysis(self, cache_key: str, analysis: GPTAnalysisResult, analysis_type: str):
        """Cache analysis result"""
        try:
            analysis_type_norm = (analysis_type or "").lower().replace("-", "_")
            is_pre_event = analysis_type_norm.startswith("pre")
            cache_duration = 3600 if is_pre_event else 86400

            if self.redis_client:
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
                "neutral": f"Balanced Tone: {speaker} maintains neutral stance. Range-bound trading in {currency} pairs with limited directional moves."
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
            headline=f"Non-Farm Payrolls Analysis - {bias} Bias Expected",
            key_takeaway=f"NFP data {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show employment trends'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"Strong NFP above {expected}: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"Weak NFP below {expected}: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"NFP in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
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
            headline=f"Consumer Price Index Analysis - {bias} Bias Expected",
            key_takeaway=f"CPI data {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show inflation trends'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"Strong CPI above {expected}: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"Weak CPI below {expected}: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"CPI in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
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
            headline=f"Interest Rate Decision Analysis - {bias} Bias Expected",
            key_takeaway=f"Interest rate decision {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show policy stance'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"Stronger than expected: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"Weaker than expected: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"In line with expectations: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
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
            headline=f"Gross Domestic Product Analysis - {bias} Bias Expected",
            key_takeaway=f"GDP data {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show economic growth'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"Strong GDP above {expected}: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"Weak GDP below {expected}: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"GDP in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
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
            headline=f"Unemployment Rate Analysis - {bias} Bias Expected",
            key_takeaway=f"Unemployment rate {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show labor market trends'} with {impact.lower()} USD impact.",
            forward_scenarios={
                "bullish": f"Lower than expected: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"Higher than expected: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"Unemployment rate in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
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
            headline_text = f"{event_title} - Market Impact Analysis"
            takeaway_text = data_note
        else:
            headline_text = f"{event_title} - {bias} Bias Expected"
            takeaway_text = f"Economic data {('came in ' + bias.lower() + ' vs expectations') if is_post_event else 'expected to show economic trends'} with {impact_str.lower()} {currency} impact."
        
        return GPTAnalysisResult(
            headline=headline_text,
            key_takeaway=takeaway_text,
            forward_scenarios={
                "bullish": f"Stronger than expected: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0",
                "bearish": f"Weaker than expected: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0",
                "neutral": f"Economic data in line with {expected}: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0"
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
        """Select appropriate GPT model based on event characteristics."""
        return select_model_for_event(event)
    
    def _get_error_fallback(self, event: Dict, analysis_type: str = "pre_event") -> GPTAnalysisResult:
        """Generate fallback analysis when GPT API fails"""
        return self._get_fallback_analysis(event, analysis_type)
    
    def _generate_enhanced_gpt_analysis(
        self,
        event: Dict,
        market_context: MarketContext,
        analysis_type: str,
        model: str,
        user_info: Dict = None,
        personalization: Dict = None,
    ) -> GPTAnalysisResult:
        """Generate enhanced GPT analysis with real API calls"""
        try:
            if not self.client:
                logger.warning("OpenAI client not available, using fallback")
                return self._get_fallback_analysis(event, analysis_type)
            
            # Prepare the prompt for GPT
            prompt = self._create_analysis_prompt(
                event,
                market_context,
                analysis_type,
                personalization=personalization,
                user_info=user_info,
            )
            
            # Prepare user identifier for OpenAI usage tracking
            # Use email if available, otherwise user_id, otherwise None
            openai_user = None
            if user_info:
                openai_user = user_info.get('user_email') or user_info.get('user_id')
                if openai_user:
                    logger.info(f"👤 Tracking OpenAI usage for user: {openai_user}")
                    print(f"👤👤👤 OPENAI USER TRACKING: {openai_user} 👤👤👤")
                else:
                    logger.warning(f"⚠️ User info provided but no email or user_id: {user_info}")
                    print(f"⚠️⚠️⚠️ NO USER IDENTIFIER IN USER_INFO: {user_info} ⚠️⚠️⚠️")
            else:
                logger.warning("⚠️ No user_info provided to OpenAI API call")
                print(f"⚠️⚠️⚠️ NO USER_INFO PROVIDED TO OPENAI API CALL ⚠️⚠️⚠️")
            
            # Prepare API call parameters
            api_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a professional forex market analyst with deep expertise in economic events and their market impact."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            }
            
            # Add user parameter for OpenAI usage tracking if available
            if openai_user:
                api_params["user"] = openai_user
                logger.info(f"✅ Adding 'user' parameter to OpenAI API call: {openai_user}")
                print(f"✅✅✅ ADDING USER PARAMETER TO OPENAI: {openai_user} ✅✅✅")
            else:
                logger.warning("⚠️ NOT adding 'user' parameter to OpenAI API call - no user identifier")
                print(f"❌❌❌ NOT ADDING USER PARAMETER TO OPENAI API CALL ❌❌❌")
            
            # Make API call to OpenAI
            logger.info(f"🚀 Making OpenAI API call with params: model={model}, user={openai_user or 'None'}")
            print(f"🚀🚀🚀 OPENAI API CALL - Model: {model}, User: {openai_user or 'None'} 🚀🚀🚀")
            response = self.client.chat.completions.create(**api_params)
            
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
    
    def _get_trading_sessions(self) -> Dict[str, Any]:
        """Get current trading session information"""
        try:
            from datetime import datetime, timezone
            
            now = datetime.now(timezone.utc)
            utc_hour = now.hour
            utc_day = now.weekday()  # 0=Monday, 6=Sunday
            
            # Check if weekend
            is_weekend = utc_day >= 5  # Saturday (5) or Sunday (6)
            
            # Check for major holidays
            utc_month = now.month
            utc_date = now.day
            is_holiday = (
                (utc_month == 1 and utc_date == 1) or  # New Year's Day
                (utc_month == 12 and utc_date == 25) or  # Christmas Day
                (utc_month == 12 and utc_date == 26)  # Boxing Day
            )
            
            if is_weekend or is_holiday:
                return {
                    'active_sessions': [],
                    'market_status': 'closed',
                    'volatility_implication': 'Markets closed - no trading activity'
                }
            
            # Trading session times (UTC)
            sessions = [
                {'name': 'Sydney', 'start': 22, 'end': 7},
                {'name': 'Tokyo', 'start': 0, 'end': 9},
                {'name': 'London', 'start': 8, 'end': 17},
                {'name': 'New York', 'start': 13, 'end': 22}
            ]
            
            active_sessions = []
            for session in sessions:
                if session['start'] <= session['end']:
                    # Same day session
                    is_active = session['start'] <= utc_hour < session['end']
                else:
                    # Overnight session
                    is_active = utc_hour >= session['start'] or utc_hour < session['end']
                
                if is_active:
                    active_sessions.append(session['name'])
            
            # Determine volatility implications
            volatility_implication = "Normal trading hours"
            if len(active_sessions) == 0:
                volatility_implication = "Markets closed - no trading activity"
            elif len(active_sessions) == 1:
                session_name = active_sessions[0]
                if session_name in ['London', 'New York']:
                    volatility_implication = f"{session_name} session active - typically higher volatility"
                else:
                    volatility_implication = f"{session_name} session active - typically lower volatility"
            elif len(active_sessions) >= 2:
                if 'London' in active_sessions and 'New York' in active_sessions:
                    volatility_implication = "London-NY overlap - highest volatility period (peak liquidity)"
                elif 'Tokyo' in active_sessions and 'London' in active_sessions:
                    volatility_implication = "Tokyo-London overlap - moderate to high volatility"
                else:
                    volatility_implication = "Multiple sessions active - moderate volatility"
            
            return {
                'active_sessions': active_sessions,
                'market_status': 'open' if active_sessions else 'closed',
                'volatility_implication': volatility_implication,
                'current_time_utc': now.strftime('%Y-%m-%d %H:%M UTC')
            }
        except Exception as e:
            logger.warning(f"Error getting trading sessions: {e}")
            return {
                'active_sessions': [],
                'market_status': 'unknown',
                'volatility_implication': 'Unable to determine session status'
            }
    
    def _get_top_3_pairs_for_currency(self, currency: str, event: Dict) -> List[str]:
        """Get the 3 most important currency pairs affected by the event"""
        # Priority order for pairs based on liquidity and importance
        currency_priority_map = {
            'USD': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
            'EUR': ['EUR/USD', 'EUR/GBP', 'EUR/JPY'],
            'GBP': ['GBP/USD', 'EUR/GBP', 'GBP/JPY'],
            'JPY': ['USD/JPY', 'EUR/JPY', 'GBP/JPY'],
            'AUD': ['AUD/USD', 'AUD/JPY', 'EUR/AUD'],
            'CAD': ['USD/CAD', 'EUR/CAD', 'GBP/CAD'],
            'CHF': ['USD/CHF', 'EUR/CHF', 'GBP/CHF'],
            'NZD': ['NZD/USD', 'NZD/JPY', 'AUD/NZD']
        }
        
        # First, try to get pairs from event
        event_pairs = event.get('currencyPairs', [])
        if event_pairs and isinstance(event_pairs, list) and len(event_pairs) > 0:
            # Take first 3 pairs from event
            return event_pairs[:3]
        
        # Otherwise, use priority map
        return currency_priority_map.get(currency.upper(), ['EUR/USD', 'USD/JPY', 'GBP/USD'])[:3]
    
    def _normalize_pair_format(self, pair: str) -> str:
        """Normalize pair format: EUR/USD -> EURUSD"""
        return pair.replace('/', '').upper()
    
    def _get_pairs_sentiment_data(self, currency: str, event: Dict, market_context: MarketContext) -> List[Dict[str, Any]]:
        """Get sentiment data for the 3 most important pairs affected by the event"""
        try:
            from services.market_sentiment_service import market_sentiment_service
            
            # Get top 3 pairs
            top_pairs = self._get_top_3_pairs_for_currency(currency, event)
            
            # Get sentiment data
            sentiment_data = market_sentiment_service.get_market_sentiment()
            if not sentiment_data:
                return []
            
            pairs_sentiment = sentiment_data.get('pairs_sentiment', [])
            if not pairs_sentiment:
                return []
            
            # Extract sentiment for our top pairs
            result = []
            for pair_with_slash in top_pairs:
                pair_normalized = self._normalize_pair_format(pair_with_slash)
                
                # Find sentiment for this pair
                pair_sentiment = next(
                    (p for p in pairs_sentiment if p.get('pair', '').upper() == pair_normalized),
                    None
                )
                
                if pair_sentiment:
                    # Get daily change directly from TradingView data for accuracy
                    daily_change = pair_sentiment.get('price_change', 0)  # This is already daily change %
                    
                    # Try to get more accurate daily change from TradingView if available
                    try:
                        from app import get_tradingview_prices
                        tradingview_data = get_tradingview_prices()
                        if tradingview_data and pair_normalized in tradingview_data:
                            tv_pair_data = tradingview_data[pair_normalized]
                            if 'changePercent' in tv_pair_data:
                                daily_change = tv_pair_data['changePercent']
                    except Exception as e:
                        logger.debug(f"Could not get TradingView changePercent for {pair_normalized}: {e}")
                        # Fall back to sentiment's price_change
                    
                    result.append({
                        'pair': pair_with_slash,
                        'sentiment': pair_sentiment.get('sentiment', 'neutral'),
                        'percentage': pair_sentiment.get('percentage', 50),
                        'daily_change': daily_change,  # Daily change percentage from TradingView
                        'rsi': pair_sentiment.get('rsi', 50),
                        'volatility': pair_sentiment.get('volatility', 0)
                    })
            
            return result
        except Exception as e:
            logger.warning(f"Error fetching pairs sentiment data: {e}")
            return []
    
    def _get_market_sentiment_data(self) -> Optional[Dict[str, Any]]:
        """Fetch market sentiment data (VIX, Risk Appetite) from market sentiment service"""
        try:
            from services.market_sentiment_service import market_sentiment_service
            
            sentiment_data = market_sentiment_service.get_market_sentiment()
            
            if not sentiment_data:
                return None
            
            # Extract VIX data
            vix_data = sentiment_data.get('vix')
            if not vix_data:
                # Try to extract from market conditions
                market_conditions = sentiment_data.get('market_conditions', [])
                volatility_condition = next(
                    (c for c in market_conditions if c.get('name') == 'Volatility Environment'),
                    None
                )
                if volatility_condition and volatility_condition.get('detail'):
                    # Parse VIX from detail string: "VIX: 15.0 (+0.0)"
                    import re
                    detail = volatility_condition.get('detail', '')
                    vix_match = re.match(r'VIX:\s*([\d.]+)\s*\(([+-]?[\d.]+)\)', detail)
                    if vix_match:
                        vix_data = {
                            'value': float(vix_match.group(1)),
                            'change': float(vix_match.group(2)),
                            'level': 'low' if float(vix_match.group(1)) < 15 else 'medium' if float(vix_match.group(1)) < 25 else 'high'
                        }
            
            # Extract Risk Appetite data
            risk_appetite_data = None
            market_conditions = sentiment_data.get('market_conditions', [])
            risk_appetite_condition = next(
                (c for c in market_conditions if c.get('name') == 'Risk Appetite'),
                None
            )
            if risk_appetite_condition:
                detail_raw = risk_appetite_condition.get('detail', '') or ''
                safe_havens = ''
                risk_fx = ''
                for part in detail_raw.split('·'):
                    p = part.strip()
                    pl = p.lower()
                    if pl.startswith('safe havens:'):
                        safe_havens = p.split(':', 1)[1].strip()
                    elif pl.startswith('risk fx:'):
                        risk_fx = p.split(':', 1)[1].strip()
                if not safe_havens and detail_raw:
                    safe_havens = detail_raw.replace('Safe Havens: ', '').replace('Safe havens: ', '').split('·')[0].strip()
                risk_appetite_data = {
                    'level': risk_appetite_condition.get('value'),  # 'low', 'medium', 'high'
                    'percentage': risk_appetite_condition.get('percentage'),  # 25, 50, 75
                    'safe_havens': safe_havens,
                    'risk_fx': risk_fx,
                    'trend': risk_appetite_condition.get('trend', 'stable')
                }
            
            return {
                'vix': vix_data,
                'risk_appetite': risk_appetite_data
            }
        except Exception as e:
            logger.warning(f"Error fetching market sentiment data: {e}")
            return None
    
    def _get_relevant_indicators(self, event_title: str, currency: Optional[str] = None) -> List[str]:
        """
        Get relevant indicator IDs based on event title and event currency (Approach 4).
        Uses currency-aware mapping so e.g. EUR inflation event -> 'inflation' (EUR), US -> 'inflation-YoY'.
        Only economies with context (USD, EUR, GBP, JPY) get indicators; others return [].
        
        Args:
            event_title: Title of the economic event (e.g. "CPI YoY", "Unemployment Rate")
            currency: Event currency (USD, EUR, GBP, JPY). If provided, mapping is per-economy.
        
        Returns:
            List of indicator IDs that exist for that economy, or empty list if no match or unsupported currency.
        """
        event_title_lower = event_title.lower()
        currency_key = (currency or '').upper()
        if currency_key in ('USD', 'EUR', 'GBP', 'JPY'):
            country = {'USD': 'US', 'EUR': 'EUR', 'GBP': 'GBP', 'JPY': 'JPY'}[currency_key]
            if country not in CONCEPT_TO_INDICATORS_BY_CURRENCY:
                return []
            by_currency = CONCEPT_TO_INDICATORS_BY_CURRENCY[country]
            concepts = set()
            for keyword, concept in TITLE_KEYWORD_TO_CONCEPT:
                if keyword in event_title_lower:
                    concepts.add(concept)
                    # Don't break: allow multiple concepts (e.g. "CPI and unemployment")
            relevant_indicators = []
            for c in concepts:
                relevant_indicators.extend(by_currency.get(c, []))
            seen = set()
            unique = []
            for ind in relevant_indicators:
                if ind not in seen:
                    seen.add(ind)
                    unique.append(ind)
            return unique
        
        # Fallback: no currency or unsupported currency - use legacy title-only mapping
        # (caller will still filter by economy_context_service so invalid IDs for that currency are dropped)
        for event_type, indicator_ids in EVENT_TYPE_MAPPING.items():
            if event_type in event_title_lower:
                out = list(indicator_ids)
                if 'interest-rate' not in out:
                    out.append('interest-rate')
                return out
        return []
    
    def _get_economy_context(self, currency: str, relevant_indicator_ids: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Get economy context for a currency (Approach 1)
        
        Args:
            currency: Currency code (USD, EUR, GBP, JPY)
            relevant_indicator_ids: Optional list of indicator IDs to filter (Approach 4)
        
        Returns:
            Dict with central bank rate and indicators, or None if not available
        """
        try:
            economy_context = economy_context_service.get_economy_context(currency)
            if not economy_context:
                return None
            
            # Filter indicators if relevant_indicator_ids provided (Approach 4)
            if relevant_indicator_ids:
                indicators = economy_context.get('indicators', {})
                filtered_indicators = {
                    ind_id: indicators[ind_id]
                    for ind_id in relevant_indicator_ids
                    if ind_id in indicators
                }
                economy_context['indicators'] = filtered_indicators
            
            return economy_context
            
        except Exception as e:
            logger.warning(f"Error getting economy context for {currency}: {e}")
            return None
    
    def _get_policy_pressure(self, currency: str, indicator_type: str, current_value: float) -> Optional[Dict]:
        """
        Calculate policy pressure based on deviation from central bank target (Approach 6)
        
        Args:
            currency: Currency code (USD, EUR, GBP, JPY)
            indicator_type: 'inflation' or 'unemployment'
            current_value: Current value of the indicator
        
        Returns:
            Dict with target, current, deviation, and pressure description, or None if not applicable
        """
        try:
            policy_targets = POLICY_TARGETS.get(currency.upper())
            if not policy_targets:
                return None
            
            target = policy_targets.get(indicator_type)
            if target is None:
                return None
            
            # Calculate deviation
            deviation = current_value - target
            deviation_percent = (deviation / target * 100) if target != 0 else 0
            
            # Determine pressure level
            if indicator_type == 'inflation':
                if deviation > 0.5:  # More than 0.5pp above target
                    pressure_level = 'strong hawkish pressure'
                elif deviation > 0.2:  # More than 0.2pp above target
                    pressure_level = 'moderate hawkish pressure'
                elif deviation < -0.5:  # More than 0.5pp below target
                    pressure_level = 'strong dovish pressure'
                elif deviation < -0.2:  # More than 0.2pp below target
                    pressure_level = 'moderate dovish pressure'
                else:
                    pressure_level = 'near target'
            else:  # unemployment
                if deviation > 0.5:  # More than 0.5pp above target
                    pressure_level = 'strong dovish pressure'
                elif deviation > 0.2:  # More than 0.2pp above target
                    pressure_level = 'moderate dovish pressure'
                elif deviation < -0.5:  # More than 0.5pp below target
                    pressure_level = 'strong hawkish pressure'
                elif deviation < -0.2:  # More than 0.2pp below target
                    pressure_level = 'moderate hawkish pressure'
                else:
                    pressure_level = 'near target'
            
            return {
                'target': target,
                'current': current_value,
                'deviation': deviation,
                'deviation_percent': deviation_percent,
                'pressure_level': pressure_level,
                'indicator_type': indicator_type,
                'central_bank': policy_targets.get('central_bank', '')
            }
            
        except Exception as e:
            logger.warning(f"Error calculating policy pressure for {currency} {indicator_type}: {e}")
            return None
    
    def _calculate_indicator_statistics(self, ind_data: Dict) -> Optional[Dict]:
        """
        Calculate statistical values from indicator chartData
        
        Args:
            ind_data: Indicator data dict with chartData array
        
        Returns:
            Dict with average, deviation, min, max, trend, or None if insufficient data
        """
        try:
            chart_data = ind_data.get('chartData', [])
            if not chart_data or len(chart_data) < 2:
                return None
            
            # Convert to float list (handle any string values)
            values = []
            for v in chart_data:
                try:
                    if isinstance(v, str):
                        # Remove % and other characters
                        v = float(v.replace('%', '').replace(',', '').strip())
                    else:
                        v = float(v)
                    values.append(v)
                except (ValueError, TypeError):
                    continue
            
            if len(values) < 2:
                return None
            
            # Calculate statistics
            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            
            # Calculate standard deviation
            variance = sum((x - avg) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            
            # Determine trend (comparing recent vs older values)
            if len(values) >= 6:
                recent_avg = sum(values[-6:]) / 6
                older_avg = sum(values[:-6]) / len(values[:-6]) if len(values) > 6 else avg
                if recent_avg > older_avg * 1.02:
                    trend = 'increasing'
                elif recent_avg < older_avg * 0.98:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                # Simple trend from first to last
                if values[-1] > values[0] * 1.02:
                    trend = 'increasing'
                elif values[-1] < values[0] * 0.98:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            
            # Current value position relative to average
            current_value_str = ind_data.get('currentValue', '')
            try:
                if isinstance(current_value_str, str):
                    current_value = float(current_value_str.replace('%', '').replace(',', '').strip())
                else:
                    current_value = float(current_value_str)
                
                deviation_from_avg = current_value - avg
                percent_from_avg = (deviation_from_avg / avg * 100) if avg != 0 else 0
                
                # Determine position
                if current_value > avg + std_dev:
                    position = 'above average'
                elif current_value < avg - std_dev:
                    position = 'below average'
                else:
                    position = 'near average'
            except (ValueError, TypeError):
                current_value = None
                deviation_from_avg = None
                percent_from_avg = None
                position = None
            
            return {
                'average': round(avg, 2),
                'min': round(min_val, 2),
                'max': round(max_val, 2),
                'std_deviation': round(std_dev, 2),
                'trend': trend,
                'current_value': round(current_value, 2) if current_value is not None else None,
                'deviation_from_avg': round(deviation_from_avg, 2) if deviation_from_avg is not None else None,
                'percent_from_avg': round(percent_from_avg, 1) if percent_from_avg is not None else None,
                'position': position,
                'range': f"{round(min_val, 2)} - {round(max_val, 2)}"
            }
        except Exception as e:
            logger.debug(f"Error calculating indicator statistics: {e}")
            return None
    
    def _format_economy_context_for_prompt(self, economy_context: Dict) -> str:
        """
        Format economy context for inclusion in GPT prompt
        
        Args:
            economy_context: Economy context dict from _get_economy_context
        
        Returns:
            Formatted string for prompt
        """
        lines = []
        currency = economy_context.get('currency', 'USD')
        
        # Central Bank Rate
        cbr = economy_context.get('central_bank_rate')
        if cbr:
            trend_str = f" (Trend: {cbr.get('trend', 'stable')})" if cbr.get('trend') else ""
            lines.append(f"- Central Bank Rate: {cbr.get('value', 'N/A')}%{trend_str}")
        
        # Indicators
        indicators = economy_context.get('indicators', {})
        
        # Format common indicators
        indicator_labels = {
            'interest-rate': 'Interest Rate',
            'inflation-YoY': 'CPI (YoY)',
            'core-inflation-YoY': 'Core CPI (YoY)',
            'gdp-growth': 'GDP Growth',
            'unemployment': 'Unemployment Rate',
            'nonfarm-payrolls': 'Non-Farm Payrolls'
        }
        
        for ind_id, ind_data in indicators.items():
            if not isinstance(ind_data, dict):
                continue
            
            current_value = ind_data.get('currentValue', 'N/A')
            # Remove % sign if present (we'll add it back if needed)
            if isinstance(current_value, str) and current_value.endswith('%'):
                current_value_display = current_value
                current_value_numeric = current_value[:-1]
            else:
                current_value_display = current_value
                current_value_numeric = current_value
            
            label = indicator_labels.get(ind_id, ind_id.replace('-', ' ').title())
            
            # Calculate statistics from chartData
            stats = self._calculate_indicator_statistics(ind_data)
            
            if stats:
                # Format with statistics
                stat_line = f"- Current {label}: {current_value_display}"
                stat_line += f" (Average: {stats['average']}, Range: {stats['range']}, Trend: {stats['trend']})"
                
                if stats['position']:
                    stat_line += f" - Position: {stats['position']}"
                    if stats['deviation_from_avg'] is not None:
                        stat_line += f" ({stats['deviation_from_avg']:+.2f} from avg, {stats['percent_from_avg']:+.1f}%)"
                
                lines.append(stat_line)
            else:
                # Fallback to simple format if no statistics available
                lines.append(f"- Current {label}: {current_value_display}")
        
        if not lines:
            return "No economy context available"
        
        return "\n".join(lines)
    
    def _add_policy_context_to_prompt(self, currency: str, economy_context: Dict, event_title: str) -> str:
        """
        Add policy target analysis to prompt (Approach 6)
        
        Args:
            currency: Currency code
            economy_context: Economy context dict
            event_title: Event title to determine if policy analysis is relevant
        
        Returns:
            Formatted policy analysis section, or empty string if not applicable
        """
        try:
            event_title_lower = event_title.lower()
            indicators = economy_context.get('indicators', {})
            
            policy_lines = []
            
            # Check if event is inflation/CPI related
            if any(keyword in event_title_lower for keyword in ['cpi', 'inflation', 'price']):
                # Get inflation indicator
                inflation_ind = indicators.get('inflation-YoY') or indicators.get('inflation')
                if inflation_ind:
                    current_value_str = inflation_ind.get('currentValue', '')
                    # Extract numeric value
                    try:
                        current_value = float(str(current_value_str).replace('%', '').strip())
                        policy_pressure = self._get_policy_pressure(currency, 'inflation', current_value)
                        if policy_pressure:
                            policy_lines.append(
                                f"Inflation Policy Pressure: {policy_pressure['pressure_level']}"
                            )
                            policy_lines.append(
                                f"  - Current: {policy_pressure['current']:.2f}%"
                            )
                            policy_lines.append(
                                f"  - Target: {policy_pressure['target']:.2f}%"
                            )
                            policy_lines.append(
                                f"  - Deviation: {policy_pressure['deviation']:+.2f}pp "
                                f"({policy_pressure['deviation_percent']:+.1f}%)"
                            )
                    except (ValueError, TypeError):
                        pass
            
            # Check if event is employment/unemployment related
            if any(keyword in event_title_lower for keyword in ['employment', 'unemployment', 'nfp', 'adp', 'payrolls', 'jobs']):
                # Get unemployment indicator
                unemployment_ind = indicators.get('unemployment')
                if unemployment_ind:
                    current_value_str = unemployment_ind.get('currentValue', '')
                    # Extract numeric value
                    try:
                        current_value = float(str(current_value_str).replace('%', '').strip())
                        policy_pressure = self._get_policy_pressure(currency, 'unemployment', current_value)
                        if policy_pressure:
                            policy_lines.append(
                                f"Unemployment Policy Pressure: {policy_pressure['pressure_level']}"
                            )
                            policy_lines.append(
                                f"  - Current: {policy_pressure['current']:.2f}%"
                            )
                            policy_lines.append(
                                f"  - Target: {policy_pressure['target']:.2f}%"
                            )
                            policy_lines.append(
                                f"  - Deviation: {policy_pressure['deviation']:+.2f}pp "
                                f"({policy_pressure['deviation_percent']:+.1f}%)"
                            )
                    except (ValueError, TypeError):
                        pass
            
            if not policy_lines:
                return ""
            
            return "POLICY TARGET ANALYSIS:\n" + "\n".join(policy_lines)
            
        except Exception as e:
            logger.warning(f"Error adding policy context to prompt: {e}")
            return ""
    
    def _create_analysis_prompt(
        self,
        event: Dict,
        market_context: MarketContext,
        analysis_type: str,
        personalization: Dict = None,
        user_info: Dict = None,
    ) -> str:
        """Create a comprehensive prompt for GPT analysis - only includes real, accurate data"""
        event_title = event.get('title', 'Unknown Event')
        currency = event.get('currency', 'USD')
        impact = event.get('impact', 'medium')
        previous = event.get('previous', 'N/A')
        # Handle both 'expected' and 'forecast' field names
        expected = event.get('expected') or event.get('forecast') or 'N/A'
        actual = event.get('actual', 'N/A')
        
        # Determine if this is pre-event or post-event analysis
        is_pre_event = actual in ['N/A', 'TBD', '', None] or actual == 'TBD'
        
        # Build market context section - only include real, accurate data (exclude None values)
        market_context_lines = []
        market_context_lines.append(f"- Current Prices: {market_context.current_prices}")
        market_context_lines.append(f"- Recent Volatility: {market_context.recent_volatility}")
        market_context_lines.append(f"- Market Sentiment: {market_context.market_sentiment}")
        
        # Only include data that is not None (real data, not inaccurate/estimated)
        if market_context.bond_yields is not None:
            market_context_lines.append(f"- Bond Yields: {market_context.bond_yields}")
        if market_context.equity_indices is not None:
            market_context_lines.append(f"- Equity Indices: {market_context.equity_indices}")
        if market_context.commodity_prices is not None:
            market_context_lines.append(f"- Commodity Prices: {market_context.commodity_prices}")
        if market_context.key_levels is not None:
            market_context_lines.append(f"- Key Technical Levels: {market_context.key_levels}")
        # Positioning data removed from prompt - no longer requested from GPT
        # if market_context.retail_sentiment is not None:
        #     market_context_lines.append(f"- Retail Sentiment: {market_context.retail_sentiment}")
        # if market_context.futures_positioning is not None:
        #     market_context_lines.append(f"- Futures Positioning: {market_context.futures_positioning}")
        # if market_context.institutional_flow is not None:
        #     market_context_lines.append(f"- Institutional Flow: {market_context.institutional_flow}")
        
        market_context_section = "\n".join(market_context_lines)
        
        # Get additional market context data
        trading_sessions = self._get_trading_sessions()
        sentiment_data = self._get_market_sentiment_data()
        pairs_sentiment = self._get_pairs_sentiment_data(currency, event, market_context)
        
        # Build additional context section
        additional_context_lines = []
        
        # Market Status Warning (if closed)
        if trading_sessions:
            market_status = trading_sessions.get('market_status', 'unknown')
            if market_status == 'closed':
                additional_context_lines.append(
                    "MARKET STATUS: Markets are currently CLOSED (weekend/holiday). "
                    "Any analysis should consider that trading will resume when markets reopen. "
                    "Price movements may be limited or non-existent until markets reopen."
                )
        
        # Trading Session Context
        if trading_sessions:
            active_sessions = trading_sessions.get('active_sessions', [])
            if active_sessions:
                additional_context_lines.append(f"- Active Trading Sessions: {', '.join(active_sessions)}")
                additional_context_lines.append(f"- Volatility Implication: {trading_sessions.get('volatility_implication', 'Normal trading hours')}")
        
        # VIX Fear Indicator
        if sentiment_data and sentiment_data.get('vix'):
            vix = sentiment_data['vix']
            additional_context_lines.append(
                f"- VIX Fear Indicator: {vix.get('value', 'N/A')} "
                f"({vix.get('change', 0):+.1f}, Level: {vix.get('level', 'unknown')})"
            )
        
        # Risk Appetite
        if sentiment_data and sentiment_data.get('risk_appetite'):
            risk = sentiment_data['risk_appetite']
            rline = (
                f"- Risk Appetite: {risk.get('level', 'unknown').upper()} "
                f"({risk.get('percentage', 0)}%) — Safe havens: {risk.get('safe_havens', 'None')}"
            )
            if risk.get('risk_fx'):
                rline += f" · Risk FX: {risk.get('risk_fx')}"
            additional_context_lines.append(rline)
        
        # Pairs Sentiment (Top 3 most important pairs) - Contextual, not deterministic
        if pairs_sentiment:
            additional_context_lines.append("\nRELEVANT FX PAIRS (Contextual, Not Deterministic):")
            for pair_data in pairs_sentiment:
                pair = pair_data['pair']
                sentiment = pair_data['sentiment'].upper()
                daily_change = pair_data['daily_change']
                rsi = pair_data['rsi']
                volatility = pair_data['volatility']
                
                additional_context_lines.append(
                    f"- {pair}: {sentiment} ({daily_change:+.2f}%), "
                    f"RSI: {rsi:.1f}, Volatility: {volatility:.2f}%"
                )
            additional_context_lines.append("\nNote: FX pair sentiment should inform bias, not override macroeconomic drivers.")
        
        additional_context_section = "\n".join(additional_context_lines) if additional_context_lines else "None available"

        focus_instruments = self._get_top_3_pairs_for_currency(currency, event)
        context_pack_enabled = is_analysis_context_pack_enabled()
        context_pack_section = ""
        if context_pack_enabled:
            user_id = (user_info or {}).get("user_id") if user_info else None
            _, context_pack_section = build_calendar_context_pack_section(
                event,
                analysis_type,
                user_id=user_id,
                token_user_info=user_info,
                focus_instruments=focus_instruments,
            )
            logger.info("Calendar analysis using AnalysisContextPack for: %s", event_title)
        else:
            preferred_instruments = []
            if personalization and isinstance(personalization, dict):
                preferred_instruments = personalization.get("primary_pairs") or []
            relevant_market_snapshot = build_relevant_market_context_block(
                currency=currency,
                text=event_title,
                focus_instruments=focus_instruments,
                preferred_instruments=preferred_instruments,
                limit=10,
                surface="calendar",
            )
            personalization_block = build_prompt_personalization_block(
                personalization, surface="economic_calendar"
            )
            context_pack_section = f"{relevant_market_snapshot}\n\n{personalization_block}".strip()
        
        # Get economy context (Approach 1, 4, 6) - use event currency so EUR gets 'inflation', US gets 'inflation-YoY', etc.
        relevant_indicator_ids = self._get_relevant_indicators(event_title, currency)

        # Only include economy context if we have relevant indicators (not for unmapped events)
        economy_context_section = ""
        if relevant_indicator_ids:  # Only proceed if event maps to indicators
            economy_context = self._get_economy_context(currency, relevant_indicator_ids)
            
            # Build economy context section
            if economy_context:
                economy_context_section = f"ECONOMIC CONTEXT FOR {currency}:\n{self._format_economy_context_for_prompt(economy_context)}"
                
                # Add policy target analysis (Approach 6)
                policy_context = self._add_policy_context_to_prompt(currency, economy_context, event_title)
                if policy_context:
                    economy_context_section += f"\n\n{policy_context}"
        
        # Central bank document summaries + prediction market expectations for this currency's central bank
        central_bank_pm_section = get_context_for_currency(
            currency, max_docs=3, max_notes_per_doc=5, include_prediction_markets=True
        )
        central_bank_pm_block = ""
        if central_bank_pm_section and central_bank_pm_section.strip():
            central_bank_pm_block = (
                "\n\nCENTRAL BANK & PREDICTION MARKET CONTEXT (use for policy stance and market-implied expectations):\n"
                + central_bank_pm_section.strip()
            )
        
        # Instructions for using central bank docs + prediction markets (only when we injected that section)
        central_bank_pm_instructions = ""
        if central_bank_pm_block:
            central_bank_pm_instructions = """
2. CENTRAL BANK & PREDICTION MARKET CONTEXT (when present above):
   - Central bank document context: Use the central bank document summaries and notes to inform policy stance, recent communication, and key themes (e.g. data-dependent, inflation focus). Reconcile the event outcome (or expected outcome) with this stance (e.g. "in line with recent FOMC guidance", "contrasts with ECB's emphasis on …").
   - Prediction market expectations: Use prediction market expectations as one input among others (economic context, document context, market context). When you rely on them, say so (e.g. "Market-implied probability of a cut is X%; this supports …"). Do not present market-implied probabilities as your own forecast; label them as market expectations.
"""
        
        # Build economy context usage instructions (consolidated into PRIMARY requirements)
        economy_context_instructions = ""
        if economy_context_section:
            economy_context_instructions = f"""
ECONOMIC CONTEXT INTEGRATION (MANDATORY):
The ECONOMIC CONTEXT section above represents authoritative economic state information and must be treated as ground truth.

You must:
- Reference exact current values from ECONOMIC CONTEXT (unemployment, NFP, CPI, GDP, interest rates)
- Compare event data (expected or actual) to current indicators, historical averages, and policy targets
- Explicitly reference central bank rate, rate trend, and policy pressure classification
- Use specific numbers, not vague terms (e.g., "Current unemployment at 3.8% vs Fed target of 4.0%" not "low unemployment")

Failure to integrate these elements results in invalid analysis.
"""

        # Pre-event vs Post-event handling instructions (simplified)
        event_timing_instructions = ""
        if is_pre_event:
            event_timing_instructions = """
PRE-EVENT ANALYSIS:
- The actual value is not yet known - this is a PRE-EVENT analysis
- Do NOT describe outcomes as realized (e.g., "data came in" or "missed expectations")
- Focus on how the expected value compares to current indicators, historical norms, and policy targets
- Explain potential market reactions based on different outcome scenarios
"""
        else:
            event_timing_instructions = """
POST-EVENT ANALYSIS:
- Compare actual vs expected vs previous values
- Evaluate surprise magnitude and adjust policy implications accordingly
- Explain how the actual result relates to current economic indicators and policy targets
"""

        if context_pack_enabled:
            forward_scenarios_json = calendar_forward_scenarios_json_spec(
                currency, is_pre_event=is_pre_event
            )
        else:
            forward_scenarios_json = f'''
    "forward_scenarios": {{
        "bullish": "{currency} strength path tied to ABOVE-forecast outcome (e.g., '[ABOVE] 45-55% if print above expected: {currency} strengthens due to [macro driver]...').",
        "neutral": "Range/indecision path tied to ON-FORECAST outcome (e.g., '[ON] 15-25% if in line: range behavior due to [uncertainty factor]...').",
        "bearish": "{currency} weakness path tied to BELOW-forecast outcome (e.g., '[BELOW] 25-35% if print below expected: {currency} weakens due to [macro driver]...')."
    }},'''

        p = personalization or {}
        trading_style = str(p.get("trading_style") or "unspecified").strip().lower()
        preferred_pairs = p.get("primary_pairs") or []
        preferred_pairs_csv = ", ".join(str(x) for x in preferred_pairs[:6]) if preferred_pairs else "none provided"
        if trading_style == "swing":
            style_rules = (
                "- Personalization mode: SWING. Give multi-week follow-through in big_picture fields; "
                "keep short-term notes as entry/noise filter rather than the main thesis."
            )
        elif trading_style == "day":
            style_rules = (
                "- Personalization mode: DAY. Prioritize immediate reaction, trigger/invalidation, and session timing "
                "in trading_plan and market_reaction."
            )
        else:
            style_rules = (
                "- Personalization mode: BALANCED. Keep both short-term and medium-term framing concise and clear."
            )
        personalization_requirements = f"""
7. PERSONALIZATION CASCADE:
   {style_rules}
   - Preferred pairs (if relevant): {preferred_pairs_csv}
   - Prioritize preferred pairs in scenarios/trading_plan when relevant to this event.
   - If preferred pairs are weakly related, state that explicitly and fall back to the most event-sensitive economy pairs.
"""

        prompt = f"""
You are a senior macroeconomic analyst specializing in foreign exchange markets, with deep expertise in economic indicators, central bank policy, and macro-to-FX transmission mechanisms.

Your task is to produce a professional, data-driven analysis of the following economic event, grounded strictly in the economic and market context provided. Avoid generic macro commentary. Where data is insufficient, explicitly state assumptions rather than fabricating precision.

EVENT DETAILS:
- Title: {event_title}
- Currency: {currency}
- Impact Level: {impact}
- Previous: {previous}
- Expected: {expected}
- Actual: {actual}
- Analysis Type: {analysis_type}

{economy_context_section}
{central_bank_pm_block}

MARKET CONTEXT:
{market_context_section}

ADDITIONAL MARKET CONTEXT:
{additional_context_section}

{context_pack_section}

PRIMARY ANALYSIS REQUIREMENTS (ENFORCED):

1. ECONOMIC CONTEXT INTEGRATION (Mandatory):
{economy_context_instructions}
{central_bank_pm_instructions}

3. FORWARD SCENARIO CONSTRUCTION:
   - Provide three scenarios with single integer probabilities that sum to exactly 100
   - For each scenario: include one integer probability prefix (e.g. "[ABOVE] 48%: ..."), reference macro driver, policy implication, expected FX reaction
   - Canonical key mapping is mandatory: `forward_scenarios.bullish` = ABOVE forecast path, `forward_scenarios.neutral` = ON-forecast path, `forward_scenarios.bearish` = BELOW forecast path.
   - Do not reinterpret keys as generic sentiment buckets. They are outcome buckets used by the Market Scenarios table.
   - Use price levels only if key levels are provided in MARKET CONTEXT, OR clearly state assumptions
{f"   - Scenarios are conditional surprise paths (beat/miss/inline), not a restatement of the latest economy scan regime{chr(10)}" if context_pack_enabled else ""}
4. VOLATILITY ASSESSMENT:
   - Must consider: trading sessions, event impact level, VIX regime, risk appetite
   - If markets are closed or liquidity is thin, explicitly state that volatility realization may be delayed

5. POLICY IMPLICATIONS:
   - Explain how the event influences policy trajectory
   - Whether current data reinforces, challenges, or complicates existing policy pressure
   - Avoid generic terms - use numbers and targets from ECONOMIC CONTEXT

6. TRADING INTELLIGENCE (Macro-First):
   - FX pairs most exposed to the macro outcome
   - Risk management considerations
   - Position sizing guidance relative to volatility
   - Strategies to avoid in uncertain conditions
   - FX pair sentiment should inform bias, not override macroeconomic drivers
   - trading_plan.best_approach MUST include at least one explicit If→then (trigger → FX outcome/level)
   - Do not use passive-only guidance ("monitor", "watch closely", "remain vigilant") without a linked trigger

{personalization_requirements}

8. ACTIONABLE TRIGGERS:
{ACTIONABLE_PROMPT_RULES}

{event_timing_instructions}

OUTPUT FORMAT (JSON):
{{
    "headline": "Compelling headline summarizing the key takeaway",
    "key_takeaway": "Main insight in 1-2 sentences",
    "analysis_confidence": "High | Medium | Low",
    "edge_confidence": "High | Medium | Low (same as analysis_confidence — your conviction in the directional read)",
    "edge_confidence_reason": "One sentence: why your edge is at this level for this release (required)",
    "assumptions": [
        "Only include if assumptions were required due to missing data (e.g., 'Assuming normal liquidity during London-NY overlap')"
    ],
    {forward_scenarios_json}
    "event_summary": {{
        "release": "Event description",
        "outcome": "{'What happened vs expectations (compare actual to expected and reference current economic indicators)' if not is_pre_event else 'Expected outcome analysis (compare expected value to current indicators and policy targets)'}",
        "previous": "{previous}",
        "expected": "{expected}",
        "actual": "{actual}"
    }},
    "market_reaction": {{
        "price_action": "Specific expected price action with currency pairs. Use price levels only if provided in MARKET CONTEXT, otherwise state assumptions clearly",
        "volatility": "Volatility expectations with reasoning (reference trading sessions, VIX, risk appetite). If markets closed or liquidity thin, state explicitly",
        "reason": "Why this reaction is expected (reference economic context, policy pressure, current indicators from ECONOMIC CONTEXT)"
    }},
    "implications_takeaways": {{
        "economic_context": "Economic implications - reference current indicator values, statistical context, and trends from ECONOMIC CONTEXT above",
        "policy_implications": "Central bank policy implications - reference current rate, trend, policy pressure, and targets from ECONOMIC CONTEXT above. Explain how event reinforces, challenges, or complicates existing policy pressure",
        "market_bias": "Start with exactly one label: BULLISH | BEARISH | NEUTRAL for {currency}, then concise reasoning based on macro drivers (not only technical indicators). Example: 'BEARISH for USD: ...'",
        "risk_level": "Risk assessment considering current economic conditions and policy environment"
    }},
    "trading_plan": {{
        "best_approach": "Recommended trading approach",
        "avoid_strategies": "Strategies to avoid",
        "key_levels": "Spot reference or illustrative zones only (no pivot/swing/support labels until structured OHLC exists). Prefix with 'Spot reference:' when using last trade/spot — e.g. 'Spot reference: EUR/USD ~1.0842'. Use 'Illustrative levels:' only when session is closed.",
        "position_sizing": "Position sizing recommendations",
        "next_catalysts": "Upcoming events to watch"
    }},
    "big_picture": {{
        "economic_outlook": "Economic outlook implications - reference current economic indicators, trends, and statistical context",
        "medium_term_direction": "Medium-term market direction based on economic trajectory and policy context (avoid repetition with market_bias)",
        "policy_trajectory": "Policy trajectory implications - reference current policy pressure, rate trends, and central bank targets",
        "forward_focus": "What to focus on going forward - specific indicators and data points to monitor"
    }},
    # Positioning context removed from prompt - no longer requested from GPT
    # "positioning_context": {{
    #     "retail_sentiment": "Retail trader sentiment (if available, otherwise state not available)",
    #     "institutional_flow": "Institutional flow analysis (if available, otherwise state not available)",
    #     "market_bias": "Overall market bias based on macro drivers (not just technical indicators)"
    # }},
    "next_catalysts": [
        "Upcoming event 1",
        "Upcoming event 2",
        "Upcoming event 3"
    ]
}}

REFERENCE THE CONTEXT YOU ARE GIVEN:
- When you make a point, tie it to the data provided. For example: cite the actual **ECONOMIC CONTEXT** numbers (e.g. "with unemployment at 3.8% and the Fed target at 4.0%"), refer to **CENTRAL BANK & PREDICTION MARKET CONTEXT** when discussing policy (e.g. "consistent with the FOMC's data-dependent stance" or "markets price a 65% chance of a cut"), and mention **MARKET CONTEXT** or **ADDITIONAL MARKET CONTEXT** when relevant (e.g. "with VIX at 15 and risk appetite high", "EUR/USD currently bullish on the day"). Do not write generic analysis that could apply to any event; anchor at least one or two concrete references per section to the context above.

SECONDARY QUALITY STANDARDS (GUIDANCE):
- Use quantitative language wherever possible, but do not fabricate precision when data is missing
- Avoid repeated phrasing across sections (market_bias, medium_term_direction, big_picture should be distinct)
- Do not over-weight RSI or short-term price action - prioritize macro → policy → FX transmission
- If certainty is low, state it explicitly in assumptions or analysis_confidence
- FX pair sentiment should inform bias, not override macroeconomic drivers

EMPHASIS (READABILITY):
- Wrap important short phrases in **double asterisks** so they render as bold for the reader. Use for: key levels (e.g. **1.0850**), surprise outcomes (**above consensus**), risk terms (**elevated volatility**), policy takeaways (**data-dependent**), and critical numbers or outcomes. One to three bold phrases per paragraph is enough; do not overuse.
- Example: "A print **above 3.2%** would reinforce **hawkish expectations** and likely lift the dollar."
- All text fields in the JSON (headline, key_takeaway, forward_scenarios, event_summary.outcome, market_reaction, implications_takeaways, trading_plan, big_picture) may contain ** for emphasis. Do not use other markdown or HTML.

HIGHLIGHTING REQUIREMENT (ENFORCED):
- You MUST include **bold emphasis** in the output (using **double asterisks**). If you do not, the output will be rejected.
- Minimum: include at least **10** bolded phrases across the whole JSON.
- Coverage: include at least **1** bolded phrase in each of these fields: `key_takeaway`, each `forward_scenarios` entry, `market_reaction.reason`, `implications_takeaways.policy_implications`, and `trading_plan.best_approach`.

CONTEXT-ANCHORING REQUIREMENT (ENFORCED):
- In each major section, explicitly cite at least one concrete input from the context above (a number, a named central bank stance/theme from the documents, a market-implied probability from prediction markets, or a market condition like VIX/risk appetite/pair move).
- At minimum, include concrete context references in: `event_summary.outcome`, `market_reaction.reason`, and `implications_takeaways.policy_implications`.
- If a required context item is missing (e.g. prediction markets not available), state that explicitly (e.g. \"Prediction markets unavailable\"), and anchor to other available context instead.
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
            
            # Normalize forward_scenarios to handle both old and new formats
            forward_scenarios = analysis_data.get('forward_scenarios', {})
            currency = event.get('currency', 'USD')
            
            # Convert new format to old format for backward compatibility
            normalized_scenarios = {}
            if forward_scenarios:
                # Check for new format (currency-specific)
                currency_upper = currency.upper()
                strength_key = f"{currency_upper}_strength_scenario"
                weakness_key = f"{currency_upper}_weakness_scenario"
                range_key = "range_or_indecision_scenario"
                
                if strength_key in forward_scenarios or weakness_key in forward_scenarios:
                    # New format - convert to old format for frontend compatibility
                    normalized_scenarios = {
                        'bullish': forward_scenarios.get(strength_key, forward_scenarios.get('bullish', '')),
                        'bearish': forward_scenarios.get(weakness_key, forward_scenarios.get('bearish', '')),
                        'neutral': forward_scenarios.get(range_key, forward_scenarios.get('neutral', ''))
                    }
                else:
                    # Old format - use as is
                    normalized_scenarios = forward_scenarios
            
            # Extract analysis_confidence if provided, otherwise use default
            analysis_confidence = analysis_data.get(
                'edge_confidence') or analysis_data.get('analysis_confidence', 'Medium')
            edge_confidence_reason = str(
                analysis_data.get('edge_confidence_reason') or ''
            ).strip()
            # Legacy numeric placeholder — finalize replaces with data_confidence_score
            confidence_map = {'High': 90.0, 'Medium': 75.0, 'Low': 60.0}
            confidence_score = confidence_map.get(str(analysis_confidence).title(), 75.0)

            assumptions = analysis_data.get('assumptions', [])
            
            return GPTAnalysisResult(
                headline=analysis_data.get('headline', f"Analysis for {event.get('title', 'Unknown Event')}"),
                key_takeaway=analysis_data.get('key_takeaway', 'Market analysis completed'),
                forward_scenarios=normalized_scenarios,
                event_summary=analysis_data.get('event_summary', {}),
                market_reaction=analysis_data.get('market_reaction', {}),
                implications_takeaways=analysis_data.get('implications_takeaways', {}),
                trading_plan=analysis_data.get('trading_plan', {}),
                big_picture=analysis_data.get('big_picture', {}),
                positioning_context=analysis_data.get('positioning_context', {}),
                next_catalysts=analysis_data.get('next_catalysts', []),
                confidence_score=confidence_score,
                analysis_confidence=str(analysis_confidence).title(),
                edge_confidence_reason=edge_confidence_reason,
                assumptions=list(assumptions) if isinstance(assumptions, list) else [],
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
        """Calculate cost estimate for API usage."""
        return estimate_cost_from_usage(usage, model)

# Global instance creation removed - let app.py create its own instance
