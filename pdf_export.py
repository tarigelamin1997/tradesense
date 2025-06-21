
import streamlit as st
import pandas as pd
from fpdf import FPDF
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class TradingReportPDF:
    """Generate professional PDF reports for trading analytics."""
    
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        
    def create_report(self, trade_data: pd.DataFrame, analytics_result: dict) -> bytes:
        """Create a comprehensive trading report PDF."""
        try:
            # Cover page
            self._add_cover_page(analytics_result)
            
            # Executive summary
            self._add_executive_summary(analytics_result)
            
            # Performance metrics
            self._add_performance_metrics(analytics_result)
            
            # Trade details
            self._add_trade_details(trade_data)
            
            # Charts and visualizations
            self._add_charts_section(analytics_result)
            
            return self.pdf.output(dest='S').encode('latin-1')
            
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            raise
    
    def _add_cover_page(self, analytics_result: dict):
        """Add professional cover page."""
        self.pdf.add_page()
        
        # Header
        self.pdf.set_font('Arial', 'B', 24)
        self.pdf.set_text_color(102, 126, 234)
        self.pdf.cell(0, 20, 'TradeSense Analytics Report', 0, 1, 'C')
        
        # Subtitle
        self.pdf.set_font('Arial', '', 16)
        self.pdf.set_text_color(100, 100, 100)
        self.pdf.cell(0, 10, 'Professional Trading Performance Analysis', 0, 1, 'C')
        
        # Date
        self.pdf.ln(20)
        self.pdf.set_font('Arial', '', 12)
        self.pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'C')
        
        # Key metrics preview
        self.pdf.ln(30)
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.cell(0, 10, 'Performance Snapshot', 0, 1, 'C')
        
        self.pdf.ln(10)
        self.pdf.set_font('Arial', '', 12)
        
        metrics = [
            f"Total P&L: ${analytics_result.get('total_pnl', 0):,.2f}",
            f"Win Rate: {analytics_result.get('win_rate', 0):.1f}%",
            f"Total Trades: {analytics_result.get('total_trades', 0):,}",
            f"Profit Factor: {analytics_result.get('profit_factor', 0):.2f}"
        ]
        
        for metric in metrics:
            self.pdf.cell(0, 8, metric, 0, 1, 'C')
    
    def _add_executive_summary(self, analytics_result: dict):
        """Add executive summary page."""
        self.pdf.add_page()
        
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.set_text_color(102, 126, 234)
        self.pdf.cell(0, 12, 'Executive Summary', 0, 1)
        
        self.pdf.ln(5)
        self.pdf.set_font('Arial', '', 11)
        self.pdf.set_text_color(0, 0, 0)
        
        # Performance overview
        total_pnl = analytics_result.get('total_pnl', 0)
        win_rate = analytics_result.get('win_rate', 0)
        
        summary_text = f"""
This report analyzes your trading performance based on {analytics_result.get('total_trades', 0)} trades.

Key Findings:
• Your overall P&L is ${total_pnl:,.2f}, indicating {'profitable' if total_pnl > 0 else 'losing'} trading performance
• Win rate of {win_rate:.1f}% {'exceeds' if win_rate > 50 else 'falls below'} the 50% benchmark
• Profit factor of {analytics_result.get('profit_factor', 0):.2f} {'indicates' if analytics_result.get('profit_factor', 0) > 1 else 'suggests room for improvement in'} risk management

Risk Assessment:
• Maximum drawdown: ${analytics_result.get('max_drawdown', 0):,.2f}
• Average trade size: ${analytics_result.get('avg_trade_size', 0):,.2f}
• Risk/reward profile: {analytics_result.get('avg_win', 0) / max(analytics_result.get('avg_loss', 1), 1):.2f}:1
        """
        
        lines = summary_text.strip().split('\n')
        for line in lines:
            if line.strip():
                self.pdf.cell(0, 6, line.strip(), 0, 1)
                self.pdf.ln(2)
    
    def _add_performance_metrics(self, analytics_result: dict):
        """Add detailed performance metrics."""
        self.pdf.add_page()
        
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.set_text_color(102, 126, 234)
        self.pdf.cell(0, 12, 'Performance Metrics', 0, 1)
        
        self.pdf.ln(5)
        
        # Create metrics table
        metrics = [
            ['Metric', 'Value'],
            ['Total P&L', f"${analytics_result.get('total_pnl', 0):,.2f}"],
            ['Total Trades', f"{analytics_result.get('total_trades', 0):,}"],
            ['Winning Trades', f"{analytics_result.get('winning_trades', 0):,}"],
            ['Losing Trades', f"{analytics_result.get('losing_trades', 0):,}"],
            ['Win Rate', f"{analytics_result.get('win_rate', 0):.1f}%"],
            ['Profit Factor', f"{analytics_result.get('profit_factor', 0):.2f}"],
            ['Average Win', f"${analytics_result.get('avg_win', 0):,.2f}"],
            ['Average Loss', f"${analytics_result.get('avg_loss', 0):,.2f}"],
            ['Maximum Drawdown', f"${analytics_result.get('max_drawdown', 0):,.2f}"],
            ['Sharpe Ratio', f"{analytics_result.get('sharpe_ratio', 0):.2f}"],
        ]
        
        self.pdf.set_font('Arial', 'B', 10)
        for i, row in enumerate(metrics):
            if i == 0:  # Header
                self.pdf.set_fill_color(102, 126, 234)
                self.pdf.set_text_color(255, 255, 255)
            else:
                self.pdf.set_fill_color(245, 245, 245) if i % 2 == 0 else self.pdf.set_fill_color(255, 255, 255)
                self.pdf.set_text_color(0, 0, 0)
                
            self.pdf.cell(80, 8, row[0], 1, 0, 'L', True)
            self.pdf.cell(80, 8, row[1], 1, 1, 'R', True)
    
    def _add_trade_details(self, trade_data: pd.DataFrame):
        """Add trade details table."""
        self.pdf.add_page()
        
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.set_text_color(102, 126, 234)
        self.pdf.cell(0, 12, 'Recent Trades Summary', 0, 1)
        
        self.pdf.ln(5)
        
        # Show top 20 trades by P&L
        top_trades = trade_data.nlargest(20, 'pnl') if 'pnl' in trade_data.columns else trade_data.head(20)
        
        self.pdf.set_font('Arial', 'B', 8)
        headers = ['Symbol', 'Side', 'Quantity', 'Entry Price', 'Exit Price', 'P&L']
        
        # Header
        self.pdf.set_fill_color(102, 126, 234)
        self.pdf.set_text_color(255, 255, 255)
        for header in headers:
            self.pdf.cell(30, 6, header, 1, 0, 'C', True)
        self.pdf.ln()
        
        # Data rows
        self.pdf.set_font('Arial', '', 7)
        self.pdf.set_text_color(0, 0, 0)
        
        for i, (_, row) in enumerate(top_trades.iterrows()):
            self.pdf.set_fill_color(245, 245, 245) if i % 2 == 0 else self.pdf.set_fill_color(255, 255, 255)
            
            values = [
                str(row.get('symbol', ''))[:8],
                str(row.get('side', ''))[:4],
                str(int(row.get('quantity', 0))),
                f"${row.get('entry_price', 0):.2f}",
                f"${row.get('exit_price', 0):.2f}",
                f"${row.get('pnl', 0):.2f}"
            ]
            
            for value in values:
                self.pdf.cell(30, 6, value, 1, 0, 'C', True)
            self.pdf.ln()
    
    def _add_charts_section(self, analytics_result: dict):
        """Add charts and visualizations section."""
        self.pdf.add_page()
        
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.set_text_color(102, 126, 234)
        self.pdf.cell(0, 12, 'Performance Visualizations', 0, 1)
        
        self.pdf.ln(10)
        self.pdf.set_font('Arial', '', 11)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.cell(0, 8, 'Charts and detailed visualizations are available in the interactive dashboard.', 0, 1)
        self.pdf.cell(0, 8, 'Visit TradeSense app for real-time chart analysis and performance tracking.', 0, 1)


def render_pdf_export_ui(trade_data: pd.DataFrame, analytics_result: dict):
    """Render PDF export interface."""
    st.subheader("📄 Export Analytics Report")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Generate a comprehensive PDF report of your trading performance")
        st.write("**Includes:**")
        st.write("• Executive summary and key findings")
        st.write("• Detailed performance metrics")
        st.write("• Trade history and analysis")
        st.write("• Professional formatting for sharing")
    
    with col2:
        if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
            try:
                with st.spinner("Generating PDF report..."):
                    report_generator = TradingReportPDF()
                    pdf_bytes = report_generator.create_report(trade_data, analytics_result)
                    
                    # Create download button
                    st.download_button(
                        label="⬇️ Download Report",
                        data=pdf_bytes,
                        file_name=f"TradeSense_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                show_toast("PDF report generated successfully!")
                
            except Exception as e:
                logger.error(f"PDF export error: {e}")
                st.error("Failed to generate PDF report. Please try again.")
