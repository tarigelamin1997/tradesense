
"""
Generate sample execution quality data with MFE/MAE values
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import random
from datetime import datetime, timedelta

def generate_execution_sample_data():
    """Generate sample trades with execution quality metrics"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tradesense.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🎯 Generating execution quality sample data...")
        
        # Get existing user
        cursor.execute("SELECT id FROM users LIMIT 1")
        user_result = cursor.fetchone()
        
        if not user_result:
            print("❌ No users found. Please add a user first.")
            return
        
        user_id = user_result[0]
        
        # Sample symbols and strategies
        symbols = ['AAPL', 'TSLA', 'NVDA', 'GOOGL', 'MSFT', 'SPY', 'QQQ', 'AMZN']
        
        # Generate 50 sample trades with execution metrics
        trades_data = []
        
        for i in range(50):
            symbol = random.choice(symbols)
            direction = random.choice(['long', 'short'])
            
            # Base price around realistic levels
            base_price = random.uniform(100, 500)
            entry_price = base_price
            
            # Generate realistic trade outcomes
            outcome_type = random.choices(
                ['good_execution', 'poor_entry', 'poor_exit', 'average'],
                weights=[25, 25, 25, 25]
            )[0]
            
            if outcome_type == 'good_execution':
                # Good entry, good exit
                price_move = random.uniform(0.02, 0.08)  # 2-8% move
                if direction == 'long':
                    mfe = entry_price * price_move  # Good upward move
                    mae = -entry_price * random.uniform(0.005, 0.015)  # Small adverse move
                    exit_price = entry_price + (mfe * random.uniform(0.8, 0.95))  # Good exit near MFE
                else:
                    mfe = entry_price * price_move  # Good downward move for short
                    mae = entry_price * random.uniform(0.005, 0.015)  # Small adverse move
                    exit_price = entry_price - (mfe * random.uniform(0.8, 0.95))
                    
            elif outcome_type == 'poor_entry':
                # Poor entry timing (chased the move)
                price_move = random.uniform(0.01, 0.05)
                if direction == 'long':
                    mae = -entry_price * random.uniform(0.02, 0.05)  # Large initial adverse move
                    mfe = entry_price * price_move
                    exit_price = entry_price + (mfe * random.uniform(0.3, 0.7))  # Mediocre exit
                else:
                    mae = entry_price * random.uniform(0.02, 0.05)
                    mfe = entry_price * price_move
                    exit_price = entry_price - (mfe * random.uniform(0.3, 0.7))
                    
            elif outcome_type == 'poor_exit':
                # Good entry, poor exit (left money on table)
                price_move = random.uniform(0.03, 0.10)
                if direction == 'long':
                    mfe = entry_price * price_move  # Large favorable move
                    mae = -entry_price * random.uniform(0.005, 0.015)
                    exit_price = entry_price + (mfe * random.uniform(0.2, 0.5))  # Early exit
                else:
                    mfe = entry_price * price_move
                    mae = entry_price * random.uniform(0.005, 0.015)
                    exit_price = entry_price - (mfe * random.uniform(0.2, 0.5))
                    
            else:  # average
                price_move = random.uniform(0.01, 0.04)
                if direction == 'long':
                    mfe = entry_price * price_move
                    mae = -entry_price * random.uniform(0.01, 0.025)
                    exit_price = entry_price + (mfe * random.uniform(0.5, 0.8))
                else:
                    mfe = entry_price * price_move
                    mae = entry_price * random.uniform(0.01, 0.025)
                    exit_price = entry_price - (mfe * random.uniform(0.5, 0.8))
            
            # Calculate other fields
            quantity = random.randint(100, 1000)
            
            if direction == 'long':
                pnl = (exit_price - entry_price) * quantity
            else:
                pnl = (entry_price - exit_price) * quantity
            
            # Generate random times
            days_ago = random.randint(1, 90)
            entry_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 6))
            exit_time = entry_time + timedelta(minutes=random.randint(15, 300))
            
            # Add some confidence scores
            confidence_score = random.randint(3, 9)
            
            trade_data = (
                f"EXEC_{symbol}_{i+1}",  # trade_id
                user_id,
                symbol,
                direction,
                quantity,
                entry_price,
                exit_price,
                entry_time.isoformat(),
                exit_time.isoformat(),
                pnl,
                random.uniform(1.0, 5.0),  # commission
                pnl - random.uniform(1.0, 5.0),  # net_pnl
                mae,  # max_adverse_excursion
                mfe,  # max_favorable_excursion
                confidence_score,
                f"Execution quality test trade {i+1}",  # notes
                datetime.now().isoformat(),
                datetime.now().isoformat()
            )
            
            trades_data.append(trade_data)
        
        # Insert trades
        insert_query = """
        INSERT INTO trades (
            trade_id, user_id, symbol, direction, quantity, 
            entry_price, exit_price, entry_time, exit_time,
            pnl, commission, net_pnl, max_adverse_excursion, 
            max_favorable_excursion, confidence_score, notes,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.executemany(insert_query, trades_data)
        conn.commit()
        
        print(f"✅ Generated {len(trades_data)} execution quality sample trades!")
        print("📊 Sample includes:")
        print("   - Good execution trades (optimal entry/exit)")
        print("   - Poor entry timing trades (chasing moves)")
        print("   - Poor exit trades (early exits)")
        print("   - Average execution trades")
        print("   - MFE/MAE data for quality analysis")
        
    except Exception as e:
        print(f"❌ Error generating execution quality data: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    generate_execution_sample_data()
#!/usr/bin/env python3

import sqlite3
import random
from datetime import datetime, timedelta
from typing import List, Dict

def generate_execution_quality_sample_data():
    """Generate sample execution quality data for existing trades"""
    try:
        print("🎯 Generating Execution Quality sample data...")
        
        # Connect to database
        conn = sqlite3.connect('tradesense.db')
        cursor = conn.cursor()
        
        # Check if we have trades to work with
        cursor.execute("SELECT COUNT(*) FROM trades WHERE exit_price IS NOT NULL AND exit_time IS NOT NULL")
        completed_trades_count = cursor.fetchone()[0]
        
        if completed_trades_count == 0:
            print("❌ No completed trades found. Please add some trades first.")
            return False
        
        print(f"📊 Found {completed_trades_count} completed trades")
        
        # Get all completed trades
        cursor.execute("""
            SELECT id, symbol, direction, entry_time, exit_time, entry_price, exit_price, 
                   pnl, quantity, confidence_score, playbook_id
            FROM trades 
            WHERE exit_price IS NOT NULL AND exit_time IS NOT NULL
        """)
        trades = cursor.fetchall()
        
        # Add execution quality columns if they don't exist
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN entry_score INTEGER")
            cursor.execute("ALTER TABLE trades ADD COLUMN exit_score INTEGER")
            cursor.execute("ALTER TABLE trades ADD COLUMN execution_score INTEGER")
            cursor.execute("ALTER TABLE trades ADD COLUMN execution_grade TEXT")
            cursor.execute("ALTER TABLE trades ADD COLUMN slippage REAL")
            cursor.execute("ALTER TABLE trades ADD COLUMN regret_index REAL")
            cursor.execute("ALTER TABLE trades ADD COLUMN holding_efficiency INTEGER")
            print("✅ Added execution quality columns to trades table")
        except sqlite3.OperationalError:
            print("📋 Execution quality columns already exist")
        
        # Generate realistic execution metrics for each trade
        updates = []
        for trade in trades:
            trade_id, symbol, direction, entry_time, exit_time, entry_price, exit_price, pnl, quantity, confidence_score, playbook_id = trade
            
            # Calculate realistic execution metrics
            execution_metrics = generate_realistic_execution_metrics(
                symbol, direction, entry_price, exit_price, pnl, confidence_score
            )
            
            updates.append((
                execution_metrics["entry_score"],
                execution_metrics["exit_score"],
                execution_metrics["execution_score"],
                execution_metrics["execution_grade"],
                execution_metrics["slippage"],
                execution_metrics["regret_index"],
                execution_metrics["holding_efficiency"],
                trade_id
            ))
        
        # Batch update all trades
        cursor.executemany("""
            UPDATE trades 
            SET entry_score = ?, exit_score = ?, execution_score = ?, execution_grade = ?,
                slippage = ?, regret_index = ?, holding_efficiency = ?
            WHERE id = ?
        """, updates)
        
        # Generate some MFE/MAE data for trades that don't have it
        cursor.execute("""
            SELECT id, pnl, direction 
            FROM trades 
            WHERE (max_favorable_excursion IS NULL OR max_adverse_excursion IS NULL)
            AND exit_price IS NOT NULL
        """)
        trades_without_mfe_mae = cursor.fetchall()
        
        mfe_mae_updates = []
        for trade_id, pnl, direction in trades_without_mfe_mae:
            if pnl is not None:
                # Generate realistic MFE/MAE
                if pnl > 0:
                    # Profitable trade
                    mfe = pnl * random.uniform(1.1, 2.5)  # MFE typically higher than final profit
                    mae = pnl * random.uniform(-0.3, -0.05)  # Small adverse move
                else:
                    # Losing trade
                    mfe = abs(pnl) * random.uniform(0.1, 0.8)  # Some favorable move before loss
                    mae = pnl * random.uniform(1.0, 1.8)  # MAE worse than final loss
                
                mfe_mae_updates.append((mfe, mae, trade_id))
        
        if mfe_mae_updates:
            cursor.executemany("""
                UPDATE trades 
                SET max_favorable_excursion = ?, max_adverse_excursion = ?
                WHERE id = ?
            """, mfe_mae_updates)
            print(f"✅ Generated MFE/MAE data for {len(mfe_mae_updates)} trades")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Updated {len(updates)} trades with execution quality metrics")
        print("🎯 Execution Quality sample data generation complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Execution quality data generation failed: {e}")
        return False

def generate_realistic_execution_metrics(symbol: str, direction: str, entry_price: float, 
                                       exit_price: float, pnl: float, confidence_score: int) -> Dict:
    """Generate realistic execution quality metrics for a trade"""
    
    # Base scores
    entry_score = random.randint(50, 90)
    exit_score = random.randint(45, 85)
    holding_efficiency = random.randint(55, 95)
    
    # Adjust based on trade outcome
    if pnl and pnl > 0:
        # Profitable trades tend to have better execution
        entry_score += random.randint(0, 15)
        exit_score += random.randint(0, 20)
        holding_efficiency += random.randint(0, 10)
    else:
        # Losing trades may have execution issues
        entry_score -= random.randint(0, 20)
        exit_score -= random.randint(0, 15)
        holding_efficiency -= random.randint(0, 15)
    
    # Adjust based on confidence
    if confidence_score:
        if confidence_score >= 8:
            # High confidence should correlate with better execution
            entry_score += random.randint(0, 10)
        elif confidence_score <= 3:
            # Low confidence might mean poor execution
            entry_score -= random.randint(0, 10)
            exit_score -= random.randint(0, 10)
    
    # Ensure scores are within bounds
    entry_score = max(10, min(100, entry_score))
    exit_score = max(10, min(100, exit_score))
    holding_efficiency = max(10, min(100, holding_efficiency))
    
    # Generate other metrics
    slippage = round(random.uniform(0.0001, 0.005), 4)
    regret_index = round(random.uniform(0.0, 0.8), 3)
    
    # Calculate composite execution score
    execution_score = int((entry_score * 0.25 + exit_score * 0.35 + holding_efficiency * 0.25 + 
                          (100 - regret_index * 100) * 0.15))
    execution_score = max(10, min(100, execution_score))
    
    # Assign grade
    if execution_score >= 90:
        grade = "A+"
    elif execution_score >= 85:
        grade = "A"
    elif execution_score >= 80:
        grade = "A-"
    elif execution_score >= 75:
        grade = "B+"
    elif execution_score >= 70:
        grade = "B"
    elif execution_score >= 65:
        grade = "B-"
    elif execution_score >= 60:
        grade = "C+"
    elif execution_score >= 55:
        grade = "C"
    elif execution_score >= 50:
        grade = "C-"
    else:
        grade = "F"
    
    return {
        "entry_score": entry_score,
        "exit_score": exit_score,
        "execution_score": execution_score,
        "execution_grade": grade,
        "slippage": slippage,
        "regret_index": regret_index,
        "holding_efficiency": holding_efficiency
    }

if __name__ == "__main__":
    generate_execution_quality_sample_data()
