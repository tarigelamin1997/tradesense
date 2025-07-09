"""
Trade service tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from backend.api.v1.trades.service import TradesService
from backend.models.trade import TradeCreate, TradeUpdate
from backend.core.exceptions import ValidationError, NotFoundError


class TestTradesService:
    """Test TradesService business logic"""

    def test_create_trade_success(self, test_db):
        """Test successful trade creation"""
        service = TradesService(test_db)
        user_id = "test-user-123"
        
        trade_data = TradeCreate(
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=Decimal("150.00"),
            trade_date=datetime.now(),
            strategy="swing_trading",
            notes="Test trade",
            tags=["tech", "large_cap"]
        )
        
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.username = "testuser"
        
        with patch.object(service, 'get_user_by_id') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            result = service.create_trade(user_id, trade_data)
            
            assert result.symbol == "AAPL"
            assert result.side == "buy"
            assert result.quantity == 100
            assert result.price == Decimal("150.00")

    def test_create_trade_invalid_data(self, test_db):
        """Test trade creation with invalid data"""
        service = TradesService(test_db)
        user_id = "test-user-123"
        
        # Test with negative quantity
        trade_data = TradeCreate(
            symbol="AAPL",
            side="buy",
            quantity=-100,  # Invalid
            price=Decimal("150.00"),
            trade_date=datetime.now(),
            strategy="swing_trading",
            notes="Test trade",
            tags=["tech"]
        )
        
        with pytest.raises(ValidationError, match="Quantity must be positive"):
            service.create_trade(user_id, trade_data)

    def test_create_trade_user_not_found(self, test_db):
        """Test trade creation with non-existent user"""
        service = TradesService(test_db)
        user_id = "nonexistent-user-123"
        
        trade_data = TradeCreate(
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=Decimal("150.00"),
            trade_date=datetime.now(),
            strategy="swing_trading",
            notes="Test trade",
            tags=["tech"]
        )
        
        with patch.object(service, 'get_user_by_id') as mock_get_user:
            mock_get_user.return_value = None
            
            with pytest.raises(NotFoundError, match="User not found"):
                service.create_trade(user_id, trade_data)

    def test_get_trade_success(self, test_db):
        """Test successful trade retrieval"""
        service = TradesService(test_db)
        trade_id = "trade-123"
        user_id = "test-user-123"
        
        mock_trade = Mock()
        mock_trade.id = trade_id
        mock_trade.user_id = user_id
        mock_trade.symbol = "AAPL"
        mock_trade.side = "buy"
        mock_trade.quantity = 100
        mock_trade.price = Decimal("150.00")
        
        with patch.object(service, 'get_trade_by_id') as mock_get:
            mock_get.return_value = mock_trade
            
            result = service.get_trade(trade_id, user_id)
            
            assert result == mock_trade
            mock_get.assert_called_once_with(trade_id)

    def test_get_trade_not_found(self, test_db):
        """Test trade retrieval when trade doesn't exist"""
        service = TradesService(test_db)
        trade_id = "nonexistent-trade-123"
        user_id = "test-user-123"
        
        with patch.object(service, 'get_trade_by_id') as mock_get:
            mock_get.return_value = None
            
            result = service.get_trade(trade_id, user_id)
            
            assert result is None

    def test_get_trade_unauthorized(self, test_db):
        """Test trade retrieval when user doesn't own the trade"""
        service = TradesService(test_db)
        trade_id = "trade-123"
        user_id = "wrong-user-123"
        
        mock_trade = Mock()
        mock_trade.id = trade_id
        mock_trade.user_id = "different-user-123"  # Different user
        
        with patch.object(service, 'get_trade_by_id') as mock_get:
            mock_get.return_value = mock_trade
            
            with pytest.raises(ValidationError, match="Not authorized"):
                service.get_trade(trade_id, user_id)

    def test_get_user_trades_success(self, test_db):
        """Test successful retrieval of user's trades"""
        service = TradesService(test_db)
        user_id = "test-user-123"
        
        mock_trades = [
            Mock(id="trade-1", symbol="AAPL", side="buy", quantity=100, price=Decimal("150.00")),
            Mock(id="trade-2", symbol="GOOGL", side="sell", quantity=50, price=Decimal("2800.00"))
        ]
        
        with patch.object(service, 'get_trades_by_user_id') as mock_get:
            mock_get.return_value = mock_trades
            
            result = service.get_user_trades(user_id)
            
            assert result == mock_trades
            mock_get.assert_called_once_with(user_id)

    def test_get_user_trades_empty(self, test_db):
        """Test retrieval of user's trades when none exist"""
        service = TradesService(test_db)
        user_id = "test-user-123"
        
        with patch.object(service, 'get_trades_by_user_id') as mock_get:
            mock_get.return_value = []
            
            result = service.get_user_trades(user_id)
            
            assert result == []

    def test_update_trade_success(self, test_db):
        """Test successful trade update"""
        service = TradesService(test_db)
        trade_id = "trade-123"
        user_id = "test-user-123"
        
        mock_trade = Mock()
        mock_trade.id = trade_id
        mock_trade.user_id = user_id
        mock_trade.symbol = "AAPL"
        mock_trade.side = "buy"
        mock_trade.quantity = 100
        mock_trade.price = Decimal("150.00")
        
        update_data = TradeUpdate(
            notes="Updated notes",
            tags=["tech", "updated"]
        )
        
        with patch.object(service, 'get_trade_by_id') as mock_get:
            mock_get.return_value = mock_trade
            
            result = service.update_trade(trade_id, user_id, update_data)
            
            assert result == mock_trade
            assert mock_trade.notes == "Updated notes"
            assert mock_trade.tags == ["tech", "updated"]

    def test_update_trade_not_found(self, test_db):
        """Test trade update when trade doesn't exist"""
        service = TradesService(test_db)
        trade_id = "nonexistent-trade-123"
        user_id = "test-user-123"
        
        update_data = TradeUpdate(notes="Updated notes")
        
        with patch.object(service, 'get_trade_by_id') as mock_get:
            mock_get.return_value = None
            
            result = service.update_trade(trade_id, user_id, update_data)
            
            assert result is None

    def test_update_trade_unauthorized(self, test_db):
        """Test trade update when user doesn't own the trade"""
        service = TradesService(test_db)
        trade_id = "trade-123"
        user_id = "wrong-user-123"
        
        mock_trade = Mock()
        mock_trade.id = trade_id
        mock_trade.user_id = "different-user-123"  # Different user
        
        update_data = TradeUpdate(notes="Updated notes")
        
        with patch.object(service, 'get_trade_by_id') as mock_get:
            mock_get.return_value = mock_trade
            
            with pytest.raises(ValidationError, match="Not authorized"):
                service.update_trade(trade_id, user_id, update_data)

    def test_delete_trade_success(self, test_db):
        """Test successful trade deletion"""
        service = TradesService(test_db)
        trade_id = "trade-123"
        user_id = "test-user-123"
        
        mock_trade = Mock()
        mock_trade.id = trade_id
        mock_trade.user_id = user_id
        mock_trade.symbol = "AAPL"
        
        with patch.object(service, 'get_trade_by_id') as mock_get, \
             patch.object(service, 'delete_trade') as mock_delete:
            
            mock_get.return_value = mock_trade
            mock_delete.return_value = True
            
            result = service.delete_trade(trade_id, user_id)
            
            assert result is True
            mock_delete.assert_called_once_with(trade_id)

    def test_delete_trade_not_found(self, test_db):
        """Test trade deletion when trade doesn't exist"""
        service = TradesService(test_db)
        trade_id = "nonexistent-trade-123"
        user_id = "test-user-123"
        
        with patch.object(service, 'get_trade_by_id') as mock_get:
            mock_get.return_value = None
            
            result = service.delete_trade(trade_id, user_id)
            
            assert result is False

    def test_delete_trade_unauthorized(self, test_db):
        """Test trade deletion when user doesn't own the trade"""
        service = TradesService(test_db)
        trade_id = "trade-123"
        user_id = "wrong-user-123"
        
        mock_trade = Mock()
        mock_trade.id = trade_id
        mock_trade.user_id = "different-user-123"  # Different user
        
        with patch.object(service, 'get_trade_by_id') as mock_get:
            mock_get.return_value = mock_trade
            
            with pytest.raises(ValidationError, match="Not authorized"):
                service.delete_trade(trade_id, user_id)

    def test_get_trade_analytics_success(self, test_db):
        """Test successful trade analytics retrieval"""
        service = TradesService(test_db)
        user_id = "test-user-123"
        
        mock_analytics = {
            "total_trades": 10,
            "winning_trades": 6,
            "losing_trades": 4,
            "win_rate": 0.6,
            "total_pnl": Decimal("1500.00"),
            "average_trade": Decimal("150.00")
        }
        
        with patch.object(service, 'calculate_trade_analytics') as mock_calc:
            mock_calc.return_value = mock_analytics
            
            result = service.get_trade_analytics(user_id)
            
            assert result == mock_analytics
            mock_calc.assert_called_once_with(user_id)

    def test_get_trade_analytics_no_trades(self, test_db):
        """Test trade analytics when user has no trades"""
        service = TradesService(test_db)
        user_id = "test-user-123"
        
        empty_analytics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": Decimal("0.00"),
            "average_trade": Decimal("0.00")
        }
        
        with patch.object(service, 'calculate_trade_analytics') as mock_calc:
            mock_calc.return_value = empty_analytics
            
            result = service.get_trade_analytics(user_id)
            
            assert result == empty_analytics

    def test_validate_trade_data_success(self, test_db):
        """Test successful trade data validation"""
        service = TradesService(test_db)
        
        trade_data = TradeCreate(
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=Decimal("150.00"),
            trade_date=datetime.now(),
            strategy="swing_trading",
            notes="Test trade",
            tags=["tech"]
        )
        
        result = service._validate_trade_data(trade_data)
        assert result is True

    def test_validate_trade_data_invalid_quantity(self, test_db):
        """Test trade data validation with invalid quantity"""
        service = TradesService(test_db)
        
        trade_data = TradeCreate(
            symbol="AAPL",
            side="buy",
            quantity=0,  # Invalid
            price=Decimal("150.00"),
            trade_date=datetime.now(),
            strategy="swing_trading",
            notes="Test trade",
            tags=["tech"]
        )
        
        with pytest.raises(ValidationError, match="Quantity must be positive"):
            service._validate_trade_data(trade_data)

    def test_validate_trade_data_invalid_price(self, test_db):
        """Test trade data validation with invalid price"""
        service = TradesService(test_db)
        
        trade_data = TradeCreate(
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=Decimal("-150.00"),  # Invalid
            trade_date=datetime.now(),
            strategy="swing_trading",
            notes="Test trade",
            tags=["tech"]
        )
        
        with pytest.raises(ValidationError, match="Price must be positive"):
            service._validate_trade_data(trade_data)

    def test_validate_trade_data_invalid_side(self, test_db):
        """Test trade data validation with invalid side"""
        service = TradesService(test_db)
        
        trade_data = TradeCreate(
            symbol="AAPL",
            side="invalid_side",  # Invalid
            quantity=100,
            price=Decimal("150.00"),
            trade_date=datetime.now(),
            strategy="swing_trading",
            notes="Test trade",
            tags=["tech"]
        )
        
        with pytest.raises(ValidationError, match="Side must be 'buy' or 'sell'"):
            service._validate_trade_data(trade_data)

    def test_calculate_trade_pnl(self, test_db):
        """Test trade P&L calculation"""
        service = TradesService(test_db)
        
        # Test buy trade (no P&L until sold)
        buy_trade = Mock()
        buy_trade.side = "buy"
        buy_trade.quantity = 100
        buy_trade.price = Decimal("150.00")
        buy_trade.exit_price = None
        
        pnl = service._calculate_trade_pnl(buy_trade)
        assert pnl == Decimal("0.00")
        
        # Test completed trade
        completed_trade = Mock()
        completed_trade.side = "buy"
        completed_trade.quantity = 100
        completed_trade.price = Decimal("150.00")
        completed_trade.exit_price = Decimal("160.00")
        
        pnl = service._calculate_trade_pnl(completed_trade)
        assert pnl == Decimal("1000.00")  # (160 - 150) * 100

    def test_get_trade_with_journal_success(self, test_db):
        """Test successful retrieval of trade with journal entries"""
        service = TradesService(test_db)
        trade_id = "trade-123"
        user_id = "test-user-123"
        
        mock_trade = Mock()
        mock_trade.id = trade_id
        mock_trade.user_id = user_id
        mock_trade.symbol = "AAPL"
        mock_trade.side = "buy"
        mock_trade.quantity = 100
        mock_trade.price = Decimal("150.00")
        
        mock_journal_entries = [
            Mock(id="entry-1", content="Entry 1", created_at=datetime.now()),
            Mock(id="entry-2", content="Entry 2", created_at=datetime.now())
        ]
        
        with patch.object(service, 'get_trade_by_id') as mock_get_trade, \
             patch.object(service, 'get_journal_entries_by_trade_id') as mock_get_journal:
            
            mock_get_trade.return_value = mock_trade
            mock_get_journal.return_value = mock_journal_entries
            
            result = service.get_trade_with_journal(trade_id, user_id)
            
            assert result["trade"] == mock_trade
            assert result["journal_entries"] == mock_journal_entries
            mock_get_trade.assert_called_once_with(trade_id)
            mock_get_journal.assert_called_once_with(trade_id)

    def test_get_trade_with_journal_not_found(self, test_db):
        """Test trade with journal retrieval when trade doesn't exist"""
        service = TradesService(test_db)
        trade_id = "nonexistent-trade-123"
        user_id = "test-user-123"
        
        with patch.object(service, 'get_trade_by_id') as mock_get_trade:
            mock_get_trade.return_value = None
            
            result = service.get_trade_with_journal(trade_id, user_id)
            
            assert result is None

    def test_get_trade_with_journal_unauthorized(self, test_db):
        """Test trade with journal retrieval when user doesn't own the trade"""
        service = TradesService(test_db)
        trade_id = "trade-123"
        user_id = "wrong-user-123"
        
        mock_trade = Mock()
        mock_trade.id = trade_id
        mock_trade.user_id = "different-user-123"  # Different user
        
        with patch.object(service, 'get_trade_by_id') as mock_get_trade:
            mock_get_trade.return_value = mock_trade
            
            with pytest.raises(ValidationError, match="Not authorized"):
                service.get_trade_with_journal(trade_id, user_id)


class TestTradesServiceIntegration:
    """Integration tests for TradesService"""

    def test_trade_lifecycle(self, test_db):
        """Test complete trade lifecycle (create, read, update, delete)"""
        service = TradesService(test_db)
        user_id = "test-user-123"
        
        # Test trade creation
        trade_data = TradeCreate(
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=Decimal("150.00"),
            trade_date=datetime.now(),
            strategy="swing_trading",
            notes="Initial trade",
            tags=["tech"]
        )
        
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.username = "testuser"
        
        with patch.object(service, 'get_user_by_id') as mock_get_user, \
             patch.object(service, 'get_trade_by_id') as mock_get_trade, \
             patch.object(service, 'delete_trade') as mock_delete:
            
            mock_get_user.return_value = mock_user
            
            # Create trade
            created_trade = service.create_trade(user_id, trade_data)
            assert created_trade.symbol == "AAPL"
            assert created_trade.side == "buy"
            
            # Read trade
            mock_get_trade.return_value = created_trade
            retrieved_trade = service.get_trade(created_trade.id, user_id)
            assert retrieved_trade == created_trade
            
            # Update trade
            update_data = TradeUpdate(notes="Updated trade")
            updated_trade = service.update_trade(created_trade.id, user_id, update_data)
            assert updated_trade.notes == "Updated trade"
            
            # Delete trade
            mock_delete.return_value = True
            delete_result = service.delete_trade(created_trade.id, user_id)
            assert delete_result is True

    def test_user_trades_analytics_integration(self, test_db):
        """Test integration between user trades and analytics"""
        service = TradesService(test_db)
        user_id = "test-user-123"
        
        mock_trades = [
            Mock(symbol="AAPL", side="buy", quantity=100, price=Decimal("150.00"), exit_price=Decimal("160.00")),
            Mock(symbol="GOOGL", side="sell", quantity=50, price=Decimal("2800.00"), exit_price=Decimal("2750.00"))
        ]
        
        with patch.object(service, 'get_trades_by_user_id') as mock_get_trades, \
             patch.object(service, 'calculate_trade_analytics') as mock_calc_analytics:
            
            mock_get_trades.return_value = mock_trades
            mock_calc_analytics.return_value = {
                "total_trades": 2,
                "winning_trades": 1,
                "losing_trades": 1,
                "win_rate": 0.5,
                "total_pnl": Decimal("500.00"),
                "average_trade": Decimal("250.00")
            }
            
            # Get user trades
            user_trades = service.get_user_trades(user_id)
            assert user_trades == mock_trades
            
            # Get analytics
            analytics = service.get_trade_analytics(user_id)
            assert analytics["total_trades"] == 2
            assert analytics["win_rate"] == 0.5
