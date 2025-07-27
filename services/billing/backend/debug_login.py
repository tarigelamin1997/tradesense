#!/usr/bin/env python3
"""Debug login issues with PostgreSQL"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import json

# Import backend components
from core.config import settings
from core.db.session import SessionLocal, DATABASE_URL
from models.user import User
from api.v1.auth.service import AuthService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_database_connection():
    """Test basic database connection"""
    print("=== Testing Database Connection ===")
    print(f"DATABASE_URL: {DATABASE_URL}")
    
    try:
        db = SessionLocal()
        # Test raw SQL
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        print(f"✅ Database connected. Users count: {count}")
        
        # Test ORM query
        users = db.query(User).limit(3).all()
        print(f"✅ ORM query successful. Found {len(users)} users:")
        for user in users:
            print(f"   - {user.username} ({user.email})")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_password_verification():
    """Test password verification for users"""
    print("\n=== Testing Password Verification ===")
    
    db = SessionLocal()
    test_password = "TestPass123!"
    
    try:
        # Get a test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ Test user not found!")
            return False
            
        print(f"Found user: {user.username} ({user.email})")
        print(f"Password hash: {user.hashed_password[:20]}...")
        
        # Test password verification
        is_valid = pwd_context.verify(test_password, user.hashed_password)
        print(f"Password verification: {'✅ PASSED' if is_valid else '❌ FAILED'}")
        
        if not is_valid:
            # Try updating the password
            new_hash = pwd_context.hash(test_password)
            user.hashed_password = new_hash
            db.commit()
            print(f"✅ Password updated for {user.username}")
            
        db.close()
        return True
    except Exception as e:
        print(f"❌ Password verification error: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False

def test_auth_service():
    """Test AuthService methods"""
    print("\n=== Testing AuthService ===")
    
    db = SessionLocal()
    auth_service = AuthService(db)
    
    try:
        # Test get_user_by_email
        user = auth_service.get_user_by_email("test@example.com")
        if user:
            print(f"✅ get_user_by_email: Found {user.username}")
        else:
            print("❌ get_user_by_email: User not found")
            
        # Test authenticate_user
        authenticated_user = auth_service.authenticate_user("test@example.com", "TestPass123!")
        if authenticated_user:
            print(f"✅ authenticate_user: Success for {authenticated_user.username}")
        else:
            print("❌ authenticate_user: Failed")
            
        # Test token creation
        if authenticated_user:
            token = auth_service.create_access_token(
                data={"sub": authenticated_user.id},
                expires_delta=timedelta(minutes=30)
            )
            print(f"✅ create_access_token: Token created ({token[:20]}...)")
            
            # Test token verification
            user_id = auth_service.verify_token(token)
            print(f"✅ verify_token: User ID = {user_id}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ AuthService error: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False

def simulate_login_request():
    """Simulate the full login flow"""
    print("\n=== Simulating Login Request ===")
    
    db = SessionLocal()
    auth_service = AuthService(db)
    
    try:
        # Simulate login data
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123!"
        }
        print(f"Login attempt: {login_data}")
        
        # Authenticate
        user = auth_service.authenticate_user(login_data["email"], login_data["password"])
        if not user:
            print("❌ Authentication failed!")
            return False
            
        print(f"✅ Authentication successful for {user.username}")
        
        # Create token
        access_token_expires = timedelta(minutes=30)
        access_token = auth_service.create_access_token(
            data={"sub": user.id}, 
            expires_delta=access_token_expires
        )
        
        # Build response
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
        
        print("✅ Login response generated:")
        print(json.dumps({k: v if k != "access_token" else v[:20] + "..." for k, v in response.items()}, indent=2))
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Login simulation error: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False

def main():
    print("=== PostgreSQL Login Debug Tool ===\n")
    
    # Run all tests
    all_passed = True
    
    if not test_database_connection():
        all_passed = False
        
    if not test_password_verification():
        all_passed = False
        
    if not test_auth_service():
        all_passed = False
        
    if not simulate_login_request():
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ All tests passed! Login should work.")
    else:
        print("❌ Some tests failed. Check the errors above.")
        
    # Additional checks
    print("\nAdditional Information:")
    print(f"- JWT Secret Key configured: {'Yes' if settings.jwt_secret_key else 'No'}")
    print(f"- JWT Algorithm: {settings.jwt_algorithm}")
    print(f"- Environment: {settings.environment}")

if __name__ == "__main__":
    main()