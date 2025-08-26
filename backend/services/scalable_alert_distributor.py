#!/usr/bin/env python3
"""
Scalable Alert Distributor for FXSentinel
Handles efficient distribution of WatcherGuru alerts to thousands of users
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from .alert_service import AlertService
from .firebase_realtime_storage import FirebaseRealtimeStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScalableAlertDistributor:
    def __init__(self):
        """Initialize scalable alert distributor"""
        self.alert_service = AlertService()
        self.firebase_storage = FirebaseRealtimeStorage()
        self.max_concurrent_users = 50  # Process 50 users at a time
        self.user_batch_size = 100  # Process users in batches of 100
        
    async def distribute_watcherguru_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Distribute a single WatcherGuru alert to all eligible users efficiently
        
        Args:
            alert_data: The processed alert data from WatcherGuru
            
        Returns:
            Distribution results with success/failure counts
        """
        try:
            logger.info(f"🚀 Starting distribution of WatcherGuru alert: {alert_data.get('title', 'Unknown')}")
            
            # Get all active users with their preferences
            active_users = await self._get_active_users()
            logger.info(f"📊 Found {len(active_users)} active users")
            
            # Filter users who should receive this alert
            eligible_users = self._filter_eligible_users(active_users, alert_data)
            logger.info(f"🎯 {len(eligible_users)} users eligible for this alert")
            
            # Distribute alerts in batches
            results = await self._distribute_in_batches(eligible_users, alert_data)
            
            # Log distribution results
            success_count = len([r for r in results if r['success']])
            failure_count = len(results) - success_count
            
            logger.info(f"✅ Alert distribution completed: {success_count} successful, {failure_count} failed")
            
            return {
                "success": True,
                "total_users": len(active_users),
                "eligible_users": len(eligible_users),
                "successful_deliveries": success_count,
                "failed_deliveries": failure_count,
                "distribution_time": datetime.now().isoformat(),
                "alert_title": alert_data.get('title', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"❌ Error in alert distribution: {e}")
            return {
                "success": False,
                "error": str(e),
                "distribution_time": datetime.now().isoformat()
            }
    
    async def _get_active_users(self) -> List[Dict[str, Any]]:
        """Get all active users with their alert preferences"""
        try:
            # Get all user settings from Firebase
            users_path = "user_settings"
            all_users = self.firebase_storage._make_request('GET', users_path)
            
            if not all_users or not isinstance(all_users, dict):
                logger.warning("No user settings found")
                return []
            
            active_users = []
            for user_id, user_data in all_users.items():
                if isinstance(user_data, dict):
                    # Check if user has any alert channels enabled
                    has_telegram = user_data.get('channels', {}).get('telegram', {}).get('enabled', False)
                    has_email = user_data.get('channels', {}).get('email', {}).get('enabled', False)
                    
                    if has_telegram or has_email:
                        active_users.append({
                            'user_id': user_id,
                            'settings': user_data
                        })
            
            logger.info(f"Found {len(active_users)} active users with alert preferences")
            return active_users
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def _filter_eligible_users(self, users: List[Dict[str, Any]], alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter users who should receive this specific alert based on their preferences"""
        eligible_users = []
        
        for user in users:
            user_settings = user['settings']
            
            # Check if user should receive this alert
            if self._should_user_receive_alert(user_settings, alert_data):
                eligible_users.append(user)
        
        return eligible_users
    
    def _should_user_receive_alert(self, user_settings: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Check if a specific user should receive this alert based on their preferences"""
        try:
            # Get user preferences
            preferences = user_settings.get('preferences', {})
            
            # Check impact level
            alert_impact = alert_data.get('impact_level', 'medium')
            impact_levels = preferences.get('impactLevels', {})
            if impact_levels and not impact_levels.get(alert_impact, True):
                return False
            
            # Check currency pairs
            alert_pairs = alert_data.get('currency_pairs', [])
            user_pairs = preferences.get('currencyPairs', [])
            if user_pairs and not any(pair in alert_pairs for pair in user_pairs):
                return False
            
            # Check alert type
            alert_type = alert_data.get('type', 'unknown')
            alert_types = preferences.get('alertTypes', {})
            if alert_types and not alert_types.get(alert_type, True):
                return False
            
            # Check quiet hours
            if self._is_quiet_hours(user_settings):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking user alert eligibility: {e}")
            return False
    
    def _is_quiet_hours(self, user_settings: Dict[str, Any]) -> bool:
        """Check if current time is within user's quiet hours"""
        try:
            quiet_hours = user_settings.get('preferences', {}).get('quietHours', {})
            if not quiet_hours:
                return False
            
            current_time = datetime.now().time()
            start_time = datetime.strptime(quiet_hours.get('start', '22:00'), '%H:%M').time()
            end_time = datetime.strptime(quiet_hours.get('end', '06:00'), '%H:%M').time()
            
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:  # Quiet hours span midnight
                return current_time >= start_time or current_time <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False
    
    async def _distribute_in_batches(self, users: List[Dict[str, Any]], alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Distribute alerts to users in batches for better performance"""
        results = []
        
        # Process users in batches
        for i in range(0, len(users), self.user_batch_size):
            batch = users[i:i + self.user_batch_size]
            batch_results = await self._process_user_batch(batch, alert_data)
            results.extend(batch_results)
            
            # Small delay between batches to avoid overwhelming services
            await asyncio.sleep(0.1)
        
        return results
    
    async def _process_user_batch(self, users: List[Dict[str, Any]], alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a batch of users concurrently"""
        try:
            # Create tasks for concurrent processing
            tasks = []
            for user in users:
                task = self._send_alert_to_user(user, alert_data)
                tasks.append(task)
            
            # Execute tasks with concurrency limit
            semaphore = asyncio.Semaphore(self.max_concurrent_users)
            
            async def limited_task(task):
                async with semaphore:
                    return await task
            
            limited_tasks = [limited_task(task) for task in tasks]
            results = await asyncio.gather(*limited_tasks, return_exceptions=True)
            
            # Convert exceptions to error results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'user_id': users[i]['user_id'],
                        'success': False,
                        'error': str(result)
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error processing user batch: {e}")
            return [{'user_id': user['user_id'], 'success': False, 'error': str(e)} for user in users]
    
    async def _send_alert_to_user(self, user: Dict[str, Any], alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to a single user"""
        try:
            user_id = user['user_id']
            user_settings = user['settings']
            
            # Use existing alert service to send the alert
            success = await self.alert_service.send_alert_to_user(user_id, alert_data, user_settings)
            
            return {
                'user_id': user_id,
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending alert to user {user.get('user_id', 'unknown')}: {e}")
            return {
                'user_id': user.get('user_id', 'unknown'),
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global instance
scalable_distributor = ScalableAlertDistributor()
