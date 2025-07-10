from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from api.deps import get_db, get_current_user
from models.user import User
from api.v1.strategy_lab.service import StrategyLabService
from api.v1.strategy_lab.schemas import (
    SimulationRequest, SimulationResponse, PlaybookPerformanceComparison, WhatIfScenario
)

router = APIRouter()

@router.post("/simulate", response_model=SimulationResponse)
def simulate_strategy(
    request: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run a strategy simulation based on filters and behavioral criteria.
    This is the core Strategy Lab feature that audits trading decisions.
    """
    service = StrategyLabService(db)
    try:
        return service.simulate_strategy(current_user.id, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.get("/playbook-comparison", response_model=List[PlaybookPerformanceComparison])
def compare_playbook_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare performance metrics across all user playbooks.
    Shows which playbooks are most/least profitable.
    """
    service = StrategyLabService(db)
    try:
        return service.compare_playbooks(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Playbook comparison failed: {str(e)}")

@router.get("/what-if-scenarios", response_model=List[WhatIfScenario])
def get_what_if_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate common what-if scenarios for the user's trading history.
    Examples: "What if I only traded high confidence setups?"
    """
    service = StrategyLabService(db)
    try:
        return service.generate_what_if_scenarios(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if analysis failed: {str(e)}")

@router.post("/batch-simulate")
def batch_simulate(
    scenarios: List[SimulationRequest],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run multiple simulations in batch for comparison.
    Useful for testing multiple filter combinations at once.
    """
    service = StrategyLabService(db)
    results = []
    
    try:
        for scenario in scenarios[:10]:  # Limit to 10 scenarios per batch
            result = service.simulate_strategy(current_user.id, scenario)
            results.append(result)
        
        return {
            "scenarios": results,
            "summary": {
                "total_scenarios": len(results),
                "best_scenario": max(results, key=lambda x: x.simulation_metrics.total_pnl).scenario_name if results else None,
                "worst_scenario": min(results, key=lambda x: x.simulation_metrics.total_pnl).scenario_name if results else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch simulation failed: {str(e)}")

@router.get("/")
async def get_strategy_lab_overview(
    current_user: dict = Depends(get_current_user)
):
    """Get overview of strategy lab features"""
    return {
        "status": "available",
        "features": [
            "Strategy backtesting",
            "Performance simulation",
            "Risk analysis",
            "Strategy optimization"
        ],
        "endpoints": {
            "strategies": "/api/v1/strategy-lab/strategies",
            "backtest": "/api/v1/strategy-lab/backtest",
            "optimize": "/api/v1/strategy-lab/optimize"
        }
    }
