
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.core.db.session import get_db
from backend.api.deps import get_current_user
from .service import CritiqueService
from .schemas import CritiqueRequest, CritiqueResponse, CritiqueFeedbackRequest

router = APIRouter(prefix="/critique", tags=["critique"])

@router.get("/trades/{trade_id}", response_model=CritiqueResponse)
async def get_trade_critique(
    trade_id: str,
    regenerate: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get AI critique for a specific trade"""
    try:
        service = CritiqueService(db)
        critique = await service.get_trade_critique(
            trade_id=trade_id, 
            user_id=current_user["id"], 
            regenerate=regenerate
        )
        return critique
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating critique: {str(e)}")

@router.post("/trades/{trade_id}/feedback")
async def submit_critique_feedback(
    trade_id: str,
    feedback: CritiqueFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit feedback on critique quality"""
    try:
        service = CritiqueService(db)
        result = await service.submit_critique_feedback(
            trade_id=trade_id,
            user_id=current_user["id"],
            feedback=feedback
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@router.get("/analytics")
async def get_critique_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get analytics on critique usage and patterns"""
    try:
        service = CritiqueService(db)
        analytics = await service.get_critique_analytics(current_user["id"])
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting critique analytics: {str(e)}")

@router.post("/trades/{trade_id}/regenerate", response_model=CritiqueResponse)
async def regenerate_trade_critique(
    trade_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Regenerate critique for a trade"""
    try:
        service = CritiqueService(db)
        critique = await service.get_trade_critique(
            trade_id=trade_id, 
            user_id=current_user["id"], 
            regenerate=True
        )
        return critique
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating critique: {str(e)}")
