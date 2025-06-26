
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
