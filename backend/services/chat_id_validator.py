#!/usr/bin/env python3
"""
Chat ID Validator
Validates Telegram chat IDs to reject placeholders and test values
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Invalid chat IDs (placeholders/test values)
INVALID_CHAT_IDS = [
    '123456789',
    '987654321',
    '000000000',
    '111111111',
    'test',
    'mock',
    'placeholder'
]

def validate_chat_id(chat_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a Telegram chat ID
    
    Args:
        chat_id: Chat ID to validate
        
    Returns:
        (is_valid, error_message)
    """
    if not chat_id:
        return False, "Chat ID is empty"
    
    chat_id_str = str(chat_id).strip()
    
    # Check if empty after stripping
    if not chat_id_str:
        return False, "Chat ID is empty"
    
    # Check against known invalid values
    if chat_id_str.lower() in [cid.lower() for cid in INVALID_CHAT_IDS]:
        return False, f"Chat ID is a known placeholder: {chat_id_str}"
    
    # Check if it's a placeholder pattern
    if chat_id_str.lower().startswith('mock_') or chat_id_str.lower().startswith('test_'):
        return False, f"Chat ID appears to be a test value: {chat_id_str}"
    
    # Check if it's too short (likely invalid)
    # Valid Telegram chat IDs are typically 9+ digits
    if len(chat_id_str) < 5:
        return False, f"Chat ID is too short (likely invalid): {chat_id_str}"
    
    # Check if it's all the same digit (likely a placeholder)
    if len(set(chat_id_str)) == 1 and len(chat_id_str) > 3:
        return False, f"Chat ID appears to be a placeholder (all same digits): {chat_id_str}"
    
    # Check if it's numeric (Telegram chat IDs are numeric strings)
    if not chat_id_str.lstrip('-').isdigit():
        return False, f"Chat ID must be numeric: {chat_id_str}"
    
    # Valid chat ID
    return True, None

def is_valid_chat_id(chat_id: str) -> bool:
    """Quick check if chat_id is valid (returns bool only)"""
    is_valid, _ = validate_chat_id(chat_id)
    return is_valid

