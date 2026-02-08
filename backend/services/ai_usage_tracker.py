"""
AI Analysis Usage Tracker
Tracks which users are using AI analysis features for analytics and feedback collection
"""
import os
from datetime import datetime, timezone, timedelta
from firebase_admin import firestore
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class AIUsageTracker:
    """Track AI analysis usage per user"""
    
    def __init__(self):
        try:
            self.db = firestore.client()
            self.firebase_available = True
            logger.info("✅ AI Usage Tracker initialized with Firestore")
        except Exception as e:
            logger.warning(f"⚠️ Firebase not available for AI Usage Tracker: {e}")
            self.db = None
            self.firebase_available = False
    
    def track_analysis_usage(self, user_info: dict, analysis_type: str, event_id: str = None, 
                            model_used: str = None, cost_estimate: float = None, 
                            cache_hit: bool = False):
        """
        Track AI analysis usage for a user
        
        Args:
            user_info: Dict with user_id, user_email, user_name
            analysis_type: Type of analysis (e.g., 'pre-event', 'post-event', 'news')
            event_id: ID of the event/news item analyzed
            model_used: GPT model used (e.g., 'gpt-4-turbo', 'gpt-3.5-turbo')
            cost_estimate: Estimated cost of the analysis
            cache_hit: Whether this was a cached result
        """
        if not self.firebase_available or not self.db:
            logger.debug("Firebase not available, skipping usage tracking")
            return
        
        if not user_info or not user_info.get('user_id'):
            logger.debug("No user info provided, skipping usage tracking")
            return
        
        try:
            user_id = user_info.get('user_id')
            user_email = user_info.get('user_email', '')
            user_name = user_info.get('user_name', '')
            
            # Create usage log entry
            usage_log = {
                'user_id': user_id,
                'user_email': user_email,
                'user_name': user_name,
                'analysis_type': analysis_type,
                'event_id': event_id,
                'model_used': model_used,
                'cost_estimate': cost_estimate,
                'cache_hit': cache_hit,
                'timestamp': datetime.now(timezone.utc),
                'date': datetime.now(timezone.utc).date().isoformat()  # For easy querying by date
            }
            
            # Add to usage_logs collection
            self.db.collection('ai_usage_logs').add(usage_log)
            
            # Update user's last_ai_usage timestamp and increment counters
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                # Update existing user document
                update_data = {
                    'last_ai_usage': datetime.now(timezone.utc),
                    'last_ai_usage_type': analysis_type,
                    'total_ai_analyses': firestore.Increment(1)
                }
                
                # Track by date for daily stats
                today = datetime.now(timezone.utc).date().isoformat()
                update_data[f'daily_ai_usage.{today}'] = firestore.Increment(1)
                
                user_ref.update(update_data)
            else:
                # Create user document if it doesn't exist
                user_ref.set({
                    'user_id': user_id,
                    'user_email': user_email,
                    'user_name': user_name,
                    'last_ai_usage': datetime.now(timezone.utc),
                    'last_ai_usage_type': analysis_type,
                    'total_ai_analyses': 1,
                    'first_ai_usage': datetime.now(timezone.utc),
                    f'daily_ai_usage.{datetime.now(timezone.utc).date().isoformat()}': 1
                })
            
            logger.info(f"✅ Tracked AI usage for user: {user_email or user_id} ({analysis_type})")
            
        except Exception as e:
            logger.error(f"❌ Error tracking AI usage: {e}")
            # Don't raise - tracking failures shouldn't break the analysis
    
    def get_user_usage_stats(self, user_id: str):
        """Get usage statistics for a specific user"""
        if not self.firebase_available or not self.db:
            return None
        
        try:
            user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                return None
            
            user_data = user_doc.to_dict()
            
            # Get recent usage logs
            recent_logs = self.db.collection('ai_usage_logs')\
                .where('user_id', '==', user_id)\
                .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                .limit(50)\
                .stream()
            
            logs = [log.to_dict() for log in recent_logs]
            
            return {
                'user_id': user_id,
                'user_email': user_data.get('user_email', ''),
                'user_name': user_data.get('user_name', ''),
                'total_analyses': user_data.get('total_ai_analyses', 0),
                'last_usage': user_data.get('last_ai_usage'),
                'last_usage_type': user_data.get('last_ai_usage_type'),
                'first_usage': user_data.get('first_ai_usage'),
                'recent_logs': logs
            }
        except Exception as e:
            logger.error(f"Error getting user usage stats: {e}")
            return None
    
    def get_active_users(self, days: int = 7, min_analyses: int = 1):
        """
        Get list of users who have used AI features in the last N days
        
        Args:
            days: Number of days to look back
            min_analyses: Minimum number of analyses to be considered active
        """
        if not self.firebase_available or not self.db:
            return []
        
        try:
            cutoff_date = datetime.now(timezone.utc).date() - timedelta(days=days)
            
            # Query users with recent AI usage
            users_query = self.db.collection('users')\
                .where('last_ai_usage', '>=', datetime.combine(cutoff_date, datetime.min.time()).replace(tzinfo=timezone.utc))\
                .where('total_ai_analyses', '>=', min_analyses)\
                .order_by('last_ai_usage', direction=firestore.Query.DESCENDING)\
                .stream()
            
            active_users = []
            for user_doc in users_query:
                user_data = user_doc.to_dict()
                active_users.append({
                    'user_id': user_doc.id,
                    'user_email': user_data.get('user_email', ''),
                    'user_name': user_data.get('user_name', ''),
                    'total_analyses': user_data.get('total_ai_analyses', 0),
                    'last_usage': user_data.get('last_ai_usage'),
                    'last_usage_type': user_data.get('last_ai_usage_type')
                })
            
            return active_users
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []

# Global instance
ai_usage_tracker = AIUsageTracker()
