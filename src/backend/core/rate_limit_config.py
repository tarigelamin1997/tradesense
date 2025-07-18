"""
Rate limiting configuration for production
"""
from datetime import timedelta
from typing import Dict, Any

# Rate limit tiers by subscription plan
RATE_LIMITS = {
    "free": {
        "requests_per_hour": 100,
        "requests_per_minute": 10,
        "api_calls_per_day": 1000,
        "csv_uploads_per_day": 3,
        "trades_per_month": 100,
        "journal_entries_per_month": 50
    },
    "pro": {
        "requests_per_hour": 1000,
        "requests_per_minute": 50,
        "api_calls_per_day": 10000,
        "csv_uploads_per_day": 20,
        "trades_per_month": -1,  # Unlimited
        "journal_entries_per_month": -1  # Unlimited
    },
    "enterprise": {
        "requests_per_hour": -1,  # Unlimited
        "requests_per_minute": -1,  # Unlimited
        "api_calls_per_day": -1,  # Unlimited
        "csv_uploads_per_day": -1,  # Unlimited
        "trades_per_month": -1,  # Unlimited
        "journal_entries_per_month": -1  # Unlimited
    }
}

# Endpoint-specific rate limits
ENDPOINT_LIMITS = {
    # Auth endpoints - stricter limits
    "/api/v1/auth/login": {
        "requests_per_minute": 5,
        "requests_per_hour": 20,
        "lockout_duration": timedelta(minutes=15)
    },
    "/api/v1/auth/register": {
        "requests_per_minute": 3,
        "requests_per_hour": 10,
        "lockout_duration": timedelta(minutes=30)
    },
    "/api/v1/auth/forgot-password": {
        "requests_per_minute": 2,
        "requests_per_hour": 5,
        "lockout_duration": timedelta(hours=1)
    },
    
    # Data endpoints - moderate limits
    "/api/v1/trades": {
        "requests_per_minute": 30,
        "requests_per_hour": 500
    },
    "/api/v1/journal/entries": {
        "requests_per_minute": 20,
        "requests_per_hour": 300
    },
    
    # Analytics endpoints - relaxed limits for pro/enterprise
    "/api/v1/analytics/*": {
        "requests_per_minute": 20,
        "requests_per_hour": 200,
        "pro_multiplier": 5,
        "enterprise_multiplier": -1  # Unlimited
    },
    
    # Upload endpoints - strict limits
    "/api/v1/trades/import": {
        "requests_per_minute": 1,
        "requests_per_hour": 10,
        "requests_per_day": 20
    }
}

# IP-based blocking rules
IP_BLOCKING_RULES = {
    "max_failed_logins": 5,
    "failed_login_window": timedelta(minutes=15),
    "block_duration": timedelta(hours=1),
    "permanent_block_threshold": 20,
    "whitelist": []  # Add trusted IPs here
}

# API key rate limits for external integrations
API_KEY_LIMITS = {
    "default": {
        "requests_per_second": 10,
        "requests_per_minute": 100,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    },
    "premium": {
        "requests_per_second": 50,
        "requests_per_minute": 500,
        "requests_per_hour": 10000,
        "requests_per_day": 100000
    }
}

def get_rate_limit_headers(remaining: int, limit: int, reset_time: int) -> Dict[str, str]:
    """Generate rate limit headers for response"""
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_time),
        "Retry-After": str(max(0, reset_time - int(timedelta(seconds=1).total_seconds())))
    }