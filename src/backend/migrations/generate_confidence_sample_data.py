
"""
Generate sample trades with confidence scores for testing confidence calibration
"""
import sqlite3
import uuid
from datetime import datetime, timedelta
import random

def generate_confidence_sample_data():
    """Generate sample trades with confidence scores and varying performance"""
    
    conn = sqlite3.connect('tradesense.db')
    cursor = conn.cursor()
    
    # Sample user ID
    user_id = "test_user_123"
    
    # Sample symbols
    symbols = ["ES", "NQ", "YM", "RTY", "CL", "GC"]
    
    # Generate 200 sample trades with different confidence patterns
    trades_data = []
    base_date = datetime.now() - timedelta(days=180)
    
    for i in range(200):
        trade_id = str(uuid.uuid4())
        symbol = random.choice(symbols)
        direction = random.choice(["long", "short"])
        quantity = random.uniform(1, 5)
        entry_price = random.uniform(50, 5000)
        
        # Generate confidence score (1-10)
        confidence = random.randint(1, 10)
        
        # Simulate realistic confidence vs performance correlation
        # Higher confidence should generally perform better, but with some noise
        base_success_rate = 0.3 + (confidence / 10) * 0.4  # 30% to 70% success rate
        
        # Add some overconfidence bias - very high confidence (9-10) slightly underperforms
        if confidence >= 9:
            base_success_rate *= 0.9
        
        # Generate win/loss based on confidence-adjusted probability
        is_winner = random.random() < base_success_rate
        
        if is_winner:
            # Winning trade
            if direction == "long":
                exit_price = entry_price * random.uniform(1.01, 1.05)
            else:
                exit_price = entry_price * random.uniform(0.95, 0.99)
            pnl = abs(exit_price - entry_price) * quantity
        else:
            # Losing trade
            if direction == "long":
                exit_price = entry_price * random.uniform(0.95, 0.99)
            else:
                exit_price = entry_price * random.uniform(1.01, 1.05)
            pnl = -abs(exit_price - entry_price) * quantity
        
        # Add some random noise to PnL
        pnl *= random.uniform(0.8, 1.2)
        
        entry_time = base_date + timedelta(days=i)
        exit_time = entry_time + timedelta(hours=random.randint(1, 8))
        
        trade_data = (
            trade_id, user_id, symbol, direction, quantity, entry_price, exit_price,
            entry_time.isoformat(), exit_time.isoformat(), round(pnl, 2), 0.0, round(pnl, 2),
            confidence, "Sample trade for confidence calibration", "closed",
            datetime.now().isoformat(), datetime.now().isoformat()
        )
        
        trades_data.append(trade_data)
    
    # Insert trades
    insert_query = """
    INSERT OR REPLACE INTO trades (
        id, user_id, symbol, direction, quantity, entry_price, exit_price,
        entry_time, exit_time, pnl, commission, net_pnl,
        confidence_score, notes, status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.executemany(insert_query, trades_data)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Generated {len(trades_data)} sample trades with confidence scores")
    print("📊 Confidence distribution:")
    
    # Show confidence distribution
    confidence_dist = {}
    for trade in trades_data:
        conf = trade[12]  # confidence_score index
        confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
    
    for conf in sorted(confidence_dist.keys()):
        print(f"   Confidence {conf}: {confidence_dist[conf]} trades")

if __name__ == "__main__":
    generate_confidence_sample_data()
