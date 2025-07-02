
import pytest
import pandas as pd
import streamlit as st
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics import compute_basic_stats, performance_over_time
from data_validation import DataValidator
from auth import AuthManager
from sync_engine import TradeDataSyncEngine
from partner_analytics import PartnerAnalyticsTracker
from notification_system import create_system_alert, NotificationType
from error_handler import ErrorHandler, safe_execute

class TestCoreWorkflows:
    """Test core business workflows end-to-end."""
    
    def setup_method(self):
        """Setup test data."""
        self.sample_trades = pd.DataFrame({
            'symbol': ['ES', 'NQ', 'YM'],
            'entry_time': ['2024-01-01 09:30:00', '2024-01-01 10:00:00', '2024-01-01 11:00:00'],
            'exit_time': ['2024-01-01 15:30:00', '2024-01-01 14:00:00', '2024-01-01 16:00:00'],
            'entry_price': [4800.0, 16000.0, 36000.0],
            'exit_price': [4850.0, 15950.0, 36100.0],
            'qty': [1, 1, 1],
            'direction': ['long', 'short', 'long'],
            'pnl': [50.0, 50.0, 100.0],
            'trade_type': ['manual', 'manual', 'manual'],
            'broker': ['test', 'test', 'test']
        })
    
    def test_data_import_workflow(self):
        """Test complete data import and validation workflow."""
        validator = DataValidator()
        
        # Test data validation
        cleaned_df, report = validator.validate_and_clean_data(self.sample_trades)
        
        assert not cleaned_df.empty
        assert report['data_quality_score'] > 80
        assert report['final_rows'] >= 3
        
        # Test analytics computation
        stats = compute_basic_stats(cleaned_df)
        assert 'total_trades' in stats
        assert stats['total_trades'] > 0
        assert 'win_rate' in stats
    
    def test_user_authentication_workflow(self):
        """Test user authentication and authorization workflow."""
        auth_manager = AuthManager()
        
        # Test user creation
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        result = auth_manager.create_user(user_data)
        assert result['success'] is True
        
        # Test login
        login_result = auth_manager.authenticate_user('test@example.com', 'TestPass123!')
        assert login_result is not None
        assert login_result['email'] == 'test@example.com'
    
    def test_partner_analytics_workflow(self):
        """Test partner analytics tracking workflow."""
        tracker = PartnerAnalyticsTracker()
        
        # Test user action tracking
        tracker.track_user_action(
            user_id=1,
            action='trade_uploaded',
            details={'trade_count': 10}
        )
        
        # Test analytics retrieval
        analytics = tracker.get_partner_analytics('test_partner')
        assert 'total_users' in analytics
        assert 'activity_summary' in analytics
    
    def test_error_handling_workflow(self):
        """Test error handling and notification workflow."""
        def failing_function():
            raise ValueError("Test error")
        
        # Test error handler
        result = safe_execute(
            failing_function,
            error_message="Test operation failed",
            default_return="fallback"
        )
        
        assert result == "fallback"
    
    def test_sync_engine_workflow(self):
        """Test sync engine workflow."""
        sync_engine = TradeDataSyncEngine()
        
        # Test sync operation
        with patch.object(sync_engine, '_fetch_trades_from_broker') as mock_fetch:
            mock_fetch.return_value = self.sample_trades
            
            result = sync_engine.sync_trades_for_user(
                user_id=1,
                connector_name='test_broker',
                config={'api_key': 'test'}
            )
            
            assert result['status'] == 'success'
            assert result['trades_synced'] > 0

class TestSecurityWorkflows:
    """Test security-related workflows."""
    
    def test_input_validation(self):
        """Test input validation and sanitization."""
        validator = DataValidator()
        
        # Test SQL injection prevention
        malicious_data = pd.DataFrame({
            'symbol': ["'; DROP TABLE trades; --"],
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
        
        cleaned_df, report = validator.validate_and_clean_data(malicious_data)
        
        # Should clean malicious input
        assert "DROP TABLE" not in str(cleaned_df['symbol'].iloc[0])
    
    def test_authentication_security(self):
        """Test authentication security measures."""
        auth_manager = AuthManager()
        
        # Test password requirements
        weak_passwords = ['123', 'password', 'abc']
        for weak_pass in weak_passwords:
            result = auth_manager.create_user({
                'email': 'test@example.com',
                'password': weak_pass,
                'first_name': 'Test',
                'last_name': 'User'
            })
            assert result['success'] is False
    
    def test_data_access_controls(self):
        """Test data access control mechanisms."""
        # Test that users can only access their own data
        auth_manager = AuthManager()
        
        # Create test users
        user1 = auth_manager.create_user({
            'email': 'user1@example.com',
            'password': 'TestPass123!',
            'first_name': 'User',
            'last_name': 'One'
        })
        
        user2 = auth_manager.create_user({
            'email': 'user2@example.com',
            'password': 'TestPass123!',
            'first_name': 'User',
            'last_name': 'Two'
        })
        
        # Test data isolation
        assert user1['user']['id'] != user2['user']['id']

class TestPerformanceWorkflows:
    """Test performance-related workflows."""
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets."""
        # Create large dataset
        large_data = pd.DataFrame({
            'symbol': ['ES'] * 10000,
            'entry_time': ['2024-01-01 09:30:00'] * 10000,
            'exit_time': ['2024-01-01 15:30:00'] * 10000,
            'entry_price': [4800.0] * 10000,
            'exit_price': [4850.0] * 10000,
            'qty': [1] * 10000,
            'direction': ['long'] * 10000,
            'pnl': [50.0] * 10000,
            'trade_type': ['manual'] * 10000,
            'broker': ['test'] * 10000
        })
        
        import time
        start_time = time.time()
        
        stats = compute_basic_stats(large_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process large dataset in reasonable time
        assert processing_time < 5.0  # Less than 5 seconds
        assert stats['total_trades'] == 10000
    
    def test_memory_usage(self):
        """Test memory usage patterns."""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Process data multiple times
        for i in range(100):
            stats = compute_basic_stats(self.sample_trades)
            del stats
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
