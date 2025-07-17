"""
Dashboard Builder Service

Comprehensive dashboard management system with support for:
- Multiple dashboard templates
- Drag-and-drop widgets
- Real-time data updates
- Caching and performance optimization
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import asyncio
import hashlib
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np
from redis import Redis
import logging

from core.db.session import get_db
from models.user import User
from models.trade import Trade
from models.portfolio import Portfolio
from models.trading_account import TradingAccount
from services.analytics_service import AnalyticsService
from services.market_data_service import MarketDataService
from core.redis import get_redis
from core.config import settings

logger = logging.getLogger(__name__)


# Enums
class DashboardTemplate(str, Enum):
    """Pre-defined dashboard templates"""
    DAY_TRADING = "day_trading"
    SWING_TRADING = "swing_trading"
    OPTIONS = "options"
    CRYPTO = "crypto"
    FOREX = "forex"
    CUSTOM = "custom"


class WidgetType(str, Enum):
    """Available widget types"""
    # Charts
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    CANDLESTICK = "candlestick"
    HEATMAP = "heatmap"
    
    # Metrics
    METRIC_CARD = "metric_card"
    GAUGE = "gauge"
    
    # Tables
    TABLE = "table"
    
    # Special widgets
    TEXT_MARKDOWN = "text_markdown"
    LIVE_MARKET = "live_market"
    PNL_CALENDAR = "pnl_calendar"
    WIN_RATE_GAUGE = "win_rate_gauge"
    DRAWDOWN_CHART = "drawdown_chart"
    TRADE_DISTRIBUTION_MAP = "trade_distribution_map"


class DataSource(str, Enum):
    """Data sources for widgets"""
    TRADES = "trades"
    PORTFOLIO = "portfolio"
    MARKET_DATA = "market_data"
    CUSTOM_CALCULATION = "custom_calculation"
    EXTERNAL_API = "external_api"


# Pydantic Models
class WidgetPosition(BaseModel):
    """Widget position in grid layout"""
    x: int = Field(..., ge=0, le=11)
    y: int = Field(..., ge=0)
    width: int = Field(..., ge=1, le=12)
    height: int = Field(..., ge=1)


class WidgetConfig(BaseModel):
    """Widget configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: WidgetType
    title: str
    position: WidgetPosition
    data_source: DataSource
    data_config: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = Field(default=300, ge=0)  # seconds, 0 = no auto refresh
    interactive: bool = True
    exportable: bool = True
    linked_widgets: List[str] = Field(default_factory=list)
    custom_styles: Dict[str, Any] = Field(default_factory=dict)


class DashboardLayout(BaseModel):
    """Dashboard layout configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    columns: int = Field(default=12, ge=1, le=24)
    row_height: int = Field(default=60, ge=20)
    margin: List[int] = Field(default=[10, 10])
    responsive_breakpoints: Dict[str, int] = Field(
        default_factory=lambda: {"lg": 1200, "md": 996, "sm": 768, "xs": 480}
    )


class Dashboard(BaseModel):
    """Dashboard model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    template: DashboardTemplate = DashboardTemplate.CUSTOM
    layout: DashboardLayout
    widgets: List[WidgetConfig] = Field(default_factory=list)
    shared_with: List[str] = Field(default_factory=list)  # user IDs
    is_public: bool = False
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)


class DashboardFilter(BaseModel):
    """Dashboard filter criteria"""
    user_id: Optional[str] = None
    template: Optional[DashboardTemplate] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    search_term: Optional[str] = None


class WidgetDataRequest(BaseModel):
    """Request for widget data"""
    widget_id: str
    dashboard_id: str
    user_id: str
    time_range: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    page: int = 1
    page_size: int = 100


class DashboardService:
    """Service for managing dashboards and widgets"""
    
    def __init__(self, db: Session, redis: Optional[Redis] = None):
        self.db = db
        self.redis = redis or get_redis()
        self.analytics_service = AnalyticsService(db)
        self.market_data_service = MarketDataService(db)
        self._cache_ttl = 300  # 5 minutes default cache
        
    # Dashboard Management
    def create_dashboard(
        self, 
        user_id: str, 
        name: str, 
        template: DashboardTemplate = DashboardTemplate.CUSTOM,
        description: Optional[str] = None
    ) -> Dashboard:
        """Create a new dashboard"""
        try:
            # Create layout based on template
            layout = self._get_template_layout(template)
            
            # Create dashboard
            dashboard = Dashboard(
                user_id=user_id,
                name=name,
                description=description,
                template=template,
                layout=layout,
                widgets=self._get_template_widgets(template)
            )
            
            # Save to database (assuming we have a Dashboard model)
            self._save_dashboard(dashboard)
            
            logger.info(f"Created dashboard {dashboard.id} for user {user_id}")
            return dashboard
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            raise
    
    def update_dashboard(
        self, 
        dashboard_id: str, 
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dashboard:
        """Update dashboard configuration"""
        try:
            dashboard = self._get_dashboard(dashboard_id, user_id)
            if not dashboard:
                raise ValueError("Dashboard not found")
            
            # Update allowed fields
            allowed_fields = ["name", "description", "layout", "tags", "is_public"]
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(dashboard, field, value)
            
            dashboard.updated_at = datetime.utcnow()
            self._save_dashboard(dashboard)
            
            # Invalidate cache
            self._invalidate_dashboard_cache(dashboard_id)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            raise
    
    def delete_dashboard(self, dashboard_id: str, user_id: str) -> bool:
        """Delete a dashboard"""
        try:
            dashboard = self._get_dashboard(dashboard_id, user_id)
            if not dashboard:
                return False
            
            # Remove from cache
            self._invalidate_dashboard_cache(dashboard_id)
            
            # Delete from storage
            self._delete_dashboard(dashboard_id)
            
            logger.info(f"Deleted dashboard {dashboard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting dashboard: {e}")
            raise
    
    def clone_dashboard(
        self, 
        dashboard_id: str, 
        user_id: str,
        new_name: str
    ) -> Dashboard:
        """Clone an existing dashboard"""
        try:
            original = self._get_dashboard(dashboard_id, user_id)
            if not original:
                raise ValueError("Dashboard not found")
            
            # Create clone
            cloned = Dashboard(
                user_id=user_id,
                name=new_name,
                description=f"Cloned from {original.name}",
                template=original.template,
                layout=original.layout.model_copy(),
                widgets=[w.model_copy() for w in original.widgets],
                tags=original.tags.copy()
            )
            
            # Generate new IDs
            cloned.id = str(uuid.uuid4())
            for widget in cloned.widgets:
                widget.id = str(uuid.uuid4())
            
            self._save_dashboard(cloned)
            
            logger.info(f"Cloned dashboard {dashboard_id} to {cloned.id}")
            return cloned
            
        except Exception as e:
            logger.error(f"Error cloning dashboard: {e}")
            raise
    
    def share_dashboard(
        self, 
        dashboard_id: str, 
        owner_id: str,
        share_with: List[str]
    ) -> Dashboard:
        """Share dashboard with other users"""
        try:
            dashboard = self._get_dashboard(dashboard_id, owner_id)
            if not dashboard:
                raise ValueError("Dashboard not found")
            
            dashboard.shared_with = list(set(dashboard.shared_with + share_with))
            dashboard.updated_at = datetime.utcnow()
            
            self._save_dashboard(dashboard)
            
            # Notify shared users
            for user_id in share_with:
                self._notify_dashboard_shared(user_id, dashboard)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error sharing dashboard: {e}")
            raise
    
    def list_dashboards(
        self, 
        filter_criteria: DashboardFilter,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dashboard], int]:
        """List dashboards with filtering"""
        try:
            # This would query from actual storage
            dashboards = self._query_dashboards(filter_criteria, page, page_size)
            total = self._count_dashboards(filter_criteria)
            
            return dashboards, total
            
        except Exception as e:
            logger.error(f"Error listing dashboards: {e}")
            raise
    
    # Widget Management
    def add_widget(
        self, 
        dashboard_id: str, 
        user_id: str,
        widget_config: WidgetConfig
    ) -> Dashboard:
        """Add a widget to dashboard"""
        try:
            dashboard = self._get_dashboard(dashboard_id, user_id)
            if not dashboard:
                raise ValueError("Dashboard not found")
            
            # Validate position doesn't overlap
            if self._check_widget_overlap(dashboard.widgets, widget_config.position):
                raise ValueError("Widget position overlaps with existing widget")
            
            dashboard.widgets.append(widget_config)
            dashboard.updated_at = datetime.utcnow()
            
            self._save_dashboard(dashboard)
            self._invalidate_dashboard_cache(dashboard_id)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error adding widget: {e}")
            raise
    
    def update_widget(
        self, 
        dashboard_id: str, 
        widget_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dashboard:
        """Update widget configuration"""
        try:
            dashboard = self._get_dashboard(dashboard_id, user_id)
            if not dashboard:
                raise ValueError("Dashboard not found")
            
            # Find widget
            widget = next((w for w in dashboard.widgets if w.id == widget_id), None)
            if not widget:
                raise ValueError("Widget not found")
            
            # Update widget
            for field, value in updates.items():
                if hasattr(widget, field):
                    setattr(widget, field, value)
            
            dashboard.updated_at = datetime.utcnow()
            self._save_dashboard(dashboard)
            
            # Invalidate widget data cache
            self._invalidate_widget_cache(dashboard_id, widget_id)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error updating widget: {e}")
            raise
    
    def remove_widget(
        self, 
        dashboard_id: str, 
        widget_id: str,
        user_id: str
    ) -> Dashboard:
        """Remove widget from dashboard"""
        try:
            dashboard = self._get_dashboard(dashboard_id, user_id)
            if not dashboard:
                raise ValueError("Dashboard not found")
            
            dashboard.widgets = [w for w in dashboard.widgets if w.id != widget_id]
            dashboard.updated_at = datetime.utcnow()
            
            self._save_dashboard(dashboard)
            self._invalidate_widget_cache(dashboard_id, widget_id)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error removing widget: {e}")
            raise
    
    def reorder_widgets(
        self, 
        dashboard_id: str, 
        user_id: str,
        widget_positions: List[Dict[str, Any]]
    ) -> Dashboard:
        """Reorder widgets with new positions"""
        try:
            dashboard = self._get_dashboard(dashboard_id, user_id)
            if not dashboard:
                raise ValueError("Dashboard not found")
            
            # Update positions
            position_map = {p["widget_id"]: p["position"] for p in widget_positions}
            
            for widget in dashboard.widgets:
                if widget.id in position_map:
                    widget.position = WidgetPosition(**position_map[widget.id])
            
            dashboard.updated_at = datetime.utcnow()
            self._save_dashboard(dashboard)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error reordering widgets: {e}")
            raise
    
    # Widget Data
    async def get_widget_data(
        self, 
        request: WidgetDataRequest
    ) -> Dict[str, Any]:
        """Get data for a specific widget"""
        try:
            # Check cache first
            cache_key = self._get_widget_cache_key(request)
            cached = self._get_cached_data(cache_key)
            if cached:
                return cached
            
            # Get dashboard and widget
            dashboard = self._get_dashboard(request.dashboard_id, request.user_id)
            widget = next((w for w in dashboard.widgets if w.id == request.widget_id), None)
            
            if not widget:
                raise ValueError("Widget not found")
            
            # Fetch data based on widget type and data source
            data = await self._fetch_widget_data(widget, request)
            
            # Cache the result
            self._cache_data(cache_key, data, ttl=widget.refresh_interval or self._cache_ttl)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting widget data: {e}")
            raise
    
    async def get_dashboard_data(
        self, 
        dashboard_id: str, 
        user_id: str,
        time_range: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get data for all widgets in a dashboard"""
        try:
            dashboard = self._get_dashboard(dashboard_id, user_id)
            if not dashboard:
                raise ValueError("Dashboard not found")
            
            # Update last accessed
            dashboard.last_accessed = datetime.utcnow()
            self._save_dashboard(dashboard)
            
            # Fetch data for all widgets in parallel
            widget_data_tasks = []
            for widget in dashboard.widgets:
                request = WidgetDataRequest(
                    widget_id=widget.id,
                    dashboard_id=dashboard_id,
                    user_id=user_id,
                    time_range=time_range
                )
                widget_data_tasks.append(self.get_widget_data(request))
            
            widget_data_results = await asyncio.gather(*widget_data_tasks, return_exceptions=True)
            
            # Compile results
            result = {
                "dashboard": dashboard.model_dump(),
                "widget_data": {}
            }
            
            for widget, data in zip(dashboard.widgets, widget_data_results):
                if isinstance(data, Exception):
                    logger.error(f"Error fetching data for widget {widget.id}: {data}")
                    result["widget_data"][widget.id] = {"error": str(data)}
                else:
                    result["widget_data"][widget.id] = data
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise
    
    # Template Management
    def _get_template_layout(self, template: DashboardTemplate) -> DashboardLayout:
        """Get layout configuration for template"""
        layouts = {
            DashboardTemplate.DAY_TRADING: DashboardLayout(
                name="Day Trading Layout",
                columns=12,
                row_height=80
            ),
            DashboardTemplate.SWING_TRADING: DashboardLayout(
                name="Swing Trading Layout",
                columns=12,
                row_height=100
            ),
            DashboardTemplate.OPTIONS: DashboardLayout(
                name="Options Layout",
                columns=16,
                row_height=80
            ),
            DashboardTemplate.CRYPTO: DashboardLayout(
                name="Crypto Layout",
                columns=12,
                row_height=90
            ),
            DashboardTemplate.FOREX: DashboardLayout(
                name="Forex Layout",
                columns=12,
                row_height=85
            ),
            DashboardTemplate.CUSTOM: DashboardLayout(
                name="Custom Layout",
                columns=12,
                row_height=80
            )
        }
        return layouts.get(template, layouts[DashboardTemplate.CUSTOM])
    
    def _get_template_widgets(self, template: DashboardTemplate) -> List[WidgetConfig]:
        """Get default widgets for template"""
        widgets = {
            DashboardTemplate.DAY_TRADING: [
                WidgetConfig(
                    type=WidgetType.METRIC_CARD,
                    title="Today's P&L",
                    position=WidgetPosition(x=0, y=0, width=3, height=2),
                    data_source=DataSource.TRADES,
                    data_config={"metric": "daily_pnl", "period": "today"}
                ),
                WidgetConfig(
                    type=WidgetType.WIN_RATE_GAUGE,
                    title="Win Rate",
                    position=WidgetPosition(x=3, y=0, width=3, height=2),
                    data_source=DataSource.TRADES,
                    data_config={"period": "today"}
                ),
                WidgetConfig(
                    type=WidgetType.LIVE_MARKET,
                    title="Market Overview",
                    position=WidgetPosition(x=6, y=0, width=6, height=2),
                    data_source=DataSource.MARKET_DATA,
                    data_config={"symbols": ["SPY", "QQQ", "IWM"]}
                ),
                WidgetConfig(
                    type=WidgetType.LINE_CHART,
                    title="Intraday P&L",
                    position=WidgetPosition(x=0, y=2, width=8, height=4),
                    data_source=DataSource.TRADES,
                    data_config={"metric": "cumulative_pnl", "interval": "5min"}
                ),
                WidgetConfig(
                    type=WidgetType.TABLE,
                    title="Recent Trades",
                    position=WidgetPosition(x=8, y=2, width=4, height=4),
                    data_source=DataSource.TRADES,
                    data_config={"limit": 10, "sort": "entry_time_desc"}
                )
            ],
            DashboardTemplate.SWING_TRADING: [
                WidgetConfig(
                    type=WidgetType.METRIC_CARD,
                    title="Open Positions",
                    position=WidgetPosition(x=0, y=0, width=3, height=2),
                    data_source=DataSource.PORTFOLIO,
                    data_config={"metric": "open_positions"}
                ),
                WidgetConfig(
                    type=WidgetType.METRIC_CARD,
                    title="Weekly P&L",
                    position=WidgetPosition(x=3, y=0, width=3, height=2),
                    data_source=DataSource.TRADES,
                    data_config={"metric": "weekly_pnl"}
                ),
                WidgetConfig(
                    type=WidgetType.PNL_CALENDAR,
                    title="P&L Calendar",
                    position=WidgetPosition(x=6, y=0, width=6, height=4),
                    data_source=DataSource.TRADES,
                    data_config={"months": 3}
                ),
                WidgetConfig(
                    type=WidgetType.CANDLESTICK,
                    title="Price Charts",
                    position=WidgetPosition(x=0, y=2, width=6, height=5),
                    data_source=DataSource.MARKET_DATA,
                    data_config={"symbol": "SPY", "interval": "1d", "period": "6mo"}
                )
            ],
            DashboardTemplate.OPTIONS: [
                WidgetConfig(
                    type=WidgetType.HEATMAP,
                    title="Options Greeks",
                    position=WidgetPosition(x=0, y=0, width=6, height=4),
                    data_source=DataSource.CUSTOM_CALCULATION,
                    data_config={"calculation": "greeks_heatmap"}
                ),
                WidgetConfig(
                    type=WidgetType.TABLE,
                    title="Options Positions",
                    position=WidgetPosition(x=6, y=0, width=6, height=4),
                    data_source=DataSource.PORTFOLIO,
                    data_config={"filter": "options_only"}
                ),
                WidgetConfig(
                    type=WidgetType.LINE_CHART,
                    title="P&L by Strategy",
                    position=WidgetPosition(x=0, y=4, width=12, height=4),
                    data_source=DataSource.TRADES,
                    data_config={"group_by": "strategy", "chart_type": "stacked"}
                )
            ]
        }
        
        return widgets.get(template, [])
    
    # Data Fetching
    async def _fetch_widget_data(
        self, 
        widget: WidgetConfig, 
        request: WidgetDataRequest
    ) -> Dict[str, Any]:
        """Fetch data for a widget based on its configuration"""
        try:
            if widget.data_source == DataSource.TRADES:
                return await self._fetch_trade_data(widget, request)
            elif widget.data_source == DataSource.PORTFOLIO:
                return await self._fetch_portfolio_data(widget, request)
            elif widget.data_source == DataSource.MARKET_DATA:
                return await self._fetch_market_data(widget, request)
            elif widget.data_source == DataSource.CUSTOM_CALCULATION:
                return await self._fetch_custom_calculation(widget, request)
            elif widget.data_source == DataSource.EXTERNAL_API:
                return await self._fetch_external_api_data(widget, request)
            else:
                raise ValueError(f"Unknown data source: {widget.data_source}")
                
        except Exception as e:
            logger.error(f"Error fetching widget data: {e}")
            raise
    
    async def _fetch_trade_data(
        self, 
        widget: WidgetConfig, 
        request: WidgetDataRequest
    ) -> Dict[str, Any]:
        """Fetch trade-related data"""
        config = widget.data_config
        
        # Get user's trades
        query = self.db.query(Trade).filter(Trade.user_id == request.user_id)
        
        # Apply time range filter
        if request.time_range:
            start_date = request.time_range.get("start")
            end_date = request.time_range.get("end")
            if start_date:
                query = query.filter(Trade.entry_time >= start_date)
            if end_date:
                query = query.filter(Trade.entry_time <= end_date)
        
        trades = query.all()
        
        # Process based on widget type
        if widget.type == WidgetType.METRIC_CARD:
            return self._calculate_trade_metric(trades, config)
        elif widget.type == WidgetType.LINE_CHART:
            return self._prepare_trade_line_chart(trades, config)
        elif widget.type == WidgetType.TABLE:
            return self._prepare_trade_table(trades, config)
        elif widget.type == WidgetType.WIN_RATE_GAUGE:
            return self._calculate_win_rate(trades)
        elif widget.type == WidgetType.PNL_CALENDAR:
            return self._prepare_pnl_calendar(trades)
        elif widget.type == WidgetType.TRADE_DISTRIBUTION_MAP:
            return self._prepare_trade_distribution(trades)
        else:
            return {"error": f"Unsupported widget type for trade data: {widget.type}"}
    
    async def _fetch_portfolio_data(
        self, 
        widget: WidgetConfig, 
        request: WidgetDataRequest
    ) -> Dict[str, Any]:
        """Fetch portfolio-related data"""
        config = widget.data_config
        
        # Get user's portfolio
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.user_id == request.user_id
        ).first()
        
        if not portfolio:
            return {"error": "No portfolio found"}
        
        if widget.type == WidgetType.METRIC_CARD:
            metric = config.get("metric")
            if metric == "total_value":
                return {"value": portfolio.total_value, "currency": "USD"}
            elif metric == "open_positions":
                return {"value": len(portfolio.positions), "unit": "positions"}
            else:
                return {"error": f"Unknown metric: {metric}"}
        elif widget.type == WidgetType.TABLE:
            return self._prepare_portfolio_table(portfolio, config)
        else:
            return {"error": f"Unsupported widget type for portfolio data: {widget.type}"}
    
    async def _fetch_market_data(
        self, 
        widget: WidgetConfig, 
        request: WidgetDataRequest
    ) -> Dict[str, Any]:
        """Fetch market data"""
        config = widget.data_config
        
        if widget.type == WidgetType.LIVE_MARKET:
            symbols = config.get("symbols", [])
            return await self.market_data_service.get_live_quotes(symbols)
        elif widget.type == WidgetType.CANDLESTICK:
            symbol = config.get("symbol")
            interval = config.get("interval", "1d")
            period = config.get("period", "1mo")
            return await self.market_data_service.get_historical_data(
                symbol, interval, period
            )
        else:
            return {"error": f"Unsupported widget type for market data: {widget.type}"}
    
    async def _fetch_custom_calculation(
        self, 
        widget: WidgetConfig, 
        request: WidgetDataRequest
    ) -> Dict[str, Any]:
        """Perform custom calculations"""
        calculation = widget.data_config.get("calculation")
        
        if calculation == "greeks_heatmap":
            return await self._calculate_options_greeks(request.user_id)
        elif calculation == "correlation_matrix":
            return await self._calculate_correlation_matrix(request.user_id)
        else:
            return {"error": f"Unknown calculation: {calculation}"}
    
    async def _fetch_external_api_data(
        self, 
        widget: WidgetConfig, 
        request: WidgetDataRequest
    ) -> Dict[str, Any]:
        """Fetch data from external APIs"""
        # This would integrate with external data sources
        return {"error": "External API integration not implemented"}
    
    # Data Processing Helpers
    def _calculate_trade_metric(
        self, 
        trades: List[Trade], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate a specific trade metric"""
        metric = config.get("metric")
        period = config.get("period", "all")
        
        # Filter by period
        if period == "today":
            today = datetime.utcnow().date()
            trades = [t for t in trades if t.entry_time.date() == today]
        elif period == "week":
            week_start = datetime.utcnow() - timedelta(days=7)
            trades = [t for t in trades if t.entry_time >= week_start]
        elif period == "month":
            month_start = datetime.utcnow() - timedelta(days=30)
            trades = [t for t in trades if t.entry_time >= month_start]
        
        if metric == "daily_pnl":
            total_pnl = sum(t.net_pnl or 0 for t in trades)
            return {
                "value": round(total_pnl, 2),
                "currency": "USD",
                "change": self._calculate_change(trades, "pnl", period)
            }
        elif metric == "weekly_pnl":
            weekly_pnl = sum(t.net_pnl or 0 for t in trades)
            return {
                "value": round(weekly_pnl, 2),
                "currency": "USD",
                "trades": len(trades)
            }
        elif metric == "total_trades":
            return {
                "value": len(trades),
                "unit": "trades"
            }
        else:
            return {"error": f"Unknown metric: {metric}"}
    
    def _prepare_trade_line_chart(
        self, 
        trades: List[Trade], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare trade data for line chart"""
        metric = config.get("metric", "cumulative_pnl")
        interval = config.get("interval", "1d")
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame([{
            "entry_time": t.entry_time,
            "pnl": t.net_pnl or 0,
            "symbol": t.symbol,
            "strategy": t.strategy_tag
        } for t in trades])
        
        if df.empty:
            return {"data": [], "labels": []}
        
        # Group by interval
        df["entry_time"] = pd.to_datetime(df["entry_time"])
        df.set_index("entry_time", inplace=True)
        
        if interval == "5min":
            grouped = df.resample("5T")
        elif interval == "1h":
            grouped = df.resample("1H")
        elif interval == "1d":
            grouped = df.resample("1D")
        else:
            grouped = df.resample("1D")
        
        if metric == "cumulative_pnl":
            data = grouped["pnl"].sum().cumsum()
        elif metric == "trade_count":
            data = grouped.size()
        else:
            data = grouped["pnl"].sum()
        
        return {
            "labels": data.index.strftime("%Y-%m-%d %H:%M").tolist(),
            "datasets": [{
                "label": metric.replace("_", " ").title(),
                "data": data.tolist(),
                "borderColor": "rgb(75, 192, 192)",
                "tension": 0.1
            }]
        }
    
    def _prepare_trade_table(
        self, 
        trades: List[Trade], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare trade data for table display"""
        limit = config.get("limit", 50)
        sort = config.get("sort", "entry_time_desc")
        
        # Sort trades
        if sort == "entry_time_desc":
            trades = sorted(trades, key=lambda t: t.entry_time, reverse=True)
        elif sort == "pnl_desc":
            trades = sorted(trades, key=lambda t: t.net_pnl or 0, reverse=True)
        
        # Limit results
        trades = trades[:limit]
        
        # Format for table
        rows = []
        for trade in trades:
            rows.append({
                "id": trade.id,
                "symbol": trade.symbol,
                "direction": trade.direction,
                "entry_time": trade.entry_time.isoformat(),
                "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
                "quantity": trade.quantity,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "pnl": round(trade.net_pnl or 0, 2),
                "strategy": trade.strategy_tag
            })
        
        return {
            "columns": [
                {"key": "symbol", "label": "Symbol"},
                {"key": "direction", "label": "Direction"},
                {"key": "entry_time", "label": "Entry Time"},
                {"key": "quantity", "label": "Quantity"},
                {"key": "pnl", "label": "P&L", "numeric": True}
            ],
            "rows": rows
        }
    
    def _calculate_win_rate(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate win rate for gauge display"""
        if not trades:
            return {"value": 0, "min": 0, "max": 100, "unit": "%"}
        
        winning_trades = [t for t in trades if (t.net_pnl or 0) > 0]
        win_rate = (len(winning_trades) / len(trades)) * 100
        
        return {
            "value": round(win_rate, 1),
            "min": 0,
            "max": 100,
            "unit": "%",
            "segments": [
                {"value": 50, "color": "red"},
                {"value": 70, "color": "yellow"},
                {"value": 100, "color": "green"}
            ],
            "winning_trades": len(winning_trades),
            "total_trades": len(trades)
        }
    
    def _prepare_pnl_calendar(self, trades: List[Trade]) -> Dict[str, Any]:
        """Prepare P&L data for calendar heatmap"""
        # Group trades by date
        daily_pnl = defaultdict(float)
        for trade in trades:
            date = trade.entry_time.date()
            daily_pnl[date] += trade.net_pnl or 0
        
        # Format for calendar
        data = []
        for date, pnl in daily_pnl.items():
            data.append({
                "date": date.isoformat(),
                "value": round(pnl, 2),
                "level": self._get_pnl_level(pnl)
            })
        
        return {
            "data": data,
            "start": min(daily_pnl.keys()).isoformat() if daily_pnl else None,
            "end": max(daily_pnl.keys()).isoformat() if daily_pnl else None
        }
    
    def _prepare_trade_distribution(self, trades: List[Trade]) -> Dict[str, Any]:
        """Prepare trade distribution data"""
        # Group by symbol
        symbol_stats = defaultdict(lambda: {"count": 0, "pnl": 0, "win_rate": 0})
        
        for trade in trades:
            symbol = trade.symbol
            symbol_stats[symbol]["count"] += 1
            symbol_stats[symbol]["pnl"] += trade.net_pnl or 0
            if (trade.net_pnl or 0) > 0:
                symbol_stats[symbol]["wins"] = symbol_stats[symbol].get("wins", 0) + 1
        
        # Calculate win rates
        for symbol, stats in symbol_stats.items():
            if stats["count"] > 0:
                stats["win_rate"] = (stats.get("wins", 0) / stats["count"]) * 100
        
        # Format for visualization
        data = []
        for symbol, stats in symbol_stats.items():
            data.append({
                "symbol": symbol,
                "trades": stats["count"],
                "pnl": round(stats["pnl"], 2),
                "win_rate": round(stats["win_rate"], 1),
                "size": stats["count"]  # For bubble size
            })
        
        return {
            "data": sorted(data, key=lambda x: x["trades"], reverse=True)[:20],
            "total_symbols": len(symbol_stats)
        }
    
    def _prepare_portfolio_table(
        self, 
        portfolio: Portfolio, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare portfolio positions for table display"""
        filter_type = config.get("filter", "all")
        
        positions = portfolio.positions  # Assuming positions is a JSON field
        
        if filter_type == "options_only":
            positions = [p for p in positions if p.get("type") == "option"]
        
        rows = []
        for position in positions:
            rows.append({
                "symbol": position.get("symbol"),
                "quantity": position.get("quantity"),
                "entry_price": position.get("entry_price"),
                "current_price": position.get("current_price"),
                "pnl": position.get("unrealized_pnl"),
                "pnl_percent": position.get("pnl_percent")
            })
        
        return {
            "columns": [
                {"key": "symbol", "label": "Symbol"},
                {"key": "quantity", "label": "Quantity", "numeric": True},
                {"key": "entry_price", "label": "Entry", "numeric": True},
                {"key": "current_price", "label": "Current", "numeric": True},
                {"key": "pnl", "label": "P&L", "numeric": True},
                {"key": "pnl_percent", "label": "P&L %", "numeric": True}
            ],
            "rows": rows
        }
    
    async def _calculate_options_greeks(self, user_id: str) -> Dict[str, Any]:
        """Calculate options Greeks for heatmap"""
        # This would integrate with options pricing models
        # Placeholder implementation
        return {
            "data": [
                {"strike": 100, "expiry": "2024-01-19", "delta": 0.5, "gamma": 0.02},
                {"strike": 105, "expiry": "2024-01-19", "delta": 0.3, "gamma": 0.015}
            ],
            "heatmap_config": {
                "x": "strike",
                "y": "expiry",
                "value": "delta"
            }
        }
    
    async def _calculate_correlation_matrix(self, user_id: str) -> Dict[str, Any]:
        """Calculate correlation matrix for traded symbols"""
        # Get unique symbols
        trades = self.db.query(Trade).filter(Trade.user_id == user_id).all()
        symbols = list(set(t.symbol for t in trades))[:10]  # Limit to 10 symbols
        
        # This would fetch price data and calculate correlations
        # Placeholder implementation
        correlations = np.random.rand(len(symbols), len(symbols))
        correlations = (correlations + correlations.T) / 2  # Make symmetric
        np.fill_diagonal(correlations, 1)  # Diagonal = 1
        
        return {
            "symbols": symbols,
            "matrix": correlations.tolist()
        }
    
    def _calculate_change(
        self, 
        trades: List[Trade], 
        metric: str, 
        period: str
    ) -> Dict[str, Any]:
        """Calculate change in metric vs previous period"""
        # This would compare with previous period
        # Placeholder implementation
        return {
            "value": np.random.uniform(-10, 10),
            "percentage": np.random.uniform(-20, 20),
            "direction": np.random.choice(["up", "down", "flat"])
        }
    
    def _get_pnl_level(self, pnl: float) -> int:
        """Get P&L level for heatmap coloring"""
        if pnl <= -500:
            return 0
        elif pnl <= -100:
            return 1
        elif pnl <= 0:
            return 2
        elif pnl <= 100:
            return 3
        elif pnl <= 500:
            return 4
        else:
            return 5
    
    # Storage helpers (these would use actual database in production)
    def _save_dashboard(self, dashboard: Dashboard) -> None:
        """Save dashboard to storage"""
        # In production, this would save to database
        # For now, we'll use Redis
        key = f"dashboard:{dashboard.id}"
        self.redis.setex(
            key,
            86400,  # 24 hours
            dashboard.model_dump_json()
        )
    
    def _get_dashboard(self, dashboard_id: str, user_id: str) -> Optional[Dashboard]:
        """Get dashboard from storage"""
        key = f"dashboard:{dashboard_id}"
        data = self.redis.get(key)
        
        if data:
            dashboard = Dashboard.model_validate_json(data)
            # Check access permissions
            if dashboard.user_id == user_id or user_id in dashboard.shared_with:
                return dashboard
        
        return None
    
    def _delete_dashboard(self, dashboard_id: str) -> None:
        """Delete dashboard from storage"""
        key = f"dashboard:{dashboard_id}"
        self.redis.delete(key)
    
    def _query_dashboards(
        self, 
        filter_criteria: DashboardFilter,
        page: int,
        page_size: int
    ) -> List[Dashboard]:
        """Query dashboards with filtering"""
        # In production, this would query database
        # For now, return empty list
        return []
    
    def _count_dashboards(self, filter_criteria: DashboardFilter) -> int:
        """Count dashboards matching criteria"""
        return 0
    
    def _check_widget_overlap(
        self, 
        existing_widgets: List[WidgetConfig],
        new_position: WidgetPosition
    ) -> bool:
        """Check if new widget position overlaps with existing widgets"""
        new_x1 = new_position.x
        new_x2 = new_position.x + new_position.width
        new_y1 = new_position.y
        new_y2 = new_position.y + new_position.height
        
        for widget in existing_widgets:
            pos = widget.position
            x1 = pos.x
            x2 = pos.x + pos.width
            y1 = pos.y
            y2 = pos.y + pos.height
            
            # Check for overlap
            if not (new_x2 <= x1 or new_x1 >= x2 or new_y2 <= y1 or new_y1 >= y2):
                return True
        
        return False
    
    def _notify_dashboard_shared(self, user_id: str, dashboard: Dashboard) -> None:
        """Notify user that dashboard was shared with them"""
        # This would send notification
        logger.info(f"Dashboard {dashboard.id} shared with user {user_id}")
    
    # Caching helpers
    def _get_widget_cache_key(self, request: WidgetDataRequest) -> str:
        """Generate cache key for widget data"""
        key_parts = [
            "widget_data",
            request.dashboard_id,
            request.widget_id,
            request.user_id
        ]
        
        # Add filters and time range to key
        if request.time_range:
            key_parts.append(hashlib.md5(
                json.dumps(request.time_range, sort_keys=True).encode()
            ).hexdigest()[:8])
        
        if request.filters:
            key_parts.append(hashlib.md5(
                json.dumps(request.filters, sort_keys=True).encode()
            ).hexdigest()[:8])
        
        return ":".join(key_parts)
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached data"""
        if not self.redis:
            return None
        
        try:
            data = self.redis.get(cache_key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        
        return None
    
    def _cache_data(self, cache_key: str, data: Dict[str, Any], ttl: int) -> None:
        """Cache data with TTL"""
        if not self.redis:
            return
        
        try:
            self.redis.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Cache write error: {e}")
    
    def _invalidate_dashboard_cache(self, dashboard_id: str) -> None:
        """Invalidate all cache entries for a dashboard"""
        if not self.redis:
            return
        
        pattern = f"widget_data:{dashboard_id}:*"
        try:
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    def _invalidate_widget_cache(self, dashboard_id: str, widget_id: str) -> None:
        """Invalidate cache for specific widget"""
        if not self.redis:
            return
        
        pattern = f"widget_data:{dashboard_id}:{widget_id}:*"
        try:
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")


# Export models and service
__all__ = [
    "DashboardService",
    "Dashboard",
    "DashboardLayout",
    "WidgetConfig",
    "WidgetPosition",
    "WidgetType",
    "DataSource",
    "DashboardTemplate",
    "DashboardFilter",
    "WidgetDataRequest"
]