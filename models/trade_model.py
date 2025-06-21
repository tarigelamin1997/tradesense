
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import pandas as pd
from enum import Enum

class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"

class TradeType(Enum):
    FUTURES = "futures"
    STOCKS = "stocks"
    OPTIONS = "options"
    FOREX = "forex"
    CRYPTO = "crypto"

@dataclass
class TradeRecord:
    """Universal trade record with strict typing and validation."""
    
    # Required fields
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    qty: float
    direction: TradeDirection
    pnl: float
    trade_type: TradeType
    broker: str
    
    # Optional fields
    notes: Optional[str] = None
    commission: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    tags: Optional[List[str]] = field(default_factory=list)
    
    # Enhanced analytics fields
    strategy_tag: Optional[str] = None
    setup_tag: Optional[str] = None
    execution_type: str = "manual"  # manual/auto
    confidence_score: Optional[int] = None  # 1-10 scale
    gross_pnl: Optional[float] = None
    net_pnl: Optional[float] = None
    
    # Metadata fields
    data_source: str = "manual"
    import_timestamp: datetime = field(default_factory=datetime.now)
    trade_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        self.validate()
        self.normalize()
    
    def validate(self) -> None:
        """Comprehensive validation of trade data."""
        errors = []
        
        # Required field validation
        if not self.symbol or not isinstance(self.symbol, str):
            errors.append("Symbol must be a non-empty string")
        
        if not isinstance(self.entry_time, datetime):
            errors.append("Entry time must be a datetime object")
        
        if not isinstance(self.exit_time, datetime):
            errors.append("Exit time must be a datetime object")
        
        if self.entry_time >= self.exit_time:
            errors.append("Exit time must be after entry time")
        
        # Price validation
        if not isinstance(self.entry_price, (int, float)) or self.entry_price <= 0:
            errors.append("Entry price must be a positive number")
        
        if not isinstance(self.exit_price, (int, float)) or self.exit_price <= 0:
            errors.append("Exit price must be a positive number")
        
        # Quantity validation
        if not isinstance(self.qty, (int, float)) or self.qty <= 0:
            errors.append("Quantity must be a positive number")
        
        # PnL validation
        if not isinstance(self.pnl, (int, float)):
            errors.append("PnL must be a number")
        
        # Optional field validation
        if self.commission is not None and (not isinstance(self.commission, (int, float)) or self.commission < 0):
            errors.append("Commission must be a non-negative number")
        
        if self.stop_loss is not None and (not isinstance(self.stop_loss, (int, float)) or self.stop_loss <= 0):
            errors.append("Stop loss must be a positive number")
        
        if self.take_profit is not None and (not isinstance(self.take_profit, (int, float)) or self.take_profit <= 0):
            errors.append("Take profit must be a positive number")
        
        # Enhanced field validation
        if self.confidence_score is not None and (not isinstance(self.confidence_score, int) or not 1 <= self.confidence_score <= 10):
            errors.append("Confidence score must be an integer between 1 and 10")
        
        if self.gross_pnl is not None and not isinstance(self.gross_pnl, (int, float)):
            errors.append("Gross P&L must be a number")
        
        if self.net_pnl is not None and not isinstance(self.net_pnl, (int, float)):
            errors.append("Net P&L must be a number")
        
        if self.execution_type not in ['manual', 'auto']:
            errors.append("Execution type must be 'manual' or 'auto'")
        
        if errors:
            raise ValueError(f"Trade validation failed: {'; '.join(errors)}")
    
    def normalize(self) -> None:
        """Normalize and clean data."""
        # Normalize symbol to uppercase
        self.symbol = self.symbol.strip().upper()
        
        # Normalize broker name
        self.broker = self.broker.strip().title()
        
        # Ensure direction and trade_type are proper enums
        if isinstance(self.direction, str):
            self.direction = TradeDirection(self.direction.lower())
        
        if isinstance(self.trade_type, str):
            self.trade_type = TradeType(self.trade_type.lower())
        
        # Generate trade_id if not provided
        if not self.trade_id:
            self.trade_id = self.generate_trade_id()
        
        # Clean notes
        if self.notes:
            self.notes = self.notes.strip()
    
    def generate_trade_id(self) -> str:
        """Generate unique trade identifier."""
        timestamp = int(self.entry_time.timestamp())
        return f"{self.symbol}_{timestamp}_{self.entry_price}_{self.exit_price}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DataFrame creation."""
        return {
            'symbol': self.symbol,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'qty': self.qty,
            'direction': self.direction.value,
            'pnl': self.pnl,
            'trade_type': self.trade_type.value,
            'broker': self.broker,
            'notes': self.notes,
            'commission': self.commission,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'tags': ','.join(self.tags) if self.tags else '',
            'strategy_tag': self.strategy_tag,
            'setup_tag': self.setup_tag,
            'execution_type': self.execution_type,
            'confidence_score': self.confidence_score,
            'gross_pnl': self.gross_pnl,
            'net_pnl': self.net_pnl,
            'data_source': self.data_source,
            'import_timestamp': self.import_timestamp,
            'trade_id': self.trade_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradeRecord':
        """Create TradeRecord from dictionary."""
        # Get expected fields from the class
        expected_fields = {field.name for field in cls.__dataclass_fields__.values()}
        
        # Filter data to only include expected fields
        filtered_data = {k: v for k, v in data.items() if k in expected_fields}
        
        # Handle enum conversion
        if isinstance(filtered_data.get('direction'), str):
            filtered_data['direction'] = TradeDirection(filtered_data['direction'].lower())
        
        if isinstance(filtered_data.get('trade_type'), str):
            filtered_data['trade_type'] = TradeType(filtered_data['trade_type'].lower())
        
        # Handle datetime conversion
        for time_field in ['entry_time', 'exit_time', 'import_timestamp']:
            if time_field in filtered_data and isinstance(filtered_data[time_field], str):
                filtered_data[time_field] = pd.to_datetime(filtered_data[time_field])
        
        # Handle tags conversion
        if 'tags' in filtered_data and isinstance(filtered_data['tags'], str):
            filtered_data['tags'] = [tag.strip() for tag in filtered_data['tags'].split(',') if tag.strip()]
        
        return cls(**filtered_data)

class UniversalTradeDataModel:
    """Universal data model for managing trade records from all sources."""
    
    def __init__(self):
        self.trades: List[TradeRecord] = []
        self._df_cache: Optional[pd.DataFrame] = None
        self._cache_dirty = True
    
    def add_trade(self, trade: TradeRecord) -> None:
        """Add a single trade record."""
        self.trades.append(trade)
        self._cache_dirty = True
    
    def add_trades(self, trades: List[TradeRecord]) -> None:
        """Add multiple trade records."""
        self.trades.extend(trades)
        self._cache_dirty = True
    
    def get_dataframe(self) -> pd.DataFrame:
        """Get pandas DataFrame representation."""
        if self._cache_dirty or self._df_cache is None:
            if not self.trades:
                # Return empty DataFrame with correct schema
                return pd.DataFrame(columns=self.get_schema_columns())
            
            data = [trade.to_dict() for trade in self.trades]
            self._df_cache = pd.DataFrame(data)
            self._cache_dirty = False
        
        return self._df_cache.copy()
    
    def clear(self) -> None:
        """Clear all trades."""
        self.trades.clear()
        self._cache_dirty = True
    
    def remove_duplicates(self) -> int:
        """Remove duplicate trades based on trade_id."""
        seen_ids = set()
        unique_trades = []
        
        for trade in self.trades:
            if trade.trade_id not in seen_ids:
                unique_trades.append(trade)
                seen_ids.add(trade.trade_id)
        
        removed_count = len(self.trades) - len(unique_trades)
        self.trades = unique_trades
        self._cache_dirty = True
        
        return removed_count
    
    def validate_all(self) -> Dict[str, Any]:
        """Validate all trades and return quality report."""
        report = {
            'total_trades': len(self.trades),
            'valid_trades': 0,
            'errors': [],
            'warnings': []
        }
        
        valid_trades = []
        for i, trade in enumerate(self.trades):
            try:
                trade.validate()
                valid_trades.append(trade)
            except ValueError as e:
                report['errors'].append(f"Trade {i}: {str(e)}")
        
        report['valid_trades'] = len(valid_trades)
        self.trades = valid_trades
        self._cache_dirty = True
        
        return report
    
    @staticmethod
    def get_schema_columns() -> List[str]:
        """Get standard schema column names."""
        return [
            'symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price',
            'qty', 'direction', 'pnl', 'trade_type', 'broker', 'notes',
            'commission', 'stop_loss', 'take_profit', 'tags', 'data_source',
            'import_timestamp', 'trade_id'
        ]
    
    def get_required_columns(self) -> List[str]:
        """Get required column names for validation."""
        return [
            'symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price',
            'qty', 'direction', 'pnl', 'trade_type', 'broker'
        ]
    
    def from_dataframe(self, df: pd.DataFrame, data_source: str = "import") -> 'UniversalTradeDataModel':
        """Create model from pandas DataFrame."""
        trades = []
        
        for _, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                row_dict['data_source'] = data_source
                
                # Handle NaN values
                for key, value in row_dict.items():
                    if pd.isna(value):
                        row_dict[key] = None
                
                trade = TradeRecord.from_dict(row_dict)
                trades.append(trade)
            except Exception as e:
                print(f"Skipping invalid row: {e}")
                continue
        
        model = UniversalTradeDataModel()
        model.add_trades(trades)
        return model
