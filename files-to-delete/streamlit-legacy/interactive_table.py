import pandas as pd
from st_aggrid import GridOptionsBuilder


def compute_trade_result(df: pd.DataFrame) -> pd.DataFrame:
    """Add trade_result column indicating win or loss.

    PnL values may come in as strings from uploaded CSV files. We coerce to
    numeric so comparisons don't raise type errors. Invalid values become ``NaN``
    and are treated as losses to avoid misleading results.
    """
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df["trade_result"] = df["pnl"].apply(
        lambda x: "Win" if pd.notna(x) and x >= 0 else "Loss"
    )
    return df


def get_grid_options(df: pd.DataFrame) -> dict:
    """Build AgGrid options with grouping and multi-sort enabled."""
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, enableRowGroup=True)
    gb.configure_column("symbol", rowGroup=True, hide=True)
    gb.configure_column("direction", rowGroup=True, hide=True)
    gb.configure_column("trade_result", rowGroup=True, hide=True)
    gb.configure_grid_options(suppressMultiSort=False)
    gb.configure_selection("single")
    return gb.build()


def trade_detail(row: pd.Series) -> dict:
    """Return additional trade metrics for detail view."""
    pnl = float(row.get("pnl", 0))
    mae = pnl if pnl < 0 else 0
    mfe = pnl if pnl > 0 else 0
    duration = pd.to_datetime(row["exit_time"]) - pd.to_datetime(row["entry_time"])
    return {"mae": mae, "mfe": mfe, "duration": duration, "notes": row.get("notes", "")}
import pandas as pd
import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode

def compute_trade_result(df: pd.DataFrame) -> pd.DataFrame:
    """Add trade_result column indicating win or loss.

    PnL values may come in as strings from uploaded CSV files. We coerce to
    numeric so comparisons don't raise type errors. Invalid values become ``NaN``
    and are treated as losses to avoid misleading results.
    """
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df["trade_result"] = df["pnl"].apply(
        lambda x: "Win" if pd.notna(x) and x >= 0 else "Loss"
    )
    return df

def get_grid_options(df: pd.DataFrame) -> dict:
    """Build AgGrid options with grouping and multi-sort enabled."""
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, enableRowGroup=True, filter=True)
    
    # Configure specific columns
    if 'symbol' in df.columns:
        gb.configure_column("symbol", rowGroup=True, hide=True)
    if 'direction' in df.columns:
        gb.configure_column("direction", rowGroup=True, hide=True)
    if 'trade_result' in df.columns:
        gb.configure_column("trade_result", rowGroup=True, hide=True)
    
    # Enable features
    gb.configure_grid_options(suppressMultiSort=False)
    gb.configure_selection("single", use_checkbox=True)
    gb.configure_pagination(paginationAutoPageSize=True)
    
    return gb.build()

def render_interactive_table(df: pd.DataFrame, height: int = 400) -> dict:
    """Render an interactive data table with advanced features."""
    if df.empty:
        st.info("No data to display")
        return {}
    
    # Add computed columns
    df_display = compute_trade_result(df)
    
    # Configure grid options
    grid_options = get_grid_options(df_display)
    
    # Render the grid
    try:
        grid_response = AgGrid(
            df_display,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            height=height,
            width='100%',
            reload_data=False
        )
        
        return {
            'data': grid_response['data'],
            'selected_rows': grid_response['selected_rows']
        }
    except Exception as e:
        st.error(f"Error rendering table: {str(e)}")
        # Fallback to regular dataframe display
        st.dataframe(df_display, height=height)
        return {'data': df_display, 'selected_rows': []}

def trade_detail(row: pd.Series) -> dict:
    """Return additional trade metrics for detail view."""
    pnl = float(row.get("pnl", 0))
    mae = pnl if pnl < 0 else 0  # Maximum Adverse Excursion
    mfe = pnl if pnl > 0 else 0  # Maximum Favorable Excursion
    
    try:
        duration = pd.to_datetime(row["exit_time"]) - pd.to_datetime(row["entry_time"])
    except:
        duration = pd.Timedelta(0)
    
    return {
        "mae": mae,
        "mfe": mfe,
        "duration": duration,
        "notes": row.get("notes", ""),
        "commission": row.get("commission", 0.0)
    }

def render_trade_detail_modal(selected_rows: list):
    """Render detailed view for selected trades."""
    if not selected_rows:
        return
    
    trade = selected_rows[0]  # Take first selected trade
    
    with st.modal("Trade Details"):
        st.subheader(f"Trade Details: {trade.get('symbol', 'Unknown')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Symbol:** {trade.get('symbol', 'N/A')}")
            st.write(f"**Direction:** {trade.get('direction', 'N/A')}")
            st.write(f"**Quantity:** {trade.get('qty', 'N/A')}")
            st.write(f"**Entry Price:** ${trade.get('entry_price', 0):.2f}")
            st.write(f"**Exit Price:** ${trade.get('exit_price', 0):.2f}")
        
        with col2:
            st.write(f"**Entry Time:** {trade.get('entry_time', 'N/A')}")
            st.write(f"**Exit Time:** {trade.get('exit_time', 'N/A')}")
            
            pnl = trade.get('pnl', 0)
            if pnl > 0:
                st.success(f"**P&L:** +${pnl:.2f}")
            else:
                st.error(f"**P&L:** ${pnl:.2f}")
            
            details = trade_detail(pd.Series(trade))
            st.write(f"**Duration:** {details['duration']}")
        
        if trade.get('notes'):
            st.subheader("Notes")
            st.write(trade['notes'])
