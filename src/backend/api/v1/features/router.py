from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from api.deps import get_current_user, get_db
from models.user import User
from models.feature_request import FeatureRequest, FeatureVote, FeatureComment
from .schemas import (
    FeatureRequestCreate, FeatureRequestUpdate, FeatureRequestResponse,
    FeatureVoteCreate, FeatureCommentCreate, FeatureCommentResponse
)
from .service import FeatureService

router = APIRouter(tags=["features"])

@router.post("/", response_model=FeatureRequestResponse)
async def create_feature_request(
    request: FeatureRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new feature request"""
    try:
        feature = FeatureService.create_feature_request(
            db=db,
            feature_data=request,
            user_id=current_user.id
        )
        return feature
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating feature request: {str(e)}")

@router.get("/", response_model=List[FeatureRequestResponse])
async def get_feature_requests(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: str = Query("votes", regex="^(votes|newest|oldest|priority)$")
):
    """Get feature requests with optional filtering and sorting."""
    try:
        features = FeatureService.get_features(
            db=db,
            skip=skip,
            limit=limit,
            category=category,
            status=status,
            sort_by=sort_by
        )
        return features
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching features: {str(e)}")

@router.get("/{feature_id}", response_model=FeatureRequestResponse)
async def get_feature_request(
    feature_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific feature request"""
    feature = FeatureService.get_feature_by_id(db=db, feature_id=feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature request not found")
    return feature

@router.post("/{feature_id}/vote", status_code=200)
async def vote_on_feature(
    feature_id: str,
    vote_data: FeatureVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vote on a feature request"""
    vote_data.feature_request_id = feature_id
    
    success = FeatureService.vote_on_feature(
        db=db,
        vote_data=vote_data,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Feature request not found")
    return {"message": "Vote recorded successfully"}

@router.post("/{feature_id}/comments", response_model=FeatureCommentResponse, status_code=201)
async def add_comment(
    feature_id: str,
    comment_data: FeatureCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a feature request"""
    comment_data.feature_request_id = feature_id
    
    try:
        comment = FeatureService.add_comment(
            db=db,
            comment_data=comment_data,
            user_id=current_user.id
        )
        return comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")

@router.get("/{feature_id}/comments", response_model=List[FeatureCommentResponse])
async def get_feature_comments(
    feature_id: str,
    db: Session = Depends(get_db)
):
    """Get comments for a feature request"""
    comments = FeatureService.get_feature_comments(db=db, feature_id=feature_id)
    return comments

@router.put("/{feature_id}", response_model=FeatureRequestResponse)
async def update_feature_request(
    feature_id: str,
    update_data: FeatureRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a feature request"""
    feature = FeatureService.update_feature_request(
        db=db,
        feature_id=feature_id,
        update_data=update_data,
        user_id=current_user.id
    )
    if not feature:
        raise HTTPException(status_code=404, detail="Feature request not found")
    return feature

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
