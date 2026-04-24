#!/usr/bin/env python3
"""
Enhanced Forex Filtering System
Uses positive and negative keywords for better accuracy
Improved to exclude irrelevant news for forex traders
"""

import re
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

class EnhancedForexFilter:
    def __init__(self):
        # Positive keywords for broad market relevance (FX, crypto, indices, commodities, rates/macro)
        self.positive_keywords = [
            # Currency names and codes
            'forex', 'currency', 'fx', 'foreign exchange',
            'dollar', 'euro', 'yen', 'pound', 'franc', 'australian dollar', 'canadian dollar', 'kiwi',
            'usd', 'eur', 'jpy', 'gbp', 'chf', 'aud', 'cad', 'nzd',
            
            # Central banks
            'fed', 'federal reserve', 'ecb', 'european central bank', 'boj', 'bank of japan', 
            'boe', 'bank of england', 'rba', 'reserve bank of australia', 'boc', 'bank of canada',
            'snb', 'swiss national bank', 'rbnz', 'reserve bank of new zealand',
            
            # Economic indicators
            'cpi', 'consumer price index', 'inflation', 'deflation', 'interest rate', 'monetary policy',
            'non-farm payrolls', 'nfp', 'gdp', 'gross domestic product', 'retail sales', 'manufacturing',
            'services pmi', 'unemployment', 'employment', 'wages', 'trade balance', 'current account',
            'balance of payments', 'budget deficit', 'fiscal policy',
            
            # Currency pairs
            'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
            'eur/gbp', 'eur/jpy', 'gbp/jpy', 'eur/chf', 'gbp/chf', 'aud/jpy', 'cad/jpy',
            
            # Market terms
            'pip', 'spread', 'leverage', 'margin', 'liquidity', 'volatility', 'correlation',
            'support', 'resistance', 'breakout', 'consolidation', 'trend', 'momentum',
            
            # Economic events
            'rate decision', 'policy meeting', 'minutes', 'speech', 'testimony', 'hearing',
            'economic calendar', 'market hours', 'session', 'asian session', 'london session', 'ny session',
            
            # Political and geopolitical events (market moving)
            'trump', 'biden', 'president', 'election', 'campaign', 'politics', 'political',
            'congress', 'senate', 'house', 'legislation', 'bill', 'law', 'policy',
            'geopolitical', 'geopolitics', 'diplomatic', 'diplomacy', 'sanctions',
            'brics', 'venezuela', 'venezuelan', 'brazil', 'russia', 'russian', 'india', 'indian',
            'south africa', 'south african', 'attack', 'conflict', 'crisis', 'instability',
            
            # Trade and tariffs
            'trade', 'tariff', 'trade war', 'trade deal', 'trade agreement', 'trade deficit',
            'trade surplus', 'import', 'export', 'trade policy', 'trade relations',
            'china trade', 'us china', 'eu trade', 'brexit', 'trade negotiations',
            
            # Countries and regions (economic impact)
            'united states', 'us', 'usa', 'america', 'american',
            'united kingdom', 'uk', 'britain', 'british', 'england',
            'european union', 'eu', 'europe', 'european',
            'china', 'chinese', 'beijing',
            'japan', 'japanese', 'tokyo',
            'australia', 'australian', 'canberra',
            'canada', 'canadian', 'ottawa',
            'switzerland', 'swiss', 'bern',
            'new zealand', 'kiwi', 'wellington',
            
            # Market sentiment and risk
            'risk-off', 'risk-on', 'safe haven', 'flight to quality', 'market sentiment',
            'investor confidence', 'market volatility', 'market uncertainty', 'market fear',
            'dollar strength', 'dollar weakness', 'currency strength', 'currency weakness',

            # Crypto
            'crypto', 'cryptocurrency', 'bitcoin', 'ethereum', 'solana', 'xrp', 'altcoin',
            'stablecoin', 'defi', 'token', 'digital asset', 'crypto market',

            # Indices
            'index', 'indices', 's&p 500', 'sp 500', 'nasdaq 100', 'dow jones',
            'ftse', 'dax', 'nikkei', 'hang seng', 'stoxx', 'sensex',

            # Rates / fixed income / macro plumbing
            'bond yield', 'treasury yield', 'yield curve', '10-year', '2-year',
            'real yield', 'policy rate', 'benchmark rate'
        ]
        
        # Non-market negatives: always exclude
        self.negative_keywords = [
            # Real estate
            'real estate', 'property', 'mortgage', 'housing', 'home', 'apartment', 'rental',
            'commercial property', 'reit', 'construction', 'builder',
            'home sales', 'housing market', 'mortgage rates', 'property market',
            
            # Technology and innovation
            'artificial intelligence', 'ai', 'machine learning', 'automation',
            'startup', 'venture capital', 'tech company', 'software', 'app',
            'social media', 'internet', 'digital', 'online platform',
            
            # Entertainment and lifestyle
            'movie', 'film', 'celebrity', 'entertainment', 'sports', 'athlete',
            'music', 'concert', 'festival', 'lifestyle', 'fashion', 'beauty',
            'food', 'restaurant', 'travel', 'tourism', 'hotel',
            
            # Health and medical
            'medical', 'healthcare', 'pharmaceutical', 'drug', 'treatment',
            'hospital', 'doctor', 'patient', 'disease', 'vaccine',
            
            # Local and regional news
            'local news', 'city council', 'mayor', 'governor', 'state',
            'community', 'neighborhood', 'local business', 'regional',
            
            # Non-financial business news
            'retail store', 'restaurant chain', 'fast food', 'coffee shop',
            'automotive', 'car', 'vehicle', 'transportation', 'logistics',
            'energy company', 'utility', 'telecommunications', 'media company'
        ]

        # Explicit stock/equity exclusion terms (policy: everything except stocks/equities)
        self.stock_exclusion_keywords = [
            'stock', 'stocks', 'equity', 'equities', 'shares', 'share price', 'shareholder',
            'earnings', 'earnings call', 'eps', 'revenue', 'guidance', 'analyst rating',
            'price target', 'dividend', 'ipo', 'buyback', 'market cap', 'pe ratio',
            'quarterly results', 'company outlook', 'ceo', 'board of directors'
        ]
        self.index_keywords = [
            'index', 'indices', 's&p 500', 'sp 500', 'nasdaq 100', 'dow jones',
            'ftse', 'dax', 'nikkei', 'hang seng', 'stoxx', 'sensex'
        ]
        self.market_keyword_map = {
            'forex': [
                'forex', 'currency', 'fx', 'foreign exchange',
                'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
                'dollar', 'euro', 'yen', 'pound', 'franc'
            ],
            'crypto': [
                'crypto', 'cryptocurrency', 'bitcoin', 'ethereum', 'solana',
                'xrp', 'altcoin', 'stablecoin', 'defi', 'token', 'digital asset'
            ],
            'indices': [
                'index', 'indices', 's&p 500', 'sp 500', 'nasdaq 100', 'dow jones',
                'ftse', 'dax', 'nikkei', 'hang seng', 'stoxx', 'sensex'
            ],
            'commodities': [
                'commodity', 'commodities', 'gold', 'silver', 'oil',
                'crude', 'natural gas', 'copper', 'wti', 'brent'
            ],
            'rates': [
                'interest rate', 'policy rate', 'benchmark rate', 'bond yield',
                'treasury yield', 'yield curve', '2-year', '10-year', 'real yield'
            ],
            'macro': [
                'cpi', 'inflation', 'nfp', 'non-farm payrolls', 'gdp', 'pmi',
                'retail sales', 'unemployment', 'trade balance', 'central bank',
                'monetary policy', 'fiscal policy'
            ]
        }
        
        # High impact keywords for scoring
        self.high_impact_keywords = [
            'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe', 'interest rate', 'non-farm payrolls', 'gdp',
            'rate decision', 'policy meeting', 'speech', 'testimony',
            'trump', 'biden', 'election', 'trade war', 'tariff', 'sanctions', 'geopolitical',
            'brexit', 'china trade', 'us china', 'market volatility', 'market uncertainty',
            'brics', 'venezuela', 'attack', 'conflict', 'crisis', 'instability',
            # Added forex-specific terms
            'fx option', 'option expiries', 'new york cut', 'london cut', 'asian session',
            'consumer prices', 'bank lending', 'lending rate', 'monetary policy',
            'currency pair', 'forex market', 'fx market', 'currency market',
            'economic data', 'economic indicator', 'economic release',
            'central bank', 'bank rate', 'policy rate', 'benchmark rate'
        ]
        
        # Medium impact keywords for scoring
        self.medium_impact_keywords = [
            'retail sales', 'manufacturing', 'services pmi', 'unemployment', 'employment', 'trade balance',
            'minutes', 'economic calendar', 'trade', 'trade deal', 'trade agreement', 'politics',
            'congress', 'legislation', 'market sentiment', 'investor confidence'
        ]
        
        # Critical forex keywords that should always trigger alerts
        self.critical_forex_keywords = [
            'fed', 'federal reserve', 'ecb', 'european central bank', 'boj', 'bank of japan',
            'boe', 'bank of england', 'rba', 'reserve bank of australia', 'boc', 'bank of canada',
            'nfp', 'non-farm payrolls', 'cpi', 'inflation', 'interest rate', 'monetary policy',
            'rate decision', 'policy meeting', 'speech', 'testimony', 'breaking', 'urgent',
            # Added critical forex terms
            'fx option', 'option expiries', 'consumer prices', 'bank lending', 'lending rate',
            'central bank', 'bank rate', 'policy rate', 'benchmark rate', 'economic data'
        ]
        
        # Credible sources that get priority
        self.credible_sources = [
            'reuters', 'bloomberg', 'cnbc', 'marketwatch', 'forexfactory', 'fxstreet',
            'investing.com', 'fxempire', 'dailyfx', 'fxcm', 'oanda', 'ig'
        ]
        
        # Forex-focused sources that should be prioritized
        self.forex_focused_sources = [
            'fxstreet', 'forexfactory', 'fxempire', 'dailyfx', 'forexlive',
            'investing.com', 'fxcm', 'oanda', 'ig', 'forex.com'
        ]
        
        # Recent market events that might affect filtering
        self.current_market_context = {
            'high_volatility_periods': [],
            'major_events': [],
            'currency_focus': []
        }
    
    def _is_stock_or_equity_news(self, text: str) -> bool:
        """Return True when content is primarily stock/equity/company-specific."""
        has_stock_term = any(term in text for term in self.stock_exclusion_keywords)
        has_index_context = any(term in text for term in self.index_keywords)
        return has_stock_term and not has_index_context

    def is_market_relevant(self, title: str, summary: str = "", source: str = "") -> bool:
        """
        Broad market filtering aligned to product policy:
        include FX/crypto/indices/commodities/macro-rates, exclude stocks/equities.
        """
        text = f"{title} {summary}".lower()
        source_lower = source.lower()
        
        # Count positive and negative keyword matches
        positive_matches = self._count_keyword_matches(text, self.positive_keywords)
        negative_matches = self._count_keyword_matches(text, self.negative_keywords)
        
        # Core market terms that indicate strong relevance
        core_forex_terms = [
            'forex', 'currency', 'fx', 'foreign exchange',
            'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
            'fed', 'ecb', 'boj', 'boe', 'rba', 'boc', 'snb', 'rbnz',
            'cpi', 'inflation', 'interest rate', 'non-farm payrolls', 'gdp',
            'crypto', 'bitcoin', 'ethereum', 'altcoin',
            'index', 'indices', 's&p 500', 'nasdaq 100', 'dow jones', 'ftse', 'dax', 'nikkei',
            'commodity', 'gold', 'silver', 'oil', 'crude', 'natural gas', 'copper',
            'treasury yield', 'bond yield', 'yield curve'
        ]
        
        # Economic and commodity terms that are forex-relevant
        forex_relevant_terms = [
            'commodity', 'oil', 'crude', 'gold', 'silver', 'copper', 'natural gas',
            'economic', 'economy', 'economic data', 'economic indicator',
            'trade', 'tariff', 'trade war', 'trade deal', 'trade agreement',
            'geopolitical', 'geopolitics', 'diplomatic', 'sanctions',
            'market sentiment', 'risk-off', 'risk-on', 'safe haven',
            'brics', 'venezuela', 'attack', 'conflict', 'crisis', 'instability'
        ]
        
        has_core_forex = any(term in text for term in core_forex_terms)
        has_forex_relevant = any(term in text for term in forex_relevant_terms)
        
        # Check if source is forex-focused (more lenient filtering)
        is_forex_source = any(forex_source in source_lower for forex_source in self.forex_focused_sources)
        
        # Enhanced decision logic:
        # 1) Explicit policy: stock/equity/company-specific content is excluded
        if self._is_stock_or_equity_news(text):
            return False

        # 2) Check for strong negative keywords that should exclude regardless
        strong_negative_keywords = [
            'real estate', 'property', 'mortgage', 'housing', 'home',
            'movie', 'film', 'celebrity', 'entertainment', 'sports', 'athlete',
            'music', 'concert', 'festival', 'lifestyle', 'fashion', 'beauty',
            'food', 'restaurant', 'travel', 'tourism', 'hotel',
            'medical', 'healthcare', 'pharmaceutical', 'drug', 'treatment',
            'local news', 'city council', 'mayor', 'governor', 'community'
        ]
        
        has_strong_negative = any(term in text for term in strong_negative_keywords)
        if has_strong_negative:
            return False  # Exclude if it has strong negative keywords
        
        # 3) If it has core market terms, include it
        if has_core_forex:
            return True
        
        # 4) If it's from a forex-focused source, be more lenient
        if is_forex_source and positive_matches > 0:
            return True  # Include forex source content with positive keywords
        
        # 5) If it has market-relevant terms and some positive context, include it
        if has_forex_relevant and positive_matches > 0:
            # But exclude if it has too many negative keywords
            return negative_matches <= 1  # Allow 1 negative keyword for context
        
        # 6) For general sources, require at least one positive and no non-market negatives.
        # This is broader than old forex-only gate but still blocks obvious noise.
        return negative_matches == 0 and positive_matches >= 2

    def is_forex_related(self, title: str, summary: str = "", source: str = "") -> bool:
        """
        Backward-compatible alias.
        Existing callers still use this name, but behavior is now market-wide.
        """
        return self.is_market_relevant(title, summary, source)
    
    def is_high_impact_for_alerts(self, title: str, summary: str = "", source: str = "") -> bool:
        """
        Strict filtering for alert-worthy news
        Only returns True for truly high-impact forex news
        """
        text = f"{title} {summary}".lower()
        source_lower = source.lower()
        
        # Check for critical forex keywords (automatic high impact)
        for keyword in self.critical_forex_keywords:
            if keyword in text:
                return True
        
        # Check source credibility
        is_credible_source = any(credible in source_lower for credible in self.credible_sources)
        is_forex_source = any(forex_source in source_lower for forex_source in self.forex_focused_sources)
        
        # For credible sources, be more lenient but still strict
        if is_credible_source or is_forex_source:
            # Must have at least 1 high-impact keyword or 1 critical keyword
            high_impact_count = self._count_keyword_matches(text, self.high_impact_keywords)
            critical_count = self._count_keyword_matches(text, self.critical_forex_keywords)
            
            return high_impact_count >= 1 or critical_count >= 1
        
        # For non-credible sources, be very strict
        # Must have at least 3 high-impact keywords or 2 critical keywords
        high_impact_count = self._count_keyword_matches(text, self.high_impact_keywords)
        critical_count = self._count_keyword_matches(text, self.critical_forex_keywords)
        
        return high_impact_count >= 3 or critical_count >= 2
    
    def get_forex_score(self, title: str, summary: str = "") -> Dict[str, Any]:
        """
        Get detailed scoring for forex relevance
        """
        text = f"{title} {summary}".lower()
        
        positive_matches = self._count_keyword_matches(text, self.positive_keywords)
        negative_matches = self._count_keyword_matches(text, self.negative_keywords)
        high_impact_matches = self._count_keyword_matches(text, self.high_impact_keywords)
        medium_impact_matches = self._count_keyword_matches(text, self.medium_impact_keywords)
        
        # Calculate impact level
        if high_impact_matches > 0:
            impact = 'high'
        elif medium_impact_matches > 0:
            impact = 'medium'
        else:
            impact = 'low'
        
        # Calculate confidence score (0-100)
        confidence = 0
        is_market = self.is_market_relevant(title, summary)
        if is_market and negative_matches == 0:
            confidence = min(100, (positive_matches * 20) + (high_impact_matches * 15) + (medium_impact_matches * 10))
        
        return {
            'is_forex': is_market,  # Backward-compatibility for existing consumers.
            'is_market': is_market,
            'positive_score': positive_matches,
            'negative_score': negative_matches,
            'high_impact_matches': high_impact_matches,
            'medium_impact_matches': medium_impact_matches,
            'impact_level': impact,
            'confidence': confidence,
            'positive_keywords_found': self._find_matching_keywords(text, self.positive_keywords),
            'negative_keywords_found': self._find_matching_keywords(text, self.negative_keywords)
        }
    
    def extract_currency_pairs(self, title: str, summary: str = "") -> List[str]:
        """
        Extract currency pairs from text with enhanced detection
        """
        text = f"{title} {summary}".lower()
        currency_pairs = []
        
        # Common currency pair patterns (exact matches)
        exact_pairs = [
            'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
            'eur/gbp', 'eur/jpy', 'gbp/jpy', 'eur/chf', 'gbp/chf', 'aud/jpy', 'cad/jpy',
            'eur/aud', 'gbp/aud', 'eur/cad', 'gbp/cad', 'aud/cad', 'nzd/jpy', 'aud/nzd'
        ]
        
        # Check for exact currency pair matches
        for pair in exact_pairs:
            if pair in text:
                currency_pairs.append(pair.upper())
        
        # Infer from currency mentions
        currency_mapping = {
            'usd': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
            'eur': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF'],
            'gbp': ['GBP/USD', 'EUR/GBP', 'GBP/JPY'],
            'jpy': ['USD/JPY', 'EUR/JPY', 'GBP/JPY'],
            'aud': ['AUD/USD', 'EUR/AUD', 'GBP/AUD'],
            'cad': ['USD/CAD', 'EUR/CAD', 'GBP/CAD'],
            'chf': ['USD/CHF', 'EUR/CHF', 'GBP/CHF'],
            'nzd': ['NZD/USD', 'EUR/NZD', 'GBP/NZD']
        }
        
        for currency, pairs in currency_mapping.items():
            if currency in text:
                currency_pairs.extend(pairs)
        
        # Remove duplicates and return
        return list(set(currency_pairs))

    def get_market_relevance(self, title: str, summary: str = "", top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Return top market relevance buckets for internal use.
        Each item contains the market name, score, and matched keywords.
        """
        text = f"{title} {summary}".lower()
        relevance = []

        for market, keywords in self.market_keyword_map.items():
            matched = [keyword for keyword in keywords if keyword in text]
            if matched:
                relevance.append({
                    'market': market,
                    'score': len(matched),
                    'matched_keywords': matched[:8]
                })

        relevance.sort(key=lambda item: item['score'], reverse=True)
        return relevance[:max(3, min(top_n, 5))]
    
    def should_trigger_alert(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive decision on whether to trigger an alert
        Returns detailed reasoning for the decision
        """
        title = news_item.get('title', '')
        summary = news_item.get('summary', '')
        content = news_item.get('content', '')
        source = news_item.get('source', '')
        
        # Get market relevance score
        forex_score = self.get_forex_score(title, summary)
        
        # Check if it's high impact for alerts
        is_high_impact = self.is_high_impact_for_alerts(title, summary, source)
        
        # Extract currency pairs
        currency_pairs = self.extract_currency_pairs(title, summary)
        
        # Decision logic
        should_alert = False
        reasoning = []
        
        if not forex_score['is_market']:
            reasoning.append("Not market-relevant")
        elif not is_high_impact:
            reasoning.append("Not high-impact enough for alerts")
        else:
            should_alert = True
            reasoning.append("High-impact market news")
        
        # Additional factors
        if source.lower() in [s.lower() for s in self.credible_sources]:
            reasoning.append("Credible source")
        
        if forex_score['confidence'] > 70:
            reasoning.append("High confidence score")
        
        return {
            'should_alert': should_alert,
            'reasoning': reasoning,
            'forex_score': forex_score,
            'currency_pairs': currency_pairs,
            'impact_level': forex_score['impact_level'],
            'confidence': forex_score['confidence']
        }
    
    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords are found in the text"""
        count = 0
        for keyword in keywords:
            if keyword in text:
                count += 1
        return count
    
    def _find_matching_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Find which specific keywords matched"""
        matches = []
        for keyword in keywords:
            if keyword in text:
                matches.append(keyword)
        return matches
    
    def update_market_context(self, context: Dict[str, Any]):
        """Update current market context for better filtering"""
        self.current_market_context.update(context)
    
    def filter_news_list(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter a list of news items, keeping only forex-relevant ones
        """
        filtered_news = []
        
        for news_item in news_list:
            title = news_item.get('title', '')
            summary = news_item.get('summary', '')
            
            if self.is_market_relevant(title, summary):
                # Add forex score to the news item
                forex_score = self.get_forex_score(title, summary)
                news_item['forex_score'] = forex_score
                news_item['currency_pairs'] = self.extract_currency_pairs(title, summary)
                
                filtered_news.append(news_item)
        
        return filtered_news

# Global instance
enhanced_forex_filter = EnhancedForexFilter()
