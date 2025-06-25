
"""
Trade service tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import uuid

from backend.api.v1.trades.service import TradeService
from backend.core.exceptions import ValidationError, NotFoundError, BusinessLogicError


class TestTradeService:
    """Test TradeService business logic"""

    def test_create_trade_success(self):
        """Test successful trade creation"""
        service = TradeService()
        user_id = "test-user-123"
        trade_data = {
            "symbol": "AAPL",
            "direction": "long",
            "quantity": 100.0,
            "entry_price": 150.0,
            "entry_time": datetime.now(),
            "strategy_tag": "momentum"
        }
        
        with patch.object(service, '_validate_trade_data') as mock_validate, \
             patch.object(service, '_save_trade') as mock_save, \
             patch.object(service, '_calculate_trade_metrics') as mock_calculate:
            
            mock_validate.return_value = True
            mock_save.return_value = {"id": "trade-123", **trade_data}
            mock_calculate.return_value = {"pnl": None, "commission": 0.0}
            
            result = service.create_trade(user_id, trade_data)
            
            assert result["symbol"] == "AAPL"
            assert result["direction"] == "long"
            assert "id" in result

    def test_create_trade_validation_error(self):
        """Test trade creation with validation errors"""
        service = TradeService()
        user_id = "test-user-123"
        invalid_trade = {
            "symbol": "",
            "direction": "invalid",
            "quantity": -100,
            "entry_price": 0
        }
        
        with patch.object(service, '_validate_trade_data') as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid trade data")
            
            with pytest.raises(ValidationError):
                service.create_trade(user_id, invalid_trade)

    def test_get_trade_by_id_success(self):
        """Test successful trade retrieval by ID"""
        service = TradeService()
        trade_id = "trade-123"
        user_id = "test-user-123"
        
        mock_trade = {
            "id": trade_id,
            "symbol": "AAPL",
            "direction": "long",
            "user_id": user_id
        }
        
        with patch.object(service, '_get_trade_from_db') as mock_get:
            mock_get.return_value = mock_trade
            
            result = service.get_trade_by_id(trade_id, user_id)
            
            assert result["id"] == trade_id
            assert result["symbol"] == "AAPL"

    def test_get_trade_by_id_not_found(self):
        """Test trade retrieval when trade doesn't exist"""
        service = TradeService()
        
        with patch.object(service, '_get_trade_from_db') as mock_get:
            mock_get.return_value = None
            
            result = service.get_trade_by_id("nonexistent", "user-123")
            
            assert result is None

    def test_get_trade_by_id_access_denied(self):
        """Test trade retrieval when user doesn't own the trade"""
        service = TradeService()
        trade_id = "trade-123"
        
        mock_trade = {
            "id": trade_id,
            "user_id": "other-user-456"  # Different user
        }
        
        with patch.object(service, '_get_trade_from_db') as mock_get:
            mock_get.return_value = mock_trade
            
            result = service.get_trade_by_id(trade_id, "test-user-123")
            
            assert result is None  # Should not return trade owned by other user

    def test_get_trades_with_filters(self):
        """Test trade retrieval with filters and pagination"""
        service = TradeService()
        user_id = "test-user-123"
        filters = {
            "symbol": "AAPL",
            "start_date": datetime.now() - timedelta(days=30),
            "min_pnl": 100
        }
        
        mock_trades = [
            {"id": "trade-1", "symbol": "AAPL", "pnl": 200},
            {"id": "trade-2", "symbol": "AAPL", "pnl": 150}
        ]
        
        with patch.object(service, '_query_trades') as mock_query:
            mock_query.return_value = mock_trades
            
            result = service.get_trades(user_id, filters, skip=0, limit=10)
            
            assert len(result) == 2
            assert all(trade["symbol"] == "AAPL" for trade in result)

    def test_update_trade_success(self):
        """Test successful trade update"""
        service = TradeService()
        trade_id = "trade-123"
        user_id = "test-user-123"
        update_data = {
            "exit_price": 160.0,
            "exit_time": datetime.now(),
            "notes": "Updated trade"
        }
        
        mock_existing_trade = {
            "id": trade_id,
            "symbol": "AAPL",
            "user_id": user_id,
            "entry_price": 150.0,
            "quantity": 100
        }
        
        with patch.object(service, '_get_trade_from_db') as mock_get, \
             patch.object(service, '_validate_update_data') as mock_validate, \
             patch.object(service, '_update_trade_in_db') as mock_update, \
             patch.object(service, '_calculate_trade_metrics') as mock_calculate:
            
            mock_get.return_value = mock_existing_trade
            mock_validate.return_value = True
            mock_calculate.return_value = {"pnl": 1000.0, "net_pnl": 990.0}
            mock_update.return_value = {**mock_existing_trade, **update_data, "pnl": 1000.0}
            
            result = service.update_trade(trade_id, user_id, update_data)
            
            assert result["exit_price"] == 160.0
            assert result["pnl"] == 1000.0

    def test_update_trade_not_found(self):
        """Test updating non-existent trade"""
        service = TradeService()
        
        with patch.object(service, '_get_trade_from_db') as mock_get:
            mock_get.return_value = None
            
            result = service.update_trade("nonexistent", "user-123", {})
            
            assert result is None

    def test_delete_trade_success(self):
        """Test successful trade deletion"""
        service = TradeService()
        trade_id = "trade-123"
        user_id = "test-user-123"
        
        mock_trade = {"id": trade_id, "user_id": user_id}
        
        with patch.object(service, '_get_trade_from_db') as mock_get, \
             patch.object(service, '_delete_trade_from_db') as mock_delete:
            
            mock_get.return_value = mock_trade
            mock_delete.return_value = True
            
            result = service.delete_trade(trade_id, user_id)
            
            assert result is True

    def test_delete_trade_not_found(self):
        """Test deleting non-existent trade"""
        service = TradeService()
        
        with patch.object(service, '_get_trade_from_db') as mock_get:
            mock_get.return_value = None
            
            result = service.delete_trade("nonexistent", "user-123")
            
            assert result is False

    def test_get_analytics_basic(self):
        """Test basic analytics calculation"""
        service = TradeService()
        user_id = "test-user-123"
        
        mock_trades = [
            {"pnl": 500.0, "direction": "long", "symbol": "AAPL"},
            {"pnl": -200.0, "direction": "short", "symbol": "TSLA"},
            {"pnl": 300.0, "direction": "long", "symbol": "AAPL"},
            {"pnl": -100.0, "direction": "long", "symbol": "MSFT"}
        ]
        
        with patch.object(service, '_get_user_trades') as mock_get_trades, \
             patch.object(service, '_calculate_analytics') as mock_calculate:
            
            mock_get_trades.return_value = mock_trades
            mock_calculate.return_value = {
                "total_trades": 4,
                "winning_trades": 2,
                "losing_trades": 2,
                "win_rate": 50.0,
                "total_pnl": 500.0,
                "profit_factor": 2.67
            }
            
            result = service.get_analytics(user_id)
            
            assert result["total_trades"] == 4
            assert result["win_rate"] == 50.0
            assert result["total_pnl"] == 500.0

    def test_get_analytics_with_date_filter(self):
        """Test analytics with date range filter"""
        service = TradeService()
        user_id = "test-user-123"
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        with patch.object(service, '_get_user_trades') as mock_get_trades, \
             patch.object(service, '_calculate_analytics') as mock_calculate:
            
            mock_get_trades.return_value = []
            mock_calculate.return_value = {"total_trades": 0}
            
            result = service.get_analytics(user_id, start_date, end_date)
            
            # Verify that date filters were passed to the query
            mock_get_trades.assert_called_once_with(
                user_id, 
                start_date=start_date, 
                end_date=end_date
            )

    def test_bulk_create_trades_success(self):
        """Test successful bulk trade creation"""
        service = TradeService()
        user_id = "test-user-123"
        trades_data = [
            {"symbol": "AAPL", "direction": "long", "quantity": 100, "entry_price": 150.0},
            {"symbol": "TSLA", "direction": "short", "quantity": 50, "entry_price": 800.0}
        ]
        
        with patch.object(service, '_validate_trade_data') as mock_validate, \
             patch.object(service, '_bulk_save_trades') as mock_bulk_save:
            
            mock_validate.return_value = True
            mock_bulk_save.return_value = {
                "created_count": 2,
                "failed_count": 0,
                "errors": []
            }
            
            result = service.bulk_create_trades(user_id, trades_data)
            
            assert result["created_count"] == 2
            assert result["failed_count"] == 0

    def test_bulk_create_trades_partial_failure(self):
        """Test bulk trade creation with some failures"""
        service = TradeService()
        user_id = "test-user-123"
        trades_data = [
            {"symbol": "AAPL", "direction": "long", "quantity": 100, "entry_price": 150.0},
            {"symbol": "", "direction": "invalid", "quantity": -50, "entry_price": 0}  # Invalid
        ]
        
        def mock_validate(trade_data):
            if not trade_data.get("symbol"):
                raise ValidationError("Symbol is required")
            return True
        
        with patch.object(service, '_validate_trade_data', side_effect=mock_validate), \
             patch.object(service, '_save_trade') as mock_save:
            
            mock_save.return_value = {"id": "trade-123"}
            
            result = service.bulk_create_trades(user_id, trades_data)
            
            assert result["created_count"] == 1
            assert result["failed_count"] == 1
            assert len(result["errors"]) == 1

    def test_calculate_trade_metrics(self):
        """Test trade metrics calculation"""
        service = TradeService()
        
        # Long position with profit
        long_trade = {
            "direction": "long",
            "quantity": 100,
            "entry_price": 150.0,
            "exit_price": 160.0
        }
        
        long_metrics = service._calculate_trade_metrics(long_trade)
        assert long_metrics["pnl"] == 1000.0  # (160 - 150) * 100
        
        # Short position with profit
        short_trade = {
            "direction": "short",
            "quantity": 50,
            "entry_price": 800.0,
            "exit_price": 790.0
        }
        
        short_metrics = service._calculate_trade_metrics(short_trade)
        assert short_metrics["pnl"] == 500.0  # (800 - 790) * 50

    def test_validate_trade_data(self):
        """Test trade data validation"""
        service = TradeService()
        
        # Valid trade
        valid_trade = {
            "symbol": "AAPL",
            "direction": "long",
            "quantity": 100.0,
            "entry_price": 150.0,
            "entry_time": datetime.now()
        }
        
        assert service._validate_trade_data(valid_trade) is True
        
        # Invalid trades
        invalid_trades = [
            {"symbol": "", "direction": "long", "quantity": 100, "entry_price": 150},  # Empty symbol
            {"symbol": "AAPL", "direction": "invalid", "quantity": 100, "entry_price": 150},  # Invalid direction
            {"symbol": "AAPL", "direction": "long", "quantity": -100, "entry_price": 150},  # Negative quantity
            {"symbol": "AAPL", "direction": "long", "quantity": 100, "entry_price": 0},  # Zero price
        ]
        
        for invalid_trade in invalid_trades:
            with pytest.raises(ValidationError):
                service._validate_trade_data(invalid_trade)

    def test_validate_update_data(self):
        """Test trade update data validation"""
        service = TradeService()
        
        # Valid updates
        valid_updates = [
            {"exit_price": 160.0},
            {"exit_time": datetime.now()},
            {"notes": "Updated trade"},
            {"exit_price": 160.0, "exit_time": datetime.now()}
        ]
        
        for update in valid_updates:
            assert service._validate_update_data(update) is True
        
        # Invalid updates
        invalid_updates = [
            {"exit_price": -160.0},  # Negative price
            {"exit_price": 0},  # Zero price
            {"entry_price": 150.0},  # Can't update entry price
            {"symbol": "TSLA"}  # Can't update symbol
        ]
        
        for invalid_update in invalid_updates:
            with pytest.raises(ValidationError):
                service._validate_update_data(invalid_update)


class TestTradeServiceAdvanced:
    """Advanced trade service tests"""

    def test_performance_summary_calculation(self):
        """Test performance summary calculation"""
        service = TradeService()
        user_id = "test-user-123"
        
        mock_trades = [
            {
                "symbol": "AAPL", "pnl": 500.0, 
                "entry_time": datetime(2024, 1, 15),
                "strategy_tag": "momentum"
            },
            {
                "symbol": "TSLA", "pnl": -200.0, 
                "entry_time": datetime(2024, 1, 16),
                "strategy_tag": "reversal"
            },
            {
                "symbol": "AAPL", "pnl": 300.0, 
                "entry_time": datetime(2024, 1, 17),
                "strategy_tag": "momentum"
            }
        ]
        
        with patch.object(service, '_get_user_trades') as mock_get_trades:
            mock_get_trades.return_value = mock_trades
            
            result = service.get_performance_summary(user_id)
            
            assert "symbol_performance" in result
            assert "strategy_performance" in result
            assert "daily_pnl" in result

    def test_risk_metrics_calculation(self):
        """Test risk metrics calculation"""
        service = TradeService()
        
        trades_pnl = [100, -50, 200, -75, 300, -25, 150]
        
        risk_metrics = service._calculate_risk_metrics(trades_pnl)
        
        assert "max_drawdown" in risk_metrics
        assert "sharpe_ratio" in risk_metrics
        assert "win_rate" in risk_metrics
        assert risk_metrics["max_drawdown"] >= 0

    def test_symbol_performance_analysis(self):
        """Test symbol performance analysis"""
        service = TradeService()
        
        trades = [
            {"symbol": "AAPL", "pnl": 500.0},
            {"symbol": "AAPL", "pnl": -200.0},
            {"symbol": "TSLA", "pnl": 300.0},
            {"symbol": "MSFT", "pnl": -100.0}
        ]
        
        symbol_performance = service._analyze_symbol_performance(trades)
        
        assert len(symbol_performance) == 3  # AAPL, TSLA, MSFT
        
        # Find AAPL performance
        aapl_perf = next(perf for perf in symbol_performance if perf["symbol"] == "AAPL")
        assert aapl_perf["total_trades"] == 2
        assert aapl_perf["total_pnl"] == 300.0


@pytest.mark.integration
class TestTradeServiceIntegration:
    """Integration tests for TradeService"""

    def test_complete_trade_workflow(self):
        """Test complete trade workflow with real calculations"""
        service = TradeService()
        user_id = "integration-user-123"
        
        # Create initial trade
        trade_data = {
            "symbol": "AAPL",
            "direction": "long",
            "quantity": 100.0,
            "entry_price": 150.0,
            "entry_time": datetime.now() - timedelta(hours=2),
            "strategy_tag": "momentum"
        }
        
        with patch.object(service, '_save_trade') as mock_save, \
             patch.object(service, '_get_trade_from_db') as mock_get, \
             patch.object(service, '_update_trade_in_db') as mock_update:
            
            # Create trade
            trade_id = str(uuid.uuid4())
            created_trade = {"id": trade_id, **trade_data, "pnl": None}
            mock_save.return_value = created_trade
            
            result = service.create_trade(user_id, trade_data)
            assert result["id"] == trade_id
            
            # Update with exit
            mock_get.return_value = created_trade
            update_data = {
                "exit_price": 160.0,
                "exit_time": datetime.now()
            }
            
            updated_trade = {**created_trade, **update_data}
            # Calculate real PnL
            metrics = service._calculate_trade_metrics(updated_trade)
            updated_trade.update(metrics)
            mock_update.return_value = updated_trade
            
            updated_result = service.update_trade(trade_id, user_id, update_data)
            
            assert updated_result["exit_price"] == 160.0
            assert updated_result["pnl"] == 1000.0  # (160-150) * 100

    def test_analytics_integration(self):
        """Test analytics calculation with realistic data"""
        service = TradeService()
        user_id = "analytics-user-123"
        
        # Simulate realistic trading data
        mock_trades = [
            {"pnl": 500.0, "symbol": "AAPL", "strategy_tag": "momentum"},
            {"pnl": -200.0, "symbol": "TSLA", "strategy_tag": "reversal"},
            {"pnl": 300.0, "symbol": "AAPL", "strategy_tag": "momentum"},
            {"pnl": -150.0, "symbol": "MSFT", "strategy_tag": "breakout"},
            {"pnl": 400.0, "symbol": "TSLA", "strategy_tag": "momentum"}
        ]
        
        with patch.object(service, '_get_user_trades') as mock_get_trades:
            mock_get_trades.return_value = mock_trades
            
            analytics = service.get_analytics(user_id)
            
            # Verify calculated metrics
            assert analytics["total_trades"] == 5
            assert analytics["winning_trades"] == 3
            assert analytics["losing_trades"] == 2
            assert analytics["win_rate"] == 60.0
            assert analytics["total_pnl"] == 850.0
            
            # Test profit factor calculation
            gross_profit = 500 + 300 + 400  # 1200
            gross_loss = 200 + 150  # 350
            expected_profit_factor = gross_profit / gross_loss
            assert abs(analytics["profit_factor"] - expected_profit_factor) < 0.01
