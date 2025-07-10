
"""
Tag service for managing trade tags
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from models.tag import Tag
from models.trade import Trade
from api.v1.tags.schemas import TagCreate, TagUpdate
from core.exceptions import NotFoundError, ValidationError


class TagService:
    """Service for tag operations"""

    @staticmethod
    async def create_tag(db: Session, tag_data: TagCreate, user_id: str) -> Tag:
        """Create a new tag for a user"""
        
        # Check if tag with same name already exists for this user
        existing_tag = db.query(Tag).filter(
            and_(Tag.user_id == user_id, Tag.name == tag_data.name)
        ).first()
        
        if existing_tag:
            raise ValidationError(f"Tag '{tag_data.name}' already exists")
        
        # Create new tag
        tag = Tag(
            user_id=user_id,
            name=tag_data.name,
            description=tag_data.description,
            color=tag_data.color
        )
        
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    @staticmethod
    async def get_user_tags(
        db: Session, 
        user_id: str,
        page: int = 1,
        per_page: int = 50,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all tags for a user with pagination"""
        
        query = db.query(Tag).filter(Tag.user_id == user_id)
        
        # Apply search filter if provided
        if search:
            query = query.filter(Tag.name.contains(search.lower()))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        tags = query.order_by(Tag.name).offset(offset).limit(per_page).all()
        
        # Add trade count for each tag
        for tag in tags:
            trade_count = db.query(func.count(Trade.id)).join(
                Trade.tag_objects
            ).filter(Tag.id == tag.id).scalar()
            tag.trade_count = trade_count or 0
        
        return {
            "tags": tags,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "has_more": total_count > page * per_page
        }

    @staticmethod
    async def get_tag_by_id(db: Session, tag_id: str, user_id: str) -> Tag:
        """Get a specific tag by ID for a user"""
        
        tag = db.query(Tag).filter(
            and_(Tag.id == tag_id, Tag.user_id == user_id)
        ).first()
        
        if not tag:
            raise NotFoundError("Tag not found")
        
        # Add trade count
        trade_count = db.query(func.count(Trade.id)).join(
            Trade.tag_objects
        ).filter(Tag.id == tag.id).scalar()
        tag.trade_count = trade_count or 0
        
        return tag

    @staticmethod
    async def update_tag(
        db: Session, 
        tag_id: str, 
        tag_data: TagUpdate, 
        user_id: str
    ) -> Tag:
        """Update an existing tag"""
        
        tag = await TagService.get_tag_by_id(db, tag_id, user_id)
        
        # Check for name conflicts if name is being updated
        if tag_data.name and tag_data.name != tag.name:
            existing_tag = db.query(Tag).filter(
                and_(
                    Tag.user_id == user_id, 
                    Tag.name == tag_data.name,
                    Tag.id != tag_id
                )
            ).first()
            
            if existing_tag:
                raise ValidationError(f"Tag '{tag_data.name}' already exists")
        
        # Update fields
        for field, value in tag_data.dict(exclude_unset=True).items():
            setattr(tag, field, value)
        
        db.commit()
        db.refresh(tag)
        return tag

    @staticmethod
    async def delete_tag(db: Session, tag_id: str, user_id: str) -> bool:
        """Delete a tag and remove it from all trades"""
        
        tag = await TagService.get_tag_by_id(db, tag_id, user_id)
        
        # Remove tag from all trades (cascade handled by relationship)
        db.delete(tag)
        db.commit()
        return True

    @staticmethod
    async def get_popular_tags(db: Session, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently used tags for a user"""
        
        popular_tags = db.query(
            Tag.id,
            Tag.name,
            Tag.color,
            func.count(Trade.id).label('usage_count')
        ).join(
            Tag.trades
        ).filter(
            Tag.user_id == user_id
        ).group_by(
            Tag.id, Tag.name, Tag.color
        ).order_by(
            func.count(Trade.id).desc()
        ).limit(limit).all()
        
        return [
            {
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
                "usage_count": tag.usage_count
            }
            for tag in popular_tags
        ]

    @staticmethod
    async def assign_tags_to_trade(
        db: Session, 
        trade_id: str, 
        tag_ids: List[str], 
        user_id: str
    ) -> None:
        """Assign multiple tags to a trade"""
        
        # Get trade
        trade = db.query(Trade).filter(
            and_(Trade.id == trade_id, Trade.user_id == user_id)
        ).first()
        
        if not trade:
            raise NotFoundError("Trade not found")
        
        # Get valid tags for this user
        tags = db.query(Tag).filter(
            and_(Tag.id.in_(tag_ids), Tag.user_id == user_id)
        ).all()
        
        if len(tags) != len(tag_ids):
            raise ValidationError("Some tags were not found or don't belong to this user")
        
        # Clear existing tags and assign new ones
        trade.tag_objects.clear()
        trade.tag_objects.extend(tags)
        
        db.commit()

    @staticmethod
    async def remove_tags_from_trade(
        db: Session, 
        trade_id: str, 
        tag_ids: List[str], 
        user_id: str
    ) -> None:
        """Remove specific tags from a trade"""
        
        # Get trade
        trade = db.query(Trade).filter(
            and_(Trade.id == trade_id, Trade.user_id == user_id)
        ).first()
        
        if not trade:
            raise NotFoundError("Trade not found")
        
        # Remove specified tags
        tags_to_remove = [tag for tag in trade.tag_objects if tag.id in tag_ids]
        for tag in tags_to_remove:
            trade.tag_objects.remove(tag)
        
        db.commit()
