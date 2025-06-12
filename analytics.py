
import pandas as pd
import numpy as np
import streamlit as st


def debug_dataframe(df: pd.DataFrame, context: str):
    """Debug helper to print DataFrame info and detect problematic data."""
    st.write(f"🔍 **DEBUG - {context}**")
    if df.empty:
        st.write(f"   - DataFrame is EMPTY")
        return
    
    st.write(f"   - Shape: {df.shape}")
    st.write(f"   - Dtypes: {dict(df.dtypes)}")
    
    # Check for infinite and NaN values
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            inf_count = np.isinf(df[col]).sum()
            nan_count = df[col].isna().sum()
            if inf_count > 0 or nan_count > 0:
                st.write(f"   - Column '{col}': {inf_count} infinite, {nan_count} NaN values")
                st.write(f"   - Sample values: {df[col].head().tolist()}")


def force_numeric_and_validate(df: pd.DataFrame, column: str, context: str) -> pd.DataFrame:
    """Force numeric conversion and validate data before analytics operations."""
    st.write(f"🔧 **FORCE NUMERIC - {context} - Column: {column}**")
    
    if df.empty:
        st.write(f"   - Input DataFrame is empty, returning empty DataFrame")
        return df
    
    if column not in df.columns:
        st.write(f"   - Column '{column}' not found in DataFrame")
        return df
    
    # Show original dtype
    st.write(f"   - Original dtype of '{column}': {df[column].dtype}")
    
    # Force numeric conversion
    df = df.copy()
    original_count = len(df)
    df[column] = pd.to_numeric(df[column], errors='coerce')
    
    # Remove NaN values
    df = df.dropna(subset=[column])
    after_nan_count = len(df)
    
    # Remove infinite values
    df = df[np.isfinite(df[column])]
    final_count = len(df)
    
    st.write(f"   - After numeric conversion: {df[column].dtype}")
    st.write(f"   - Rows: {original_count} → {after_nan_count} (after NaN removal) → {final_count} (after infinite removal)")
    
    if not df.empty:
        st.write(f"   - Value range: {df[column].min():.2f} to {df[column].max():.2f}")
        st.write(f"   - Sample values: {df[column].head().tolist()}")
    
    return df


def validate_chart_data(df: pd.DataFrame, context: str) -> bool:
    """Validate data is suitable for charting."""
    st.write(f"📊 **CHART VALIDATION - {context}**")
    
    if df.empty:
        st.warning(f"⚠️ Cannot chart {context}: DataFrame is empty")
        return False
    
    if len(df) < 2:
        st.warning(f"⚠️ Cannot chart {context}: Need at least 2 data points, got {len(df)}")
        return False
    
    # Check all numeric columns for infinite/NaN values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        inf_count = np.isinf(df[col]).sum()
        nan_count = df[col].isna().sum()
        if inf_count > 0 or nan_count > 0:
            st.warning(f"⚠️ Cannot chart {context}: Column '{col}' has {inf_count} infinite and {nan_count} NaN values")
            return False
    
    st.success(f"✅ Chart validation passed for {context}")
    return True


def compute_basic_stats(df: pd.DataFrame) -> dict:
    """Compute basic trading statistics with comprehensive debugging."""
    st.write("=" * 50)
    st.write("🚀 **STARTING compute_basic_stats**")
    
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
        debug_dataframe(df, "compute_basic_stats INPUT")
        
        if df.empty:
            st.warning("⚠️ compute_basic_stats: Input DataFrame is empty, returning defaults")
            return default_stats

        # Force numeric conversion on PnL
        df = force_numeric_and_validate(df, 'pnl', "compute_basic_stats")
        
        if df.empty:
            st.warning("⚠️ compute_basic_stats: No valid PnL data after cleaning")
            return default_stats

        debug_dataframe(df, "compute_basic_stats AFTER PnL CLEANING")

        # Calculate basic metrics
        total_trades = len(df)
        wins = df[df["pnl"] > 0]
        losses = df[df["pnl"] <= 0]
        
        st.write(f"📈 Total trades: {total_trades}, Wins: {len(wins)}, Losses: {len(losses)}")
        
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0
        
        # Safe average calculations with debugging
        st.write("🧮 Computing averages...")
        avg_win = 0.0
        avg_loss = 0.0
        
        if not wins.empty:
            st.write(f"   - Wins PnL dtype before mean: {wins['pnl'].dtype}")
            avg_win = float(wins["pnl"].mean())
            st.write(f"   - Average win: {avg_win}")
        
        if not losses.empty:
            st.write(f"   - Losses PnL dtype before mean: {losses['pnl'].dtype}")
            avg_loss = float(losses["pnl"].mean())
            st.write(f"   - Average loss: {avg_loss}")
        
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
        st.write("🧮 Computing profit factor...")
        wins_sum = 0.0
        losses_sum = 0.0
        
        if not wins.empty:
            st.write(f"   - Wins PnL dtype before sum: {wins['pnl'].dtype}")
            wins_sum = float(wins["pnl"].sum())
            st.write(f"   - Wins sum: {wins_sum}")
            
        if not losses.empty:
            st.write(f"   - Losses PnL dtype before sum: {losses['pnl'].dtype}")
            losses_sum = float(abs(losses["pnl"].sum()))
            st.write(f"   - Losses sum: {losses_sum}")
        
        if losses_sum != 0 and np.isfinite(losses_sum) and np.isfinite(wins_sum):
            profit_factor = wins_sum / losses_sum
            profit_factor = min(profit_factor, 999.99)  # Cap at reasonable max
        else:
            profit_factor = 0.0 if wins_sum == 0 else 999.99

        # Create equity curve with proper datetime index
        st.write("📈 Creating equity curve...")
        try:
            if 'exit_time' in df.columns:
                df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
                df = df.dropna(subset=['exit_time'])
                if not df.empty:
                    df_sorted = df.sort_values('exit_time')
                    st.write(f"   - Exit_time dtype: {df_sorted['exit_time'].dtype}")
                    st.write(f"   - PnL dtype before cumsum: {df_sorted['pnl'].dtype}")
                    
                    equity_curve = df_sorted['pnl'].cumsum()
                    equity_curve.index = df_sorted['exit_time']
                    
                    # Ensure no infinite values in equity curve
                    equity_curve = equity_curve[np.isfinite(equity_curve)]
                    st.write(f"   - Equity curve length: {len(equity_curve)}")
                    st.write(f"   - Equity curve dtype: {equity_curve.dtype}")
                else:
                    equity_curve = pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))
            else:
                st.write(f"   - PnL dtype before cumsum: {df['pnl'].dtype}")
                equity_curve = df['pnl'].cumsum()
                # Ensure no infinite values
                equity_curve = equity_curve[np.isfinite(equity_curve)]
                
            # Ensure minimum 2 points for charting
            if len(equity_curve) < 2:
                equity_curve = pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))
                
        except Exception as e:
            st.error(f"Error creating equity curve: {str(e)}")
            equity_curve = pd.Series([0.0, 0.0], index=pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D'))

        # Calculate max drawdown safely
        st.write("📉 Computing max drawdown...")
        try:
            if not equity_curve.empty and len(equity_curve) > 1:
                st.write(f"   - Equity curve dtype before drawdown: {equity_curve.dtype}")
                drawdown = equity_curve.cummax() - equity_curve
                max_drawdown = float(drawdown.max()) if not drawdown.empty else 0.0
                max_drawdown = max_drawdown if np.isfinite(max_drawdown) else 0.0
                st.write(f"   - Max drawdown: {max_drawdown}")
            else:
                max_drawdown = 0.0
        except Exception as e:
            st.error(f"Error calculating max drawdown: {str(e)}")
            max_drawdown = 0.0

        # Calculate Sharpe ratio safely
        st.write("📊 Computing Sharpe ratio...")
        try:
            if not equity_curve.empty and len(equity_curve) > 1:
                returns = equity_curve.pct_change().dropna()
                returns = returns[np.isfinite(returns)]  # Remove infinite values
                st.write(f"   - Returns dtype: {returns.dtype}")
                st.write(f"   - Returns length: {len(returns)}")
                if not returns.empty and returns.std() != 0:
                    sharpe = float(np.sqrt(252) * returns.mean() / returns.std())
                    sharpe = max(min(sharpe, 10.0), -10.0) if np.isfinite(sharpe) else 0.0
                    st.write(f"   - Sharpe ratio: {sharpe}")
                else:
                    sharpe = 0.0
            else:
                sharpe = 0.0
        except Exception as e:
            st.error(f"Error calculating Sharpe ratio: {str(e)}")
            sharpe = 0.0

        final_stats = {
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
        
        st.write("✅ **compute_basic_stats COMPLETED**")
        st.write(f"   - Final stats: {list(final_stats.keys())}")
        
        return final_stats

    except Exception as e:
        st.error(f"❌ Error in compute_basic_stats: {str(e)}")
        return default_stats


def performance_over_time(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """Return P&L and win rate aggregated by period with comprehensive debugging."""
    st.write("=" * 50)
    st.write("🚀 **STARTING performance_over_time**")
    
    try:
        debug_dataframe(df, "performance_over_time INPUT")
        
        if df.empty:
            st.warning("⚠️ performance_over_time: Input DataFrame is empty")
            default_date = pd.Timestamp.now().normalize()
            return pd.DataFrame({
                "period": [default_date, default_date + pd.Timedelta(days=1)], 
                "pnl": [0.0, 0.0], 
                "win_rate": [0.0, 0.0]
            })

        # Force numeric conversion on PnL
        df = force_numeric_and_validate(df, 'pnl', "performance_over_time")
        
        if df.empty:
            st.warning("⚠️ performance_over_time: No valid PnL data after cleaning")
            default_date = pd.Timestamp.now().normalize()
            return pd.DataFrame({
                "period": [default_date, default_date + pd.Timedelta(days=1)], 
                "pnl": [0.0, 0.0], 
                "win_rate": [0.0, 0.0]
            })

        # Convert exit_time safely
        st.write("📅 Converting exit_time...")
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
        df = df.dropna(subset=["exit_time"])
        st.write(f"   - Exit_time dtype: {df['exit_time'].dtype}")
        st.write(f"   - Rows after exit_time cleaning: {len(df)}")

        if df.empty:
            st.warning("⚠️ performance_over_time: No valid exit_time data")
            default_date = pd.Timestamp.now().normalize()
            return pd.DataFrame({
                "period": [default_date, default_date + pd.Timedelta(days=1)], 
                "pnl": [0.0, 0.0], 
                "win_rate": [0.0, 0.0]
            })

        # Group by period
        st.write(f"📊 Grouping by period (freq={freq})...")
        period = df["exit_time"].dt.to_period(freq).dt.to_timestamp()
        grouped = df.groupby(period)
        st.write(f"   - Number of groups: {len(grouped)}")
        
        # Calculate aggregated values with debugging
        st.write("🧮 Computing grouped aggregations...")
        st.write(f"   - PnL dtype before sum: {df['pnl'].dtype}")
        pnl = grouped["pnl"].sum()
        st.write(f"   - PnL sums dtype: {pnl.dtype}")
        st.write(f"   - PnL sums: {pnl.tolist()}")
        
        win_rate = grouped.apply(lambda g: float((g["pnl"] > 0).mean() * 100), include_groups=False)
        st.write(f"   - Win rates: {win_rate.tolist()}")

        # Clean data - remove infinite and NaN values
        pnl = pnl.fillna(0.0)
        win_rate = win_rate.fillna(0.0)
        
        # Ensure finite values only
        pnl_values = [float(x) if np.isfinite(x) else 0.0 for x in pnl.values]
        wr_values = [float(x) if np.isfinite(x) else 0.0 for x in win_rate.values]
        
        st.write(f"   - Final PnL values: {pnl_values}")
        st.write(f"   - Final win rate values: {wr_values}")

        result = pd.DataFrame({
            "period": pnl.index, 
            "pnl": pnl_values, 
            "win_rate": wr_values
        })

        debug_dataframe(result, "performance_over_time RESULT before validation")

        # Ensure minimum data points for charting
        if len(result) < 2:
            st.write("📊 Adding dummy data point for minimum chart requirements")
            if len(result) == 1:
                dummy_row = result.iloc[0:1].copy()
                dummy_row['period'] = dummy_row['period'] + pd.Timedelta(days=1)
                result = pd.concat([result, dummy_row], ignore_index=True)
        
        debug_dataframe(result, "performance_over_time FINAL RESULT")
        st.write("✅ **performance_over_time COMPLETED**")
        
        return result

    except Exception as e:
        st.error(f"❌ Error in performance_over_time: {str(e)}")
        default_date = pd.Timestamp.now().normalize()
        return pd.DataFrame({
            "period": [default_date, default_date + pd.Timedelta(days=1)], 
            "pnl": [0.0, 0.0], 
            "win_rate": [0.0, 0.0]
        })


def median_results(df: pd.DataFrame) -> dict:
    """Return median PnL statistics with debugging."""
    st.write("=" * 50)
    st.write("🚀 **STARTING median_results**")
    
    try:
        debug_dataframe(df, "median_results INPUT")
        
        df = force_numeric_and_validate(df, 'pnl', "median_results")

        if df.empty:
            st.warning("⚠️ median_results: No valid PnL data")
            return {
                "median_pnl": 0.0,
                "median_win": 0.0,
                "median_loss": 0.0,
            }

        wins = df[df["pnl"] > 0]
        losses = df[df["pnl"] <= 0]
        
        st.write(f"📊 Computing medians - Total: {len(df)}, Wins: {len(wins)}, Losses: {len(losses)}")

        median_pnl = 0.0
        median_win = 0.0
        median_loss = 0.0
        
        if not df.empty:
            st.write(f"   - All PnL dtype before median: {df['pnl'].dtype}")
            median_pnl = float(df["pnl"].median())
            
        if not wins.empty:
            st.write(f"   - Wins PnL dtype before median: {wins['pnl'].dtype}")
            median_win = float(wins["pnl"].median())
            
        if not losses.empty:
            st.write(f"   - Losses PnL dtype before median: {losses['pnl'].dtype}")
            median_loss = float(losses["pnl"].median())

        # Ensure finite values
        median_pnl = median_pnl if np.isfinite(median_pnl) else 0.0
        median_win = median_win if np.isfinite(median_win) else 0.0
        median_loss = median_loss if np.isfinite(median_loss) else 0.0
        
        result = {
            "median_pnl": median_pnl,
            "median_win": median_win,
            "median_loss": median_loss,
        }
        
        st.write(f"✅ **median_results COMPLETED**: {result}")
        return result

    except Exception as e:
        st.error(f"❌ Error in median_results: {str(e)}")
        return {
            "median_pnl": 0.0,
            "median_win": 0.0,
            "median_loss": 0.0,
        }


def profit_factor_by_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate profit factor for each trading symbol with debugging."""
    st.write("=" * 50)
    st.write("🚀 **STARTING profit_factor_by_symbol**")
    
    try:
        debug_dataframe(df, "profit_factor_by_symbol INPUT")
        
        if df.empty:
            st.warning("⚠️ profit_factor_by_symbol: Input DataFrame is empty")
            return pd.DataFrame({
                "symbol": ["No Data"],
                "profit_factor": [0.0]
            })

        # Force numeric conversion
        df = force_numeric_and_validate(df, 'pnl', "profit_factor_by_symbol")
        df = df.dropna(subset=["symbol"])

        if df.empty:
            st.warning("⚠️ profit_factor_by_symbol: No valid data after cleaning")
            return pd.DataFrame({
                "symbol": ["No Data"],
                "profit_factor": [0.0]
            })

        def _pf(group: pd.DataFrame) -> float:
            try:
                st.write(f"   - Computing PF for symbol: {group.name}")
                st.write(f"   - Group PnL dtype: {group['pnl'].dtype}")
                
                wins = group[group["pnl"] > 0]["pnl"].sum()
                losses = group[group["pnl"] <= 0]["pnl"].sum()
                
                st.write(f"   - Wins sum: {wins}, Losses sum: {losses}")
                
                wins = wins if np.isfinite(wins) else 0.0
                losses = losses if np.isfinite(losses) else 0.0
                
                if losses != 0:
                    pf = wins / abs(losses)
                    result = min(pf, 999.99) if np.isfinite(pf) else 0.0
                else:
                    result = 999.99 if wins > 0 else 0.0
                    
                st.write(f"   - Final PF: {result}")
                return result
            except Exception as e:
                st.error(f"Error computing PF for group: {str(e)}")
                return 0.0

        st.write("🧮 Computing profit factors by symbol...")
        result = (
            df.groupby("symbol")
            .apply(_pf, include_groups=False)
            .reset_index(name="profit_factor")
            .sort_values("symbol")
        )
        
        debug_dataframe(result, "profit_factor_by_symbol RESULT")
        st.write("✅ **profit_factor_by_symbol COMPLETED**")
        
        return result

    except Exception as e:
        st.error(f"❌ Error in profit_factor_by_symbol: {str(e)}")
        return pd.DataFrame({
            "symbol": ["Error"],
            "profit_factor": [0.0]
        })


def trade_duration_stats(df: pd.DataFrame) -> dict:
    """Calculate statistics on trade durations in minutes with debugging."""
    st.write("=" * 50)
    st.write("🚀 **STARTING trade_duration_stats**")
    
    try:
        debug_dataframe(df, "trade_duration_stats INPUT")
        
        if df.empty:
            st.warning("⚠️ trade_duration_stats: Input DataFrame is empty")
            return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}

        df = df.copy()
        df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
        df = df.dropna(subset=["entry_time", "exit_time"])
        
        st.write(f"📅 Time columns after conversion:")
        st.write(f"   - Entry_time dtype: {df['entry_time'].dtype}")
        st.write(f"   - Exit_time dtype: {df['exit_time'].dtype}")
        st.write(f"   - Rows after time cleaning: {len(df)}")
        
        if df.empty:
            st.warning("⚠️ trade_duration_stats: No valid time data")
            return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}
        
        durations = (df["exit_time"] - df["entry_time"]).dt.total_seconds() / 60
        durations = durations[np.isfinite(durations)]  # Remove infinite values
        
        st.write(f"⏱️ Duration stats:")
        st.write(f"   - Durations dtype: {durations.dtype}")
        st.write(f"   - Valid durations: {len(durations)}")
        
        if durations.empty:
            st.warning("⚠️ trade_duration_stats: No valid duration data")
            return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}
        
        st.write(f"   - Duration dtype before aggregations: {durations.dtype}")
        
        result = {
            "average_minutes": float(durations.mean()) if not durations.empty else 0,
            "max_minutes": float(durations.max()) if not durations.empty else 0,
            "min_minutes": float(durations.min()) if not durations.empty else 0,
            "median_minutes": float(durations.median()) if not durations.empty else 0,
        }
        
        st.write(f"✅ **trade_duration_stats COMPLETED**: {result}")
        return result

    except Exception as e:
        st.error(f"❌ Error in trade_duration_stats: {str(e)}")
        return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}


def max_streaks(df: pd.DataFrame) -> dict:
    """Return the longest consecutive win and loss streaks with debugging."""
    st.write("=" * 50)
    st.write("🚀 **STARTING max_streaks**")
    
    try:
        debug_dataframe(df, "max_streaks INPUT")
        
        df = force_numeric_and_validate(df, 'pnl', "max_streaks")

        if df.empty:
            st.warning("⚠️ max_streaks: No valid PnL data")
            return {"max_win_streak": 0, "max_loss_streak": 0}

        max_win = 0
        max_loss = 0
        current_win = 0
        current_loss = 0
        
        st.write(f"🔢 Processing {len(df)} PnL values for streaks...")
        st.write(f"   - PnL dtype: {df['pnl'].dtype}")
        
        for i, pnl in enumerate(df["pnl"]):
            if not np.isfinite(pnl):
                st.write(f"   - Skipping non-finite value at index {i}: {pnl}")
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
        st.write(f"✅ **max_streaks COMPLETED**: {result}")
        return result

    except Exception as e:
        st.error(f"❌ Error in max_streaks: {str(e)}")
        return {"max_win_streak": 0, "max_loss_streak": 0}


def rolling_metrics(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Compute rolling win rate and profit factor over a trade window with debugging."""
    st.write("=" * 50)
    st.write("🚀 **STARTING rolling_metrics**")
    
    try:
        debug_dataframe(df, "rolling_metrics INPUT")
        
        df = force_numeric_and_validate(df, 'pnl', "rolling_metrics")

        if df.empty or len(df) < window:
            st.warning(f"⚠️ rolling_metrics: Need at least {window} trades, got {len(df)}")
            return pd.DataFrame({
                "end_index": [0.0, 1.0],
                "win_rate": [0.0, 0.0],
                "profit_factor": [0.0, 0.0]
            })

        results = []
        st.write(f"🔄 Computing rolling metrics with window={window}...")
        
        for end in range(window, len(df) + 1):
            try:
                window_df = df.iloc[end - window : end]
                st.write(f"   - Window {end-window} to {end-1}:")
                st.write(f"     - Window PnL dtype: {window_df['pnl'].dtype}")
                
                stats = compute_basic_stats(window_df)

                # Ensure finite values only
                win_rate = stats["win_rate"] if np.isfinite(stats["win_rate"]) else 0.0
                profit_factor = stats["profit_factor"] if np.isfinite(stats["profit_factor"]) else 0.0

                st.write(f"     - Win rate: {win_rate}, PF: {profit_factor}")

                results.append({
                    "end_index": float(end - 1),
                    "win_rate": win_rate,
                    "profit_factor": profit_factor,
                })
            except Exception as e:
                st.error(f"Error in rolling window {end}: {str(e)}")
                continue

        if not results:
            st.warning("⚠️ rolling_metrics: No valid rolling calculations")
            return pd.DataFrame({
                "end_index": [0.0, 1.0],
                "win_rate": [0.0, 0.0],
                "profit_factor": [0.0, 0.0]
            })

        result_df = pd.DataFrame(results)
        
        # Ensure minimum data points for charting
        if len(result_df) < 2:
            st.write("📊 Adding dummy data point for minimum chart requirements")
            if len(result_df) == 1:
                dummy_row = result_df.iloc[0:1].copy()
                dummy_row['end_index'] = dummy_row['end_index'] + 1
                result_df = pd.concat([result_df, dummy_row], ignore_index=True)
        
        debug_dataframe(result_df, "rolling_metrics FINAL RESULT")
        st.write("✅ **rolling_metrics COMPLETED**")
        
        return result_df

    except Exception as e:
        st.error(f"❌ Error in rolling_metrics: {str(e)}")
        return pd.DataFrame({
            "end_index": [0.0, 1.0],
            "win_rate": [0.0, 0.0],
            "profit_factor": [0.0, 0.0]
        })


def calculate_kpis(df: pd.DataFrame, commission_per_trade: float = 3.5) -> dict:
    """Calculate key performance indicators including commission costs with debugging."""
    st.write("=" * 50)
    st.write("🚀 **STARTING calculate_kpis**")
    
    try:
        debug_dataframe(df, "calculate_kpis INPUT")
        
        df = force_numeric_and_validate(df, 'pnl', "calculate_kpis")

        if df.empty:
            st.warning("⚠️ calculate_kpis: No valid PnL data")
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
        st.write(f"💰 Computing PnL metrics:")
        st.write(f"   - PnL dtype before sum: {df['pnl'].dtype}")
        
        gross_pnl = float(df["pnl"].sum()) if not df.empty else 0.0
        gross_pnl = gross_pnl if np.isfinite(gross_pnl) else 0.0
        net_pnl_after_commission = gross_pnl - total_commission
        
        st.write(f"   - Gross PnL: {gross_pnl}")
        st.write(f"   - Total commission: {total_commission}")
        st.write(f"   - Net PnL: {net_pnl_after_commission}")

        # Win rate %
        winning_trades = df[df["pnl"] > 0]
        losing_trades = df[df["pnl"] <= 0]
        win_rate_percent = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0

        # Average RR (Reward to Risk ratio)
        avg_win = 0
        avg_loss = 0
        
        if not winning_trades.empty:
            st.write(f"   - Winning trades PnL dtype before mean: {winning_trades['pnl'].dtype}")
            avg_win = float(winning_trades["pnl"].mean())
            
        if not losing_trades.empty:
            st.write(f"   - Losing trades PnL dtype before mean: {losing_trades['pnl'].dtype}")
            avg_loss = float(abs(losing_trades["pnl"].mean()))
        
        avg_win = avg_win if np.isfinite(avg_win) else 0
        avg_loss = avg_loss if np.isfinite(avg_loss) else 0
        
        if avg_loss != 0:
            average_rr = avg_win / avg_loss
            average_rr = average_rr if np.isfinite(average_rr) else 0
        else:
            average_rr = np.inf if avg_win > 0 else 0

        # Max single trade loss and win
        st.write(f"   - PnL dtype before min/max: {df['pnl'].dtype}")
        
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
        
        st.write(f"✅ **calculate_kpis COMPLETED**")
        for k, v in result.items():
            st.write(f"   - {k}: {v}")
        
        return result

    except Exception as e:
        st.error(f"❌ Error in calculate_kpis: {str(e)}")
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
