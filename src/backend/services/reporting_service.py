from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date, timedelta
import logging
import json
import csv
import io
import os
import uuid
from pathlib import Path
import asyncio
from collections import defaultdict

from models.user import User
from models.trade import Trade
from models.portfolio import Portfolio
from core.exceptions import NotFoundError, ValidationError, DatabaseError
from core.config import settings
from services.analytics_service import AnalyticsService
from services.email_service import EmailService
from utils.pdf_generator import PDFReportGenerator
from utils.excel_generator import ExcelReportGenerator

logger = logging.getLogger(__name__)


class ReportingService:
    """Service for generating and managing trading reports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analytics_service = AnalyticsService(db)
        self.email_service = EmailService()
        self.pdf_generator = PDFReportGenerator()
        self.excel_generator = ExcelReportGenerator()
        self.reports_dir = Path(settings.reports_directory)
        self.reports_dir.mkdir(exist_ok=True)
    
    async def generate_report(
        self,
        user_id: int,
        report_type: str,
        start_date: date,
        end_date: date,
        filters: Dict[str, Any],
        groupings: List[str],
        metrics: List[str],
        format: str,
        include_charts: bool = True,
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """Generate a report based on specified parameters"""
        try:
            # Validate date range
            if end_date < start_date:
                raise ValidationError("End date must be after start date")
            
            # Get base data
            trades = self._get_filtered_trades(user_id, start_date, end_date, filters)
            
            if not trades:
                return {
                    "report_type": report_type,
                    "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                    "data": {},
                    "summary": {"total_trades": 0},
                    "generated_at": datetime.utcnow().isoformat()
                }
            
            # Generate report based on type
            report_data = await self._generate_report_data(
                report_type, trades, groupings, metrics, include_charts
            )
            
            # Add summary if requested
            if include_summary:
                report_data["summary"] = self._generate_summary(trades)
            
            # Add metadata
            report_data.update({
                "report_type": report_type,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "filters": filters,
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            })
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
    
    async def generate_report_file(
        self,
        user_id: int,
        report_id: str,
        request: Dict[str, Any]
    ):
        """Generate report file in background"""
        try:
            # Generate report data
            report_data = await self.generate_report(
                user_id=user_id,
                report_type=request["report_type"],
                start_date=request["start_date"],
                end_date=request["end_date"],
                filters=request.get("filters", {}),
                groupings=request.get("groupings", []),
                metrics=request.get("metrics", []),
                format="json",  # Always generate JSON first
                include_charts=request.get("include_charts", True),
                include_summary=request.get("include_summary", True)
            )
            
            # Convert to requested format
            if request["format"] == "pdf":
                file_path = await self.pdf_generator.generate(
                    report_data, 
                    report_id,
                    self.reports_dir
                )
                media_type = "application/pdf"
            elif request["format"] == "excel":
                file_path = await self.excel_generator.generate(
                    report_data,
                    report_id,
                    self.reports_dir
                )
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
            # Save report metadata
            self._save_report_metadata(
                user_id, report_id, request["report_type"], 
                file_path, media_type, report_data
            )
            
        except Exception as e:
            logger.error(f"Error generating report file: {str(e)}")
            # Save error status
            self._update_report_status(report_id, "failed", str(e))
    
    async def get_available_report_types(self, user_id: int) -> List[Dict[str, Any]]:
        """Get list of available report types"""
        report_types = [
            {
                "type": "performance",
                "name": "Performance Report",
                "description": "Comprehensive trading performance analysis",
                "available_metrics": ["pnl", "win_rate", "avg_trade", "sharpe_ratio", "max_drawdown"],
                "available_groupings": ["strategy", "symbol", "month", "day_of_week"],
                "default_format": "pdf",
                "supports_scheduling": True
            },
            {
                "type": "trade_log",
                "name": "Trade Log",
                "description": "Detailed list of all trades with entry/exit details",
                "available_metrics": ["entry_price", "exit_price", "pnl", "duration", "volume"],
                "available_groupings": ["date", "symbol", "strategy"],
                "default_format": "excel",
                "supports_scheduling": True
            },
            {
                "type": "win_loss",
                "name": "Win/Loss Analysis",
                "description": "Analysis of winning vs losing trades",
                "available_metrics": ["win_count", "loss_count", "avg_win", "avg_loss", "profit_factor"],
                "available_groupings": ["strategy", "symbol", "time_of_day"],
                "default_format": "pdf",
                "supports_scheduling": True
            },
            {
                "type": "strategy_analysis",
                "name": "Strategy Analysis",
                "description": "Performance breakdown by trading strategy",
                "available_metrics": ["total_trades", "win_rate", "pnl", "avg_duration"],
                "available_groupings": ["month", "symbol"],
                "default_format": "pdf",
                "supports_scheduling": True
            },
            {
                "type": "risk_analysis",
                "name": "Risk Analysis",
                "description": "Risk metrics and exposure analysis",
                "available_metrics": ["var", "max_drawdown", "position_sizing", "risk_reward"],
                "available_groupings": ["strategy", "symbol"],
                "default_format": "pdf",
                "supports_scheduling": False
            },
            {
                "type": "tax_report",
                "name": "Tax Report",
                "description": "Trading activity for tax purposes",
                "available_metrics": ["realized_pnl", "unrealized_pnl", "fees", "wash_sales"],
                "available_groupings": ["quarter", "symbol"],
                "default_format": "excel",
                "supports_scheduling": False
            },
            {
                "type": "monthly_summary",
                "name": "Monthly Summary",
                "description": "Monthly trading performance summary",
                "available_metrics": ["trades", "pnl", "win_rate", "best_day", "worst_day"],
                "available_groupings": ["week", "strategy"],
                "default_format": "pdf",
                "supports_scheduling": True
            },
            {
                "type": "annual_summary",
                "name": "Annual Summary",
                "description": "Yearly trading performance overview",
                "available_metrics": ["monthly_pnl", "quarterly_performance", "best_trades", "worst_trades"],
                "available_groupings": ["month", "quarter"],
                "default_format": "pdf",
                "supports_scheduling": True
            }
        ]
        
        # Check user subscription level for advanced reports
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.subscription_tier != "premium":
            # Filter out premium-only reports
            report_types = [rt for rt in report_types if rt["type"] not in ["tax_report", "risk_analysis"]]
        
        return report_types
    
    async def schedule_report(
        self,
        user_id: int,
        report_type: str,
        recurrence: str,
        delivery_time: str,
        delivery_emails: List[str],
        report_config: Dict[str, Any],
        timezone: str = "UTC",
        active: bool = True
    ) -> Dict[str, Any]:
        """Schedule a recurring report"""
        try:
            # Validate report type supports scheduling
            report_types = await self.get_available_report_types(user_id)
            report_info = next((rt for rt in report_types if rt["type"] == report_type), None)
            
            if not report_info:
                raise ValidationError(f"Invalid report type: {report_type}")
            
            if not report_info["supports_scheduling"]:
                raise ValidationError(f"Report type {report_type} does not support scheduling")
            
            # Create schedule record (would be in database)
            schedule_id = str(uuid.uuid4())
            next_run = self._calculate_next_run(recurrence, delivery_time, timezone)
            
            scheduled_report = {
                "id": schedule_id,
                "user_id": user_id,
                "report_type": report_type,
                "recurrence": recurrence,
                "delivery_time": delivery_time,
                "delivery_emails": delivery_emails,
                "report_config": report_config,
                "timezone": timezone,
                "active": active,
                "created_at": datetime.utcnow(),
                "last_run": None,
                "next_run": next_run
            }
            
            # TODO: Save to database
            
            return scheduled_report
            
        except Exception as e:
            logger.error(f"Error scheduling report: {str(e)}")
            raise
    
    async def get_scheduled_reports(
        self, 
        user_id: int, 
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get user's scheduled reports"""
        # TODO: Implement database query
        # For now, return mock data
        return []
    
    async def update_scheduled_report(
        self,
        schedule_id: str,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update scheduled report"""
        # TODO: Implement database update
        raise NotFoundError(f"Scheduled report {schedule_id} not found")
    
    async def delete_scheduled_report(
        self,
        schedule_id: str,
        user_id: int
    ):
        """Delete scheduled report"""
        # TODO: Implement database delete
        raise NotFoundError(f"Scheduled report {schedule_id} not found")
    
    async def get_report_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        report_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user's report generation history"""
        # TODO: Implement database query
        # For now, return mock data
        return {
            "items": [],
            "total": 0
        }
    
    async def get_report_file(
        self,
        report_id: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get report file info for download"""
        # TODO: Implement file retrieval
        return None
    
    def convert_to_csv(self, report_data: Dict[str, Any]) -> str:
        """Convert report data to CSV format"""
        output = io.StringIO()
        
        # Extract tabular data from report
        if "data" in report_data and isinstance(report_data["data"], list):
            if report_data["data"]:
                writer = csv.DictWriter(output, fieldnames=report_data["data"][0].keys())
                writer.writeheader()
                writer.writerows(report_data["data"])
        
        return output.getvalue()
    
    # Dashboard methods
    async def create_dashboard(
        self,
        user_id: int,
        name: str,
        description: Optional[str],
        layout: Dict[str, Any],
        is_public: bool = False,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new dashboard"""
        dashboard_id = str(uuid.uuid4())
        dashboard = {
            "id": dashboard_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "layout": layout,
            "is_public": is_public,
            "tags": tags or [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "widgets": []
        }
        # TODO: Save to database
        return dashboard
    
    async def list_dashboards(
        self,
        user_id: int,
        include_public: bool = True,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List user's dashboards"""
        # TODO: Implement database query
        return {
            "items": [],
            "total": 0
        }
    
    async def get_dashboard(
        self,
        dashboard_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Get dashboard details"""
        # TODO: Implement database query
        raise NotFoundError(f"Dashboard {dashboard_id} not found")
    
    async def update_dashboard(
        self,
        dashboard_id: str,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update dashboard"""
        # TODO: Implement database update
        raise NotFoundError(f"Dashboard {dashboard_id} not found")
    
    async def delete_dashboard(
        self,
        dashboard_id: str,
        user_id: int
    ):
        """Delete dashboard"""
        # TODO: Implement database delete
        raise NotFoundError(f"Dashboard {dashboard_id} not found")
    
    async def add_widget(
        self,
        dashboard_id: str,
        user_id: int,
        widget_type: str,
        title: str,
        config: Dict[str, Any],
        position: Dict[str, int],
        refresh_interval: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add widget to dashboard"""
        widget_id = str(uuid.uuid4())
        widget = {
            "id": widget_id,
            "dashboard_id": dashboard_id,
            "type": widget_type,
            "title": title,
            "config": config,
            "position": position,
            "refresh_interval": refresh_interval,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        # TODO: Save to database
        return widget
    
    async def update_widget(
        self,
        dashboard_id: str,
        widget_id: str,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update widget"""
        # TODO: Implement database update
        raise NotFoundError(f"Widget {widget_id} not found")
    
    async def remove_widget(
        self,
        dashboard_id: str,
        widget_id: str,
        user_id: int
    ):
        """Remove widget from dashboard"""
        # TODO: Implement database delete
        raise NotFoundError(f"Widget {widget_id} not found")
    
    # Private helper methods
    def _get_filtered_trades(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        filters: Dict[str, Any]
    ) -> List[Trade]:
        """Get trades with filters applied"""
        query = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.entry_date >= start_date,
            Trade.entry_date <= end_date
        )
        
        # Apply additional filters
        if filters.get("strategy"):
            query = query.filter(Trade.strategy == filters["strategy"])
        if filters.get("symbol"):
            query = query.filter(Trade.symbol == filters["symbol"])
        if filters.get("min_pnl") is not None:
            query = query.filter(Trade.pnl >= filters["min_pnl"])
        if filters.get("max_pnl") is not None:
            query = query.filter(Trade.pnl <= filters["max_pnl"])
        
        return query.all()
    
    async def _generate_report_data(
        self,
        report_type: str,
        trades: List[Trade],
        groupings: List[str],
        metrics: List[str],
        include_charts: bool
    ) -> Dict[str, Any]:
        """Generate report data based on type"""
        if report_type == "performance":
            return await self._generate_performance_report(trades, groupings, metrics, include_charts)
        elif report_type == "trade_log":
            return self._generate_trade_log(trades)
        elif report_type == "win_loss":
            return self._generate_win_loss_analysis(trades, groupings)
        elif report_type == "strategy_analysis":
            return self._generate_strategy_analysis(trades, groupings, metrics)
        elif report_type == "risk_analysis":
            return await self._generate_risk_analysis(trades)
        elif report_type == "tax_report":
            return self._generate_tax_report(trades)
        elif report_type == "monthly_summary":
            return self._generate_monthly_summary(trades)
        elif report_type == "annual_summary":
            return self._generate_annual_summary(trades)
        else:
            raise ValidationError(f"Unknown report type: {report_type}")
    
    async def _generate_performance_report(
        self,
        trades: List[Trade],
        groupings: List[str],
        metrics: List[str],
        include_charts: bool
    ) -> Dict[str, Any]:
        """Generate performance report"""
        data = {
            "total_trades": len(trades),
            "metrics": {},
            "groupings": {},
            "charts": {}
        }
        
        # Calculate metrics
        if "pnl" in metrics or not metrics:
            data["metrics"]["total_pnl"] = sum(t.pnl for t in trades if t.pnl)
        if "win_rate" in metrics or not metrics:
            wins = len([t for t in trades if t.pnl and t.pnl > 0])
            data["metrics"]["win_rate"] = wins / len(trades) if trades else 0
        if "avg_trade" in metrics or not metrics:
            data["metrics"]["avg_trade"] = sum(t.pnl for t in trades if t.pnl) / len(trades) if trades else 0
        
        # Apply groupings
        for grouping in groupings:
            if grouping == "strategy":
                data["groupings"]["by_strategy"] = self._group_by_strategy(trades)
            elif grouping == "symbol":
                data["groupings"]["by_symbol"] = self._group_by_symbol(trades)
            elif grouping == "month":
                data["groupings"]["by_month"] = self._group_by_month(trades)
        
        # Generate charts if requested
        if include_charts:
            data["charts"]["equity_curve"] = await self._generate_equity_curve(trades)
            data["charts"]["monthly_pnl"] = self._generate_monthly_pnl_chart(trades)
        
        return data
    
    def _generate_trade_log(self, trades: List[Trade]) -> Dict[str, Any]:
        """Generate trade log report"""
        return {
            "data": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "strategy": t.strategy,
                    "entry_date": t.entry_date.isoformat() if t.entry_date else None,
                    "exit_date": t.exit_date.isoformat() if t.exit_date else None,
                    "entry_price": float(t.entry_price) if t.entry_price else None,
                    "exit_price": float(t.exit_price) if t.exit_price else None,
                    "quantity": t.quantity,
                    "pnl": float(t.pnl) if t.pnl else None,
                    "pnl_percent": float(t.pnl_percent) if t.pnl_percent else None,
                    "fees": float(t.fees) if t.fees else None,
                    "notes": t.notes
                }
                for t in trades
            ]
        }
    
    def _generate_win_loss_analysis(
        self, 
        trades: List[Trade], 
        groupings: List[str]
    ) -> Dict[str, Any]:
        """Generate win/loss analysis"""
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl <= 0]
        
        data = {
            "summary": {
                "total_trades": len(trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": len(winning_trades) / len(trades) if trades else 0,
                "avg_win": sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
                "avg_loss": sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
                "profit_factor": abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades and sum(t.pnl for t in losing_trades) != 0 else 0
            },
            "distributions": {}
        }
        
        # Apply groupings
        for grouping in groupings:
            if grouping == "strategy":
                data["distributions"]["by_strategy"] = self._win_loss_by_strategy(trades)
            elif grouping == "symbol":
                data["distributions"]["by_symbol"] = self._win_loss_by_symbol(trades)
        
        return data
    
    def _generate_strategy_analysis(
        self,
        trades: List[Trade],
        groupings: List[str],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Generate strategy analysis report"""
        strategies = defaultdict(list)
        for trade in trades:
            if trade.strategy:
                strategies[trade.strategy].append(trade)
        
        data = {"strategies": {}}
        
        for strategy, strategy_trades in strategies.items():
            strategy_data = {
                "total_trades": len(strategy_trades),
                "metrics": {}
            }
            
            if "win_rate" in metrics or not metrics:
                wins = len([t for t in strategy_trades if t.pnl and t.pnl > 0])
                strategy_data["metrics"]["win_rate"] = wins / len(strategy_trades) if strategy_trades else 0
            
            if "pnl" in metrics or not metrics:
                strategy_data["metrics"]["total_pnl"] = sum(t.pnl for t in strategy_trades if t.pnl)
            
            if "avg_duration" in metrics or not metrics:
                durations = []
                for t in strategy_trades:
                    if t.entry_date and t.exit_date:
                        duration = (t.exit_date - t.entry_date).total_seconds() / 3600  # hours
                        durations.append(duration)
                strategy_data["metrics"]["avg_duration_hours"] = sum(durations) / len(durations) if durations else 0
            
            data["strategies"][strategy] = strategy_data
        
        return data
    
    async def _generate_risk_analysis(self, trades: List[Trade]) -> Dict[str, Any]:
        """Generate risk analysis report"""
        # This would integrate with risk calculation services
        return {
            "var_95": 0,  # Value at Risk
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "risk_per_trade": {},
            "position_sizing_analysis": {}
        }
    
    def _generate_tax_report(self, trades: List[Trade]) -> Dict[str, Any]:
        """Generate tax report"""
        return {
            "realized_gains": sum(t.pnl for t in trades if t.pnl and t.pnl > 0),
            "realized_losses": sum(t.pnl for t in trades if t.pnl and t.pnl < 0),
            "net_realized": sum(t.pnl for t in trades if t.pnl),
            "total_fees": sum(t.fees for t in trades if t.fees),
            "trades": self._generate_trade_log(trades)["data"]
        }
    
    def _generate_monthly_summary(self, trades: List[Trade]) -> Dict[str, Any]:
        """Generate monthly summary"""
        # Group trades by month
        monthly_data = defaultdict(lambda: {"trades": [], "pnl": 0, "count": 0})
        
        for trade in trades:
            if trade.entry_date:
                month_key = trade.entry_date.strftime("%Y-%m")
                monthly_data[month_key]["trades"].append(trade)
                monthly_data[month_key]["count"] += 1
                if trade.pnl:
                    monthly_data[month_key]["pnl"] += trade.pnl
        
        return {
            "months": [
                {
                    "month": month,
                    "total_trades": data["count"],
                    "total_pnl": data["pnl"],
                    "win_rate": len([t for t in data["trades"] if t.pnl and t.pnl > 0]) / data["count"] if data["count"] > 0 else 0,
                    "best_trade": max((t.pnl for t in data["trades"] if t.pnl), default=0),
                    "worst_trade": min((t.pnl for t in data["trades"] if t.pnl), default=0)
                }
                for month, data in sorted(monthly_data.items())
            ]
        }
    
    def _generate_annual_summary(self, trades: List[Trade]) -> Dict[str, Any]:
        """Generate annual summary"""
        return {
            "year_overview": {
                "total_trades": len(trades),
                "total_pnl": sum(t.pnl for t in trades if t.pnl),
                "months_traded": len(set(t.entry_date.month for t in trades if t.entry_date)),
                "best_month": {},  # Would calculate
                "worst_month": {},  # Would calculate
            },
            "quarterly_breakdown": {},  # Would calculate
            "top_10_trades": [],  # Would calculate
            "bottom_10_trades": []  # Would calculate
        }
    
    def _generate_summary(self, trades: List[Trade]) -> Dict[str, Any]:
        """Generate basic summary statistics"""
        if not trades:
            return {"total_trades": 0}
        
        wins = [t for t in trades if t.pnl and t.pnl > 0]
        losses = [t for t in trades if t.pnl and t.pnl <= 0]
        
        return {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": len(wins) / len(trades) if trades else 0,
            "total_pnl": sum(t.pnl for t in trades if t.pnl),
            "avg_win": sum(t.pnl for t in wins) / len(wins) if wins else 0,
            "avg_loss": sum(t.pnl for t in losses) / len(losses) if losses else 0,
            "best_trade": max((t.pnl for t in trades if t.pnl), default=0),
            "worst_trade": min((t.pnl for t in trades if t.pnl), default=0),
            "total_fees": sum(t.fees for t in trades if t.fees)
        }
    
    def _group_by_strategy(self, trades: List[Trade]) -> Dict[str, Any]:
        """Group trades by strategy"""
        grouped = defaultdict(list)
        for trade in trades:
            grouped[trade.strategy or "No Strategy"].append(trade)
        
        return {
            strategy: {
                "count": len(trades),
                "pnl": sum(t.pnl for t in trades if t.pnl),
                "win_rate": len([t for t in trades if t.pnl and t.pnl > 0]) / len(trades) if trades else 0
            }
            for strategy, trades in grouped.items()
        }
    
    def _group_by_symbol(self, trades: List[Trade]) -> Dict[str, Any]:
        """Group trades by symbol"""
        grouped = defaultdict(list)
        for trade in trades:
            grouped[trade.symbol].append(trade)
        
        return {
            symbol: {
                "count": len(trades),
                "pnl": sum(t.pnl for t in trades if t.pnl),
                "win_rate": len([t for t in trades if t.pnl and t.pnl > 0]) / len(trades) if trades else 0
            }
            for symbol, trades in grouped.items()
        }
    
    def _group_by_month(self, trades: List[Trade]) -> Dict[str, Any]:
        """Group trades by month"""
        grouped = defaultdict(list)
        for trade in trades:
            if trade.entry_date:
                month_key = trade.entry_date.strftime("%Y-%m")
                grouped[month_key].append(trade)
        
        return {
            month: {
                "count": len(trades),
                "pnl": sum(t.pnl for t in trades if t.pnl),
                "win_rate": len([t for t in trades if t.pnl and t.pnl > 0]) / len(trades) if trades else 0
            }
            for month, trades in sorted(grouped.items())
        }
    
    def _win_loss_by_strategy(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate win/loss by strategy"""
        grouped = defaultdict(lambda: {"wins": 0, "losses": 0})
        
        for trade in trades:
            if trade.pnl:
                strategy = trade.strategy or "No Strategy"
                if trade.pnl > 0:
                    grouped[strategy]["wins"] += 1
                else:
                    grouped[strategy]["losses"] += 1
        
        return dict(grouped)
    
    def _win_loss_by_symbol(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate win/loss by symbol"""
        grouped = defaultdict(lambda: {"wins": 0, "losses": 0})
        
        for trade in trades:
            if trade.pnl:
                if trade.pnl > 0:
                    grouped[trade.symbol]["wins"] += 1
                else:
                    grouped[trade.symbol]["losses"] += 1
        
        return dict(grouped)
    
    async def _generate_equity_curve(self, trades: List[Trade]) -> Dict[str, Any]:
        """Generate equity curve data"""
        # Sort trades by exit date
        sorted_trades = sorted(
            [t for t in trades if t.exit_date and t.pnl],
            key=lambda t: t.exit_date
        )
        
        equity_curve = []
        cumulative_pnl = 0
        
        for trade in sorted_trades:
            cumulative_pnl += trade.pnl
            equity_curve.append({
                "date": trade.exit_date.isoformat(),
                "cumulative_pnl": cumulative_pnl,
                "trade_pnl": trade.pnl
            })
        
        return {"data": equity_curve}
    
    def _generate_monthly_pnl_chart(self, trades: List[Trade]) -> Dict[str, Any]:
        """Generate monthly P&L chart data"""
        monthly_pnl = defaultdict(float)
        
        for trade in trades:
            if trade.exit_date and trade.pnl:
                month_key = trade.exit_date.strftime("%Y-%m")
                monthly_pnl[month_key] += trade.pnl
        
        return {
            "data": [
                {"month": month, "pnl": pnl}
                for month, pnl in sorted(monthly_pnl.items())
            ]
        }
    
    def _calculate_next_run(
        self, 
        recurrence: str, 
        delivery_time: str, 
        timezone: str
    ) -> datetime:
        """Calculate next run time for scheduled report"""
        # Simple implementation - would need proper timezone handling
        now = datetime.utcnow()
        hour, minute = map(int, delivery_time.split(":"))
        
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_run <= now:
            if recurrence == "daily":
                next_run += timedelta(days=1)
            elif recurrence == "weekly":
                next_run += timedelta(days=7)
            elif recurrence == "monthly":
                # Simple implementation - add 30 days
                next_run += timedelta(days=30)
        
        return next_run
    
    def _save_report_metadata(
        self,
        user_id: int,
        report_id: str,
        report_type: str,
        file_path: str,
        media_type: str,
        report_data: Dict[str, Any]
    ):
        """Save report metadata to database"""
        # TODO: Implement database save
        pass
    
    def _update_report_status(
        self,
        report_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update report generation status"""
        # TODO: Implement database update
        pass