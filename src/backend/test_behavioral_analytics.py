
"""
Test script for behavioral analytics functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from services.behavioral_analytics import BehavioralAnalyticsService

def create_sample_trades():
    """Create sample trades for testing"""
    base_date = datetime.now() - timedelta(days=30)
    
    sample_trades = [
        # Win streak
        {
            'entry_time': base_date + timedelta(days=1),
            'pnl': 100,
            'quantity': 1,
            'tags': ['breakout'],
            'strategy_tag': 'momentum'
        },
        {
            'entry_time': base_date + timedelta(days=2),
            'pnl': 150,
            'quantity': 1,
            'tags': ['trend'],
            'strategy_tag': 'momentum'
        },
        {
            'entry_time': base_date + timedelta(days=3),
            'pnl': 75,
            'quantity': 1,
            'tags': ['pullback'],
            'strategy_tag': 'momentum'
        },
        # Loss streak
        {
            'entry_time': base_date + timedelta(days=4),
            'pnl': -50,
            'quantity': 2,  # Increased position after wins
            'tags': ['fomo'],
            'strategy_tag': 'momentum'
        },
        {
            'entry_time': base_date + timedelta(days=5),
            'pnl': -80,
            'quantity': 3,  # Revenge trade
            'tags': ['revenge'],
            'strategy_tag': 'momentum'
        },
        # Recovery
        {
            'entry_time': base_date + timedelta(days=7),
            'pnl': 120,
            'quantity': 1,
            'tags': ['disciplined'],
            'strategy_tag': 'scalping'
        },
        # Overtrading day
        {
            'entry_time': base_date + timedelta(days=10, hours=9),
            'pnl': 25,
            'quantity': 1,
            'tags': ['quick'],
            'strategy_tag': 'scalping'
        },
        {
            'entry_time': base_date + timedelta(days=10, hours=10),
            'pnl': -15,
            'quantity': 1,
            'tags': ['rushed'],
            'strategy_tag': 'scalping'
        },
        {
            'entry_time': base_date + timedelta(days=10, hours=11),
            'pnl': 30,
            'quantity': 1,
            'tags': ['recovery'],
            'strategy_tag': 'scalping'
        }
    ]
    
    return sample_trades

def test_behavioral_analytics():
    """Test the behavioral analytics service"""
    print("🧠 Testing TradeSense Behavioral Analytics...")
    print("=" * 50)
    
    # Create service instance
    service = BehavioralAnalyticsService()
    
    # Create sample data
    trades = create_sample_trades()
    print(f"📊 Analyzing {len(trades)} sample trades...")
    print()
    
    # Run analysis
    results = service.analyze_behavioral_patterns(trades)
    
    # Display results
    print("🎯 BEHAVIORAL ANALYSIS RESULTS")
    print("=" * 50)
    
    print(f"🏆 Max Win Streak: {results['max_win_streak']}")
    print(f"📉 Max Loss Streak: {results['max_loss_streak']}")
    
    current_streak = results['current_streak']
    print(f"🔄 Current Streak: {current_streak['count']} {current_streak['type']}(s)")
    print()
    
    print(f"📈 Consistency Rating: {results['consistency_rating']}")
    print(f"🎓 Discipline Score: {results['discipline_score']}/100")
    print(f"📊 Volume Consistency: {results['volume_consistency']}")
    print()
    
    print(f"📅 Average Trades/Day: {results['average_trades_per_day']}")
    print(f"🚫 Days with No Trades: {results['days_with_no_trades']}")
    print(f"📆 Total Trading Days: {results['total_trading_days']}")
    print()
    
    emotional = results['emotional_indicators']
    print("😤 EMOTIONAL PATTERNS")
    print("-" * 30)
    print(f"🤯 FOMO Trades: {emotional.get('fomo_trades', 0)}")
    print(f"😡 Revenge Trades: {emotional.get('revenge_trades', 0)}")
    print(f"🏷️ Total Emotional Tags: {emotional.get('emotional_tag_count', 0)}")
    if emotional.get('most_common_emotional_tag'):
        print(f"🔥 Most Common Tag: {emotional['most_common_emotional_tag']}")
    print(f"💰 Emotional P&L Impact: {emotional.get('emotional_impact_on_pnl', 0)}%")
    print()
    
    timing = results['timing_patterns']
    if timing:
        print("⏰ TIMING PATTERNS")
        print("-" * 30)
        if timing.get('most_active_hour'):
            print(f"🕐 Most Active Hour: {timing['most_active_hour']}:00")
        if timing.get('most_active_day'):
            print(f"📅 Most Active Day: {timing['most_active_day']}")
        print()
    
    flags = results['behavioral_flags']
    if flags:
        print("🚨 BEHAVIORAL FLAGS")
        print("-" * 30)
        for flag in flags:
            print(f"⚠️ {flag}")
        print()
    
    print("✅ Behavioral Analytics Test Complete!")
    print("🚀 Ready to integrate with TradeSense dashboard!")

if __name__ == "__main__":
    test_behavioral_analytics()
