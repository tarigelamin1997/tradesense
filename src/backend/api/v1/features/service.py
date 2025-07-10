from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from models.feature_request import FeatureRequest, FeatureVote, FeatureComment
from models.user import User
from api.v1.features.schemas import (
    FeatureRequestCreate, FeatureRequestUpdate, 
    FeatureVoteCreate, FeatureCommentCreate
)
import uuid
from datetime import datetime

class FeatureService:
    @staticmethod
    def get_features(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "votes"
    ) -> List[FeatureRequest]:
        """Get feature requests with optional filtering and sorting."""
        query = db.query(FeatureRequest)

        # Apply filters
        if category and category != "all":
            query = query.filter(FeatureRequest.category == category)
        if status and status != "all":
            query = query.filter(FeatureRequest.status == status)

        # Apply sorting
        if sort_by == "votes":
            query = query.order_by(desc(FeatureRequest.upvotes - FeatureRequest.downvotes))
        elif sort_by == "newest":
            query = query.order_by(desc(FeatureRequest.created_at))
        elif sort_by == "oldest":
            query = query.order_by(asc(FeatureRequest.created_at))
        elif sort_by == "priority":
            priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            query = query.order_by(
                desc(FeatureRequest.priority.op("IN")(priority_order.keys()))
            )

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_feature_by_id(db: Session, feature_id: str) -> Optional[FeatureRequest]:
        """Get a specific feature request by ID."""
        return db.query(FeatureRequest).filter(FeatureRequest.id == feature_id).first()

    @staticmethod
    def create_feature_request(
        db: Session, 
        feature_data: FeatureRequestCreate, 
        user_id: str
    ) -> FeatureRequest:
        """Create a new feature request."""
        feature = FeatureRequest(
            id=str(uuid.uuid4()),
            title=feature_data.title,
            description=feature_data.description,
            category=feature_data.category,
            priority=feature_data.priority or "medium",
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(feature)
        db.commit()
        db.refresh(feature)
        return feature

    @staticmethod
    def update_feature_request(
        db: Session,
        feature_id: str,
        update_data: FeatureRequestUpdate,
        user_id: str
    ) -> Optional[FeatureRequest]:
        """Update a feature request (admin only for status changes)."""
        feature = db.query(FeatureRequest).filter(FeatureRequest.id == feature_id).first()
        if not feature:
            return None

        # Only allow user to edit their own features or admin to edit status
        if feature.user_id == user_id:
            if update_data.title:
                feature.title = update_data.title
            if update_data.description:
                feature.description = update_data.description
            if update_data.category:
                feature.category = update_data.category

        # Admin-only fields (you'd need to check if user is admin)
        if update_data.status:
            feature.status = update_data.status
        if update_data.priority:
            feature.priority = update_data.priority
        if update_data.admin_notes:
            feature.admin_notes = update_data.admin_notes

        feature.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(feature)
        return feature

    @staticmethod
    def vote_on_feature(
        db: Session,
        vote_data: FeatureVoteCreate,
        user_id: str
    ) -> bool:
        """Vote on a feature request."""
        # Check if user already voted
        existing_vote = db.query(FeatureVote).filter(
            FeatureVote.feature_request_id == vote_data.feature_request_id,
            FeatureVote.user_id == user_id
        ).first()

        feature = db.query(FeatureRequest).filter(
            FeatureRequest.id == vote_data.feature_request_id
        ).first()

        if not feature:
            return False

        if existing_vote:
            # Update existing vote
            if existing_vote.vote_type != vote_data.vote_type:
                # Remove old vote count
                if existing_vote.vote_type == "upvote":
                    feature.upvotes = max(0, feature.upvotes - 1)
                else:
                    feature.downvotes = max(0, feature.downvotes - 1)

                # Add new vote count
                if vote_data.vote_type == "upvote":
                    feature.upvotes += 1
                else:
                    feature.downvotes += 1

                existing_vote.vote_type = vote_data.vote_type
        else:
            # Create new vote
            vote = FeatureVote(
                id=str(uuid.uuid4()),
                feature_request_id=vote_data.feature_request_id,
                user_id=user_id,
                vote_type=vote_data.vote_type,
                created_at=datetime.utcnow()
            )

            # Update vote counts
            if vote_data.vote_type == "upvote":
                feature.upvotes += 1
            else:
                feature.downvotes += 1

            db.add(vote)

        feature.updated_at = datetime.utcnow()
        db.commit()
        return True

    @staticmethod
    def add_comment(
        db: Session,
        comment_data: FeatureCommentCreate,
        user_id: str
    ) -> FeatureComment:
        """Add a comment to a feature request."""
        comment = FeatureComment(
            id=str(uuid.uuid4()),
            feature_request_id=comment_data.feature_request_id,
            user_id=user_id,
            content=comment_data.content,
            created_at=datetime.utcnow()
        )

        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def get_feature_comments(
        db: Session,
        feature_id: str
    ) -> List[FeatureComment]:
        """Get comments for a feature request."""
        return db.query(FeatureComment)\
            .filter(FeatureComment.feature_request_id == feature_id)\
            .order_by(asc(FeatureComment.created_at))\
            .all()