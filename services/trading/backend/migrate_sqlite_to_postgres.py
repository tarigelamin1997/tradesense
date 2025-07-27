#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL
"""
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
import sys
import os

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from models import User, Trade, Portfolio, TradingAccount, Playbook, Tag, TradeNote, TradeReview
from core.db.session import Base

def parse_datetime(date_str):
    """Parse datetime string to Python datetime object"""
    if not date_str:
        return None
    
    # Try different formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    print(f"Warning: Could not parse date '{date_str}'")
    return None

def migrate_data():
    """Migrate all data from SQLite to PostgreSQL"""
    print("🚀 Starting migration from SQLite to PostgreSQL...")
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('tradesense.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    pg_engine = create_engine('postgresql://postgres:postgres@localhost/tradesense')
    Session = sessionmaker(bind=pg_engine)
    pg_session = Session()
    
    try:
        # Clear existing data in PostgreSQL (optional - comment out if you want to append)
        print("⚠️  Clearing existing PostgreSQL data...")
        pg_session.query(TradeNote).delete()
        pg_session.query(TradeReview).delete()
        pg_session.query(Trade).delete()
        pg_session.query(Portfolio).delete()
        pg_session.query(TradingAccount).delete()
        pg_session.query(Playbook).delete()
        pg_session.query(Tag).delete()
        pg_session.query(User).delete()
        pg_session.commit()
        
        # Migrate Users
        print("\n📤 Migrating users...")
        users = sqlite_cursor.execute("SELECT * FROM users").fetchall()
        user_map = {}  # Map old IDs to new IDs
        
        for user in users:
            new_user = User(
                id=user['id'],
                email=user['email'],
                username=user['username'],
                hashed_password=user['hashed_password'],
                first_name=user['first_name'],
                last_name=user['last_name'],
                is_active=bool(user['is_active']) if user['is_active'] is not None else True,
                is_verified=bool(user['is_verified']) if user['is_verified'] is not None else False,
                verification_token=user['verification_token'],
                reset_password_token=user['reset_password_token'],
                reset_password_expires=parse_datetime(user['reset_password_expires']),
                last_login=parse_datetime(user['last_login']),
                created_at=parse_datetime(user['created_at']) or datetime.utcnow(),
                updated_at=parse_datetime(user['updated_at']) or datetime.utcnow(),
                trading_experience=user['trading_experience'],
                preferred_markets=user['preferred_markets'],
                timezone=user['timezone'] or 'UTC'
            )
            pg_session.add(new_user)
            user_map[user['id']] = new_user.id
            print(f"  ✅ Migrated user: {user['email']}")
        
        pg_session.commit()
        print(f"✅ Migrated {len(users)} users")
        
        # Migrate Portfolios
        print("\n📤 Migrating portfolios...")
        try:
            portfolios = sqlite_cursor.execute("SELECT * FROM portfolios").fetchall()
            for portfolio in portfolios:
                new_portfolio = Portfolio(
                    id=portfolio['id'],
                    user_id=portfolio['user_id'],
                    name=portfolio['name'],
                    initial_balance=float(portfolio['initial_balance']) if portfolio['initial_balance'] else 0.0,
                    current_balance=float(portfolio['current_balance']) if portfolio['current_balance'] else 0.0,
                    currency=portfolio['currency'] or 'USD',
                    created_at=parse_datetime(portfolio['created_at']) or datetime.utcnow(),
                    updated_at=parse_datetime(portfolio['updated_at']) or datetime.utcnow()
                )
                pg_session.add(new_portfolio)
            pg_session.commit()
            print(f"✅ Migrated {len(portfolios)} portfolios")
        except Exception as e:
            print(f"⚠️  Error migrating portfolios: {e}")
        
        # Migrate Trades
        print("\n📤 Migrating trades...")
        trades = sqlite_cursor.execute("SELECT * FROM trades").fetchall()
        trade_map = {}
        
        for trade in trades:
            # Generate new ID if needed
            trade_id = trade['id'] if trade['id'] else str(uuid.uuid4())
            
            new_trade = Trade(
                id=trade_id,
                user_id=trade['user_id'],
                symbol=trade['symbol'],
                entry_time=parse_datetime(trade['entry_time']),
                exit_time=parse_datetime(trade['exit_time']),
                entry_price=float(trade['entry_price']) if trade['entry_price'] else None,
                exit_price=float(trade['exit_price']) if trade['exit_price'] else None,
                quantity=int(trade['quantity']) if trade['quantity'] else None,
                trade_type=trade['trade_type'],
                pnl=float(trade['pnl']) if trade['pnl'] else None,
                pnl_percentage=float(trade['pnl_percentage']) if trade['pnl_percentage'] else None,
                strategy_id=trade['strategy_id'],
                emotions_before=trade['emotions_before'],
                emotions_after=trade['emotions_after'],
                confidence_level=int(trade['confidence_level']) if trade['confidence_level'] else None,
                created_at=parse_datetime(trade['created_at']) or datetime.utcnow()
            )
            pg_session.add(new_trade)
            trade_map[trade['id']] = trade_id
            
        pg_session.commit()
        print(f"✅ Migrated {len(trades)} trades")
        
        # Migrate Trade Notes
        print("\n📤 Migrating trade notes...")
        try:
            notes = sqlite_cursor.execute("SELECT * FROM trade_notes").fetchall()
            for note in notes:
                if note['trade_id'] in trade_map:
                    new_note = TradeNote(
                        id=note['id'],
                        trade_id=trade_map[note['trade_id']],
                        user_id=note['user_id'],
                        content=note['content'],
                        note_type=note['note_type'],
                        created_at=parse_datetime(note['created_at']) or datetime.utcnow()
                    )
                    pg_session.add(new_note)
            pg_session.commit()
            print(f"✅ Migrated {len(notes)} trade notes")
        except Exception as e:
            print(f"⚠️  Error migrating trade notes: {e}")
        
        # Migrate Tags
        print("\n📤 Migrating tags...")
        try:
            tags = sqlite_cursor.execute("SELECT * FROM tags").fetchall()
            for tag in tags:
                new_tag = Tag(
                    id=tag['id'],
                    name=tag['name'],
                    color=tag['color'],
                    created_at=parse_datetime(tag['created_at']) or datetime.utcnow()
                )
                pg_session.add(new_tag)
            pg_session.commit()
            print(f"✅ Migrated {len(tags)} tags")
        except Exception as e:
            print(f"⚠️  Error migrating tags: {e}")
        
        print("\n✅ Migration completed successfully!")
        
        # Verify migration
        print("\n📊 Verification:")
        print(f"  Users in PostgreSQL: {pg_session.query(User).count()}")
        print(f"  Trades in PostgreSQL: {pg_session.query(Trade).count()}")
        print(f"  Portfolios in PostgreSQL: {pg_session.query(Portfolio).count()}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        pg_session.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_session.close()

if __name__ == "__main__":
    migrate_data()