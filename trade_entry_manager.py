
"""
Universal Trade Entry Manager
Handles all trade entry sources (manual, file, API) with unified analytics processing.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from models.trade_model import UniversalTradeDataModel, TradeRecord, TradeDirection, TradeType
from analytics import (
    compute_basic_stats,
    performance_over_time,
    calculate_kpis,
    median_results,
    profit_factor_by_symbol,
    trade_duration_stats,
    max_streaks,
    rolling_metrics
)

# Import centralized logging
try:
    from logging_manager import log_error, log_info, log_warning, LogCategory
    CENTRALIZED_LOGGING = True
except ImportError:
    import logging
    CENTRALIZED_LOGGING = False
    logger = logging.getLogger(__name__)


class TradeEntryManager:
    """Universal manager for all trade entry sources with unified analytics."""
    
    def __init__(self):
        self.model = UniversalTradeDataModel()
        self._analytics_cache = {}
        self._cache_dirty = True
    
    def add_manual_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a single manual trade entry."""
        try:
            # Normalize manual trade data to universal format
            normalized_trade = self._normalize_manual_trade(trade_data)
            
            # Create trade record
            trade_record = TradeRecord(**normalized_trade)
            
            # Add to model
            self.model.add_trade(trade_record)
            self._cache_dirty = True
            
            # Log the action
            if CENTRALIZED_LOGGING:
                log_info("Manual trade added successfully", 
                        details={"symbol": trade_data.get("symbol"), "pnl": trade_data.get("pnl")},
                        category=LogCategory.USER_ACTION)
            else:
                logger.info(f"Manual trade added: {trade_data.get('symbol')}")
            
            return {"status": "success", "trade_id": trade_record.trade_id}
            
        except Exception as e:
            error_msg = f"Failed to add manual trade: {str(e)}"
            if CENTRALIZED_LOGGING:
                log_error(error_msg, details={"trade_data": trade_data}, category=LogCategory.DATA_PROCESSING)
            else:
                logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def add_file_trades(self, df: pd.DataFrame, data_source: str = "file") -> Dict[str, Any]:
        """Add trades from file upload (CSV/Excel)."""
        try:
            # Convert DataFrame to universal model
            file_model = UniversalTradeDataModel()
            file_model = file_model.from_dataframe(df, data_source)
            
            # Validate data
            validation_report = file_model.validate_all()
            
            # Remove duplicates
            duplicates_removed = file_model.remove_duplicates()
            
            # Add valid trades to main model
            self.model.add_trades(file_model.trades)
            self._cache_dirty = True
            
            result = {
                "status": "success",
                "trades_added": len(file_model.trades),
                "duplicates_removed": duplicates_removed,
                "validation_report": validation_report
            }
            
            if CENTRALIZED_LOGGING:
                log_info("File trades imported", 
                        details=result, 
                        category=LogCategory.DATA_PROCESSING)
            else:
                logger.info(f"File trades imported: {len(file_model.trades)} trades")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to import file trades: {str(e)}"
            if CENTRALIZED_LOGGING:
                log_error(error_msg, details={"data_source": data_source}, category=LogCategory.DATA_PROCESSING)
            else:
                logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def add_api_trades(self, trades: List[Dict[str, Any]], connector_name: str) -> Dict[str, Any]:
        """Add trades from API connector."""
        try:
            api_trades = []
            
            for trade_data in trades:
                # Normalize API trade data
                normalized_trade = self._normalize_api_trade(trade_data, connector_name)
                trade_record = TradeRecord(**normalized_trade)
                api_trades.append(trade_record)
            
            # Add to model
            self.model.add_trades(api_trades)
            self._cache_dirty = True
            
            result = {
                "status": "success",
                "trades_added": len(api_trades),
                "connector": connector_name
            }
            
            if CENTRALIZED_LOGGING:
                log_info("API trades imported", details=result, category=LogCategory.DATA_PROCESSING)
            else:
                logger.info(f"API trades imported from {connector_name}: {len(api_trades)} trades")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to import API trades from {connector_name}: {str(e)}"
            if CENTRALIZED_LOGGING:
                log_error(error_msg, details={"connector": connector_name}, category=LogCategory.DATA_PROCESSING)
            else:
                logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def get_all_trades_dataframe(self) -> pd.DataFrame:
        """Get unified DataFrame of all trades from all sources."""
        return self.model.get_dataframe()
    
    def get_unified_analytics(self, fresh_calculation: bool = False) -> Dict[str, Any]:
        """Get comprehensive analytics for all trades regardless of source."""
        if not fresh_calculation and not self._cache_dirty and self._analytics_cache:
            return self._analytics_cache
        
        try:
            df = self.get_all_trades_dataframe()
            
            if df.empty:
                return self._empty_analytics()
            
            # Calculate all analytics using the same functions
            analytics = {
                "basic_stats": compute_basic_stats(df),
                "kpis": calculate_kpis(df),
                "performance_over_time": performance_over_time(df),
                "median_results": median_results(df),
                "profit_factor_by_symbol": profit_factor_by_symbol(df),
                "trade_duration_stats": trade_duration_stats(df),
                "max_streaks": max_streaks(df),
                "rolling_metrics": rolling_metrics(df),
                "trade_summary": {
                    "total_trades": len(df),
                    "data_sources": df['data_source'].value_counts().to_dict() if 'data_source' in df.columns else {},
                    "symbols_traded": df['symbol'].nunique() if 'symbol' in df.columns else 0,
                    "date_range": self._get_date_range(df)
                }
            }
            
            # Cache results
            self._analytics_cache = analytics
            self._cache_dirty = False
            
            return analytics
            
        except Exception as e:
            error_msg = f"Failed to calculate unified analytics: {str(e)}"
            if CENTRALIZED_LOGGING:
                log_error(error_msg, category=LogCategory.DATA_PROCESSING)
            else:
                logger.error(error_msg)
            return self._empty_analytics()
    
    def clear_all_trades(self) -> None:
        """Clear all trades from all sources."""
        self.model.clear()
        self._analytics_cache = {}
        self._cache_dirty = True
        
        if CENTRALIZED_LOGGING:
            log_info("All trades cleared", category=LogCategory.USER_ACTION)
        else:
            logger.info("All trades cleared")
    
    def get_trades_by_source(self, data_source: str) -> pd.DataFrame:
        """Get trades filtered by data source."""
        df = self.get_all_trades_dataframe()
        if df.empty or 'data_source' not in df.columns:
            return pd.DataFrame()
        return df[df['data_source'] == data_source]
    
    def remove_trades_by_source(self, data_source: str) -> int:
        """Remove all trades from a specific source."""
        initial_count = len(self.model.trades)
        self.model.trades = [t for t in self.model.trades if t.data_source != data_source]
        removed_count = initial_count - len(self.model.trades)
        
        if removed_count > 0:
            self._cache_dirty = True
            
        if CENTRALIZED_LOGGING:
            log_info(f"Removed {removed_count} trades from source {data_source}", 
                    category=LogCategory.USER_ACTION)
        else:
            logger.info(f"Removed {removed_count} trades from source {data_source}")
            
        return removed_count
    
    def _normalize_manual_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize manual trade entry to universal format."""
        now = datetime.now()
        
        return {
            "symbol": trade_data.get("symbol", "").strip().upper(),
            "entry_time": trade_data.get("entry_time", now),
            "exit_time": trade_data.get("exit_time", now),
            "entry_price": float(trade_data.get("entry_price", 0)),
            "exit_price": float(trade_data.get("exit_price", 0)),
            "qty": float(trade_data.get("trade_size", trade_data.get("qty", 1))),
            "direction": TradeDirection(trade_data.get("direction", "long").lower()),
            "pnl": float(trade_data.get("pnl", 0)),
            "trade_type": TradeType(trade_data.get("trade_type", "stocks").lower()),
            "broker": trade_data.get("broker", "Manual"),
            "notes": trade_data.get("notes", ""),
            "commission": trade_data.get("commission"),
            "stop_loss": trade_data.get("stop_loss"),
            "take_profit": trade_data.get("take_profit"),
            "tags": trade_data.get("tags", []) if isinstance(trade_data.get("tags"), list) else [],
            "data_source": "manual"
        }
    
    def _normalize_api_trade(self, trade_data: Dict[str, Any], connector_name: str) -> Dict[str, Any]:
        """Normalize API trade data to universal format."""
        return {
            "symbol": trade_data.get("symbol", "").strip().upper(),
            "entry_time": pd.to_datetime(trade_data.get("entry_time")),
            "exit_time": pd.to_datetime(trade_data.get("exit_time")),
            "entry_price": float(trade_data.get("entry_price", 0)),
            "exit_price": float(trade_data.get("exit_price", 0)),
            "qty": float(trade_data.get("qty", 1)),
            "direction": TradeDirection(trade_data.get("direction", "long").lower()),
            "pnl": float(trade_data.get("pnl", 0)),
            "trade_type": TradeType(trade_data.get("trade_type", "stocks").lower()),
            "broker": trade_data.get("broker", connector_name),
            "notes": trade_data.get("notes", ""),
            "commission": trade_data.get("commission"),
            "stop_loss": trade_data.get("stop_loss"),
            "take_profit": trade_data.get("take_profit"),
            "tags": trade_data.get("tags", []) if isinstance(trade_data.get("tags"), list) else [],
            "data_source": f"api_{connector_name}"
        }
    
    def _get_date_range(self, df: pd.DataFrame) -> Dict[str, str]:
        """Get date range of all trades."""
        if df.empty or 'exit_time' not in df.columns:
            return {"start": "N/A", "end": "N/A"}
        
        try:
            dates = pd.to_datetime(df['exit_time'], errors='coerce').dropna()
            if dates.empty:
                return {"start": "N/A", "end": "N/A"}
            
            return {
                "start": dates.min().strftime("%Y-%m-%d"),
                "end": dates.max().strftime("%Y-%m-%d")
            }
        except Exception:
            return {"start": "N/A", "end": "N/A"}
    
    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure."""
        return {
            "basic_stats": {},
            "kpis": {},
            "performance_over_time": pd.DataFrame(),
            "median_results": {},
            "profit_factor_by_symbol": pd.DataFrame(),
            "trade_duration_stats": {},
            "max_streaks": {},
            "rolling_metrics": pd.DataFrame(),
            "trade_summary": {
                "total_trades": 0,
                "data_sources": {},
                "symbols_traded": 0,
                "date_range": {"start": "N/A", "end": "N/A"}
            }
        }

# Global instance for the application
trade_manager = TradeEntryManager()
