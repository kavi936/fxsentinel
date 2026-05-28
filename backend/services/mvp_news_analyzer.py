#!/usr/bin/env python3
"""
MVP News Analyzer for FXSentinel
Implements simplified two-paragraph analysis format with hybrid free/GPT analysis
"""

import json
import logging
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)
from services.analysis_personalization import (
    build_prompt_personalization_block,
    prioritize_instruments,
)
from services.relevant_market_context import build_relevant_market_context_block
from services.openai_model_config import (
    MODEL_COST_PER_1K_TOKENS,
    estimate_cost_from_usage,
    select_model_for_news,
)
from services.analysis_context_pack import (
    build_news_context_pack_section,
    is_analysis_context_pack_enabled,
)

@dataclass
class MVPAnalysisResult:
    """MVP analysis result with simplified format"""
    news_impact: str  # Paragraph 1: News impact summary
    trading_implications: str  # Paragraph 2: Trading implications
    immediate_reaction: str  # bullish_usd/bearish_usd/neutral
    key_pairs: List[str]
    volatility: str  # high/medium/low
    timeframe: str
    confidence: int
    analysis_type: str  # free_enhanced or gpt_enhanced
    risk_assessment: Optional[Dict[str, str]] = None
    market_context: Optional[Dict[str, List[str]]] = None
    cost: float = 0.0  # Cost of GPT API call in USD
    data_quality: str = "unknown"  # live_data, cached, fallback, unknown
    market_data_source: str = "unknown"  # TradingView, unknown

class MVPNewsAnalyzer:
    """MVP news analyzer with hybrid free/GPT analysis"""
    
    def __init__(self):
        self.sentiment_keywords = self._load_sentiment_keywords()
        self.political_keywords = self._load_political_keywords()
        self.source_credibility = self._load_source_credibility()
        
        # Cost tracking
        self.total_cost = 0.0
        self.cost_estimates = dict(MODEL_COST_PER_1K_TOKENS)
        
        # Rate limiting
        self.api_calls_this_hour = 0
        self.max_calls_per_hour = 50  # Conservative limit
        self.last_hour_reset = datetime.now()
        
        logger.info("✅ MVP News Analyzer initialized with cost tracking and rate limiting")
        
    def _load_sentiment_keywords(self) -> Dict[str, List[str]]:
        """Load sentiment keywords for analysis"""
        return {
            'positive': [
                'bullish', 'strong', 'higher', 'better', 'improved', 'growth', 'gain',
                'rise', 'increase', 'surge', 'rally', 'boost', 'positive', 'optimistic',
                'stronger', 'robust', 'healthy', 'expansion', 'recovery', 'outperform',
                'beat', 'exceed', 'above', 'surpass', 'accelerate', 'momentum'
            ],
            'negative': [
                'bearish', 'weak', 'lower', 'worse', 'decline', 'fall', 'drop',
                'plunge', 'crash', 'downturn', 'negative', 'pessimistic', 'weaker',
                'soft', 'sluggish', 'contraction', 'recession', 'underperform',
                'miss', 'below', 'disappoint', 'slowdown', 'stagnation', 'concern'
            ],
            'neutral': [
                'stable', 'steady', 'unchanged', 'flat', 'mixed', 'balanced',
                'moderate', 'gradual', 'slight', 'marginal', 'limited', 'contained'
            ]
        }
    
    def _load_political_keywords(self) -> Dict[str, List[str]]:
        """Load political risk keywords"""
        return {
            'trump': ['trump', 'donald', 'president'],
            'central_bank': ['fed', 'ecb', 'boe', 'boj', 'central bank'],
            'intervention': ['intervention', 'weaken', 'strengthen', 'currency'],
            'trade_policy': ['tariffs', 'trade war', 'trade deal']
        }
    
    def _load_source_credibility(self) -> Dict[str, float]:
        """Load source credibility scores"""
        return {
            'reuters': 0.95,
            'bloomberg': 0.95,
            'cnbc': 0.90,
            'marketwatch': 0.85,
            'financial times': 0.90,
            'wall street journal': 0.95,
            'watcherguru': 0.80
        }
    
    def should_use_gpt_analysis(self, news_item: Dict) -> bool:
        """Determine if news deserves GPT analysis - ENABLED: Use GPT for all news"""
        # ENABLED: Return True to use GPT analysis for all news items
        return True
        
        # Original logic (commented out for testing):
        # # Calculate impact score
        # impact_score = self._calculate_impact_score(news_item)
        # 
        # # Check for political content
        # has_political_content = self._has_political_content(news_item)
        # 
        # Check source credibility
        # source_credibility = self._get_source_credibility(news_item.get('source', ''))
        # 
        # # Check currency pair relevance
        # currency_pairs = news_item.get('currency_pairs', [])
        # has_major_pairs = any(pair in ['EUR/USD', 'USD/JPY', 'GBP/USD'] for pair in currency_pairs)
        # 
        # # Decision logic
        # if has_political_content or impact_score >= 0.8:
        #     return True
        # elif impact_score >= 0.6 and source_credibility >= 0.8:
        #     return True
        # else:
        #     return False
    
    def _calculate_impact_score(self, news_item: Dict) -> float:
        """Calculate news impact score (0.0 to 1.0)"""
        title = news_item.get('title', '').lower()
        summary = news_item.get('summary', '').lower()
        full_text = f"{title} {summary}"
        
        # High-impact keywords
        high_impact_keywords = [
            'cpi', 'inflation', 'fed', 'ecb', 'boe', 'boj', 'interest rate',
            'non-farm payrolls', 'gdp', 'trump', 'tariffs', 'trade war',
            'emergency', 'crisis', 'shock', 'surprise', 'intervention'
        ]
        
        # Medium-impact keywords
        medium_impact_keywords = [
            'retail sales', 'manufacturing', 'unemployment', 'employment',
            'trade balance', 'current account', 'housing', 'consumer confidence'
        ]
        
        # Count keywords
        high_impact_count = sum(1 for keyword in high_impact_keywords if keyword in full_text)
        medium_impact_count = sum(1 for keyword in medium_impact_keywords if keyword in full_text)
        
        # Calculate weighted score
        total_impact = (high_impact_count * 3) + (medium_impact_count * 2)
        
        if total_impact == 0:
            return 0.3  # Default medium-low impact
        
        # Normalize to 0-1 scale
        impact_score = min(1.0, total_impact / 10.0)
        return impact_score
    
    def _has_political_content(self, news_item: Dict) -> bool:
        """Check if news has political content"""
        title = news_item.get('title', '').lower()
        
        for category, keywords in self.political_keywords.items():
            if any(keyword in title for keyword in keywords):
                return True
        
        return False
    
    def _get_source_credibility(self, source: str) -> float:
        """Get source credibility score"""
        source_lower = source.lower()
        return self.source_credibility.get(source_lower, 0.5)
    
    def _calculate_cost_estimate(self, usage, model: str) -> float:
        """Calculate cost estimate for GPT API usage."""
        return estimate_cost_from_usage(usage, model)
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        
        # Reset counter if hour has passed
        if (now - self.last_hour_reset).total_seconds() > 3600:
            self.api_calls_this_hour = 0
            self.last_hour_reset = now
            logger.info("🔄 Rate limit counter reset")
        
        is_within_limit = self.api_calls_this_hour < self.max_calls_per_hour
        if not is_within_limit:
            logger.warning(f"⚠️ Rate limit reached: {self.api_calls_this_hour}/{self.max_calls_per_hour} calls this hour")
        
        return is_within_limit
    
    def _select_model(self, news_item: Dict) -> str:
        """Select appropriate GPT model based on news characteristics."""
        return select_model_for_news(news_item)
    
    def _get_enhanced_market_context(self) -> Dict[str, Any]:
        """Get enhanced market context from live market data service"""
        try:
            from services.live_market_data import live_market_data_service
            
            live_market_data = live_market_data_service.get_live_market_data()
            
            # Only use real data, ignore None values
            market_context = {
                'current_prices': live_market_data.get('current_prices') or {},
                'recent_volatility': live_market_data.get('recent_volatility') or {},
                'market_sentiment': live_market_data.get('market_sentiment') or {},
                'data_source': live_market_data.get('data_source', 'unknown'),
                'data_quality': live_market_data.get('data_quality', 'unknown')
            }
            
            logger.info(f"✅ Live market data retrieved from {market_context['data_source']}")
            return market_context
            
        except Exception as e:
            logger.warning(f"⚠️ Error getting live market data: {e}")
            return {
                'current_prices': {},
                'recent_volatility': {},
                'market_sentiment': {},
                'data_source': 'unknown',
                'data_quality': 'fallback'
            }
    
    def _get_trading_sessions(self) -> Dict[str, Any]:
        """Get current trading session information"""
        try:
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
    
    def _normalize_pair_format(self, pair: str) -> str:
        """Normalize pair format: EUR/USD -> EURUSD"""
        return pair.replace('/', '').upper()
    
    def _get_pairs_sentiment_data(self, currency_pairs: List[str]) -> List[Dict[str, Any]]:
        """Get sentiment data for currency pairs affected by the news"""
        try:
            from services.market_sentiment_service import market_sentiment_service
            
            # Get sentiment data
            sentiment_data = market_sentiment_service.get_market_sentiment()
            if not sentiment_data:
                return []
            
            pairs_sentiment = sentiment_data.get('pairs_sentiment', [])
            if not pairs_sentiment:
                return []
            
            # Extract sentiment for our pairs
            result = []
            for pair_with_slash in currency_pairs[:3]:  # Top 3 pairs
                pair_normalized = self._normalize_pair_format(pair_with_slash)
                
                # Find sentiment for this pair
                pair_sentiment = next(
                    (p for p in pairs_sentiment if p.get('pair', '').upper() == pair_normalized),
                    None
                )
                
                if pair_sentiment:
                    # Get daily change directly from sentiment data
                    daily_change = pair_sentiment.get('price_change', 0)
                    
                    result.append({
                        'pair': pair_with_slash,
                        'sentiment': pair_sentiment.get('sentiment', 'neutral'),
                        'percentage': pair_sentiment.get('percentage', 50),
                        'daily_change': daily_change,
                        'rsi': pair_sentiment.get('rsi', 50),
                        'volatility': pair_sentiment.get('volatility', 0)
                    })
            
            return result
        except Exception as e:
            logger.warning(f"Error fetching pairs sentiment data: {e}")
            return []
    
    def analyze_news(
        self,
        news_item: Dict,
        market_context: Optional[Dict] = None,
        user_info: Optional[Dict] = None,
        personalization: Optional[Dict] = None,
    ) -> MVPAnalysisResult:
        """Analyze news using hybrid approach
        
        Args:
            news_item: News item to analyze
            market_context: Optional market context data
            user_info: Optional dict with user_id, user_email, user_name for OpenAI usage tracking
        """
        try:
            # Determine analysis method
            should_use_gpt = self.should_use_gpt_analysis(news_item)
            print(f"🔍 Should use GPT analysis: {should_use_gpt}")
            
            if should_use_gpt:
                print(f"🔍 Attempting GPT analysis...")
                result = self._analyze_with_gpt(
                    news_item,
                    market_context,
                    user_info=user_info,
                    personalization=personalization,
                )
                print(f"🔍 GPT analysis completed, type: {result.analysis_type}")
                return result
            else:
                print(f"🔍 Using free analysis...")
                result = self._analyze_with_free(news_item)
                print(f"🔍 Free analysis completed, type: {result.analysis_type}")
                return result
                
        except Exception as e:
            logger.error(f"Error analyzing news: {e}")
            return self._get_fallback_analysis(news_item)
    
    def _analyze_with_free(self, news_item: Dict) -> MVPAnalysisResult:
        """Analyze news using free sentiment analysis"""
        title = news_item.get('title', '')
        summary = news_item.get('summary', '')
        source = news_item.get('source', '')
        
        print(f"🔍 Free analysis - Title: {title}")
        print(f"🔍 Free analysis - Summary: {summary}")
        print(f"🔍 Free analysis - Source: {source}")
        
        # Analyze sentiment with political context
        sentiment = self._analyze_sentiment_with_context(f"{title} {summary}", news_item)
        print(f"🔍 Free analysis - Sentiment: {sentiment}")
        
        # Generate news impact paragraph
        news_impact = self._generate_news_impact_paragraph(title, source, sentiment)
        print(f"🔍 Free analysis - News impact length: {len(news_impact)}")
        
        # Generate trading implications paragraph
        trading_implications = self._generate_trading_implications_paragraph(sentiment, news_item)
        print(f"🔍 Free analysis - Trading implications length: {len(trading_implications)}")
        
        # Get affected instruments (primary first, e.g. XAU/USD for gold news)
        affected_instruments = self._extract_affected_instruments(
            news_item.get('title', ''), news_item.get('summary', '')
        )
        if not affected_instruments:
            affected_instruments = ['EUR/USD', 'USD/JPY']
        result = MVPAnalysisResult(
            news_impact=news_impact,
            trading_implications=trading_implications,
            immediate_reaction=self._sentiment_to_reaction(sentiment),
            key_pairs=affected_instruments,
            volatility="medium",
            timeframe="1-24_hours",
            confidence=int(sentiment['confidence'] * 100),
            analysis_type="free_enhanced",
            risk_assessment={
                "market_volatility": "medium",
                "liquidity_impact": "medium",
                "correlation_risk": "medium"
            },
            market_context={
                "economic_factors": ["Market sentiment", "Economic uncertainty", "Policy implications"],
                "technical_levels": ["Key support and resistance levels", "Psychological price levels"],
                "sentiment_drivers": ["News sentiment", "Market positioning", "Risk appetite"]
            },
            cost=0.0,
            data_quality="free_analysis",
            market_data_source="unknown"
        )
        
        print(f"🔍 Free analysis - Result news_impact: {result.news_impact[:50]}...")
        print(f"🔍 Free analysis - Result trading_implications: {result.trading_implications[:50]}...")
        
        return result
    
    def _analyze_with_gpt(
        self,
        news_item: Dict,
        market_context: Optional[Dict] = None,
        user_info: Optional[Dict] = None,
        personalization: Optional[Dict] = None,
    ) -> MVPAnalysisResult:
        """Analyze news using GPT with enhanced prompts and live market data
        
        Args:
            news_item: News item to analyze
            market_context: Optional market context data
            user_info: Optional dict with user_id, user_email, user_name for OpenAI usage tracking
        """
        news_id = str(news_item.get('id', 'unknown'))
        news_title = news_item.get('title', 'Unknown')[:100]
        
        try:
            import openai
            import os
            
            logger.info(f"🔍 Starting GPT analysis for news: {news_title}")
            
            # Get API key
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("No OpenAI API key found, falling back to free analysis")
                return self._analyze_with_free(news_item)
            
            # Check rate limit
            if not self._check_rate_limit():
                logger.warning("Rate limit exceeded, falling back to free analysis")
                return self._analyze_with_free(news_item)
            
            # Select model based on impact
            model = self._select_model(news_item)
            logger.info(f"Selected model: {model} for news impact: {news_item.get('impact', 'medium')}")
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=api_key, timeout=30.0)
            
            # Get live market data
            market_data = self._get_enhanced_market_context()
            market_data_source = market_data.get('data_source', 'unknown')
            data_quality = market_data.get('data_quality', 'unknown')
            
            # Get additional market context
            trading_sessions = self._get_trading_sessions()
            sentiment_data = self._get_market_sentiment_data()
            
            # Extract affected instruments (commodities first when relevant, e.g. XAU/USD for gold news)
            title = news_item.get('title', '')
            summary = news_item.get('summary', '')
            source = news_item.get('source', '')
            affected_instruments = self._extract_affected_instruments(title, summary)
            preferred = (personalization or {}).get("primary_pairs") or []
            affected_instruments = prioritize_instruments(affected_instruments, preferred, limit=4)
            # Sentiment service has FX pairs only; pass through and it will skip unknowns like XAU/USD
            pairs_sentiment = self._get_pairs_sentiment_data(affected_instruments)
            
            # Build context pack section (Phase D) or fall back to legacy blocks
            context_pack_section = None
            if is_analysis_context_pack_enabled():
                user_id = (user_info or {}).get("user_id") if user_info else None
                _, context_pack_section = build_news_context_pack_section(
                    news_item,
                    user_id=user_id,
                    token_user_info=user_info,
                    focus_instruments=affected_instruments,
                )
                logger.info("Live news analysis using AnalysisContextPack for: %s", news_title)

            # Build enhanced prompt with live market data
            prompt = self._create_enhanced_prompt(
                news_item, affected_instruments, market_data, trading_sessions,
                sentiment_data, pairs_sentiment, personalization=personalization,
                context_pack_section=context_pack_section,
            )
            
            # Prepare user identifier for OpenAI usage tracking
            # Use email if available, otherwise user_id, otherwise None
            openai_user = None
            if user_info:
                openai_user = user_info.get('user_email') or user_info.get('user_id')
                if openai_user:
                    logger.info(f"👤 Tracking OpenAI usage for user: {openai_user}")
            
            # Prepare API call parameters
            api_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a senior forex market analyst with 15+ years of experience. Your job is to provide professional, actionable market intelligence for forex traders."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            # Add user parameter for OpenAI usage tracking if available
            if openai_user:
                api_params["user"] = openai_user
            
            # Call GPT API
            logger.info(f"🔍 Calling GPT API with model: {model}")
            try:
                response = client.chat.completions.create(**api_params)
            except openai.RateLimitError as e:
                logger.error(f"OpenAI RateLimitError for news {news_id}: {e}")
                return self._analyze_with_free(news_item)
            except openai.APITimeoutError as e:
                logger.error(f"OpenAI APITimeoutError for news {news_id}: {e}")
                return self._analyze_with_free(news_item)
            except openai.AuthenticationError as e:
                logger.error(f"OpenAI AuthenticationError: {e}")
                return self._analyze_with_free(news_item)
            except openai.APIError as e:
                logger.error(f"OpenAI APIError for news {news_id}: {e}")
                return self._analyze_with_free(news_item)
            
            # Calculate cost
            cost = self._calculate_cost_estimate(response.usage, model)
            self.total_cost += cost
            logger.info(f"✅ GPT API call completed. Cost: ${cost:.4f}, Total cost: ${self.total_cost:.4f}")
            
            # Update rate limiting
            self.api_calls_this_hour += 1
            
            # Track usage for analytics
            if user_info:
                try:
                    from services.ai_usage_tracker import ai_usage_tracker
                    ai_usage_tracker.track_analysis_usage(
                        user_info=user_info,
                        analysis_type='news',
                        event_id=news_id,
                        model_used=model,
                        cost_estimate=cost,
                        cache_hit=False
                    )
                except Exception as e:
                    logger.debug(f"Usage tracking failed (non-critical): {e}")
            
            # Parse response
            content = response.choices[0].message.content
            logger.info(f"🔍 GPT response received, length: {len(content)}")
            
            try:
                # Try to extract JSON from response
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    gpt_result = json.loads(json_str)
                    logger.info("✅ JSON parsed successfully")
                else:
                    logger.error("No JSON found in GPT response")
                    raise ValueError("No JSON found in response")
                
                # Create MVP result with cost and data quality tracking
                immediate_reaction = self._enforce_reaction_consistency(
                    gpt_result.get('immediate_reaction', 'neutral'),
                    gpt_result.get('news_impact', ''),
                    gpt_result.get('trading_implications', ''),
                )
                result = MVPAnalysisResult(
                    news_impact=gpt_result.get('news_impact', ''),
                    trading_implications=gpt_result.get('trading_implications', ''),
                    immediate_reaction=immediate_reaction,
                    key_pairs=prioritize_instruments(
                        gpt_result.get('key_pairs', affected_instruments[:4] if affected_instruments else ['EUR/USD']),
                        (personalization or {}).get("primary_pairs") or [],
                        limit=4,
                    ),
                    volatility=gpt_result.get('volatility', 'medium'),
                    timeframe=gpt_result.get('timeframe', '1-24 hours'),
                    confidence=gpt_result.get('confidence', 75),
                    analysis_type='gpt_enhanced',
                    risk_assessment={
                        "market_volatility": gpt_result.get('volatility', 'medium'),
                        "liquidity_impact": "medium",
                        "correlation_risk": "medium"
                    },
                    market_context={
                        "economic_factors": ["Market sentiment", "Economic uncertainty", "Policy implications"],
                        "technical_levels": ["Key support and resistance levels", "Psychological price levels"],
                        "sentiment_drivers": ["News sentiment", "Market positioning", "Risk appetite"]
                    },
                    cost=cost,
                    data_quality=data_quality,
                    market_data_source=market_data_source
                )
                
                logger.info(f"✅ GPT analysis completed successfully for news: {news_title}")
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse GPT response for news {news_id}: {e}")
                logger.error(f"Raw response preview: {content[:500]}")
                logger.error(f"News title: {news_title}")
                # Fallback to free analysis
                return self._analyze_with_free(news_item)
                
        except Exception as e:
            logger.error(f"Unexpected error in GPT analysis for news {news_id}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback to free analysis
            return self._analyze_with_free(news_item)
    
    def _create_enhanced_prompt(
        self,
        news_item: Dict,
        affected_instruments: List[str],
        market_data: Dict,
        trading_sessions: Dict,
        sentiment_data: Optional[Dict],
        pairs_sentiment: List[Dict],
        personalization: Optional[Dict] = None,
        context_pack_section: Optional[str] = None,
    ) -> str:
        """Create enhanced prompt with live market data and context. affected_instruments has primary asset first (e.g. XAU/USD for gold news).

        When context_pack_section is provided (Phase D / ANALYSIS_CONTEXT_PACK_ENABLED=true),
        it replaces the legacy personalization + relevant_market_snapshot blocks so GPT receives
        the same shared context as the calendar surface.
        """
        title = news_item.get('title', '')
        summary = news_item.get('summary', '')
        source = news_item.get('source', '')
        
        # Build market context section
        market_context_lines = []
        if market_data.get('current_prices'):
            market_context_lines.append(f"- Current Prices: {market_data['current_prices']}")
        if market_data.get('recent_volatility'):
            market_context_lines.append(f"- Recent Volatility: {market_data['recent_volatility']}")
        if market_data.get('market_sentiment'):
            market_context_lines.append(f"- Market Sentiment: {market_data['market_sentiment']}")
        
        market_context_section = "\n".join(market_context_lines) if market_context_lines else "Limited market data available"
        
        # Build additional context section
        additional_context_lines = []
        
        # Market Status Warning (if closed)
        if trading_sessions.get('market_status') == 'closed':
            additional_context_lines.append(
                "MARKET STATUS: Markets are currently CLOSED (weekend/holiday). "
                "Any analysis should consider that trading will resume when markets reopen. "
                "Price movements may be limited or non-existent until markets reopen."
            )
        
        # Trading Session Context
        if trading_sessions.get('active_sessions'):
            active_sessions = trading_sessions['active_sessions']
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
        
        # Pairs/instruments sentiment (Contextual; only FX pairs have live sentiment data)
        if pairs_sentiment:
            additional_context_lines.append("\nRELEVANT FX INSTRUMENTS (Contextual, Not Deterministic):")
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
        
        additional_context_section = "\n".join(additional_context_lines) if additional_context_lines else "Limited additional context available"

        # When pack is enabled, it replaces legacy personalization + market snapshot blocks.
        # When pack is off, fall back to legacy blocks exactly as before.
        if context_pack_section:
            shared_context_block = context_pack_section
        else:
            personalization_block = build_prompt_personalization_block(personalization, surface="live_news")
            preferred_instruments = []
            if personalization and isinstance(personalization, dict):
                preferred_instruments = personalization.get("primary_pairs") or []
            relevant_market_snapshot = build_relevant_market_context_block(
                currency="USD",
                text=f"{title} {summary}",
                focus_instruments=affected_instruments,
                preferred_instruments=preferred_instruments,
                limit=10,
                surface="news",
            )
            shared_context_block = f"{relevant_market_snapshot}\n\n{personalization_block}".strip()

        phase_f_news_block = ""
        if context_pack_section:
            p = personalization or {}
            trading_style = str(p.get("trading_style") or "balanced").strip().lower()
            preferred_pairs = p.get("primary_pairs") or []
            preferred_pairs_csv = ", ".join(str(x) for x in preferred_pairs[:6]) if preferred_pairs else "none provided"
            style_line = (
                "SWING mode: emphasize multi-session follow-through and invalidation conditions."
                if trading_style == "swing"
                else "DAY mode: emphasize immediate triggers, session timing, and near-term risk controls."
                if trading_style == "day"
                else "BALANCED mode: provide both near-term reaction and follow-through context."
            )
            phase_f_news_block = """
PHASE F QUALITY (when ANALYSIS CONTEXT PACK is present — mandatory):
- In news_impact, state whether the headline aligns or challenges the prevailing short-term bias from the latest economy scan (if MACRO SNAPSHOT is present).
- Never write "macro snapshot" — use "latest economy scan" or "prevailing short-term bias".
- Cite at least one concrete pack input per paragraph (scan bias, VIX, pair move, geo flag, freshness).
- confidence reflects edge strength; trading_implications must mention what could negate the thesis.
- Do not repeat generic Fed/policy filler more than once.
- trading_implications MUST include at least one explicit If→then with the primary instrument (trigger → expected move / level / session).
- Replace passive-only phrases ("monitor", "watch closely", "remain vigilant") with a concrete conditional.
"""
            phase_f_news_block += f"""
PERSONALIZATION CASCADE (mandatory):
- {style_line}
- Preferred pairs: {preferred_pairs_csv}
- Lead with preferred pairs when relevant; if relevance is weak, state that explicitly.
"""

        prompt = f"""
You are a senior forex market analyst with 15+ years of experience. Your job is to provide professional, actionable market intelligence for forex traders.

NEWS TO ANALYZE:
Title: {title}
Summary: {summary}
Source: {source}
Affected instruments (primary first; use these in your analysis): {affected_instruments}

CURRENT MARKET CONTEXT (Live Data):
{market_context_section}

ADDITIONAL MARKET CONTEXT:
{additional_context_section}

{shared_context_block}
{phase_f_news_block}
ANALYSIS REQUIREMENTS:

1. **Market Impact Analysis** (2-3 sentences, 150-250 words):
   - Explain the specific market implications and sentiment
   - Focus on the PRIMARY AFFECTED INSTRUMENT(S) listed above (e.g. XAU/USD for gold news, not USD/JPY)
   - When the news is about gold/commodities, center your analysis on XAU/USD (gold) or the listed commodity; only mention FX pairs if directly relevant (e.g. dollar strength vs gold)
   - Include magnitude of expected impact (high/medium/low)
   - Reference current market context, trading sessions, and volatility conditions
   - Consider VIX level and risk appetite when relevant

2. **Trading Intelligence** (2-3 sentences, 150-250 words):
   - Provide actionable market intelligence (NOT trade recommendations)
   - Identify key levels to watch and market dynamics for the PRIMARY instrument(s)
   - For gold news, refer to XAU/USD and gold levels; do not default to USD/JPY or other FX unless the story is clearly about forex
   - Include timeframe expectations and volatility outlook
   - Reference active trading sessions and liquidity conditions

3. **Instrument-Specific Analysis**:
   - Focus on the first (primary) instrument in the list above (e.g. XAU/USD for gold headlines)
   - Use standard symbols: XAU/USD = gold, XAG/USD = silver; then any relevant FX pairs
   - Do not repeatedly reference USD/JPY when the news is about a different asset (e.g. gold)
   - Consider cross-market correlations and safe-haven flows when relevant

4. **Risk Context**:
   - Identify potential market risks and uncertainties
   - Explain what could amplify or dampen the impact
   - Consider political, economic, and technical factors
   - Reference VIX level and risk appetite when relevant

IMPORTANT GUIDELINES:
- Discuss the PRIMARY affected instrument first (e.g. XAU/USD for gold news); do not default to USD/JPY or EUR/USD when the headline is about another asset
- Be specific about the instruments that match the news (gold → XAU/USD, silver → XAG/USD, forex → pairs)
- Provide concrete market intelligence, not generic statements
- Focus on "what to watch" rather than "what to do"
- Include specific price levels and timeframes when relevant
- Include at least one "If [trigger] → then [outcome]" in trading_implications (instrument + level or session).
- Avoid generic phrases like "monitor for opportunities" unless paired with a concrete trigger
- Reference live market data when available (prices, volatility, sentiment)
- Consider trading session context (higher volatility during London-NY overlap)
- FX pair sentiment should inform bias, not override macroeconomic drivers

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no code blocks, no explanations outside the JSON.

RESPONSE FORMAT (JSON ONLY):
{{
    "news_impact": "Specific market impact explanation with currency focus. 2-3 sentences explaining implications, affected pairs, and impact magnitude. Reference current market context and trading sessions.",
    "trading_implications": "Actionable market intelligence and what to watch. 2-3 sentences identifying key levels, timeframes, and monitoring points. Reference volatility expectations and trading sessions.",
    "immediate_reaction": "bullish_usd|bearish_usd|neutral",
    "key_pairs": ["primary instrument first, e.g. XAU/USD or EUR/USD"],
    "volatility": "high|medium|low",
    "timeframe": "specific timeframe like 'next 2-4 hours' or 'London session'",
    "confidence": 85
}}

VALIDATION RULES:
- immediate_reaction: MUST be exactly "bullish_usd", "bearish_usd", or "neutral"
- volatility: MUST be exactly "high", "medium", or "low"
- confidence: Integer between 50-95
- key_pairs: Array of 1-4 instruments; MUST put the primary asset first (e.g. XAU/USD for gold news, not USD/JPY). Use XAU/USD for gold, XAG/USD for silver, then XXX/YYY for forex
- news_impact: String, 150-250 words, focus on the primary instrument. Wrap key levels, pairs, and critical outcomes in **double asterisks** for emphasis (same as calendar analysis). One to three per paragraph; no other markdown.
- trading_implications: String, 150-250 words, focus on the primary instrument. Use **double asterisks** for key levels, timeframes, and actionable phrases (one to three per paragraph).

EXAMPLE (gold news):
{{
    "news_impact": "Goldman Sachs' $5,400 gold forecast reflects strong central bank demand and Fed rate-cut expectations, supporting XAU/USD. Gold (XAU/USD) is the primary focus; upside risk from private diversification and options-driven volatility. Dollar weakness and real yields matter for gold more than USD/JPY in this context.",
    "trading_implications": "Focus on XAU/USD (gold): watch key resistance levels toward the forecast target and volatility around options expiry. Expect higher volatility as noted in the note. Fed cut expectations and central bank buying are the main drivers; monitor real yields and dollar index for gold direction.",
    "immediate_reaction": "neutral",
    "key_pairs": ["XAU/USD"],
    "volatility": "high",
    "timeframe": "through 2026 / near-term volatility as options activity rises",
    "confidence": 78
}}

EXAMPLE (forex news):
{{
    "news_impact": "Fed Chair Powell's hawkish comments suggest potential rate hikes ahead, creating bullish sentiment for USD. EUR/USD and GBP/USD are most affected, with expected downward pressure of 50-100 pips. London-NY session overlap expected to see highest volatility.",
    "trading_implications": "Monitor EUR/USD support at 1.0800 and GBP/USD at 1.2600 for potential breakdowns. Expect increased volatility during London session (next 2-4 hours). Watch USD/JPY for 149.00 resistance.",
    "immediate_reaction": "bullish_usd",
    "key_pairs": ["EUR/USD", "GBP/USD", "USD/JPY"],
    "volatility": "high",
    "timeframe": "next 2-4 hours",
    "confidence": 85
}}

Now analyze the news above and respond with ONLY the JSON object:
"""
        return prompt
    
    def _extract_commodity_instruments(self, title: str, summary: str) -> List[str]:
        """Extract commodity instruments when news is primarily about commodities (gold, silver).
        Returns e.g. ['XAU/USD'] for gold-focused news so analysis focuses on the primary asset."""
        text = f"{title} {summary}".lower()
        instruments = []
        # Gold: headline/summary clearly about gold (price, forecast, demand, etc.)
        gold_primary = ('gold' in text and any(
            w in text for w in ['forecast', 'price', 'target', 'rally', 'demand', 'central bank', 'bullion', 'xau']
        )) or 'gold price' in text or 'gold forecast' in text
        if gold_primary:
            instruments.append('XAU/USD')
        # Silver: only if explicitly about silver (and not just gold article mentioning silver)
        if 'silver' in text and ('price' in text or 'forecast' in text or 'xag' in text):
            if 'XAG/USD' not in instruments:
                instruments.append('XAG/USD')
        return instruments[:2]

    def _extract_currency_pairs(self, title: str, summary: str) -> List[str]:
        """Extract relevant currency pairs from news content (forex only)."""
        text = f"{title} {summary}".lower()
        pairs = []
        currency_mapping = {
            'euro': 'EUR/USD', 'eur': 'EUR/USD', 'ecb': 'EUR/USD',
            'dollar': 'USD/JPY', 'usd': 'USD/JPY', 'fed': 'USD/JPY',
            'pound': 'GBP/USD', 'gbp': 'GBP/USD', 'boe': 'GBP/USD',
            'yen': 'USD/JPY', 'jpy': 'USD/JPY', 'boj': 'USD/JPY',
            'franc': 'USD/CHF', 'chf': 'USD/CHF', 'snb': 'USD/CHF',
            'australian': 'AUD/USD', 'aud': 'AUD/USD', 'rba': 'AUD/USD',
            'canadian': 'USD/CAD', 'cad': 'USD/CAD', 'boc': 'USD/CAD',
            'new zealand': 'NZD/USD', 'nzd': 'NZD/USD', 'rbnz': 'NZD/USD'
        }
        for keyword, pair in currency_mapping.items():
            if keyword in text and pair not in pairs:
                pairs.append(pair)
        return pairs

    def _extract_affected_instruments(self, title: str, summary: str) -> List[str]:
        """Extract affected instruments with primary asset first. For commodity news (e.g. gold),
        returns XAU/USD first so analysis and UI refer to the correct asset instead of defaulting to USD/JPY."""
        commodities = self._extract_commodity_instruments(title, summary)
        fx_pairs = self._extract_currency_pairs(title, summary)
        if commodities:
            # Primary asset first; then add up to 2 FX pairs for context (e.g. dollar strength vs gold)
            seen = list(commodities)
            for p in fx_pairs:
                if p not in seen and len(seen) < 4:
                    seen.append(p)
            return seen[:4]
        if not fx_pairs:
            fx_pairs = ['EUR/USD', 'USD/JPY']
        return fx_pairs[:3]
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        text_lower = text.lower()
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        # Count sentiment keywords
        for word in self.sentiment_keywords['positive']:
            positive_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
        
        for word in self.sentiment_keywords['negative']:
            negative_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
        
        for word in self.sentiment_keywords['neutral']:
            neutral_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
        
        # Calculate sentiment
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return {'sentiment': 'neutral', 'confidence': 0.5}
        
        # Calculate confidence based on word count
        confidence = min(1.0, total_sentiment_words / 10.0)
        
        # Determine sentiment
        if positive_count > negative_count and positive_count > neutral_count:
            sentiment = 'positive'
        elif negative_count > positive_count and negative_count > neutral_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {'sentiment': sentiment, 'confidence': confidence}
    
    def _generate_news_impact_paragraph(self, title: str, source: str, sentiment: Dict) -> str:
        """Generate news impact paragraph"""
        sentiment_text = sentiment['sentiment']
        # Use affected instruments (e.g. XAU/USD for gold) so we don't default to FX only
        instruments = self._extract_affected_instruments(title, "")
        pairs_text = ', '.join(instruments[:2]) if instruments else 'EUR/USD, USD/JPY'
        
        if sentiment_text == 'positive':
            return f"{title} from {source} creates bullish sentiment for {pairs_text}. This news suggests strengthening fundamentals that may drive currency appreciation. The development increases probability of upward movements as markets price in improved economic conditions. Focus on {pairs_text} for maximum impact during the next trading session."
        elif sentiment_text == 'negative':
            return f"{title} from {source} creates bearish sentiment for {pairs_text}. This news suggests weakening fundamentals that may drive currency depreciation. The development increases probability of downward movements as markets price in economic challenges. Focus on {pairs_text} for maximum impact during the next trading session."
        else:
            return f"{title} from {source} has mixed implications for {pairs_text}. This news shows neutral sentiment with conflicting signals for affected currencies. The development maintains probability of sideways movements as markets await clearer directional signals. Monitor {pairs_text} for breakout opportunities during the next trading session."
    
    def _generate_trading_implications_paragraph(self, sentiment: Dict, news_item: Dict) -> str:
        """Generate trading implications paragraph"""
        sentiment_text = sentiment['sentiment']
        instruments = self._extract_affected_instruments(
            news_item.get('title', ''), news_item.get('summary', '')
        )
        pairs_text = ', '.join(instruments[:2]) if instruments else 'EUR/USD, USD/JPY'
        
        if sentiment_text == 'positive':
            return f"Focus on {pairs_text} for bullish momentum opportunities. Monitor key resistance levels and watch for breakout confirmations. Expect increased volatility during the next 2-4 hours as markets digest this news. Key levels to watch: current price +20 pips resistance, -15 pips support. Risk management crucial as sentiment-driven moves can be volatile."
        elif sentiment_text == 'negative':
            return f"Focus on {pairs_text} for bearish momentum opportunities. Monitor key support levels and watch for breakdown confirmations. Expect increased volatility during the next 2-4 hours as markets digest this news. Key levels to watch: current price -20 pips support, +15 pips resistance. Risk management crucial as sentiment-driven moves can be volatile."
        else:
            return f"Monitor {pairs_text} for breakout opportunities in either direction. Current neutral sentiment suggests range-bound trading until clearer signals emerge. Expect low to medium volatility during the next 2-4 hours. Key levels to watch: current price ±15 pips for potential breakout zones. Wait for confirmation before taking directional positions."
    
    def _sentiment_to_reaction(self, sentiment: Dict) -> str:
        """Convert sentiment to immediate reaction"""
        sentiment_text = sentiment['sentiment']
        
        if sentiment_text == 'positive':
            return 'bullish_usd'
        elif sentiment_text == 'negative':
            return 'bearish_usd'
        else:
            return 'neutral'

    def _infer_reaction_from_text(self, text: str) -> str:
        """Infer a directional lean from narrative text for consistency checks."""
        if not text:
            return "neutral"
        text_upper = text.upper()

        bearish_hits = [
            "BEARISH USD",
            "USD WEAK",
            "USD WEAKENS",
            "DOVISH FED",
            "DOWNWARD PRESSURE ON THE DOLLAR",
            "EUR/USD RALLY",
            "GBP/USD RALLY",
        ]
        bullish_hits = [
            "BULLISH USD",
            "USD STRONG",
            "USD STRENGTHENS",
            "HAWKISH FED",
            "DOWNWARD PRESSURE ON THE EURO",
            "EUR/USD LOWER",
            "GBP/USD LOWER",
        ]

        bearish = sum(1 for token in bearish_hits if token in text_upper)
        bullish = sum(1 for token in bullish_hits if token in text_upper)
        if bearish > bullish and bearish >= 1:
            return "bearish_usd"
        if bullish > bearish and bullish >= 1:
            return "bullish_usd"
        return "neutral"

    def _enforce_reaction_consistency(
        self,
        immediate_reaction: str,
        news_impact: str,
        trading_implications: str,
    ) -> str:
        """
        Keep immediate_reaction aligned with narrative lean.
        If body text implies a clear lean, do not allow a contradictory/neutral label.
        """
        value = str(immediate_reaction or "neutral").strip().lower()
        if value not in ("bullish_usd", "bearish_usd", "neutral"):
            value = "neutral"

        combined = f"{news_impact}\n{trading_implications}"
        inferred = self._infer_reaction_from_text(combined)
        if inferred in ("bullish_usd", "bearish_usd") and value != inferred:
            logger.info(
                "Adjusted immediate_reaction for consistency: %s -> %s",
                value,
                inferred,
            )
            return inferred
        return value
    
    def _analyze_sentiment_with_context(self, text: str, news_item: Dict) -> Dict[str, Any]:
        """Analyze sentiment with political context"""
        # First get basic sentiment
        basic_sentiment = self._analyze_sentiment(text)
        
        # Check for political context that might override basic sentiment
        title = news_item.get('title', '').lower()
        
        # Trump comments about dollar weakness = bearish USD
        if 'trump' in title and any(word in title for word in ['dollar', 'weak', 'intervention']):
            return {'sentiment': 'negative', 'confidence': max(basic_sentiment['confidence'], 0.7)}
        
        # Fed dovish comments = bearish USD
        if 'fed' in title and any(word in title for word in ['dovish', 'rate cuts', 'easing']):
            return {'sentiment': 'negative', 'confidence': max(basic_sentiment['confidence'], 0.7)}
        
        # Fed hawkish comments = bullish USD
        if 'fed' in title and any(word in title for word in ['hawkish', 'rate hikes', 'tightening']):
            return {'sentiment': 'positive', 'confidence': max(basic_sentiment['confidence'], 0.7)}
        
        # Currency intervention = bearish for intervened currency
        if 'intervention' in title:
            return {'sentiment': 'negative', 'confidence': max(basic_sentiment['confidence'], 0.7)}
        
        return basic_sentiment
    

    
    def _get_fallback_analysis(self, news_item: Dict) -> MVPAnalysisResult:
        """Get fallback analysis when analysis fails"""
        title = news_item.get('title', 'News Event')
        source = news_item.get('source', 'Unknown')
        instruments = self._extract_affected_instruments(title, news_item.get('summary', ''))
        if not instruments:
            instruments = ['EUR/USD', 'USD/JPY']
        pairs_text = ', '.join(instruments[:2])
        return MVPAnalysisResult(
            news_impact=f"{title} from {source} has mixed implications for {pairs_text}. This news shows neutral sentiment with conflicting signals for affected instruments. The development maintains probability of sideways movements as markets await clearer directional signals. Monitor {pairs_text} for breakout opportunities during the next trading session.",
            trading_implications=f"Monitor {pairs_text} for breakout opportunities in either direction. Current neutral sentiment suggests range-bound trading until clearer signals emerge. Expect low to medium volatility during the next 2-4 hours. Key levels to watch: current price ±15 pips for potential breakout zones. Wait for confirmation before taking directional positions.",
            immediate_reaction="neutral",
            key_pairs=instruments,
            volatility="low",
            timeframe="next 2-4 hours",
            confidence=50,
            analysis_type="free_enhanced",
            risk_assessment={
                "market_volatility": "low",
                "liquidity_impact": "medium",
                "correlation_risk": "medium"
            },
            market_context={
                "economic_factors": ["Market sentiment", "Economic uncertainty", "Policy implications"],
                "technical_levels": ["Key support and resistance levels", "Psychological price levels"],
                "sentiment_drivers": ["News sentiment", "Market positioning", "Risk appetite"]
            },
            cost=0.0,
            data_quality="fallback",
            market_data_source="unknown"
        )

# Create global instance
mvp_news_analyzer = MVPNewsAnalyzer()
