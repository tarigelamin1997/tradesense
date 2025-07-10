
import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import hashlib
import uuid
from logging_manager import log_info, log_warning, LogCategory
from notification_system import create_system_alert, NotificationType, NotificationPriority

class BugSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"

class BugStatus(Enum):
    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    WONT_FIX = "wont_fix"
    DUPLICATE = "duplicate"
    INVALID = "invalid"

class BugBountyManager:
    """Manage bug bounty program and external security reviews."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.reward_schedule = {
            BugSeverity.CRITICAL: 500,
            BugSeverity.HIGH: 250,
            BugSeverity.MEDIUM: 100,
            BugSeverity.LOW: 50,
            BugSeverity.INFORMATIONAL: 25
        }
        self._init_database()
    
    def _init_database(self):
        """Initialize bug bounty database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bug_reports (
                id TEXT PRIMARY KEY,
                reporter_email TEXT NOT NULL,
                reporter_name TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'submitted',
                category TEXT,
                reproduction_steps TEXT,
                proof_of_concept TEXT,
                affected_urls TEXT,
                browser_info TEXT,
                reward_amount INTEGER DEFAULT 0,
                reward_paid BOOLEAN DEFAULT FALSE,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                triaged_at TIMESTAMP,
                resolved_at TIMESTAMP,
                triage_notes TEXT,
                resolution_notes TEXT,
                duplicate_of TEXT,
                security_impact TEXT,
                business_impact TEXT,
                cvss_score REAL,
                cve_id TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bounty_hunters (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                total_reports INTEGER DEFAULT 0,
                valid_reports INTEGER DEFAULT 0,
                total_rewards INTEGER DEFAULT 0,
                reputation_score INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_report_at TIMESTAMP,
                verification_status TEXT DEFAULT 'unverified',
                payment_method TEXT,
                payment_details TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS external_reviews (
                id TEXT PRIMARY KEY,
                review_type TEXT NOT NULL,
                provider_name TEXT NOT NULL,
                provider_contact TEXT,
                scope TEXT,
                start_date DATE,
                end_date DATE,
                status TEXT NOT NULL,
                report_url TEXT,
                findings_count INTEGER DEFAULT 0,
                critical_findings INTEGER DEFAULT 0,
                high_findings INTEGER DEFAULT 0,
                medium_findings INTEGER DEFAULT 0,
                low_findings INTEGER DEFAULT 0,
                overall_rating TEXT,
                cost REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def submit_bug_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new bug report."""
        report_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert bug report
            cursor.execute('''
                INSERT INTO bug_reports (
                    id, reporter_email, reporter_name, title, description,
                    severity, category, reproduction_steps, proof_of_concept,
                    affected_urls, browser_info, security_impact, business_impact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                report_data['reporter_email'],
                report_data.get('reporter_name', ''),
                report_data['title'],
                report_data['description'],
                report_data['severity'],
                report_data.get('category', ''),
                report_data.get('reproduction_steps', ''),
                report_data.get('proof_of_concept', ''),
                report_data.get('affected_urls', ''),
                report_data.get('browser_info', ''),
                report_data.get('security_impact', ''),
                report_data.get('business_impact', '')
            ))
            
            # Update or create bounty hunter record
            cursor.execute('''
                INSERT OR REPLACE INTO bounty_hunters (
                    email, name, total_reports, last_report_at
                ) VALUES (
                    ?, ?, 
                    COALESCE((SELECT total_reports FROM bounty_hunters WHERE email = ?), 0) + 1,
                    CURRENT_TIMESTAMP
                )
            ''', (report_data['reporter_email'], report_data.get('reporter_name', ''), report_data['reporter_email']))
            
            conn.commit()
            
            # Send notification
            create_system_alert(
                title=f"🐛 New Bug Report: {report_data['title']}",
                message=f"Severity: {report_data['severity']} | Reporter: {report_data['reporter_email']}",
                notification_type=NotificationType.WARNING,
                priority=NotificationPriority.HIGH if report_data['severity'] in ['critical', 'high'] else NotificationPriority.MEDIUM
            )
            
            # Log bug report
            log_info(
                f"Bug report submitted: {report_id}",
                details={
                    'reporter': report_data['reporter_email'],
                    'severity': report_data['severity'],
                    'title': report_data['title']
                },
                category=LogCategory.SYSTEM_ERROR
            )
            
            return {
                'success': True,
                'report_id': report_id,
                'message': 'Bug report submitted successfully'
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def triage_bug_report(self, report_id: str, triage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Triage a bug report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update bug report
            cursor.execute('''
                UPDATE bug_reports 
                SET status = ?, severity = ?, triage_notes = ?, triaged_at = CURRENT_TIMESTAMP,
                    cvss_score = ?, reward_amount = ?
                WHERE id = ?
            ''', (
                triage_data['status'],
                triage_data.get('severity'),
                triage_data.get('triage_notes', ''),
                triage_data.get('cvss_score'),
                triage_data.get('reward_amount', 0),
                report_id
            ))
            
            # If confirmed, update bounty hunter reputation
            if triage_data['status'] == 'confirmed':
                cursor.execute('''
                    SELECT reporter_email FROM bug_reports WHERE id = ?
                ''', (report_id,))
                
                reporter_email = cursor.fetchone()
                if reporter_email:
                    cursor.execute('''
                        UPDATE bounty_hunters 
                        SET valid_reports = valid_reports + 1,
                            reputation_score = reputation_score + ?,
                            total_rewards = total_rewards + ?
                        WHERE email = ?
                    ''', (
                        self._calculate_reputation_points(triage_data.get('severity', 'low')),
                        triage_data.get('reward_amount', 0),
                        reporter_email[0]
                    ))
            
            conn.commit()
            
            return {
                'success': True,
                'message': 'Bug report triaged successfully'
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def resolve_bug_report(self, report_id: str, resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a bug report as resolved."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE bug_reports 
                SET status = 'fixed', resolution_notes = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (resolution_data.get('resolution_notes', ''), report_id))
            
            # Award bounty if applicable
            if resolution_data.get('award_bounty', False):
                cursor.execute('''
                    UPDATE bug_reports 
                    SET reward_paid = TRUE
                    WHERE id = ?
                ''', (report_id,))
            
            conn.commit()
            
            return {
                'success': True,
                'message': 'Bug report resolved successfully'
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def get_bug_reports(self, status: Optional[str] = None, severity: Optional[str] = None) -> List[Dict]:
        """Get bug reports with optional filtering."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM bug_reports WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        query += " ORDER BY submitted_at DESC"
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        reports = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return reports
    
    def get_bounty_hunter_stats(self, email: Optional[str] = None) -> Dict[str, Any]:
        """Get bounty hunter statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if email:
            cursor.execute('''
                SELECT * FROM bounty_hunters WHERE email = ?
            ''', (email,))
            hunter = cursor.fetchone()
            
            if hunter:
                columns = [desc[0] for desc in cursor.description]
                hunter_data = dict(zip(columns, hunter))
                
                # Get recent reports
                cursor.execute('''
                    SELECT id, title, severity, status, submitted_at, reward_amount
                    FROM bug_reports 
                    WHERE reporter_email = ?
                    ORDER BY submitted_at DESC
                    LIMIT 10
                ''', (email,))
                
                reports_columns = [desc[0] for desc in cursor.description]
                recent_reports = [dict(zip(reports_columns, row)) for row in cursor.fetchall()]
                
                hunter_data['recent_reports'] = recent_reports
                
                conn.close()
                return hunter_data
        else:
            # Get overall stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_hunters,
                    SUM(total_reports) as total_reports,
                    SUM(valid_reports) as valid_reports,
                    SUM(total_rewards) as total_rewards_paid,
                    AVG(reputation_score) as avg_reputation
                FROM bounty_hunters
            ''')
            
            stats = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            
            conn.close()
            return dict(zip(columns, stats)) if stats else {}
    
    def schedule_external_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule an external security review."""
        review_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO external_reviews (
                    id, review_type, provider_name, provider_contact,
                    scope, start_date, end_date, status, cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                review_id,
                review_data['review_type'],
                review_data['provider_name'],
                review_data['provider_contact'],
                review_data['scope'],
                review_data['start_date'],
                review_data['end_date'],
                'scheduled',
                review_data.get('cost', 0)
            ))
            
            conn.commit()
            
            return {
                'success': True,
                'review_id': review_id,
                'message': 'External review scheduled successfully'
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def _calculate_reputation_points(self, severity: str) -> int:
        """Calculate reputation points based on bug severity."""
        points_map = {
            'critical': 50,
            'high': 30,
            'medium': 20,
            'low': 10,
            'informational': 5
        }
        return points_map.get(severity, 5)

def render_bug_bounty_portal():
    """Render bug bounty portal interface."""
    st.header("🐛 Bug Bounty Program")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Submit Bug", "Bug Reports", "Bounty Hunters", "External Reviews"])
    
    bounty_manager = BugBountyManager()
    
    with tab1:
        st.subheader("🎯 Submit a Bug Report")
        
        with st.form("bug_submission"):
            col1, col2 = st.columns(2)
            
            with col1:
                reporter_email = st.text_input("Email*", placeholder="your@email.com")
                reporter_name = st.text_input("Name", placeholder="Your Name")
                title = st.text_input("Bug Title*", placeholder="Brief description of the issue")
                severity = st.selectbox("Severity*", ["low", "medium", "high", "critical"])
                category = st.selectbox("Category", [
                    "Authentication", "Authorization", "SQL Injection", "XSS", 
                    "CSRF", "Data Exposure", "Business Logic", "Other"
                ])
            
            with col2:
                affected_urls = st.text_area("Affected URLs", placeholder="List affected pages/endpoints")
                browser_info = st.text_input("Browser/Environment", placeholder="Chrome 96, Windows 10")
                security_impact = st.text_area("Security Impact", placeholder="What could an attacker do?")
                business_impact = st.text_area("Business Impact", placeholder="How does this affect the business?")
            
            description = st.text_area("Detailed Description*", placeholder="Describe the vulnerability in detail")
            reproduction_steps = st.text_area("Reproduction Steps", placeholder="1. Go to...\n2. Click on...\n3. Observe...")
            proof_of_concept = st.text_area("Proof of Concept", placeholder="Code, screenshots, or demonstration")
            
            submitted = st.form_submit_button("🚀 Submit Bug Report", type="primary")
            
            if submitted:
                if not all([reporter_email, title, description, severity]):
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    report_data = {
                        'reporter_email': reporter_email,
                        'reporter_name': reporter_name,
                        'title': title,
                        'description': description,
                        'severity': severity,
                        'category': category,
                        'reproduction_steps': reproduction_steps,
                        'proof_of_concept': proof_of_concept,
                        'affected_urls': affected_urls,
                        'browser_info': browser_info,
                        'security_impact': security_impact,
                        'business_impact': business_impact
                    }
                    
                    result = bounty_manager.submit_bug_report(report_data)
                    
                    if result['success']:
                        st.success(f"✅ Bug report submitted! ID: {result['report_id']}")
                        st.info("💰 Reward will be determined after triage and validation")
                    else:
                        st.error(f"❌ Error submitting report: {result['error']}")
    
    with tab2:
        st.subheader("📋 Bug Reports Dashboard")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("Filter by Status", 
                ["All", "submitted", "triaged", "confirmed", "in_progress", "fixed"])
        
        with col2:
            severity_filter = st.selectbox("Filter by Severity", 
                ["All", "critical", "high", "medium", "low", "informational"])
        
        reports = bounty_manager.get_bug_reports(
            status=None if status_filter == "All" else status_filter,
            severity=None if severity_filter == "All" else severity_filter
        )
        
        if reports:
            for report in reports:
                with st.expander(f"🐛 {report['title']} | {report['severity'].upper()} | {report['status']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Reporter:** {report['reporter_email']}")
                        st.write(f"**Submitted:** {report['submitted_at']}")
                        st.write(f"**Category:** {report['category']}")
                        st.write(f"**Reward:** ${report['reward_amount']}")
                    
                    with col2:
                        st.write(f"**Security Impact:** {report['security_impact']}")
                        st.write(f"**Business Impact:** {report['business_impact']}")
                    
                    st.write("**Description:**")
                    st.write(report['description'])
                    
                    if report['reproduction_steps']:
                        st.write("**Reproduction Steps:**")
                        st.code(report['reproduction_steps'])
        else:
            st.info("No bug reports found matching the selected filters.")
    
    with tab3:
        st.subheader("🏆 Bounty Hunter Leaderboard")
        
        stats = bounty_manager.get_bounty_hunter_stats()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Hunters", stats.get('total_hunters', 0))
            
            with col2:
                st.metric("Total Reports", stats.get('total_reports', 0))
            
            with col3:
                st.metric("Valid Reports", stats.get('valid_reports', 0))
            
            with col4:
                st.metric("Rewards Paid", f"${stats.get('total_rewards_paid', 0)}")
        
        # Individual hunter lookup
        st.write("**Look up individual hunter:**")
        hunter_email = st.text_input("Hunter Email")
        
        if hunter_email and st.button("Look Up"):
            hunter_data = bounty_manager.get_bounty_hunter_stats(hunter_email)
            
            if hunter_data:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Reports", hunter_data['total_reports'])
                
                with col2:
                    st.metric("Valid Reports", hunter_data['valid_reports'])
                
                with col3:
                    st.metric("Total Rewards", f"${hunter_data['total_rewards']}")
                
                st.metric("Reputation Score", hunter_data['reputation_score'])
                
                if hunter_data.get('recent_reports'):
                    st.write("**Recent Reports:**")
                    for report in hunter_data['recent_reports']:
                        st.write(f"• {report['title']} ({report['severity']}) - ${report['reward_amount']}")
            else:
                st.warning("Hunter not found")
    
    with tab4:
        st.subheader("🔍 External Security Reviews")
        
        with st.form("schedule_review"):
            st.write("**Schedule New Review:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                review_type = st.selectbox("Review Type", 
                    ["Penetration Testing", "Code Review", "Infrastructure Audit", "Compliance Assessment"])
                provider_name = st.text_input("Provider Name")
                provider_contact = st.text_input("Provider Contact")
            
            with col2:
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
                cost = st.number_input("Estimated Cost ($)", min_value=0)
            
            scope = st.text_area("Review Scope", placeholder="Describe what will be reviewed...")
            
            if st.form_submit_button("📅 Schedule Review"):
                review_data = {
                    'review_type': review_type,
                    'provider_name': provider_name,
                    'provider_contact': provider_contact,
                    'scope': scope,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'cost': cost
                }
                
                result = bounty_manager.schedule_external_review(review_data)
                
                if result['success']:
                    st.success(f"✅ Review scheduled! ID: {result['review_id']}")
                else:
                    st.error(f"❌ Error scheduling review: {result['error']}")

if __name__ == "__main__":
    render_bug_bounty_portal()
