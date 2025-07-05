from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from models.portfolio import Portfolio, EquitySnapshot
from backend.models.trade import Trade
from models.user import User

class PortfolioSimulator:
    """Service for managing virtual portfolio simulations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_portfolio(self, user_id: str, name: str, initial_balance: float = 10000.0) -> Dict[str, Any]:
        """Create a new virtual portfolio"""
        try:
            # Check if this should be the default portfolio
            existing_portfolios = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).count()
            is_default = existing_portfolios == 0
            
            portfolio = Portfolio(
                user_id=user_id,
                name=name,
                initial_balance=initial_balance,
                current_balance=initial_balance,
                is_default=is_default
            )
            
            self.db.add(portfolio)
            self.db.commit()
            
            # Create initial equity snapshot
            self._create_equity_snapshot(portfolio.id, initial_balance, 0.0, 0.0, 0)
            
            return {
                "success": True,
                "portfolio_id": portfolio.id,
                "message": f"Portfolio '{name}' created successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_user_portfolios(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all portfolios for a user"""
        portfolios = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        
        result = []
        for portfolio in portfolios:
            result.append({
                "id": portfolio.id,
                "name": portfolio.name,
                "initial_balance": portfolio.initial_balance,
                "current_balance": portfolio.current_balance,
                "total_pnl": portfolio.total_pnl,
                "total_trades": portfolio.total_trades,
                "winning_trades": portfolio.winning_trades,
                "win_rate": portfolio.winning_trades / max(portfolio.total_trades, 1) * 100,
                "is_default": portfolio.is_default,
                "created_at": portfolio.created_at.isoformat(),
                "return_percentage": ((portfolio.current_balance - portfolio.initial_balance) / portfolio.initial_balance) * 100
            })
        
        return result
    
    def simulate_trades_on_portfolio(self, portfolio_id: str, trade_ids: List[str]) -> Dict[str, Any]:
        """Simulate a list of trades on a portfolio"""
        try:
            portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if not portfolio:
                return {"success": False, "error": "Portfolio not found"}
            
            trades = self.db.query(Trade).filter(Trade.id.in_(trade_ids)).order_by(Trade.entry_time).all()
            
            if not trades:
                return {"success": False, "error": "No trades found"}
            
            # Reset portfolio to initial state
            portfolio.current_balance = portfolio.initial_balance
            portfolio.total_pnl = 0.0
            portfolio.total_trades = 0
            portfolio.winning_trades = 0
            
            # Clear existing snapshots
            self.db.query(EquitySnapshot).filter(EquitySnapshot.portfolio_id == portfolio_id).delete()
            
            # Simulate each trade
            running_balance = portfolio.initial_balance
            daily_snapshots = {}
            
            for trade in trades:
                if trade.pnl is not None:
                    running_balance += trade.pnl
                    portfolio.total_pnl += trade.pnl
                    portfolio.total_trades += 1
                    
                    if trade.pnl > 0:
                        portfolio.winning_trades += 1
                    
                    # Create daily snapshot
                    trade_date = trade.exit_time.date() if trade.exit_time else trade.entry_time.date()
                    
                    if trade_date not in daily_snapshots:
                        daily_snapshots[trade_date] = {
                            'balance': running_balance,
                            'daily_pnl': trade.pnl,
                            'trade_count': 1
                        }
                    else:
                        daily_snapshots[trade_date]['balance'] = running_balance
                        daily_snapshots[trade_date]['daily_pnl'] += trade.pnl
                        daily_snapshots[trade_date]['trade_count'] += 1
            
            portfolio.current_balance = running_balance
            
            # Create equity snapshots
            for date, data in daily_snapshots.items():
                self._create_equity_snapshot(
                    portfolio_id, 
                    data['balance'], 
                    data['daily_pnl'],
                    data['balance'] - portfolio.initial_balance,
                    data['trade_count'],
                    datetime.combine(date, datetime.min.time())
                )
            
            self.db.commit()
            
            return {
                "success": True,
                "portfolio_summary": {
                    "initial_balance": portfolio.initial_balance,
                    "final_balance": portfolio.current_balance,
                    "total_pnl": portfolio.total_pnl,
                    "total_trades": portfolio.total_trades,
                    "winning_trades": portfolio.winning_trades,
                    "win_rate": portfolio.winning_trades / max(portfolio.total_trades, 1) * 100,
                    "return_percentage": ((portfolio.current_balance - portfolio.initial_balance) / portfolio.initial_balance) * 100
                }
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_equity_curve(self, portfolio_id: str) -> Dict[str, Any]:
        """Get equity curve data for portfolio"""
        try:
            snapshots = self.db.query(EquitySnapshot).filter(
                EquitySnapshot.portfolio_id == portfolio_id
            ).order_by(EquitySnapshot.timestamp).all()
            
            if not snapshots:
                return {"success": False, "error": "No equity data found"}
            
            equity_data = []
            for snapshot in snapshots:
                equity_data.append({
                    "date": snapshot.timestamp.isoformat(),
                    "balance": snapshot.balance,
                    "daily_pnl": snapshot.daily_pnl,
                    "total_pnl": snapshot.total_pnl,
                    "trade_count": snapshot.trade_count
                })
            
            # Calculate additional metrics
            df = pd.DataFrame(equity_data)
            if len(df) > 1:
                df['returns'] = df['balance'].pct_change()
                sharpe_ratio = df['returns'].mean() / df['returns'].std() * (252 ** 0.5) if df['returns'].std() != 0 else 0
                max_drawdown = ((df['balance'] / df['balance'].cummax()) - 1).min() * 100
            else:
                sharpe_ratio = 0
                max_drawdown = 0
            
            return {
                "success": True,
                "equity_curve": equity_data,
                "metrics": {
                    "sharpe_ratio": round(sharpe_ratio, 3),
                    "max_drawdown": round(max_drawdown, 2),
                    "total_return": round(((equity_data[-1]['balance'] - equity_data[0]['balance']) / equity_data[0]['balance']) * 100, 2) if equity_data else 0
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_equity_snapshot(self, portfolio_id: str, balance: float, daily_pnl: float, 
                               total_pnl: float, trade_count: int, timestamp: datetime = None):
        """Create an equity snapshot record"""
        snapshot = EquitySnapshot(
            portfolio_id=portfolio_id,
            timestamp=timestamp or datetime.utcnow(),
            balance=balance,
            daily_pnl=daily_pnl,
            total_pnl=total_pnl,
            trade_count=trade_count
        )
        self.db.add(snapshot)
    
    def delete_portfolio(self, portfolio_id: str, user_id: str) -> Dict[str, Any]:
        """Delete a portfolio and all its data"""
        try:
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id
            ).first()
            
            if not portfolio:
                return {"success": False, "error": "Portfolio not found"}
            
            if portfolio.is_default:
                return {"success": False, "error": "Cannot delete default portfolio"}
            
            self.db.delete(portfolio)
            self.db.commit()
            
            return {"success": True, "message": "Portfolio deleted successfully"}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
