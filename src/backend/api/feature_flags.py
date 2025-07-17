"""
Feature flags API endpoints for TradeSense.
Manages feature rollouts and A/B testing.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user, require_admin
from core.db.session import get_db
from models.user import User
from src.backend.features.feature_flags import (
    feature_flag_service, FeatureFlagType, FeatureFlagStatus
)

router = APIRouter(prefix="/api/v1/feature-flags", tags=["feature-flags"])


# Request models
class CreateFeatureFlagRequest(BaseModel):
    key: str
    name: str
    description: str
    type: FeatureFlagType
    default_value: Any
    targeting_rules: List[Dict[str, Any]] = []
    variants: Optional[Dict[str, Any]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class UpdateFeatureFlagRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[FeatureFlagStatus] = None
    default_value: Optional[Any] = None
    targeting_rules: Optional[List[Dict[str, Any]]] = None
    variants: Optional[Dict[str, Any]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# Public endpoints (for users)
@router.get("/evaluate")
async def evaluate_user_flags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all feature flag values for current user."""
    try:
        flags = await feature_flag_service.evaluate_all_flags(
            user=current_user,
            db=db
        )
        
        return {
            "flags": flags,
            "user_id": str(current_user.id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluate/{flag_key}")
async def evaluate_single_flag(
    flag_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Evaluate a specific feature flag for current user."""
    try:
        value = await feature_flag_service.evaluate_flag(
            flag_key=flag_key,
            user=current_user,
            db=db
        )
        
        if value is None:
            raise HTTPException(status_code=404, detail="Feature flag not found")
        
        return {
            "flag_key": flag_key,
            "value": value,
            "user_id": str(current_user.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints
@router.get("/")
async def list_feature_flags(
    include_inactive: bool = Query(False),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all feature flags (admin only)."""
    try:
        flags = await feature_flag_service.get_all_flags(
            include_inactive=include_inactive,
            db=db
        )
        
        return {
            "flags": flags,
            "total": len(flags)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_feature_flag(
    flag_data: CreateFeatureFlagRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new feature flag (admin only)."""
    try:
        # Check if flag key already exists
        existing = await feature_flag_service.get_flag(flag_data.key, db)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Feature flag with key '{flag_data.key}' already exists"
            )
        
        # Parse dates if provided
        from datetime import datetime
        start_date = None
        end_date = None
        
        if flag_data.start_date:
            start_date = datetime.fromisoformat(flag_data.start_date)
        if flag_data.end_date:
            end_date = datetime.fromisoformat(flag_data.end_date)
        
        flag_id = await feature_flag_service.create_flag(
            key=flag_data.key,
            name=flag_data.name,
            description=flag_data.description,
            flag_type=flag_data.type,
            default_value=flag_data.default_value,
            targeting_rules=flag_data.targeting_rules,
            variants=flag_data.variants,
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        
        return {
            "flag_id": flag_id,
            "message": "Feature flag created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{flag_id}")
async def update_feature_flag(
    flag_id: str,
    update_data: UpdateFeatureFlagRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a feature flag (admin only)."""
    try:
        # Build updates dict
        updates = {}
        
        if update_data.name is not None:
            updates["name"] = update_data.name
        if update_data.description is not None:
            updates["description"] = update_data.description
        if update_data.status is not None:
            updates["status"] = update_data.status
        if update_data.default_value is not None:
            updates["default_value"] = update_data.default_value
        if update_data.targeting_rules is not None:
            updates["targeting_rules"] = update_data.targeting_rules
        if update_data.variants is not None:
            updates["variants"] = update_data.variants
        
        # Parse dates if provided
        if update_data.start_date is not None:
            from datetime import datetime
            updates["start_date"] = datetime.fromisoformat(update_data.start_date) if update_data.start_date else None
        if update_data.end_date is not None:
            from datetime import datetime
            updates["end_date"] = datetime.fromisoformat(update_data.end_date) if update_data.end_date else None
        
        success = await feature_flag_service.update_flag(
            flag_id=flag_id,
            updates=updates,
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Feature flag not found")
        
        return {"message": "Feature flag updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{flag_id}")
async def delete_feature_flag(
    flag_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a feature flag (admin only)."""
    try:
        # Soft delete by setting status to inactive
        success = await feature_flag_service.update_flag(
            flag_id=flag_id,
            updates={"status": FeatureFlagStatus.INACTIVE},
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Feature flag not found")
        
        return {"message": "Feature flag deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Testing endpoints (admin only)
@router.post("/test/{flag_key}")
async def test_feature_flag(
    flag_key: str,
    test_user_id: str = Body(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Test a feature flag for a specific user (admin only)."""
    try:
        # Get test user
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT * FROM users WHERE id = :user_id"),
            {"user_id": test_user_id}
        )
        test_user_data = result.first()
        
        if not test_user_data:
            raise HTTPException(status_code=404, detail="Test user not found")
        
        # Create User object from data
        test_user = User(**dict(test_user_data))
        
        # Evaluate flag
        value = await feature_flag_service.evaluate_flag(
            flag_key=flag_key,
            user=test_user,
            db=db
        )
        
        if value is None:
            raise HTTPException(status_code=404, detail="Feature flag not found")
        
        # Also get user stats for debugging
        user_stats = await feature_flag_service._get_user_stats(test_user, db)
        
        return {
            "flag_key": flag_key,
            "value": value,
            "test_user": {
                "id": str(test_user.id),
                "email": test_user.email,
                "tier": test_user.subscription_tier,
                "created_at": test_user.created_at
            },
            "user_stats": user_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@router.get("/analytics/{flag_key}")
async def get_flag_analytics(
    flag_key: str,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics for a feature flag (admin only)."""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get evaluation stats
        result = await db.execute(
            text("""
                SELECT 
                    DATE(created_at) as date,
                    properties->>'value' as value,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM analytics_events
                WHERE event_type = 'feature_flag'
                AND properties->>'flag_key' = :flag_key
                AND created_at >= :since_date
                GROUP BY DATE(created_at), properties->>'value'
                ORDER BY date DESC
            """),
            {
                "flag_key": flag_key,
                "since_date": since_date
            }
        )
        
        evaluations = []
        for row in result:
            evaluations.append({
                "date": row.date.isoformat(),
                "value": row.value,
                "count": row.count,
                "unique_users": row.unique_users
            })
        
        # Get conversion metrics if applicable
        conversion_result = await db.execute(
            text("""
                SELECT 
                    e1.properties->>'value' as flag_value,
                    COUNT(DISTINCT e1.user_id) as exposed_users,
                    COUNT(DISTINCT e2.user_id) as converted_users
                FROM analytics_events e1
                LEFT JOIN analytics_events e2 ON 
                    e1.user_id = e2.user_id AND
                    e2.event_type = 'conversion' AND
                    e2.created_at > e1.created_at AND
                    e2.created_at < e1.created_at + INTERVAL '7 days'
                WHERE e1.event_type = 'feature_flag'
                AND e1.properties->>'flag_key' = :flag_key
                AND e1.created_at >= :since_date
                GROUP BY e1.properties->>'value'
            """),
            {
                "flag_key": flag_key,
                "since_date": since_date
            }
        )
        
        conversions = {}
        for row in conversion_result:
            conversion_rate = (row.converted_users / row.exposed_users * 100) if row.exposed_users > 0 else 0
            conversions[row.flag_value] = {
                "exposed_users": row.exposed_users,
                "converted_users": row.converted_users,
                "conversion_rate": round(conversion_rate, 2)
            }
        
        return {
            "flag_key": flag_key,
            "period_days": days,
            "evaluations": evaluations,
            "conversions": conversions,
            "total_evaluations": sum(e["count"] for e in evaluations),
            "unique_users": sum(set(e["unique_users"] for e in evaluations))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))