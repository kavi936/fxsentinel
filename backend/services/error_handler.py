"""
Centralized error handling for Stripe operations
"""
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import stripe

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StripeErrorHandler:
    """Centralized error handling for Stripe operations"""
    
    # Stripe error codes and their user-friendly messages
    STRIPE_ERROR_MESSAGES = {
        # Card errors
        'card_declined': 'Your card was declined. Please try a different payment method.',
        'expired_card': 'Your card has expired. Please update your payment method.',
        'incorrect_cvc': 'The security code (CVC) is incorrect. Please check and try again.',
        'insufficient_funds': 'Your card has insufficient funds. Please try a different card.',
        'invalid_cvc': 'The security code (CVC) is invalid. Please check and try again.',
        'invalid_expiry_month': 'The expiration month is invalid. Please check and try again.',
        'invalid_expiry_year': 'The expiration year is invalid. Please check and try again.',
        'invalid_number': 'The card number is invalid. Please check and try again.',
        
        # Payment errors
        'payment_intent_authentication_failure': 'Payment authentication failed. Please try again.',
        'payment_intent_payment_attempt_failed': 'Payment attempt failed. Please try again.',
        'payment_intent_unexpected_state': 'Payment processing error. Please contact support.',
        
        # Customer errors
        'customer_max_payment_methods': 'Maximum payment methods reached. Please remove an existing method.',
        'customer_max_subscriptions': 'Maximum subscriptions reached. Please cancel an existing subscription.',
        
        # Subscription errors
        'subscription_incomplete': 'Subscription setup incomplete. Please try again.',
        'subscription_incomplete_expired': 'Subscription setup expired. Please start over.',
        'subscription_payment_intent_requires_action': 'Additional authentication required. Please complete the payment.',
        
        # General errors
        'api_connection_error': 'Connection error. Please check your internet and try again.',
        'api_error': 'Service temporarily unavailable. Please try again later.',
        'authentication_error': 'Authentication error. Please log in again.',
        'invalid_request_error': 'Invalid request. Please try again.',
        'rate_limit_error': 'Too many requests. Please wait a moment and try again.',
        'validation_error': 'Invalid data provided. Please check your information and try again.',
    }
    
    @staticmethod
    def get_user_friendly_message(stripe_error: stripe.error.StripeError) -> str:
        """Convert Stripe error to user-friendly message"""
        error_code = getattr(stripe_error, 'code', None)
        
        # Check if we have a specific message for this error
        if error_code and error_code in StripeErrorHandler.STRIPE_ERROR_MESSAGES:
            return StripeErrorHandler.STRIPE_ERROR_MESSAGES[error_code]
        
        # Check for nested card errors
        if hasattr(stripe_error, 'decline_code') and stripe_error.decline_code:
            decline_code = stripe_error.decline_code
            if decline_code in StripeErrorHandler.STRIPE_ERROR_MESSAGES:
                return StripeErrorHandler.STRIPE_ERROR_MESSAGES[decline_code]
        
        # Generic messages based on error type
        if isinstance(stripe_error, stripe.error.CardError):
            return "There was an issue with your card. Please check your payment details and try again."
        elif isinstance(stripe_error, stripe.error.InvalidRequestError):
            return "Invalid request. Please check your information and try again."
        elif isinstance(stripe_error, stripe.error.AuthenticationError):
            return "Authentication error. Please log in again."
        elif isinstance(stripe_error, stripe.error.APIConnectionError):
            return "Connection error. Please check your internet and try again."
        elif isinstance(stripe_error, stripe.error.StripeError):
            return "Payment processing error. Please try again or contact support."
        else:
            return "An unexpected error occurred. Please try again or contact support."
    
    @staticmethod
    def log_error(error: Exception, context: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
        """Log error with context for debugging"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'user_id': user_id
        }
        
        # Log to console/file
        logger.error(f"Stripe Error: {error_info['error_type']} - {error_info['error_message']}")
        logger.error(f"Context: {error_info['context']}")
        logger.error(f"User ID: {error_info['user_id']}")
        logger.error(f"Traceback: {error_info['traceback']}")
        
        return error_info
    
    @staticmethod
    def handle_stripe_error(error: stripe.error.StripeError, context: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
        """Handle Stripe errors and return appropriate response"""
        # Log the error
        error_info = StripeErrorHandler.log_error(error, context, user_id)
        
        # Get user-friendly message
        user_message = StripeErrorHandler.get_user_friendly_message(error)
        
        # Determine HTTP status code
        if isinstance(error, stripe.error.CardError):
            status_code = 400
        elif isinstance(error, stripe.error.InvalidRequestError):
            status_code = 400
        elif isinstance(error, stripe.error.AuthenticationError):
            status_code = 401
        elif isinstance(error, stripe.error.APIConnectionError):
            status_code = 503
        elif isinstance(error, stripe.error.RateLimitError):
            status_code = 429
        else:
            status_code = 500
        
        return {
            'success': False,
            'error': user_message,
            'error_code': getattr(error, 'code', None),
            'status_code': status_code,
            'error_id': error_info['timestamp'],  # For tracking in logs
            'debug_info': error_info if context and context.get('debug', False) else None
        }
    
    @staticmethod
    def handle_general_error(error: Exception, context: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
        """Handle general errors (non-Stripe)"""
        error_info = StripeErrorHandler.log_error(error, context, user_id)
        
        return {
            'success': False,
            'error': 'An unexpected error occurred. Please try again or contact support.',
            'status_code': 500,
            'error_id': error_info['timestamp'],
            'debug_info': error_info if context and context.get('debug', False) else None
        }
    
    @staticmethod
    def create_error_response(error: Exception, context: Dict[str, Any] = None, user_id: str = None) -> tuple:
        """Create Flask response tuple for errors"""
        if isinstance(error, stripe.error.StripeError):
            error_data = StripeErrorHandler.handle_stripe_error(error, context, user_id)
        else:
            error_data = StripeErrorHandler.handle_general_error(error, context, user_id)
        
        return error_data, error_data['status_code']
    
    @staticmethod
    def should_retry(error: stripe.error.StripeError) -> bool:
        """Determine if an operation should be retried"""
        # Retry on connection errors and rate limits
        if isinstance(error, (stripe.error.APIConnectionError, stripe.error.RateLimitError)):
            return True
        
        # Don't retry on card errors or authentication errors
        if isinstance(error, (stripe.error.CardError, stripe.error.AuthenticationError)):
            return False
        
        # Don't retry on invalid requests
        if isinstance(error, stripe.error.InvalidRequestError):
            return False
        
        return False
    
    @staticmethod
    def get_retry_delay(attempt: int, max_attempts: int = 3) -> int:
        """Calculate retry delay with exponential backoff"""
        if attempt >= max_attempts:
            return 0
        
        # Exponential backoff: 1s, 2s, 4s
        return min(2 ** (attempt - 1), 60)  # Max 60 seconds
