"""
Tests for filters analytics module
"""

import pytest
from datetime import datetime, timedelta
from analytics.filters import (
    filter_trades_by_symbol,
    apply_trade_filters,
    filter_by_date_range,
    filter_by_strategy
)


class MockTrade:
    """Mock Trade object for testing"""
    def __init__(self, symbol='TEST', strategy=None, entry_time=None, pnl=100):
        self.id = f"trade_{id(self)}"
        self.symbol = symbol
        self.strategy_tag = strategy
        self.entry_time = entry_time or datetime(2024, 1, 1)
        self.pnl = pnl
        self.direction = 'long'
        self.user_id = 'test_user'

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __getitem__(self, key):
        return getattr(self, key)


class TestFiltersAnalytics:
    """Test filter analytics functions"""

    def test_filter_by_date_range(self):
        """Test filtering trades by date range"""
        trades = [
            MockTrade('AAPL', entry_time=datetime(2024, 1, 1)),
            MockTrade('TSLA', entry_time=datetime(2024, 1, 15)),
            MockTrade('MSFT', entry_time=datetime(2024, 2, 1))
        ]
        
        start_date = datetime(2024, 1, 10)
        end_date = datetime(2024, 1, 20)
        
        result = filter_by_date_range(trades, start_date, end_date)
        
        assert len(result) == 1
        assert result[0].symbol == 'TSLA'

    def test_filter_by_symbol(self):
        """Test filtering trades by symbol"""
        trades = [
            MockTrade('AAPL'),
            MockTrade('TSLA'),
            MockTrade('MSFT'),
            MockTrade('AAPL')
        ]
        
        result = filter_trades_by_symbol(trades, ['AAPL'])
        
        assert len(result) == 2
        assert all(t.symbol == 'AAPL' for t in result)

    def test_filter_by_strategy(self):
        """Test filtering trades by strategy"""
        trades = [
            MockTrade('AAPL', strategy='momentum'),
            MockTrade('TSLA', strategy='reversal'),
            MockTrade('MSFT', strategy='momentum'),
            MockTrade('NVDA', strategy='breakout')
        ]
        
        result = filter_by_strategy(trades, ['momentum'])
        
        assert len(result) == 2
        assert all(t.strategy_tag == 'momentum' for t in result)

    def test_apply_multiple_filters(self):
        """Test applying multiple filters together"""
        trades = [
            MockTrade('AAPL', strategy='momentum', entry_time=datetime(2024, 1, 1)),
            MockTrade('AAPL', strategy='reversal', entry_time=datetime(2024, 1, 15)),
            MockTrade('TSLA', strategy='momentum', entry_time=datetime(2024, 1, 10)),
            MockTrade('AAPL', strategy='momentum', entry_time=datetime(2024, 2, 1))
        ]
        
        filters = {
            'symbols': ['AAPL'],
            'strategies': ['momentum'],
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 1, 31)
        }
        
        result = apply_trade_filters(trades, filters)
        
        assert len(result) == 1
        assert result[0].symbol == 'AAPL'
        assert result[0].strategy_tag == 'momentum'

    def test_filter_empty_trades(self):
        """Test filtering with empty trades list"""
        result = filter_trades_by_symbol([], ['AAPL'])
        assert result == []

    def test_filter_case_insensitive_symbols(self):
        """Test that symbol filtering is case insensitive"""
        trades = [
            MockTrade('aapl'),
            MockTrade('TSLA'),
            MockTrade('Msft')
        ]
        
        result = filter_trades_by_symbol(trades, ['AAPL', 'msft'])
        
        assert len(result) == 2
        assert {t.symbol.upper() for t in result} == {'AAPL', 'MSFT'}

    def test_filter_no_matching_criteria(self):
        """Test filtering with no matching criteria"""
        trades = [
            MockTrade('AAPL'),
            MockTrade('TSLA')
        ]
        
        result = filter_trades_by_symbol(trades, ['NVDA'])
        assert len(result) == 0
