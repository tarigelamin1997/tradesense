"""
Universal Trade Entry Manager
Handles all trade entry sources (manual, file, API) with unified analytics processing.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from models.trade_model import UniversalTradeDataModel, TradeRecord, TradeDirection, TradeType
from deduplication_manager import dedup_manager
from analytics import (
    compute_basic_stats, calculate_kpis, performance_over_time,
    median_results, profit_factor_by_symbol, trade_duration_stats,
    max_streaks, rolling_metrics
)
import numpy as np

# Import centralized logging
try:
    from logging_manager import log_error, log_info, log_warning, LogCategory
    CENTRALIZED_LOGGING = True
except ImportError:
    import logging
    CENTRALIZED_LOGGING = False
    logger = logging.getLogger(__name__)

# Module imports - let them fail naturally if not available
# Don't check availability here as it causes premature warnings


class TradeEntryManager:
    """Universal manager for all trade entry sources with unified analytics."""

    def __init__(self):
        self.model = UniversalTradeDataModel()
        self._analytics_cache = {}
        self._cache_dirty = True

    def add_manual_trade(self, trade_data: Dict[str, Any], user_id: int = None) -> Dict[str, Any]:
        """Add a single manual trade entry with deduplication."""
        try:
            # Normalize manual trade data to universal format
            normalized_trade = self._normalize_manual_trade(trade_data)

            # Perform deduplication check if user_id provided
            if user_id:
                dedup_results = dedup_manager.deduplicate_trades([normalized_trade], user_id, auto_resolve=True)

                if dedup_results['duplicates_removed'] > 0:
                    duplicate_info = dedup_results['duplicates_found'][0]
                    return {
                        "status": "duplicate",
                        "message": "Trade appears to be a duplicate",
                        "duplicate_info": duplicate_info,
                        "existing_trade_id": duplicate_info.get("existing_trade_id")
                    }

                if dedup_results['conflicts_requiring_review']:
                    conflict = dedup_results['conflicts_requiring_review'][0]
                    return {
                        "status": "needs_review",
                        "message": "Potential duplicate found - manual review required",
                        "potential_matches": conflict['potential_matches']
                    }

                # Use deduplicated trade data
                if dedup_results['unique_trades']:
                    normalized_trade = dedup_results['unique_trades'][0]

            # Create trade record
            trade_record = TradeRecord(**normalized_trade)

            # Add to model
            self.model.add_trade(trade_record)
            self._cache_dirty = True

            # Register trade fingerprint for future deduplication
            if user_id:
                dedup_manager.register_trades([trade_record], user_id)

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

    def add_file_trades(self, df: pd.DataFrame, data_source: str = "file", user_id: int = None) -> Dict[str, Any]:
        """Add trades from file upload (CSV/Excel) with deduplication."""
        try:
            # Validate and clean data first
            from data_validation import DataValidator
            validator = DataValidator()
            df_cleaned, validation_report = validator.validate_and_clean_data(df, interactive=False)

            # Convert DataFrame to universal model
            file_model = UniversalTradeDataModel()
            file_model = file_model.from_dataframe(df_cleaned, data_source)

            # Validate data
            model_validation_report = file_model.validate_all()

            # Remove duplicates within the file
            internal_duplicates_removed = file_model.remove_duplicates()

            # Perform cross-source deduplication if user_id provided
            dedup_report = None
            if user_id and file_model.trades:
                trades_data = [trade.to_dict() for trade in file_model.trades]
                dedup_results = dedup_manager.deduplicate_trades(trades_data, user_id, auto_resolve=True)

                # Create new model with only unique trades
                unique_model = UniversalTradeDataModel()
                for trade_dict in dedup_results['unique_trades']:
                    # Remove dedup review flag if present
                    trade_dict.pop('_requires_dedup_review', None)
                    trade_record = TradeRecord.from_dict(trade_dict)
                    unique_model.add_trade(trade_record)

                file_model = unique_model
                dedup_report = dedup_results

            # Add valid trades to main model
            self.model.add_trades(file_model.trades)
            self._cache_dirty = True

            # Register trade fingerprints for future deduplication
            if user_id and file_model.trades:
                dedup_manager.register_trades(file_model.trades, user_id)

            result = {
                "status": "success",
                "trades_added": len(file_model.trades),
                "internal_duplicates_removed": internal_duplicates_removed,
                "validation_report": validation_report,
                "model_validation_report": model_validation_report
            }

            # Add deduplication results if performed
            if dedup_report:
                result.update({
                    "cross_source_duplicates_removed": dedup_report['duplicates_removed'],
                    "conflicts_requiring_review": len(dedup_report['conflicts_requiring_review']),
                    "deduplication_summary": {
                        "original_count": dedup_report['original_count'],
                        "final_count": len(dedup_report['unique_trades']),
                        "duplicates_found": len(dedup_report['duplicates_found'])
                    }
                })

            if CENTRALIZED_LOGGING:
                log_info("File trades imported with deduplication", 
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

    def add_api_trades(self, trades: List[Dict[str, Any]], connector_name: str, user_id: int = None) -> Dict[str, Any]:
        """Add trades from API connector with deduplication."""
        try:
            # Normalize API trade data
            normalized_trades = []
            for trade_data in trades:
                normalized_trade = self._normalize_api_trade(trade_data, connector_name)
                normalized_trades.append(normalized_trade)

            # Perform deduplication if user_id provided
            dedup_report = None
            if user_id and normalized_trades:
                dedup_results = dedup_manager.deduplicate_trades(normalized_trades, user_id, auto_resolve=True)
                unique_trades_data = dedup_results['unique_trades']
                dedup_report = dedup_results
            else:
                unique_trades_data = normalized_trades

            # Create trade records from unique data
            api_trades = []
            for trade_dict in unique_trades_data:
                # Remove dedup review flag if present
                trade_dict.pop('_requires_dedup_review', None)
                trade_record = TradeRecord(**trade_dict)
                api_trades.append(trade_record)

            # Add to model
            self.model.add_trades(api_trades)
            self._cache_dirty = True

            # Register trade fingerprints for future deduplication
            if user_id and api_trades:
                dedup_manager.register_trades(api_trades, user_id)

            result = {
                "status": "success",
                "trades_added": len(api_trades),
                "connector": connector_name
            }

            # Add deduplication results if performed
            if dedup_report:
                result.update({
                    "duplicates_removed": dedup_report['duplicates_removed'],
                    "conflicts_requiring_review": len(dedup_report['conflicts_requiring_review']),
                    "deduplication_summary": {
                        "original_count": dedup_report['original_count'],
                        "final_count": len(dedup_report['unique_trades']),
                        "duplicates_found": len(dedup_report['duplicates_found'])
                    }
                })

            if CENTRALIZED_LOGGING:
                log_info("API trades imported with deduplication", details=result, category=LogCategory.DATA_PROCESSING)
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

    def get_unified_dataframe(self) -> pd.DataFrame:
        """Alias for get_all_trades_dataframe for compatibility."""
        return self.get_all_trades_dataframe()

    def get_unified_analytics(self, fresh_calculation: bool = False) -> Dict[str, Any]:
        """Get comprehensive analytics for all trades regardless of source."""
        if not fresh_calculation and not self._cache_dirty and self._analytics_cache:
            return self._analytics_cache

        try:
            df = self.get_all_trades_dataframe()

            if df.empty:
                return self._empty_analytics()

            # Validate required columns exist
            required_cols = ['pnl']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                error_msg = f"Missing required columns for analytics: {missing_cols}"
                if CENTRALIZED_LOGGING:
                    log_error(error_msg, category=LogCategory.DATA_PROCESSING)
                else:
                    logger.error(error_msg)
                return self._empty_analytics()

            # Clean data before analytics
            df_clean = df.copy()
            df_clean['pnl'] = pd.to_numeric(df_clean['pnl'], errors='coerce')
            df_clean = df_clean.dropna(subset=['pnl'])
            df_clean = df_clean[np.isfinite(df_clean['pnl'])]

            if df_clean.empty:
                logger.warning("No valid data after cleaning for analytics")
                return self._empty_analytics()

            # Calculate all analytics using the same functions
            analytics = {
                "basic_stats": compute_basic_stats(df_clean),
                "kpis": calculate_kpis(df_clean),
                "performance_over_time": performance_over_time(df_clean),
                "median_results": median_results(df_clean),
                "profit_factor_by_symbol": profit_factor_by_symbol(df_clean),
                "trade_duration_stats": trade_duration_stats(df_clean),
                "max_streaks": max_streaks(df_clean),
                "rolling_metrics": rolling_metrics(df_clean),
                "trade_summary": {
                    "total_trades": len(df_clean),
                    "data_sources": df_clean['data_source'].value_counts().to_dict() if 'data_source' in df_clean.columns else {},
                    "symbols_traded": df_clean['symbol'].nunique() if 'symbol' in df_clean.columns else 0,
                    "date_range": self._get_date_range(df_clean)
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
            "basic_stats": {
                'total_trades': 0,
                'win_rate': 0,
                'average_win': 0,
                'average_loss': 0,
                'reward_risk': 0,
                'expectancy': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'equity_curve': pd.Series()
            },
            "kpis": {
                'total_trades': 0,
                'gross_pnl': 0,
                'total_commission': 0,
                'net_pnl_after_commission': 0,
                'win_rate_percent': 0,
                'max_single_trade_win': 0,
                'max_single_trade_loss': 0,
                'average_rr': 0
            },
            "performance_over_time": pd.DataFrame(),
            "median_results": {
                'median_pnl': 0,
                'median_win': 0,
                'median_loss': 0
            },
            "profit_factor_by_symbol": pd.DataFrame(),
            "trade_duration_stats": {
                'average_minutes': 0,
                'min_minutes': 0,
                'max_minutes': 0,
                'median_minutes': 0
            },
            "max_streaks": {
                'max_win_streak': 0,
                'max_loss_streak': 0
            },
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