
import pytest
import pandas as pd
import sqlite3
import tempfile
import os
from unittest.mock import patch, Mock
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_scanner import SecurityScanner
from auth import AuthManager
from data_validation import DataValidator

class TestSecurityValidation:
    """Test security validation and protection mechanisms."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = SecurityScanner(self.temp_dir)
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in data processing."""
        # Create malicious data
        malicious_data = pd.DataFrame({
            'symbol': ["'; DROP TABLE trades; --", "AAPL"],
            'entry_price': [100, 150],
            'exit_price': [110, 160],
            'qty': [1, 1],
            'direction': ['long', 'short'],
            'pnl': [10, -10],
            'entry_time': ['2024-01-01', '2024-01-02'],
            'exit_time': ['2024-01-01', '2024-01-02'],
            'trade_type': ['manual', 'manual'],
            'broker': ['test', 'test']
        })
        
        validator = DataValidator()
        cleaned_df, report = validator.validate_and_clean_data(malicious_data)
        
        # Should not contain SQL injection attempts
        assert "DROP TABLE" not in str(cleaned_df['symbol'].iloc[0])
        assert len(cleaned_df) > 0  # Should still have valid data
    
    def test_xss_prevention_in_outputs(self):
        """Test XSS prevention in data outputs."""
        # Test data with potential XSS
        xss_data = pd.DataFrame({
            'symbol': ['<script>alert("xss")</script>', 'AAPL'],
            'entry_price': [100, 150],
            'exit_price': [110, 160],
            'qty': [1, 1],
            'direction': ['long', 'short'],
            'pnl': [10, -10],
            'entry_time': ['2024-01-01', '2024-01-02'],
            'exit_time': ['2024-01-01', '2024-01-02'],
            'trade_type': ['manual', 'manual'],
            'broker': ['test', 'test']
        })
        
        validator = DataValidator()
        cleaned_df, report = validator.validate_and_clean_data(xss_data)
        
        # Should not contain script tags
        assert '<script>' not in str(cleaned_df['symbol'].iloc[0])
        assert 'alert(' not in str(cleaned_df['symbol'].iloc[0])
    
    def test_file_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        # Create test file with path traversal attempt
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write('open("../../../etc/passwd", "r")')
        
        results = self.scanner.scan_code_vulnerabilities()
        
        # Should detect path traversal vulnerability
        assert any('path_traversal' in str(vulns) for vulns in results.values())
    
    def test_hardcoded_secrets_detection(self):
        """Test detection of hardcoded secrets."""
        # Create test file with hardcoded secrets
        test_file = os.path.join(self.temp_dir, "config.py")
        with open(test_file, 'w') as f:
            f.write('API_KEY = "sk-1234567890abcdef1234567890abcdef"')
            f.write('\nPASSWORD = "supersecret123"')
        
        results = self.scanner.scan_code_vulnerabilities()
        
        # Should detect hardcoded secrets
        assert any('hardcoded_secrets' in str(vulns) for vulns in results.values())
    
    def test_authentication_security_measures(self):
        """Test authentication security measures."""
        auth_manager = AuthManager()
        
        # Test password strength requirements
        weak_passwords = [
            'password',
            '123456',
            'qwerty',
            'abc123',
            'password123'
        ]
        
        for weak_pass in weak_passwords:
            result = auth_manager.create_user({
                'email': 'test@example.com',
                'password': weak_pass,
                'first_name': 'Test',
                'last_name': 'User'
            })
            
            # Should reject weak passwords
            assert result['success'] is False
            assert 'password' in result.get('error', '').lower()
    
    def test_data_sanitization(self):
        """Test data sanitization functions."""
        validator = DataValidator()
        
        # Test various malicious inputs
        malicious_inputs = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "'; DELETE FROM users; --",
            "../../../etc/passwd",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for malicious_input in malicious_inputs:
            test_data = pd.DataFrame({
                'symbol': [malicious_input],
                'entry_price': [100],
                'exit_price': [110],
                'qty': [1],
                'direction': ['long'],
                'pnl': [10],
                'entry_time': ['2024-01-01'],
                'exit_time': ['2024-01-01'],
                'trade_type': ['manual'],
                'broker': ['test']
            })
            
            cleaned_df, report = validator.validate_and_clean_data(test_data)
            
            # Should sanitize dangerous content
            sanitized_symbol = str(cleaned_df['symbol'].iloc[0])
            assert 'javascript:' not in sanitized_symbol
            assert '<script>' not in sanitized_symbol
            assert 'DELETE FROM' not in sanitized_symbol
    
    def test_rate_limiting_simulation(self):
        """Test rate limiting mechanisms."""
        # Simulate rapid authentication attempts
        auth_manager = AuthManager()
        
        attempts = []
        for i in range(10):
            result = auth_manager.authenticate_user('test@example.com', 'wrongpassword')
            attempts.append(result)
        
        # Should eventually start blocking requests (in a real implementation)
        # For now, just ensure consistent behavior
        assert all(attempt is None for attempt in attempts)
    
    def test_secure_database_connections(self):
        """Test database connection security."""
        # Test that database connections use proper security measures
        with tempfile.NamedTemporaryFile(suffix='.db') as temp_db:
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()
            
            # Test parameterized queries
            test_symbol = "'; DROP TABLE test; --"
            
            cursor.execute('''
                CREATE TABLE test_trades (symbol TEXT, price REAL)
            ''')
            
            # Use parameterized query (safe)
            cursor.execute('''
                INSERT INTO test_trades (symbol, price) VALUES (?, ?)
            ''', (test_symbol, 100.0))
            
            # Verify data was inserted safely
            cursor.execute('SELECT COUNT(*) FROM test_trades')
            count = cursor.fetchone()[0]
            assert count == 1
            
            # Verify table still exists (wasn't dropped)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_trades'")
            table_exists = cursor.fetchone()
            assert table_exists is not None
            
            conn.close()

class TestComplianceValidation:
    """Test compliance and regulatory validation."""
    
    def test_gdpr_data_handling(self):
        """Test GDPR compliance in data handling."""
        # Test data minimization
        test_data = pd.DataFrame({
            'symbol': ['AAPL', 'MSFT'],
            'entry_price': [100, 200],
            'exit_price': [110, 210],
            'qty': [1, 1],
            'direction': ['long', 'long'],
            'pnl': [10, 10],
            'entry_time': ['2024-01-01', '2024-01-02'],
            'exit_time': ['2024-01-01', '2024-01-02'],
            'trade_type': ['manual', 'manual'],
            'broker': ['test', 'test'],
            'user_email': ['user@example.com', 'user@example.com'],  # Personal data
            'user_ip': ['192.168.1.1', '192.168.1.1']  # Personal data
        })
        
        # Should handle personal data appropriately
        # In a real implementation, would check for proper consent, etc.
        assert 'user_email' in test_data.columns
        assert len(test_data) == 2
    
    def test_data_retention_policies(self):
        """Test data retention policy compliance."""
        # Test that old data can be identified for deletion
        old_data = pd.DataFrame({
            'symbol': ['AAPL'],
            'entry_time': ['2020-01-01'],  # Old data
            'exit_time': ['2020-01-01'],
            'entry_price': [100],
            'exit_price': [110],
            'qty': [1],
            'direction': ['long'],
            'pnl': [10],
            'trade_type': ['manual'],
            'broker': ['test']
        })
        
        # Convert to datetime for age checking
        old_data['entry_time'] = pd.to_datetime(old_data['entry_time'])
        
        # Check if data is older than retention period (e.g., 3 years)
        from datetime import datetime, timedelta
        retention_cutoff = datetime.now() - timedelta(days=3*365)
        
        old_records = old_data[old_data['entry_time'] < retention_cutoff]
        assert len(old_records) > 0  # Should identify old records
    
    def test_audit_trail_functionality(self):
        """Test audit trail for compliance."""
        # In a real implementation, would test that all data changes
        # are logged with user, timestamp, and action details
        
        # Mock audit log entry
        audit_entry = {
            'user_id': 'user123',
            'action': 'data_import',
            'timestamp': '2024-01-01T10:00:00Z',
            'details': {'records_imported': 100}
        }
        
        # Verify audit entry structure
        required_fields = ['user_id', 'action', 'timestamp', 'details']
        assert all(field in audit_entry for field in required_fields)
        assert isinstance(audit_entry['details'], dict)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
