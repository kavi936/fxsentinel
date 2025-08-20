#!/usr/bin/env python3
"""
Firebase Realtime Database Storage for Alerts System
Uses Firebase Realtime Database instead of Firestore
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseRealtimeStorage:
    def __init__(self):
        self.project_id = os.getenv('FIREBASE_PROJECT_ID', 'fxsentinel')
        self.database_url = os.getenv('FIREBASE_REALTIME_URL', f"https://{self.project_id}-default-rtdb.firebaseio.com")
        
        # For Realtime Database, we don't need service account credentials
        # The database is accessed via REST API with simple authentication
        
        # Default alert settings
        self.default_settings = {
            "impact_levels": {"high": True, "medium": True, "low": False},
            "alert_types": {"preNews": True, "postNews": True, "liveNews": True},
            "currency_pairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
            "quiet_hours": {"enabled": False, "start": "22:00", "end": "06:00", "timezone": "UTC"}
        }
    

    
    def _make_request(self, method: str, path: str, data: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to Firebase Realtime Database"""
        try:
            url = f"{self.database_url}/{path}.json"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Firebase Realtime Database request failed: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error making Firebase request: {e}")
            return {}
    
    def get_user_alert_settings(self, user_id: str) -> Dict[str, Any]:
        """Get user alert settings from Firebase Realtime Database"""
        try:
            logger.info(f"Getting alert settings for user {user_id} from Firebase Realtime Database")
            # Hash user_id to create a safe path for Firebase (no special characters)
            import hashlib
            safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
            path = f"alerts/users/{safe_user_id}/settings"
            logger.info(f"Making request to: {self.database_url}/{path}.json")
            result = self._make_request('GET', path)
            
            # Check if user exists (empty dict means user doesn't exist)
            logger.info(f"DEBUG: Result type: {type(result)}, Result value: {result}")
            if result is None or result == {}:
                # User doesn't exist, return None for security checks
                logger.info(f"User {user_id} not found, returning None for security check")
                return None
            
            # Merge with defaults for missing fields
            settings = self.default_settings.copy()
            if isinstance(result, dict):
                settings.update(result)
            
            logger.info(f"Retrieved alert settings for user {user_id}")
            return settings
            
        except Exception as e:
            logger.error(f"Error getting user alert settings: {e}")
            return None
    
    def update_user_alert_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """Update user alert settings in Firebase Realtime Database"""
        try:
            # Hash user_id to create a safe path for Firebase (no special characters)
            import hashlib
            safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
            path = f"alerts/users/{safe_user_id}/settings"
            result = self._make_request('PUT', path, settings)
            
            if result is not None:
                logger.info(f"Updated alert settings for user {user_id}")
                return True
            else:
                logger.error(f"Failed to update alert settings for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating user alert settings: {e}")
            return False
    
    def log_alert_history(self, user_id: str, alert_data: Dict[str, Any]) -> bool:
        """Log alert to user's history in Firebase Realtime Database"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in alert_data:
                alert_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Hash user_id to create a safe path for Firebase (no special characters)
            import hashlib
            safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
            path = f"alerts/users/{safe_user_id}/history"
            result = self._make_request('POST', path, alert_data)
            
            if result and 'name' in result:
                logger.info(f"Logged alert to history for user {user_id}")
                return True
            else:
                logger.error(f"Failed to log alert to history for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging alert history: {e}")
            return False
    
    def get_user_alert_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's alert history from Firebase Realtime Database"""
        try:
            # Hash user_id to create a safe path for Firebase (no special characters)
            import hashlib
            safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
            path = f"alerts/users/{safe_user_id}/history"
            result = self._make_request('GET', path)
            
            if not result:
                return []
            
            # Convert Firebase object format to list
            history = []
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, dict):
                        value['id'] = key
                        history.append(value)
            
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Limit results
            history = history[:limit]
            
            logger.info(f"Retrieved {len(history)} alert history items for user {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"Error getting user alert history: {e}")
            return []
    
    def get_all_users_with_alerts(self) -> List[Dict[str, Any]]:
        """Get all users who have alert settings configured"""
        try:
            path = "alerts/users"
            result = self._make_request('GET', path)
            
            if not result:
                return []
            
            users = []
            for user_id, user_data in result.items():
                if isinstance(user_data, dict) and 'settings' in user_data:
                    users.append({
                        'user_id': user_id,
                        'settings': user_data.get('settings', {}),
                        'telegram_chat_id': user_data.get('telegram_chat_id')
                    })
            
            logger.info(f"Retrieved {len(users)} users with alert settings")
            return users
            
        except Exception as e:
            logger.error(f"Error getting users with alerts: {e}")
            return []
    
    def save_telegram_chat_id(self, user_id: str, chat_id: str) -> bool:
        """Save user's Telegram chat ID"""
        try:
            # Hash user_id to create a safe path for Firebase (no special characters)
            import hashlib
            safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
            path = f"alerts/users/{safe_user_id}/telegram_chat_id"
            result = self._make_request('PUT', path, chat_id)
            
            if result is not None:
                logger.info(f"Saved Telegram chat ID for user {user_id}")
                return True
            else:
                logger.error(f"Failed to save Telegram chat ID for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving Telegram chat ID: {e}")
            return False
    
    def get_telegram_chat_id(self, user_id: str) -> Optional[str]:
        """Get user's Telegram chat ID"""
        try:
            # Hash user_id to create a safe path for Firebase (no special characters)
            import hashlib
            safe_user_id = hashlib.md5(user_id.encode()).hexdigest()
            path = f"alerts/users/{safe_user_id}/telegram_chat_id"
            result = self._make_request('GET', path)
            
            if result:
                logger.info(f"Retrieved Telegram chat ID for user {user_id}")
                return str(result)
            else:
                logger.info(f"No Telegram chat ID found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Telegram chat ID: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test Firebase Realtime Database connection"""
        try:
            path = "test"
            test_data = {"timestamp": datetime.utcnow().isoformat(), "test": True}
            
            # Test write
            write_result = self._make_request('PUT', path, test_data)
            if write_result is None:
                logger.error("Failed to write test data to Firebase")
                return False
            
            # Test read
            read_result = self._make_request('GET', path)
            if not read_result:
                logger.error("Failed to read test data from Firebase")
                return False
            
            # Clean up
            self._make_request('DELETE', path)
            
            logger.info("Firebase Realtime Database connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Firebase Realtime Database connection test failed: {e}")
            return False
