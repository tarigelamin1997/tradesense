"""
Security-specific metrics for TradeSense
"""
from prometheus_client import Counter, Histogram, Gauge


class SecurityMetrics:
    """Container for security-related metrics"""
    
    def __init__(self):
        # MFA metrics
        self.mfa_setup_started = Counter(
            'tradesense_mfa_setup_started_total',
            'MFA setup attempts started',
            ['method']
        )
        
        self.mfa_enabled = Counter(
            'tradesense_mfa_enabled_total',
            'MFA enabled by users',
            ['method']
        )
        
        self.mfa_disabled = Counter(
            'tradesense_mfa_disabled_total',
            'MFA disabled by users'
        )
        
        self.mfa_verifications = Counter(
            'tradesense_mfa_verifications_total',
            'MFA verification attempts',
            ['method', 'result']
        )
        
        self.mfa_codes_sent = Counter(
            'tradesense_mfa_codes_sent_total',
            'MFA codes sent',
            ['method']
        )
        
        self.backup_codes_used = Counter(
            'tradesense_mfa_backup_codes_used_total',
            'Backup codes used'
        )
        
        self.mfa_device_removed = Counter(
            'tradesense_mfa_device_removed_total',
            'MFA devices removed'
        )
        
        # Authentication metrics
        self.login_attempts = Counter(
            'tradesense_login_attempts_total',
            'Login attempts',
            ['result', 'method']
        )
        
        self.password_resets = Counter(
            'tradesense_password_resets_total',
            'Password reset requests'
        )
        
        # Security events
        self.security_events = Counter(
            'tradesense_security_events_total',
            'Security events',
            ['event_type', 'severity']
        )
        
        self.failed_auth_attempts = Counter(
            'tradesense_failed_auth_attempts_total',
            'Failed authentication attempts',
            ['reason']
        )
        
        # Rate limiting
        self.rate_limit_hits = Counter(
            'tradesense_rate_limit_hits_total',
            'Rate limit hits',
            ['endpoint', 'limit_type']
        )


# Create global instance
security_metrics = SecurityMetrics()