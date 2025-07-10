import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from collections import Counter, defaultdict
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models.trade import Trade
from models.mental_map import MentalMapEntry
from models.pattern_cluster import PatternCluster, PatternClusterCreate

class PatternDetectionEngine:
    """ML-powered trade pattern detection and clustering engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.feature_weights = {
            'instrument': 0.15,
            'hour_of_day': 0.20,
            'day_of_week': 0.10,
            'pnl_normalized': 0.25,
            'holding_time_hours': 0.15,
            'confidence_score': 0.10,
            'post_loss_trade': 0.05
        }
        
    def analyze_patterns(self, user_id: str, min_trades: int = 20) -> List[PatternCluster]:
        """Main method to detect and cluster trade patterns"""
        
        # Get trade data with mental map context
        trades_df = self._prepare_trade_features(user_id)
        
        if len(trades_df) < min_trades:
            return []
        
        # Perform clustering
        clusters = self._cluster_trades(trades_df)
        
        # Save clusters to database
        pattern_clusters = []
        for cluster_id, cluster_data in clusters.items():
            if cluster_id == -1:  # Skip noise cluster from DBSCAN
                continue
                
            cluster_obj = self._create_cluster_object(
                user_id, cluster_id, cluster_data, trades_df
            )
            pattern_clusters.append(cluster_obj)
        
        return pattern_clusters
    
    def _prepare_trade_features(self, user_id: str) -> pd.DataFrame:
        """Extract and engineer features for clustering"""
        
        # Get trades with mental map entries
        query = self.db.query(Trade).filter(Trade.user_id == user_id)
        trades = query.all()
        
        if not trades:
            return pd.DataFrame()
        
        # Convert to DataFrame
        trade_data = []
        for trade in trades:
            # Get associated mental map entry if exists
            mental_entry = self.db.query(MentalMapEntry).filter(
                MentalMapEntry.trade_id == trade.id
            ).first()
            
            trade_data.append({
                'id': trade.id,
                'symbol': trade.symbol,
                'direction': trade.direction,
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'pnl': trade.pnl or 0,
                'confidence_score': trade.confidence_score or 5,
                'strategy_tag': trade.strategy_tag or 'unknown',
                'mood': mental_entry.mood if mental_entry else 'neutral',
                'notes': trade.notes or ''
            })
        
        df = pd.DataFrame(trade_data)
        
        # Feature engineering
        df['entry_hour'] = pd.to_datetime(df['entry_time']).dt.hour
        df['entry_day_of_week'] = pd.to_datetime(df['entry_time']).dt.dayofweek
        df['holding_time_hours'] = (
            pd.to_datetime(df['exit_time']) - pd.to_datetime(df['entry_time'])
        ).dt.total_seconds() / 3600
        
        # Normalize PnL by position size proxy (use absolute value for clustering)
        df['pnl_normalized'] = df['pnl'] / (df['pnl'].std() + 1e-6)
        df['is_winner'] = (df['pnl'] > 0).astype(int)
        
        # Post-loss trade indicator
        df = df.sort_values('entry_time')
        df['prev_pnl'] = df['pnl'].shift(1)
        df['post_loss_trade'] = ((df['prev_pnl'] < 0) & (df['prev_pnl'].notna())).astype(int)
        
        # Sentiment analysis on notes (basic)
        df['notes_sentiment'] = df['notes'].apply(self._analyze_note_sentiment)
        
        return df
    
    def _analyze_note_sentiment(self, note: str) -> float:
        """Basic sentiment analysis of trade notes"""
        if not note:
            return 0.0
        
        note_lower = note.lower()
        positive_words = ['good', 'great', 'perfect', 'strong', 'confident', 'solid']
        negative_words = ['bad', 'terrible', 'weak', 'unsure', 'mistake', 'revenge', 'fomo']
        
        pos_count = sum(1 for word in positive_words if word in note_lower)
        neg_count = sum(1 for word in negative_words if word in note_lower)
        
        return (pos_count - neg_count) / max(len(note.split()), 1)
    
    def _cluster_trades(self, df: pd.DataFrame) -> Dict[int, Dict[str, Any]]:
        """Perform clustering on trade features"""
        
        # Prepare features for clustering
        feature_columns = [
            'entry_hour', 'entry_day_of_week', 'pnl_normalized', 
            'holding_time_hours', 'confidence_score', 'post_loss_trade',
            'notes_sentiment'
        ]
        
        # Handle categorical variables
        le_symbol = LabelEncoder()
        le_mood = LabelEncoder()
        le_strategy = LabelEncoder()
        
        df_encoded = df.copy()
        df_encoded['symbol_encoded'] = le_symbol.fit_transform(df['symbol'])
        df_encoded['mood_encoded'] = le_mood.fit_transform(df['mood'])
        df_encoded['strategy_encoded'] = le_strategy.fit_transform(df['strategy_tag'])
        
        feature_columns.extend(['symbol_encoded', 'mood_encoded', 'strategy_encoded'])
        
        # Fill missing values
        X = df_encoded[feature_columns].fillna(0)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Try different clustering approaches
        best_clusters = None
        best_score = -1
        best_labels = None
        
        # DBSCAN - good for finding patterns of varying density
        for eps in [0.5, 0.8, 1.0, 1.2]:
            dbscan = DBSCAN(eps=eps, min_samples=max(3, len(df) // 10))
            labels = dbscan.fit_predict(X_scaled)
            
            if len(set(labels)) > 1 and len(set(labels)) < len(df) // 2:
                try:
                    score = silhouette_score(X_scaled, labels)
                    if score > best_score:
                        best_score = score
                        best_labels = labels
                        best_clusters = 'dbscan'
                except:
                    continue
        
        # KMeans - for when we want specific number of clusters
        for n_clusters in range(2, min(8, len(df) // 5)):
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)
            
            try:
                score = silhouette_score(X_scaled, labels)
                if score > best_score:
                    best_score = score
                    best_labels = labels
                    best_clusters = 'kmeans'
            except:
                continue
        
        if best_labels is None:
            return {}
        
        # Group trades by cluster
        df['cluster'] = best_labels
        clusters = {}
        
        for cluster_id in set(best_labels):
            cluster_trades = df[df['cluster'] == cluster_id]
            
            clusters[cluster_id] = {
                'trades': cluster_trades,
                'size': len(cluster_trades),
                'avg_pnl': cluster_trades['pnl'].mean(),
                'win_rate': (cluster_trades['pnl'] > 0).mean(),
                'total_pnl': cluster_trades['pnl'].sum(),
                'dominant_features': self._extract_dominant_features(cluster_trades),
                'silhouette_score': best_score
            }
        
        return clusters
    
    def _extract_dominant_features(self, cluster_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract dominant characteristics of a trade cluster"""
        
        features = {}
        
        # Most common instrument
        features['instrument'] = cluster_df['symbol'].mode().iloc[0] if not cluster_df['symbol'].mode().empty else 'mixed'
        
        # Time patterns
        features['avg_hour'] = cluster_df['entry_hour'].mean()
        features['time_window'] = self._categorize_time_window(features['avg_hour'])
        
        # Most common day
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        most_common_day = cluster_df['entry_day_of_week'].mode()
        features['dominant_day'] = day_names[most_common_day.iloc[0]] if not most_common_day.empty else 'mixed'
        
        # Strategy patterns
        features['dominant_strategy'] = cluster_df['strategy_tag'].mode().iloc[0] if not cluster_df['strategy_tag'].mode().empty else 'mixed'
        
        # Mood patterns
        features['dominant_mood'] = cluster_df['mood'].mode().iloc[0] if not cluster_df['mood'].mode().empty else 'neutral'
        
        # Holding time
        features['avg_holding_hours'] = cluster_df['holding_time_hours'].mean()
        features['holding_category'] = self._categorize_holding_time(features['avg_holding_hours'])
        
        # Behavioral flags
        features['post_loss_frequency'] = cluster_df['post_loss_trade'].mean()
        features['avg_confidence'] = cluster_df['confidence_score'].mean()
        
        return features
    
    def _categorize_time_window(self, hour: float) -> str:
        """Categorize trading hour into time windows"""
        if 9 <= hour < 10:
            return "Market Open (9-10 AM)"
        elif 10 <= hour < 12:
            return "Morning (10-12 PM)"
        elif 12 <= hour < 14:
            return "Lunch (12-2 PM)"
        elif 14 <= hour < 16:
            return "Afternoon (2-4 PM)"
        elif 15.5 <= hour < 16:
            return "Market Close (3:30-4 PM)"
        else:
            return f"Hour {int(hour)}"
    
    def _categorize_holding_time(self, hours: float) -> str:
        """Categorize holding time"""
        if hours < 0.5:
            return "Scalp (< 30 min)"
        elif hours < 2:
            return "Short-term (30 min - 2 hrs)"
        elif hours < 8:
            return "Intraday (2-8 hrs)"
        elif hours < 24:
            return "Day trade (8-24 hrs)"
        else:
            return "Swing (> 1 day)"
    
    def _create_cluster_object(
        self, user_id: str, cluster_id: int, cluster_data: Dict[str, Any], df: pd.DataFrame
    ) -> PatternCluster:
        """Create and save PatternCluster object"""
        
        trades_in_cluster = cluster_data['trades']
        features = cluster_data['dominant_features']
        
        # Generate descriptive name
        name = self._generate_cluster_name(features, cluster_data)
        
        # Generate summary
        summary = self._generate_cluster_summary(features, cluster_data)
        
        # Create cluster object
        cluster_create = PatternClusterCreate(
            name=name,
            summary=summary,
            cluster_type="performance",
            trade_ids=trades_in_cluster['id'].tolist(),
            pattern_features=features
        )
        
        cluster_obj = PatternCluster(
            user_id=user_id,
            name=cluster_create.name,
            summary=cluster_create.summary,
            cluster_type=cluster_create.cluster_type,
            trade_ids=cluster_create.trade_ids,
            trade_count=str(len(cluster_create.trade_ids)),
            avg_return=cluster_data['avg_pnl'],
            win_rate=cluster_data['win_rate'],
            total_pnl=cluster_data['total_pnl'],
            risk_reward_ratio=abs(cluster_data['avg_pnl']) / max(trades_in_cluster['pnl'].std(), 0.01),
            pattern_features=cluster_create.pattern_features,
            dominant_instrument=features.get('instrument'),
            dominant_time_window=features.get('time_window'),
            dominant_setup=features.get('dominant_strategy'),
            dominant_mood=features.get('dominant_mood'),
            cluster_score=cluster_data['silhouette_score']
        )
        
        self.db.add(cluster_obj)
        self.db.commit()
        self.db.refresh(cluster_obj)
        
        return cluster_obj
    
    def _generate_cluster_name(self, features: Dict[str, Any], cluster_data: Dict[str, Any]) -> str:
        """Generate descriptive name for cluster"""
        
        parts = []
        
        # Performance indicator
        avg_pnl = cluster_data['avg_pnl']
        if avg_pnl > 0:
            parts.append("🟩 Profitable")
        else:
            parts.append("🔻 Losing")
        
        # Key characteristics
        if features['instrument'] != 'mixed':
            parts.append(features['instrument'])
        
        if features['time_window']:
            parts.append(features['time_window'])
        
        if features['post_loss_frequency'] > 0.5:
            parts.append("Post-Loss")
        
        if features['dominant_mood'] not in ['neutral', 'mixed']:
            parts.append(f"{features['dominant_mood'].title()} Mood")
        
        return " | ".join(parts[:4])  # Limit to 4 parts
    
    def _generate_cluster_summary(self, features: Dict[str, Any], cluster_data: Dict[str, Any]) -> str:
        """Generate detailed summary for cluster"""
        
        summary_parts = []
        
        # Performance summary
        win_rate = cluster_data['win_rate'] * 100
        avg_pnl = cluster_data['avg_pnl']
        trade_count = cluster_data['size']
        
        summary_parts.append(
            f"Pattern of {trade_count} trades with {win_rate:.1f}% win rate "
            f"and ${avg_pnl:.2f} average P&L."
        )
        
        # Key characteristics
        chars = []
        if features['instrument'] != 'mixed':
            chars.append(f"Primarily {features['instrument']}")
        
        if features['time_window']:
            chars.append(f"during {features['time_window']}")
        
        if features['holding_category']:
            chars.append(f"with {features['holding_category']} holds")
        
        if features['post_loss_frequency'] > 0.3:
            chars.append("often following losses")
        
        if chars:
            summary_parts.append(" ".join(chars) + ".")
        
        # Behavioral insights
        if features['avg_confidence'] < 4:
            summary_parts.append("Low confidence trades - consider avoiding this pattern.")
        elif features['avg_confidence'] > 7:
            summary_parts.append("High confidence pattern - potential edge identified.")
        
        return " ".join(summary_parts)
