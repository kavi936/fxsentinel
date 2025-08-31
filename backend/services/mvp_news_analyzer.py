#!/usr/bin/env python3
"""
MVP News Analyzer for FXSentinel
Implements simplified two-paragraph analysis format with hybrid free/GPT analysis
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

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

class MVPNewsAnalyzer:
    """MVP news analyzer with hybrid free/GPT analysis"""
    
    def __init__(self):
        self.sentiment_keywords = self._load_sentiment_keywords()
        self.political_keywords = self._load_political_keywords()
        self.source_credibility = self._load_source_credibility()
        
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
    
    def analyze_news(self, news_item: Dict, market_context: Optional[Dict] = None) -> MVPAnalysisResult:
        """Analyze news using hybrid approach"""
        try:
            # Determine analysis method
            should_use_gpt = self.should_use_gpt_analysis(news_item)
            print(f"🔍 Should use GPT analysis: {should_use_gpt}")
            
            if should_use_gpt:
                print(f"🔍 Attempting GPT analysis...")
                result = self._analyze_with_gpt(news_item, market_context)
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
        
        # Get currency pairs
        currency_pairs = news_item.get('currency_pairs', ['EUR/USD', 'USD/JPY'])
        
        result = MVPAnalysisResult(
            news_impact=news_impact,
            trading_implications=trading_implications,
            immediate_reaction=self._sentiment_to_reaction(sentiment),
            key_pairs=currency_pairs,
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
            }
        )
        
        print(f"🔍 Free analysis - Result news_impact: {result.news_impact[:50]}...")
        print(f"🔍 Free analysis - Result trading_implications: {result.trading_implications[:50]}...")
        
        return result
    
    def _analyze_with_gpt(self, news_item: Dict, market_context: Optional[Dict] = None) -> MVPAnalysisResult:
        """Analyze news using GPT with optimized prompts"""
        try:
            import openai
            import os
            
            print(f"🔍 Starting GPT analysis...")
            
            # Get API key
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print(f"🔍 No OpenAI API key found, falling back to free analysis")
                logger.warning("No OpenAI API key found, falling back to free analysis")
                return self._analyze_with_free(news_item)
            
            print(f"🔍 OpenAI API key found, proceeding with GPT analysis")
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=api_key, timeout=30.0)
            
            # Create enhanced prompt for trader-focused analysis
            title = news_item.get('title', '')
            summary = news_item.get('summary', '')
            source = news_item.get('source', '')
            
            # Extract currency pairs from the news
            currency_pairs = self._extract_currency_pairs(title, summary)
            
            prompt = f"""
You are a senior forex market analyst with 15+ years of experience. Your job is to provide professional, actionable market intelligence for forex traders.

NEWS TO ANALYZE:
Title: {title}
Summary: {summary}
Source: {source}
Affected Currency Pairs: {currency_pairs}

ANALYSIS REQUIREMENTS:

1. **Market Impact Analysis** (2-3 sentences):
   - Explain the specific market implications and sentiment
   - Focus on which currency pairs are most affected and why
   - Include magnitude of expected impact (high/medium/low)
   - Reference current market context and positioning

2. **Trading Intelligence** (2-3 sentences):
   - Provide actionable market intelligence (NOT trade recommendations)
   - Identify key levels to watch and market dynamics
   - Explain what traders should monitor and why
   - Include timeframe expectations and volatility outlook

3. **Currency-Specific Analysis**:
   - Focus on the most relevant currency pairs from the news
   - Explain the specific impact on each major pair
   - Consider cross-market correlations and safe-haven flows

4. **Risk Context**:
   - Identify potential market risks and uncertainties
   - Explain what could amplify or dampen the impact
   - Consider political, economic, and technical factors

IMPORTANT GUIDELINES:
- Be specific about currency pairs and market dynamics
- Provide concrete market intelligence, not generic statements
- Focus on "what to watch" rather than "what to do"
- Consider current market positioning and sentiment
- Include specific price levels and timeframes when relevant
- Avoid generic phrases like "monitor for opportunities"

RESPONSE FORMAT (JSON):
{{
    "news_impact": "Specific market impact explanation with currency focus...",
    "trading_implications": "Actionable market intelligence and what to watch...",
    "immediate_reaction": "bullish_usd|bearish_usd|neutral",
    "key_pairs": ["EUR/USD", "USD/JPY"],
    "volatility": "high|medium|low",
    "timeframe": "specific timeframe like 'next 2-4 hours' or 'London session'",
    "confidence": 85
}}

For immediate_reaction, use ONLY: "bullish_usd", "bearish_usd", or "neutral"
For volatility, use ONLY: "high", "medium", or "low"
For confidence, use 50-95 based on clarity and certainty of the news impact.
"""
            
            # Call GPT
            print(f"🔍 Calling GPT API...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse response
            content = response.choices[0].message.content
            print(f"🔍 GPT response received, length: {len(content)}")
            print(f"🔍 GPT response preview: {content[:200]}...")
            
            try:
                # Try to extract JSON from response
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    print(f"🔍 Extracted JSON: {json_str}")
                    gpt_result = json.loads(json_str)
                    print(f"🔍 JSON parsed successfully")
                else:
                    print(f"🔍 No JSON found in response")
                    raise ValueError("No JSON found in response")
                
                # Create MVP result
                return MVPAnalysisResult(
                    news_impact=gpt_result.get('news_impact', ''),
                    trading_implications=gpt_result.get('trading_implications', ''),
                    immediate_reaction=gpt_result.get('immediate_reaction', 'neutral'),
                    key_pairs=gpt_result.get('key_pairs', ['EUR/USD']),
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
                    }
                )
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse GPT response: {e}")
                logger.error(f"Raw response: {content}")
                # Fallback to free analysis
                return self._analyze_with_free(news_item)
                
        except Exception as e:
            logger.error(f"GPT analysis failed: {e}")
            # Fallback to free analysis
            return self._analyze_with_free(news_item)
    
    def _extract_currency_pairs(self, title: str, summary: str) -> List[str]:
        """Extract relevant currency pairs from news content"""
        text = f"{title} {summary}".lower()
        pairs = []
        
        # Define currency keywords and their corresponding pairs
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
        
        # Check for currency mentions
        for keyword, pair in currency_mapping.items():
            if keyword in text and pair not in pairs:
                pairs.append(pair)
        
        # If no specific currencies found, return major pairs
        if not pairs:
            pairs = ['EUR/USD', 'USD/JPY']
        
        return pairs[:3]  # Limit to top 3 most relevant pairs
    
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
        
        # Extract currency pairs from title
        currency_pairs = self._extract_currency_pairs(title, "")
        pairs_text = ', '.join(currency_pairs[:2])  # Focus on top 2 pairs
        
        if sentiment_text == 'positive':
            return f"{title} from {source} creates bullish sentiment for {pairs_text}. This news suggests strengthening fundamentals that may drive currency appreciation. The development increases probability of upward movements as markets price in improved economic conditions. Focus on {pairs_text} for maximum impact during the next trading session."
        elif sentiment_text == 'negative':
            return f"{title} from {source} creates bearish sentiment for {pairs_text}. This news suggests weakening fundamentals that may drive currency depreciation. The development increases probability of downward movements as markets price in economic challenges. Focus on {pairs_text} for maximum impact during the next trading session."
        else:
            return f"{title} from {source} has mixed implications for {pairs_text}. This news shows neutral sentiment with conflicting signals for affected currencies. The development maintains probability of sideways movements as markets await clearer directional signals. Monitor {pairs_text} for breakout opportunities during the next trading session."
    
    def _generate_trading_implications_paragraph(self, sentiment: Dict, news_item: Dict) -> str:
        """Generate trading implications paragraph"""
        sentiment_text = sentiment['sentiment']
        currency_pairs = self._extract_currency_pairs(news_item.get('title', ''), news_item.get('summary', ''))
        pairs_text = ', '.join(currency_pairs[:2])
        
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
        
        # Extract currency pairs from title
        currency_pairs = self._extract_currency_pairs(title, news_item.get('summary', ''))
        pairs_text = ', '.join(currency_pairs[:2])
        
        return MVPAnalysisResult(
            news_impact=f"{title} from {source} has mixed implications for {pairs_text}. This news shows neutral sentiment with conflicting signals for affected currencies. The development maintains probability of sideways movements as markets await clearer directional signals. Monitor {pairs_text} for breakout opportunities during the next trading session.",
            trading_implications=f"Monitor {pairs_text} for breakout opportunities in either direction. Current neutral sentiment suggests range-bound trading until clearer signals emerge. Expect low to medium volatility during the next 2-4 hours. Key levels to watch: current price ±15 pips for potential breakout zones. Wait for confirmation before taking directional positions.",
            immediate_reaction="neutral",
            key_pairs=currency_pairs,
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
            }
        )

# Create global instance
mvp_news_analyzer = MVPNewsAnalyzer()
