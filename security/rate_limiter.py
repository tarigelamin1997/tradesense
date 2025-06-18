
import time
from collections import defaultdict, deque
from typing import Dict, Optional
import streamlit as st

class RateLimiter:
    """Simple rate limiter for protecting endpoints."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        user_requests = self.requests[identifier]
        while user_requests and user_requests[0] < window_start:
            user_requests.popleft()
        
        # Check if under limit
        if len(user_requests) >= self.max_requests:
            return False
        
        # Add current request
        user_requests.append(now)
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        return max(0, self.max_requests - len(self.requests[identifier]))
    
    def get_reset_time(self, identifier: str) -> Optional[float]:
        """Get time when rate limit resets."""
        user_requests = self.requests[identifier]
        if not user_requests:
            return None
        return user_requests[0] + self.window_seconds

# Global rate limiter
rate_limiter = RateLimiter()

def rate_limit_check(identifier: str = None) -> bool:
    """Streamlit-compatible rate limit check."""
    if identifier is None:
        # Use session ID as identifier
        identifier = st.session_state.get('session_id', 'anonymous')
    
    if not rate_limiter.is_allowed(identifier):
        remaining_time = rate_limiter.get_reset_time(identifier)
        if remaining_time:
            wait_time = int(remaining_time - time.time())
            st.error(f"Rate limit exceeded. Please wait {wait_time} seconds.")
        return False
    return True
