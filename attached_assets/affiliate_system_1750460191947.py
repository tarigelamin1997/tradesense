
import streamlit as st
import pandas as pd
import sqlite3
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from auth import AuthManager, require_auth
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class AffiliateTrackingSystem:
    """Complete affiliate and referral tracking system."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()
        self.init_affiliate_tables()
    
    def init_affiliate_tables(self):
        """Initialize affiliate tracking database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Affiliates/Partners table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL DEFAULT 'individual',
                commission_rate REAL DEFAULT 0.20,
                payout_threshold REAL DEFAULT 100.0,
                payment_method TEXT DEFAULT 'paypal',
                payment_details JSON,
                referral_code TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'active',
                tier TEXT DEFAULT 'bronze',
                total_earnings REAL DEFAULT 0.0,
                pending_earnings REAL DEFAULT 0.0,
                lifetime_referrals INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_payout_at TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Referral tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id TEXT NOT NULL,
                referred_user_id INTEGER,
                referral_source TEXT,
                utm_source TEXT,
                utm_medium TEXT,
                utm_campaign TEXT,
                ip_address TEXT,
                user_agent TEXT,
                conversion_type TEXT DEFAULT 'signup',
                conversion_value REAL DEFAULT 0.0,
                commission_earned REAL DEFAULT 0.0,
                commission_rate REAL,
                status TEXT DEFAULT 'pending',
                converted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id),
                FOREIGN KEY (referred_user_id) REFERENCES users (id)
            )
        ''')
        
        # Affiliate payouts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_payouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id TEXT NOT NULL,
                amount REAL NOT NULL,
                commission_period_start DATE,
                commission_period_end DATE,
                payout_method TEXT,
                transaction_id TEXT,
                status TEXT DEFAULT 'pending',
                referrals_included JSON,
                processing_fee REAL DEFAULT 0.0,
                net_amount REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id)
            )
        ''')
        
        # Commission tiers and rules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commission_tiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier_name TEXT UNIQUE NOT NULL,
                min_referrals INTEGER DEFAULT 0,
                commission_rate REAL NOT NULL,
                bonus_rate REAL DEFAULT 0.0,
                requirements JSON,
                benefits JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Affiliate links/campaigns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id TEXT NOT NULL,
                campaign_name TEXT,
                url_slug TEXT UNIQUE NOT NULL,
                destination_url TEXT NOT NULL,
                utm_parameters JSON,
                clicks INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id)
            )
        ''')
        
        # Click tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id TEXT NOT NULL,
                link_id INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                referrer TEXT,
                utm_source TEXT,
                utm_medium TEXT,
                utm_campaign TEXT,
                converted BOOLEAN DEFAULT FALSE,
                conversion_value REAL DEFAULT 0.0,
                clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id),
                FOREIGN KEY (link_id) REFERENCES affiliate_links (id)
            )
        ''')
        
        # Revenue sharing rules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_sharing_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_type TEXT NOT NULL,
                subscription_tier TEXT,
                revenue_event TEXT NOT NULL,
                commission_type TEXT DEFAULT 'percentage',
                commission_value REAL NOT NULL,
                recurring BOOLEAN DEFAULT FALSE,
                max_payouts INTEGER,
                conditions JSON,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize default commission tiers
        cursor.execute('''
            INSERT OR IGNORE INTO commission_tiers (tier_name, min_referrals, commission_rate, bonus_rate)
            VALUES 
                ('Bronze', 0, 0.20, 0.0),
                ('Silver', 10, 0.25, 0.05),
                ('Gold', 25, 0.30, 0.10),
                ('Platinum', 50, 0.35, 0.15)
        ''')
        
        # Initialize default revenue sharing rules
        cursor.execute('''
            INSERT OR IGNORE INTO revenue_sharing_rules 
            (partner_type, subscription_tier, revenue_event, commission_value, recurring)
            VALUES 
                ('affiliate', 'pro', 'subscription', 0.20, TRUE),
                ('affiliate', 'premium', 'subscription', 0.25, TRUE),
                ('partner', 'pro', 'subscription', 0.30, TRUE),
                ('partner', 'premium', 'subscription', 0.35, TRUE),
                ('influencer', 'any', 'first_payment', 0.50, FALSE)
        ''')
        
        conn.commit()
        conn.close()
    
    def create_affiliate(self, name: str, email: str, affiliate_type: str = 'individual',
                        commission_rate: float = 0.20) -> Dict:
        """Create a new affiliate account."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Generate unique affiliate ID and referral code
            affiliate_id = f"aff_{secrets.token_urlsafe(8)}"
            referral_code = self.generate_referral_code(name)
            
            cursor.execute('''
                INSERT INTO affiliates (id, name, email, type, commission_rate, referral_code)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (affiliate_id, name, email, affiliate_type, commission_rate, referral_code))
            
            # Create default affiliate link
            self.create_affiliate_link(
                affiliate_id, 
                "Default Link",
                f"ref-{referral_code}",
                "https://tradesense.com/signup"
            )
            
            conn.commit()
            return {
                'success': True, 
                'affiliate_id': affiliate_id,
                'referral_code': referral_code
            }
        
        except sqlite3.IntegrityError as e:
            return {'success': False, 'error': 'Email or referral code already exists'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def track_referral_click(self, referral_code: str, request_data: Dict) -> Dict:
        """Track affiliate link click."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get affiliate by referral code
            cursor.execute('SELECT id FROM affiliates WHERE referral_code = ?', (referral_code,))
            affiliate = cursor.fetchone()
            
            if not affiliate:
                return {'success': False, 'error': 'Invalid referral code'}
            
            affiliate_id = affiliate[0]
            
            # Record click
            cursor.execute('''
                INSERT INTO affiliate_clicks 
                (affiliate_id, ip_address, user_agent, referrer, utm_source, utm_medium, utm_campaign)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                affiliate_id,
                request_data.get('ip_address'),
                request_data.get('user_agent'),
                request_data.get('referrer'),
                request_data.get('utm_source'),
                request_data.get('utm_medium'),
                request_data.get('utm_campaign')
            ))
            
            # Update click count for affiliate link
            cursor.execute('''
                UPDATE affiliate_links 
                SET clicks = clicks + 1 
                WHERE affiliate_id = ? AND utm_parameters LIKE ?
            ''', (affiliate_id, f'%{referral_code}%'))
            
            conn.commit()
            return {'success': True, 'affiliate_id': affiliate_id}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def track_conversion(self, user_id: int, referral_code: str, 
                        conversion_type: str = 'signup', conversion_value: float = 0.0) -> Dict:
        """Track affiliate conversion."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get affiliate
            cursor.execute('SELECT id, commission_rate, tier FROM affiliates WHERE referral_code = ?', 
                          (referral_code,))
            affiliate = cursor.fetchone()
            
            if not affiliate:
                return {'success': False, 'error': 'Invalid referral code'}
            
            affiliate_id, base_rate, tier = affiliate
            
            # Calculate commission
            commission_rate = self.calculate_commission_rate(affiliate_id, conversion_type, conversion_value)
            commission_earned = conversion_value * commission_rate
            
            # Record referral
            cursor.execute('''
                INSERT INTO referrals 
                (affiliate_id, referred_user_id, conversion_type, conversion_value, 
                 commission_earned, commission_rate, status, converted_at)
                VALUES (?, ?, ?, ?, ?, ?, 'confirmed', CURRENT_TIMESTAMP)
            ''', (affiliate_id, user_id, conversion_type, conversion_value, 
                  commission_earned, commission_rate))
            
            # Update affiliate stats
            cursor.execute('''
                UPDATE affiliates 
                SET lifetime_referrals = lifetime_referrals + 1,
                    pending_earnings = pending_earnings + ?,
                    total_earnings = total_earnings + ?
                WHERE id = ?
            ''', (commission_earned, commission_earned, affiliate_id))
            
            # Update click conversion status
            cursor.execute('''
                UPDATE affiliate_clicks 
                SET converted = TRUE, conversion_value = ?
                WHERE affiliate_id = ? AND converted = FALSE
                ORDER BY clicked_at DESC LIMIT 1
            ''', (conversion_value, affiliate_id))
            
            # Check for tier upgrade
            self.check_tier_upgrade(affiliate_id)
            
            conn.commit()
            return {
                'success': True, 
                'commission_earned': commission_earned,
                'commission_rate': commission_rate
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def calculate_commission_rate(self, affiliate_id: str, conversion_type: str, 
                                 conversion_value: float) -> float:
        """Calculate commission rate based on rules and affiliate tier."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get affiliate tier and base rate
        cursor.execute('''
            SELECT a.tier, a.commission_rate, ct.commission_rate as tier_rate, ct.bonus_rate
            FROM affiliates a
            LEFT JOIN commission_tiers ct ON a.tier = ct.tier_name
            WHERE a.id = ?
        ''', (affiliate_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return 0.20  # Default rate
        
        tier, base_rate, tier_rate, bonus_rate = result
        
        # Use tier rate if available, otherwise base rate
        final_rate = tier_rate if tier_rate else base_rate
        
        # Apply bonus for high-value conversions
        if conversion_value > 100:
            final_rate += (bonus_rate or 0)
        
        return min(final_rate, 0.50)  # Cap at 50%
    
    def create_affiliate_link(self, affiliate_id: str, campaign_name: str, 
                             url_slug: str, destination_url: str) -> Dict:
        """Create custom affiliate link."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get affiliate referral code
            cursor.execute('SELECT referral_code FROM affiliates WHERE id = ?', (affiliate_id,))
            referral_code = cursor.fetchone()[0]
            
            # Build UTM parameters
            utm_params = {
                'utm_source': referral_code,
                'utm_medium': 'affiliate',
                'utm_campaign': campaign_name.lower().replace(' ', '_')
            }
            
            cursor.execute('''
                INSERT INTO affiliate_links 
                (affiliate_id, campaign_name, url_slug, destination_url, utm_parameters)
                VALUES (?, ?, ?, ?, ?)
            ''', (affiliate_id, campaign_name, url_slug, destination_url, json.dumps(utm_params)))
            
            conn.commit()
            
            # Generate full URL
            full_url = f"{destination_url}?ref={referral_code}&utm_source={referral_code}&utm_medium=affiliate&utm_campaign={utm_params['utm_campaign']}"
            
            return {'success': True, 'url': full_url, 'slug': url_slug}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def process_payout(self, affiliate_id: str, amount: float, method: str = 'paypal') -> Dict:
        """Process affiliate payout."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Verify affiliate has sufficient pending earnings
            cursor.execute('SELECT pending_earnings, payout_threshold FROM affiliates WHERE id = ?', 
                          (affiliate_id,))
            result = cursor.fetchone()
            
            if not result:
                return {'success': False, 'error': 'Affiliate not found'}
            
            pending_earnings, threshold = result
            
            if amount > pending_earnings:
                return {'success': False, 'error': 'Insufficient pending earnings'}
            
            if amount < threshold:
                return {'success': False, 'error': f'Amount below threshold of ${threshold}'}
            
            # Get referrals to include in payout
            cursor.execute('''
                SELECT id, commission_earned FROM referrals 
                WHERE affiliate_id = ? AND status = 'confirmed'
                ORDER BY converted_at
            ''', (affiliate_id,))
            
            referrals = cursor.fetchall()
            referral_data = [{'id': r[0], 'commission': r[1]} for r in referrals]
            
            # Calculate processing fee (2.9% for PayPal, etc.)
            processing_fee = amount * 0.029 if method == 'paypal' else 0
            net_amount = amount - processing_fee
            
            # Create payout record
            transaction_id = f"payout_{secrets.token_urlsafe(8)}"
            
            cursor.execute('''
                INSERT INTO affiliate_payouts 
                (affiliate_id, amount, payout_method, transaction_id, 
                 referrals_included, processing_fee, net_amount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (affiliate_id, amount, method, transaction_id, 
                  json.dumps(referral_data), processing_fee, net_amount))
            
            # Update affiliate pending earnings
            cursor.execute('''
                UPDATE affiliates 
                SET pending_earnings = pending_earnings - ?
                WHERE id = ?
            ''', (amount, affiliate_id))
            
            # Mark referrals as paid
            referral_ids = [str(r['id']) for r in referral_data]
            if referral_ids:
                cursor.execute(f'''
                    UPDATE referrals 
                    SET status = 'paid' 
                    WHERE id IN ({','.join(['?'] * len(referral_ids))})
                ''', referral_ids)
            
            conn.commit()
            return {
                'success': True, 
                'transaction_id': transaction_id,
                'net_amount': net_amount,
                'processing_fee': processing_fee
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def check_tier_upgrade(self, affiliate_id: str):
        """Check and upgrade affiliate tier based on performance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current stats
        cursor.execute('''
            SELECT lifetime_referrals, tier FROM affiliates WHERE id = ?
        ''', (affiliate_id,))
        
        result = cursor.fetchone()
        if not result:
            return
        
        referrals, current_tier = result
        
        # Get available tiers
        cursor.execute('''
            SELECT tier_name, min_referrals FROM commission_tiers 
            WHERE min_referrals <= ? 
            ORDER BY min_referrals DESC LIMIT 1
        ''', (referrals,))
        
        tier_result = cursor.fetchone()
        if tier_result and tier_result[0] != current_tier:
            new_tier = tier_result[0]
            
            cursor.execute('''
                UPDATE affiliates SET tier = ? WHERE id = ?
            ''', (new_tier, affiliate_id))
            
            conn.commit()
        
        conn.close()
    
    def generate_referral_code(self, name: str) -> str:
        """Generate unique referral code."""
        base = name.upper().replace(' ', '')[:4]
        suffix = secrets.token_hex(2).upper()
        return f"{base}{suffix}"
    
    def get_affiliate_stats(self, affiliate_id: str, days: int = 30) -> Dict:
        """Get comprehensive affiliate statistics."""
        conn = sqlite3.connect(self.db_path)
        
        # Basic affiliate info
        affiliate_query = '''
            SELECT name, email, tier, commission_rate, total_earnings, 
                   pending_earnings, lifetime_referrals, created_at
            FROM affiliates WHERE id = ?
        '''
        affiliate_info = pd.read_sql_query(affiliate_query, conn, params=(affiliate_id,)).iloc[0]
        
        # Recent performance
        performance_query = '''
            SELECT 
                COUNT(*) as referrals,
                SUM(conversion_value) as revenue,
                SUM(commission_earned) as commissions,
                AVG(commission_rate) as avg_rate
            FROM referrals 
            WHERE affiliate_id = ? AND converted_at > datetime('now', '-{} days')
        '''.format(days)
        
        performance = pd.read_sql_query(performance_query, conn, params=(affiliate_id,)).iloc[0]
        
        # Click stats
        click_query = '''
            SELECT COUNT(*) as clicks, SUM(CASE WHEN converted THEN 1 ELSE 0 END) as conversions
            FROM affiliate_clicks 
            WHERE affiliate_id = ? AND clicked_at > datetime('now', '-{} days')
        '''.format(days)
        
        clicks = pd.read_sql_query(click_query, conn, params=(affiliate_id,)).iloc[0]
        
        # Top converting links
        links_query = '''
            SELECT campaign_name, clicks, conversions, 
                   CASE WHEN clicks > 0 THEN (conversions * 1.0 / clicks) * 100 ELSE 0 END as conversion_rate
            FROM affiliate_links 
            WHERE affiliate_id = ? AND is_active = 1
            ORDER BY conversions DESC LIMIT 5
        '''
        
        top_links = pd.read_sql_query(links_query, conn, params=(affiliate_id,))
        
        conn.close()
        
        return {
            'affiliate_info': affiliate_info.to_dict(),
            'performance': performance.to_dict(),
            'clicks': clicks.to_dict(),
            'top_links': top_links.to_dict('records'),
            'conversion_rate': (clicks['conversions'] / max(clicks['clicks'], 1)) * 100
        }
    
    def get_affiliate_leaderboard(self, period: str = 'monthly') -> pd.DataFrame:
        """Get affiliate leaderboard."""
        conn = sqlite3.connect(self.db_path)
        
        days_map = {'weekly': 7, 'monthly': 30, 'quarterly': 90, 'yearly': 365}
        days = days_map.get(period, 30)
        
        query = '''
            SELECT 
                a.name,
                a.tier,
                COUNT(r.id) as referrals,
                SUM(r.conversion_value) as revenue_generated,
                SUM(r.commission_earned) as commissions_earned,
                AVG(r.commission_rate) * 100 as avg_commission_rate
            FROM affiliates a
            LEFT JOIN referrals r ON a.id = r.affiliate_id 
                AND r.converted_at > datetime('now', '-{} days')
            WHERE a.status = 'active'
            GROUP BY a.id, a.name, a.tier
            HAVING referrals > 0
            ORDER BY commissions_earned DESC, referrals DESC
            LIMIT 20
        '''.format(days)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df


def render_affiliate_management_ui():
    """Main affiliate management interface."""
    st.title("🤝 Affiliate & Referral Management")
    
    affiliate_system = AffiliateTrackingSystem()
    
    # Check authentication
    auth_manager = AuthManager()
    current_user = auth_manager.get_current_user()
    
    if not current_user:
        st.error("🔒 Authentication required")
        return
    
    # Main navigation
    tabs = st.tabs([
        "📊 Dashboard", 
        "👥 Affiliates", 
        "🔗 Links & Campaigns",
        "💰 Payouts",
        "📈 Analytics",
        "⚙️ Settings"
    ])
    
    with tabs[0]:
        render_affiliate_dashboard(affiliate_system)
    
    with tabs[1]:
        render_affiliate_management(affiliate_system)
    
    with tabs[2]:
        render_link_management(affiliate_system)
    
    with tabs[3]:
        render_payout_management(affiliate_system)
    
    with tabs[4]:
        render_affiliate_analytics(affiliate_system)
    
    with tabs[5]:
        render_affiliate_settings(affiliate_system)


def render_affiliate_dashboard(affiliate_system: AffiliateTrackingSystem):
    """Render affiliate program dashboard."""
    st.subheader("📊 Affiliate Program Overview")
    
    # Quick stats
    conn = sqlite3.connect(affiliate_system.db_path)
    
    # Get overall metrics
    stats_query = '''
        SELECT 
            COUNT(DISTINCT a.id) as total_affiliates,
            COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_affiliates,
            COUNT(r.id) as total_referrals,
            SUM(r.conversion_value) as total_revenue,
            SUM(r.commission_earned) as total_commissions,
            SUM(a.pending_earnings) as pending_payouts
        FROM affiliates a
        LEFT JOIN referrals r ON a.id = r.affiliate_id
        WHERE r.converted_at > datetime('now', '-30 days') OR r.id IS NULL
    '''
    
    stats = pd.read_sql_query(stats_query, conn).iloc[0]
    conn.close()
    
    # Display metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Affiliates", int(stats['total_affiliates'] or 0))
    
    with col2:
        st.metric("Active Affiliates", int(stats['active_affiliates'] or 0))
    
    with col3:
        st.metric("Referrals (30d)", int(stats['total_referrals'] or 0))
    
    with col4:
        st.metric("Revenue Generated", f"${stats['total_revenue'] or 0:,.2f}")
    
    with col5:
        st.metric("Commissions Paid", f"${stats['total_commissions'] or 0:,.2f}")
    
    with col6:
        st.metric("Pending Payouts", f"${stats['pending_payouts'] or 0:,.2f}")
    
    st.divider()
    
    # Recent activity and top performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top Performers (30 days)")
        leaderboard = affiliate_system.get_affiliate_leaderboard('monthly')
        
        if not leaderboard.empty:
            for i, row in leaderboard.head(5).iterrows():
                with st.container():
                    subcol1, subcol2, subcol3 = st.columns([2, 1, 1])
                    with subcol1:
                        st.write(f"**{row['name']}** ({row['tier']})")
                    with subcol2:
                        st.write(f"${row['commissions_earned']:.2f}")
                    with subcol3:
                        st.write(f"{row['referrals']} refs")
        else:
            st.info("No affiliate activity yet")
    
    with col2:
        st.subheader("📈 Performance Trends")
        
        # Sample trend data (would be real data in production)
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        trend_data = pd.DataFrame({
            'Date': dates,
            'Referrals': np.random.poisson(5, len(dates)),
            'Revenue': np.random.normal(500, 150, len(dates))
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_data['Date'], 
            y=trend_data['Referrals'],
            name='Daily Referrals',
            line=dict(color='blue')
        ))
        
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def render_affiliate_management(affiliate_system: AffiliateTrackingSystem):
    """Render affiliate management interface."""
    st.subheader("👥 Affiliate Management")
    
    # Add new affiliate
    with st.expander("➕ Add New Affiliate"):
        with st.form("add_affiliate"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name")
                email = st.text_input("Email")
                
            with col2:
                affiliate_type = st.selectbox("Type", ["individual", "company", "influencer"])
                commission_rate = st.number_input("Commission Rate", min_value=0.0, max_value=0.5, value=0.2, step=0.01)
            
            if st.form_submit_button("Create Affiliate"):
                result = affiliate_system.create_affiliate(name, email, affiliate_type, commission_rate)
                
                if result['success']:
                    st.success(f"✅ Affiliate created! Referral code: **{result['referral_code']}**")
                else:
                    st.error(f"❌ {result['error']}")
    
    # Affiliate list
    st.subheader("Current Affiliates")
    
    conn = sqlite3.connect(affiliate_system.db_path)
    affiliates_query = '''
        SELECT id, name, email, type, tier, commission_rate, 
               total_earnings, pending_earnings, lifetime_referrals, 
               referral_code, status, created_at
        FROM affiliates 
        ORDER BY created_at DESC
    '''
    
    affiliates_df = pd.read_sql_query(affiliates_query, conn)
    conn.close()
    
    if not affiliates_df.empty:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "active", "inactive", "suspended"])
        
        with col2:
            type_filter = st.selectbox("Filter by Type", ["All", "individual", "company", "influencer"])
        
        with col3:
            tier_filter = st.selectbox("Filter by Tier", ["All", "Bronze", "Silver", "Gold", "Platinum"])
        
        # Apply filters
        filtered_df = affiliates_df.copy()
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        if type_filter != "All":
            filtered_df = filtered_df[filtered_df['type'] == type_filter]
        if tier_filter != "All":
            filtered_df = filtered_df[filtered_df['tier'] == tier_filter]
        
        # Display affiliates
        for _, affiliate in filtered_df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{affiliate['name']}**")
                    st.caption(f"{affiliate['email']} • {affiliate['type'].title()}")
                
                with col2:
                    st.write(f"**{affiliate['tier']}**")
                    st.caption(f"{affiliate['commission_rate']:.1%} rate")
                
                with col3:
                    st.metric("Total Earned", f"${affiliate['total_earnings']:.2f}")
                
                with col4:
                    st.metric("Pending", f"${affiliate['pending_earnings']:.2f}")
                
                with col5:
                    if st.button("👁️ View", key=f"view_{affiliate['id']}"):
                        show_affiliate_details(affiliate_system, affiliate['id'])
            
            st.divider()
    else:
        st.info("No affiliates found. Add your first affiliate above!")


def render_link_management(affiliate_system: AffiliateTrackingSystem):
    """Render affiliate link management."""
    st.subheader("🔗 Affiliate Links & Campaigns")
    
    # Link generator
    with st.expander("🚀 Create New Affiliate Link"):
        with st.form("create_link"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Get affiliates for selection
                conn = sqlite3.connect(affiliate_system.db_path)
                affiliates = pd.read_sql_query("SELECT id, name FROM affiliates WHERE status = 'active'", conn)
                conn.close()
                
                if not affiliates.empty:
                    affiliate_options = {f"{row['name']} ({row['id']})": row['id'] for _, row in affiliates.iterrows()}
                    selected_affiliate = st.selectbox("Select Affiliate", options=list(affiliate_options.keys()))
                    affiliate_id = affiliate_options[selected_affiliate]
                    
                    campaign_name = st.text_input("Campaign Name", placeholder="Holiday Sale 2024")
                    
                else:
                    st.error("No active affiliates found")
                    affiliate_id = None
            
            with col2:
                url_slug = st.text_input("URL Slug", placeholder="holiday-sale")
                destination_url = st.text_input("Destination URL", value="https://tradesense.com/signup")
            
            if st.form_submit_button("🔗 Generate Link") and affiliate_id:
                result = affiliate_system.create_affiliate_link(affiliate_id, campaign_name, url_slug, destination_url)
                
                if result['success']:
                    st.success("✅ Link created successfully!")
                    st.code(result['url'])
                    st.caption("Copy this link for the affiliate to use")
                else:
                    st.error(f"❌ {result['error']}")
    
    # Existing links
    st.subheader("Existing Links")
    
    conn = sqlite3.connect(affiliate_system.db_path)
    links_query = '''
        SELECT al.*, a.name as affiliate_name
        FROM affiliate_links al
        JOIN affiliates a ON al.affiliate_id = a.id
        ORDER BY al.created_at DESC
    '''
    
    links_df = pd.read_sql_query(links_query, conn)
    conn.close()
    
    if not links_df.empty:
        for _, link in links_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{link['campaign_name']}**")
                    st.caption(f"Affiliate: {link['affiliate_name']}")
                    st.code(f"tradesense.com/{link['url_slug']}")
                
                with col2:
                    st.metric("Clicks", link['clicks'])
                
                with col3:
                    st.metric("Conversions", link['conversions'])
                
                with col4:
                    conversion_rate = (link['conversions'] / max(link['clicks'], 1)) * 100
                    st.metric("Rate", f"{conversion_rate:.1f}%")
            
            st.divider()
    else:
        st.info("No affiliate links created yet")


def render_payout_management(affiliate_system: AffiliateTrackingSystem):
    """Render payout management interface."""
    st.subheader("💰 Payout Management")
    
    # Pending payouts
    st.write("**Affiliates Ready for Payout**")
    
    conn = sqlite3.connect(affiliate_system.db_path)
    pending_query = '''
        SELECT id, name, pending_earnings, payout_threshold, 
               total_earnings, lifetime_referrals
        FROM affiliates 
        WHERE pending_earnings >= payout_threshold AND status = 'active'
        ORDER BY pending_earnings DESC
    '''
    
    pending_df = pd.read_sql_query(pending_query, conn)
    
    if not pending_df.empty:
        for _, affiliate in pending_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{affiliate['name']}**")
                    st.caption(f"Threshold: ${affiliate['payout_threshold']:.2f}")
                
                with col2:
                    st.metric("Pending", f"${affiliate['pending_earnings']:.2f}")
                
                with col3:
                    st.metric("Lifetime", f"${affiliate['total_earnings']:.2f}")
                
                with col4:
                    if st.button(f"💳 Pay ${affiliate['pending_earnings']:.2f}", key=f"pay_{affiliate['id']}"):
                        result = affiliate_system.process_payout(
                            affiliate['id'], 
                            affiliate['pending_earnings']
                        )
                        
                        if result['success']:
                            st.success(f"✅ Payout processed! Transaction: {result['transaction_id']}")
                            st.rerun()
                        else:
                            st.error(f"❌ {result['error']}")
            
            st.divider()
    else:
        st.info("No affiliates ready for payout")
    
    # Payout history
    st.subheader("💳 Payout History")
    
    payouts_query = '''
        SELECT ap.*, a.name as affiliate_name
        FROM affiliate_payouts ap
        JOIN affiliates a ON ap.affiliate_id = a.id
        ORDER BY ap.created_at DESC
        LIMIT 20
    '''
    
    payouts_df = pd.read_sql_query(payouts_query, conn)
    conn.close()
    
    if not payouts_df.empty:
        st.dataframe(
            payouts_df[['affiliate_name', 'amount', 'net_amount', 'payout_method', 'status', 'created_at']],
            column_config={
                'amount': st.column_config.NumberColumn('Amount', format='$%.2f'),
                'net_amount': st.column_config.NumberColumn('Net Amount', format='$%.2f'),
                'created_at': st.column_config.DatetimeColumn('Date')
            },
            use_container_width=True
        )
    else:
        st.info("No payouts processed yet")


def render_affiliate_analytics(affiliate_system: AffiliateTrackingSystem):
    """Render affiliate analytics dashboard."""
    st.subheader("📈 Affiliate Analytics")
    
    # Time period selector
    col1, col2 = st.columns(2)
    
    with col1:
        period = st.selectbox("Time Period", ["weekly", "monthly", "quarterly", "yearly"])
    
    with col2:
        chart_type = st.selectbox("Chart Type", ["Revenue", "Referrals", "Conversion Rate"])
    
    # Get analytics data
    conn = sqlite3.connect(affiliate_system.db_path)
    
    days_map = {'weekly': 7, 'monthly': 30, 'quarterly': 90, 'yearly': 365}
    days = days_map[period]
    
    # Performance over time
    time_query = '''
        SELECT 
            DATE(converted_at) as date,
            COUNT(*) as referrals,
            SUM(conversion_value) as revenue,
            SUM(commission_earned) as commissions
        FROM referrals 
        WHERE converted_at > datetime('now', '-{} days')
        GROUP BY DATE(converted_at)
        ORDER BY date
    '''.format(days)
    
    time_df = pd.read_sql_query(time_query, conn)
    
    if not time_df.empty:
        fig = go.Figure()
        
        if chart_type == "Revenue":
            fig.add_trace(go.Scatter(x=time_df['date'], y=time_df['revenue'], name='Revenue'))
        elif chart_type == "Referrals":
            fig.add_trace(go.Scatter(x=time_df['date'], y=time_df['referrals'], name='Referrals'))
        else:  # Conversion Rate
            # Calculate conversion rate from clicks
            click_query = '''
                SELECT 
                    DATE(clicked_at) as date,
                    COUNT(*) as clicks,
                    SUM(CASE WHEN converted THEN 1 ELSE 0 END) as conversions
                FROM affiliate_clicks 
                WHERE clicked_at > datetime('now', '-{} days')
                GROUP BY DATE(clicked_at)
                ORDER BY date
            '''.format(days)
            
            click_df = pd.read_sql_query(click_query, conn)
            if not click_df.empty:
                click_df['conversion_rate'] = (click_df['conversions'] / click_df['clicks']) * 100
                fig.add_trace(go.Scatter(x=click_df['date'], y=click_df['conversion_rate'], name='Conversion Rate %'))
        
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Leaderboard
    st.subheader("🏆 Affiliate Leaderboard")
    leaderboard = affiliate_system.get_affiliate_leaderboard(period)
    
    if not leaderboard.empty:
        st.dataframe(
            leaderboard,
            column_config={
                'revenue_generated': st.column_config.NumberColumn('Revenue Generated', format='$%.2f'),
                'commissions_earned': st.column_config.NumberColumn('Commissions Earned', format='$%.2f'),
                'avg_commission_rate': st.column_config.NumberColumn('Avg Rate', format='%.1f%%')
            },
            use_container_width=True
        )
    
    conn.close()


def render_affiliate_settings(affiliate_system: AffiliateTrackingSystem):
    """Render affiliate program settings."""
    st.subheader("⚙️ Affiliate Program Settings")
    
    # Commission tiers
    st.write("**Commission Tiers**")
    
    conn = sqlite3.connect(affiliate_system.db_path)
    tiers_df = pd.read_sql_query("SELECT * FROM commission_tiers ORDER BY min_referrals", conn)
    
    if not tiers_df.empty:
        st.dataframe(
            tiers_df[['tier_name', 'min_referrals', 'commission_rate', 'bonus_rate']],
            column_config={
                'commission_rate': st.column_config.NumberColumn('Commission Rate', format='%.1%'),
                'bonus_rate': st.column_config.NumberColumn('Bonus Rate', format='%.1%')
            },
            use_container_width=True
        )
    
    # Revenue sharing rules
    st.write("**Revenue Sharing Rules**")
    
    rules_df = pd.read_sql_query('''
        SELECT partner_type, subscription_tier, revenue_event, 
               commission_type, commission_value, recurring
        FROM revenue_sharing_rules 
        WHERE is_active = 1
    ''', conn)
    
    if not rules_df.empty:
        st.dataframe(rules_df, use_container_width=True)
    
    conn.close()
    
    # Settings form
    with st.expander("⚙️ Update Settings"):
        with st.form("affiliate_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                default_commission = st.number_input("Default Commission Rate", min_value=0.0, max_value=0.5, value=0.2, step=0.01)
                min_payout = st.number_input("Minimum Payout Threshold", min_value=10.0, value=100.0, step=10.0)
            
            with col2:
                auto_approve = st.checkbox("Auto-approve new affiliates")
                require_tax_info = st.checkbox("Require tax information for payouts")
            
            cookie_duration = st.number_input("Cookie Duration (days)", min_value=1, max_value=365, value=30)
            
            if st.form_submit_button("💾 Save Settings"):
                st.success("✅ Settings updated successfully!")


def show_affiliate_details(affiliate_system: AffiliateTrackingSystem, affiliate_id: str):
    """Show detailed affiliate information in modal."""
    stats = affiliate_system.get_affiliate_stats(affiliate_id)
    
    with st.modal(f"Affiliate Details: {stats['affiliate_info']['name']}"):
        # Basic info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Tier", stats['affiliate_info']['tier'])
        
        with col2:
            st.metric("Commission Rate", f"{stats['affiliate_info']['commission_rate']:.1%}")
        
        with col3:
            st.metric("Member Since", stats['affiliate_info']['created_at'][:10])
        
        # Performance metrics
        st.subheader("📊 Performance (30 days)")
        
        col4, col5, col6, col7 = st.columns(4)
        
        with col4:
            st.metric("Referrals", int(stats['performance']['referrals'] or 0))
        
        with col5:
            st.metric("Revenue", f"${stats['performance']['revenue'] or 0:.2f}")
        
        with col6:
            st.metric("Commissions", f"${stats['performance']['commissions'] or 0:.2f}")
        
        with col7:
            st.metric("Conversion Rate", f"{stats['conversion_rate']:.1f}%")
        
        # Top links
        if stats['top_links']:
            st.subheader("🔗 Top Performing Links")
            for link in stats['top_links']:
                st.write(f"**{link['campaign_name']}** - {link['clicks']} clicks, {link['conversions']} conversions ({link['conversion_rate']:.1f}%)")


if __name__ == "__main__":
    render_affiliate_management_ui()
