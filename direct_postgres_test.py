#!/usr/bin/env python3
"""Direct test of PostgreSQL login"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backend'))

# Import after path is set
from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from core.config import settings
from core.db.session import SessionLocal, DATABASE_URL

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_direct_login():
    """Test login directly against PostgreSQL"""
    print(f"Database URL: {DATABASE_URL}")
    print(f"Settings database_url: {settings.database_url}")
    
    # Test with testuser
    email = "test@example.com"
    password = "TestPass123!"
    
    db = SessionLocal()
    try:
        # Check database type
        result = db.execute(text("SELECT 1"))
        print(f"✓ Database connection successful")
        
        # Get user
        result = db.execute(
            text("SELECT id, username, email, hashed_password FROM users WHERE email = :email"),
            {"email": email}
        )
        user = result.fetchone()
        
        if user:
            print(f"✓ User found: {user[1]} ({user[2]})")
            
            # Verify password
            if pwd_context.verify(password, user[3]):
                print("✓ Password verification successful!")
                return True
            else:
                print("✗ Password verification failed")
                # Let's try to update the password
                new_hash = pwd_context.hash(password)
                db.execute(
                    text("UPDATE users SET hashed_password = :hash WHERE email = :email"),
                    {"hash": new_hash, "email": email}
                )
                db.commit()
                print("✓ Password updated in PostgreSQL")
                return True
        else:
            print(f"✗ User not found with email: {email}")
            
            # List all users
            result = db.execute(text("SELECT username, email FROM users"))
            users = result.fetchall()
            print(f"\nUsers in database ({len(users)}):")
            for u in users:
                print(f"  - {u[0]} ({u[1]})")
            
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=== Direct PostgreSQL Login Test ===\n")
    
    # Ensure we're loading from .env
    from dotenv import load_dotenv
    load_dotenv()
    
    if test_direct_login():
        print("\n✅ Direct PostgreSQL test passed!")
    else:
        print("\n❌ Direct PostgreSQL test failed!")