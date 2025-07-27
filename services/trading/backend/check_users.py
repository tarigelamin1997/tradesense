#!/usr/bin/env python3
from core.db.session import SessionLocal
from models.user import User

db = SessionLocal()
users = db.query(User).all()

print("\n📊 Existing Users in Database:")
print("-" * 50)
for user in users:
    print(f"Email: {user.email}")
    print(f"Username: {user.username}")
    print(f"ID: {user.id}")
    print(f"Active: {user.is_active}")
    print("-" * 50)

print(f"\nTotal users: {len(users)}")
db.close()