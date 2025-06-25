
"""
Tests for performance analytics module
"""

import pytest
from datetime import datetime, timedelta
from backend.analytics.performance import (
    calculate_win_rate,
    calculate_profit_factor,
    calculate_expectancy,
    calculate_risk_reward_metrics
)
from backend.models.trade import Trade


class MockTrade:
    """Mock Trade object for testing"""
    def __init__(self, pnl, symbol='TEST', direction='long', entry_time=None, exit_time=None):
        self.id = f"trade_{id(self)}"
        self.pnl = pnl
        self.symbol = symbol
        self.direction = direction
        self.entry_time = entry_time or datetime.now()
        self.exit_time = exit_time or datetime.now()
        self.strategy_tag = 'test_strategy'
        self.user_id = 'test_user'
        self.quantity = 100
        self.entry_price = 100.0
        self.exit_price = 101.0 if pnl > 0 else 99.0


class TestPerformanceAnalytics:
    """Test performance analytics functions"""

    def test_calculate_win_rate_empty_trades(self):
        """Test win rate calculation with empty trades list"""
        result = calculate_win_rate([])
        assert result == 0.0

    def test_calculate_win_rate_all_winners(self):
        """Test win rate calculation with all winning trades"""
        trades = [
            MockTrade(100),
            MockTrade(200),
            MockTrade(50)
        ]
        result = calculate_win_rate(trades)
        assert result == 100.0

    def test_calculate_win_rate_all_losers(self):
        """Test win rate calculation with all losing trades"""
        trades = [
            MockTrade(-100),
            MockTrade(-200),
            MockTrade(-50)
        ]
        result = calculate_win_rate(trades)
        assert result == 0.0

    def test_calculate_win_rate_mixed(self):
        """Test win rate calculation with mixed trades"""
        trades = [
            MockTrade(100),  # win
            MockTrade(-50),  # loss
            MockTrade(200),  # win
            MockTrade(-25)   # loss
        ]
        result = calculate_win_rate(trades)
        assert result == 50.0

    def test_calculate_profit_factor_empty_trades(self):
        """Test profit factor calculation with empty trades"""
        result = calculate_profit_factor([])
        assert result == 0.0

    def test_calculate_profit_factor_no_losses(self):
        """Test profit factor calculation with no losing trades"""
        trades = [
            MockTrade(100),
            MockTrade(200)
        ]
        result = calculate_profit_factor(trades)
        assert result == float('inf')

    def test_calculate_profit_factor_normal(self):
        """Test profit factor calculation with normal data"""
        trades = [
            MockTrade(300),  # +300 gross profit
            MockTrade(-100)  # -100 gross loss
        ]
        result = calculate_profit_factor(trades)
        assert result == 3.0

    def test_calculate_expectancy(self):
        """Test expectancy calculation"""
        trades = [
            MockTrade(100),
            MockTrade(-50),
            MockTrade(200),
            MockTrade(-25)
        ]
        result = calculate_expectancy(trades)
        expected = (100 - 50 + 200 - 25) / 4
        assert result == expected

    def test_comprehensive_metrics(self):
        """Test comprehensive risk/reward metrics calculation"""
        trades = [
            MockTrade(100, entry_time=datetime(2024, 1, 1)),
            MockTrade(-50, entry_time=datetime(2024, 1, 2)),
            MockTrade(200, entry_time=datetime(2024, 1, 3)),
            MockTrade(-25, entry_time=datetime(2024, 1, 4))
        ]
        
        result = calculate_risk_reward_metrics(trades)
        
        assert result['total_trades'] == 4
        assert result['winning_trades'] == 2
        assert result['losing_trades'] == 2
        assert result['win_rate'] == 50.0
        assert result['total_pnl'] == 225
        assert result['best_trade'] == 200
        assert result['worst_trade'] == -50
        assert result['profit_factor'] == 4.0  # 300/75
        assert result['expectancy'] == 56.25  # 225/4

    def test_performance_with_none_pnl(self):
        """Test performance calculation with None PnL values"""
        class MockTradeWithNone:
            def __init__(self, pnl):
                self.id = f"trade_{id(self)}"
                self.pnl = pnl
                self.symbol = 'TEST'
                self.direction = 'long'
                self.entry_time = datetime.now()
                self.exit_time = datetime.now()
                self.strategy_tag = 'test'
                self.user_id = 'test_user'

        trades = [
            MockTradeWithNone(100),
            MockTradeWithNone(None),
            MockTradeWithNone(-50)
        ]
        
        result = calculate_win_rate(trades)
        # Should only count trades with valid PnL
        assert result == 50.0  # 1 win out of 2 valid trades
