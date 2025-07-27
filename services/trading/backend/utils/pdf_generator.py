from typing import Dict, Any
from pathlib import Path
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart
import io

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate PDF reports from report data"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=1  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.gray
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))
    
    async def generate(
        self, 
        report_data: Dict[str, Any], 
        report_id: str,
        output_dir: Path
    ) -> str:
        """Generate PDF report and return file path"""
        try:
            filename = f"report_{report_id}.pdf"
            file_path = output_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )
            
            # Build content
            story = []
            
            # Title page
            story.extend(self._create_title_page(report_data))
            
            # Summary section
            if "summary" in report_data:
                story.extend(self._create_summary_section(report_data["summary"]))
            
            # Performance metrics
            if "data" in report_data and "metrics" in report_data["data"]:
                story.extend(self._create_metrics_section(report_data["data"]["metrics"]))
            
            # Charts
            if "data" in report_data and "charts" in report_data["data"]:
                story.extend(self._create_charts_section(report_data["data"]["charts"]))
            
            # Detailed data tables
            if "data" in report_data and "groupings" in report_data["data"]:
                story.extend(self._create_groupings_section(report_data["data"]["groupings"]))
            
            # Trade log
            if report_data.get("report_type") == "trade_log" and "data" in report_data:
                story.extend(self._create_trade_log_section(report_data["data"]))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _create_title_page(self, report_data: Dict[str, Any]) -> list:
        """Create title page elements"""
        elements = []
        
        # Report title
        report_type = report_data.get("report_type", "Report").replace("_", " ").title()
        title = Paragraph(f"{report_type}", self.styles['CustomTitle'])
        elements.append(title)
        
        # Date range
        if "period" in report_data:
            period_text = f"{report_data['period']['start']} to {report_data['period']['end']}"
            period = Paragraph(period_text, self.styles['Normal'])
            elements.append(period)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Generated timestamp
        generated_at = report_data.get("generated_at", datetime.utcnow().isoformat())
        timestamp = Paragraph(f"Generated: {generated_at}", self.styles['Normal'])
        elements.append(timestamp)
        
        elements.append(PageBreak())
        
        return elements
    
    def _create_summary_section(self, summary: Dict[str, Any]) -> list:
        """Create summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Create summary table
        data = []
        for key, value in summary.items():
            label = key.replace("_", " ").title()
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
            data.append([label, formatted_value])
        
        if data:
            table = Table(data, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            elements.append(table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        return elements
    
    def _create_metrics_section(self, metrics: Dict[str, Any]) -> list:
        """Create metrics section"""
        elements = []
        
        elements.append(Paragraph("Key Metrics", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Create metrics grid
        metric_items = []
        for key, value in metrics.items():
            label = key.replace("_", " ").title()
            if isinstance(value, float):
                if "rate" in key or "percent" in key:
                    formatted_value = f"{value*100:.1f}%"
                else:
                    formatted_value = f"${value:,.2f}" if "pnl" in key else f"{value:.2f}"
            else:
                formatted_value = str(value)
            
            metric_items.append([
                Paragraph(label, self.styles['MetricLabel']),
                Paragraph(formatted_value, self.styles['MetricValue'])
            ])
        
        if metric_items:
            # Arrange in 2 columns
            rows = []
            for i in range(0, len(metric_items), 2):
                row = metric_items[i:i+2]
                if len(row) == 1:
                    row.append(["", ""])  # Empty cell
                rows.append([item for sublist in row for item in sublist])
            
            table = Table(rows, colWidths=[2*inch, 1.5*inch, 2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        return elements
    
    def _create_charts_section(self, charts: Dict[str, Any]) -> list:
        """Create charts section"""
        elements = []
        
        elements.append(Paragraph("Performance Charts", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Placeholder for actual chart generation
        # In production, would use matplotlib or similar to generate chart images
        elements.append(Paragraph("Charts would be rendered here", self.styles['Normal']))
        
        elements.append(PageBreak())
        
        return elements
    
    def _create_groupings_section(self, groupings: Dict[str, Any]) -> list:
        """Create groupings section with tables"""
        elements = []
        
        for grouping_name, grouping_data in groupings.items():
            title = grouping_name.replace("_", " ").title()
            elements.append(Paragraph(title, self.styles['SectionHeader']))
            elements.append(Spacer(1, 0.1*inch))
            
            # Create table for grouping data
            if isinstance(grouping_data, dict):
                data = [["Group", "Count", "P&L", "Win Rate"]]
                for group, stats in grouping_data.items():
                    row = [
                        group,
                        str(stats.get("count", 0)),
                        f"${stats.get('pnl', 0):,.2f}",
                        f"{stats.get('win_rate', 0)*100:.1f}%"
                    ]
                    data.append(row)
                
                if len(data) > 1:
                    table = Table(data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(table)
            
            elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_trade_log_section(self, trades_data: Any) -> list:
        """Create trade log section"""
        elements = []
        
        elements.append(Paragraph("Trade Log", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        if isinstance(trades_data, dict) and "data" in trades_data:
            trades = trades_data["data"]
        elif isinstance(trades_data, list):
            trades = trades_data
        else:
            trades = []
        
        if trades:
            # Create table headers
            headers = ["Symbol", "Entry Date", "Exit Date", "Entry Price", "Exit Price", "P&L"]
            data = [headers]
            
            # Add trade rows (limit to prevent huge PDFs)
            for trade in trades[:100]:  # Limit to first 100 trades
                row = [
                    trade.get("symbol", ""),
                    trade.get("entry_date", "")[:10] if trade.get("entry_date") else "",
                    trade.get("exit_date", "")[:10] if trade.get("exit_date") else "",
                    f"${trade.get('entry_price', 0):.2f}" if trade.get("entry_price") else "",
                    f"${trade.get('exit_price', 0):.2f}" if trade.get("exit_price") else "",
                    f"${trade.get('pnl', 0):.2f}" if trade.get("pnl") is not None else ""
                ]
                data.append(row)
            
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                # Color code P&L
                ('TEXTCOLOR', (5, 1), (5, -1), colors.green),
            ]))
            
            # Apply red color to negative P&L
            for i in range(1, len(data)):
                if i < len(trades) and trades[i-1].get("pnl", 0) < 0:
                    table.setStyle(TableStyle([
                        ('TEXTCOLOR', (5, i), (5, i), colors.red)
                    ]))
            
            elements.append(table)
            
            if len(trades) > 100:
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph(
                    f"Note: Showing first 100 of {len(trades)} trades", 
                    self.styles['Normal']
                ))
        
        return elements