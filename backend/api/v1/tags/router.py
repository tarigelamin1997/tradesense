
"""
Tag management API endpoints
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.db.session import get_db
from backend.api.deps import get_current_active_user
from backend.api.v1.tags.schemas import (
    TagCreate, TagUpdate, TagResponse, TagListResponse
)
from backend.api.v1.tags.service import TagService
from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.response import create_response

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.post("/", response_model=TagResponse, status_code=201)
async def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create a new tag for the current user
    """
    try:
        tag = await TagService.create_tag(db, tag_data, current_user["user_id"])
        return tag
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=TagListResponse)
async def list_tags(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by tag name"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get all tags for the current user with pagination and search
    """
    result = await TagService.get_user_tags(
        db=db,
        user_id=current_user["user_id"],
        page=page,
        per_page=per_page,
        search=search
    )
    return result


@router.get("/popular", response_model=List[Dict[str, Any]])
async def get_popular_tags(
    limit: int = Query(10, ge=1, le=50, description="Number of popular tags to return"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get most frequently used tags for analytics and suggestions
    """
    popular_tags = await TagService.get_popular_tags(
        db=db,
        user_id=current_user["user_id"],
        limit=limit
    )
    return create_response(
        data=popular_tags,
        message=f"Retrieved {len(popular_tags)} popular tags"
    )


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific tag by ID
    """
    try:
        tag = await TagService.get_tag_by_id(db, tag_id, current_user["user_id"])
        return tag
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    tag_data: TagUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update an existing tag
    """
    try:
        tag = await TagService.update_tag(db, tag_id, tag_data, current_user["user_id"])
        return tag
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a tag and remove it from all trades
    """
    try:
        await TagService.delete_tag(db, tag_id, current_user["user_id"])
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")


@router.post("/trades/{trade_id}/assign")
async def assign_tags_to_trade(
    trade_id: str,
    tag_ids: List[str],
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Assign multiple tags to a specific trade
    """
    try:
        await TagService.assign_tags_to_trade(
            db=db,
            trade_id=trade_id,
            tag_ids=tag_ids,
            user_id=current_user["user_id"]
        )
        return create_response(
            message=f"Successfully assigned {len(tag_ids)} tags to trade"
        )
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/trades/{trade_id}/remove")
async def remove_tags_from_trade(
    trade_id: str,
    tag_ids: List[str],
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Remove specific tags from a trade
    """
    try:
        await TagService.remove_tags_from_trade(
            db=db,
            trade_id=trade_id,
            tag_ids=tag_ids,
            user_id=current_user["user_id"]
        )
        return create_response(
            message=f"Successfully removed {len(tag_ids)} tags from trade"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
