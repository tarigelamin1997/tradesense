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
    account: str = ""

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
            broker=s['broker'],
            account=s.get('account', '')
        )
