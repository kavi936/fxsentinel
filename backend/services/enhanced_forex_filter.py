#!/usr/bin/env python3
"""
Enhanced Forex Filtering System
Uses positive and negative keywords for better accuracy
"""

import re
from typing import List, Dict, Any, Tuple

class EnhancedForexFilter:
    def __init__(self):
        # Positive keywords (must have for forex relevance)
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
            'dollar strength', 'dollar weakness', 'currency strength', 'currency weakness'
        ]
        
        # Negative keywords (exclude if present)
        self.negative_keywords = [
            # Cryptocurrency
            'cryptocurrency', 'bitcoin', 'ethereum', 'crypto', 'blockchain', 'defi', 'nft',
            'altcoin', 'stablecoin', 'token', 'ico', 'airdrop', 'mining', 'wallet',
            
            # Stocks and equities
            'stock', 'equity', 'shares', 'dividend', 'earnings', 'revenue', 'profit', 'loss',
            'market cap', 'pe ratio', 'ipo', 'secondary offering', 'buyback', 'split',
            
            # Commodities
            'commodity', 'oil', 'crude', 'gold', 'silver', 'copper', 'natural gas', 'corn',
            'wheat', 'soybeans', 'cotton', 'sugar', 'coffee', 'cocoa', 'lumber',
            
            # Real estate
            'real estate', 'property', 'mortgage', 'housing', 'home', 'apartment', 'rental',
            'commercial property', 'reit', 'construction', 'builder',
            
            # Other non-forex
            'bonds', 'treasury', 'corporate bond', 'municipal bond', 'yield curve',
            'options', 'futures', 'derivatives', 'hedge fund', 'mutual fund', 'etf'
        ]
        
        # High impact keywords for scoring
        self.high_impact_keywords = [
            'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe', 'interest rate', 'non-farm payrolls', 'gdp',
            'rate decision', 'policy meeting', 'speech', 'testimony',
            'trump', 'biden', 'election', 'trade war', 'tariff', 'sanctions', 'geopolitical',
            'brexit', 'china trade', 'us china', 'market volatility', 'market uncertainty'
        ]
        
        # Medium impact keywords for scoring
        self.medium_impact_keywords = [
            'retail sales', 'manufacturing', 'services pmi', 'unemployment', 'employment', 'trade balance',
            'minutes', 'economic calendar', 'trade', 'trade deal', 'trade agreement', 'politics',
            'congress', 'legislation', 'market sentiment', 'investor confidence'
        ]
    
    def is_forex_related(self, title: str, summary: str = "") -> bool:
        """
        Enhanced forex filtering using positive and negative keywords
        """
        text = f"{title} {summary}".lower()
        
        # Count positive and negative keyword matches
        positive_matches = self._count_keyword_matches(text, self.positive_keywords)
        negative_matches = self._count_keyword_matches(text, self.negative_keywords)
        
        # Decision logic: must have positive keywords AND no negative keywords
        return positive_matches > 0 and negative_matches == 0
    
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
        if positive_matches > 0 and negative_matches == 0:
            confidence = min(100, (positive_matches * 20) + (high_impact_matches * 15) + (medium_impact_matches * 10))
        
        return {
            'is_forex': positive_matches > 0 and negative_matches == 0,
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
        Extract currency pairs from text
        """
        text = f"{title} {summary}".lower()
        currency_pairs = []
        
        # Common currency pair patterns
        pairs = [
            'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
            'eur/gbp', 'eur/jpy', 'gbp/jpy', 'eur/chf', 'gbp/chf', 'aud/jpy', 'cad/jpy',
            'eur/aud', 'gbp/aud', 'eur/cad', 'gbp/cad', 'aud/cad', 'nzd/jpy', 'aud/nzd'
        ]
        
        for pair in pairs:
            if pair in text:
                currency_pairs.append(pair.upper())
        
        return currency_pairs
    
    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords match in the text"""
        count = 0
        for keyword in keywords:
            if keyword.lower() in text:
                count += 1
        return count
    
    def _find_matching_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Find which specific keywords matched"""
        matches = []
        for keyword in keywords:
            if keyword.lower() in text:
                matches.append(keyword)
        return matches

# Global instance
enhanced_forex_filter = EnhancedForexFilter()
