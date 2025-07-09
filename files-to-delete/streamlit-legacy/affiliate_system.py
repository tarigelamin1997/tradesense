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

class AffiliateTrackingSystem:
    """Comprehensive affiliate tracking and management system."""

    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()
        self.init_database()

    def init_database(self):
        """Initialize affiliate tracking database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Affiliates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                affiliate_code TEXT UNIQUE NOT NULL,
                tier TEXT DEFAULT 'bronze',
                commission_rate REAL DEFAULT 0.10,
                total_earnings REAL DEFAULT 0.0,
                total_referrals INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_payout TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Referrals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id INTEGER,
                referred_user_id INTEGER,
                commission_amount REAL DEFAULT 0.0,
                commission_paid BOOLEAN DEFAULT 0,
                conversion_date TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id),
                FOREIGN KEY (referred_user_id) REFERENCES users (id)
            )
        ''')

        # Commission tiers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commission_tiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier_name TEXT UNIQUE NOT NULL,
                min_referrals INTEGER DEFAULT 0,
                commission_rate REAL NOT NULL,
                bonus_amount REAL DEFAULT 0.0,
                requirements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Affiliate payouts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_payouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id INTEGER,
                amount REAL NOT NULL,
                payout_method TEXT,
                transaction_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP NULL,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id)
            )
        ''')

        # Marketing materials table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketing_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                material_type TEXT NOT NULL,
                file_url TEXT,
                download_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Initialize default commission tiers
        cursor.execute('SELECT COUNT(*) FROM commission_tiers')
        if cursor.fetchone()[0] == 0:
            default_tiers = [
                ('Bronze', 0, 0.10, 0.0, 'Basic affiliate tier'),
                ('Silver', 10, 0.15, 50.0, '10+ referrals required'),
                ('Gold', 25, 0.20, 100.0, '25+ referrals required'),
                ('Platinum', 50, 0.25, 250.0, '50+ referrals required'),
                ('Diamond', 100, 0.30, 500.0, '100+ referrals required')
            ]

            cursor.executemany('''
                INSERT INTO commission_tiers (tier_name, min_referrals, commission_rate, bonus_amount, requirements)
                VALUES (?, ?, ?, ?, ?)
            ''', default_tiers)

        conn.commit()
        conn.close()

    @require_auth
    def render_affiliate_dashboard(self):
        """Render affiliate dashboard."""
        current_user = self.auth_manager.get_current_user()
        if not current_user:
            st.error("🚫 Authentication required")
            return

        st.title("💰 Affiliate Program Dashboard")

        # Check if user is an affiliate
        affiliate_data = self.get_affiliate_by_user_id(current_user['id'])

        if not affiliate_data:
            self._render_affiliate_signup()
            return

        # Main affiliate dashboard
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", "👥 Referrals", "💳 Payouts", "📈 Marketing"
        ])

        with tab1:
            self._render_affiliate_overview(affiliate_data)
        with tab2:
            self._render_referrals_section(affiliate_data)
        with tab3:
            self._render_payouts_section(affiliate_data)
        with tab4:
            self._render_marketing_materials()

    def _render_affiliate_signup(self):
        """Render affiliate signup form."""
        st.header("🚀 Join Our Affiliate Program")

        st.markdown("""
        ### 💰 Earn Up to 30% Commission

        **Commission Tiers:**
        - 🥉 **Bronze**: 10% (0+ referrals)
        - 🥈 **Silver**: 15% + $50 bonus (10+ referrals)
        - 🥇 **Gold**: 20% + $100 bonus (25+ referrals)
        - 💎 **Platinum**: 25% + $250 bonus (50+ referrals)
        - 💎 **Diamond**: 30% + $500 bonus (100+ referrals)

        **Program Benefits:**
        - Real-time tracking dashboard
        - Monthly payouts
        - Marketing materials provided
        - Dedicated affiliate support
        """)

        if st.button("🎯 Become an Affiliate", type="primary"):
            result = self.create_affiliate(st.session_state.current_user['id'])
            if result['success']:
                st.success(f"🎉 Welcome to our affiliate program! Your code: **{result['affiliate_code']}**")
                st.rerun()
            else:
                st.error(result['message'])

    def _render_affiliate_overview(self, affiliate_data: Dict):
        """Render affiliate overview dashboard."""
        st.header("📊 Your Performance Overview")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Earnings", 
                f"${affiliate_data['total_earnings']:,.2f}",
                help="Lifetime earnings from referrals"
            )

        with col2:
            st.metric(
                "Total Referrals", 
                affiliate_data['total_referrals'],
                help="Total users you've referred"
            )

        with col3:
            st.metric(
                "Commission Rate", 
                f"{affiliate_data['commission_rate']*100:.0f}%",
                help="Your current commission percentage"
            )

        with col4:
            current_tier = affiliate_data['tier'].title()
            st.metric(
                "Current Tier", 
                f"{current_tier}",
                help="Your affiliate tier level"
            )

        # Affiliate code and links
        st.subheader("🔗 Your Affiliate Tools")

        col1, col2 = st.columns(2)

        with col1:
            st.text_input(
                "Affiliate Code", 
                value=affiliate_data['affiliate_code'],
                disabled=True,
                help="Your unique affiliate identifier"
            )

        with col2:
            affiliate_url = f"https://tradesense.app?ref={affiliate_data['affiliate_code']}"
            st.text_input(
                "Referral Link", 
                value=affiliate_url,
                disabled=True,
                help="Share this link to earn commissions"
            )

        # Performance charts
        self._render_performance_charts(affiliate_data['id'])

        # Next tier progress
        self._render_tier_progress(affiliate_data)

    def _render_referrals_section(self, affiliate_data: Dict):
        """Render referrals tracking section."""
        st.header("👥 Your Referrals")

        # Referrals statistics
        referrals_stats = self.get_referral_statistics(affiliate_data['id'])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("This Month", referrals_stats.get('this_month', 0))
        with col2:
            st.metric("Conversions", referrals_stats.get('conversions', 0))
        with col3:
            st.metric("Pending", referrals_stats.get('pending', 0))
        with col4:
            conversion_rate = referrals_stats.get('conversion_rate', 0)
            st.metric("Conversion Rate", f"{conversion_rate:.1f}%")

        # Referrals table
        st.subheader("📋 Recent Referrals")
        referrals_df = self.get_referrals_dataframe(affiliate_data['id'])

        if not referrals_df.empty:
            st.dataframe(referrals_df, use_container_width=True)
        else:
            st.info("No referrals yet. Start sharing your affiliate link!")

    def _render_payouts_section(self, affiliate_data: Dict):
        """Render payouts section."""
        st.header("💳 Payouts & Earnings")

        # Payout summary
        payout_stats = self.get_payout_statistics(affiliate_data['id'])

        col1, col2, col3 = st.columns(3)

        with col1:
            pending_earnings = payout_stats.get('pending_earnings', 0)
            st.metric("Pending Earnings", f"${pending_earnings:.2f}")

        with col2:
            total_paid = payout_stats.get('total_paid', 0)
            st.metric("Total Paid", f"${total_paid:.2f}")

        with col3:
            next_payout = payout_stats.get('next_payout_date', 'TBD')
            st.metric("Next Payout", next_payout)

        # Payout methods
        st.subheader("⚙️ Payout Settings")

        with st.form("payout_settings"):
            payout_method = st.selectbox(
                "Payout Method", 
                ["PayPal", "Bank Transfer", "Crypto", "Check"]
            )
            payout_details = st.text_input("Account Details")
            min_payout = st.number_input("Minimum Payout", value=50.0, min_value=10.0)

            if st.form_submit_button("Update Settings"):
                st.success("Payout settings updated!")

        # Payout history
        st.subheader("📊 Payout History")
        payouts_df = self.get_payouts_dataframe(affiliate_data['id'])

        if not payouts_df.empty:
            st.dataframe(payouts_df, use_container_width=True)
        else:
            st.info("No payouts yet")

    def _render_marketing_materials(self):
        """Render marketing materials section."""
        st.header("📈 Marketing Materials")

        st.markdown("""
        ### 🎯 Promotion Ideas

        **Social Media:**
        - Share your success stories
        - Post about TradeSense features
        - Create trading tip content

        **Email Marketing:**
        - Include in newsletter signatures
        - Send to your trading network
        - Share in trading communities
        """)

        # Marketing materials
        materials = self.get_marketing_materials()

        if materials:
            for material in materials:
                with st.expander(f"📄 {material['title']}"):
                    st.write(material['description'])
                    if st.button(f"Download {material['title']}", key=f"download_{material['id']}"):
                        self.track_material_download(material['id'])
                        st.info(f"Download link: {material['file_url']}")
        else:
            st.info("Marketing materials coming soon!")

    def _render_performance_charts(self, affiliate_id: int):
        """Render performance charts."""
        st.subheader("📈 Performance Trends")

        # Get performance data
        performance_data = self.get_performance_data(affiliate_id)

        if performance_data:
            col1, col2 = st.columns(2)

            with col1:
                # Referrals over time
                fig_referrals = px.line(
                    performance_data['referrals_timeline'], 
                    x='date', 
                    y='count',
                    title='Referrals Over Time'
                )
                st.plotly_chart(fig_referrals, use_container_width=True)

            with col2:
                # Earnings over time
                fig_earnings = px.line(
                    performance_data['earnings_timeline'], 
                    x='date', 
                    y='amount',
                    title='Earnings Over Time'
                )
                st.plotly_chart(fig_earnings, use_container_width=True)

    def _render_tier_progress(self, affiliate_data: Dict):
        """Render tier progress section."""
        st.subheader("🎯 Tier Progress")

        current_tier = affiliate_data['tier']
        current_referrals = affiliate_data['total_referrals']

        # Get next tier requirements
        next_tier_info = self.get_next_tier_info(current_tier, current_referrals)

        if next_tier_info:
            progress = min(current_referrals / next_tier_info['min_referrals'], 1.0)
            remaining = max(next_tier_info['min_referrals'] - current_referrals, 0)

            st.progress(progress)
            st.write(f"**Next Tier:** {next_tier_info['tier_name']}")
            st.write(f"**Progress:** {current_referrals}/{next_tier_info['min_referrals']} referrals")

            if remaining > 0:
                st.write(f"**Remaining:** {remaining} referrals")
                st.write(f"**Reward:** {next_tier_info['commission_rate']*100:.0f}% commission + ${next_tier_info['bonus_amount']} bonus")
            else:
                st.success("🎉 You've reached the maximum tier!")
        else:
            st.success("🎉 You've reached the maximum tier!")

    def create_affiliate(self, user_id: int) -> Dict[str, Any]:
        """Create new affiliate account."""
        try:
            # Generate unique affiliate code
            affiliate_code = self._generate_affiliate_code()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if user is already an affiliate
            cursor.execute("SELECT id FROM affiliates WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "message": "User is already an affiliate"}

            # Create affiliate record
            cursor.execute('''
                INSERT INTO affiliates (user_id, affiliate_code, tier, commission_rate)
                VALUES (?, ?, 'bronze', 0.10)
            ''', (user_id, affiliate_code))

            conn.commit()
            conn.close()

            return {
                "success": True, 
                "affiliate_code": affiliate_code,
                "message": "Affiliate account created successfully"
            }

        except Exception as e:
            return {"success": False, "message": f"Failed to create affiliate: {str(e)}"}

    def get_affiliate_by_user_id(self, user_id: int) -> Optional[Dict]:
        """Get affiliate data by user ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, affiliate_code, tier, commission_rate, 
                       total_earnings, total_referrals, status, created_at
                FROM affiliates WHERE user_id = ?
            ''', (user_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'affiliate_code': row[2],
                    'tier': row[3],
                    'commission_rate': row[4],
                    'total_earnings': row[5],
                    'total_referrals': row[6],
                    'status': row[7],
                    'created_at': row[8]
                }
            return None

        except Exception:
            return None

    def _generate_affiliate_code(self) -> str:
        """Generate unique affiliate code."""
        while True:
            code = f"TS{secrets.token_hex(4).upper()}"

            # Check if code already exists
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM affiliates WHERE affiliate_code = ?", (code,))

            if not cursor.fetchone():
                conn.close()
                return code

            conn.close()

    def get_referral_statistics(self, affiliate_id: int) -> Dict:
        """Get referral statistics for affiliate."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # This month referrals
            cursor.execute('''
                SELECT COUNT(*) FROM referrals 
                WHERE affiliate_id = ? AND created_at > datetime('now', 'start of month')
            ''', (affiliate_id,))
            this_month = cursor.fetchone()[0]

            # Total conversions
            cursor.execute('''
                SELECT COUNT(*) FROM referrals 
                WHERE affiliate_id = ? AND conversion_date IS NOT NULL
            ''', (affiliate_id,))
            conversions = cursor.fetchone()[0]

            # Pending conversions
            cursor.execute('''
                SELECT COUNT(*) FROM referrals 
                WHERE affiliate_id = ? AND conversion_date IS NULL
            ''', (affiliate_id,))
            pending = cursor.fetchone()[0]

            # Conversion rate
            total_referrals = conversions + pending
            conversion_rate = (conversions / total_referrals * 100) if total_referrals > 0 else 0

            conn.close()

            return {
                'this_month': this_month,
                'conversions': conversions,
                'pending': pending,
                'conversion_rate': conversion_rate
            }

        except Exception:
            return {}

    def get_referrals_dataframe(self, affiliate_id: int) -> pd.DataFrame:
        """Get referrals dataframe for affiliate."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT 
                    r.created_at as "Referral Date",
                    u.username as "Referred User",
                    r.commission_amount as "Commission",
                    CASE 
                        WHEN r.conversion_date IS NOT NULL THEN 'Converted'
                        ELSE 'Pending'
                    END as "Status",
                    r.conversion_date as "Conversion Date"
                FROM referrals r
                JOIN users u ON r.referred_user_id = u.id
                WHERE r.affiliate_id = ?
                ORDER BY r.created_at DESC
                LIMIT 50
            '''
            df = pd.read_sql_query(query, conn, params=[affiliate_id])
            conn.close()
            return df
        except Exception:
            return pd.DataFrame()

    def get_payout_statistics(self, affiliate_id: int) -> Dict:
        """Get payout statistics for affiliate."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Pending earnings (unpaid commissions)
            cursor.execute('''
                SELECT COALESCE(SUM(commission_amount), 0) FROM referrals 
                WHERE affiliate_id = ? AND commission_paid = 0 AND conversion_date IS NOT NULL
            ''', (affiliate_id,))
            pending_earnings = cursor.fetchone()[0]

            # Total paid
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM affiliate_payouts 
                WHERE affiliate_id = ? AND status = 'completed'
            ''', (affiliate_id,))
            total_paid = cursor.fetchone()[0]

            conn.close()

            # Next payout date (first Monday of next month)
            next_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)
            next_month = next_month.replace(day=1)

            # Find first Monday
            while next_month.weekday() != 0:  # 0 = Monday
                next_month += timedelta(days=1)

            return {
                'pending_earnings': pending_earnings,
                'total_paid': total_paid,
                'next_payout_date': next_month.strftime('%Y-%m-%d')
            }

        except Exception:
            return {}

    def get_payouts_dataframe(self, affiliate_id: int) -> pd.DataFrame:
        """Get payouts dataframe for affiliate."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT 
                    created_at as "Date",
                    amount as "Amount",
                    payout_method as "Method",
                    status as "Status",
                    processed_at as "Processed"
                FROM affiliate_payouts 
                WHERE affiliate_id = ?
                ORDER BY created_at DESC
            '''
            df = pd.read_sql_query(query, conn, params=[affiliate_id])
            conn.close()
            return df
        except Exception:
            return pd.DataFrame()

    def get_marketing_materials(self) -> List[Dict]:
        """Get available marketing materials."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM marketing_materials ORDER BY created_at DESC')

            materials = []
            for row in cursor.fetchall():
                materials.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'material_type': row[3],
                    'file_url': row[4],
                    'download_count': row[5]
                })

            conn.close()
            return materials
        except Exception:
            return []

    def track_material_download(self, material_id: int):
        """Track marketing material download."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE marketing_materials 
                SET download_count = download_count + 1 
                WHERE id = ?
            ''', (material_id,))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_performance_data(self, affiliate_id: int) -> Dict:
        """Get performance data for charts."""
        try:
            conn = sqlite3.connect(self.db_path)

            # Referrals timeline
            referrals_query = '''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM referrals 
                WHERE affiliate_id = ? AND created_at > datetime('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            '''
            referrals_df = pd.read_sql_query(referrals_query, conn, params=[affiliate_id])

            # Earnings timeline
            earnings_query = '''
                SELECT DATE(conversion_date) as date, SUM(commission_amount) as amount
                FROM referrals 
                WHERE affiliate_id = ? AND conversion_date IS NOT NULL 
                      AND conversion_date > datetime('now', '-30 days')
                GROUP BY DATE(conversion_date)
                ORDER BY date
            '''
            earnings_df = pd.read_sql_query(earnings_query, conn, params=[affiliate_id])

            conn.close()

            return {
                'referrals_timeline': referrals_df,
                'earnings_timeline': earnings_df
            }

        except Exception:
            return {}

    def get_next_tier_info(self, current_tier: str, current_referrals: int) -> Optional[Dict]:
        """Get next tier information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT tier_name, min_referrals, commission_rate, bonus_amount
                FROM commission_tiers 
                WHERE min_referrals > ?
                ORDER BY min_referrals ASC
                LIMIT 1
            ''', (current_referrals,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'tier_name': row[0],
                    'min_referrals': row[1],
                    'commission_rate': row[2],
                    'bonus_amount': row[3]
                }
            return None

        except Exception:
            return None

`