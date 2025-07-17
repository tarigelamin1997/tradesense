"""
Onboarding API endpoints for TradeSense.
Manages new user experience and progressive feature introduction.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.db.session import get_db
from models.user import User
from src.backend.onboarding.onboarding_service import onboarding_service, OnboardingStep

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


# Request models
class CompleteStepRequest(BaseModel):
    step: OnboardingStep
    data: Optional[Dict[str, Any]] = None


class SkipStepRequest(BaseModel):
    step: OnboardingStep
    reason: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    trading_experience: Optional[str] = None
    trading_goals: Optional[str] = None
    preferred_markets: Optional[List[str]] = None
    risk_tolerance: Optional[str] = None


class TradingPreferencesRequest(BaseModel):
    default_timezone: Optional[str] = None
    currency: Optional[str] = None
    notification_preferences: Optional[Dict[str, bool]] = None
    display_preferences: Optional[Dict[str, Any]] = None


# Endpoints
@router.get("/state")
async def get_onboarding_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current onboarding state for user."""
    try:
        state = await onboarding_service.get_user_onboarding_state(
            user=current_user,
            db=db
        )
        
        return state
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checklist")
async def get_onboarding_checklist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get onboarding checklist with completion status."""
    try:
        checklist = await onboarding_service.get_onboarding_checklist(
            user=current_user,
            db=db
        )
        
        return {
            "checklist": checklist,
            "user_id": str(current_user.id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete-step")
async def complete_onboarding_step(
    request: CompleteStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark an onboarding step as completed."""
    try:
        result = await onboarding_service.complete_step(
            user=current_user,
            step=request.step,
            step_data=request.data,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skip-step")
async def skip_onboarding_step(
    request: SkipStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Skip an optional onboarding step."""
    try:
        result = await onboarding_service.skip_step(
            user=current_user,
            step=request.step,
            reason=request.reason,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Step-specific endpoints
@router.post("/profile")
async def update_onboarding_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile during onboarding."""
    try:
        from sqlalchemy import text
        
        # Update user profile
        updates = []
        params = {"user_id": current_user.id}
        
        if profile_data.full_name:
            updates.append("full_name = :full_name")
            params["full_name"] = profile_data.full_name
        
        # Store additional data in user metadata
        metadata_updates = {}
        if profile_data.trading_experience:
            metadata_updates["trading_experience"] = profile_data.trading_experience
        if profile_data.trading_goals:
            metadata_updates["trading_goals"] = profile_data.trading_goals
        if profile_data.preferred_markets:
            metadata_updates["preferred_markets"] = profile_data.preferred_markets
        if profile_data.risk_tolerance:
            metadata_updates["risk_tolerance"] = profile_data.risk_tolerance
        
        if metadata_updates:
            updates.append("metadata = metadata || :metadata")
            params["metadata"] = json.dumps(metadata_updates)
        
        if updates:
            await db.execute(
                text(f"""
                    UPDATE users
                    SET {', '.join(updates)}, updated_at = NOW()
                    WHERE id = :user_id
                """),
                params
            )
            await db.commit()
        
        # Complete profile setup step
        result = await onboarding_service.complete_step(
            user=current_user,
            step=OnboardingStep.PROFILE_SETUP,
            step_data=profile_data.dict(exclude_none=True),
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def update_trading_preferences(
    preferences: TradingPreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update trading preferences during onboarding."""
    try:
        from sqlalchemy import text
        
        # Store preferences in user settings
        settings_updates = {}
        
        if preferences.default_timezone:
            settings_updates["default_timezone"] = preferences.default_timezone
        if preferences.currency:
            settings_updates["currency"] = preferences.currency
        if preferences.notification_preferences:
            settings_updates["notifications"] = preferences.notification_preferences
        if preferences.display_preferences:
            settings_updates["display"] = preferences.display_preferences
        
        if settings_updates:
            await db.execute(
                text("""
                    UPDATE users
                    SET settings = COALESCE(settings, '{}'::jsonb) || :settings,
                        updated_at = NOW()
                    WHERE id = :user_id
                """),
                {
                    "user_id": current_user.id,
                    "settings": json.dumps(settings_updates)
                }
            )
            await db.commit()
        
        # Complete preferences step
        result = await onboarding_service.complete_step(
            user=current_user,
            step=OnboardingStep.TRADING_PREFERENCES,
            step_data=preferences.dict(exclude_none=True),
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/first-trade-imported")
async def mark_first_trade_imported(
    trade_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark that user has imported their first trade."""
    try:
        # Verify user has trades
        from sqlalchemy import text
        result = await db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM trades
                WHERE user_id = :user_id
            """),
            {"user_id": current_user.id}
        )
        
        trade_count = result.scalar() or 0
        
        if trade_count == 0:
            raise HTTPException(
                status_code=400,
                detail="No trades found. Please import trades first."
            )
        
        # Complete first trade step
        result = await onboarding_service.complete_step(
            user=current_user,
            step=OnboardingStep.FIRST_TRADE,
            step_data={
                "trade_count": trade_count,
                "import_method": trade_data.get("import_method", "manual"),
                **trade_data
            },
            db=db
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics-tour-completed")
async def complete_analytics_tour(
    tour_data: Dict[str, Any] = Body({}),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark analytics tour as completed."""
    try:
        result = await onboarding_service.complete_step(
            user=current_user,
            step=OnboardingStep.ANALYTICS_TOUR,
            step_data={
                "completed_at": datetime.utcnow().isoformat(),
                **tour_data
            },
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan-selected")
async def mark_plan_selected(
    plan_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark that user has selected a plan."""
    try:
        # Check if user has active subscription
        if current_user.subscription_tier == "free" and not plan_data.get("selected_plan"):
            # User chose to stay on free plan
            plan_data["selected_plan"] = "free"
            plan_data["action"] = "stayed_free"
        
        result = await onboarding_service.complete_step(
            user=current_user,
            step=OnboardingStep.PLAN_SELECTION,
            step_data=plan_data,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dismiss")
async def dismiss_onboarding(
    reason: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dismiss onboarding (skip all remaining steps)."""
    try:
        from sqlalchemy import text
        
        # Mark onboarding as dismissed
        await db.execute(
            text("""
                UPDATE user_onboarding
                SET onboarding_step = 'completed',
                    onboarding_data = onboarding_data || :data,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {
                "user_id": current_user.id,
                "data": json.dumps({
                    "dismissed": True,
                    "dismissed_at": datetime.utcnow().isoformat(),
                    "reason": reason
                })
            }
        )
        
        await db.commit()
        
        # Track dismissal
        from src.backend.analytics import track_onboarding_event
        await track_onboarding_event(
            user_id=str(current_user.id),
            event="onboarding_dismissed",
            data={"reason": reason}
        )
        
        return {"success": True, "message": "Onboarding dismissed"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@router.get("/tips")
async def get_onboarding_tips(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get contextual tips based on user progress."""
    try:
        state = await onboarding_service.get_user_onboarding_state(
            user=current_user,
            db=db
        )
        
        return {
            "tips": state.get("tips", []),
            "account_age_days": state["user_stats"]["account_age_days"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import json
from datetime import datetime