
import pandas as pd
import numpy as np
import streamlit as st


def safe_numeric_conversion(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Safely convert a column to numeric, handling errors gracefully."""
    try:
        df = df.copy()
        df[column] = pd.to_numeric(df[column], errors='coerce')
        # Drop rows where conversion failed (NaN values)
        df = df.dropna(subset=[column])
        # Remove infinite values
        df = df[np.isfinite(df[column])]
        return df
    except Exception:
        return pd.DataFrame()


def ensure_minimum_data_points(df: pd.DataFrame, min_points: int = 2) -> pd.DataFrame:
    """Ensure DataFrame has minimum data points for charting."""
    if df.empty:
        return df
    
    if len(df) < min_points:
        # Duplicate the last row to meet minimum requirements
        while len(df) < min_points:
            last_row = df.iloc[-1:].copy()
            if 'period' in df.columns:
                # Increment period by 1 day for time-based data
                last_row['period'] = last_row['period'] + pd.Timedelta(days=1)
            elif 'end_index' in df.columns:
                # Increment index for rolling metrics
                last_row['end_index'] = last_row['end_index'] + 1
            df = pd.concat([df, last_row], ignore_index=True)
    
    return df


def compute_basic_stats(df: pd.DataFrame) -> dict:
    """Compute basic trading statistics with comprehensive error handling."""
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
            return default_stats

        # Safe numeric conversion for PnL
        df = safe_numeric_conversion(df, 'pnl')
        
        if df.empty:
            return default_stats

        # Calculate basic metrics
        total_trades = len(df)
        wins = df[df["pnl"] > 0]
        losses = df[df["pnl"] <= 0]
        
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0
        
        # Safe average calculations
        avg_win = float(wins["pnl"].mean()) if not wins.empty else 0.0
        avg_loss = float(losses["pnl"].mean()) if not losses.empty else 0.0
        
        # Ensure no infinite values
        avg_win = avg_win if np.isfinite(avg_win) else 0.0
        avg_loss = avg_loss if np.isfinite(avg_loss) else 0.0
        
        # Calculate reward/risk ratio safely
        if avg_loss != 0 and np.isfinite(avg_loss) and np.isfinite(avg_win):
            reward_risk = abs(avg_win / avg_loss)
            reward_risk = min(reward_risk, 999.99)  # Cap at reasonable max
        else:
            reward_risk = 0.0

        # Calculate expectancy
        expectancy = (win_rate / 100) * avg_win + (1 - win_rate / 100) * avg_loss
        expectancy = expectancy if np.isfinite(expectancy) else 0.0

        # Calculate profit factor
        wins_sum = float(wins["pnl"].sum()) if not wins.empty else 0.0
        losses_sum = float(abs(losses["pnl"].sum())) if not losses.empty else 0.0
        
        if losses_sum != 0 and np.isfinite(losses_sum) and np.isfinite(wins_sum):
            profit_factor = wins_sum / losses_sum
            profit_factor = min(profit_factor, 999.99)  # Cap at reasonable max
        else:
            profit_factor = 0.0 if wins_sum == 0 else 999.99

        # Create equity curve with proper datetime index
        try:
            if 'exit_time' in df.columns:
                df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
                df = df.dropna(subset=['exit_time'])
                if not df.empty:
                    df_sorted = df.sort_values('exit_time')
                    equity_curve = df_sorted['pnl'].cumsum()
                    equity_curve.index = df_sorted['exit_time']
                    # Ensure no infinite values in equity curve
                    equity_curve = equity_curve[np.isfinite(equity_curve)]
                else:
                    equity_curve = pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))
            else:
                equity_curve = df['pnl'].cumsum()
                # Ensure no infinite values
                equity_curve = equity_curve[np.isfinite(equity_curve)]
                
            # Ensure minimum 2 points for charting
            if len(equity_curve) < 2:
                equity_curve = pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))
                
        except Exception:
            equity_curve = pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))

        # Calculate max drawdown safely
        try:
            if not equity_curve.empty and len(equity_curve) > 1:
                drawdown = equity_curve.cummax() - equity_curve
                max_drawdown = float(drawdown.max()) if not drawdown.empty else 0.0
                max_drawdown = max_drawdown if np.isfinite(max_drawdown) else 0.0
            else:
                max_drawdown = 0.0
        except Exception:
            max_drawdown = 0.0

        # Calculate Sharpe ratio safely
        try:
            if not equity_curve.empty and len(equity_curve) > 1:
                returns = equity_curve.pct_change().dropna()
                returns = returns[np.isfinite(returns)]  # Remove infinite values
                if not returns.empty and returns.std() != 0:
                    sharpe = float(np.sqrt(252) * returns.mean() / returns.std())
                    sharpe = max(min(sharpe, 10.0), -10.0) if np.isfinite(sharpe) else 0.0
                else:
                    sharpe = 0.0
            else:
                sharpe = 0.0
        except Exception:
            sharpe = 0.0

        return {
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

    except Exception as e:
        st.error(f"Error computing basic statistics: {str(e)}")
        return default_stats


def performance_over_time(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """Return P&L and win rate aggregated by period with comprehensive error handling."""
    try:
        if df.empty:
            default_date = pd.Timestamp.now().normalize()
            return pd.DataFrame({
                "period": [default_date, default_date + pd.Timedelta(days=1)], 
                "pnl": [0.0, 0.0], 
                "win_rate": [0.0, 0.0]
            })

        # Safe numeric conversions
        df = safe_numeric_conversion(df, 'pnl')
        
        if df.empty:
            default_date = pd.Timestamp.now().normalize()
            return pd.DataFrame({
                "period": [default_date, default_date + pd.Timedelta(days=1)], 
                "pnl": [0.0, 0.0], 
                "win_rate": [0.0, 0.0]
            })

        # Convert exit_time safely
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
        df = df.dropna(subset=["exit_time"])

        if df.empty:
            default_date = pd.Timestamp.now().normalize()
            return pd.DataFrame({
                "period": [default_date, default_date + pd.Timedelta(days=1)], 
                "pnl": [0.0, 0.0], 
                "win_rate": [0.0, 0.0]
            })

        # Group by period
        period = df["exit_time"].dt.to_period(freq).dt.to_timestamp()
        grouped = df.groupby(period)
        
        # Calculate aggregated values
        pnl = grouped["pnl"].sum()
        win_rate = grouped.apply(lambda g: float((g["pnl"] > 0).mean() * 100), include_groups=False)

        # Clean data - remove infinite and NaN values
        pnl = pnl.fillna(0.0)
        win_rate = win_rate.fillna(0.0)
        
        # Ensure finite values only
        pnl_values = [float(x) if np.isfinite(x) else 0.0 for x in pnl.values]
        wr_values = [float(x) if np.isfinite(x) else 0.0 for x in win_rate.values]

        result = pd.DataFrame({
            "period": pnl.index, 
            "pnl": pnl_values, 
            "win_rate": wr_values
        })

        # Ensure minimum data points for charting
        result = ensure_minimum_data_points(result, min_points=2)
        
        return result

    except Exception as e:
        st.error(f"Error calculating performance over time: {str(e)}")
        default_date = pd.Timestamp.now().normalize()
        return pd.DataFrame({
            "period": [default_date, default_date + pd.Timedelta(days=1)], 
            "pnl": [0.0, 0.0], 
            "win_rate": [0.0, 0.0]
        })


def median_results(df: pd.DataFrame) -> dict:
    """Return median PnL statistics with error handling."""
    try:
        df = safe_numeric_conversion(df, 'pnl')

        if df.empty:
            return {
                "median_pnl": 0.0,
                "median_win": 0.0,
                "median_loss": 0.0,
            }

        wins = df[df["pnl"] > 0]
        losses = df[df["pnl"] <= 0]

        median_pnl = float(df["pnl"].median()) if not df.empty else 0.0
        median_win = float(wins["pnl"].median()) if not wins.empty else 0.0
        median_loss = float(losses["pnl"].median()) if not losses.empty else 0.0

        # Ensure finite values
        median_pnl = median_pnl if np.isfinite(median_pnl) else 0.0
        median_win = median_win if np.isfinite(median_win) else 0.0
        median_loss = median_loss if np.isfinite(median_loss) else 0.0

        return {
            "median_pnl": median_pnl,
            "median_win": median_win,
            "median_loss": median_loss,
        }

    except Exception as e:
        st.error(f"Error calculating median results: {str(e)}")
        return {
            "median_pnl": 0.0,
            "median_win": 0.0,
            "median_loss": 0.0,
        }


def profit_factor_by_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate profit factor for each trading symbol with error handling."""
    try:
        if df.empty:
            return pd.DataFrame({
                "symbol": ["No Data"],
                "profit_factor": [0.0]
            })

        # Safe numeric conversion
        df = safe_numeric_conversion(df, 'pnl')
        df = df.dropna(subset=["symbol"])

        if df.empty:
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
                    return min(pf, 999.99) if np.isfinite(pf) else 0.0
                else:
                    return 999.99 if wins > 0 else 0.0
            except Exception:
                return 0.0

        result = (
            df.groupby("symbol")
            .apply(_pf, include_groups=False)
            .reset_index(name="profit_factor")
            .sort_values("symbol")
        )
        
        return result

    except Exception as e:
        st.error(f"Error calculating profit factor by symbol: {str(e)}")
        return pd.DataFrame({
            "symbol": ["Error"],
            "profit_factor": [0.0]
        })


def trade_duration_stats(df: pd.DataFrame) -> dict:
    """Calculate statistics on trade durations in minutes with error handling."""
    try:
        if df.empty:
            return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}

        df = df.copy()
        df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
        df = df.dropna(subset=["entry_time", "exit_time"])
        
        if df.empty:
            return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}
        
        durations = (df["exit_time"] - df["entry_time"]).dt.total_seconds() / 60
        durations = durations[np.isfinite(durations)]  # Remove infinite values
        
        if durations.empty:
            return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}
        
        return {
            "average_minutes": float(durations.mean()) if not durations.empty else 0,
            "max_minutes": float(durations.max()) if not durations.empty else 0,
            "min_minutes": float(durations.min()) if not durations.empty else 0,
            "median_minutes": float(durations.median()) if not durations.empty else 0,
        }

    except Exception as e:
        st.error(f"Error calculating trade duration statistics: {str(e)}")
        return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}


def max_streaks(df: pd.DataFrame) -> dict:
    """Return the longest consecutive win and loss streaks with error handling."""
    try:
        df = safe_numeric_conversion(df, 'pnl')

        if df.empty:
            return {"max_win_streak": 0, "max_loss_streak": 0}

        max_win = 0
        max_loss = 0
        current_win = 0
        current_loss = 0
        
        for pnl in df["pnl"]:
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

        return {"max_win_streak": max_win, "max_loss_streak": max_loss}

    except Exception as e:
        st.error(f"Error calculating max streaks: {str(e)}")
        return {"max_win_streak": 0, "max_loss_streak": 0}


def rolling_metrics(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Compute rolling win rate and profit factor over a trade window with error handling."""
    try:
        df = safe_numeric_conversion(df, 'pnl')

        if df.empty or len(df) < window:
            return pd.DataFrame({
                "end_index": [0.0, 1.0],
                "win_rate": [0.0, 0.0],
                "profit_factor": [0.0, 0.0]
            })

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
                # Skip this window if calculation fails
                continue

        if not results:
            return pd.DataFrame({
                "end_index": [0.0, 1.0],
                "win_rate": [0.0, 0.0],
                "profit_factor": [0.0, 0.0]
            })

        result_df = pd.DataFrame(results)
        result_df = ensure_minimum_data_points(result_df, min_points=2)
        
        return result_df

    except Exception as e:
        st.error(f"Error calculating rolling metrics: {str(e)}")
        return pd.DataFrame({
            "end_index": [0.0, 1.0],
            "win_rate": [0.0, 0.0],
            "profit_factor": [0.0, 0.0]
        })


def calculate_kpis(df: pd.DataFrame, commission_per_trade: float = 3.5) -> dict:
    """Calculate key performance indicators including commission costs with error handling."""
    try:
        df = safe_numeric_conversion(df, 'pnl')

        if df.empty:
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
        avg_win = float(winning_trades["pnl"].mean()) if not winning_trades.empty else 0
        avg_loss = float(abs(losing_trades["pnl"].mean())) if not losing_trades.empty else 0
        
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

        return {
            "total_trades": total_trades,
            "win_rate_percent": win_rate_percent,
            "average_rr": average_rr,
            "net_pnl_after_commission": net_pnl_after_commission,
            "max_single_trade_loss": max_single_trade_loss,
            "max_single_trade_win": max_single_trade_win,
            "total_commission": total_commission,
            "gross_pnl": gross_pnl
        }

    except Exception as e:
        st.error(f"Error calculating KPIs: {str(e)}")
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
