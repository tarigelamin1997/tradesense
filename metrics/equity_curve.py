
"""
Equity curve generation and analysis tools.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class EquityCurveEngine:
    """Generate and analyze equity curves with advanced features."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with trade DataFrame.
        
        Args:
            df: DataFrame containing trade data
        """
        self.df = df.copy()
        self.equity_data = None
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for equity curve analysis."""
        # Ensure we have valid P&L data
        self.df['pnl_numeric'] = pd.to_numeric(self.df['pnl'], errors='coerce')
        self.df = self.df.dropna(subset=['pnl_numeric'])
        
        # Sort by exit time for proper chronological order
        if 'exit_time' in self.df.columns:
            self.df['exit_time'] = pd.to_datetime(self.df['exit_time'])
            self.df = self.df.sort_values('exit_time')
        
        # Calculate cumulative P&L
        self.df['cumulative_pnl'] = self.df['pnl_numeric'].cumsum()
        
        # Calculate running maximum for drawdown
        self.df['running_max'] = self.df['cumulative_pnl'].expanding().max()
        
        # Calculate drawdown
        self.df['drawdown'] = self.df['running_max'] - self.df['cumulative_pnl']
        self.df['drawdown_percent'] = (self.df['drawdown'] / self.df['running_max']) * 100
        
        # Mark win/loss streaks
        self.df['is_winner'] = self.df['pnl_numeric'] > 0
        self._mark_streaks()
        
        self.equity_data = self.df
    
    def _mark_streaks(self):
        """Mark winning and losing streaks in the data."""
        if len(self.df) == 0:
            return
        
        streak_id = 0
        current_streak_type = self.df['is_winner'].iloc[0]
        self.df['streak_id'] = 0
        self.df['streak_type'] = 'win' if current_streak_type else 'loss'
        
        for i in range(1, len(self.df)):
            if self.df['is_winner'].iloc[i] == current_streak_type:
                self.df.loc[self.df.index[i], 'streak_id'] = streak_id
                self.df.loc[self.df.index[i], 'streak_type'] = 'win' if current_streak_type else 'loss'
            else:
                streak_id += 1
                current_streak_type = self.df['is_winner'].iloc[i]
                self.df.loc[self.df.index[i], 'streak_id'] = streak_id
                self.df.loc[self.df.index[i], 'streak_type'] = 'win' if current_streak_type else 'loss'
    
    def generate_equity_curve_chart(self, show_streaks: bool = True, show_drawdown: bool = True) -> go.Figure:
        """
        Generate comprehensive equity curve chart.
        
        Args:
            show_streaks: Whether to color-code win/loss streaks
            show_drawdown: Whether to show drawdown subplot
        
        Returns:
            Plotly figure with equity curve
        """
        if self.equity_data is None or len(self.equity_data) == 0:
            return self._create_empty_chart()
        
        # Create subplots
        if show_drawdown:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Cumulative P&L', 'Drawdown'),
                vertical_spacing=0.1,
                row_heights=[0.7, 0.3],
                shared_xaxes=True
            )
        else:
            fig = go.Figure()
        
        # Main equity curve
        if show_streaks:
            self._add_streak_colored_equity_curve(fig, show_drawdown)
        else:
            self._add_simple_equity_curve(fig, show_drawdown)
        
        # Add drawdown if requested
        if show_drawdown:
            self._add_drawdown_chart(fig)
        
        # Update layout
        self._update_chart_layout(fig, show_drawdown)
        
        return fig
    
    def _add_streak_colored_equity_curve(self, fig: go.Figure, is_subplot: bool):
        """Add equity curve with streak coloring."""
        row = 1 if is_subplot else None
        col = 1 if is_subplot else None
        
        # Group by streaks for coloring
        for streak_id in self.equity_data['streak_id'].unique():
            streak_data = self.equity_data[self.equity_data['streak_id'] == streak_id]
            
            if len(streak_data) == 0:
                continue
            
            streak_type = streak_data['streak_type'].iloc[0]
            color = '#00CC96' if streak_type == 'win' else '#EF553B'
            
            # Create x-axis (trade numbers)
            x_values = list(range(streak_data.index[0], streak_data.index[-1] + 1))
            
            fig.add_trace(go.Scatter(
                x=x_values,
                y=streak_data['cumulative_pnl'],
                mode='lines+markers',
                line=dict(color=color, width=2),
                marker=dict(size=4, color=color),
                name=f'{streak_type.title()} Streak {streak_id}',
                showlegend=False,
                hovertemplate='<b>Trade #%{x}</b><br>' +
                             'Cumulative P&L: $%{y:,.2f}<br>' +
                             f'Streak: {streak_type.title()}<br>' +
                             '<extra></extra>'
            ), row=row, col=col)
        
        # Add overall trend line
        fig.add_trace(go.Scatter(
            x=list(range(len(self.equity_data))),
            y=self.equity_data['cumulative_pnl'],
            mode='lines',
            line=dict(color='rgba(0,0,0,0.3)', width=1, dash='dash'),
            name='Overall Trend',
            showlegend=True
        ), row=row, col=col)
    
    def _add_simple_equity_curve(self, fig: go.Figure, is_subplot: bool):
        """Add simple equity curve without streak coloring."""
        row = 1 if is_subplot else None
        col = 1 if is_subplot else None
        
        fig.add_trace(go.Scatter(
            x=list(range(len(self.equity_data))),
            y=self.equity_data['cumulative_pnl'],
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4),
            name='Cumulative P&L',
            hovertemplate='<b>Trade #%{x}</b><br>' +
                         'Cumulative P&L: $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ), row=row, col=col)
        
        # Add running maximum
        fig.add_trace(go.Scatter(
            x=list(range(len(self.equity_data))),
            y=self.equity_data['running_max'],
            mode='lines',
            line=dict(color='#ff7f0e', width=1, dash='dash'),
            name='Peak Equity',
            opacity=0.7
        ), row=row, col=col)
    
    def _add_drawdown_chart(self, fig: go.Figure):
        """Add drawdown chart to subplot."""
        fig.add_trace(go.Scatter(
            x=list(range(len(self.equity_data))),
            y=-self.equity_data['drawdown'],
            mode='lines',
            fill='tonexty',
            line=dict(color='#d62728', width=1),
            name='Drawdown',
            hovertemplate='<b>Trade #%{x}</b><br>' +
                         'Drawdown: $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ), row=2, col=1)
    
    def _update_chart_layout(self, fig: go.Figure, show_drawdown: bool):
        """Update chart layout and styling."""
        height = 600 if show_drawdown else 400
        
        fig.update_layout(
            title="Trading Performance - Equity Curve Analysis",
            xaxis_title="Trade Number",
            yaxis_title="Cumulative P&L ($)",
            hovermode='x unified',
            height=height,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        if show_drawdown:
            fig.update_xaxes(title_text="Trade Number", row=2, col=1)
            fig.update_yaxes(title_text="Drawdown ($)", row=2, col=1)
    
    def _create_empty_chart(self) -> go.Figure:
        """Create empty chart when no data is available."""
        fig = go.Figure()
        fig.add_annotation(
            text="No trade data available for equity curve",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title="Equity Curve - No Data",
            height=400
        )
        return fig
    
    def get_drawdown_analysis(self) -> Dict[str, Any]:
        """Get detailed drawdown analysis."""
        if self.equity_data is None or len(self.equity_data) == 0:
            return {}
        
        max_drawdown = self.equity_data['drawdown'].max()
        max_drawdown_percent = self.equity_data['drawdown_percent'].max()
        
        # Find drawdown periods
        drawdown_periods = []
        in_drawdown = False
        start_idx = None
        
        for idx, row in self.equity_data.iterrows():
            if row['drawdown'] > 0 and not in_drawdown:
                in_drawdown = True
                start_idx = idx
            elif row['drawdown'] == 0 and in_drawdown:
                in_drawdown = False
                if start_idx is not None:
                    drawdown_periods.append({
                        'start': start_idx,
                        'end': idx,
                        'duration': idx - start_idx,
                        'max_drawdown': self.equity_data.loc[start_idx:idx, 'drawdown'].max()
                    })
        
        # Current drawdown
        current_drawdown = self.equity_data['drawdown'].iloc[-1]
        
        return {
            'max_drawdown_dollar': max_drawdown,
            'max_drawdown_percent': max_drawdown_percent,
            'current_drawdown': current_drawdown,
            'drawdown_periods': len(drawdown_periods),
            'avg_drawdown_duration': np.mean([p['duration'] for p in drawdown_periods]) if drawdown_periods else 0,
            'longest_drawdown': max([p['duration'] for p in drawdown_periods]) if drawdown_periods else 0
        }
    
    def get_recovery_analysis(self) -> Dict[str, Any]:
        """Analyze recovery patterns after drawdowns."""
        if self.equity_data is None or len(self.equity_data) == 0:
            return {}
        
        recovery_times = []
        peak_to_peak_times = []
        
        # Find peak-to-peak recovery periods
        peaks = self.equity_data[self.equity_data['cumulative_pnl'] == self.equity_data['running_max']]
        
        for i in range(1, len(peaks)):
            peak_to_peak_times.append(peaks.index[i] - peaks.index[i-1])
        
        return {
            'avg_recovery_time': np.mean(peak_to_peak_times) if peak_to_peak_times else 0,
            'median_recovery_time': np.median(peak_to_peak_times) if peak_to_peak_times else 0,
            'longest_recovery': max(peak_to_peak_times) if peak_to_peak_times else 0,
            'recovery_periods': len(peak_to_peak_times)
        }
