#!/usr/bin/env python3
"""Update all user passwords in PostgreSQL"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backend'))

from sqlalchemy import text
from passlib.context import CryptContext
from core.db.session import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def update_all_passwords():
    """Update all user passwords to TestPass123!"""
    password = "TestPass123!"
    password_hash = pwd_context.hash(password)
    
    db = SessionLocal()
    try:
        # Get all users
        result = db.execute(text("SELECT id, username, email FROM users"))
        users = result.fetchall()
        
        print(f"Found {len(users)} users to update:")
        
        for user in users:
            db.execute(
                text("UPDATE users SET hashed_password = :hash WHERE id = :id"),
                {"hash": password_hash, "id": user[0]}
            )
            print(f"  ✓ Updated password for {user[1]} ({user[2]})")
        
        db.commit()
        print(f"\n✅ All passwords updated to: {password}")
        print("\nYou can now login with any of these users using the password above.")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=== Update User Passwords in PostgreSQL ===\n")
    update_all_passwords()