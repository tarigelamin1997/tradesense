#!/usr/bin/env python3
"""
Reset test user password script
Run this when the backend is running to reset the test user
"""
from core.db.session import SessionLocal
from models.user import User
from api.v1.auth.service import AuthService

def reset_test_user():
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # Delete existing test user if exists
        existing = db.query(User).filter_by(email="test@example.com").first()
        if existing:
            db.delete(existing)
            db.commit()
            print("❌ Deleted existing test@example.com user")
        
        # Create new test user with known password
        from api.v1.auth.schemas import UserRegistration
        
        user_data = UserRegistration(
            email="test@example.com",
            username="testuser",
            password="Password123!",
            first_name="Test",
            last_name="User"
        )
        
        new_user = auth_service.create_user(user_data)
        print(f"✅ Created new test user: {new_user.email}")
        print(f"   Username: {new_user.username}")
        print(f"   Password: Password123!")
        print("\n🔑 Login credentials:")
        print("   Email: test@example.com")
        print("   Password: Password123!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTip: Make sure the backend is running before executing this script")
    finally:
        db.close()

if __name__ == "__main__":
    reset_test_user()