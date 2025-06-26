
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.models.feature_request import FeatureRequest, FeatureVote, FeatureComment
from .schemas import (
    FeatureRequestCreate, FeatureRequestUpdate, FeatureRequestResponse,
    FeatureVoteCreate, FeatureCommentCreate, FeatureCommentResponse
)
from .service import FeatureService

router = APIRouter(prefix="/features", tags=["features"])

@router.post("/", response_model=FeatureRequestResponse)
async def create_feature_request(
    request: FeatureRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new feature request"""
    service = FeatureService(db)
    return service.create_feature_request(request, current_user.id)

@router.get("/", response_model=List[FeatureRequestResponse])
async def get_feature_requests(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: str = Query("votes", description="votes, created_at, priority"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get feature requests with optional filtering and sorting"""
    service = FeatureService(db)
    return service.get_feature_requests(
        category=category,
        status=status,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )

@router.get("/{feature_id}", response_model=FeatureRequestResponse)
async def get_feature_request(
    feature_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific feature request"""
    service = FeatureService(db)
    feature = service.get_feature_request(feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature request not found")
    return feature

@router.post("/{feature_id}/vote")
async def vote_on_feature(
    feature_id: str,
    vote: FeatureVoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vote on a feature request"""
    service = FeatureService(db)
    return service.vote_on_feature(feature_id, vote.vote_type, current_user.id)

@router.post("/{feature_id}/comments", response_model=FeatureCommentResponse)
async def add_comment(
    feature_id: str,
    comment: FeatureCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a feature request"""
    service = FeatureService(db)
    return service.add_comment(feature_id, comment.content, current_user.id)

@router.get("/{feature_id}/comments", response_model=List[FeatureCommentResponse])
async def get_comments(
    feature_id: str,
    db: Session = Depends(get_db)
):
    """Get comments for a feature request"""
    service = FeatureService(db)
    return service.get_comments(feature_id)

@router.put("/{feature_id}")
async def update_feature_request(
    feature_id: str,
    update: FeatureRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a feature request (admin only)"""
    # TODO: Add admin check
    service = FeatureService(db)
    return service.update_feature_request(feature_id, update)

@router.delete("/{feature_id}")
async def delete_feature_request(
    feature_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a feature request (admin or creator only)"""
    service = FeatureService(db)
    return service.delete_feature_request(feature_id, current_user.id)

@router.get("/stats/summary")
async def get_feature_stats(
    db: Session = Depends(get_db)
):
    """Get feature request statistics"""
    service = FeatureService(db)
    return service.get_feature_stats()
