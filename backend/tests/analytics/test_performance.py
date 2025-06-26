
"""
Test performance analytics functionality
"""
import pytest
from datetime import datetime, timedelta
from backend.analytics.performance import PerformanceAnalyzer
from backend.models.trade import Trade


class TestPerformanceAnalyzer:
    """Test performance analytics calculations"""
    
    @pytest.fixture
    def sample_trades(self, db_session, test_user):
        """Create sample trades for testing"""
        trades = [
            # Winning trades
            Trade(
                user_id=test_user.id,
                symbol="AAPL",
                direction="long",
                quantity=100,
                entry_price=150.0,
                exit_price=155.0,
                entry_time=datetime.now() - timedelta(days=5),
                exit_time=datetime.now() - timedelta(days=5, hours=-2),
                pnl=500.0
            ),
            Trade(
                user_id=test_user.id,
                symbol="TSLA",
                direction="long",
                quantity=50,
                entry_price=800.0,
                exit_price=820.0,
                entry_time=datetime.now() - timedelta(days=4),
                exit_time=datetime.now() - timedelta(days=4, hours=-3),
                pnl=1000.0
            ),
            # Losing trades
            Trade(
                user_id=test_user.id,
                symbol="MSFT",
                direction="short",
                quantity=75,
                entry_price=300.0,
                exit_price=305.0,
                entry_time=datetime.now() - timedelta(days=3),
                exit_time=datetime.now() - timedelta(days=3, hours=-1),
                pnl=-375.0
            ),
            Trade(
                user_id=test_user.id,
                symbol="GOOGL",
                direction="long",
                quantity=25,
                entry_price=2500.0,
                exit_price=2450.0,
                entry_time=datetime.now() - timedelta(days=2),
                exit_time=datetime.now() - timedelta(days=2, hours=-4),
                pnl=-1250.0
            )
        ]
        
        for trade in trades:
            db_session.add(trade)
        db_session.commit()
        return trades

    def test_win_rate_calculation(self, sample_trades, test_user):
        """Test win rate calculation"""
        analyzer = PerformanceAnalyzer(test_user.id)
        win_rate = analyzer.calculate_win_rate()
        
        # 2 winning trades out of 4 total = 50%
        assert win_rate == 0.5

    def test_profit_factor_calculation(self, sample_trades, test_user):
        """Test profit factor calculation"""
        analyzer = PerformanceAnalyzer(test_user.id)
        profit_factor = analyzer.calculate_profit_factor()
        
        # Total wins: 1500, Total losses: 1625
        # Profit factor = 1500 / 1625 ≈ 0.923
        assert abs(profit_factor - 0.923) < 0.01

    def test_average_win_loss(self, sample_trades, test_user):
        """Test average win and loss calculations"""
        analyzer = PerformanceAnalyzer(test_user.id)
        avg_win = analyzer.calculate_average_win()
        avg_loss = analyzer.calculate_average_loss()
        
        # Average win: (500 + 1000) / 2 = 750
        assert avg_win == 750.0
        
        # Average loss: (375 + 1250) / 2 = 812.5
        assert avg_loss == 812.5

    def test_total_pnl(self, sample_trades, test_user):
        """Test total P&L calculation"""
        analyzer = PerformanceAnalyzer(test_user.id)
        total_pnl = analyzer.calculate_total_pnl()
        
        # Total: 500 + 1000 - 375 - 1250 = -125
        assert total_pnl == -125.0

    def test_sharpe_ratio(self, sample_trades, test_user):
        """Test Sharpe ratio calculation"""
        analyzer = PerformanceAnalyzer(test_user.id)
        sharpe = analyzer.calculate_sharpe_ratio()
        
        # Should return a numeric value
        assert isinstance(sharpe, (int, float))

    def test_maximum_drawdown(self, sample_trades, test_user):
        """Test maximum drawdown calculation"""
        analyzer = PerformanceAnalyzer(test_user.id)
        max_dd = analyzer.calculate_max_drawdown()
        
        # Should return a numeric value
        assert isinstance(max_dd, (int, float))
        assert max_dd <= 0  # Drawdown should be negative or zero

    def test_performance_by_symbol(self, sample_trades, test_user):
        """Test performance breakdown by symbol"""
        analyzer = PerformanceAnalyzer(test_user.id)
        symbol_performance = analyzer.get_performance_by_symbol()
        
        assert "AAPL" in symbol_performance
        assert "TSLA" in symbol_performance
        assert "MSFT" in symbol_performance
        assert "GOOGL" in symbol_performance
        
        # AAPL should show positive P&L
        assert symbol_performance["AAPL"]["total_pnl"] == 500.0
        assert symbol_performance["AAPL"]["win_rate"] == 1.0

    def test_performance_over_time(self, sample_trades, test_user):
        """Test performance analysis over time"""
        analyzer = PerformanceAnalyzer(test_user.id)
        time_series = analyzer.get_performance_over_time()
        
        assert len(time_series) > 0
        assert "date" in time_series[0]
        assert "cumulative_pnl" in time_series[0]

    def test_risk_metrics(self, sample_trades, test_user):
        """Test risk metrics calculation"""
        analyzer = PerformanceAnalyzer(test_user.id)
        risk_metrics = analyzer.calculate_risk_metrics()
        
        required_metrics = [
            "max_drawdown",
            "volatility",
            "var_95",
            "calmar_ratio"
        ]
        
        for metric in required_metrics:
            assert metric in risk_metrics
            assert isinstance(risk_metrics[metric], (int, float))

    def test_empty_trades_handling(self, test_user):
        """Test analytics with no trades"""
        analyzer = PerformanceAnalyzer(test_user.id)
        
        assert analyzer.calculate_win_rate() == 0.0
        assert analyzer.calculate_total_pnl() == 0.0
        assert analyzer.calculate_profit_factor() == 0.0

    def test_date_filtering(self, sample_trades, test_user):
        """Test analytics with date filtering"""
        analyzer = PerformanceAnalyzer(test_user.id)
        
        # Filter to last 3 days (should exclude oldest trade)
        start_date = datetime.now() - timedelta(days=3)
        filtered_pnl = analyzer.calculate_total_pnl(start_date=start_date)
        
        # Should exclude the first AAPL trade (500 profit)
        assert filtered_pnl != -125.0  # Total without filtering
