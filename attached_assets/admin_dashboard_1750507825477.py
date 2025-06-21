
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from auth import AuthManager, require_auth
from system_status import system_monitor
from logging_manager import logger_instance
from partner_analytics import PartnerAnalyticsTracker
from sync_engine import sync_engine

class AdminDashboard:
    """Internal admin dashboard for monitoring system health and usage."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()
        self.analytics_tracker = PartnerAnalyticsTracker()
    
    def get_sync_analytics(self, days: int = 30) -> Dict:
        """Get comprehensive sync analytics."""
        conn = sqlite3.connect(self.db_path)
        
        # Overall sync stats
        sync_stats_query = '''
            SELECT 
                COUNT(*) as total_syncs,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_syncs,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_syncs,
                AVG(duration_seconds) as avg_duration,
                SUM(records_processed) as total_records,
                COUNT(DISTINCT user_id) as active_sync_users,
                COUNT(DISTINCT connector_name) as connectors_used
            FROM sync_logs 
            WHERE timestamp > datetime('now', '-{} days')
        '''.format(days)
        
        stats = pd.read_sql_query(sync_stats_query, conn).iloc[0]
        
        # Sync trends over time
        trends_query = '''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as sync_count,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failure_count,
                AVG(duration_seconds) as avg_duration
            FROM sync_logs 
            WHERE timestamp > datetime('now', '-{} days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        '''.format(days)
        
        trends = pd.read_sql_query(trends_query, conn)
        
        # Connector performance
        connector_query = '''
            SELECT 
                connector_name,
                COUNT(*) as total_syncs,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_syncs,
                AVG(duration_seconds) as avg_duration,
                COUNT(DISTINCT user_id) as unique_users
            FROM sync_logs 
            WHERE timestamp > datetime('now', '-{} days')
            GROUP BY connector_name
            ORDER BY total_syncs DESC
        '''.format(days)
        
        connectors = pd.read_sql_query(connector_query, conn)
        
        # Partner sync breakdown
        partner_sync_query = '''
            SELECT 
                COALESCE(partner_id, 'Individual') as partner_name,
                COUNT(*) as sync_count,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
                COUNT(DISTINCT user_id) as user_count,
                SUM(records_processed) as total_records
            FROM sync_logs 
            WHERE timestamp > datetime('now', '-{} days')
            GROUP BY partner_id
            ORDER BY sync_count DESC
        '''.format(days)
        
        partner_syncs = pd.read_sql_query(partner_sync_query, conn)
        
        conn.close()
        
        return {
            'stats': stats.to_dict(),
            'trends': trends,
            'connectors': connectors,
            'partner_breakdown': partner_syncs
        }
    
    def get_error_analytics(self, days: int = 30) -> Dict:
        """Get comprehensive error analytics."""
        conn = sqlite3.connect(self.db_path)
        
        # Error overview
        error_overview_query = '''
            SELECT 
                level,
                category,
                COUNT(*) as count,
                COUNT(DISTINCT user_id) as affected_users,
                COUNT(DISTINCT partner_id) as affected_partners
            FROM system_logs 
            WHERE level IN ('ERROR', 'CRITICAL') 
            AND timestamp > datetime('now', '-{} days')
            GROUP BY level, category
            ORDER BY count DESC
        '''.format(days)
        
        error_overview = pd.read_sql_query(error_overview_query, conn)
        
        # Error trends
        error_trends_query = '''
            SELECT 
                DATE(timestamp) as date,
                level,
                COUNT(*) as error_count
            FROM system_logs 
            WHERE level IN ('ERROR', 'CRITICAL') 
            AND timestamp > datetime('now', '-{} days')
            GROUP BY DATE(timestamp), level
            ORDER BY date, level
        '''.format(days)
        
        error_trends = pd.read_sql_query(error_trends_query, conn)
        
        # Top error patterns
        error_patterns_query = '''
            SELECT 
                error_signature,
                severity,
                occurrence_count,
                first_occurrence,
                last_occurrence,
                status
            FROM error_patterns 
            WHERE last_occurrence > datetime('now', '-{} days')
            ORDER BY occurrence_count DESC
            LIMIT 20
        '''.format(days)
        
        error_patterns = pd.read_sql_query(error_patterns_query, conn)
        
        # Recent critical errors
        critical_errors_query = '''
            SELECT 
                timestamp,
                message,
                details,
                user_id,
                partner_id
            FROM system_logs 
            WHERE level = 'CRITICAL' 
            AND timestamp > datetime('now', '-{} days')
            ORDER BY timestamp DESC
            LIMIT 50
        '''.format(days)
        
        critical_errors = pd.read_sql_query(critical_errors_query, conn)
        
        conn.close()
        
        return {
            'overview': error_overview,
            'trends': error_trends,
            'patterns': error_patterns,
            'critical_errors': critical_errors
        }
    
    def get_user_analytics(self, days: int = 30) -> Dict:
        """Get user activity and engagement analytics."""
        conn = sqlite3.connect(self.db_path)
        
        # User activity overview
        user_overview_query = '''
            SELECT 
                COUNT(DISTINCT user_id) as total_active_users,
                COUNT(DISTINCT CASE WHEN partner_id IS NOT NULL THEN user_id END) as partner_users,
                COUNT(DISTINCT CASE WHEN partner_id IS NULL THEN user_id END) as individual_users,
                COUNT(*) as total_actions,
                COUNT(DISTINCT action_type) as unique_action_types
            FROM user_actions 
            WHERE timestamp > datetime('now', '-{} days')
        '''.format(days)
        
        user_overview = pd.read_sql_query(user_overview_query, conn).iloc[0]
        
        # Daily active users trend
        dau_query = '''
            SELECT 
                DATE(timestamp) as date,
                COUNT(DISTINCT user_id) as daily_active_users,
                COUNT(DISTINCT CASE WHEN partner_id IS NOT NULL THEN user_id END) as partner_dau,
                COUNT(DISTINCT CASE WHEN partner_id IS NULL THEN user_id END) as individual_dau
            FROM user_actions 
            WHERE timestamp > datetime('now', '-{} days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        '''.format(days)
        
        dau_trends = pd.read_sql_query(dau_query, conn)
        
        # Feature usage
        feature_usage_query = '''
            SELECT 
                action_type,
                COUNT(*) as usage_count,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT partner_id) as unique_partners
            FROM user_actions 
            WHERE timestamp > datetime('now', '-{} days')
            GROUP BY action_type
            ORDER BY usage_count DESC
        '''.format(days)
        
        feature_usage = pd.read_sql_query(feature_usage_query, conn)
        
        # User engagement by partner
        partner_engagement_query = '''
            SELECT 
                COALESCE(partner_id, 'Individual') as partner_name,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_actions,
                AVG(session_duration) as avg_session_duration,
                COUNT(*) / COUNT(DISTINCT user_id) as actions_per_user
            FROM user_actions 
            WHERE timestamp > datetime('now', '-{} days')
            GROUP BY partner_id
            ORDER BY active_users DESC
        '''.format(days)
        
        partner_engagement = pd.read_sql_query(partner_engagement_query, conn)
        
        conn.close()
        
        return {
            'overview': user_overview.to_dict(),
            'dau_trends': dau_trends,
            'feature_usage': feature_usage,
            'partner_engagement': partner_engagement
        }
    
    def get_partner_usage_analytics(self, days: int = 30) -> Dict:
        """Get detailed per-partner usage analytics."""
        conn = sqlite3.connect(self.db_path)
        
        # Partner overview with billing data
        partner_overview_query = '''
            SELECT 
                p.id as partner_id,
                p.name as partner_name,
                p.type as partner_type,
                p.status,
                COUNT(DISTINCT u.id) as total_users,
                COUNT(DISTINCT CASE WHEN u.last_login > datetime('now', '-7 days') THEN u.id END) as active_users_7d,
                COUNT(DISTINCT CASE WHEN u.last_login > datetime('now', '-30 days') THEN u.id END) as active_users_30d,
                COALESCE(SUM(pr.amount), 0) as total_revenue
            FROM partners p
            LEFT JOIN users u ON p.id = u.partner_id
            LEFT JOIN partner_revenue pr ON p.id = pr.partner_id 
                AND pr.recorded_at > datetime('now', '-{} days')
            GROUP BY p.id, p.name, p.type, p.status
            ORDER BY total_users DESC
        '''.format(days)
        
        partner_overview = pd.read_sql_query(partner_overview_query, conn)
        
        # Partner feature usage
        partner_features_query = '''
            SELECT 
                partner_id,
                feature_name,
                SUM(usage_count) as total_usage,
                COUNT(DISTINCT usage_date) as active_days
            FROM partner_feature_usage 
            WHERE usage_date > date('now', '-{} days')
            GROUP BY partner_id, feature_name
            ORDER BY partner_id, total_usage DESC
        '''.format(days)
        
        partner_features = pd.read_sql_query(partner_features_query, conn)
        
        # Partner sync health
        partner_sync_health_query = '''
            SELECT 
                partner_id,
                COUNT(*) as total_syncs,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_syncs,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_syncs,
                AVG(duration_seconds) as avg_duration,
                MAX(timestamp) as last_sync
            FROM sync_logs 
            WHERE timestamp > datetime('now', '-{} days')
            AND partner_id IS NOT NULL
            GROUP BY partner_id
            ORDER BY total_syncs DESC
        '''.format(days)
        
        partner_sync_health = pd.read_sql_query(partner_sync_health_query, conn)
        
        conn.close()
        
        return {
            'overview': partner_overview,
            'feature_usage': partner_features,
            'sync_health': partner_sync_health
        }

    @require_auth
    def render_admin_dashboard(self, current_user: Dict):
        """Render the main admin dashboard."""
        # Check admin permissions
        if current_user.get('role') not in ['admin', 'super_admin']:
            st.error("🚫 Admin access required")
            return
        
        st.title("🛠️ Admin Dashboard")
        st.caption("Internal monitoring and analytics for system administrators")
        
        # Time period selector
        col1, col2, col3 = st.columns([2, 2, 4])
        
        with col1:
            time_period = st.selectbox("Time Period", 
                                     options=[7, 14, 30, 60, 90], 
                                     format_func=lambda x: f"{x} days",
                                     index=2)
        
        with col2:
            refresh_interval = st.selectbox("Auto Refresh", 
                                          options=[0, 30, 60, 300], 
                                          format_func=lambda x: "Off" if x == 0 else f"{x}s",
                                          index=0)
        
        with col3:
            if st.button("🔄 Refresh Data", type="primary"):
                st.rerun()
        
        # Auto refresh logic
        if refresh_interval > 0:
            st.info(f"⏱️ Auto-refreshing every {refresh_interval} seconds")
            import time
            time.sleep(refresh_interval)
            st.rerun()
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "🔄 Sync Analytics", 
            "🚨 Error Monitoring", 
            "👥 User Analytics", 
            "🤝 Partner Usage"
        ])
        
        with tab1:
            self.render_overview_tab(time_period)
        
        with tab2:
            self.render_sync_analytics_tab(time_period)
        
        with tab3:
            self.render_error_monitoring_tab(time_period)
        
        with tab4:
            self.render_user_analytics_tab(time_period)
        
        with tab5:
            self.render_partner_usage_tab(time_period)
    
    def render_overview_tab(self, days: int):
        """Render system overview tab."""
        st.subheader("🎯 System Health Overview")
        
        # Get overall metrics
        sync_data = self.get_sync_analytics(days)
        error_data = self.get_error_analytics(days)
        user_data = self.get_user_analytics(days)
        partner_data = self.get_partner_usage_analytics(days)
        
        # Key metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            success_rate = (sync_data['stats']['successful_syncs'] / max(sync_data['stats']['total_syncs'], 1)) * 100
            st.metric("Sync Success Rate", f"{success_rate:.1f}%", 
                     delta="Good" if success_rate > 95 else "Needs Attention")
        
        with col2:
            st.metric("Active Users", user_data['overview']['total_active_users'], 
                     delta=f"+{user_data['overview']['total_active_users'] // 10}")
        
        with col3:
            error_count = len(error_data['overview'])
            st.metric("Error Events", error_count,
                     delta="Low" if error_count < 10 else "High")
        
        with col4:
            st.metric("Partner Users", user_data['overview']['partner_users'])
        
        with col5:
            total_revenue = partner_data['overview']['total_revenue'].sum() if not partner_data['overview'].empty else 0
            st.metric("Partner Revenue", f"${total_revenue:,.2f}")
        
        # System status widget
        st.divider()
        system_monitor.render_status_widget()
        
        # Health indicators
        st.subheader("🚦 Health Indicators")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sync health
            if success_rate > 95:
                st.success("✅ Sync Health: Excellent")
            elif success_rate > 85:
                st.warning("⚠️ Sync Health: Good")
            else:
                st.error("🚨 Sync Health: Needs Attention")
            
            # Error rate
            total_actions = user_data['overview']['total_actions']
            error_rate = (error_count / max(total_actions, 1)) * 100
            
            if error_rate < 0.1:
                st.success("✅ Error Rate: Low")
            elif error_rate < 1:
                st.warning("⚠️ Error Rate: Moderate")
            else:
                st.error("🚨 Error Rate: High")
        
        with col2:
            # User engagement
            actions_per_user = user_data['overview']['total_actions'] / max(user_data['overview']['total_active_users'], 1)
            
            if actions_per_user > 50:
                st.success("✅ User Engagement: High")
            elif actions_per_user > 20:
                st.warning("⚠️ User Engagement: Moderate")
            else:
                st.error("🚨 User Engagement: Low")
            
            # Partner satisfaction
            if not partner_data['overview'].empty:
                avg_partner_users = partner_data['overview']['active_users_7d'].mean()
                if avg_partner_users > 10:
                    st.success("✅ Partner Adoption: Strong")
                elif avg_partner_users > 5:
                    st.warning("⚠️ Partner Adoption: Moderate")
                else:
                    st.error("🚨 Partner Adoption: Weak")
    
    def render_sync_analytics_tab(self, days: int):
        """Render sync analytics tab."""
        st.subheader("🔄 Sync Analytics & Performance")
        
        sync_data = self.get_sync_analytics(days)
        
        # Key sync metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Syncs", f"{sync_data['stats']['total_syncs']:,}")
        
        with col2:
            success_rate = (sync_data['stats']['successful_syncs'] / max(sync_data['stats']['total_syncs'], 1)) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            st.metric("Avg Duration", f"{sync_data['stats']['avg_duration']:.1f}s")
        
        with col4:
            st.metric("Records Processed", f"{sync_data['stats']['total_records']:,}")
        
        # Sync trends chart
        if not sync_data['trends'].empty:
            st.subheader("📈 Sync Trends Over Time")
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Daily Sync Count', 'Success vs Failure Rate', 
                              'Average Duration', 'Cumulative Records'),
                specs=[[{"secondary_y": False}, {"secondary_y": True}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Daily sync count
            fig.add_trace(
                go.Scatter(x=sync_data['trends']['date'], 
                          y=sync_data['trends']['sync_count'],
                          name='Total Syncs', line=dict(color='blue')),
                row=1, col=1
            )
            
            # Success vs failure rate
            sync_data['trends']['success_rate'] = (sync_data['trends']['success_count'] / sync_data['trends']['sync_count']) * 100
            
            fig.add_trace(
                go.Scatter(x=sync_data['trends']['date'], 
                          y=sync_data['trends']['success_rate'],
                          name='Success Rate %', line=dict(color='green')),
                row=1, col=2
            )
            
            fig.add_trace(
                go.Scatter(x=sync_data['trends']['date'], 
                          y=sync_data['trends']['failure_count'],
                          name='Failures', line=dict(color='red')),
                row=1, col=2, secondary_y=True
            )
            
            # Average duration
            fig.add_trace(
                go.Scatter(x=sync_data['trends']['date'], 
                          y=sync_data['trends']['avg_duration'],
                          name='Avg Duration (s)', line=dict(color='orange')),
                row=2, col=1
            )
            
            # Cumulative records (calculated)
            sync_data['trends']['cumulative_records'] = sync_data['trends']['sync_count'].cumsum() * 100  # Estimate
            fig.add_trace(
                go.Scatter(x=sync_data['trends']['date'], 
                          y=sync_data['trends']['cumulative_records'],
                          name='Cumulative Records', line=dict(color='purple')),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Connector performance
        if not sync_data['connectors'].empty:
            st.subheader("🔌 Connector Performance")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Success rate by connector
                sync_data['connectors']['success_rate'] = (
                    sync_data['connectors']['successful_syncs'] / 
                    sync_data['connectors']['total_syncs'] * 100
                )
                
                fig = px.bar(sync_data['connectors'], 
                           x='connector_name', y='success_rate',
                           title='Success Rate by Connector',
                           color='success_rate',
                           color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Performance table
                st.write("**Connector Details**")
                display_df = sync_data['connectors'][['connector_name', 'total_syncs', 'successful_syncs', 'avg_duration', 'unique_users']]
                display_df.columns = ['Connector', 'Total', 'Success', 'Avg Duration (s)', 'Users']
                st.dataframe(display_df, use_container_width=True)
        
        # Partner sync breakdown
        if not sync_data['partner_breakdown'].empty:
            st.subheader("🤝 Partner Sync Activity")
            
            fig = px.treemap(sync_data['partner_breakdown'], 
                           path=['partner_name'], 
                           values='sync_count',
                           color='success_count',
                           title='Sync Volume by Partner')
            st.plotly_chart(fig, use_container_width=True)
    
    def render_error_monitoring_tab(self, days: int):
        """Render error monitoring tab."""
        st.subheader("🚨 Error Monitoring & Analysis")
        
        error_data = self.get_error_analytics(days)
        
        # Error overview
        if not error_data['overview'].empty:
            col1, col2, col3 = st.columns(3)
            
            total_errors = error_data['overview']['count'].sum()
            critical_errors = error_data['overview'][error_data['overview']['level'] == 'CRITICAL']['count'].sum()
            affected_users = error_data['overview']['affected_users'].sum()
            
            with col1:
                st.metric("Total Errors", f"{total_errors:,}")
            
            with col2:
                st.metric("Critical Errors", f"{critical_errors:,}", 
                         delta="🚨 High" if critical_errors > 10 else "✅ Low")
            
            with col3:
                st.metric("Affected Users", f"{affected_users:,}")
            
            # Error breakdown
            st.subheader("📊 Error Breakdown")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Errors by level
                fig = px.pie(error_data['overview'], 
                           values='count', names='level',
                           title='Errors by Severity Level',
                           color_discrete_map={'ERROR': 'orange', 'CRITICAL': 'red'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Errors by category
                fig = px.bar(error_data['overview'], 
                           x='category', y='count',
                           color='level',
                           title='Errors by Category',
                           color_discrete_map={'ERROR': 'orange', 'CRITICAL': 'red'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Error trends
        if not error_data['trends'].empty:
            st.subheader("📈 Error Trends")
            
            pivot_df = error_data['trends'].pivot(index='date', columns='level', values='error_count').fillna(0)
            
            fig = go.Figure()
            for level in pivot_df.columns:
                color = 'red' if level == 'CRITICAL' else 'orange'
                fig.add_trace(go.Scatter(
                    x=pivot_df.index, 
                    y=pivot_df[level],
                    name=level,
                    line=dict(color=color),
                    stackgroup='one'
                ))
            
            fig.update_layout(title='Error Trends Over Time', xaxis_title='Date', yaxis_title='Error Count')
            st.plotly_chart(fig, use_container_width=True)
        
        # Top error patterns
        if not error_data['patterns'].empty:
            st.subheader("🔍 Top Error Patterns")
            
            # Filter for active patterns
            active_patterns = error_data['patterns'][error_data['patterns']['status'] == 'active']
            
            if not active_patterns.empty:
                st.warning(f"⚠️ **{len(active_patterns)} active error patterns** require attention")
                
                for _, pattern in active_patterns.head(10).iterrows():
                    with st.expander(f"🔥 {pattern['error_signature'][:100]}... ({pattern['occurrence_count']} occurrences)"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Severity:** {pattern['severity']}")
                            st.write(f"**First Seen:** {pattern['first_occurrence']}")
                            st.write(f"**Last Seen:** {pattern['last_occurrence']}")
                        
                        with col2:
                            st.write(f"**Occurrences:** {pattern['occurrence_count']}")
                            st.write(f"**Status:** {pattern['status']}")
                            
                            if st.button(f"Mark as Resolved", key=f"resolve_{pattern['error_signature'][:20]}"):
                                # Mark pattern as resolved
                                conn = sqlite3.connect(self.db_path)
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE error_patterns 
                                    SET status = 'resolved' 
                                    WHERE error_signature = ?
                                ''', (pattern['error_signature'],))
                                conn.commit()
                                conn.close()
                                st.success("Pattern marked as resolved!")
                                st.rerun()
            else:
                st.success("✅ No active error patterns detected")
        
        # Recent critical errors
        if not error_data['critical_errors'].empty:
            st.subheader("🚨 Recent Critical Errors")
            
            for _, error in error_data['critical_errors'].head(20).iterrows():
                with st.expander(f"🚨 {error['timestamp']} - {error['message'][:100]}..."):
                    st.write(f"**Time:** {error['timestamp']}")
                    st.write(f"**Message:** {error['message']}")
                    
                    if error['user_id']:
                        st.write(f"**User ID:** {error['user_id']}")
                    
                    if error['partner_id']:
                        st.write(f"**Partner ID:** {error['partner_id']}")
                    
                    if error['details']:
                        try:
                            details = json.loads(error['details'])
                            st.json(details)
                        except:
                            st.text(error['details'])
    
    def render_user_analytics_tab(self, days: int):
        """Render user analytics tab."""
        st.subheader("👥 User Activity & Engagement")
        
        user_data = self.get_user_analytics(days)
        
        # User overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Active Users", f"{user_data['overview']['total_active_users']:,}")
        
        with col2:
            st.metric("Partner Users", f"{user_data['overview']['partner_users']:,}")
        
        with col3:
            st.metric("Individual Users", f"{user_data['overview']['individual_users']:,}")
        
        with col4:
            actions_per_user = user_data['overview']['total_actions'] / max(user_data['overview']['total_active_users'], 1)
            st.metric("Actions per User", f"{actions_per_user:.1f}")
        
        # Daily active users trend
        if not user_data['dau_trends'].empty:
            st.subheader("📈 Daily Active Users Trend")
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=user_data['dau_trends']['date'],
                y=user_data['dau_trends']['daily_active_users'],
                name='Total DAU',
                line=dict(color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=user_data['dau_trends']['date'],
                y=user_data['dau_trends']['partner_dau'],
                name='Partner Users',
                line=dict(color='green')
            ))
            
            fig.add_trace(go.Scatter(
                x=user_data['dau_trends']['date'],
                y=user_data['dau_trends']['individual_dau'],
                name='Individual Users',
                line=dict(color='orange')
            ))
            
            fig.update_layout(
                title='Daily Active Users Over Time',
                xaxis_title='Date',
                yaxis_title='Active Users'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Feature usage analysis
        if not user_data['feature_usage'].empty:
            st.subheader("🎯 Feature Usage Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Most used features
                top_features = user_data['feature_usage'].head(10)
                
                fig = px.bar(top_features, 
                           x='usage_count', y='action_type',
                           orientation='h',
                           title='Most Used Features',
                           color='usage_count',
                           color_continuous_scale='Blues')
                
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Feature adoption (unique users)
                fig = px.scatter(user_data['feature_usage'], 
                               x='unique_users', y='usage_count',
                               hover_data=['action_type'],
                               title='Feature Adoption vs Usage',
                               labels={'unique_users': 'Unique Users', 'usage_count': 'Total Usage'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Partner engagement comparison
        if not user_data['partner_engagement'].empty:
            st.subheader("🤝 Partner Engagement Comparison")
            
            # Sort by actions per user
            user_data['partner_engagement'] = user_data['partner_engagement'].sort_values('actions_per_user', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(user_data['partner_engagement'], 
                           x='partner_name', y='active_users',
                           title='Active Users by Partner',
                           color='active_users',
                           color_continuous_scale='Greens')
                
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(user_data['partner_engagement'], 
                           x='partner_name', y='actions_per_user',
                           title='Engagement Level (Actions per User)',
                           color='actions_per_user',
                           color_continuous_scale='Blues')
                
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed partner engagement table
            st.write("**Partner Engagement Details**")
            display_df = user_data['partner_engagement'][['partner_name', 'active_users', 'total_actions', 'actions_per_user', 'avg_session_duration']]
            display_df.columns = ['Partner', 'Active Users', 'Total Actions', 'Actions/User', 'Avg Session (min)']
            display_df['Avg Session (min)'] = display_df['Avg Session (min)'].fillna(0).round(1)
            
            st.dataframe(display_df, use_container_width=True)
    
    def render_partner_usage_tab(self, days: int):
        """Render partner usage analytics tab."""
        st.subheader("🤝 Partner Usage & Revenue Analytics")
        
        partner_data = self.get_partner_usage_analytics(days)
        
        if partner_data['overview'].empty:
            st.info("No partner data available for the selected time period")
            return
        
        # Partner overview
        st.subheader("📊 Partner Overview")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Partners", len(partner_data['overview']))
        
        with col2:
            active_partners = len(partner_data['overview'][partner_data['overview']['active_users_7d'] > 0])
            st.metric("Active Partners", active_partners)
        
        with col3:
            total_partner_users = partner_data['overview']['total_users'].sum()
            st.metric("Total Partner Users", f"{total_partner_users:,}")
        
        with col4:
            total_revenue = partner_data['overview']['total_revenue'].sum()
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
        
        # Partner performance table
        st.subheader("🏆 Partner Performance Leaderboard")
        
        # Calculate additional metrics
        partner_data['overview']['user_growth_rate'] = (
            (partner_data['overview']['active_users_7d'] / 
             partner_data['overview']['active_users_30d'].replace(0, 1)) * 100
        ).fillna(0)
        
        partner_data['overview']['revenue_per_user'] = (
            partner_data['overview']['total_revenue'] / 
            partner_data['overview']['total_users'].replace(0, 1)
        ).fillna(0)
        
        # Display table with key metrics
        display_columns = ['partner_name', 'partner_type', 'status', 'total_users', 
                          'active_users_7d', 'active_users_30d', 'total_revenue', 'revenue_per_user']
        
        partner_table = partner_data['overview'][display_columns].copy()
        partner_table.columns = ['Partner', 'Type', 'Status', 'Total Users', 
                                'Active (7d)', 'Active (30d)', 'Revenue', 'Revenue/User']
        
        # Format revenue columns
        partner_table['Revenue'] = partner_table['Revenue'].apply(lambda x: f"${x:,.2f}")
        partner_table['Revenue/User'] = partner_table['Revenue/User'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(
            partner_table,
            column_config={
                "Status": st.column_config.TextColumn(
                    help="Partner account status"
                ),
                "Revenue": st.column_config.TextColumn(
                    help=f"Revenue generated in last {days} days"
                )
            },
            use_container_width=True
        )
        
        # Partner type analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Partner Type Distribution")
            
            type_summary = partner_data['overview'].groupby('partner_type').agg({
                'total_users': 'sum',
                'total_revenue': 'sum',
                'partner_id': 'count'
            }).reset_index()
            
            type_summary.columns = ['Partner Type', 'Total Users', 'Total Revenue', 'Count']
            
            fig = px.pie(type_summary, 
                        values='Count', names='Partner Type',
                        title='Partners by Type')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💰 Revenue by Partner Type")
            
            fig = px.bar(type_summary, 
                        x='Partner Type', y='Total Revenue',
                        title='Revenue Distribution by Partner Type',
                        color='Total Revenue',
                        color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)
        
        # Feature usage heatmap
        if not partner_data['feature_usage'].empty:
            st.subheader("🎯 Feature Usage Heatmap")
            
            # Pivot feature usage data
            feature_pivot = partner_data['feature_usage'].pivot_table(
                index='partner_id', 
                columns='feature_name', 
                values='total_usage',
                fill_value=0
            )
            
            if not feature_pivot.empty:
                fig = px.imshow(
                    feature_pivot.values,
                    x=feature_pivot.columns,
                    y=feature_pivot.index,
                    aspect='auto',
                    title='Feature Usage by Partner',
                    color_continuous_scale='Blues'
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Sync health by partner
        if not partner_data['sync_health'].empty:
            st.subheader("🔄 Partner Sync Health")
            
            # Calculate sync success rate
            partner_data['sync_health']['success_rate'] = (
                partner_data['sync_health']['successful_syncs'] / 
                partner_data['sync_health']['total_syncs'] * 100
            )
            
            # Merge with partner names
            sync_health_display = partner_data['sync_health'].merge(
                partner_data['overview'][['partner_id', 'partner_name']], 
                on='partner_id', 
                how='left'
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(sync_health_display, 
                           x='partner_name', y='success_rate',
                           title='Sync Success Rate by Partner',
                           color='success_rate',
                           color_continuous_scale='RdYlGn',
                           range_color=[0, 100])
                
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.scatter(sync_health_display, 
                               x='total_syncs', y='avg_duration',
                               size='successful_syncs',
                               hover_data=['partner_name'],
                               title='Sync Volume vs Performance',
                               labels={'total_syncs': 'Total Syncs', 
                                      'avg_duration': 'Avg Duration (s)'})
                st.plotly_chart(fig, use_container_width=True)
            
            # Sync health details table
            st.write("**Sync Health Details**")
            sync_display = sync_health_display[['partner_name', 'total_syncs', 'successful_syncs', 
                                              'failed_syncs', 'success_rate', 'avg_duration']]
            sync_display.columns = ['Partner', 'Total', 'Success', 'Failed', 'Success Rate %', 'Avg Duration (s)']
            sync_display['Success Rate %'] = sync_display['Success Rate %'].round(1)
            sync_display['Avg Duration (s)'] = sync_display['Avg Duration (s)'].round(2)
            
            st.dataframe(sync_display, use_container_width=True)

# Global admin dashboard instance
admin_dashboard = AdminDashboard()

def render_admin_monitoring_dashboard():
    """Main entry point for admin dashboard."""
    admin_dashboard.render_admin_dashboard(st.session_state.get('current_user', {}))

if __name__ == "__main__":
    render_admin_monitoring_dashboard()
