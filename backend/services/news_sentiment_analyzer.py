#!/usr/bin/env python3
"""
News Sentiment Analyzer for FXSentinel
Uses free techniques to analyze forex news sentiment without expensive APIs
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    sentiment: str  # 'positive', 'negative', 'neutral'
    confidence: float  # 0.0 to 1.0
    keywords: List[str]
    impact_score: float  # 0.0 to 1.0
    affected_pairs: List[str]
    trading_implications: List[str]

class NewsSentimentAnalyzer:
    def __init__(self):
        self.sentiment_keywords = self._load_sentiment_keywords()
        self.forex_keywords = self._load_forex_keywords()
        self.impact_keywords = self._load_impact_keywords()
        self.currency_pairs = self._load_currency_pairs()
        
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
    
    def _load_forex_keywords(self) -> Dict[str, List[str]]:
        """Load forex-specific keywords"""
        return {
            'currencies': ['dollar', 'euro', 'yen', 'pound', 'franc', 'australian dollar', 'canadian dollar'],
            'pairs': ['eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad'],
            'economic_indicators': [
                'cpi', 'inflation', 'gdp', 'employment', 'unemployment', 'retail sales',
                'manufacturing', 'services', 'pmi', 'interest rate', 'fed', 'ecb', 'boj', 'boe'
            ],
            'market_terms': [
                'volatility', 'liquidity', 'spread', 'pip', 'lot', 'leverage',
                'margin', 'stop loss', 'take profit', 'support', 'resistance'
            ]
        }
    
    def _load_impact_keywords(self) -> Dict[str, List[str]]:
        """Load impact level keywords"""
        return {
            'high_impact': [
                'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe', 'interest rate',
                'non-farm payrolls', 'gdp', 'trump', 'tariffs', 'trade war',
                'emergency', 'crisis', 'shock', 'surprise'
            ],
            'medium_impact': [
                'retail sales', 'manufacturing', 'unemployment', 'employment',
                'trade balance', 'current account', 'housing', 'consumer confidence'
            ],
            'low_impact': [
                'minor', 'secondary', 'regional', 'local', 'small', 'insignificant'
            ]
        }
    
    def _load_currency_pairs(self) -> Dict[str, Dict]:
        """Load currency pair information"""
        return {
            'EUR/USD': {
                'base': 'EUR',
                'quote': 'USD',
                'correlations': ['GBP/USD', 'AUD/USD'],
                'inverse': ['USD/JPY', 'USD/CHF']
            },
            'USD/JPY': {
                'base': 'USD',
                'quote': 'JPY',
                'correlations': ['USD/CHF'],
                'inverse': ['EUR/USD', 'GBP/USD']
            },
            'GBP/USD': {
                'base': 'GBP',
                'quote': 'USD',
                'correlations': ['EUR/USD', 'AUD/USD'],
                'inverse': ['USD/JPY', 'USD/CHF']
            },
            'USD/CHF': {
                'base': 'USD',
                'quote': 'CHF',
                'correlations': ['USD/JPY'],
                'inverse': ['EUR/USD', 'GBP/USD']
            },
            'AUD/USD': {
                'base': 'AUD',
                'quote': 'USD',
                'correlations': ['EUR/USD', 'GBP/USD'],
                'inverse': ['USD/JPY', 'USD/CHF']
            },
            'USD/CAD': {
                'base': 'USD',
                'quote': 'CAD',
                'correlations': ['USD/JPY'],
                'inverse': ['EUR/USD', 'GBP/USD']
            }
        }
    
    def analyze_news_sentiment(self, news_text: str, title: str = "") -> SentimentResult:
        """Analyze sentiment of forex news"""
        try:
            # Combine title and text for analysis
            full_text = f"{title} {news_text}".lower()
            
            # Analyze sentiment
            sentiment, confidence = self._calculate_sentiment(full_text)
            
            # Extract keywords
            keywords = self._extract_keywords(full_text)
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(full_text)
            
            # Identify affected currency pairs
            affected_pairs = self._identify_affected_pairs(full_text)
            
            # Generate trading implications
            trading_implications = self._generate_trading_implications(
                sentiment, impact_score, affected_pairs, keywords
            )
            
            return SentimentResult(
                sentiment=sentiment,
                confidence=confidence,
                keywords=keywords,
                impact_score=impact_score,
                affected_pairs=affected_pairs,
                trading_implications=trading_implications
            )
            
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return self._get_default_sentiment()
    
    def _calculate_sentiment(self, text: str) -> Tuple[str, float]:
        """Calculate sentiment score and confidence"""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        # Count sentiment keywords
        for word in self.sentiment_keywords['positive']:
            positive_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
        
        for word in self.sentiment_keywords['negative']:
            negative_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
        
        for word in self.sentiment_keywords['neutral']:
            neutral_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
        
        # Calculate sentiment
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return 'neutral', 0.5
        
        # Calculate confidence based on word count
        confidence = min(1.0, total_sentiment_words / 10.0)
        
        # Determine sentiment
        if positive_count > negative_count and positive_count > neutral_count:
            sentiment = 'positive'
        elif negative_count > positive_count and negative_count > neutral_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return sentiment, confidence
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        keywords = []
        
        # Extract forex keywords
        for category, words in self.forex_keywords.items():
            for word in words:
                if re.search(r'\b' + re.escape(word) + r'\b', text):
                    keywords.append(word)
        
        # Extract sentiment keywords
        for sentiment, words in self.sentiment_keywords.items():
            for word in words:
                if re.search(r'\b' + re.escape(word) + r'\b', text):
                    keywords.append(word)
        
        # Remove duplicates and limit to top keywords
        unique_keywords = list(set(keywords))
        return unique_keywords[:10]  # Return top 10 keywords
    
    def _calculate_impact_score(self, text: str) -> float:
        """Calculate impact score (0.0 to 1.0)"""
        high_impact_count = 0
        medium_impact_count = 0
        low_impact_count = 0
        
        # Count impact keywords
        for word in self.impact_keywords['high_impact']:
            high_impact_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
        
        for word in self.impact_keywords['medium_impact']:
            medium_impact_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
        
        for word in self.impact_keywords['low_impact']:
            low_impact_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
        
        # Calculate weighted impact score
        total_impact = (high_impact_count * 3) + (medium_impact_count * 2) + low_impact_count
        
        if total_impact == 0:
            return 0.3  # Default medium-low impact
        
        # Normalize to 0-1 scale
        impact_score = min(1.0, total_impact / 10.0)
        return impact_score
    
    def _identify_affected_pairs(self, text: str) -> List[str]:
        """Identify currency pairs mentioned or affected by the news"""
        mentioned_pairs = []
        
        # Look for direct pair mentions
        for pair in self.currency_pairs.keys():
            if re.search(r'\b' + re.escape(pair.lower()) + r'\b', text):
                mentioned_pairs.append(pair)
        
        # Look for currency mentions and infer pairs
        currencies_mentioned = []
        for currency in self.forex_keywords['currencies']:
            if re.search(r'\b' + re.escape(currency) + r'\b', text):
                currencies_mentioned.append(currency)
        
        # Infer pairs from currency mentions
        if 'dollar' in currencies_mentioned and 'euro' in currencies_mentioned:
            mentioned_pairs.append('EUR/USD')
        if 'dollar' in currencies_mentioned and 'yen' in currencies_mentioned:
            mentioned_pairs.append('USD/JPY')
        if 'dollar' in currencies_mentioned and 'pound' in currencies_mentioned:
            mentioned_pairs.append('GBP/USD')
        
        # Remove duplicates
        unique_pairs = list(set(mentioned_pairs))
        
        # If no specific pairs found, return major pairs
        if not unique_pairs:
            return ['EUR/USD', 'USD/JPY']
        
        return unique_pairs
    
    def _generate_trading_implications(self, sentiment: str, impact_score: float, 
                                     affected_pairs: List[str], keywords: List[str]) -> List[str]:
        """Generate trading implications based on sentiment analysis"""
        implications = []
        
        # Base implications based on sentiment
        if sentiment == 'positive':
            implications.append("Consider bullish positions on affected pairs")
            implications.append("Look for breakout opportunities above resistance")
        elif sentiment == 'negative':
            implications.append("Consider bearish positions on affected pairs")
            implications.append("Look for breakdown opportunities below support")
        else:
            implications.append("Monitor for clear directional signals")
            implications.append("Consider range trading strategies")
        
        # Impact-based implications
        if impact_score > 0.7:
            implications.append("High volatility expected - use wider stops")
            implications.append("Consider reduced position sizes due to high impact")
        elif impact_score > 0.4:
            implications.append("Moderate volatility expected")
            implications.append("Standard position sizing appropriate")
        else:
            implications.append("Low volatility expected")
            implications.append("Consider tighter stops for better risk/reward")
        
        # Keyword-specific implications
        if any(word in keywords for word in ['cpi', 'inflation']):
            implications.append("Monitor bond yields for confirmation")
            implications.append("Central bank policy implications likely")
        
        if any(word in keywords for word in ['fed', 'ecb', 'boj', 'boe']):
            implications.append("Interest rate differentials may shift")
            implications.append("Carry trade flows could be affected")
        
        if any(word in keywords for word in ['employment', 'jobs']):
            implications.append("Consumer spending implications")
            implications.append("Wage growth trends to monitor")
        
        return implications[:5]  # Return top 5 implications
    
    def _get_default_sentiment(self) -> SentimentResult:
        """Return default sentiment when analysis fails"""
        return SentimentResult(
            sentiment='neutral',
            confidence=0.5,
            keywords=[],
            impact_score=0.3,
            affected_pairs=['EUR/USD', 'USD/JPY'],
            trading_implications=[
                "Monitor for clear directional signals",
                "Use standard risk management",
                "Wait for confirmation before entering trades"
            ]
        )
    
    def analyze_multiple_news(self, news_items: List[Dict]) -> Dict[str, Any]:
        """Analyze multiple news items and provide aggregated insights"""
        try:
            all_sentiments = []
            all_keywords = []
            all_pairs = []
            
            for news_item in news_items:
                title = news_item.get('title', '')
                content = news_item.get('content', '') or news_item.get('summary', '')
                
                sentiment_result = self.analyze_news_sentiment(content, title)
                all_sentiments.append(sentiment_result)
                all_keywords.extend(sentiment_result.keywords)
                all_pairs.extend(sentiment_result.affected_pairs)
            
            # Aggregate results
            sentiment_counts = {
                'positive': sum(1 for s in all_sentiments if s.sentiment == 'positive'),
                'negative': sum(1 for s in all_sentiments if s.sentiment == 'negative'),
                'neutral': sum(1 for s in all_sentiments if s.sentiment == 'neutral')
            }
            
            # Calculate overall sentiment
            if sentiment_counts['positive'] > sentiment_counts['negative']:
                overall_sentiment = 'positive'
            elif sentiment_counts['negative'] > sentiment_counts['positive']:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            # Get most common keywords
            keyword_counts = {}
            for keyword in all_keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Get most affected pairs
            pair_counts = {}
            for pair in all_pairs:
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
            
            top_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'overall_sentiment': overall_sentiment,
                'sentiment_distribution': sentiment_counts,
                'top_keywords': [kw[0] for kw in top_keywords],
                'most_affected_pairs': [pair[0] for pair in top_pairs],
                'total_news_analyzed': len(news_items),
                'average_impact_score': np.mean([s.impact_score for s in all_sentiments]),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing multiple news: {e}")
            return {
                'overall_sentiment': 'neutral',
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 1},
                'top_keywords': [],
                'most_affected_pairs': ['EUR/USD', 'USD/JPY'],
                'total_news_analyzed': 0,
                'average_impact_score': 0.3,
                'timestamp': datetime.now().isoformat()
            }

# Create global instance
news_sentiment_analyzer = NewsSentimentAnalyzer()
