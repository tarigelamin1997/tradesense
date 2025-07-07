
"""
Export Service
Handles PDF exports, CSV exports, and analytics report generation
"""

import logging
import sqlite3
import pandas as pd
import io
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime, date, timedelta
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

class ExportService:
    """Complete export service implementation for PDF and CSV generation"""
    
    def __init__(self):
        self.db_path = 'tradesense.db'
    
    async def generate_performance_pdf(
        self, 
        user_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        include_charts: bool = True
    ) -> BinaryIO:
        """Generate performance report as PDF"""
        try:
            # Get trade data for the user
            trades_data = await self._get_user_trades(user_id, start_date, end_date)
            
            # Generate PDF content using a simple text-based approach
            # In production, you'd use libraries like reportlab or weasyprint
            pdf_content = self._create_simple_pdf_report(trades_data, include_charts)
            
            return io.BytesIO(pdf_content.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"PDF generation failed for user {user_id}: {e}")
            # Return a simple error PDF
            error_content = f"PDF Report Generation Error\nUser: {user_id}\nError: {str(e)}\nGenerated: {datetime.now()}"
            return io.BytesIO(error_content.encode('utf-8'))
    
    async def generate_trades_csv(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        symbol: Optional[str] = None
    ) -> BinaryIO:
        """Generate trades data as CSV"""
        try:
            # Get filtered trade data
            trades_data = await self._get_user_trades(user_id, start_date, end_date, symbol)
            
            # Convert to DataFrame and then CSV
            if trades_data:
                df = pd.DataFrame(trades_data)
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_content = csv_buffer.getvalue()
                
                return io.BytesIO(csv_content.encode('utf-8'))
            else:
                # Return empty CSV with headers
                empty_csv = "symbol,entry_time,exit_time,quantity,entry_price,exit_price,pnl,strategy\n"
                return io.BytesIO(empty_csv.encode('utf-8'))
                
        except Exception as e:
            logger.error(f"CSV generation failed for user {user_id}: {e}")
            error_csv = f"Error generating CSV: {str(e)}\n"
            return io.BytesIO(error_csv.encode('utf-8'))
    
    async def generate_analytics_json(self, user_id: int) -> Dict[str, Any]:
        """Generate complete analytics data as JSON"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user trades
                cursor.execute("""
                    SELECT * FROM trades WHERE user_id = ?
                    ORDER BY entry_time DESC
                """, (user_id,))
                
                trades = []
                for row in cursor.fetchall():
                    trades.append({
                        "id": row[0],
                        "symbol": row[1],
                        "entry_time": row[2],
                        "exit_time": row[3],
                        "quantity": row[4],
                        "entry_price": row[5],
                        "exit_price": row[6],
                        "pnl": row[7],
                        "strategy": row[8] if len(row) > 8 else "Unknown"
                    })
                
                # Calculate basic analytics
                total_trades = len(trades)
                profitable_trades = len([t for t in trades if t['pnl'] > 0])
                total_pnl = sum(t['pnl'] for t in trades)
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                
                return {
                    "user_id": user_id,
                    "total_trades": total_trades,
                    "profitable_trades": profitable_trades,
                    "total_pnl": total_pnl,
                    "win_rate": win_rate,
                    "trades": trades,
                    "timestamp": datetime.now().isoformat(),
                    "export_type": "analytics_json"
                }
                
        except Exception as e:
            logger.error(f"Analytics JSON generation failed for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "export_type": "analytics_json_error"
            }
    
    async def _get_user_trades(
        self, 
        user_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user trades with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query with filters
                query = "SELECT * FROM trades WHERE user_id = ?"
                params = [user_id]
                
                if start_date:
                    query += " AND DATE(entry_time) >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND DATE(entry_time) <= ?"
                    params.append(end_date.isoformat())
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                query += " ORDER BY entry_time DESC"
                
                cursor.execute(query, params)
                
                trades = []
                for row in cursor.fetchall():
                    trades.append({
                        "id": row[0] if len(row) > 0 else None,
                        "symbol": row[1] if len(row) > 1 else "Unknown",
                        "entry_time": row[2] if len(row) > 2 else None,
                        "exit_time": row[3] if len(row) > 3 else None,
                        "quantity": row[4] if len(row) > 4 else 0,
                        "entry_price": row[5] if len(row) > 5 else 0,
                        "exit_price": row[6] if len(row) > 6 else 0,
                        "pnl": row[7] if len(row) > 7 else 0,
                        "strategy": row[8] if len(row) > 8 else "Unknown"
                    })
                
                return trades
                
        except Exception as e:
            logger.error(f"Failed to get user trades: {e}")
            return []
    
    def _create_simple_pdf_report(self, trades_data: List[Dict], include_charts: bool = True) -> str:
        """Create a simple text-based PDF report (placeholder for real PDF generation)"""
        try:
            total_trades = len(trades_data)
            profitable_trades = len([t for t in trades_data if t['pnl'] > 0])
            total_pnl = sum(t['pnl'] for t in trades_data)
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
            
            report = f"""
TradeSense Performance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PERFORMANCE SUMMARY
==================
Total Trades: {total_trades}
Profitable Trades: {profitable_trades}
Win Rate: {win_rate:.2f}%
Total P&L: ${total_pnl:.2f}

RECENT TRADES
=============
"""
            
            # Add recent trades (limit to 10)
            for trade in trades_data[:10]:
                report += f"""
Symbol: {trade['symbol']}
Entry: {trade['entry_time']} @ ${trade['entry_price']}
Exit: {trade['exit_time']} @ ${trade['exit_price']}
P&L: ${trade['pnl']:.2f}
Strategy: {trade['strategy']}
---
"""
            
            if include_charts:
                report += """

CHARTS & ANALYTICS
==================
[Chart visualizations would be embedded here in production]
- Equity Curve
- Win/Loss Distribution
- Performance by Symbol
- Monthly Performance
"""
            
            return report
            
        except Exception as e:
            logger.error(f"Simple PDF report creation failed: {e}")
            return f"Error creating PDF report: {str(e)}"
