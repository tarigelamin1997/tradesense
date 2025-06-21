
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import streamlit as st

class PartnerAnalyticsTracker:
    """Track and analyze partner-specific metrics."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.init_analytics_tables()
    
    def init_analytics_tables(self):
        """Initialize partner analytics tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Partner revenue tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                revenue_type TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                description TEXT,
                billing_period TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Partner user engagement
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_user_engagement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                session_duration INTEGER,
                pages_viewed INTEGER,
                features_used TEXT,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Partner feature usage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_feature_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                feature_name TEXT NOT NULL,
                usage_count INTEGER DEFAULT 1,
                usage_date DATE DEFAULT CURRENT_DATE,
                user_id INTEGER,
                FOREIGN KEY (partner_id) REFERENCES partners (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def track_user_activity(self, partner_id: str, user_id: int, 
                           activity_type: str, activity_data: Dict = None):
        """Track user activity for partner analytics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO partner_user_activity 
            (partner_id, user_id, activity_type, activity_data)
            VALUES (?, ?, ?, ?)
        ''', (partner_id, user_id, activity_type, json.dumps(activity_data or {})))
        
        conn.commit()
        conn.close()
    
    def track_revenue(self, partner_id: str, revenue_type: str, 
                     amount: float, description: str = None):
        """Track revenue for partner."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO partner_revenue 
            (partner_id, revenue_type, amount, description)
            VALUES (?, ?, ?, ?)
        ''', (partner_id, revenue_type, amount, description))
        
        conn.commit()
        conn.close()
    
    def track_feature_usage(self, partner_id: str, feature_name: str, 
                           user_id: int = None):
        """Track feature usage for partner analytics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if entry exists for today
        cursor.execute('''
            SELECT id, usage_count FROM partner_feature_usage
            WHERE partner_id = ? AND feature_name = ? AND usage_date = CURRENT_DATE
        ''', (partner_id, feature_name))
        
        result = cursor.fetchone()
        
        if result:
            # Update existing entry
            cursor.execute('''
                UPDATE partner_feature_usage 
                SET usage_count = usage_count + 1
                WHERE id = ?
            ''', (result[0],))
        else:
            # Create new entry
            cursor.execute('''
                INSERT INTO partner_feature_usage 
                (partner_id, feature_name, user_id)
                VALUES (?, ?, ?)
            ''', (partner_id, feature_name, user_id))
        
        conn.commit()
        conn.close()
    
    def get_partner_metrics(self, partner_id: str, days: int = 30) -> Dict:
        """Get comprehensive partner metrics."""
        conn = sqlite3.connect(self.db_path)
        
        # User metrics
        user_query = '''
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN created_at > datetime('now', '-7 days') THEN 1 END) as new_users_week,
                COUNT(CASE WHEN last_login > datetime('now', '-7 days') THEN 1 END) as active_users_week,
                COUNT(CASE WHEN last_login > datetime('now', '-30 days') THEN 1 END) as active_users_month
            FROM users 
            WHERE partner_id = ?
        '''
        
        user_metrics = pd.read_sql_query(user_query, conn, params=(partner_id,)).iloc[0]
        
        # Revenue metrics
        revenue_query = '''
            SELECT 
                SUM(amount) as total_revenue,
                AVG(amount) as avg_revenue,
                COUNT(*) as revenue_transactions
            FROM partner_revenue 
            WHERE partner_id = ? AND recorded_at > datetime('now', '-{} days')
        '''.format(days)
        
        revenue_metrics = pd.read_sql_query(revenue_query, conn, params=(partner_id,)).iloc[0]
        
        # Feature usage
        feature_query = '''
            SELECT feature_name, SUM(usage_count) as total_usage
            FROM partner_feature_usage 
            WHERE partner_id = ? AND usage_date > date('now', '-{} days')
            GROUP BY feature_name
            ORDER BY total_usage DESC
            LIMIT 10
        '''.format(days)
        
        feature_usage = pd.read_sql_query(feature_query, conn, params=(partner_id,))
        
        conn.close()
        
        return {
            'user_metrics': user_metrics.to_dict(),
            'revenue_metrics': revenue_metrics.to_dict(),
            'feature_usage': feature_usage.to_dict('records')
        }
    
    def get_engagement_trends(self, partner_id: str, days: int = 30) -> pd.DataFrame:
        """Get user engagement trends."""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                DATE(last_activity) as date,
                COUNT(DISTINCT user_id) as active_users,
                AVG(session_duration) as avg_session_duration,
                SUM(pages_viewed) as total_page_views
            FROM partner_user_engagement
            WHERE partner_id = ? AND last_activity > datetime('now', '-{} days')
            GROUP BY DATE(last_activity)
            ORDER BY date
        '''.format(days)
        
        df = pd.read_sql_query(query, conn, params=(partner_id,))
        conn.close()
        
        return df
    
    def generate_partner_report(self, partner_id: str, 
                               report_type: str = 'monthly') -> Dict:
        """Generate comprehensive partner report."""
        days_map = {'weekly': 7, 'monthly': 30, 'quarterly': 90}
        days = days_map.get(report_type, 30)
        
        metrics = self.get_partner_metrics(partner_id, days)
        trends = self.get_engagement_trends(partner_id, days)
        
        # Calculate growth rates
        user_growth = self.calculate_growth_rate(partner_id, 'users', days)
        revenue_growth = self.calculate_growth_rate(partner_id, 'revenue', days)
        
        return {
            'period': report_type,
            'metrics': metrics,
            'trends': trends,
            'growth_rates': {
                'user_growth': user_growth,
                'revenue_growth': revenue_growth
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def calculate_growth_rate(self, partner_id: str, 
                             metric_type: str, days: int) -> float:
        """Calculate growth rate for a specific metric."""
        conn = sqlite3.connect(self.db_path)
        
        if metric_type == 'users':
            # User growth rate
            current_query = '''
                SELECT COUNT(*) FROM users 
                WHERE partner_id = ? AND created_at > datetime('now', '-{} days')
            '''.format(days)
            
            previous_query = '''
                SELECT COUNT(*) FROM users 
                WHERE partner_id = ? AND created_at BETWEEN 
                datetime('now', '-{} days') AND datetime('now', '-{} days')
            '''.format(days * 2, days)
            
        else:  # revenue
            current_query = '''
                SELECT COALESCE(SUM(amount), 0) FROM partner_revenue 
                WHERE partner_id = ? AND recorded_at > datetime('now', '-{} days')
            '''.format(days)
            
            previous_query = '''
                SELECT COALESCE(SUM(amount), 0) FROM partner_revenue 
                WHERE partner_id = ? AND recorded_at BETWEEN 
                datetime('now', '-{} days') AND datetime('now', '-{} days')
            '''.format(days * 2, days)
        
        current = conn.execute(current_query, (partner_id,)).fetchone()[0]
        previous = conn.execute(previous_query, (partner_id,)).fetchone()[0]
        
        conn.close()
        
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        
        return ((current - previous) / previous) * 100


def render_partner_analytics_widget(partner_id: str):
    """Render partner analytics widget for dashboard."""
    tracker = PartnerAnalyticsTracker()
    
    # Track page view
    tracker.track_feature_usage(partner_id, 'dashboard_view')
    
    # Get quick metrics
    metrics = tracker.get_partner_metrics(partner_id, 7)  # Last 7 days
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Active Users (7d)", 
            metrics['user_metrics']['active_users_week']
        )
    
    with col2:
        st.metric(
            "Revenue (7d)", 
            f"${metrics['revenue_metrics']['total_revenue'] or 0:.2f}"
        )
    
    with col3:
        top_feature = metrics['feature_usage'][0] if metrics['feature_usage'] else {'feature_name': 'N/A', 'total_usage': 0}
        st.metric(
            "Top Feature", 
            top_feature['feature_name'],
            delta=f"{top_feature['total_usage']} uses"
        )


# Integration function for main app
def track_user_action(action: str, user_data: Dict = None):
    """Helper function to track user actions across the app."""
    current_user = st.session_state.get('current_user')
    
    if current_user and current_user.get('partner_id'):
        tracker = PartnerAnalyticsTracker()
        tracker.track_user_activity(
            current_user['partner_id'],
            current_user['id'],
            action,
            user_data
        )
        
        # Track feature usage
        feature_map = {
            'trade_entry': 'Trade Entry',
            'analytics_view': 'Analytics Dashboard',
            'risk_analysis': 'Risk Management',
            'data_export': 'Data Export',
            'report_generation': 'Report Generation'
        }
        
        if action in feature_map:
            tracker.track_feature_usage(
                current_user['partner_id'],
                feature_map[action],
                current_user['id']
            )

if __name__ == "__main__":
    # Demo analytics tracking
    st.title("Partner Analytics Demo")
    
    tracker = PartnerAnalyticsTracker()
    
    # Sample data
    partner_id = "demo_partner"
    metrics = tracker.get_partner_metrics(partner_id)
    
    st.json(metrics)
