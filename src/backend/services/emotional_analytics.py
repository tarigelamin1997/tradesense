from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models.trade import Trade
from datetime import datetime, timedelta
import json

class EmotionalAnalyticsService:
    
    # Predefined emotional states
    EMOTIONAL_STATES = [
        "FOMO", "Fear", "Greed", "Confidence", "Frustration", 
        "Revenge", "Hesitation", "Overconfidence", "Anxiety",
        "Excitement", "Calm", "Impatient", "Focused", "Stressed"
    ]
    
    MOOD_CATEGORIES = [
        "Euphoric", "Confident", "Calm", "Neutral", "Anxious", 
        "Frustrated", "Angry", "Disappointed", "Regretful"
    ]
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
    
    def get_emotional_performance_correlation(self) -> Dict[str, Any]:
        """Analyze correlation between emotions and trading performance"""
        
        # Get all trades with emotional data
        trades = self.db.query(Trade).filter(
            and_(
                Trade.user_id == self.user_id,
                Trade.emotional_tags.isnot(None),
                Trade.pnl.isnot(None)
            )
        ).all()
        
        emotion_stats = {}
        
        for trade in trades:
            if trade.emotional_tags:
                emotions = json.loads(trade.emotional_tags) if isinstance(trade.emotional_tags, str) else trade.emotional_tags
                
                for emotion in emotions:
                    if emotion not in emotion_stats:
                        emotion_stats[emotion] = {
                            'count': 0,
                            'total_pnl': 0,
                            'wins': 0,
                            'losses': 0,
                            'avg_emotional_score': 0,
                            'plan_adherence': 0
                        }
                    
                    stats = emotion_stats[emotion]
                    stats['count'] += 1
                    stats['total_pnl'] += trade.pnl or 0
                    
                    if trade.pnl and trade.pnl > 0:
                        stats['wins'] += 1
                    elif trade.pnl and trade.pnl < 0:
                        stats['losses'] += 1
                    
                    if trade.emotional_score:
                        stats['avg_emotional_score'] += trade.emotional_score
                    
                    if trade.executed_plan:
                        stats['plan_adherence'] += 1
        
        # Calculate final metrics
        for emotion, stats in emotion_stats.items():
            if stats['count'] > 0:
                stats['avg_pnl'] = stats['total_pnl'] / stats['count']
                stats['win_rate'] = stats['wins'] / stats['count'] * 100
                stats['avg_emotional_score'] = stats['avg_emotional_score'] / stats['count']
                stats['plan_adherence_rate'] = stats['plan_adherence'] / stats['count'] * 100
        
        return emotion_stats
    
    def get_plan_execution_analysis(self) -> Dict[str, Any]:
        """Analyze performance when following vs breaking trading plan"""
        
        followed_plan = self.db.query(Trade).filter(
            and_(
                Trade.user_id == self.user_id,
                Trade.executed_plan == True,
                Trade.pnl.isnot(None)
            )
        ).all()
        
        broke_plan = self.db.query(Trade).filter(
            and_(
                Trade.user_id == self.user_id,
                Trade.executed_plan == False,
                Trade.pnl.isnot(None)
            )
        ).all()
        
        def calculate_stats(trades):
            if not trades:
                return {}
            
            total_pnl = sum(t.pnl for t in trades if t.pnl)
            wins = len([t for t in trades if t.pnl and t.pnl > 0])
            avg_emotional_score = sum(t.emotional_score for t in trades if t.emotional_score) / len([t for t in trades if t.emotional_score]) if any(t.emotional_score for t in trades) else 0
            
            return {
                'count': len(trades),
                'total_pnl': total_pnl,
                'avg_pnl': total_pnl / len(trades),
                'win_rate': wins / len(trades) * 100,
                'avg_emotional_score': avg_emotional_score
            }
        
        return {
            'followed_plan': calculate_stats(followed_plan),
            'broke_plan': calculate_stats(broke_plan),
            'plan_adherence_impact': {
                'pnl_difference': calculate_stats(followed_plan).get('avg_pnl', 0) - calculate_stats(broke_plan).get('avg_pnl', 0),
                'win_rate_difference': calculate_stats(followed_plan).get('win_rate', 0) - calculate_stats(broke_plan).get('win_rate', 0)
            }
        }
    
    def get_emotional_trends_over_time(self, days: int = 30) -> Dict[str, Any]:
        """Track emotional control improvement over time"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        trades = self.db.query(Trade).filter(
            and_(
                Trade.user_id == self.user_id,
                Trade.entry_time >= start_date,
                Trade.emotional_score.isnot(None)
            )
        ).order_by(Trade.entry_time).all()
        
        # Group by week
        weekly_data = {}
        for trade in trades:
            week = trade.entry_time.strftime("%Y-W%U")
            if week not in weekly_data:
                weekly_data[week] = {
                    'emotional_scores': [],
                    'plan_adherence': [],
                    'pnl': []
                }
            
            weekly_data[week]['emotional_scores'].append(trade.emotional_score)
            if trade.executed_plan is not None:
                weekly_data[week]['plan_adherence'].append(1 if trade.executed_plan else 0)
            if trade.pnl:
                weekly_data[week]['pnl'].append(trade.pnl)
        
        # Calculate weekly averages
        trend_data = []
        for week, data in weekly_data.items():
            trend_data.append({
                'week': week,
                'avg_emotional_score': sum(data['emotional_scores']) / len(data['emotional_scores']),
                'plan_adherence_rate': sum(data['plan_adherence']) / len(data['plan_adherence']) * 100 if data['plan_adherence'] else 0,
                'avg_pnl': sum(data['pnl']) / len(data['pnl']) if data['pnl'] else 0,
                'trade_count': len(data['emotional_scores'])
            })
        
        return {
            'weekly_trends': trend_data,
            'overall_improvement': self._calculate_improvement_trend([d['avg_emotional_score'] for d in trend_data])
        }
    
    def _calculate_improvement_trend(self, scores: List[float]) -> Dict[str, Any]:
        """Calculate if there's improvement trend in emotional scores"""
        if len(scores) < 2:
            return {'trend': 'insufficient_data', 'slope': 0}
        
        # Simple linear regression slope
        n = len(scores)
        sum_x = sum(range(n))
        sum_y = sum(scores)
        sum_xy = sum(i * scores[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.1:
            trend = 'improving'
        elif slope < -0.1:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {'trend': trend, 'slope': slope}
    
    def get_emotional_insights(self) -> List[str]:
        """Generate actionable insights from emotional data"""
        insights = []
        
        emotion_stats = self.get_emotional_performance_correlation()
        plan_analysis = self.get_plan_execution_analysis()
        
        # Identify problematic emotions
        for emotion, stats in emotion_stats.items():
            if stats['count'] >= 3:  # Only consider emotions with sufficient data
                if stats['avg_pnl'] < -50:  # Significant negative PnL
                    insights.append(f"⚠️ Trades tagged with '{emotion}' average ${stats['avg_pnl']:.2f} loss - consider avoiding trading when feeling {emotion.lower()}")
                
                if stats['win_rate'] < 30:  # Low win rate
                    insights.append(f"📊 {emotion} trades have only {stats['win_rate']:.1f}% win rate - this emotion may be sabotaging your performance")
        
        # Plan adherence insights
        if plan_analysis.get('plan_adherence_impact', {}).get('pnl_difference', 0) > 0:
            diff = plan_analysis['plan_adherence_impact']['pnl_difference']
            insights.append(f"✅ Following your plan generates ${diff:.2f} more profit per trade on average")
        
        # Emotional control insights
        best_emotions = sorted(emotion_stats.items(), key=lambda x: x[1]['avg_pnl'], reverse=True)[:3]
        if best_emotions:
            best_emotion = best_emotions[0][0]
            insights.append(f"🎯 Your best performance comes when feeling '{best_emotion}' - try to cultivate this mental state")
        
        return insights[:5]  # Return top 5 insights
