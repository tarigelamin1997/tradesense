
"""
Streak Analytics Module

Contains functions for analyzing winning and losing streaks:
- Maximum consecutive wins/losses
- Streak pattern analysis
- Streak distribution statistics
"""

from typing import List, Dict, Any, Tuple


def calculate_win_loss_streaks(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive win/loss streak statistics
    
    Args:
        trades: List of trade dictionaries with 'pnl' field
        
    Returns:
        Dictionary with streak statistics
    """
    if not trades:
        return {
            'max_win_streak': 0,
            'max_loss_streak': 0,
            'current_streak': 0,
            'current_streak_type': 'none',
            'avg_win_streak': 0.0,
            'avg_loss_streak': 0.0,
            'total_win_streaks': 0,
            'total_loss_streaks': 0
        }
    
    # Sort trades by entry time to ensure proper sequence
    sorted_trades = sorted(trades, key=lambda x: x.get('entry_time', ''))
    
    max_win_streak = 0
    max_loss_streak = 0
    current_streak = 0
    current_streak_type = 'none'
    
    win_streaks = []
    loss_streaks = []
    temp_streak = 0
    temp_streak_type = 'none'
    
    for trade in sorted_trades:
        pnl = trade.get('pnl', 0)
        
        if pnl > 0:  # Winning trade
            if temp_streak_type == 'win':
                temp_streak += 1
            else:
                # End of losing streak, start of winning streak
                if temp_streak_type == 'loss' and temp_streak > 0:
                    loss_streaks.append(temp_streak)
                temp_streak = 1
                temp_streak_type = 'win'
        
        elif pnl < 0:  # Losing trade
            if temp_streak_type == 'loss':
                temp_streak += 1
            else:
                # End of winning streak, start of losing streak
                if temp_streak_type == 'win' and temp_streak > 0:
                    win_streaks.append(temp_streak)
                temp_streak = 1
                temp_streak_type = 'loss'
        
        # Update current streak (last trade in sequence)
        current_streak = temp_streak
        current_streak_type = temp_streak_type
    
    # Don't forget the final streak
    if temp_streak_type == 'win' and temp_streak > 0:
        win_streaks.append(temp_streak)
    elif temp_streak_type == 'loss' and temp_streak > 0:
        loss_streaks.append(temp_streak)
    
    # Calculate statistics
    max_win_streak = max(win_streaks) if win_streaks else 0
    max_loss_streak = max(loss_streaks) if loss_streaks else 0
    avg_win_streak = sum(win_streaks) / len(win_streaks) if win_streaks else 0.0
    avg_loss_streak = sum(loss_streaks) / len(loss_streaks) if loss_streaks else 0.0
    
    return {
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'current_streak': current_streak,
        'current_streak_type': current_streak_type,
        'avg_win_streak': avg_win_streak,
        'avg_loss_streak': avg_loss_streak,
        'total_win_streaks': len(win_streaks),
        'total_loss_streaks': len(loss_streaks),
        'win_streak_distribution': _calculate_streak_distribution(win_streaks),
        'loss_streak_distribution': _calculate_streak_distribution(loss_streaks)
    }


def calculate_max_consecutive_wins(trades: List[Dict[str, Any]]) -> int:
    """
    Calculate maximum consecutive winning trades
    
    Args:
        trades: List of trade dictionaries with 'pnl' field
        
    Returns:
        Maximum consecutive wins
    """
    streaks = calculate_win_loss_streaks(trades)
    return streaks['max_win_streak']


def calculate_max_consecutive_losses(trades: List[Dict[str, Any]]) -> int:
    """
    Calculate maximum consecutive losing trades
    
    Args:
        trades: List of trade dictionaries with 'pnl' field
        
    Returns:
        Maximum consecutive losses
    """
    streaks = calculate_win_loss_streaks(trades)
    return streaks['max_loss_streak']


def analyze_streak_patterns(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze patterns in winning and losing streaks
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Dictionary with streak pattern analysis
    """
    streaks = calculate_win_loss_streaks(trades)
    
    if not trades:
        return {
            'streak_consistency': 0.0,
            'streak_volatility': 0.0,
            'recovery_rate': 0.0,
            'breakdown_rate': 0.0
        }
    
    # Calculate streak consistency (how often streaks are similar length)
    win_streaks = streaks.get('win_streak_distribution', {})
    loss_streaks = streaks.get('loss_streak_distribution', {})
    
    # Streak volatility (variance in streak lengths)
    all_streaks = list(win_streaks.keys()) + list(loss_streaks.keys())
    if len(all_streaks) > 1:
        streak_variance = sum((int(s) - sum(int(x) for x in all_streaks)/len(all_streaks))**2 for s in all_streaks) / len(all_streaks)
        streak_volatility = streak_variance ** 0.5
    else:
        streak_volatility = 0.0
    
    # Recovery rate (how often losses are followed by wins)
    # Breakdown rate (how often wins are followed by losses)
    recovery_count = 0
    breakdown_count = 0
    transitions = 0
    
    sorted_trades = sorted(trades, key=lambda x: x.get('entry_time', ''))
    
    for i in range(len(sorted_trades) - 1):
        current_pnl = sorted_trades[i].get('pnl', 0)
        next_pnl = sorted_trades[i + 1].get('pnl', 0)
        
        if current_pnl < 0 and next_pnl > 0:  # Loss followed by win
            recovery_count += 1
        elif current_pnl > 0 and next_pnl < 0:  # Win followed by loss
            breakdown_count += 1
        
        transitions += 1
    
    recovery_rate = (recovery_count / transitions * 100) if transitions > 0 else 0.0
    breakdown_rate = (breakdown_count / transitions * 100) if transitions > 0 else 0.0
    
    return {
        'streak_consistency': _calculate_streak_consistency(streaks),
        'streak_volatility': streak_volatility,
        'recovery_rate': recovery_rate,
        'breakdown_rate': breakdown_rate,
        'max_win_streak': streaks['max_win_streak'],
        'max_loss_streak': streaks['max_loss_streak'],
        'avg_win_streak': streaks['avg_win_streak'],
        'avg_loss_streak': streaks['avg_loss_streak']
    }


def _calculate_streak_distribution(streaks: List[int]) -> Dict[str, int]:
    """
    Calculate distribution of streak lengths
    
    Args:
        streaks: List of streak lengths
        
    Returns:
        Dictionary mapping streak length to frequency
    """
    distribution = {}
    for streak in streaks:
        streak_str = str(streak)
        distribution[streak_str] = distribution.get(streak_str, 0) + 1
    
    return distribution


def _calculate_streak_consistency(streak_data: Dict[str, Any]) -> float:
    """
    Calculate how consistent streak lengths are (lower variance = more consistent)
    
    Args:
        streak_data: Output from calculate_win_loss_streaks
        
    Returns:
        Consistency score (0-100, higher is more consistent)
    """
    win_dist = streak_data.get('win_streak_distribution', {})
    loss_dist = streak_data.get('loss_streak_distribution', {})
    
    all_streaks = []
    
    # Flatten distributions into list of actual streak lengths
    for length_str, count in win_dist.items():
        all_streaks.extend([int(length_str)] * count)
    
    for length_str, count in loss_dist.items():
        all_streaks.extend([int(length_str)] * count)
    
    if len(all_streaks) <= 1:
        return 100.0  # Perfect consistency if 0 or 1 streak
    
    # Calculate coefficient of variation (inverted for consistency score)
    mean_streak = sum(all_streaks) / len(all_streaks)
    variance = sum((s - mean_streak) ** 2 for s in all_streaks) / len(all_streaks)
    std_dev = variance ** 0.5
    
    if mean_streak == 0:
        return 0.0
    
    coefficient_of_variation = std_dev / mean_streak
    consistency_score = max(0, 100 - (coefficient_of_variation * 100))
    
    return min(100.0, consistency_score)
