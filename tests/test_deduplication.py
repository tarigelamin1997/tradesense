
import pytest
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import os

from deduplication_manager import TradeDeduplicationManager, DuplicateMatchType
from models.trade_model import TradeRecord, TradeDirection, TradeType

class TestTradeDeduplication:
    """Test suite for trade deduplication functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.dedup_manager = TradeDeduplicationManager(self.temp_db.name)
        self.test_user_id = 1
    
    def teardown_method(self):
        """Clean up test environment."""
        os.unlink(self.temp_db.name)
    
    def create_test_trade(self, symbol="AAPL", entry_price=150.0, exit_price=155.0, 
                         entry_time=None, exit_time=None, **kwargs):
        """Helper to create test trade data."""
        if entry_time is None:
            entry_time = datetime.now() - timedelta(hours=2)
        if exit_time is None:
            exit_time = datetime.now() - timedelta(hours=1)
            
        return {
            "symbol": symbol,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "qty": kwargs.get("qty", 100),
            "direction": kwargs.get("direction", "long"),
            "pnl": kwargs.get("pnl", (exit_price - entry_price) * kwargs.get("qty", 100)),
            "trade_type": kwargs.get("trade_type", "stocks"),
            "broker": kwargs.get("broker", "TestBroker"),
            "data_source": kwargs.get("data_source", "test")
        }
    
    def test_exact_hash_generation(self):
        """Test exact hash generation for identical trades."""
        trade1 = self.create_test_trade()
        trade2 = self.create_test_trade()
        
        hash1 = self.dedup_manager.generate_exact_hash(trade1)
        hash2 = self.dedup_manager.generate_exact_hash(trade2)
        
        assert hash1 == hash2, "Identical trades should have same exact hash"
        
        # Different trade should have different hash
        trade3 = self.create_test_trade(symbol="TSLA")
        hash3 = self.dedup_manager.generate_exact_hash(trade3)
        
        assert hash1 != hash3, "Different trades should have different exact hashes"
    
    def test_fuzzy_hash_generation(self):
        """Test fuzzy hash generation for similar trades."""
        base_time = datetime.now()
        
        trade1 = self.create_test_trade(
            entry_time=base_time,
            exit_time=base_time + timedelta(hours=1)
        )
        
        # Trade with slight time difference (within tolerance)
        trade2 = self.create_test_trade(
            entry_time=base_time + timedelta(minutes=2),
            exit_time=base_time + timedelta(hours=1, minutes=2)
        )
        
        hash1 = self.dedup_manager.generate_fuzzy_hash(trade1)
        hash2 = self.dedup_manager.generate_fuzzy_hash(trade2)
        
        assert hash1 == hash2, "Similar trades should have same fuzzy hash"
    
    def test_exact_duplicate_detection(self):
        """Test detection of exact duplicates."""
        trade_data = self.create_test_trade()
        
        # Register the first trade
        trade_record = TradeRecord.from_dict(trade_data)
        self.dedup_manager.register_trades([trade_record], self.test_user_id)
        
        # Try to add the same trade again
        duplicates = self.dedup_manager.find_potential_duplicates(trade_data, self.test_user_id)
        
        assert len(duplicates) == 1, "Should find one exact duplicate"
        assert duplicates[0].match_type == DuplicateMatchType.EXACT
        assert duplicates[0].confidence_score == 1.0
    
    def test_fuzzy_duplicate_detection(self):
        """Test detection of fuzzy duplicates."""
        base_time = datetime.now()
        
        # Register original trade
        original_trade = self.create_test_trade(
            entry_time=base_time,
            exit_time=base_time + timedelta(hours=1),
            entry_price=150.00,
            exit_price=155.00
        )
        
        trade_record = TradeRecord.from_dict(original_trade)
        self.dedup_manager.register_trades([trade_record], self.test_user_id)
        
        # Similar trade with slight differences
        similar_trade = self.create_test_trade(
            entry_time=base_time + timedelta(minutes=3),  # Within tolerance
            exit_time=base_time + timedelta(hours=1, minutes=3),
            entry_price=150.01,  # Slight price difference
            exit_price=155.01
        )
        
        duplicates = self.dedup_manager.find_potential_duplicates(similar_trade, self.test_user_id)
        
        assert len(duplicates) >= 1, "Should find fuzzy duplicate"
        assert duplicates[0].confidence_score >= 0.85
    
    def test_no_false_positives(self):
        """Test that different trades are not flagged as duplicates."""
        # Register original trade
        original_trade = self.create_test_trade(symbol="AAPL", entry_price=150.0)
        trade_record = TradeRecord.from_dict(original_trade)
        self.dedup_manager.register_trades([trade_record], self.test_user_id)
        
        # Completely different trade
        different_trade = self.create_test_trade(
            symbol="TSLA", 
            entry_price=200.0,
            exit_price=190.0,
            entry_time=datetime.now() + timedelta(days=1)
        )
        
        duplicates = self.dedup_manager.find_potential_duplicates(different_trade, self.test_user_id)
        
        assert len(duplicates) == 0, "Different trades should not be flagged as duplicates"
    
    def test_batch_deduplication(self):
        """Test deduplication of multiple trades at once."""
        trades_data = [
            self.create_test_trade(symbol="AAPL", entry_price=150.0),
            self.create_test_trade(symbol="AAPL", entry_price=150.0),  # Duplicate
            self.create_test_trade(symbol="TSLA", entry_price=200.0),
            self.create_test_trade(symbol="MSFT", entry_price=300.0),
        ]
        
        results = self.dedup_manager.deduplicate_trades(trades_data, self.test_user_id)
        
        assert results['original_count'] == 4
        assert results['duplicates_removed'] == 1
        assert len(results['unique_trades']) == 3
    
    def test_cross_source_deduplication(self):
        """Test deduplication across different data sources."""
        # Register trade from CSV
        csv_trade = self.create_test_trade(data_source="csv")
        trade_record = TradeRecord.from_dict(csv_trade)
        self.dedup_manager.register_trades([trade_record], self.test_user_id)
        
        # Try to add same trade from API
        api_trade = self.create_test_trade(data_source="api")
        
        duplicates = self.dedup_manager.find_potential_duplicates(api_trade, self.test_user_id)
        
        assert len(duplicates) == 1, "Should detect duplicate across sources"
        assert duplicates[0].match_type == DuplicateMatchType.EXACT
    
    def test_user_isolation(self):
        """Test that deduplication is isolated per user."""
        user1_id = 1
        user2_id = 2
        
        # Register trade for user 1
        trade_data = self.create_test_trade()
        trade_record = TradeRecord.from_dict(trade_data)
        self.dedup_manager.register_trades([trade_record], user1_id)
        
        # Same trade for user 2 should not be flagged as duplicate
        duplicates = self.dedup_manager.find_potential_duplicates(trade_data, user2_id)
        
        assert len(duplicates) == 0, "Trades should be isolated per user"
    
    def test_performance_with_large_dataset(self):
        """Test deduplication performance with larger dataset."""
        import time
        
        # Create 1000 unique trades
        trades_data = []
        for i in range(1000):
            trade = self.create_test_trade(
                symbol=f"STOCK{i % 100}",  # 100 different symbols
                entry_price=100 + (i % 50),  # Price variation
                entry_time=datetime.now() - timedelta(days=i % 30)  # Time variation
            )
            trades_data.append(trade)
        
        # Add some duplicates
        trades_data.extend(trades_data[:50])  # 50 duplicates
        
        start_time = time.time()
        results = self.dedup_manager.deduplicate_trades(trades_data, self.test_user_id)
        processing_time = time.time() - start_time
        
        assert results['original_count'] == 1050
        assert results['duplicates_removed'] == 50
        assert processing_time < 10.0, f"Processing took too long: {processing_time:.2f}s"
    
    def test_duplicate_resolution_logging(self):
        """Test that duplicate resolutions are properly logged."""
        trade_data = self.create_test_trade()
        
        # Register original trade
        trade_record = TradeRecord.from_dict(trade_data)
        self.dedup_manager.register_trades([trade_record], self.test_user_id)
        
        # Process duplicate with auto-resolution
        results = self.dedup_manager.deduplicate_trades([trade_data], self.test_user_id, auto_resolve=True)
        
        assert results['duplicates_removed'] == 1
        
        # Check that resolution was logged
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM duplicate_resolutions 
            WHERE user_id = ? AND action_taken = 'auto_removed'
        ''', (self.test_user_id,))
        
        log_count = cursor.fetchone()[0]
        conn.close()
        
        assert log_count == 1, "Duplicate resolution should be logged"
    
    def test_deduplication_stats(self):
        """Test deduplication statistics generation."""
        # Register some trades and process duplicates
        for i in range(5):
            trade = self.create_test_trade(symbol=f"STOCK{i}")
            trade_record = TradeRecord.from_dict(trade)
            self.dedup_manager.register_trades([trade_record], self.test_user_id)
        
        # Process some duplicates
        duplicate_trade = self.create_test_trade(symbol="STOCK0")
        self.dedup_manager.deduplicate_trades([duplicate_trade], self.test_user_id, auto_resolve=True)
        
        stats = self.dedup_manager.get_deduplication_stats(self.test_user_id)
        
        assert stats['total_registered_trades'] == 5
        assert len(stats['resolution_stats']) > 0
    
    def test_cleanup_old_fingerprints(self):
        """Test cleanup of old trade fingerprints."""
        # Register some trades
        for i in range(10):
            trade = self.create_test_trade(symbol=f"OLD{i}")
            trade_record = TradeRecord.from_dict(trade)
            self.dedup_manager.register_trades([trade_record], self.test_user_id)
        
        # Clean up with 0 days to keep (should clean all)
        cleaned_count = self.dedup_manager.cleanup_old_fingerprints(days_to_keep=0)
        
        assert cleaned_count == 10, "Should clean up all old fingerprints"
        
        # Verify cleanup
        stats = self.dedup_manager.get_deduplication_stats(self.test_user_id)
        assert stats['total_registered_trades'] == 0
