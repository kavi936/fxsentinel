#!/usr/bin/env python3
"""
FXSentinel Alert Quality Enhancer
Ensures only high-quality, actionable alerts are sent to users
"""

import os
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlertQualityScore:
    """Quality score for an alert"""
    overall_score: float  # 0.0 to 1.0
    relevance_score: float  # How relevant to forex
    urgency_score: float  # How urgent the news is
    credibility_score: float  # Source credibility
    actionability_score: float  # How actionable the alert is
    user_feedback_score: float  # Historical user feedback
    factors: Dict[str, Any]  # Detailed scoring factors

class AlertQualityEnhancer:
    def __init__(self):
        """Initialize the alert quality enhancer"""
        self.min_quality_threshold = 0.7  # Minimum score to send alert
        self.high_quality_threshold = 0.85  # Score for premium alerts
        
        # Source credibility scores (0.0 to 1.0)
        self.source_credibility = {
            'reuters': 0.95,
            'bloomberg': 0.95,
            'cnbc': 0.90,
            'marketwatch': 0.85,
            'forexfactory': 0.90,
            'fxstreet': 0.85,
            'investing.com': 0.80,
            'fxempire': 0.80,
            'dailyfx': 0.85,
            'fxcm': 0.80,
            'oanda': 0.80,
            'ig': 0.80,
            'watcherguru': 0.90,  # High credibility for forex-specific content
            'forexlive': 0.85,
            'tradingview': 0.80
        }
        
        # Critical forex keywords (automatic high relevance)
        self.critical_forex_keywords = [
            'fed', 'federal reserve', 'ecb', 'european central bank', 'boe', 'bank of england',
            'boj', 'bank of japan', 'rba', 'reserve bank of australia', 'boc', 'bank of canada',
            'nfp', 'non-farm payrolls', 'cpi', 'inflation', 'interest rate', 'monetary policy',
            'rate decision', 'policy meeting', 'speech', 'testimony', 'intervention', 'currency war'
        ]
        
        # High-impact forex keywords
        self.high_impact_keywords = [
            'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe', 'interest rate', 'non-farm payrolls', 'gdp',
            'rate decision', 'policy meeting', 'speech', 'testimony', 'trump', 'biden', 'election',
            'trade war', 'tariff', 'sanctions', 'geopolitical', 'brexit', 'china trade', 'us china',
            'market volatility', 'market uncertainty', 'emergency', 'crisis', 'shock', 'surprise'
        ]
        
        # Actionable keywords (news that suggests trading opportunities)
        self.actionable_keywords = [
            'breakout', 'support', 'resistance', 'key level', 'technical analysis', 'chart pattern',
            'momentum', 'trend', 'reversal', 'consolidation', 'volatility', 'liquidity',
            'position', 'entry', 'exit', 'stop loss', 'take profit', 'risk management'
        ]
        
        # Noise keywords (news that's likely not actionable)
        self.noise_keywords = [
            'daily wrap', 'market recap', 'weekend update', 'holiday schedule', 'market hours',
            'trading holiday', 'market closed', 'regular update', 'routine', 'scheduled',
            'announcement', 'notice', 'reminder', 'update', 'change', 'modification'
        ]
        
        # User feedback tracking
        self.user_feedback = {}  # Track user feedback on alerts
    
    def evaluate_alert_quality(self, news_item: Dict[str, Any], user_preferences: Dict[str, Any]) -> AlertQualityScore:
        """Evaluate the quality of an alert before sending"""
        try:
            title = news_item.get('title', '').lower()
            summary = news_item.get('summary', '').lower()
            content = news_item.get('content', '').lower()
            source = news_item.get('source', '').lower()
            full_text = f"{title} {summary} {content}"
            
            # Calculate individual scores
            relevance_score = self._calculate_relevance_score(full_text, user_preferences)
            urgency_score = self._calculate_urgency_score(news_item)
            credibility_score = self._calculate_credibility_score(source, full_text)
            actionability_score = self._calculate_actionability_score(full_text, news_item)
            user_feedback_score = self._get_user_feedback_score(news_item.get('id'), user_preferences.get('user_id'))
            
            # Calculate overall score with weighted average
            overall_score = (
                relevance_score * 0.25 +
                urgency_score * 0.20 +
                credibility_score * 0.20 +
                actionability_score * 0.25 +
                user_feedback_score * 0.10
            )
            
            # Collect scoring factors for transparency
            factors = {
                'relevance_score': relevance_score,
                'urgency_score': urgency_score,
                'credibility_score': credibility_score,
                'actionability_score': actionability_score,
                'user_feedback_score': user_feedback_score,
                'critical_keywords_found': self._find_critical_keywords(full_text),
                'high_impact_keywords_found': self._find_high_impact_keywords(full_text),
                'actionable_keywords_found': self._find_actionable_keywords(full_text),
                'noise_keywords_found': self._find_noise_keywords(full_text),
                'source_credibility': self.source_credibility.get(source, 0.5),
                'user_preferences_matched': self._check_user_preferences(news_item, user_preferences)
            }
            
            return AlertQualityScore(
                overall_score=overall_score,
                relevance_score=relevance_score,
                urgency_score=urgency_score,
                credibility_score=credibility_score,
                actionability_score=actionability_score,
                user_feedback_score=user_feedback_score,
                factors=factors
            )
            
        except Exception as e:
            logger.error(f"Error evaluating alert quality: {e}")
            # Return low score on error to prevent sending
            return AlertQualityScore(
                overall_score=0.0,
                relevance_score=0.0,
                urgency_score=0.0,
                credibility_score=0.0,
                actionability_score=0.0,
                user_feedback_score=0.0,
                factors={'error': str(e)}
            )
    
    def _calculate_relevance_score(self, text: str, user_preferences: Dict[str, Any]) -> float:
        """Calculate how relevant the news is to forex trading"""
        score = 0.0
        
        # Check for critical forex keywords (automatic high relevance)
        critical_matches = self._find_critical_keywords(text)
        if critical_matches:
            score += 0.8  # High base score for critical keywords
        
        # Check for high-impact keywords
        high_impact_matches = self._find_high_impact_keywords(text)
        score += len(high_impact_matches) * 0.1  # 0.1 per high-impact keyword
        
        # Check user's preferred currency pairs
        user_pairs = user_preferences.get('currencyPairs', [])
        if user_pairs:
            pair_matches = 0
            for pair in user_pairs:
                if pair.lower() in text:
                    pair_matches += 1
            score += (pair_matches / len(user_pairs)) * 0.3  # Up to 0.3 for matching pairs
        
        # Check user's preferred impact levels
        user_impact_levels = user_preferences.get('impactLevels', {})
        if user_impact_levels.get('high', True) and len(critical_matches) > 0:
            score += 0.2
        
        # Penalize noise keywords
        noise_matches = self._find_noise_keywords(text)
        score -= len(noise_matches) * 0.2  # Penalty for noise
        
        return min(1.0, max(0.0, score))
    
    def _calculate_urgency_score(self, news_item: Dict[str, Any]) -> float:
        """Calculate how urgent the news is"""
        score = 0.0
        
        # Check for urgency keywords
        urgency_keywords = ['breaking', 'urgent', 'flash', 'alert', 'emergency', 'crisis', 'shock', 'surprise']
        title = news_item.get('title', '').lower()
        summary = news_item.get('summary', '').lower()
        text = f"{title} {summary}"
        
        urgency_matches = sum(1 for keyword in urgency_keywords if keyword in text)
        score += urgency_matches * 0.2  # 0.2 per urgency keyword
        
        # Check publication time (newer = more urgent)
        published_at = news_item.get('published_at')
        if published_at:
            try:
                pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                time_diff = datetime.now(pub_time.tzinfo) - pub_time
                
                if time_diff.total_seconds() < 300:  # Less than 5 minutes
                    score += 0.4
                elif time_diff.total_seconds() < 1800:  # Less than 30 minutes
                    score += 0.2
                elif time_diff.total_seconds() < 3600:  # Less than 1 hour
                    score += 0.1
            except Exception as e:
                logger.error(f"Error parsing publication time: {e}")
        
        # Check if it's a live event
        if news_item.get('is_live_event', False):
            score += 0.3
        
        return min(1.0, max(0.0, score))
    
    def _calculate_credibility_score(self, source: str, text: str) -> float:
        """Calculate source credibility score"""
        # Get base credibility from source
        base_credibility = self.source_credibility.get(source, 0.5)
        
        # Adjust based on content quality
        adjustments = 0.0
        
        # Check for professional language
        professional_indicators = ['official', 'confirmed', 'announced', 'released', 'statement']
        professional_count = sum(1 for indicator in professional_indicators if indicator in text)
        adjustments += professional_count * 0.05
        
        # Check for specific data/numbers
        if re.search(r'\d+\.?\d*%', text) or re.search(r'\$\d+', text):
            adjustments += 0.1  # Bonus for specific data
        
        # Check for attribution
        if re.search(r'(said|announced|confirmed|reported)', text):
            adjustments += 0.05
        
        return min(1.0, max(0.0, base_credibility + adjustments))
    
    def _calculate_actionability_score(self, text: str, news_item: Dict[str, Any]) -> float:
        """Calculate how actionable the news is for trading"""
        score = 0.0
        
        # Check for actionable keywords
        actionable_matches = self._find_actionable_keywords(text)
        score += len(actionable_matches) * 0.15  # 0.15 per actionable keyword
        
        # Check for specific price levels
        price_patterns = [
            r'\d+\.?\d*',  # Numbers that could be prices
            r'(support|resistance) at \d+\.?\d*',
            r'(above|below) \d+\.?\d*',
            r'(target|level) \d+\.?\d*'
        ]
        
        for pattern in price_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.2
                break
        
        # Check for clear market direction
        direction_keywords = ['bullish', 'bearish', 'rally', 'decline', 'surge', 'drop', 'gain', 'loss']
        direction_matches = sum(1 for keyword in direction_keywords if keyword in text)
        score += direction_matches * 0.1
        
        # Check for time-sensitive information
        time_keywords = ['today', 'this week', 'immediate', 'short-term', 'long-term']
        time_matches = sum(1 for keyword in time_keywords if keyword in text)
        score += time_matches * 0.05
        
        # Bonus for news with clear implications
        if any(keyword in text for keyword in ['impact', 'effect', 'influence', 'drive', 'push']):
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _get_user_feedback_score(self, news_id: str, user_id: str) -> float:
        """Get historical user feedback score for similar news"""
        if not news_id or not user_id:
            return 0.5  # Neutral score if no feedback available
        
        # Get user's historical feedback
        user_key = f"{user_id}_{news_id}"
        feedback = self.user_feedback.get(user_key, [])
        
        if not feedback:
            return 0.5  # Neutral score if no feedback
        
        # Calculate average feedback score
        avg_score = sum(feedback) / len(feedback)
        return avg_score
    
    def _find_critical_keywords(self, text: str) -> List[str]:
        """Find critical forex keywords in text"""
        return [keyword for keyword in self.critical_forex_keywords if keyword in text]
    
    def _find_high_impact_keywords(self, text: str) -> List[str]:
        """Find high-impact keywords in text"""
        return [keyword for keyword in self.high_impact_keywords if keyword in text]
    
    def _find_actionable_keywords(self, text: str) -> List[str]:
        """Find actionable keywords in text"""
        return [keyword for keyword in self.actionable_keywords if keyword in text]
    
    def _find_noise_keywords(self, text: str) -> List[str]:
        """Find noise keywords in text"""
        return [keyword for keyword in self.noise_keywords if keyword in text]
    
    def _check_user_preferences(self, news_item: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, bool]:
        """Check if news matches user preferences"""
        return {
            'currency_pairs_match': self._check_currency_pairs(news_item, user_preferences),
            'impact_level_match': self._check_impact_level(news_item, user_preferences),
            'alert_type_match': self._check_alert_type(news_item, user_preferences),
            'quiet_hours_respected': self._check_quiet_hours(user_preferences)
        }
    
    def _check_currency_pairs(self, news_item: Dict[str, Any], user_preferences: Dict[str, Any]) -> bool:
        """Check if news affects user's preferred currency pairs"""
        user_pairs = user_preferences.get('currencyPairs', [])
        if not user_pairs:
            return True  # No preference = match all
        
        text = f"{news_item.get('title', '')} {news_item.get('summary', '')}".lower()
        return any(pair.lower() in text for pair in user_pairs)
    
    def _check_impact_level(self, news_item: Dict[str, Any], user_preferences: Dict[str, Any]) -> bool:
        """Check if news matches user's preferred impact levels"""
        impact_levels = user_preferences.get('impactLevels', {})
        news_impact = news_item.get('impact', 'medium').lower()
        
        return impact_levels.get(news_impact, True)
    
    def _check_alert_type(self, news_item: Dict[str, Any], user_preferences: Dict[str, Any]) -> bool:
        """Check if news matches user's preferred alert types"""
        alert_types = user_preferences.get('alertTypes', {})
        news_type = news_item.get('type', 'liveNews')
        
        return alert_types.get(news_type, True)
    
    def _check_quiet_hours(self, user_preferences: Dict[str, Any]) -> bool:
        """Check if current time is within user's quiet hours"""
        quiet_hours = user_preferences.get('quietHours', {})
        if not quiet_hours.get('enabled', False):
            return True  # No quiet hours = always allow
        
        current_time = datetime.now().time()
        start_time = datetime.strptime(quiet_hours.get('start', '22:00'), '%H:%M').time()
        end_time = datetime.strptime(quiet_hours.get('end', '06:00'), '%H:%M').time()
        
        if start_time <= end_time:
            return not (start_time <= current_time <= end_time)
        else:
            return not (current_time >= start_time or current_time <= end_time)
    
    def should_send_alert(self, quality_score: AlertQualityScore, user_preferences: Dict[str, Any]) -> Tuple[bool, str]:
        """Determine if alert should be sent based on quality score"""
        # Check minimum quality threshold
        if quality_score.overall_score < self.min_quality_threshold:
            return False, f"Quality score {quality_score.overall_score:.2f} below threshold {self.min_quality_threshold}"
        
        # Check user preferences
        preferences = quality_score.factors.get('user_preferences_matched', {})
        if not preferences.get('currency_pairs_match', True):
            return False, "News doesn't match user's preferred currency pairs"
        
        if not preferences.get('impact_level_match', True):
            return False, "News doesn't match user's preferred impact levels"
        
        if not preferences.get('alert_type_match', True):
            return False, "News doesn't match user's preferred alert types"
        
        if not preferences.get('quiet_hours_respected', True):
            return False, "Current time is within user's quiet hours"
        
        return True, "Alert meets all quality and preference criteria"
    
    def record_user_feedback(self, news_id: str, user_id: str, feedback_score: float):
        """Record user feedback on an alert (0.0 to 1.0)"""
        try:
            user_key = f"{user_id}_{news_id}"
            if user_key not in self.user_feedback:
                self.user_feedback[user_key] = []
            
            self.user_feedback[user_key].append(feedback_score)
            
            # Keep only last 10 feedback entries per user/news combination
            if len(self.user_feedback[user_key]) > 10:
                self.user_feedback[user_key] = self.user_feedback[user_key][-10:]
            
            logger.info(f"Recorded user feedback: {feedback_score} for news {news_id} by user {user_id}")
            
        except Exception as e:
            logger.error(f"Error recording user feedback: {e}")
    
    def get_quality_insights(self, quality_score: AlertQualityScore) -> Dict[str, Any]:
        """Get insights about alert quality for improvement"""
        insights = {
            'overall_quality': 'high' if quality_score.overall_score >= 0.85 else 'medium' if quality_score.overall_score >= 0.7 else 'low',
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # Identify strengths
        if quality_score.relevance_score >= 0.8:
            insights['strengths'].append('Highly relevant to forex markets')
        if quality_score.urgency_score >= 0.8:
            insights['strengths'].append('High urgency and timeliness')
        if quality_score.credibility_score >= 0.8:
            insights['strengths'].append('High source credibility')
        if quality_score.actionability_score >= 0.8:
            insights['strengths'].append('Highly actionable for trading')
        
        # Identify weaknesses
        if quality_score.relevance_score < 0.5:
            insights['weaknesses'].append('Low relevance to forex markets')
        if quality_score.urgency_score < 0.3:
            insights['weaknesses'].append('Low urgency or outdated')
        if quality_score.credibility_score < 0.5:
            insights['weaknesses'].append('Low source credibility')
        if quality_score.actionability_score < 0.3:
            insights['weaknesses'].append('Low actionability for trading')
        
        # Provide recommendations
        if quality_score.relevance_score < 0.5:
            insights['recommendations'].append('Consider filtering for more forex-specific content')
        if quality_score.credibility_score < 0.5:
            insights['recommendations'].append('Verify source credibility before sending')
        if quality_score.actionability_score < 0.3:
            insights['recommendations'].append('Include more specific trading implications')
        
        return insights

# Global instance
alert_quality_enhancer = AlertQualityEnhancer()
