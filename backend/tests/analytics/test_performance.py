import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pandas as pd

from backend.analytics.performance import PerformanceAnalyzer
from backend.models.trade import Trade

class TestPerformanceAnalyzer:

    @pytest.fixture
    def mock_trades(self):
        """Create mock trade data for testing"""
        trades = []
        base_date = datetime(2024, 1, 1)

        for i in range(10):
            trade = Mock(spec=Trade)
            trade.symbol = "AAPL" if i % 2 == 0 else "MSFT"
            trade.entry_price = 100.0 + i
            trade.exit_price = 105.0 + i if i % 3 != 0 else 95.0 + i  # Some losses
            trade.quantity = 100
            trade.entry_time = base_date + timedelta(days=i)
            trade.exit_time = base_date + timedelta(days=i, hours=2)
            trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity
            trade.side = "long"
            trades.append(trade)

        return trades

    def test_calculate_basic_metrics(self, mock_trades):
        """Test basic performance metrics calculation"""
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.calculate_basic_metrics(mock_trades)

        assert "total_trades" in metrics
        assert "win_rate" in metrics
        assert "total_pnl" in metrics
        assert "avg_win" in metrics
        assert "avg_loss" in metrics
        assert metrics["total_trades"] == 10
        assert 0 <= metrics["win_rate"] <= 1

    def test_calculate_sharpe_ratio(self, mock_trades):
        """Test Sharpe ratio calculation"""
        analyzer = PerformanceAnalyzer()
        sharpe = analyzer.calculate_sharpe_ratio(mock_trades)

        assert isinstance(sharpe, (int, float))
        assert not pd.isna(sharpe)

    def test_calculate_max_drawdown(self, mock_trades):
        """Test maximum drawdown calculation"""
        analyzer = PerformanceAnalyzer()
        max_dd = analyzer.calculate_max_drawdown(mock_trades)

        assert isinstance(max_dd, (int, float))
        assert max_dd <= 0  # Drawdown should be negative or zero

    def test_empty_trades_handling(self):
        """Test handling of empty trade list"""
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.calculate_basic_metrics([])

        assert metrics["total_trades"] == 0
        assert metrics["total_pnl"] == 0
        assert metrics["win_rate"] == 0