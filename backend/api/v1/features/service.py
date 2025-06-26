
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.models.feature_request import FeatureRequest, FeatureVote, FeatureComment
from .schemas import FeatureRequestCreate, FeatureRequestUpdate

class FeatureService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_feature_request(self, request: FeatureRequestCreate, user_id: str) -> FeatureRequest:
        """Create a new feature request"""
        feature = FeatureRequest(
            title=request.title,
            description=request.description,
            category=request.category,
            user_id=user_id
        )
        
        self.db.add(feature)
        self.db.commit()
        self.db.refresh(feature)
        
        return self._add_computed_fields(feature, user_id)
    
    def get_feature_requests(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "votes",
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None
    ) -> List[FeatureRequest]:
        """Get feature requests with filtering and sorting"""
        query = self.db.query(FeatureRequest)
        
        # Apply filters
        if category:
            query = query.filter(FeatureRequest.category == category)
        if status:
            query = query.filter(FeatureRequest.status == status)
        
        # Apply sorting
        if sort_by == "votes":
            query = query.order_by(desc(FeatureRequest.upvotes - FeatureRequest.downvotes))
        elif sort_by == "created_at":
            query = query.order_by(desc(FeatureRequest.created_at))
        elif sort_by == "priority":
            # Custom priority ordering
            priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            query = query.order_by(
                desc(func.case(
                    [(FeatureRequest.priority == k, v) for k, v in priority_order.items()],
                    else_=0
                ))
            )
        
        features = query.offset(offset).limit(limit).all()
        return [self._add_computed_fields(f, user_id) for f in features]
    
    def get_feature_request(self, feature_id: str, user_id: Optional[str] = None) -> Optional[FeatureRequest]:
        """Get a specific feature request"""
        feature = self.db.query(FeatureRequest).filter(
            FeatureRequest.id == feature_id
        ).first()
        
        if feature:
            return self._add_computed_fields(feature, user_id)
        return None
    
    def vote_on_feature(self, feature_id: str, vote_type: str, user_id: str) -> Dict[str, Any]:
        """Vote on a feature request"""
        # Check if user already voted
        existing_vote = self.db.query(FeatureVote).filter(
            FeatureVote.feature_request_id == feature_id,
            FeatureVote.user_id == user_id
        ).first()
        
        feature = self.db.query(FeatureRequest).filter(
            FeatureRequest.id == feature_id
        ).first()
        
        if not feature:
            raise ValueError("Feature request not found")
        
        if existing_vote:
            # Update existing vote
            if existing_vote.vote_type != vote_type:
                # Remove old vote from count
                if existing_vote.vote_type == "upvote":
                    feature.upvotes = max(0, feature.upvotes - 1)
                else:
                    feature.downvotes = max(0, feature.downvotes - 1)
                
                # Update vote and add to new count
                existing_vote.vote_type = vote_type
                if vote_type == "upvote":
                    feature.upvotes += 1
                else:
                    feature.downvotes += 1
            # If same vote type, no change needed
        else:
            # Create new vote
            new_vote = FeatureVote(
                feature_request_id=feature_id,
                user_id=user_id,
                vote_type=vote_type
            )
            self.db.add(new_vote)
            
            # Update vote count
            if vote_type == "upvote":
                feature.upvotes += 1
            else:
                feature.downvotes += 1
        
        feature.updated_at = datetime.utcnow()
        self.db.commit()
        
        return {
            "success": True,
            "upvotes": feature.upvotes,
            "downvotes": feature.downvotes,
            "user_vote": vote_type
        }
    
    def add_comment(self, feature_id: str, content: str, user_id: str) -> FeatureComment:
        """Add a comment to a feature request"""
        comment = FeatureComment(
            feature_request_id=feature_id,
            user_id=user_id,
            content=content
        )
        
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        return comment
    
    def get_comments(self, feature_id: str) -> List[FeatureComment]:
        """Get comments for a feature request"""
        return self.db.query(FeatureComment).filter(
            FeatureComment.feature_request_id == feature_id
        ).order_by(FeatureComment.created_at).all()
    
    def update_feature_request(self, feature_id: str, update: FeatureRequestUpdate) -> Optional[FeatureRequest]:
        """Update a feature request (admin only)"""
        feature = self.db.query(FeatureRequest).filter(
            FeatureRequest.id == feature_id
        ).first()
        
        if not feature:
            return None
        
        update_data = update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feature, field, value)
        
        feature.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(feature)
        
        return feature
    
    def delete_feature_request(self, feature_id: str, user_id: str) -> bool:
        """Delete a feature request"""
        feature = self.db.query(FeatureRequest).filter(
            FeatureRequest.id == feature_id
        ).first()
        
        if not feature:
            return False
        
        # Only allow creator or admin to delete
        # TODO: Add admin check
        if feature.user_id != user_id:
            raise ValueError("Not authorized to delete this feature request")
        
        # Delete related votes and comments
        self.db.query(FeatureVote).filter(
            FeatureVote.feature_request_id == feature_id
        ).delete()
        
        self.db.query(FeatureComment).filter(
            FeatureComment.feature_request_id == feature_id
        ).delete()
        
        self.db.delete(feature)
        self.db.commit()
        
        return True
    
    def get_feature_stats(self) -> Dict[str, Any]:
        """Get feature request statistics"""
        total_requests = self.db.query(FeatureRequest).count()
        
        # Group by status
        status_counts = dict(
            self.db.query(FeatureRequest.status, func.count(FeatureRequest.id))
            .group_by(FeatureRequest.status)
            .all()
        )
        
        # Group by category
        category_counts = dict(
            self.db.query(FeatureRequest.category, func.count(FeatureRequest.id))
            .group_by(FeatureRequest.category)
            .all()
        )
        
        # Top voted features
        top_voted = self.db.query(FeatureRequest).order_by(
            desc(FeatureRequest.upvotes - FeatureRequest.downvotes)
        ).limit(5).all()
        
        # Recent features
        recent_requests = self.db.query(FeatureRequest).order_by(
            desc(FeatureRequest.created_at)
        ).limit(5).all()
        
        return {
            "total_requests": total_requests,
            "by_status": status_counts,
            "by_category": category_counts,
            "top_voted": [self._add_computed_fields(f) for f in top_voted],
            "recent_requests": [self._add_computed_fields(f) for f in recent_requests]
        }
    
    def _add_computed_fields(self, feature: FeatureRequest, user_id: Optional[str] = None) -> FeatureRequest:
        """Add computed fields to feature request"""
        feature.net_votes = feature.upvotes - feature.downvotes
        
        if user_id:
            user_vote = self.db.query(FeatureVote).filter(
                FeatureVote.feature_request_id == feature.id,
                FeatureVote.user_id == user_id
            ).first()
            feature.user_vote = user_vote.vote_type if user_vote else None
        
        return feature
