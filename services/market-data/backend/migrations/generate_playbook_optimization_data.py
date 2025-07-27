
#!/usr/bin/env python3
"""
Generate Sample Data for Playbook Optimization Engine Testing

This script creates realistic sample playbooks and trades to test the optimization engine.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'tradesense.db')
    return sqlite3.connect(db_path)

def create_sample_playbooks() -> List[Dict]:
    """Create sample playbooks with different characteristics"""
    playbooks = [
        {
            "name": "Momentum Breakout",
            "entry_criteria": "Price breaks above resistance with volume spike",
            "exit_criteria": "Take profit at 2:1 R/R or stop loss at support",
            "description": "High-momentum breakout strategy for trending markets"
        },
        {
            "name": "Mean Reversion",
            "entry_criteria": "Price touches lower Bollinger Band with RSI < 30",
            "exit_criteria": "Exit at middle BB or RSI > 70",
            "description": "Counter-trend strategy for range-bound markets"
        },
        {
            "name": "News Event Trading",
            "entry_criteria": "Enter on news catalysts with strong fundamentals",
            "exit_criteria": "Quick scalp, exit within 30 minutes",
            "description": "Event-driven short-term trading strategy"
        },
        {
            "name": "Swing Reversal",
            "entry_criteria": "Hammer/doji at key support with confluence",
            "exit_criteria": "Exit at next resistance level",
            "description": "Multi-day swing trading approach"
        },
        {
            "name": "Gap Fill Strategy",
            "entry_criteria": "Trade overnight gaps > 2% with proper setup",
            "exit_criteria": "Exit when gap fills or stop loss triggered",
            "description": "Gap trading for mean reversion plays"
        }
    ]
    return playbooks

def generate_realistic_trades(playbook_id: str, playbook_name: str, num_trades: int) -> List[Dict]:
    """Generate realistic trades based on playbook characteristics"""
    trades = []
    base_date = datetime.now() - timedelta(days=90)  # Last 3 months
    
    # Define playbook-specific parameters
    playbook_params = {
        "Momentum Breakout": {
            "win_rate": 0.45,  # Lower win rate but higher reward
            "avg_win": 150,
            "avg_loss": -80,
            "confidence_bias": 7,  # Higher confidence
            "symbols": ["AAPL", "TSLA", "NVDA", "MSFT"],
            "preferred_hours": [9, 10, 14, 15]  # Market open and close
        },
        "Mean Reversion": {
            "win_rate": 0.65,  # Higher win rate but smaller wins
            "avg_win": 80,
            "avg_loss": -60,
            "confidence_bias": 6,
            "symbols": ["SPY", "QQQ", "IWM", "DIA"],
            "preferred_hours": [11, 12, 13, 14]  # Mid-day
        },
        "News Event Trading": {
            "win_rate": 0.55,
            "avg_win": 200,
            "avg_loss": -120,
            "confidence_bias": 8,  # Very confident on news
            "symbols": ["TSLA", "AMZN", "GOOGL", "META"],
            "preferred_hours": [9, 16]  # Market open and after hours
        },
        "Swing Reversal": {
            "win_rate": 0.58,
            "avg_win": 300,
            "avg_loss": -150,
            "confidence_bias": 5,  # More cautious
            "symbols": ["SPY", "AAPL", "MSFT", "GOOGL"],
            "preferred_hours": [10, 11, 15, 16]
        },
        "Gap Fill Strategy": {
            "win_rate": 0.70,  # High win rate strategy
            "avg_win": 100,
            "avg_loss": -45,
            "confidence_bias": 7,
            "symbols": ["QQQ", "SPY", "AAPL", "TSLA"],
            "preferred_hours": [9, 10]  # Early morning
        }
    }
    
    params = playbook_params.get(playbook_name, playbook_params["Mean Reversion"])
    
    for i in range(num_trades):
        # Generate entry time (weighted towards preferred hours)
        days_ago = random.randint(1, 90)
        if random.random() < 0.6:  # 60% chance of preferred hour
            hour = random.choice(params["preferred_hours"])
        else:
            hour = random.randint(9, 16)
        
        entry_time = base_date + timedelta(
            days=days_ago,
            hours=hour,
            minutes=random.randint(0, 59)
        )
        
        # Generate exit time (1 hour to 3 days later)
        hold_minutes = random.randint(60, 4320)  # 1 hour to 3 days
        exit_time = entry_time + timedelta(minutes=hold_minutes)
        
        # Determine if trade is winning
        is_winner = random.random() < params["win_rate"]
        
        # Generate PnL based on win/loss
        if is_winner:
            pnl = random.normalvariate(params["avg_win"], params["avg_win"] * 0.3)
        else:
            pnl = random.normalvariate(params["avg_loss"], abs(params["avg_loss"]) * 0.3)
        
        # Generate confidence score (biased towards playbook's typical confidence)
        confidence = max(1, min(10, int(random.normalvariate(params["confidence_bias"], 1.5))))
        
        # Generate entry/exit prices
        entry_price = round(random.uniform(50, 500), 2)
        if pnl > 0:
            exit_price = entry_price + (pnl / 100)  # Assuming 100 shares
        else:
            exit_price = entry_price + (pnl / 100)
        
        symbol = random.choice(params["symbols"])
        direction = random.choice(["long", "short"])
        
        trade = {
            "id": str(uuid.uuid4()),
            "playbook_id": playbook_id,
            "symbol": symbol,
            "direction": direction,
            "entry_time": entry_time.isoformat(),
            "exit_time": exit_time.isoformat(),
            "entry_price": entry_price,
            "exit_price": round(exit_price, 2),
            "quantity": 100,
            "pnl": round(pnl, 2),
            "confidence_score": confidence,
            "notes": f"Auto-generated {playbook_name} trade"
        }
        
        trades.append(trade)
    
    return trades

def main():
    print("🎯 Generating Playbook Optimization Engine Test Data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if we have any users
        cursor.execute("SELECT id FROM users LIMIT 1")
        user_result = cursor.fetchone()
        
        if not user_result:
            print("❌ No users found. Creating a test user...")
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, email, hashed_password, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, "test@tradesense.com", "hashed_pass", 1, datetime.now().isoformat()))
        else:
            user_id = user_result[0]
            print(f"✅ Using existing user: {user_id}")
        
        # Create sample playbooks
        playbooks_data = create_sample_playbooks()
        playbook_ids = []
        
        print(f"📚 Creating {len(playbooks_data)} sample playbooks...")
        
        for playbook_data in playbooks_data:
            playbook_id = str(uuid.uuid4())
            playbook_ids.append((playbook_id, playbook_data["name"]))
            
            cursor.execute("""
                INSERT INTO playbooks (id, user_id, name, entry_criteria, exit_criteria, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                playbook_id,
                user_id,
                playbook_data["name"],
                playbook_data["entry_criteria"],
                playbook_data["exit_criteria"],
                playbook_data["description"],
                "active",
                datetime.now().isoformat()
            ))
            
            print(f"  ✅ Created playbook: {playbook_data['name']}")
        
        # Generate trades for each playbook
        total_trades = 0
        
        for playbook_id, playbook_name in playbook_ids:
            # Vary the number of trades per playbook
            if "Momentum" in playbook_name:
                num_trades = random.randint(25, 40)  # High activity
            elif "News Event" in playbook_name:
                num_trades = random.randint(15, 25)  # Medium activity
            else:
                num_trades = random.randint(10, 30)  # Variable activity
            
            print(f"📊 Generating {num_trades} trades for {playbook_name}...")
            
            trades = generate_realistic_trades(playbook_id, playbook_name, num_trades)
            
            for trade in trades:
                cursor.execute("""
                    INSERT INTO trades (
                        id, user_id, playbook_id, symbol, direction, 
                        entry_time, exit_time, entry_price, exit_price, 
                        quantity, pnl, confidence_score, notes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade["id"],
                    user_id,
                    trade["playbook_id"],
                    trade["symbol"],
                    trade["direction"],
                    trade["entry_time"],
                    trade["exit_time"],
                    trade["entry_price"],
                    trade["exit_price"],
                    trade["quantity"],
                    trade["pnl"],
                    trade["confidence_score"],
                    trade["notes"],
                    datetime.now().isoformat()
                ))
            
            total_trades += num_trades
            print(f"  ✅ Added {num_trades} trades")
        
        conn.commit()
        
        print(f"\n🎉 Successfully generated optimization test data!")
        print(f"📈 Created {len(playbooks_data)} playbooks")
        print(f"💼 Generated {total_trades} realistic trades")
        print(f"👤 User ID: {user_id}")
        print(f"\n🚀 Ready to test Playbook Optimization Engine!")
        
        # Test the optimization endpoint
        print("\n🔍 Quick verification...")
        cursor.execute("""
            SELECT p.name, COUNT(t.id) as trade_count, 
                   ROUND(AVG(CASE WHEN t.pnl > 0 THEN 1.0 ELSE 0.0 END) * 100, 1) as win_rate,
                   ROUND(AVG(t.pnl), 2) as avg_pnl
            FROM playbooks p 
            LEFT JOIN trades t ON p.id = t.playbook_id 
            WHERE p.user_id = ?
            GROUP BY p.id, p.name
            ORDER BY avg_pnl DESC
        """, (user_id,))
        
        results = cursor.fetchall()
        print("\n📊 Playbook Summary:")
        print("Playbook Name | Trades | Win Rate | Avg P&L")
        print("-" * 50)
        for row in results:
            print(f"{row[0]:<20} | {row[1]:<6} | {row[2]:<8}% | ${row[3]}")
        
    except Exception as e:
        print(f"❌ Error generating data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
