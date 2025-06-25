
"""
User service layer - handles all user management business logic
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from backend.models.user import User, UserCreate, UserRead, UserUpdate
from backend.core.security import SecurityManager
from backend.core.exceptions import ValidationError, BusinessLogicError, NotFoundError

logger = logging.getLogger(__name__)


class UserService:
    """User service handling user management operations"""
    
    def __init__(self):
        self.security_manager = SecurityManager()
    
    async def create_user(self, db: Session, user_data: UserCreate) -> UserRead:
        """Create a new user"""
        try:
            # Check if username or email already exists
            existing_user = db.query(User).filter(
                (User.username == user_data.username) | (User.email == user_data.email)
            ).first()
            
            if existing_user:
                if existing_user.username == user_data.username:
                    raise ValidationError("Username already exists")
                else:
                    raise ValidationError("Email already exists")
            
            # Hash password
            hashed_password = self.security_manager.hash_password(user_data.password)
            
            # Create user record
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                role=user_data.role,
                is_active=True
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"User {user_data.username} created successfully")
            
            return UserRead.from_orm(db_user)
            
        except (ValidationError, BusinessLogicError):
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error creating user {user_data.username}: {str(e)}")
            raise ValidationError("Username or email already exists")
        except Exception as e:
            db.rollback()
            logger.error(f"User creation failed for {user_data.username}: {str(e)}")
            raise BusinessLogicError(f"User creation failed: {str(e)}")
    
    async def get_users(self, db: Session, skip: int = 0, limit: int = 100, 
                       role_filter: Optional[str] = None, 
                       active_only: bool = True) -> List[UserRead]:
        """Get list of users with filtering"""
        try:
            query = db.query(User)
            
            if active_only:
                query = query.filter(User.is_active == True)
            
            if role_filter:
                query = query.filter(User.role == role_filter)
            
            users = query.offset(skip).limit(limit).all()
            
            return [UserRead.from_orm(user) for user in users]
            
        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            raise BusinessLogicError("Failed to retrieve users")
    
    async def get_user_by_id(self, db: Session, user_id: str) -> UserRead:
        """Get user by ID"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise NotFoundError("User not found")
            
            return UserRead.from_orm(user)
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            raise BusinessLogicError("Failed to retrieve user")
    
    async def update_user(self, db: Session, user_id: str, user_update: UserUpdate) -> UserRead:
        """Update user"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise NotFoundError("User not found")
            
            # Update fields
            update_data = user_update.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(user, field, value)
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"User {user_id} updated successfully")
            
            return UserRead.from_orm(user)
            
        except NotFoundError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"User update failed for {user_id}: {str(e)}")
            raise BusinessLogicError(f"User update failed: {str(e)}")
    
    async def soft_delete_user(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Soft delete user (set is_active = False)"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise NotFoundError("User not found")
            
            if not user.is_active:
                raise ValidationError("User is already inactive")
            
            user.is_active = False
            db.commit()
            
            logger.info(f"User {user_id} soft deleted successfully")
            
            return {"message": "User deactivated successfully", "user_id": user_id}
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"User soft delete failed for {user_id}: {str(e)}")
            raise BusinessLogicError(f"User deletion failed: {str(e)}")
    
    async def activate_user(self, db: Session, user_id: str) -> UserRead:
        """Activate user (set is_active = True)"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise NotFoundError("User not found")
            
            if user.is_active:
                raise ValidationError("User is already active")
            
            user.is_active = True
            db.commit()
            db.refresh(user)
            
            logger.info(f"User {user_id} activated successfully")
            
            return UserRead.from_orm(user)
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"User activation failed for {user_id}: {str(e)}")
            raise BusinessLogicError(f"User activation failed: {str(e)}")
