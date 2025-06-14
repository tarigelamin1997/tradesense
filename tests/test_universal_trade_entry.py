
"""
Comprehensive unit tests for universal trade entry system and analytics.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trade_entry_manager import TradeEntryManager
from models.trade_model import TradeDirection, TradeType
from analytics import (
    compute_basic_stats,
    calculate_kpis,
    performance_over_time,
    median_results,
    profit_factor_by_symbol,
    trade_duration_stats,
    max_streaks,
    rolling_metrics
)


class TestUniversalTradeEntry:
    """Test universal trade entry system."""
    
    def setup_method(self):
        """Setup for each test."""
        self.manager = TradeEntryManager()
    
    def test_manual_trade_entry(self):
        """Test manual trade entry."""
        trade_data = {
            "symbol": "AAPL",
            "entry_price": 150.0,
            "exit_price": 155.0,
            "trade_size": 100,
            "direction": "long",
            "pnl": 500.0,
            "broker": "Manual",
            "notes": "Test trade"
        }
        
        result = self.manager.add_manual_trade(trade_data)
        
        assert result["status"] == "success"
        assert "trade_id" in result
        
        df = self.manager.get_all_trades_dataframe()
        assert len(df) == 1
        assert df.iloc[0]["symbol"] == "AAPL"
        assert df.iloc[0]["pnl"] == 500.0
        assert df.iloc[0]["data_source"] == "manual"
    
    def test_file_trade_import(self):
        """Test file trade import."""
        # Create sample DataFrame
        data = [
            {
                "symbol": "TSLA",
                "entry_time": "2023-01-01 09:00:00",
                "exit_time": "2023-01-01 15:00:00",
                "entry_price": 200.0,
                "exit_price": 210.0,
                "qty": 50,
                "direction": "long",
                "pnl": 500.0,
                "trade_type": "stocks",
                "broker": "TestBroker"
            },
            {
                "symbol": "NVDA",
                "entry_time": "2023-01-02 09:00:00",
                "exit_time": "2023-01-02 15:00:00",
                "entry_price": 300.0,
                "exit_price": 290.0,
                "qty": 25,
                "direction": "long",
                "pnl": -250.0,
                "trade_type": "stocks",
                "broker": "TestBroker"
            }
        ]
        df = pd.DataFrame(data)
        
        result = self.manager.add_file_trades(df, "test_file")
        
        assert result["status"] == "success"
        assert result["trades_added"] == 2
        
        all_trades = self.manager.get_all_trades_dataframe()
        assert len(all_trades) == 2
        assert all(all_trades["data_source"] == "test_file")
    
    def test_api_trade_import(self):
        """Test API trade import."""
        api_trades = [
            {
                "symbol": "SPY",
                "entry_time": "2023-01-03 09:00:00",
                "exit_time": "2023-01-03 15:00:00",
                "entry_price": 400.0,
                "exit_price": 405.0,
                "qty": 100,
                "direction": "long",
                "pnl": 500.0,
                "trade_type": "stocks",
                "broker": "API_Broker"
            }
        ]
        
        result = self.manager.add_api_trades(api_trades, "test_connector")
        
        assert result["status"] == "success"
        assert result["trades_added"] == 1
        
        all_trades = self.manager.get_all_trades_dataframe()
        assert len(all_trades) == 1
        assert all_trades.iloc[0]["data_source"] == "api_test_connector"
    
    def test_unified_analytics(self):
        """Test unified analytics across all sources."""
        # Add manual trade
        manual_trade = {
            "symbol": "AAPL",
            "entry_price": 150.0,
            "exit_price": 155.0,
            "trade_size": 100,
            "direction": "long",
            "pnl": 500.0
        }
        self.manager.add_manual_trade(manual_trade)
        
        # Add file trade
        file_data = pd.DataFrame([{
            "symbol": "TSLA",
            "entry_time": "2023-01-01 09:00:00",
            "exit_time": "2023-01-01 15:00:00",
            "entry_price": 200.0,
            "exit_price": 190.0,
            "qty": 50,
            "direction": "long",
            "pnl": -500.0,
            "trade_type": "stocks",
            "broker": "TestBroker"
        }])
        self.manager.add_file_trades(file_data)
        
        # Get unified analytics
        analytics = self.manager.get_unified_analytics()
        
        assert analytics["trade_summary"]["total_trades"] == 2
        assert len(analytics["trade_summary"]["data_sources"]) == 2
        assert "manual" in analytics["trade_summary"]["data_sources"]
        assert "file" in analytics["trade_summary"]["data_sources"]
        
        # Check that analytics are calculated
        assert "basic_stats" in analytics
        assert "kpis" in analytics
        assert analytics["basic_stats"]["win_rate"] == 50.0  # 1 win, 1 loss


class TestAnalyticsFunctions:
    """Comprehensive tests for all analytics functions."""
    
    def setup_method(self):
        """Setup test data."""
        self.sample_data = [
            {
                "symbol": "AAPL",
                "entry_time": "2023-01-01 09:00:00",
                "exit_time": "2023-01-01 15:00:00",
                "entry_price": 150.0,
                "exit_price": 155.0,
                "qty": 100,
                "direction": "long",
                "pnl": 500.0,
                "trade_type": "stocks",
                "broker": "TestBroker"
            },
            {
                "symbol": "TSLA",
                "entry_time": "2023-01-02 09:00:00",
                "exit_time": "2023-01-02 15:00:00",
                "entry_price": 200.0,
                "exit_price": 190.0,
                "qty": 50,
                "direction": "long",
                "pnl": -500.0,
                "trade_type": "stocks",
                "broker": "TestBroker"
            },
            {
                "symbol": "AAPL",
                "entry_time": "2023-01-03 09:00:00",
                "exit_time": "2023-01-03 15:00:00",
                "entry_price": 160.0,
                "exit_price": 170.0,
                "qty": 75,
                "direction": "long",
                "pnl": 750.0,
                "trade_type": "stocks",
                "broker": "TestBroker"
            }
        ]
        self.df = pd.DataFrame(self.sample_data)
    
    def test_compute_basic_stats(self):
        """Test basic statistics calculation."""
        stats = compute_basic_stats(self.df)
        
        assert stats["total_trades"] == 3
        assert stats["win_rate"] == pytest.approx(66.67, rel=1e-2)  # 2 wins, 1 loss
        assert stats["average_win"] == 625.0  # (500 + 750) / 2
        assert stats["average_loss"] == -500.0
        assert stats["profit_factor"] == 2.5  # 1250 / 500
        assert "expectancy" in stats
        assert "max_drawdown" in stats
    
    def test_calculate_kpis(self):
        """Test KPI calculation."""
        kpis = calculate_kpis(self.df)
        
        assert kpis["total_trades"] == 3
        assert kpis["gross_pnl"] == 750.0  # 500 - 500 + 750
        assert kpis["win_rate_percent"] == pytest.approx(66.67, rel=1e-2)
        assert kpis["max_single_trade_win"] == 750.0
        assert kpis["max_single_trade_loss"] == -500.0
        assert "total_commission" in kpis
        assert "net_pnl_after_commission" in kpis
    
    def test_performance_over_time(self):
        """Test performance over time calculation."""
        performance = performance_over_time(self.df, freq='D')
        
        assert not performance.empty
        assert "pnl" in performance.columns
        assert "win_rate" in performance.columns
        assert len(performance) <= 3  # Maximum 3 days of data
    
    def test_median_results(self):
        """Test median results calculation."""
        medians = median_results(self.df)
        
        assert "median_pnl" in medians
        assert "median_win" in medians
        assert "median_loss" in medians
        assert medians["median_pnl"] == 500.0  # Middle value
        assert medians["median_win"] == 625.0  # (500 + 750) / 2
        assert medians["median_loss"] == -500.0  # Only one loss
    
    def test_profit_factor_by_symbol(self):
        """Test profit factor by symbol calculation."""
        pf_by_symbol = profit_factor_by_symbol(self.df)
        
        assert not pf_by_symbol.empty
        assert "symbol" in pf_by_symbol.columns
        assert "profit_factor" in pf_by_symbol.columns
        
        # AAPL should have profit factor > 0 (2 wins, no losses)
        aapl_pf = pf_by_symbol[pf_by_symbol["symbol"] == "AAPL"]["profit_factor"].iloc[0]
        assert aapl_pf > 0
        
        # TSLA should have profit factor = 0 (0 wins, 1 loss)
        tsla_pf = pf_by_symbol[pf_by_symbol["symbol"] == "TSLA"]["profit_factor"].iloc[0]
        assert tsla_pf == 0
    
    def test_trade_duration_stats(self):
        """Test trade duration statistics."""
        duration_stats = trade_duration_stats(self.df)
        
        assert "average_minutes" in duration_stats
        assert "min_minutes" in duration_stats
        assert "max_minutes" in duration_stats
        assert "median_minutes" in duration_stats
        
        # All trades are 6 hours = 360 minutes
        assert duration_stats["average_minutes"] == 360.0
        assert duration_stats["min_minutes"] == 360.0
        assert duration_stats["max_minutes"] == 360.0
        assert duration_stats["median_minutes"] == 360.0
    
    def test_max_streaks(self):
        """Test maximum streak calculation."""
        # Create data with known streaks
        streak_data = [
            {"symbol": "TEST", "exit_time": "2023-01-01", "pnl": 100},  # Win
            {"symbol": "TEST", "exit_time": "2023-01-02", "pnl": 200},  # Win
            {"symbol": "TEST", "exit_time": "2023-01-03", "pnl": -100}, # Loss
            {"symbol": "TEST", "exit_time": "2023-01-04", "pnl": -200}, # Loss
            {"symbol": "TEST", "exit_time": "2023-01-05", "pnl": -300}, # Loss
            {"symbol": "TEST", "exit_time": "2023-01-06", "pnl": 400},  # Win
        ]
        streak_df = pd.DataFrame(streak_data)
        
        streaks = max_streaks(streak_df)
        
        assert "max_win_streak" in streaks
        assert "max_loss_streak" in streaks
        assert streaks["max_win_streak"] == 2
        assert streaks["max_loss_streak"] == 3
    
    def test_rolling_metrics(self):
        """Test rolling metrics calculation."""
        # Need more data for rolling metrics
        extended_data = []
        for i in range(15):
            pnl = 100 if i % 2 == 0 else -50  # Alternating wins/losses
            extended_data.append({
                "symbol": "TEST",
                "exit_time": f"2023-01-{i+1:02d}",
                "pnl": pnl
            })
        
        extended_df = pd.DataFrame(extended_data)
        rolling = rolling_metrics(extended_df, window=10)
        
        assert not rolling.empty
        assert "win_rate" in rolling.columns
        assert "profit_factor" in rolling.columns
        assert len(rolling) >= 1  # At least one rolling period
    
    def test_empty_dataframe_handling(self):
        """Test that analytics functions handle empty DataFrames gracefully."""
        empty_df = pd.DataFrame()
        
        stats = compute_basic_stats(empty_df)
        assert stats == {}
        
        kpis = calculate_kpis(empty_df)
        assert kpis["total_trades"] == 0
        
        performance = performance_over_time(empty_df)
        assert performance.empty
        
        medians = median_results(empty_df)
        assert all(v == 0 for v in medians.values())
    
    def test_invalid_data_handling(self):
        """Test handling of invalid/corrupted data."""
        invalid_data = [
            {"symbol": "TEST", "pnl": "invalid"},  # Invalid PnL
            {"symbol": "TEST", "pnl": np.inf},     # Infinite PnL
            {"symbol": "TEST", "pnl": np.nan},     # NaN PnL
            {"symbol": "TEST", "pnl": 100},        # Valid PnL
        ]
        invalid_df = pd.DataFrame(invalid_data)
        
        # Functions should handle invalid data gracefully
        stats = compute_basic_stats(invalid_df)
        assert stats["total_trades"] == 1  # Only valid trades counted
        
        kpis = calculate_kpis(invalid_df)
        assert kpis["total_trades"] == 1


class TestDataIntegrity:
    """Test data integrity across different entry methods."""
    
    def test_data_consistency_across_sources(self):
        """Test that the same trade data produces same analytics regardless of entry method."""
        manager = TradeEntryManager()
        
        # Same trade data entered via different methods
        trade_data = {
            "symbol": "AAPL",
            "entry_time": datetime(2023, 1, 1, 9, 0),
            "exit_time": datetime(2023, 1, 1, 15, 0),
            "entry_price": 150.0,
            "exit_price": 155.0,
            "qty": 100,
            "direction": "long",
            "pnl": 500.0,
            "trade_type": "stocks",
            "broker": "TestBroker"
        }
        
        # Manual entry
        manager.add_manual_trade(trade_data)
        manual_analytics = manager.get_unified_analytics()
        
        # Clear and add via file
        manager.clear_all_trades()
        df = pd.DataFrame([trade_data])
        manager.add_file_trades(df)
        file_analytics = manager.get_unified_analytics()
        
        # Clear and add via API
        manager.clear_all_trades()
        manager.add_api_trades([trade_data], "test_api")
        api_analytics = manager.get_unified_analytics()
        
        # Compare key metrics (should be identical)
        assert manual_analytics["basic_stats"]["total_trades"] == file_analytics["basic_stats"]["total_trades"] == api_analytics["basic_stats"]["total_trades"]
        assert manual_analytics["kpis"]["gross_pnl"] == file_analytics["kpis"]["gross_pnl"] == api_analytics["kpis"]["gross_pnl"]
    
    def test_mixed_source_analytics(self):
        """Test analytics when trades come from multiple sources."""
        manager = TradeEntryManager()
        
        # Add trades from different sources
        manual_trade = {"symbol": "AAPL", "entry_price": 150, "exit_price": 155, "trade_size": 100, "direction": "long", "pnl": 500}
        manager.add_manual_trade(manual_trade)
        
        file_data = pd.DataFrame([{
            "symbol": "TSLA", "entry_time": "2023-01-01", "exit_time": "2023-01-01",
            "entry_price": 200, "exit_price": 190, "qty": 50, "direction": "long",
            "pnl": -500, "trade_type": "stocks", "broker": "FileBroker"
        }])
        manager.add_file_trades(file_data)
        
        api_trade = [{
            "symbol": "NVDA", "entry_time": "2023-01-01", "exit_time": "2023-01-01",
            "entry_price": 300, "exit_price": 310, "qty": 25, "direction": "long",
            "pnl": 250, "trade_type": "stocks", "broker": "ApiBroker"
        }]
        manager.add_api_trades(api_trade, "test_api")
        
        analytics = manager.get_unified_analytics()
        
        # Should have trades from all three sources
        assert analytics["trade_summary"]["total_trades"] == 3
        assert len(analytics["trade_summary"]["data_sources"]) == 3
        
        # Analytics should reflect combined data
        assert analytics["kpis"]["gross_pnl"] == 250  # 500 - 500 + 250
        assert analytics["basic_stats"]["win_rate"] == pytest.approx(66.67, rel=1e-2)
