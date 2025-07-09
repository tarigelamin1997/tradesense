"""
Tests for streaks analytics module
"""

import pytest
from datetime import datetime, timedelta
from backend.analytics.streaks import (
    calculate_win_loss_streaks,
    calculate_max_consecutive_wins,
    calculate_max_consecutive_losses,
)


class MockTrade:
    """Mock Trade object for testing"""
    def __init__(self, pnl, day_offset=0):
        self.id = f"trade_{id(self)}"
        self.pnl = pnl
        self.symbol = 'TEST'
        self.direction = 'long'
        self.entry_time = datetime(2024, 1, 1) + timedelta(days=day_offset)
        self.exit_time = self.entry_time + timedelta(hours=1)
        self.strategy_tag = 'test_strategy'
        self.user_id = 'test_user'

    def get(self, key, default=None):
        return getattr(self, key, default)


class TestStreakAnalytics:
    """Test streak analytics functions"""

    def test_calculate_streaks_empty(self):
        """Test streak calculation with empty trades"""
        result = calculate_win_loss_streaks([])
        
        assert result['max_win_streak'] == 0
        assert result['max_loss_streak'] == 0
        assert result['current_streak'] == 0
        assert result['current_streak_type'] == 'none'

    def test_calculate_streaks_single_win(self):
        """Test streak calculation with single winning trade"""
        trades = [MockTrade(100)]
        result = calculate_win_loss_streaks(trades)
        
        assert result['max_win_streak'] == 1
        assert result['max_loss_streak'] == 0
        assert result['current_streak'] == 1
        assert result['current_streak_type'] == 'win'

    def test_calculate_streaks_alternating(self):
        """Test streak calculation with alternating wins/losses"""
        trades = [
            MockTrade(100, 0),   # win
            MockTrade(-50, 1),   # loss
            MockTrade(200, 2),   # win
            MockTrade(-25, 3)    # loss
        ]
        
        result = calculate_win_loss_streaks(trades)
        
        assert result['max_win_streak'] == 1
        assert result['max_loss_streak'] == 1
        assert result['current_streak'] == 1
        assert result['current_streak_type'] == 'loss'
        assert result['total_streaks'] == 4

    def test_calculate_streaks_consecutive_wins(self):
        """Test streak calculation with consecutive wins"""
        trades = [
            MockTrade(100, 0),   # win
            MockTrade(150, 1),   # win
            MockTrade(200, 2),   # win
            MockTrade(-50, 3),   # loss
            MockTrade(75, 4)     # win
        ]
        
        result = calculate_win_loss_streaks(trades)
        
        assert result['max_win_streak'] == 3
        assert result['max_loss_streak'] == 1
        assert result['current_streak'] == 1
        assert result['current_streak_type'] == 'win'

    def test_calculate_streaks_consecutive_losses(self):
        """Test streak calculation with consecutive losses"""
        trades = [
            MockTrade(100, 0),   # win
            MockTrade(-50, 1),   # loss
            MockTrade(-75, 2),   # loss
            MockTrade(-25, 3),   # loss
            MockTrade(200, 4)    # win
        ]
        
        result = calculate_win_loss_streaks(trades)
        
        assert result['max_win_streak'] == 1
        assert result['max_loss_streak'] == 3
        assert result['current_streak'] == 1
        assert result['current_streak_type'] == 'win'

    def test_find_max_win_streak_details(self):
        """Test finding max win streak with details"""
        trades = [
            MockTrade(100, 0),   # win
            MockTrade(150, 1),   # win (start of max streak)
            MockTrade(200, 2),   # win
            MockTrade(75, 3),    # win (end of max streak)
            MockTrade(-50, 4),   # loss
            MockTrade(125, 5)    # win
        ]
        
        result = calculate_max_consecutive_wins(trades)
        
        assert result['length'] == 4
        assert result['pnl'] == 525  # 150 + 200 + 75 + 100
        assert len(result['trades']) == 4

    def test_find_max_loss_streak_details(self):
        """Test finding max loss streak with details"""
        trades = [
            MockTrade(100, 0),   # win
            MockTrade(-50, 1),   # loss (start of max streak)
            MockTrade(-75, 2),   # loss
            MockTrade(-25, 3),   # loss (end of max streak)
            MockTrade(200, 4),   # win
            MockTrade(-10, 5)    # loss
        ]
        
        result = calculate_max_consecutive_losses(trades)
        
        assert result['length'] == 3
        assert result['pnl'] == -150  # -50 + -75 + -25
        assert len(result['trades']) == 3

    def test_streaks_with_none_pnl(self):
        """Test streak calculation with None PnL values"""
        class MockTradeWithNone:
            def __init__(self, pnl, day_offset=0):
                self.id = f"trade_{id(self)}"
                self.pnl = pnl
                self.symbol = 'TEST'
                self.entry_time = datetime(2024, 1, 1) + timedelta(days=day_offset)
                self.exit_time = self.entry_time + timedelta(hours=1)

            def get(self, key, default=None):
                return getattr(self, key, default)

        trades = [
            MockTradeWithNone(100, 0),   # win
            MockTradeWithNone(None, 1),  # invalid - should be skipped
            MockTradeWithNone(-50, 2)    # loss
        ]
        
        result = calculate_win_loss_streaks(trades)
        
        # Should skip the None trade
        assert result['max_win_streak'] == 1
        assert result['max_loss_streak'] == 1
        assert result['total_streaks'] == 2
