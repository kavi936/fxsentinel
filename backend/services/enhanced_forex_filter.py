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
        
        # Enhanced currency detection - look for individual currencies and suggest pairs
        currencies_found = []
        
        # Currency keywords and their codes
        currency_keywords = {
            'dollar': 'USD', 'us dollar': 'USD', 'greenback': 'USD', 'buck': 'USD',
            'euro': 'EUR', 'european': 'EUR',
            'pound': 'GBP', 'sterling': 'GBP', 'british pound': 'GBP',
            'yen': 'JPY', 'japanese yen': 'JPY',
            'franc': 'CHF', 'swiss franc': 'CHF',
            'australian dollar': 'AUD', 'aussie': 'AUD',
            'canadian dollar': 'CAD', 'loonie': 'CAD',
            'new zealand dollar': 'NZD', 'kiwi': 'NZD',
            'yuan': 'CNY', 'chinese yuan': 'CNY', 'renminbi': 'CNY',
            'rupee': 'INR', 'indian rupee': 'INR',
            'real': 'BRL', 'brazilian real': 'BRL',
            'peso': 'MXN', 'mexican peso': 'MXN',
            'won': 'KRW', 'south korean won': 'KRW',
            'krona': 'SEK', 'swedish krona': 'SEK',
            'krone': 'NOK', 'norwegian krone': 'NOK',
            'danish krone': 'DKK',
            'zloty': 'PLN', 'polish zloty': 'PLN',
            'koruna': 'CZK', 'czech koruna': 'CZK',
            'forint': 'HUF', 'hungarian forint': 'HUF',
            'leu': 'RON', 'romanian leu': 'RON',
            'lev': 'BGN', 'bulgarian lev': 'BGN',
            'kuna': 'HRK', 'croatian kuna': 'HRK',
            'dinar': 'RSD', 'serbian dinar': 'RSD',
            'lira': 'TRY', 'turkish lira': 'TRY',
            'rand': 'ZAR', 'south african rand': 'ZAR',
            'ruble': 'RUB', 'russian ruble': 'RUB',
            'singapore dollar': 'SGD', 'sgd': 'SGD'
        }
        
        # Country to currency mapping for better detection
        country_currency_map = {
            # Major countries
            'united states': 'USD', 'us ': 'USD', 'usa': 'USD', 'america': 'USD', 'american': 'USD',
            'european union': 'EUR', 'eu ': 'EUR', 'eurozone': 'EUR', 'europe': 'EUR', 'european': 'EUR',
            'united kingdom': 'GBP', 'uk ': 'GBP', 'britain': 'GBP', 'british': 'GBP', 'england': 'GBP',
            'japan': 'JPY', 'japanese': 'JPY',
            'australia': 'AUD', 'australian': 'AUD',
            'canada': 'CAD', 'canadian': 'CAD',
            'switzerland': 'CHF', 'swiss': 'CHF',
            'new zealand': 'NZD', 'nz ': 'NZD',
            'china': 'CNY', 'chinese': 'CNY',
            'india': 'INR', 'indian': 'INR',
            'brazil': 'BRL', 'brazilian': 'BRL',
            'mexico': 'MXN', 'mexican': 'MXN',
            'south korea': 'KRW', 'korean': 'KRW',
            'sweden': 'SEK', 'swedish': 'SEK',
            'norway': 'NOK', 'norwegian': 'NOK',
            'denmark': 'DKK', 'danish': 'DKK',
            'poland': 'PLN', 'polish': 'PLN',
            'czech republic': 'CZK', 'czech': 'CZK',
            'hungary': 'HUF', 'hungarian': 'HUF',
            'romania': 'RON', 'romanian': 'RON',
            'bulgaria': 'BGN', 'bulgarian': 'BGN',
            'croatia': 'HRK', 'croatian': 'HRK',
            'serbia': 'RSD', 'serbian': 'RSD',
            'turkey': 'TRY', 'turkish': 'TRY',
            'south africa': 'ZAR', 'african': 'ZAR',
            'russia': 'RUB', 'russian': 'RUB',
            'singapore': 'SGD',
            
            # Individual Eurozone countries (map to EUR)
            'germany': 'EUR', 'german': 'EUR', 'deutschland': 'EUR',
            'france': 'EUR', 'french': 'EUR',
            'italy': 'EUR', 'italian': 'EUR',
            'spain': 'EUR', 'spanish': 'EUR',
            'netherlands': 'EUR', 'dutch': 'EUR',
            'belgium': 'EUR', 'belgian': 'EUR',
            'austria': 'EUR', 'austrian': 'EUR',
            'finland': 'EUR', 'finnish': 'EUR',
            'ireland': 'EUR', 'irish': 'EUR',
            'portugal': 'EUR', 'portuguese': 'EUR',
            'greece': 'EUR', 'greek': 'EUR',
            'slovenia': 'EUR', 'slovenian': 'EUR',
            'slovakia': 'EUR', 'slovak': 'EUR',
            'estonia': 'EUR', 'estonian': 'EUR',
            'latvia': 'EUR', 'latvian': 'EUR',
            'lithuania': 'EUR', 'lithuanian': 'EUR',
            'luxembourg': 'EUR', 'luxembourgish': 'EUR',
            'malta': 'EUR', 'maltese': 'EUR',
            'cyprus': 'EUR', 'cypriot': 'EUR'
        }
        
        # Find currencies mentioned in the text
        for keyword, currency_code in currency_keywords.items():
            if keyword in text:
                currencies_found.append(currency_code)
        
        # Find currencies based on country names
        for country, currency_code in country_currency_map.items():
            if country in text:
                currencies_found.append(currency_code)
        
        # Also check for currency codes directly
        currency_codes = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD', 'CNY', 'INR', 'BRL', 'MXN', 'KRW', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RON', 'BGN', 'HRK', 'RSD', 'TRY', 'ZAR', 'RUB', 'SGD']
        for code in currency_codes:
            if code.lower() in text:
                currencies_found.append(code)
        
        # Remove duplicates
        currencies_found = list(set(currencies_found))
        
        # If we found currencies but no exact pairs, suggest relevant pairs
        if currencies_found and not currency_pairs:
            # Major currency pairs to suggest based on found currencies
            major_pairs = {
                'USD': ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD'],
                'EUR': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/CAD', 'EUR/AUD'],
                'GBP': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF', 'GBP/CAD', 'GBP/AUD'],
                'JPY': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY', 'CAD/JPY', 'CHF/JPY'],
                'AUD': ['AUD/USD', 'EUR/AUD', 'GBP/AUD', 'AUD/JPY', 'AUD/CAD', 'AUD/CHF'],
                'CAD': ['USD/CAD', 'EUR/CAD', 'GBP/CAD', 'CAD/JPY', 'AUD/CAD', 'CAD/CHF'],
                'CHF': ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'CHF/JPY', 'AUD/CHF', 'CAD/CHF'],
                'NZD': ['NZD/USD', 'EUR/NZD', 'GBP/NZD', 'NZD/JPY', 'AUD/NZD', 'NZD/CAD']
            }
            
            # Add relevant pairs for each currency found
            for currency in currencies_found:
                if currency in major_pairs:
                    # Add top 3 most liquid pairs for each currency
                    currency_pairs.extend(major_pairs[currency][:3])
            
            # Remove duplicates and limit to reasonable number
            currency_pairs = list(set(currency_pairs))[:6]
        
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
