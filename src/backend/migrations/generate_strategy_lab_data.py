
"""
Generate sample playbook data and link to existing trades for Strategy Lab testing
"""

import sqlite3
import uuid
from datetime import datetime
import random
from pathlib import Path

def generate_sample_playbooks_and_links():
    """Generate sample playbooks and link them to existing trades"""
    
    db_path = Path(__file__).parent.parent / "tradesense.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🎯 Generating Strategy Lab sample data...")
        
        # Sample playbooks with different strategies
        sample_playbooks = [
            {
                "name": "Morning Breakout",
                "entry_criteria": "Price breaks above previous day high with volume > 1.5x average, RSI < 70",
                "exit_criteria": "Target: 2:1 R/R, Stop: Previous day low, Time: Close by 11 AM",
                "description": "Early morning momentum breakout strategy"
            },
            {
                "name": "Reversal Scalp",
                "entry_criteria": "Price touches support/resistance with divergence signal, high confidence setup",
                "exit_criteria": "Quick 1:1 target, tight stop below entry level",
                "description": "Short-term reversal scalping at key levels"
            },
            {
                "name": "Trend Follow",
                "entry_criteria": "Price above 20 EMA, pullback to support, momentum confirmation",
                "exit_criteria": "Trail stop below 20 EMA, take partial profits at resistance",
                "description": "Medium-term trend following strategy"
            },
            {
                "name": "Gap Fill",
                "entry_criteria": "Gap down > 2% at open, volume spike, oversold bounce setup",
                "exit_criteria": "Target gap fill level, stop below premarket low",
                "description": "Gap down reversal strategy"
            },
            {
                "name": "High Momentum",
                "entry_criteria": "Strong catalyst, volume > 3x average, price action confirmation",
                "exit_criteria": "Aggressive scaling out, trail with volatility stop",
                "description": "High momentum breakout trading"
            }
        ]
        
        # Get user IDs from trades (assuming we have some)
        cursor.execute("SELECT DISTINCT user_id FROM trades LIMIT 5")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        if not user_ids:
            print("❌ No users found in trades table. Please add some trades first.")
            return False
        
        # Create playbooks for each user
        playbook_ids = []
        for user_id in user_ids:
            for playbook_data in sample_playbooks:
                playbook_id = str(uuid.uuid4())
                
                cursor.execute("""
                    INSERT OR IGNORE INTO playbooks 
                    (id, user_id, name, entry_criteria, exit_criteria, description, status, created_at) 
                    VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
                """, (
                    playbook_id,
                    user_id,
                    playbook_data["name"],
                    playbook_data["entry_criteria"],
                    playbook_data["exit_criteria"],
                    playbook_data["description"],
                    datetime.now().isoformat()
                ))
                
                playbook_ids.append((playbook_id, user_id))
        
        # Link existing trades to playbooks (randomly assign about 70% of trades)
        for user_id in user_ids:
            cursor.execute("SELECT id FROM trades WHERE user_id = ?", (user_id,))
            trade_ids = [row[0] for row in cursor.fetchall()]
            
            # Get playbooks for this user
            user_playbooks = [pid for pid, uid in playbook_ids if uid == user_id]
            
            # Randomly assign playbooks to trades
            for trade_id in trade_ids:
                # 70% chance to assign a playbook
                if random.random() < 0.7 and user_playbooks:
                    playbook_id = random.choice(user_playbooks)
                    cursor.execute(
                        "UPDATE trades SET playbook_id = ? WHERE id = ?",
                        (playbook_id, trade_id)
                    )
        
        # Update some trades with confidence scores if they don't have them
        cursor.execute("SELECT id FROM trades WHERE confidence_score IS NULL")
        trades_without_confidence = [row[0] for row in cursor.fetchall()]
        
        for trade_id in trades_without_confidence[:50]:  # Limit to 50 updates
            confidence = random.randint(1, 10)
            cursor.execute(
                "UPDATE trades SET confidence_score = ? WHERE id = ?",
                (confidence, trade_id)
            )
        
        # Add some emotional tags to random trades
        emotional_tags = ['fomo', 'revenge', 'confident', 'patient', 'rushed', 'greedy', 'disciplined']
        cursor.execute("SELECT id, tags FROM trades WHERE tags IS NULL OR tags = '[]' LIMIT 30")
        trades_for_tags = cursor.fetchall()
        
        for trade_id, existing_tags in trades_for_tags:
            # 50% chance to add emotional tags
            if random.random() < 0.5:
                num_tags = random.randint(1, 2)
                selected_tags = random.sample(emotional_tags, num_tags)
                tags_json = str(selected_tags).replace("'", '"')  # Convert to JSON format
                cursor.execute(
                    "UPDATE trades SET tags = ? WHERE id = ?",
                    (tags_json, trade_id)
                )
        
        conn.commit()
        conn.close()
        
        print(f"✅ Created {len(sample_playbooks)} playbooks for {len(user_ids)} users")
        print("✅ Linked trades to playbooks randomly")
        print("✅ Added confidence scores and emotional tags")
        print("🚀 Strategy Lab sample data generation complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Data generation failed: {e}")
        return False

if __name__ == "__main__":
    generate_sample_playbooks_and_links()
