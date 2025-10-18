"""
Retry mechanism for failed Stripe operations
"""
import time
import logging
from typing import Callable, Any, Dict, Optional
from functools import wraps
import stripe
from .error_handler import StripeErrorHandler

logger = logging.getLogger(__name__)

class RetryHandler:
    """Handles retrying failed operations with exponential backoff"""
    
    @staticmethod
    def retry_operation(operation: Callable, max_attempts: int = 3, context: Dict[str, Any] = None, user_id: str = None):
        """
        Retry a Stripe operation with exponential backoff
        
        Args:
            operation: The function to retry
            max_attempts: Maximum number of retry attempts
            context: Additional context for error logging
            user_id: User ID for error logging
            
        Returns:
            The result of the operation if successful
            
        Raises:
            The last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Attempting operation (attempt {attempt}/{max_attempts})")
                return operation()
                
            except stripe.StripeError as e:
                last_exception = e
                
                # Check if we should retry this error
                if not StripeErrorHandler.should_retry(e):
                    logger.warning(f"Non-retryable error on attempt {attempt}: {e}")
                    raise e
                
                # Calculate retry delay
                delay = StripeErrorHandler.get_retry_delay(attempt, max_attempts)
                
                if attempt < max_attempts:
                    logger.warning(f"Retryable error on attempt {attempt}: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Operation failed after {max_attempts} attempts. Last error: {e}")
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                raise e
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
    
    @staticmethod
    def retry_decorator(max_attempts: int = 3):
        """
        Decorator for automatically retrying functions
        
        Usage:
            @RetryHandler.retry_decorator(max_attempts=3)
            def my_stripe_operation():
                # Your Stripe operation here
                pass
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                def operation():
                    return func(*args, **kwargs)
                
                return RetryHandler.retry_operation(operation, max_attempts)
            return wrapper
        return decorator

class PaymentRetryHandler:
    """Specialized retry handler for payment operations"""
    
    @staticmethod
    def retry_payment_operation(operation: Callable, max_attempts: int = 2, context: Dict[str, Any] = None, user_id: str = None):
        """
        Retry payment operations with special handling
        
        Payment operations are more sensitive, so we use fewer retries
        and more specific error handling
        """
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Attempting payment operation (attempt {attempt}/{max_attempts})")
                return operation()
                
            except stripe.CardError as e:
                # Card errors should not be retried
                logger.warning(f"Card error on attempt {attempt}: {e}")
                raise e
                
            except stripe.PaymentIntentError as e:
                # Payment intent errors might be retryable depending on the state
                if e.code == 'payment_intent_payment_attempt_failed':
                    if attempt < max_attempts:
                        delay = 2 ** (attempt - 1)  # 1s, 2s
                        logger.warning(f"Payment attempt failed, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Payment failed after {max_attempts} attempts")
                        raise e
                else:
                    # Other payment intent errors should not be retried
                    logger.warning(f"Non-retryable payment error: {e}")
                    raise e
                    
            except stripe.APIConnectionError as e:
                last_exception = e
                if attempt < max_attempts:
                    delay = 2 ** (attempt - 1)
                    logger.warning(f"API connection error, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"API connection failed after {max_attempts} attempts")
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected payment error: {e}")
                raise e
        
        if last_exception:
            raise last_exception

class WebhookRetryHandler:
    """Specialized retry handler for webhook processing"""
    
    @staticmethod
    def retry_webhook_processing(operation: Callable, max_attempts: int = 3, context: Dict[str, Any] = None):
        """
        Retry webhook processing operations
        
        Webhook processing should be more resilient as webhooks can be redelivered
        """
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Processing webhook (attempt {attempt}/{max_attempts})")
                return operation()
                
            except stripe.SignatureVerificationError as e:
                # Signature errors should not be retried
                logger.error(f"Webhook signature verification failed: {e}")
                raise e
                
            except Exception as e:
                last_exception = e
                logger.error(f"Webhook processing error on attempt {attempt}: {e}")
                
                if attempt < max_attempts:
                    delay = 2 ** (attempt - 1)
                    logger.info(f"Retrying webhook processing in {delay}s...")
                    time.sleep(delay)
        
        if last_exception:
            logger.error(f"Webhook processing failed after {max_attempts} attempts")
            raise last_exception
