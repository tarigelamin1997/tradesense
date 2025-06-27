"""
Authentication Service

Handles user authentication, registration, and session management.
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.core.db.session import get_db
from backend.models.user import User
from sqlalchemy.exc import IntegrityError

from backend.api.v1.auth.schemas import UserRegistration, UserUpdate
from backend.core.exceptions import AuthenticationError, ValidationError


class AuthService:
    """Authentication service for user management"""

    def __init__(self, db: Session):
        self.db = db
        self.secret_key = "your-secret-key-here"  # In production, use environment variable
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
    def get_password_hash(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user ID"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except jwt.PyJWTError:
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: UserRegistration) -> User:
        """Create a new user"""
        # Check if user already exists
        if self.get_user_by_email(user_data.email):
            raise ValidationError("Email already registered")

        if self.get_user_by_username(user_data.username):
            raise ValidationError("Username already taken")

        # Create new user
        hashed_password = self.get_password_hash(user_data.password)

        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            trading_experience=user_data.trading_experience,
            preferred_markets=user_data.preferred_markets,
            timezone=user_data.timezone or "UTC"
        )

        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise ValidationError("User could not be created")

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()

        return user

    def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        # Update fields if provided
        if user_data.email and user_data.email != user.email:
            # Check if new email is already taken
            existing_user = self.get_user_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise ValidationError("Email already registered")
            user.email = user_data.email

        if user_data.username and user_data.username != user.username:
            # Check if new username is already taken
            existing_user = self.get_user_by_username(user_data.username)
            if existing_user and existing_user.id != user_id:
                raise ValidationError("Username already taken")
            user.username = user_data.username

        if user_data.first_name is not None:
            user.first_name = user_data.first_name

        if user_data.last_name is not None:
            user.last_name = user_data.last_name

        if user_data.trading_experience is not None:
            user.trading_experience = user_data.trading_experience

        if user_data.preferred_markets is not None:
            user.preferred_markets = user_data.preferred_markets

        if user_data.timezone is not None:
            user.timezone = user_data.timezone

        user.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValidationError("User could not be updated")

    def generate_password_reset_token(self, email: str) -> Optional[str]:
        """Generate password reset token"""
        user = self.get_user_by_email(email)
        if not user:
            return None

        # Create reset token (expires in 1 hour)
        reset_data = {
            "sub": user.id,
            "purpose": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(reset_data, self.secret_key, algorithm=self.algorithm)

        # Store reset token in user record
        user.reset_password_token = token
        user.reset_password_expires = datetime.utcnow() + timedelta(hours=1)
        self.db.commit()

        return token

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            purpose = payload.get("purpose")

            if purpose != "password_reset":
                return False

            user = self.get_user_by_id(user_id)
            if not user or user.reset_password_token != token:
                return False

            if user.reset_password_expires < datetime.utcnow():
                return False

            # Update password
            user.hashed_password = self.get_password_hash(new_password)
            user.reset_password_token = None
            user.reset_password_expires = None
            user.updated_at = datetime.utcnow()

            self.db.commit()
            return True

        except jwt.PyJWTError:
            return False

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def activate_user(self, user_id: str) -> bool:
        """Activate a user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True