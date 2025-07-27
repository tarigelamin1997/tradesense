
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime

class SimulationFilters(BaseModel):
    """Filters for Strategy Lab simulation"""
    playbook_ids: Optional[List[UUID]] = Field(None, description="Filter by specific playbooks")
    exclude_playbook_ids: Optional[List[UUID]] = Field(None, description="Exclude specific playbooks")
    confidence_score_min: Optional[int] = Field(None, ge=1, le=10, description="Minimum confidence score")
    confidence_score_max: Optional[int] = Field(None, ge=1, le=10, description="Maximum confidence score")
    entry_time_start: Optional[datetime] = Field(None, description="Entry time range start")
    entry_time_end: Optional[datetime] = Field(None, description="Entry time range end")
    symbols: Optional[List[str]] = Field(None, description="Filter by specific symbols")
    directions: Optional[List[str]] = Field(None, description="Filter by trade directions (long/short)")
    tags_include: Optional[List[str]] = Field(None, description="Include trades with these tags")
    tags_exclude: Optional[List[str]] = Field(None, description="Exclude trades with these tags")
    min_hold_time_minutes: Optional[int] = Field(None, ge=0, description="Minimum hold time in minutes")
    max_hold_time_minutes: Optional[int] = Field(None, ge=0, description="Maximum hold time in minutes")
    pnl_min: Optional[float] = Field(None, description="Minimum P&L")
    pnl_max: Optional[float] = Field(None, description="Maximum P&L")

class SimulationRequest(BaseModel):
    """Request body for strategy lab simulation"""
    filters: SimulationFilters
    name: Optional[str] = Field(None, description="Name for this simulation scenario")
    compare_to_baseline: bool = Field(True, description="Compare results to overall performance")

class TradeSimulationResult(BaseModel):
    """Individual trade result in simulation"""
    trade_id: str
    symbol: str
    direction: str
    entry_time: datetime
    exit_time: Optional[datetime]
    pnl: Optional[float]
    confidence_score: Optional[int]
    playbook_name: Optional[str]
    tags: Optional[List[str]]

class PerformanceMetrics(BaseModel):
    """Performance metrics for simulation results"""
    total_trades: int
    completed_trades: int
    total_pnl: float
    avg_pnl: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: float
    consecutive_wins: int
    consecutive_losses: int
    avg_hold_time_minutes: Optional[float]
    best_trade: float
    worst_trade: float

class ComparisonMetrics(BaseModel):
    """Comparison between simulation and baseline"""
    pnl_difference: float
    pnl_improvement_pct: float
    win_rate_difference: float
    profit_factor_difference: Optional[float]
    avg_pnl_difference: float
    trade_count_difference: int

class SimulationResponse(BaseModel):
    """Response from strategy lab simulation"""
    scenario_name: Optional[str]
    filters_applied: SimulationFilters
    simulation_metrics: PerformanceMetrics
    baseline_metrics: Optional[PerformanceMetrics]
    comparison: Optional[ComparisonMetrics]
    filtered_trades: List[TradeSimulationResult]
    insights: List[str]
    recommendations: List[str]
    
class PlaybookPerformanceComparison(BaseModel):
    """Compare performance across different playbooks"""
    playbook_id: Optional[UUID]
    playbook_name: str
    metrics: PerformanceMetrics
    trade_count: int

class WhatIfScenario(BaseModel):
    """What-if scenario analysis"""
    scenario_name: str
    description: str
    metrics: PerformanceMetrics
    improvement_pct: float
