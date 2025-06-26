
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.core.db.session import get_db
from backend.api.deps import get_current_user
from backend.services.portfolio_simulator import PortfolioSimulator
from backend.models.user import User
from backend.api.v1.portfolio.schemas import PortfolioCreate, PortfolioResponse, EquityCurveResponse

router = APIRouter()

@router.post("/", response_model=Dict[str, Any])
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new virtual portfolio"""
    simulator = PortfolioSimulator(db)
    result = simulator.create_portfolio(
        user_id=current_user.id,
        name=portfolio_data.name,
        initial_balance=portfolio_data.initial_balance
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/", response_model=List[PortfolioResponse])
async def get_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all portfolios for the current user"""
    simulator = PortfolioSimulator(db)
    portfolios = simulator.get_user_portfolios(current_user.id)
    return portfolios

@router.post("/{portfolio_id}/simulate")
async def simulate_trades(
    portfolio_id: str,
    trade_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simulate trades on a portfolio"""
    simulator = PortfolioSimulator(db)
    result = simulator.simulate_trades_on_portfolio(portfolio_id, trade_ids)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/{portfolio_id}/equity-curve", response_model=EquityCurveResponse)
async def get_equity_curve(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get equity curve data for a portfolio"""
    simulator = PortfolioSimulator(db)
    result = simulator.get_equity_curve(portfolio_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a portfolio"""
    simulator = PortfolioSimulator(db)
    result = simulator.delete_portfolio(portfolio_id, current_user.id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result
