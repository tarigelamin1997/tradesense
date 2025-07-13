#!/usr/bin/env python3
"""
Quick script to seed the database with sample trade data.
This allows us to test the analytics dashboard without fixing the upload UI.
"""

import sys
import os
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db.session import get_db
from models.trade import Trade
from models.user import User
import bcrypt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_user(db: Session):
    """Create a test user if it doesn't exist."""
    test_email = "test@example.com"
    existing_user = db.query(User).filter(User.email == test_email).first()
    
    if existing_user:
        logger.info(f"User {test_email} already exists")
        return existing_user
    
    # Hash the password using bcrypt
    password = "Password123!"
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    user = User(
        email=test_email,
        username="testuser",
        hashed_password=password_hash,  # Note: field is hashed_password, not password_hash
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created test user: {test_email}")
    return user

def load_trades_from_csv(csv_path: str, user_id: str, db: Session):
    """Load trades from CSV file into the database."""
    # Read the CSV file
    df = pd.read_csv(csv_path)
    logger.info(f"Loading {len(df)} trades from {csv_path}")
    
    trades_added = 0
    for _, row in df.iterrows():
        try:
            # Parse datetime strings
            entry_time = pd.to_datetime(row['entry_time'])
            exit_time = pd.to_datetime(row['exit_time'])
            
            # Create trade object
            trade = Trade(
                user_id=user_id,
                symbol=row['symbol'],
                entry_time=entry_time,
                exit_time=exit_time,
                entry_price=float(row['entry_price']),
                exit_price=float(row['exit_price']),
                quantity=int(row['qty']),
                direction=row['direction'],  # 'long' or 'short'
                pnl=float(row['pnl']),
                # Optional fields with defaults
                confidence_score=7,  # Default confidence
                notes=f"Trade from {row.get('broker', 'Unknown')} broker",
                emotional_tags=['focused', 'disciplined'] if float(row['pnl']) > 0 else ['anxious'],
                post_trade_mood='satisfied' if float(row['pnl']) > 0 else ['disappointed'],
                executed_plan=True
            )
            
            db.add(trade)
            trades_added += 1
            
        except Exception as e:
            logger.error(f"Error adding trade for row {_}: {e}")
            continue
    
    # Commit all trades
    db.commit()
    logger.info(f"Successfully added {trades_added} trades to the database")
    return trades_added

def main():
    """Main function to seed the database."""
    # CSV file path
    csv_path = "/home/tarigelamin/Desktop/tradesense/attached_assets/Demo_TradeSense_Sample_Data_1750284653019.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create or get test user
        user = create_test_user(db)
        
        # Check if user already has trades
        existing_trades = db.query(Trade).filter(Trade.user_id == user.id).count()
        if existing_trades > 0:
            logger.info(f"User already has {existing_trades} trades")
            response = input("Do you want to add more trades? (y/n): ")
            if response.lower() != 'y':
                return
        
        # Load trades from CSV
        trades_added = load_trades_from_csv(csv_path, user.id, db)
        
        # Show summary
        total_trades = db.query(Trade).filter(Trade.user_id == user.id).count()
        from sqlalchemy import func
        total_pnl = db.query(func.sum(Trade.pnl)).filter(Trade.user_id == user.id).scalar() or 0
        
        logger.info(f"\n=== Summary ===")
        logger.info(f"User: {user.email}")
        logger.info(f"Total trades: {total_trades}")
        logger.info(f"Total P&L: ${total_pnl:.2f}")
        logger.info(f"\nYou can now login with:")
        logger.info(f"Email: {user.email}")
        logger.info(f"Password: Password123!")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()