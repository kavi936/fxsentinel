#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation
Prevents cascading failures by stopping requests when a service is failing
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests immediately
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    Prevents cascading failures by stopping requests when service is failing
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            success_threshold: Number of successes needed to close circuit
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
        
        self.lock = Lock()
        
        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_rejections = 0
        self.state_changes = 0
    
    def call(self, func: Callable, *args, **kwargs) -> tuple[bool, Any, Optional[str]]:
        """
        Execute function with circuit breaker protection
        
        Returns:
            (success, result, error_message)
        """
        with self.lock:
            self.total_requests += 1
            
            # Check circuit state
            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self.last_failure_time and \
                   (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout:
                    # Move to half-open state
                    self._transition_to_half_open()
                else:
                    # Still open, reject request
                    self.total_rejections += 1
                    logger.warning(f"Circuit breaker {self.name} is OPEN - rejecting request")
                    return False, None, "Circuit breaker is open"
            
            # Try to execute function
            try:
                result = func(*args, **kwargs)
                
                # Check if result indicates success or failure
                # If result is a tuple (success, value, error), extract success
                if isinstance(result, tuple) and len(result) >= 1:
                    success = result[0]
                elif isinstance(result, bool):
                    success = result
                else:
                    # Assume success if no explicit failure
                    success = True
                
                if success:
                    self._record_success()
                    return True, result, None
                else:
                    self._record_failure()
                    error_msg = result[2] if isinstance(result, tuple) and len(result) >= 3 else "Function returned failure"
                    return False, result, error_msg
                    
            except Exception as e:
                self._record_failure()
                logger.error(f"Circuit breaker {self.name} caught exception: {e}")
                return False, None, str(e)
    
    def _record_success(self):
        """Record a successful call"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._transition_to_closed()
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    def _record_failure(self):
        """Record a failed call"""
        with self.lock:
            self.total_failures += 1
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self._transition_to_open()
            elif self.state == CircuitState.HALF_OPEN:
                # Failure in half-open, go back to open
                self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
            self.state_changes += 1
            logger.warning(f"Circuit breaker {self.name} opened after {self.failure_count} failures")
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        if self.state != CircuitState.HALF_OPEN:
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = datetime.now()
            self.state_changes += 1
            self.success_count = 0
            logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN state")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.last_state_change = datetime.now()
            self.state_changes += 1
            self.failure_count = 0
            self.success_count = 0
            logger.info(f"Circuit breaker {self.name} closed - service recovered")
    
    def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        with self.lock:
            self._transition_to_closed()
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            logger.info(f"Circuit breaker {self.name} manually reset")
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        with self.lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'total_requests': self.total_requests,
                'total_failures': self.total_failures,
                'total_rejections': self.total_rejections,
                'state_changes': self.state_changes,
                'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
                'last_state_change': self.last_state_change.isoformat()
            }

# Global circuit breaker instances
_telegram_circuit_breaker = None

def get_telegram_circuit_breaker() -> CircuitBreaker:
    """Get global Telegram API circuit breaker"""
    global _telegram_circuit_breaker
    if _telegram_circuit_breaker is None:
        _telegram_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=2,
            name="telegram_api"
        )
    return _telegram_circuit_breaker

