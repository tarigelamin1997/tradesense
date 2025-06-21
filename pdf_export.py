#!/usr/bin/env python3
"""
PDF Export System
Professional PDF generation for trading analytics reports
"""

import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import io
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

class TradingReportPDF(FPDF):
    """Custom PDF class for trading reports with enhanced styling."""

    def __init__(self, theme='light'):
        super().__init__()
        self.theme = theme
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        """Add professional header to each page."""
        # Logo area (simplified)
        self.set_font('Arial', 'B', 20)
        self.set_text_color(66, 139, 202)  # Professional blue
        self.cell(0, 15, '📊 TradeSense Analytics Report', 0, 1, 'C')

        self.set_text_color(0, 0, 0)  # Reset to black
        self.set_font('Arial', '', 10)
        self.cell(0, 8, f'Professional Trading Performance Analysis', 0, 1, 'C')

        # Line separator
        self.set_draw_color(66, 139, 202)
        self.line(10, 35, 200, 35)
        self.ln(10)

    def footer(self):
        """Add professional footer to each page."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Page {self.page_no()} | TradeSense Platform', 0, 0, 'C')

    def chapter_title(self, title):
        """Add chapter title with styling."""
        self.set_font('Arial', 'B', 16)
        self.set_text_color(66, 139, 202)
        self.cell(0, 12, title, 0, 1, 'L')
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def add_metric_box(self, title, value, x, y, width=45, height=25, color=(66, 139, 202)):
        """Add styled metric box."""
        # Save current position
        curr_x, curr_y = self.get_x(), self.get_y()

        # Draw box
        self.set_xy(x, y)
        self.set_draw_color(*color)
        self.set_line_width(0.5)
        self.rect(x, y, width, height)

        # Add title
        self.set_xy(x + 2, y + 3)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(80, 80, 80)
        self.cell(width - 4, 6, title, 0, 1, 'C')

        # Add value
        self.set_xy(x + 2, y + 12)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(*color)
        self.cell(width - 4, 8, str(value), 0, 1, 'C')

        # Restore position and color
        self.set_xy(curr_x, curr_y)
        self.set_text_color(0, 0, 0)

def render_pdf_export_button(data, stats):
    """Render enhanced PDF export button with theme options."""
    st.subheader("📄 Export Professional Report")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Theme selection for PDF
        pdf_theme = st.radio(
            "PDF Theme",
            options=['light', 'dark'],
            format_func=lambda x: f"{'☀️' if x == 'light' else '🌙'} {x.title()} Theme",
            horizontal=True,
            key="pdf_theme_selector"
        )

    with col2:
        # Preview option
        if st.button("👁️ Preview PDF", help="Preview before downloading"):
            st.info("PDF preview functionality coming soon!")

    # Main export button
    if st.button("📄 Generate & Download PDF Report", type="primary", use_container_width=True):
        try:
            with st.spinner("🔄 Generating professional PDF report..."):
                pdf_buffer = generate_enhanced_trading_report_pdf(data, stats, pdf_theme)

                if pdf_buffer:
                    # Create download button
                    filename = f"TradeSense_Analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_buffer,
                        file_name=filename,
                        mime="application/pdf",
                        key="pdf_download",
                        use_container_width=True
                    )

                    # Success toast
                    st.success("✅ PDF report generated successfully!")
                    st.balloons()
                else:
                    st.error("❌ Failed to generate PDF report")

        except Exception as e:
            logger.error(f"PDF export error: {e}")
            st.error(f"Error generating PDF: {str(e)}")

def generate_enhanced_trading_report_pdf(data, stats, theme='light'):
    """Generate comprehensive and professional trading analytics PDF report."""
    try:
        pdf = TradingReportPDF(theme=theme)
        pdf.add_page()

        # Title section with enhanced styling
        pdf.set_font('Arial', 'B', 28)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 20, 'Trading Performance Report', 0, 1, 'C')

        pdf.set_font('Arial', '', 14)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f'Analysis Period: {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'C')
        pdf.ln(20)

        # Executive Summary with metric boxes
        pdf.chapter_title('📊 Executive Summary')

        # Calculate position for metric boxes (3x3 grid)
        start_x = 15
        start_y = pdf.get_y() + 5
        box_width = 55
        box_height = 30
        spacing = 5

        # Row 1
        pdf.add_metric_box('Total Trades', f"{stats.get('total_trades', 0):,}", 
                          start_x, start_y, box_width, box_height)
        pdf.add_metric_box('Win Rate', f"{stats.get('win_rate', 0):.1f}%", 
                          start_x + box_width + spacing, start_y, box_width, box_height, 
                          (39, 174, 96) if stats.get('win_rate', 0) > 50 else (231, 76, 60))
        pdf.add_metric_box('Net P&L', f"${stats.get('total_pnl', 0):,.0f}", 
                          start_x + 2*(box_width + spacing), start_y, box_width, box_height,
                          (39, 174, 96) if stats.get('total_pnl', 0) > 0 else (231, 76, 60))

        # Row 2
        row2_y = start_y + box_height + spacing
        profit_factor = stats.get('profit_factor', 0)
        pf_display = "∞" if profit_factor == float('inf') else f"{profit_factor:.2f}"
        pdf.add_metric_box('Profit Factor', pf_display, 
                          start_x, row2_y, box_width, box_height,
                          (39, 174, 96) if profit_factor > 1.5 else (231, 76, 60))
        pdf.add_metric_box('Best Trade', f"${stats.get('best_trade', 0):,.0f}", 
                          start_x + box_width + spacing, row2_y, box_width, box_height, (39, 174, 96))
        pdf.add_metric_box('Avg Duration', f"{stats.get('avg_trade_duration', 0):.1f}h", 
                          start_x + 2*(box_width + spacing), row2_y, box_width, box_height)

        # Move cursor below boxes
        pdf.set_y(row2_y + box_height + 15)

        # Performance Analysis Section
        pdf.chapter_title('📈 Performance Analysis')

        pdf.set_font('Arial', '', 11)

        # Dynamic analysis based on performance
        win_rate = stats.get('win_rate', 0)
        profit_factor = stats.get('profit_factor', 0)
        total_pnl = stats.get('total_pnl', 0)

        if win_rate > 60 and profit_factor > 2.0 and total_pnl > 0:
            analysis = """EXCELLENT PERFORMANCE: Your trading strategy demonstrates exceptional profitability with a high win rate and strong profit factor. The consistent positive returns indicate robust risk management and effective trade selection. Consider scaling your strategy while maintaining current risk parameters."""

        elif win_rate > 50 and profit_factor > 1.5:
            analysis = """GOOD PERFORMANCE: Your strategy shows solid profitability metrics with room for optimization. The positive profit factor indicates effective risk-reward management. Focus on improving trade selection criteria and consider position sizing adjustments to enhance returns."""

        elif win_rate > 40 or profit_factor > 1.2:
            analysis = """ACCEPTABLE PERFORMANCE: Your trading shows potential but requires improvement in key areas. Consider reviewing your entry and exit criteria, implementing stricter risk management rules, and focusing on high-probability setups to improve overall performance."""

        else:
            analysis = """PERFORMANCE REQUIRES ATTENTION: Current metrics indicate significant room for improvement. Recommend comprehensive strategy review, enhanced risk management implementation, and potentially seeking additional education or mentorship to improve trading outcomes."""

        pdf.multi_cell(0, 7, analysis)
        pdf.ln(10)

        # Risk Assessment Section
        pdf.chapter_title('⚠️ Risk Assessment')

        # Risk analysis
        max_loss = abs(stats.get('worst_trade', 0))
        avg_loss = abs(stats.get('total_pnl', 0) / max(stats.get('losing_trades', 1), 1)) if stats.get('losing_trades', 0) > 0 else 0

        risk_text = f"""Maximum Single Loss: ${max_loss:,.2f}
Average Loss per Losing Trade: ${avg_loss:,.2f}
Risk Management Assessment: {'Conservative' if max_loss < 1000 else 'Moderate' if max_loss < 5000 else 'Aggressive'}

Recommendations: Monitor position sizing relative to account size and implement stop-loss orders to limit downside risk."""

        pdf.multi_cell(0, 6, risk_text)
        pdf.ln(10)

        # Add new page for trade details
        pdf.add_page()

        # Trade History Table
        pdf.chapter_title('📋 Recent Trade History')

        if len(data) > 0:
            # Enhanced table headers
            pdf.set_font('Arial', 'B', 10)
            pdf.set_fill_color(66, 139, 202)
            pdf.set_text_color(255, 255, 255)

            col_widths = [25, 20, 25, 25, 25, 30, 35]
            headers = ['Symbol', 'Dir', 'Entry', 'Exit', 'Qty', 'P&L', 'Date']

            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1, 0, 'C', fill=True)
            pdf.ln()

            # Table data (last 25 trades)
            pdf.set_font('Arial', '', 8)
            pdf.set_text_color(0, 0, 0)
            recent_trades = data.tail(25) if len(data) > 25 else data

            for idx, (_, trade) in enumerate(recent_trades.iterrows()):
                # Alternate row colors
                if idx % 2 == 0:
                    pdf.set_fill_color(245, 245, 245)
                    fill = True
                else:
                    fill = False

                # Format data
                pnl = trade.get('pnl', 0)
                pnl_color = (39, 174, 96) if pnl > 0 else (231, 76, 60) if pnl < 0 else (0, 0, 0)

                row_data = [
                    str(trade.get('symbol', 'N/A'))[:8],
                    str(trade.get('direction', 'N/A'))[:4],
                    f"${trade.get('entry_price', 0):.2f}"[:12],
                    f"${trade.get('exit_price', 0):.2f}"[:12],
                    str(trade.get('qty', 0))[:8],
                    f"${pnl:.2f}"[:12],
                    str(trade.get('date', 'N/A'))[:14]
                ]

                # Draw cells
                for i, cell_data in enumerate(row_data):
                    if i == 5:  # P&L column
                        pdf.set_text_color(*pnl_color)
                    else:
                        pdf.set_text_color(0, 0, 0)

                    pdf.cell(col_widths[i], 8, cell_data, 1, 0, 'C', fill=fill)
                pdf.ln()

        # Footer section
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 6, """
This report is generated by TradeSense Analytics Platform. All calculations are based on the provided trade data. 
Past performance does not guarantee future results. Please ensure all data accuracy before making trading decisions.

For support or questions, visit: tradesense.io/support
        """)

        # Generate and return PDF
        pdf_buffer = io.BytesIO()
        pdf_string = pdf.output(dest='S').encode('latin-1')
        pdf_buffer.write(pdf_string)
        pdf_buffer.seek(0)

        return pdf_buffer.getvalue()

    except Exception as e:
        logger.error(f"Enhanced PDF generation error: {e}")
        return None