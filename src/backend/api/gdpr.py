"""
GDPR compliance API endpoints for TradeSense.
Handles data export requests, account deletion, and privacy settings.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from core.db.session import get_db
from models.user import User
from gdpr.data_export_service import data_export_service
from analytics import track_gdpr_event

router = APIRouter(prefix="/api/v1/gdpr", tags=["gdpr"])


# Request models
class DataExportRequest(BaseModel):
    confirmation: bool  # User must confirm they understand the request


class AccountDeletionRequest(BaseModel):
    confirmation: bool
    password: str  # Require password for deletion
    reason: Optional[str] = None
    feedback: Optional[str] = None


class PrivacySettingsUpdate(BaseModel):
    analytics_enabled: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    data_sharing: Optional[bool] = None
    cookie_preferences: Optional[Dict[str, bool]] = None


# Endpoints
@router.post("/export")
async def request_data_export(
    request: DataExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request a full export of user data (GDPR Article 15)."""
    try:
        if not request.confirmation:
            raise HTTPException(
                status_code=400,
                detail="Please confirm you want to export your data"
            )
        
        # Check for existing pending request
        from sqlalchemy import text
        existing = await db.execute(
            text("""
                SELECT id, status, requested_at
                FROM gdpr_requests
                WHERE user_id = :user_id
                AND request_type = 'export'
                AND status IN ('pending', 'processing')
                ORDER BY requested_at DESC
                LIMIT 1
            """),
            {"user_id": current_user.id}
        )
        
        existing_request = existing.first()
        if existing_request:
            return {
                "request_id": str(existing_request.id),
                "status": existing_request.status,
                "message": "You already have a pending export request",
                "requested_at": existing_request.requested_at
            }
        
        # Create new export request
        request_id = await data_export_service.create_export_request(
            user=current_user,
            request_type="export",
            db=db
        )
        
        # Track event
        await track_gdpr_event(
            user_id=str(current_user.id),
            event="data_export_requested"
        )
        
        return {
            "request_id": request_id,
            "status": "pending",
            "message": "Your data export request has been received. You'll receive an email when it's ready.",
            "estimated_time": "1-2 hours"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/account")
async def request_account_deletion(
    request: AccountDeletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request account deletion (GDPR Article 17 - Right to be forgotten)."""
    try:
        if not request.confirmation:
            raise HTTPException(
                status_code=400,
                detail="Please confirm you want to delete your account"
            )
        
        # Verify password
        from services.auth_service import auth_service
        if not await auth_service.verify_password(current_user, request.password):
            raise HTTPException(
                status_code=401,
                detail="Invalid password"
            )
        
        # Check for active subscription
        if current_user.subscription_tier != "free":
            return {
                "error": "active_subscription",
                "message": "Please cancel your subscription before deleting your account",
                "subscription_tier": current_user.subscription_tier
            }
        
        # Store deletion reason
        if request.reason or request.feedback:
            await db.execute(
                text("""
                    INSERT INTO account_deletion_feedback
                    (user_id, reason, feedback, created_at)
                    VALUES (:user_id, :reason, :feedback, NOW())
                """),
                {
                    "user_id": current_user.id,
                    "reason": request.reason,
                    "feedback": request.feedback
                }
            )
            await db.commit()
        
        # Create deletion request
        request_id = await data_export_service.create_export_request(
            user=current_user,
            request_type="deletion",
            db=db
        )
        
        # Track event
        await track_gdpr_event(
            user_id=str(current_user.id),
            event="account_deletion_requested",
            data={"reason": request.reason}
        )
        
        return {
            "request_id": request_id,
            "status": "pending",
            "message": "Your account deletion request has been received. Your account will be deleted within 24 hours.",
            "warning": "This action is irreversible"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/request/{request_id}")
async def get_request_status(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check status of a GDPR request."""
    try:
        status = await data_export_service.get_request_status(
            request_id=request_id,
            user_id=str(current_user.id),
            db=db
        )
        
        if not status:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{request_id}")
async def download_data_export(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download completed data export."""
    try:
        # Get export data
        export_data = await data_export_service.download_export(
            request_id=request_id,
            user_id=str(current_user.id),
            db=db
        )
        
        if not export_data:
            raise HTTPException(
                status_code=404,
                detail="Export not found or expired"
            )
        
        # Track download
        await track_gdpr_event(
            user_id=str(current_user.id),
            event="data_export_downloaded",
            data={"request_id": request_id}
        )
        
        # Return file
        return Response(
            content=export_data,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=tradesense_export_{request_id}.zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/privacy-settings")
async def get_privacy_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's privacy settings."""
    try:
        from sqlalchemy import text
        
        # Get privacy settings
        result = await db.execute(
            text("""
                SELECT 
                    analytics_enabled,
                    marketing_emails,
                    data_sharing,
                    cookie_preferences
                FROM user_privacy_settings
                WHERE user_id = :user_id
            """),
            {"user_id": current_user.id}
        )
        
        settings = result.first()
        
        if not settings:
            # Return defaults
            return {
                "analytics_enabled": True,
                "marketing_emails": True,
                "data_sharing": False,
                "cookie_preferences": {
                    "necessary": True,
                    "analytics": True,
                    "marketing": False
                }
            }
        
        return {
            "analytics_enabled": settings.analytics_enabled,
            "marketing_emails": settings.marketing_emails,
            "data_sharing": settings.data_sharing,
            "cookie_preferences": settings.cookie_preferences or {
                "necessary": True,
                "analytics": settings.analytics_enabled,
                "marketing": False
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/privacy-settings")
async def update_privacy_settings(
    settings_update: PrivacySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's privacy settings."""
    try:
        from sqlalchemy import text
        
        # Build update query
        updates = {}
        if settings_update.analytics_enabled is not None:
            updates["analytics_enabled"] = settings_update.analytics_enabled
        if settings_update.marketing_emails is not None:
            updates["marketing_emails"] = settings_update.marketing_emails
        if settings_update.data_sharing is not None:
            updates["data_sharing"] = settings_update.data_sharing
        if settings_update.cookie_preferences is not None:
            updates["cookie_preferences"] = json.dumps(settings_update.cookie_preferences)
        
        if updates:
            # Upsert privacy settings
            await db.execute(
                text("""
                    INSERT INTO user_privacy_settings (
                        user_id, analytics_enabled, marketing_emails,
                        data_sharing, cookie_preferences
                    ) VALUES (
                        :user_id, :analytics_enabled, :marketing_emails,
                        :data_sharing, :cookie_preferences
                    )
                    ON CONFLICT (user_id) DO UPDATE SET
                        analytics_enabled = EXCLUDED.analytics_enabled,
                        marketing_emails = EXCLUDED.marketing_emails,
                        data_sharing = EXCLUDED.data_sharing,
                        cookie_preferences = EXCLUDED.cookie_preferences,
                        updated_at = NOW()
                """),
                {
                    "user_id": current_user.id,
                    "analytics_enabled": updates.get("analytics_enabled", True),
                    "marketing_emails": updates.get("marketing_emails", True),
                    "data_sharing": updates.get("data_sharing", False),
                    "cookie_preferences": updates.get("cookie_preferences", "{}")
                }
            )
            
            await db.commit()
            
            # Track privacy settings change
            await track_gdpr_event(
                user_id=str(current_user.id),
                event="privacy_settings_updated",
                data=updates
            )
        
        return {"message": "Privacy settings updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-categories")
async def get_data_categories():
    """Get information about data categories collected (GDPR Article 13)."""
    return {
        "categories": [
            {
                "name": "Account Information",
                "description": "Basic account details like email, name, and preferences",
                "purpose": "Account management and authentication",
                "retention": "Until account deletion"
            },
            {
                "name": "Trading Data",
                "description": "Trade records, performance metrics, and analysis",
                "purpose": "Core service functionality",
                "retention": "Until account deletion"
            },
            {
                "name": "Usage Analytics",
                "description": "Feature usage, page views, and interaction data",
                "purpose": "Product improvement and personalization",
                "retention": "2 years"
            },
            {
                "name": "Support Communications",
                "description": "Support tickets and communications",
                "purpose": "Customer service",
                "retention": "3 years"
            },
            {
                "name": "Payment Information",
                "description": "Subscription and payment history (not card details)",
                "purpose": "Billing and compliance",
                "retention": "7 years (legal requirement)"
            }
        ],
        "third_party_sharing": {
            "payment_processor": {
                "name": "Stripe",
                "purpose": "Payment processing",
                "data_shared": "Email, name, payment details"
            },
            "analytics": {
                "name": "Internal analytics only",
                "purpose": "Product improvement",
                "data_shared": "Anonymized usage data"
            }
        },
        "user_rights": [
            "Access your personal data",
            "Correct inaccurate data",
            "Delete your account and data",
            "Export your data",
            "Object to data processing",
            "Restrict data processing"
        ]
    }


@router.post("/consent/withdraw/{consent_type}")
async def withdraw_consent(
    consent_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Withdraw consent for specific data processing."""
    try:
        valid_consent_types = ["marketing", "analytics", "data_sharing"]
        
        if consent_type not in valid_consent_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid consent type. Must be one of: {', '.join(valid_consent_types)}"
            )
        
        # Update consent
        from sqlalchemy import text
        await db.execute(
            text(f"""
                UPDATE user_privacy_settings
                SET {consent_type}_emails = FALSE
                WHERE user_id = :user_id
            """),
            {"user_id": current_user.id}
        )
        
        await db.commit()
        
        # Track consent withdrawal
        await track_gdpr_event(
            user_id=str(current_user.id),
            event="consent_withdrawn",
            data={"consent_type": consent_type}
        )
        
        return {
            "message": f"Consent for {consent_type} has been withdrawn",
            "consent_type": consent_type,
            "status": "withdrawn"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import json
from typing import Dict