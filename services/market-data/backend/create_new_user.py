#!/usr/bin/env python3
"""
Create a new user with known credentials
Alternative to resetting the test user
"""
from core.db.session import SessionLocal
from models.user import User
from api.v1.auth.service import AuthService

def create_new_user():
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # Create new user with unique email
        from api.v1.auth.schemas import UserRegistration
        
        user_data = UserRegistration(
            email="demo@tradesense.com",
            username="demouser",
            password="DemoPass123!",
            first_name="Demo",
            last_name="User"
        )
        
        # Check if user already exists
        existing = db.query(User).filter_by(email=user_data.email).first()
        if existing:
            print(f"ℹ️  User {user_data.email} already exists")
            print("\n🔑 Login credentials:")
            print(f"   Email: {user_data.email}")
            print(f"   Password: DemoPass123!")
        else:
            new_user = auth_service.create_user(user_data)
            print(f"✅ Created new user: {new_user.email}")
            print(f"   Username: {new_user.username}")
            print("\n🔑 Login credentials:")
            print(f"   Email: {user_data.email}")
            print(f"   Password: DemoPass123!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTip: Make sure the backend is running before executing this script")
    finally:
        db.close()

if __name__ == "__main__":
    create_new_user()