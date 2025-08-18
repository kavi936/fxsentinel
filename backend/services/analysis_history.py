#!/usr/bin/env python3
"""
Analysis History Service
Tracks which news items have been analyzed and stores their analysis results
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class AnalysisRecord:
    """Record of a news analysis"""
    news_id: str
    news_title: str
    news_source: str
    analyzed_at: str
    analysis_type: str  # free_enhanced, gpt_enhanced
    confidence: int
    immediate_reaction: str
    cost: float
    analysis_data: Dict[str, Any]

class AnalysisHistory:
    """Manages analysis history for news items"""
    
    def __init__(self, history_file: str = "analysis_history.json"):
        self.history_file = history_file
        self.max_history_items = 1000  # Keep last 1000 analyses
        
    def add_analysis(self, news_item: Dict[str, Any], analysis_result: Dict[str, Any]) -> bool:
        """Add an analysis record to history"""
        try:
            # Create analysis record
            record = AnalysisRecord(
                news_id=str(news_item.get('id')),
                news_title=news_item.get('title', 'Unknown'),
                news_source=news_item.get('source', 'Unknown'),
                analyzed_at=datetime.now().isoformat(),
                analysis_type=analysis_result.get('analysis_type', 'unknown'),
                confidence=analysis_result.get('confidence', 0),
                immediate_reaction=analysis_result.get('immediate_reaction', 'neutral'),
                cost=analysis_result.get('cost', 0.0),
                analysis_data=analysis_result
            )
            
            # Load existing history
            history = self.load_history()
            
            # Add new record
            history.append(asdict(record))
            
            # Keep only the most recent items
            if len(history) > self.max_history_items:
                history = history[-self.max_history_items:]
            
            # Save updated history
            self.save_history(history)
            
            logger.info(f"Added analysis record for news ID: {record.news_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding analysis record: {e}")
            return False
    
    def get_analysis_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get analysis history from the last N hours"""
        try:
            history = self.load_history()
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_analyses = []
            for record in history:
                try:
                    analyzed_at = datetime.fromisoformat(record.get('analyzed_at', '').replace('Z', '+00:00'))
                    if analyzed_at >= cutoff_time:
                        recent_analyses.append(record)
                except:
                    # If date parsing fails, include the record
                    recent_analyses.append(record)
            
            return recent_analyses
            
        except Exception as e:
            logger.error(f"Error getting analysis history: {e}")
            return []
    
    def get_analyzed_news_ids(self) -> List[str]:
        """Get list of news IDs that have been analyzed"""
        try:
            history = self.load_history()
            return [record.get('news_id') for record in history if record.get('news_id')]
        except Exception as e:
            logger.error(f"Error getting analyzed news IDs: {e}")
            return []
    
    def is_news_analyzed(self, news_id: str) -> bool:
        """Check if a news item has been analyzed"""
        try:
            analyzed_ids = self.get_analyzed_news_ids()
            return str(news_id) in analyzed_ids
        except Exception as e:
            logger.error(f"Error checking if news is analyzed: {e}")
            return False
    
    def get_analysis_for_news(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis for a specific news item"""
        try:
            history = self.load_history()
            
            # Find the most recent analysis for this news ID
            for record in reversed(history):
                if record.get('news_id') == str(news_id):
                    return record.get('analysis_data')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis for news: {e}")
            return None
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get statistics about analysis history"""
        try:
            history = self.load_history()
            
            if not history:
                return {
                    'total_analyses': 0,
                    'analysis_types': {},
                    'total_cost': 0.0,
                    'average_confidence': 0
                }
            
            # Count analysis types
            analysis_types = {}
            total_cost = 0.0
            total_confidence = 0
            
            for record in history:
                analysis_type = record.get('analysis_type', 'unknown')
                analysis_types[analysis_type] = analysis_types.get(analysis_type, 0) + 1
                
                total_cost += record.get('cost', 0.0)
                total_confidence += record.get('confidence', 0)
            
            return {
                'total_analyses': len(history),
                'analysis_types': analysis_types,
                'total_cost': round(total_cost, 4),
                'average_confidence': round(total_confidence / len(history), 1) if history else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis stats: {e}")
            return {
                'total_analyses': 0,
                'analysis_types': {},
                'total_cost': 0.0,
                'average_confidence': 0
            }
    
    def load_history(self) -> List[Dict[str, Any]]:
        """Load analysis history from file"""
        try:
            if not os.path.exists(self.history_file):
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading analysis history: {e}")
            return []
    
    def save_history(self, history: List[Dict[str, Any]]) -> bool:
        """Save analysis history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving analysis history: {e}")
            return False
    
    def clear_history(self) -> bool:
        """Clear all analysis history"""
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
                logger.info("Analysis history cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing analysis history: {e}")
            return False

# Global instance
analysis_history = AnalysisHistory()
