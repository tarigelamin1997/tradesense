import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import scipy.stats as stats
from dataclasses import dataclass
from enum import Enum

class EmotionalState(Enum):
    CALM = "calm"
    ANXIOUS = "anxious"
    REVENGE = "revenge"
    EUPHORIC = "euphoric"
    OVERCONFIDENT = "overconfident"
    FEARFUL = "fearful"

class MarketRegime(Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGE_BOUND = "range_bound"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"

@dataclass
class BehavioralPattern:
    pattern_type: str
    confidence: float
    description: str
    trade_ids: List[str]
    impact_on_pnl: float
    frequency: int

class BehavioralAnalyticsEngine:
    """Advanced behavioral pattern detection and analysis."""

    def __init__(self):
        self.revenge_trade_threshold = 30  # minutes after a loss
        self.position_size_deviation_threshold = 0.3  # 30% deviation from normal
        self.euphoria_win_threshold = 3  # consecutive wins

    def analyze_trading_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive behavioral analysis of trading data."""

        if df.empty:
            return {}

        # Prepare data
        df = self._prepare_behavioral_data(df)

        results = {
            'emotional_patterns': self._detect_emotional_patterns(df),
            'risk_behavior': self._analyze_risk_behavior(df),
            'timing_patterns': self._analyze_timing_patterns(df),
            'performance_attribution': self._analyze_performance_attribution(df),
            'behavioral_scores': self._calculate_behavioral_scores(df),
            'recommendations': self._generate_behavioral_recommendations(df)
        }

        return results

    def _prepare_behavioral_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data with behavioral indicators."""
        df = df.copy()
        df = df.sort_values('exit_time')

        # Calculate time gaps between trades
        df['time_since_last_trade'] = df['entry_time'].diff().dt.total_seconds() / 60

        # Mark wins/losses
        df['is_winner'] = df['pnl'] > 0

        # Calculate position size as percentage (if portfolio value available)
        df['position_value'] = df['qty'] * df['entry_price']
        median_position = df['position_value'].median()
        df['position_size_ratio'] = df['position_value'] / median_position

        # Add sequence numbering
        df['trade_sequence'] = range(len(df))

        # Rolling statistics
        df['rolling_win_rate'] = df['is_winner'].rolling(10, min_periods=1).mean()
        df['rolling_avg_pnl'] = df['pnl'].rolling(10, min_periods=1).mean()

        return df

    def _detect_emotional_patterns(self, df: pd.DataFrame) -> Dict[str, List[BehavioralPattern]]:
        """Detect emotional trading patterns."""
        patterns = {
            'revenge_trading': [],
            'euphoric_trading': [],
            'fear_patterns': [],
            'overconfidence': []
        }

        # Revenge trading detection
        revenge_patterns = self._detect_revenge_trading(df)
        patterns['revenge_trading'] = revenge_patterns

        # Euphoric trading (after winning streaks)
        euphoric_patterns = self._detect_euphoric_trading(df)
        patterns['euphoric_trading'] = euphoric_patterns

        # Fear patterns (position size reduction after losses)
        fear_patterns = self._detect_fear_patterns(df)
        patterns['fear_patterns'] = fear_patterns

        # Overconfidence patterns
        overconfidence_patterns = self._detect_overconfidence_patterns(df)
        patterns['overconfidence'] = overconfidence_patterns

        return patterns

    def _detect_revenge_trading(self, df: pd.DataFrame) -> List[BehavioralPattern]:
        """Detect revenge trading patterns."""
        revenge_patterns = []

        for i in range(1, len(df)):
            current_trade = df.iloc[i]
            previous_trade = df.iloc[i-1]

            # Check if previous trade was a loss
            if previous_trade['pnl'] < 0:
                time_gap = current_trade['time_since_last_trade']

                # Quick follow-up trade after loss
                if time_gap <= self.revenge_trade_threshold:
                    # Larger position size than normal
                    if current_trade['position_size_ratio'] > 1.5:
                        confidence = min(0.9, (1.5 / current_trade['position_size_ratio']) + 
                                       (self.revenge_trade_threshold / max(time_gap, 1)) * 0.5)

                        pattern = BehavioralPattern(
                            pattern_type="revenge_trading",
                            confidence=confidence,
                            description=f"Quick larger trade {time_gap:.1f}min after ${previous_trade['pnl']:.2f} loss",
                            trade_ids=[str(current_trade.name)],
                            impact_on_pnl=current_trade['pnl'],
                            frequency=1
                        )
                        revenge_patterns.append(pattern)

        return revenge_patterns

    def _detect_euphoric_trading(self, df: pd.DataFrame) -> List[BehavioralPattern]:
        """Detect euphoric trading after winning streaks."""
        euphoric_patterns = []

        # Look for winning streaks followed by larger position sizes
        winning_streaks = self._find_winning_streaks(df)

        for streak_end_idx in winning_streaks:
            if streak_end_idx + 1 < len(df):
                next_trade = df.iloc[streak_end_idx + 1]

                # Check if position size increased significantly
                if next_trade['position_size_ratio'] > 1.8:
                    streak_length = winning_streaks[streak_end_idx]
                    confidence = min(0.85, streak_length * 0.2 + next_trade['position_size_ratio'] * 0.1)

                    pattern = BehavioralPattern(
                        pattern_type="euphoric_trading",
                        confidence=confidence,
                        description=f"Oversized trade after {streak_length}-win streak",
                        trade_ids=[str(next_trade.name)],
                        impact_on_pnl=next_trade['pnl'],
                        frequency=1
                    )
                    euphoric_patterns.append(pattern)

        return euphoric_patterns

    def _detect_fear_patterns(self, df: pd.DataFrame) -> List[BehavioralPattern]:
        """Detect fear-based position size reduction."""
        fear_patterns = []

        for i in range(3, len(df)):  # Need some history
            current_trade = df.iloc[i]
            recent_trades = df.iloc[i-3:i]

            # Check if recent trades were mostly losses
            recent_loss_rate = (recent_trades['pnl'] < 0).mean()

            if recent_loss_rate >= 0.67:  # 2/3 or more losses
                # Check if position size significantly reduced
                if current_trade['position_size_ratio'] < 0.6:
                    confidence = recent_loss_rate * (1 - current_trade['position_size_ratio'])

                    pattern = BehavioralPattern(
                        pattern_type="fear_trading",
                        confidence=confidence,
                        description=f"Position size reduced to {current_trade['position_size_ratio']:.1f}x after recent losses",
                        trade_ids=[str(current_trade.name)],
                        impact_on_pnl=current_trade['pnl'],
                        frequency=1
                    )
                    fear_patterns.append(pattern)

        return fear_patterns

    def _detect_overconfidence_patterns(self, df: pd.DataFrame) -> List[BehavioralPattern]:
        """Detect overconfidence patterns."""
        overconfidence_patterns = []

        # Look for patterns where high confidence scores lead to worse performance
        if 'confidence_score' in df.columns:
            high_confidence_trades = df[df['confidence_score'] >= 8]

            if len(high_confidence_trades) > 5:
                high_conf_performance = high_confidence_trades['pnl'].mean()
                overall_performance = df['pnl'].mean()

                if high_conf_performance < overall_performance * 0.8:
                    confidence = abs(high_conf_performance - overall_performance) / abs(overall_performance)

                    pattern = BehavioralPattern(
                        pattern_type="overconfidence",
                        confidence=min(0.9, confidence),
                        description=f"High confidence trades underperform by {((overall_performance - high_conf_performance)/overall_performance*100):.1f}%",
                        trade_ids=high_confidence_trades.index.astype(str).tolist(),
                        impact_on_pnl=high_conf_performance - overall_performance,
                        frequency=len(high_confidence_trades)
                    )
                    overconfidence_patterns.append(pattern)

        return overconfidence_patterns

    def _analyze_risk_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze risk-taking behavior patterns."""
        return {
            'position_sizing_consistency': self._analyze_position_sizing(df),
            'stop_loss_discipline': self._analyze_stop_loss_behavior(df),
            'risk_escalation': self._analyze_risk_escalation(df),
            'correlation_concentration': self._analyze_correlation_risk(df)
        }

    def _analyze_timing_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze timing and session-based patterns."""
        timing_analysis = {}

        if 'entry_time' in df.columns:
            df['hour'] = pd.to_datetime(df['entry_time']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['entry_time']).dt.dayofweek

            # Hour-based performance
            hourly_performance = df.groupby('hour').agg({
                'pnl': ['mean', 'std', 'count'],
                'is_winner': 'mean'
            }).round(3)

            timing_analysis['hourly_performance'] = hourly_performance

            # Day of week performance
            dow_performance = df.groupby('day_of_week').agg({
                'pnl': ['mean', 'std', 'count'],
                'is_winner': 'mean'
            }).round(3)

            timing_analysis['day_of_week_performance'] = dow_performance

            # Session classification
            timing_analysis['session_analysis'] = self._classify_trading_sessions(df)

        return timing_analysis

    def _find_winning_streaks(self, df: pd.DataFrame) -> Dict[int, int]:
        """Find winning streaks and their lengths."""
        streaks = {}
        current_streak = 0

        for i, row in df.iterrows():
            if row['is_winner']:
                current_streak += 1
            else:
                if current_streak >= self.euphoria_win_threshold:
                    streaks[i-1] = current_streak  # Index of last win in streak
                current_streak = 0

        # Check final streak
        if current_streak >= self.euphoria_win_threshold:
            streaks[len(df)-1] = current_streak

        return streaks

    def _calculate_behavioral_scores(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate overall behavioral health scores."""
        scores = {}

        # Emotional control score (0-100)
        revenge_trades = len(self._detect_revenge_trading(df))
        total_trades = len(df)
        emotional_control = max(0, 100 - (revenge_trades / max(total_trades, 1) * 100))
        scores['emotional_control'] = emotional_control

        # Risk discipline score
        position_consistency = 100 - (df['position_size_ratio'].std() * 50)
        scores['risk_discipline'] = max(0, min(100, position_consistency))

        # Timing discipline score
        avg_time_gap = df['time_since_last_trade'].median()
        timing_discipline = min(100, max(0, avg_time_gap / 60 * 20))  # Reward longer gaps
        scores['timing_discipline'] = timing_discipline

        # Overall behavioral score
        scores['overall_behavioral_health'] = np.mean([
            scores['emotional_control'],
            scores['risk_discipline'], 
            scores['timing_discipline']
        ])

        return scores

    def _generate_behavioral_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate actionable behavioral recommendations."""
        recommendations = []

        patterns = self._detect_emotional_patterns(df)
        scores = self._calculate_behavioral_scores(df)

        # Emotional control recommendations
        if len(patterns['revenge_trading']) > 0:
            recommendations.append(
                f"🚨 CRITICAL: Detected {len(patterns['revenge_trading'])} revenge trades. "
                "Implement a 30-minute cooling-off period after losses."
            )

        if len(patterns['euphoric_trading']) > 0:
            recommendations.append(
                f"⚠️ WARNING: {len(patterns['euphoric_trading'])} euphoric trades detected. "
                "Set maximum position size limits during winning streaks."
            )

        # Risk discipline recommendations
        if scores['risk_discipline'] < 70:
            recommendations.append(
                "📊 RISK: Inconsistent position sizing detected. "
                "Implement systematic position sizing rules (e.g., 1-2% risk per trade)."
            )

        # Performance attribution
        if 'confidence_score' in df.columns:
            overconf_patterns = patterns.get('overconfidence', [])
            if overconf_patterns:
                recommendations.append(
                    "🎯 INSIGHT: High-confidence trades underperform. "
                    "Review your confidence assessment criteria."
                )

        return recommendations

class BehavioralEngine:
    """Advanced behavioral analysis for trading patterns."""

    def __init__(self):
        self.patterns = {}
        self.alerts = []
        self.behavioral_labels = {
            'revenge_trader': 'Tends to increase position size after losses',
            'pattern_trader': 'Shows consistent entry/exit patterns',
            'emotional_trader': 'High volatility in trading frequency',
            'disciplined_trader': 'Consistent risk management',
            'overtrader': 'Excessive trading frequency',
            'undertrader': 'Insufficient trading frequency'
        }

    def analyze_trading_behavior(self, trades_df):
        """Comprehensive behavioral analysis."""
        if trades_df.empty:
            return {}

        analysis = {
            'discipline_score': self._calculate_discipline_score(trades_df),
            'revenge_trading': self._detect_revenge_trading(trades_df),
            'overtrading': self._detect_overtrading(trades_df),
            'pattern_recognition': self._analyze_patterns(trades_df),
            'behavioral_labels': self._assign_behavioral_labels(trades_df),
            'trading_psychology': self._analyze_psychology(trades_df),
            'edge_opportunities': self._identify_edges(trades_df),
            'performance_segments': self._segment_performance(trades_df)
        }

        return analysis

    def _assign_behavioral_labels(self, trades_df):
        """Auto-tag behavioral patterns."""
        labels = []

        # Revenge trading detection
        if self._detect_revenge_trading(trades_df)['risk_score'] > 0.7:
            labels.append('revenge_trader')

        # Discipline assessment
        discipline_score = self._calculate_discipline_score(trades_df)
        if discipline_score > 0.8:
            labels.append('disciplined_trader')
        elif discipline_score < 0.4:
            labels.append('emotional_trader')

        # Trading frequency analysis
        daily_trades = trades_df.groupby(trades_df['entry_time'].dt.date).size()
        if daily_trades.mean() > 10:
            labels.append('overtrader')
        elif daily_trades.mean() < 2:
            labels.append('undertrader')

        return labels

    def _analyze_psychology(self, trades_df):
        """Deep psychological trading analysis."""
        psychology = {}

        # Loss aversion
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] < 0]

        if not wins.empty and not losses.empty:
            avg_win_time = (wins['exit_time'] - wins['entry_time']).mean()
            avg_loss_time = (losses['exit_time'] - losses['entry_time']).mean()

            psychology['cuts_losses_quickly'] = avg_loss_time < avg_win_time
            psychology['lets_winners_run'] = avg_win_time > avg_loss_time

        # Risk consistency
        if 'qty' in trades_df.columns:
            qty_std = trades_df['qty'].std()
            qty_mean = trades_df['qty'].mean()
            psychology['position_sizing_consistency'] = qty_std / qty_mean if qty_mean > 0 else 0

        return psychology

    def _identify_edges(self, trades_df):
        """Identify trading edges and opportunities."""
        edges = {}

        # Time-based edges
        trades_df['hour'] = trades_df['entry_time'].dt.hour
        hourly_pnl = trades_df.groupby('hour')['pnl'].agg(['mean', 'count'])
        best_hours = hourly_pnl[hourly_pnl['count'] >= 5].sort_values('mean', ascending=False).head(3)
        edges['best_trading_hours'] = best_hours.index.tolist()

        # Symbol-based edges
        if 'symbol' in trades_df.columns:
            symbol_performance = trades_df.groupby('symbol')['pnl'].agg(['mean', 'count', 'sum'])
            symbol_performance = symbol_performance[symbol_performance['count'] >= 5]
            edges['best_symbols'] = symbol_performance.sort_values('mean', ascending=False).head(5).index.tolist()

        # Streak analysis
        trades_df['trade_result'] = trades_df['pnl'].apply(lambda x: 1 if x > 0 else -1)
        edges['streak_performance'] = self._analyze_streaks(trades_df)

        return edges

    def _segment_performance(self, trades_df):
        """Segment performance by various criteria."""
        segments = {}

        # Day of week performance
        trades_df['day_of_week'] = trades_df['entry_time'].dt.day_name()
        day_performance = trades_df.groupby('day_of_week')['pnl'].agg(['mean', 'count', 'sum'])
        segments['by_day_of_week'] = day_performance.to_dict('index')

        # Monthly performance
        trades_df['month'] = trades_df['entry_time'].dt.to_period('M')
        monthly_performance = trades_df.groupby('month')['pnl'].agg(['mean', 'count', 'sum'])
        segments['by_month'] = monthly_performance.to_dict('index')

        # Trade size performance
        if 'qty' in trades_df.columns:
            trades_df['size_category'] = pd.qcut(trades_df['qty'], q=3, labels=['Small', 'Medium', 'Large'])
            size_performance = trades_df.groupby('size_category')['pnl'].agg(['mean', 'count', 'sum'])
            segments['by_trade_size'] = size_performance.to_dict('index')

        return segments

    def _analyze_streaks(self, trades_df):
        """Analyze winning/losing streaks."""
        streak_data = []
        current_streak = 0
        current_type = None

        for _, trade in trades_df.iterrows():
            result = 'win' if trade['pnl'] > 0 else 'loss'

            if result == current_type:
                current_streak += 1
            else:
                if current_streak > 0:
                    streak_data.append({'type': current_type, 'length': current_streak})
                current_streak = 1
                current_type = result

        # Add final streak
        if current_streak > 0:
            streak_data.append({'type': current_type, 'length': current_streak})

        streak_df = pd.DataFrame(streak_data)

        if not streak_df.empty:
            return {
                'max_winning_streak': streak_df[streak_df['type'] == 'win']['length'].max() if 'win' in streak_df['type'].values else 0,
                'max_losing_streak': streak_df[streak_df['type'] == 'loss']['length'].max() if 'loss' in streak_df['type'].values else 0,
                'avg_winning_streak': streak_df[streak_df['type'] == 'win']['length'].mean() if 'win' in streak_df['type'].values else 0,
                'avg_losing_streak': streak_df[streak_df['type'] == 'loss']['length'].mean() if 'loss' in streak_df['type'].values else 0
            }

        return {'max_winning_streak': 0, 'max_losing_streak': 0, 'avg_winning_streak': 0, 'avg_losing_streak': 0}