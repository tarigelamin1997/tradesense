import pandas as pd
import numpy as np
import streamlit as st
import logging
from datetime import datetime

# Configure logging for analytics
logging.basicConfig(
    filename='analytics.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)
logger = logging.getLogger(__name__)

def log_debug_info(context: str, data):
    """Log debug information to file instead of UI."""
    logger.debug(f"{context}: {data}")

def format_currency(value, default="–"):
    """Format currency values with $ and 2 decimal places."""
    try:
        if pd.isna(value) or not np.isfinite(value):
            return default
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return default

def format_percentage(value, default="–"):
    """Format percentage values with % and 1 decimal place."""
    try:
        if pd.isna(value) or not np.isfinite(value):
            return default
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return default

def format_number(value, decimals=2, default="–"):
    """Format general numbers with specified decimal places."""
    try:
        if pd.isna(value) or not np.isfinite(value):
            return default
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return default

@st.cache_data
def compute_basic_stats(df: pd.DataFrame) -> dict:
    """Compute basic trading statistics efficiently."""
    logger.info("Starting compute_basic_stats")

    default_stats = {
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "max_drawdown": 0.0,
        "sharpe_ratio": 0.0,
        "average_win": 0.0,
        "average_loss": 0.0,
        "reward_risk": 0.0,
        "equity_curve": pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))
    }

    try:
        if df.empty:
            logger.warning("Empty DataFrame provided to compute_basic_stats")
            return default_stats

        # Clean PnL data
        df = clean_numeric_data(df, 'pnl')
        if df.empty:
            logger.warning("No valid PnL data after cleaning")
            return default_stats

        log_debug_info("DataFrame shape after cleaning", df.shape)
        log_debug_info("PnL column dtype", df['pnl'].dtype)

        # Calculate basic metrics
        total_trades = len(df)
        wins = df[df["pnl"] > 0]
        losses = df[df["pnl"] <= 0]

        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0

        # Safe average calculations
        avg_win = float(wins["pnl"].mean()) if not wins.empty else 0.0
        avg_loss = float(losses["pnl"].mean()) if not losses.empty else 0.0

        # Ensure finite values
        avg_win = avg_win if np.isfinite(avg_win) else 0.0
        avg_loss = avg_loss if np.isfinite(avg_loss) else 0.0

        log_debug_info("Average win", avg_win)
        log_debug_info("Average loss", avg_loss)

        # Calculate reward/risk ratio
        reward_risk = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
        reward_risk = min(reward_risk, 999.99) if np.isfinite(reward_risk) else 0.0

        # Calculate expectancy
        expectancy = (win_rate / 100) * avg_win + (1 - win_rate / 100) * avg_loss
        expectancy = expectancy if np.isfinite(expectancy) else 0.0

        # Calculate profit factor
        wins_sum = float(wins["pnl"].sum()) if not wins.empty else 0.0
        losses_sum = float(abs(losses["pnl"].sum())) if not losses.empty else 0.0

        if losses_sum != 0 and np.isfinite(losses_sum) and np.isfinite(wins_sum):
            profit_factor = min(wins_sum / losses_sum, 999.99)
        else:
            profit_factor = 0.0 if wins_sum == 0 else 999.99

        # Create equity curve
        try:
            if 'exit_time' in df.columns:
                df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
                df = df.dropna(subset=['exit_time'])
                if not df.empty:
                    df_sorted = df.sort_values('exit_time')
                    equity_curve = df_sorted['pnl'].cumsum()
                    equity_curve.index = df_sorted['exit_time']
                    equity_curve = equity_curve[np.isfinite(equity_curve)]
                else:
                    equity_curve = pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))
            else:
                equity_curve = df['pnl'].cumsum()
                equity_curve = equity_curve[np.isfinite(equity_curve)]

            # Ensure minimum 2 points
            if len(equity_curve) < 2:
                equity_curve = pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))

        except Exception as e:
            logger.error(f"Error creating equity curve: {str(e)}")
            equity_curve = pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))

        # Calculate max drawdown
        try:
            if len(equity_curve) > 1:
                drawdown = equity_curve.cummax() - equity_curve
                max_drawdown = float(drawdown.max()) if not drawdown.empty else 0.0
                max_drawdown = max_drawdown if np.isfinite(max_drawdown) else 0.0
            else:
                max_drawdown = 0.0
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {str(e)}")
            max_drawdown = 0.0

        # Calculate Sharpe ratio
        try:
            if len(equity_curve) > 1:
                returns = equity_curve.pct_change().dropna()
                returns = returns[np.isfinite(returns)]
                if not returns.empty and returns.std() != 0:
                    sharpe = float(np.sqrt(252) * returns.mean() / returns.std())
                    sharpe = max(min(sharpe, 10.0), -10.0) if np.isfinite(sharpe) else 0.0
                else:
                    sharpe = 0.0
            else:
                sharpe = 0.0
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {str(e)}")
            sharpe = 0.0

        result = {
            "win_rate": win_rate,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "reward_risk": reward_risk,
            "expectancy": expectancy,
            "max_drawdown": max_drawdown,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "equity_curve": equity_curve,
        }

        logger.info("Successfully computed basic stats")
        log_debug_info("Final stats", result)
        return result

    except Exception as e:
        logger.error(f"Error in compute_basic_stats: {str(e)}")
        return default_stats


def clean_numeric_data(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Clean numeric data by removing infinite and NaN values."""
    if df.empty or column not in df.columns:
        return df

    df = df.copy()
    df[column] = pd.to_numeric(df[column], errors='coerce')
    df = df.dropna(subset=[column])
    df = df[np.isfinite(df[column])]

    log_debug_info(f"Cleaned {column} column", f"Rows remaining: {len(df)}")
    return df


def ensure_chart_ready_data(df: pd.DataFrame, min_rows: int = 2) -> bool:
    """Ensure data is ready for charting without verbose output."""
    if df.empty or len(df) < min_rows:
        return False

    # Check numeric columns for infinite/NaN values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if np.isinf(df[col]).any() or df[col].isna().any():
            return False

    return True


def performance_over_time(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """Return P&L and win rate aggregated by period efficiently."""
    logger.info(f"Computing performance over time with frequency: {freq}")

    default_date = pd.Timestamp.now().normalize()
    default_result = pd.DataFrame({
        "period": [default_date, default_date + pd.Timedelta(days=1)], 
        "pnl": [0.0, 0.0], 
        "win_rate": [0.0, 0.0]
    })

    try:
        if df.empty:
            logger.warning("Empty DataFrame provided to performance_over_time")
            return default_result

        # Clean data
        df = clean_numeric_data(df, 'pnl')
        if df.empty:
            logger.warning("No valid PnL data for performance over time")
            return default_result

        # Convert exit_time
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
        df = df.dropna(subset=["exit_time"])

        if df.empty:
            logger.warning("No valid exit_time data for performance over time")
            return default_result

        # Group by period
        period = df["exit_time"].dt.to_period(freq).dt.to_timestamp()
        grouped = df.groupby(period)

        # Calculate aggregated values
        pnl = grouped["pnl"].sum().fillna(0.0)
        win_rate = grouped.apply(lambda g: float((g["pnl"] > 0).mean() * 100), include_groups=False).fillna(0.0)

        # Ensure finite values only
        pnl_values = [float(x) if np.isfinite(x) else 0.0 for x in pnl.values]
        wr_values = [float(x) if np.isfinite(x) else 0.0 for x in win_rate.values]

        result = pd.DataFrame({
            "period": pnl.index, 
            "pnl": pnl_values, 
            "win_rate": wr_values
        })

        # Ensure minimum data points
        if len(result) < 2 and len(result) == 1:
            dummy_row = result.iloc[0:1].copy()
            dummy_row['period'] = dummy_row['period'] + pd.Timedelta(days=1)
            result = pd.concat([result, dummy_row], ignore_index=True)
        elif len(result) == 0:
            result = default_result

        logger.info(f"Performance over time computed successfully with {len(result)} periods")
        return result

    except Exception as e:
        logger.error(f"Error in performance_over_time: {str(e)}")
        return default_result


def median_results(df: pd.DataFrame) -> dict:
    """Return median PnL statistics efficiently."""
    logger.info("Computing median results")

    try:
        df = clean_numeric_data(df, 'pnl')
        if df.empty:
            logger.warning("No valid PnL data for median results")
            return {"median_pnl": 0.0, "median_win": 0.0, "median_loss": 0.0}

        wins = df[df["pnl"] > 0]
        losses = df[df["pnl"] <= 0]

        median_pnl = float(df["pnl"].median()) if not df.empty else 0.0
        median_win = float(wins["pnl"].median()) if not wins.empty else 0.0
        median_loss = float(losses["pnl"].median()) if not losses.empty else 0.0

        # Ensure finite values
        result = {
            "median_pnl": median_pnl if np.isfinite(median_pnl) else 0.0,
            "median_win": median_win if np.isfinite(median_win) else 0.0,
            "median_loss": median_loss if np.isfinite(median_loss) else 0.0,
        }

        logger.info("Median results computed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in median_results: {str(e)}")
        return {"median_pnl": 0.0, "median_win": 0.0, "median_loss": 0.0}


def profit_factor_by_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate profit factor for each trading symbol."""
    logger.info("Computing profit factor by symbol")

    try:
        if df.empty:
            logger.warning("Empty DataFrame provided to profit_factor_by_symbol")
            return pd.DataFrame({
                "symbol": ["No Data"],
                "profit_factor": [0.0]
            })

        # Force numeric conversion
        df = clean_numeric_data(df, 'pnl')
        df = df.dropna(subset=["symbol"])

        if df.empty:
            logger.warning("No valid data after cleaning for profit factor by symbol")
            return pd.DataFrame({
                "symbol": ["No Data"],
                "profit_factor": [0.0]
            })

        def _pf(group: pd.DataFrame) -> float:
            try:
                wins = group[group["pnl"] > 0]["pnl"].sum()
                losses = group[group["pnl"] <= 0]["pnl"].sum()

                wins = wins if np.isfinite(wins) else 0.0
                losses = losses if np.isfinite(losses) else 0.0

                if losses != 0:
                    pf = wins / abs(losses)
                    result = min(pf, 999.99) if np.isfinite(pf) else 0.0
                else:
                    result = 999.99 if wins > 0 else 0.0

                return result
            except Exception as e:
                logger.error(f"Error computing PF for group: {str(e)}")
                return 0.0

        result = (
            df.groupby("symbol")
            .apply(_pf, include_groups=False)
            .reset_index(name="profit_factor")
            .sort_values("symbol")
        )

        logger.info(f"Profit factor by symbol computed for {len(result)} symbols")
        return result

    except Exception as e:
        logger.error(f"Error in profit_factor_by_symbol: {str(e)}")
        return pd.DataFrame({
            "symbol": ["Error"],
            "profit_factor": [0.0]
        })


def trade_duration_stats(df: pd.DataFrame) -> dict:
    """Calculate statistics on trade durations in minutes."""
    logger.info("Computing trade duration stats")

    try:
        if df.empty:
            logger.warning("Empty DataFrame provided to trade_duration_stats")
            return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}

        df = df.copy()
        df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
        df = df.dropna(subset=["entry_time", "exit_time"])

        if df.empty:
            logger.warning("No valid time data for trade duration stats")
            return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}

        durations = (df["exit_time"] - df["entry_time"]).dt.total_seconds() / 60
        durations = durations[np.isfinite(durations)]  # Remove infinite values

        if durations.empty:
            logger.warning("No valid duration data for trade duration stats")
            return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}

        result = {
            "average_minutes": float(durations.mean()) if not durations.empty else 0,
            "max_minutes": float(durations.max()) if not durations.empty else 0,
            "min_minutes": float(durations.min()) if not durations.empty else 0,
            "median_minutes": float(durations.median()) if not durations.empty else 0,
        }

        logger.info("Trade duration stats computed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in trade_duration_stats: {str(e)}")
        return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}


def max_streaks(df: pd.DataFrame) -> dict:
    """Return the longest consecutive win and loss streaks."""
    logger.info("Computing max streaks")

    try:
        df = clean_numeric_data(df, 'pnl')

        if df.empty:
            logger.warning("No valid PnL data for max streaks")
            return {"max_win_streak": 0, "max_loss_streak": 0}

        max_win = 0
        max_loss = 0
        current_win = 0
        current_loss = 0

        for i, pnl in enumerate(df["pnl"]):
            if not np.isfinite(pnl):
                continue

            if pnl > 0:
                current_win += 1
                current_loss = 0
            else:
                current_loss += 1
                current_win = 0
            max_win = max(max_win, current_win)
            max_loss = max(max_loss, current_loss)

        result = {"max_win_streak": max_win, "max_loss_streak": max_loss}
        logger.info(f"Max streaks computed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in max_streaks: {str(e)}")
        return {"max_win_streak": 0, "max_loss_streak": 0}


def rolling_metrics(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Compute rolling win rate and profit factor efficiently."""
    logger.info(f"Computing rolling metrics with window: {window}")

    default_result = pd.DataFrame({
        "end_index": [0.0, 1.0],
        "win_rate": [0.0, 0.0],
        "profit_factor": [0.0, 0.0]
    })

    try:
        df = clean_numeric_data(df, 'pnl')
        if df.empty or len(df) < window:
            logger.warning(f"Insufficient data for rolling metrics (need {window}, have {len(df)})")
            return default_result

        results = []

        for end in range(window, len(df) + 1):
            try:
                window_df = df.iloc[end - window : end]
                stats = compute_basic_stats(window_df)

                # Ensure finite values only
                win_rate = stats["win_rate"] if np.isfinite(stats["win_rate"]) else 0.0
                profit_factor = stats["profit_factor"] if np.isfinite(stats["profit_factor"]) else 0.0

                results.append({
                    "end_index": float(end - 1),
                    "win_rate": win_rate,
                    "profit_factor": profit_factor,
                })
            except Exception:
                continue

        if not results:
            logger.warning("No valid rolling metrics computed")
            return default_result

        result_df = pd.DataFrame(results)

        # Ensure minimum data points
        if len(result_df) < 2 and len(result_df) == 1:
            dummy_row = result_df.iloc[0:1].copy()
            dummy_row['end_index'] = dummy_row['end_index'] + 1
            result_df = pd.concat([result_df, dummy_row], ignore_index=True)
        elif len(result_df) == 0:
            result_df = default_result

        logger.info(f"Rolling metrics computed for {len(result_df)} windows")
        return result_df

    except Exception as e:
        logger.error(f"Error in rolling_metrics: {str(e)}")
        return default_result


def calculate_kpis(df: pd.DataFrame, commission_per_trade: float = 3.5) -> dict:
    """Calculate key performance indicators including commission costs."""
    logger.info("Computing KPIs")

    try:
        df = clean_numeric_data(df, 'pnl')

        if df.empty:
            logger.warning("No valid PnL data for KPIs")
            return {
                "total_trades": 0,
                "win_rate_percent": 0,
                "average_rr": 0,
                "net_pnl_after_commission": 0,
                "max_single_trade_loss": 0,
                "max_single_trade_win": 0,
                "total_commission": 0,
                "gross_pnl": 0
            }

        # Total number of trades
        total_trades = len(df)

        # Total commission
        total_commission = total_trades * commission_per_trade

        # Net PnL after commission
        gross_pnl = float(df["pnl"].sum()) if not df.empty else 0.0
        gross_pnl = gross_pnl if np.isfinite(gross_pnl) else 0.0
        net_pnl_after_commission = gross_pnl - total_commission

        # Win rate %
        winning_trades = df[df["pnl"] > 0]
        losing_trades = df[df["pnl"] <= 0]
        win_rate_percent = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0

        # Average RR (Reward to Risk ratio)
        avg_win = 0
        avg_loss = 0

        if not winning_trades.empty:
            avg_win = float(winning_trades["pnl"].mean())

        if not losing_trades.empty:
            avg_loss = float(abs(losing_trades["pnl"].mean()))

        avg_win = avg_win if np.isfinite(avg_win) else 0
        avg_loss = avg_loss if np.isfinite(avg_loss) else 0

        if avg_loss != 0:
            average_rr = avg_win / avg_loss
            average_rr = average_rr if np.isfinite(average_rr) else 0
        else:
            average_rr = np.inf if avg_win > 0 else 0

        # Max single trade loss and win
        max_single_trade_loss = float(df["pnl"].min()) if not df.empty else 0
        max_single_trade_win = float(df["pnl"].max()) if not df.empty else 0

        max_single_trade_loss = max_single_trade_loss if np.isfinite(max_single_trade_loss) else 0
        max_single_trade_win = max_single_trade_win if np.isfinite(max_single_trade_win) else 0

        result = {
            "total_trades": total_trades,
            "win_rate_percent": win_rate_percent,
            "average_rr": average_rr,
            "net_pnl_after_commission": net_pnl_after_commission,
            "max_single_trade_loss": max_single_trade_loss,
            "max_single_trade_win": max_single_trade_win,
            "total_commission": total_commission,
            "gross_pnl": gross_pnl
        }

        logger.info("KPIs computed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in calculate_kpis: {str(e)}")
        return {
            "total_trades": 0,
            "win_rate_percent": 0,
            "average_rr": 0,
            "net_pnl_after_commission": 0,
            "max_single_trade_loss": 0,
            "max_single_trade_win": 0,
            "total_commission": 0,
            "gross_pnl": 0
        }