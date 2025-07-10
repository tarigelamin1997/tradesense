
"""
Test suite for analytics service
"""
import pytest
import asyncio
from services.analytics_service import AnalyticsService
import pandas as pd
from datetime import datetime, timedelta

@pytest.fixture
def sample_trades_data():
    """Sample trade data for testing"""
    return pd.DataFrame([
        {
            "symbol": "AAPL",
            "entry_time": datetime.now() - timedelta(days=5),
            "exit_time": datetime.now() - timedelta(days=4),
            "entry_price": 150.0,
            "exit_price": 155.0,
            "quantity": 100,
            "pnl": 500.0,
            "direction": "long"
        },
        {
            "symbol": "TSLA",
            "entry_time": datetime.now() - timedelta(days=3),
            "exit_time": datetime.now() - timedelta(days=2),
            "entry_price": 800.0,
            "exit_price": 790.0,
            "quantity": 10,
            "pnl": -100.0,
            "direction": "long"
        }
    ])

@pytest.mark.asyncio
async def test_analytics_overview(sample_trades_data):
    """Test analytics overview calculation"""
    analytics_service = AnalyticsService()
    overview = analytics_service._calculate_overview(sample_trades_data)
    
    assert overview["total_trades"] == 2
    assert overview["winning_trades"] == 1
    assert overview["losing_trades"] == 1
    assert overview["win_rate"] == 50.0
    assert overview["total_pnl"] == 400.0

@pytest.mark.asyncio
async def test_performance_metrics(sample_trades_data):
    """Test performance metrics calculation"""
    analytics_service = AnalyticsService()
    metrics = analytics_service._calculate_performance_metrics(sample_trades_data)
    
    assert "sharpe_ratio" in metrics
    assert "sortino_ratio" in metrics
    assert metrics["average_win"] == 500.0
    assert metrics["average_loss"] == -100.0
