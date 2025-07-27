"""
Circuit Breaker and Retry Logic for Fault Tolerance

Implements circuit breaker pattern, retry logic, and fallback mechanisms
"""

import asyncio
import time
from typing import Optional, Callable, Any, TypeVar, Union, Dict, List
from functools import wraps
from enum import Enum
from datetime import datetime, timedelta
import random
from contextlib import asynccontextmanager
import logging

from core.logging_config import get_logger
from core.monitoring.datadog_apm import get_apm
from core.cache.redis_cache import get_cache, CacheNamespace

logger = get_logger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        success_threshold: int = 3,
        half_open_max_calls: int = 3,
        exclude_exceptions: Optional[List[type]] = None
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self.half_open_max_calls = half_open_max_calls
        self.exclude_exceptions = exclude_exceptions or []


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        
        # Metrics
        self._metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "rejected_calls": 0,
            "state_changes": 0
        }
        
        # APM
        self.apm = get_apm()
        
        # Cache for distributed state
        self.cache = get_cache()
        self._state_key = f"circuit:{name}:state"
        self._failure_key = f"circuit:{name}:failures"
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        # Try to get from cache for distributed coordination
        cached_state = self.cache.get(CacheNamespace.TEMP, self._state_key)
        if cached_state:
            self._state = CircuitState(cached_state)
        return self._state
    
    @state.setter
    def state(self, value: CircuitState):
        """Set circuit state"""
        old_state = self._state
        self._state = value
        
        # Cache state for distributed coordination
        self.cache.set(CacheNamespace.TEMP, self._state_key, value.value, ttl=300)
        
        if old_state != value:
            self._metrics["state_changes"] += 1
            logger.info(f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {value.value}")
            
            # Record metric
            if self.apm:
                self.apm.record_metric(
                    "circuit_breaker.state_change",
                    1,
                    "counter",
                    {
                        "circuit": self.name,
                        "from_state": old_state.value,
                        "to_state": value.value
                    }
                )
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""
        return asyncio.run(self.acall(func, *args, **kwargs)) if asyncio.iscoroutinefunction(func) else self._call_sync(func, *args, **kwargs)
    
    def _call_sync(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Synchronous call execution"""
        self._metrics["total_calls"] += 1
        
        with self.apm.trace_operation(f"circuit_breaker.{self.name}", {
            "circuit.name": self.name,
            "circuit.state": self.state.value
        }):
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                else:
                    self._metrics["rejected_calls"] += 1
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )
            
            # Check half-open limit
            if self.state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._metrics["rejected_calls"] += 1
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' half-open limit reached"
                    )
                self._half_open_calls += 1
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                self._on_success()
                return result
            
            except Exception as e:
                if self._should_count_failure(e):
                    self._on_failure()
                raise
    
    async def acall(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Asynchronous call execution"""
        self._metrics["total_calls"] += 1
        
        with self.apm.trace_operation(f"circuit_breaker.{self.name}", {
            "circuit.name": self.name,
            "circuit.state": self.state.value
        }):
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                else:
                    self._metrics["rejected_calls"] += 1
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )
            
            # Check half-open limit
            if self.state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._metrics["rejected_calls"] += 1
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' half-open limit reached"
                    )
                self._half_open_calls += 1
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            
            except Exception as e:
                if self._should_count_failure(e):
                    self._on_failure()
                raise
    
    def _should_count_failure(self, exception: Exception) -> bool:
        """Check if exception should count as failure"""
        # Don't count excluded exceptions
        for excluded in self.config.exclude_exceptions:
            if isinstance(exception, excluded):
                return False
        
        # Count if it's the expected exception type
        return isinstance(exception, self.config.expected_exception)
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        return (
            self._last_failure_time and
            time.time() - self._last_failure_time >= self.config.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call"""
        self._metrics["successful_calls"] += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self._reset_counts()
        elif self.state == CircuitState.CLOSED:
            self._reset_counts()
    
    def _on_failure(self):
        """Handle failed call"""
        self._metrics["failed_calls"] += 1
        self._last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self._reset_counts()
        elif self.state == CircuitState.CLOSED:
            self._failure_count += 1
            
            # Cache failure count for distributed tracking
            self.cache.set(
                CacheNamespace.TEMP,
                self._failure_key,
                self._failure_count,
                ttl=300
            )
            
            if self._failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self._reset_counts()
    
    def _reset_counts(self):
        """Reset internal counters"""
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        
        # Clear cached counts
        self.cache.delete(CacheNamespace.TEMP, self._failure_key)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        total = self._metrics["total_calls"]
        success_rate = (
            self._metrics["successful_calls"] / total if total > 0 else 0
        )
        
        return {
            **self._metrics,
            "success_rate": success_rate,
            "current_state": self.state.value,
            "failure_count": self._failure_count
        }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass


# Retry configuration
class RetryConfig:
    """Retry configuration"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: Optional[List[type]] = None,
        dont_retry_on: Optional[List[type]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or [Exception]
        self.dont_retry_on = dont_retry_on or []


class RetryManager:
    """Retry logic implementation"""
    
    def __init__(self, name: str, config: RetryConfig):
        self.name = name
        self.config = config
        self.apm = get_apm()
    
    def _should_retry(self, exception: Exception) -> bool:
        """Check if exception should trigger retry"""
        # Don't retry if in don't_retry_on list
        for exc_type in self.config.dont_retry_on:
            if isinstance(exception, exc_type):
                return False
        
        # Retry if in retry_on list
        for exc_type in self.config.retry_on:
            if isinstance(exception, exc_type):
                return True
        
        return False
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry"""
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay
        )
        
        if self.config.jitter:
            # Add random jitter (±25%)
            jitter = delay * 0.25 * (2 * random.random() - 1)
            delay += jitter
        
        return max(0, delay)
    
    def retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for retry logic"""
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, self.config.max_attempts + 1):
                try:
                    with self.apm.trace_operation(f"retry.{self.name}", {
                        "retry.attempt": attempt,
                        "retry.max_attempts": self.config.max_attempts
                    }):
                        result = func(*args, **kwargs)
                        
                        if attempt > 1:
                            logger.info(
                                f"Retry successful for '{self.name}' "
                                f"after {attempt} attempts"
                            )
                        
                        return result
                
                except Exception as e:
                    last_exception = e
                    
                    if not self._should_retry(e) or attempt >= self.config.max_attempts:
                        logger.error(
                            f"Retry failed for '{self.name}' "
                            f"after {attempt} attempts: {e}"
                        )
                        raise
                    
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retry {attempt}/{self.config.max_attempts} "
                        f"for '{self.name}' failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, self.config.max_attempts + 1):
                try:
                    with self.apm.trace_operation(f"retry.{self.name}", {
                        "retry.attempt": attempt,
                        "retry.max_attempts": self.config.max_attempts
                    }):
                        result = await func(*args, **kwargs)
                        
                        if attempt > 1:
                            logger.info(
                                f"Retry successful for '{self.name}' "
                                f"after {attempt} attempts"
                            )
                        
                        return result
                
                except Exception as e:
                    last_exception = e
                    
                    if not self._should_retry(e) or attempt >= self.config.max_attempts:
                        logger.error(
                            f"Retry failed for '{self.name}' "
                            f"after {attempt} attempts: {e}"
                        )
                        raise
                    
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retry {attempt}/{self.config.max_attempts} "
                        f"for '{self.name}' failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


# Fallback strategies
class FallbackStrategy:
    """Base fallback strategy"""
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute fallback logic"""
        raise NotImplementedError


class ValueFallback(FallbackStrategy):
    """Return a default value"""
    
    def __init__(self, value: Any):
        self.value = value
    
    def execute(self, *args, **kwargs) -> Any:
        return self.value


class CacheFallback(FallbackStrategy):
    """Return cached value"""
    
    def __init__(self, cache_key: str, namespace: str = CacheNamespace.TEMP):
        self.cache_key = cache_key
        self.namespace = namespace
        self.cache = get_cache()
    
    def execute(self, *args, **kwargs) -> Any:
        return self.cache.get(self.namespace, self.cache_key)


class FunctionFallback(FallbackStrategy):
    """Execute alternative function"""
    
    def __init__(self, fallback_func: Callable):
        self.fallback_func = fallback_func
    
    def execute(self, *args, **kwargs) -> Any:
        return self.fallback_func(*args, **kwargs)


# Combined resilience decorator
def resilient(
    circuit_breaker: Optional[str] = None,
    retry: Optional[str] = None,
    fallback: Optional[FallbackStrategy] = None,
    cache_result: bool = False,
    cache_ttl: int = 300
):
    """Combined decorator for resilience patterns"""
    
    def decorator(func):
        # Get circuit breaker and retry manager
        cb = circuit_breakers.get(circuit_breaker) if circuit_breaker else None
        rm = retry_managers.get(retry) if retry else None
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                # Apply retry logic
                if rm:
                    func_with_retry = rm.retry(func)
                else:
                    func_with_retry = func
                
                # Apply circuit breaker
                if cb:
                    result = await cb.acall(func_with_retry, *args, **kwargs)
                else:
                    result = await func_with_retry(*args, **kwargs)
                
                # Cache result if requested
                if cache_result:
                    cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                    get_cache().set(
                        CacheNamespace.TEMP,
                        cache_key,
                        result,
                        ttl=cache_ttl
                    )
                
                return result
            
            except Exception as e:
                if fallback:
                    logger.warning(
                        f"Using fallback for {func.__name__}: {e}"
                    )
                    return fallback.execute(*args, **kwargs)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                # Apply retry logic
                if rm:
                    func_with_retry = rm.retry(func)
                else:
                    func_with_retry = func
                
                # Apply circuit breaker
                if cb:
                    result = cb.call(func_with_retry, *args, **kwargs)
                else:
                    result = func_with_retry(*args, **kwargs)
                
                # Cache result if requested
                if cache_result:
                    cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                    get_cache().set(
                        CacheNamespace.TEMP,
                        cache_key,
                        result,
                        ttl=cache_ttl
                    )
                
                return result
            
            except Exception as e:
                if fallback:
                    logger.warning(
                        f"Using fallback for {func.__name__}: {e}"
                    )
                    return fallback.execute(*args, **kwargs)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global circuit breakers and retry managers
circuit_breakers: Dict[str, CircuitBreaker] = {}
retry_managers: Dict[str, RetryManager] = {}


def register_circuit_breaker(name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
    """Register a circuit breaker"""
    cb = CircuitBreaker(name, config)
    circuit_breakers[name] = cb
    return cb


def register_retry_manager(name: str, config: RetryConfig) -> RetryManager:
    """Register a retry manager"""
    rm = RetryManager(name, config)
    retry_managers[name] = rm
    return rm


# Pre-configured circuit breakers
def setup_default_circuit_breakers():
    """Set up default circuit breakers"""
    
    # Database circuit breaker
    register_circuit_breaker(
        "database",
        CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception,
            exclude_exceptions=[KeyboardInterrupt, SystemExit]
        )
    )
    
    # External API circuit breaker
    register_circuit_breaker(
        "external_api",
        CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )
    )
    
    # Redis circuit breaker
    register_circuit_breaker(
        "redis",
        CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=20
        )
    )


# Pre-configured retry managers
def setup_default_retry_managers():
    """Set up default retry managers"""
    
    # Database retry
    register_retry_manager(
        "database",
        RetryConfig(
            max_attempts=3,
            initial_delay=0.5,
            max_delay=5.0
        )
    )
    
    # External API retry
    register_retry_manager(
        "external_api",
        RetryConfig(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0
        )
    )
    
    # Redis retry
    register_retry_manager(
        "redis",
        RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
            max_delay=1.0
        )
    )