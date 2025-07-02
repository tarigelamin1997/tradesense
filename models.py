from dataclasses import dataclass
from datetime import datetime

@dataclass
class Trade:
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    qty: float
    direction: str  # 'long' or 'short'
    pnl: float
    trade_type: str
    broker: str

    @property
    def duration(self) -> float:
        """Trade duration in minutes."""
        return (self.exit_time - self.entry_time).total_seconds() / 60

    @staticmethod
    def from_series(s: 'pd.Series') -> 'Trade':
        from pandas import Timestamp
        entry = s['entry_time']
        exit_ = s['exit_time']
        if isinstance(entry, str):
            entry = Timestamp(entry)
        if isinstance(exit_, str):
            exit_ = Timestamp(exit_)
        return Trade(
            symbol=s['symbol'],
            entry_time=entry.to_pydatetime(),
            exit_time=exit_.to_pydatetime(),
            entry_price=s['entry_price'],
            exit_price=s['exit_price'],
            qty=s['qty'],
            direction=s['direction'],
            pnl=s['pnl'],
            trade_type=s['trade_type'],
            broker=s['broker']
        )
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Trade:
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    qty: float
    direction: str  # 'long' or 'short'
    pnl: float
    trade_type: str
    broker: str
    commission: Optional[float] = 0.0
    tags: Optional[str] = ""
    notes: Optional[str] = ""

    @property
    def duration(self) -> float:
        """Trade duration in minutes."""
        return (self.exit_time - self.entry_time).total_seconds() / 60

    @property
    def is_winner(self) -> bool:
        """Check if trade is profitable."""
        return self.pnl > 0

    @staticmethod
    def from_series(s: 'pd.Series') -> 'Trade':
        """Create Trade from pandas Series."""
        from pandas import Timestamp
        entry = s['entry_time']
        exit_ = s['exit_time']
        if isinstance(entry, str):
            entry = Timestamp(entry)
        if isinstance(exit_, str):
            exit_ = Timestamp(exit_)
        return Trade(
            symbol=s['symbol'],
            entry_time=entry.to_pydatetime(),
            exit_time=exit_.to_pydatetime(),
            entry_price=s['entry_price'],
            exit_price=s['exit_price'],
            qty=s['qty'],
            direction=s['direction'],
            pnl=s['pnl'],
            trade_type=s.get('trade_type', 'unknown'),
            broker=s.get('broker', 'unknown'),
            commission=s.get('commission', 0.0),
            tags=s.get('tags', ''),
            notes=s.get('notes', '')
        )

@dataclass
class AnalyticsMetrics:
    """Container for analytics calculations."""
    total_trades: int
    win_rate: float
    average_win: float
    average_loss: float
    reward_risk: float
    expectancy: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    total_pnl: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for easy serialization."""
        return {
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'average_win': self.average_win,
            'average_loss': self.average_loss,
            'reward_risk': self.reward_risk,
            'expectancy': self.expectancy,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'total_pnl': self.total_pnl
        }

@dataclass
class UserSession:
    """User session information."""
    user_id: int
    session_id: str
    partner_id: Optional[str]
    role: str
    created_at: datetime
    expires_at: datetime
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now() > self.expires_at
