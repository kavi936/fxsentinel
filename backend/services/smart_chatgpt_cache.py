#!/usr/bin/env python3
"""
Smart ChatGPT Caching System
Optimizes API usage through intelligent multi-layer caching
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import redis
import os

logger = logging.getLogger(__name__)

class SmartChatGPTCache:
    """Intelligent caching system for ChatGPT API optimization"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.cache_timestamps = {}
        
        # Initialize Redis if available
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Redis cache connected for smart ChatGPT caching")
        except:
            logger.warning("⚠️ Redis not available, using in-memory cache")
            self.redis_client = None
        
        # Cache layers configuration
        self.cache_layers = {
            'exact_match': {
                'duration': 86400,  # 24 hours
                'description': 'Same event, same data = instant response'
            },
            'similar_events': {
                'duration': 604800,  # 1 week
                'description': 'Similar indicators, different data = modified response'
            },
            'currency_context': {
                'duration': 2592000,  # 1 month
                'description': 'Same currency, different event = reuse context'
            },
            'indicator_patterns': {
                'duration': 7776000,  # 3 months
                'description': 'Same indicator type = reuse analysis structure'
            },
            'economic_theory': {
                'duration': 15552000,  # 6 months
                'description': 'Fundamental relationships = long-term cache'
            }
        }
        
        # Cost tracking
        self.api_calls_saved = 0
        self.cost_saved = 0.0
        self.cache_hit_rates = {
            'exact_match': 0,
            'similar_events': 0,
            'currency_context': 0,
            'indicator_patterns': 0,
            'economic_theory': 0
        }
    
    def get_cached_analysis(self, event: Dict, analysis_type: str = "post_event") -> Optional[Dict]:
        """Try multiple cache layers to find existing analysis"""
        
        # Try exact match first (most specific)
        exact_result = self._get_exact_cache(event, analysis_type)
        if exact_result:
            self.cache_hit_rates['exact_match'] += 1
            self.api_calls_saved += 1
            self.cost_saved += 0.12  # Estimated GPT-4 cost
            logger.info(f"✅ Exact cache hit for {event.get('title', 'Unknown')}")
            return exact_result
        
        # Try similar event with data modification
        similar_result = self._get_similar_cache(event, analysis_type)
        if similar_result:
            self.cache_hit_rates['similar_events'] += 1
            self.api_calls_saved += 1
            self.cost_saved += 0.12
            logger.info(f"✅ Similar cache hit for {event.get('title', 'Unknown')}")
            return self._modify_for_new_data(similar_result, event)
        
        # Try indicator pattern with context injection
        pattern_result = self._get_pattern_cache(event, analysis_type)
        if pattern_result:
            self.cache_hit_rates['indicator_patterns'] += 1
            self.api_calls_saved += 1
            self.cost_saved += 0.12
            logger.info(f"✅ Pattern cache hit for {event.get('title', 'Unknown')}")
            return self._inject_event_specific_data(pattern_result, event)
        
        # Try currency context
        currency_result = self._get_currency_context_cache(event, analysis_type)
        if currency_result:
            self.cache_hit_rates['currency_context'] += 1
            logger.info(f"✅ Currency context cache hit for {event.get('currency', 'Unknown')}")
            return self._enhance_with_currency_context(currency_result, event)
        
        # No cache hit
        logger.info(f"❌ No cache hit for {event.get('title', 'Unknown')} - will call ChatGPT API")
        return None
    
    def cache_analysis(self, event: Dict, analysis: Dict, analysis_type: str = "post_event"):
        """Cache analysis at multiple levels for future use"""
        
        # Cache exact match
        self._cache_exact_analysis(event, analysis, analysis_type)
        
        # Cache similar event pattern
        self._cache_similar_pattern(event, analysis, analysis_type)
        
        # Cache indicator pattern
        self._cache_indicator_pattern(event, analysis, analysis_type)
        
        # Cache currency context
        self._cache_currency_context(event, analysis, analysis_type)
        
        logger.info(f"💾 Cached analysis for {event.get('title', 'Unknown')} at multiple levels")
    
    def _get_exact_cache(self, event: Dict, analysis_type: str) -> Optional[Dict]:
        """Get exact event match from cache"""
        cache_key = self._generate_exact_cache_key(event, analysis_type)
        return self._get_from_cache(cache_key, 'exact_match')
    
    def _get_similar_cache(self, event: Dict, analysis_type: str) -> Optional[Dict]:
        """Get similar event pattern from cache"""
        cache_key = self._generate_similar_cache_key(event, analysis_type)
        return self._get_from_cache(cache_key, 'similar_events')
    
    def _get_pattern_cache(self, event: Dict, analysis_type: str) -> Optional[Dict]:
        """Get indicator pattern from cache"""
        cache_key = self._generate_pattern_cache_key(event, analysis_type)
        return self._get_from_cache(cache_key, 'indicator_patterns')
    
    def _get_currency_context_cache(self, event: Dict, analysis_type: str) -> Optional[Dict]:
        """Get currency context from cache"""
        cache_key = self._generate_currency_context_key(event, analysis_type)
        return self._get_from_cache(cache_key, 'currency_context')
    
    def _generate_exact_cache_key(self, event: Dict, analysis_type: str) -> str:
        """Generate exact match cache key"""
        key_data = {
            'title': event.get('title', ''),
            'currency': event.get('currency', ''),
            'actual': event.get('actual', ''),
            'expected': event.get('expected', ''),
            'previous': event.get('previous', ''),
            'analysis_type': analysis_type
        }
        return f"exact_{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"
    
    def _generate_similar_cache_key(self, event: Dict, analysis_type: str) -> str:
        """Generate similar event cache key"""
        surprise_magnitude = self._calculate_surprise_magnitude(event)
        key_data = {
            'title': event.get('title', ''),
            'currency': event.get('currency', ''),
            'surprise_magnitude': surprise_magnitude,
            'analysis_type': analysis_type
        }
        return f"similar_{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"
    
    def _generate_pattern_cache_key(self, event: Dict, analysis_type: str) -> str:
        """Generate indicator pattern cache key"""
        indicator_type = self._classify_indicator(event.get('title', ''))
        key_data = {
            'indicator_type': indicator_type,
            'currency': event.get('currency', ''),
            'analysis_type': analysis_type
        }
        return f"pattern_{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"
    
    def _generate_currency_context_key(self, event: Dict, analysis_type: str) -> str:
        """Generate currency context cache key"""
        key_data = {
            'currency': event.get('currency', ''),
            'analysis_type': analysis_type
        }
        return f"currency_{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"
    
    def _calculate_surprise_magnitude(self, event: Dict) -> str:
        """Calculate surprise magnitude category"""
        try:
            actual = float(str(event.get('actual', '0')).replace('%', ''))
            expected = float(str(event.get('expected', '0')).replace('%', ''))
            surprise = abs(actual - expected)
            
            if surprise < 0.1:
                return 'minimal'
            elif surprise < 0.5:
                return 'small'
            elif surprise < 1.0:
                return 'medium'
            else:
                return 'large'
        except:
            return 'unknown'
    
    def _classify_indicator(self, title: str) -> str:
        """Classify economic indicator type"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['cpi', 'inflation', 'consumer price']):
            return 'inflation'
        elif any(word in title_lower for word in ['gdp', 'gross domestic product']):
            return 'gdp'
        elif any(word in title_lower for word in ['employment', 'unemployment', 'non-farm', 'nfp']):
            return 'employment'
        elif any(word in title_lower for word in ['interest rate', 'fed', 'ecb', 'boj', 'boe']):
            return 'interest_rate'
        elif any(word in title_lower for word in ['retail sales', 'consumer spending']):
            return 'retail_sales'
        elif any(word in title_lower for word in ['manufacturing', 'pmi', 'industrial']):
            return 'manufacturing'
        elif any(word in title_lower for word in ['trade balance', 'current account']):
            return 'trade'
        elif any(word in title_lower for word in ['housing', 'building permits']):
            return 'housing'
        else:
            return 'general'
    
    def _get_from_cache(self, cache_key: str, cache_type: str) -> Optional[Dict]:
        """Get data from cache (Redis or memory)"""
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # In-memory cache
                if cache_key in self.memory_cache:
                    timestamp = self.cache_timestamps.get(cache_key, 0)
                    cache_duration = self.cache_layers[cache_type]['duration']
                    if datetime.now().timestamp() - timestamp < cache_duration:
                        return self.memory_cache[cache_key]
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict, cache_type: str):
        """Save data to cache (Redis or memory)"""
        try:
            cache_duration = self.cache_layers[cache_type]['duration']
            
            if self.redis_client:
                self.redis_client.setex(cache_key, cache_duration, json.dumps(data))
            else:
                # In-memory cache
                self.memory_cache[cache_key] = data
                self.cache_timestamps[cache_key] = datetime.now().timestamp()
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def _cache_exact_analysis(self, event: Dict, analysis: Dict, analysis_type: str):
        """Cache exact event analysis"""
        cache_key = self._generate_exact_cache_key(event, analysis_type)
        self._save_to_cache(cache_key, analysis, 'exact_match')
    
    def _cache_similar_pattern(self, event: Dict, analysis: Dict, analysis_type: str):
        """Cache similar event pattern"""
        cache_key = self._generate_similar_cache_key(event, analysis_type)
        self._save_to_cache(cache_key, analysis, 'similar_events')
    
    def _cache_indicator_pattern(self, event: Dict, analysis: Dict, analysis_type: str):
        """Cache indicator pattern"""
        cache_key = self._generate_pattern_cache_key(event, analysis_type)
        self._save_to_cache(cache_key, analysis, 'indicator_patterns')
    
    def _cache_currency_context(self, event: Dict, analysis: Dict, analysis_type: str):
        """Cache currency context"""
        cache_key = self._generate_currency_context_key(event, analysis_type)
        self._save_to_cache(cache_key, analysis, 'currency_context')
    
    def _modify_for_new_data(self, cached_analysis: Dict, new_event: Dict) -> Dict:
        """Modify cached analysis for new event data"""
        # Create a copy of the cached analysis
        modified_analysis = cached_analysis.copy()
        
        # Update event-specific data
        modified_analysis['event_summary'] = {
            'release': new_event.get('title', 'Unknown'),
            'currency': new_event.get('currency', 'Unknown'),
            'actual': new_event.get('actual', 'N/A'),
            'expected': new_event.get('expected', 'N/A'),
            'previous': new_event.get('previous', 'N/A'),
            'surprise_magnitude': self._calculate_surprise_magnitude(new_event),
            'immediate_bias': self._calculate_bias(new_event)
        }
        
        # Update market reaction based on new data
        surprise_magnitude = self._calculate_surprise_magnitude(new_event)
        if surprise_magnitude == 'large':
            modified_analysis['market_reaction']['expected_movement'] = 'significant movement'
            modified_analysis['market_reaction']['volatility_forecast'] = 'high (20+ pips)'
        elif surprise_magnitude == 'medium':
            modified_analysis['market_reaction']['expected_movement'] = 'moderate movement'
            modified_analysis['market_reaction']['volatility_forecast'] = 'medium (10-20 pips)'
        else:
            modified_analysis['market_reaction']['expected_movement'] = 'range-bound'
            modified_analysis['market_reaction']['volatility_forecast'] = 'low (5-10 pips)'
        
        return modified_analysis
    
    def _inject_event_specific_data(self, pattern_analysis: Dict, event: Dict) -> Dict:
        """Inject event-specific data into pattern analysis"""
        # Use pattern analysis as base and add event-specific details
        analysis = pattern_analysis.copy()
        
        # Update with event-specific information
        analysis['event_summary'] = {
            'release': event.get('title', 'Unknown'),
            'currency': event.get('currency', 'Unknown'),
            'actual': event.get('actual', 'N/A'),
            'expected': event.get('expected', 'N/A'),
            'previous': event.get('previous', 'N/A'),
            'surprise_magnitude': self._calculate_surprise_magnitude(event),
            'immediate_bias': self._calculate_bias(event)
        }
        
        return analysis
    
    def _enhance_with_currency_context(self, currency_context: Dict, event: Dict) -> Dict:
        """Enhance analysis with currency-specific context"""
        # Use currency context as base and add event details
        analysis = currency_context.copy()
        
        # Add event-specific data
        analysis['event_summary'] = {
            'release': event.get('title', 'Unknown'),
            'currency': event.get('currency', 'Unknown'),
            'actual': event.get('actual', 'N/A'),
            'expected': event.get('expected', 'N/A'),
            'previous': event.get('previous', 'N/A'),
            'surprise_magnitude': self._calculate_surprise_magnitude(event),
            'immediate_bias': self._calculate_bias(event)
        }
        
        return analysis
    
    def _calculate_bias(self, event: Dict) -> str:
        """Calculate immediate bias based on event data"""
        try:
            actual = float(str(event.get('actual', '0')).replace('%', ''))
            expected = float(str(event.get('expected', '0')).replace('%', ''))
            
            if abs(actual - expected) < 0.01:
                return 'neutral'
            elif actual > expected:
                return 'bearish'  # Higher unemployment, inflation, etc. is bearish
            else:
                return 'bullish'  # Lower unemployment, inflation, etc. is bullish
        except:
            return 'neutral'
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_hits = sum(self.cache_hit_rates.values())
        total_requests = total_hits + self.api_calls_saved  # Approximate
        
        return {
            'cache_hit_rates': self.cache_hit_rates,
            'total_cache_hits': total_hits,
            'api_calls_saved': self.api_calls_saved,
            'cost_saved': round(self.cost_saved, 2),
            'cache_hit_percentage': round((total_hits / total_requests * 100) if total_requests > 0 else 0, 2),
            'cache_layers': self.cache_layers
        }
    
    def pre_cache_popular_events(self, events: List[Dict]):
        """Pre-cache popular events to improve hit rates"""
        logger.info(f"🔄 Pre-caching {len(events)} popular events")
        
        for event in events:
            # Create basic analysis structure for pre-caching
            basic_analysis = self._create_basic_analysis_structure(event)
            
            # Cache at pattern level
            self._cache_indicator_pattern(event, basic_analysis, 'post_event')
            
            # Cache currency context
            self._cache_currency_context(event, basic_analysis, 'post_event')
        
        logger.info(f"✅ Pre-cached {len(events)} events")

# Global instance
smart_cache = SmartChatGPTCache()
