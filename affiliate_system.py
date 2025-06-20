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
import logging

logger = logging.getLogger(__name__)

class AffiliateTrackingSystem:
    """Comprehensive affiliate tracking and referral system."""

    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()
        self.init_affiliate_tables()

    def init_affiliate_tables(self):
        """Initialize affiliate tracking database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Affiliate programs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                commission_rate REAL,
                commission_type TEXT DEFAULT 'percentage',
                tier_structure TEXT,
                terms_conditions TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Affiliates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                program_id INTEGER,
                referral_code TEXT UNIQUE,
                status TEXT DEFAULT 'active',
                total_referrals INTEGER DEFAULT 0,
                total_commission REAL DEFAULT 0.0,
                current_tier INTEGER DEFAULT 1,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payment_info TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (program_id) REFERENCES affiliate_programs (id)
            )
        ''')

        # Referrals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id INTEGER,
                referred_user_id INTEGER,
                referral_code TEXT,
                conversion_type TEXT,
                commission_amount REAL,
                commission_paid BOOLEAN DEFAULT 0,
                referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                conversion_date TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id),
                FOREIGN KEY (referred_user_id) REFERENCES users (id)
            )
        ''')

        # Commission payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commission_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id INTEGER,
                amount REAL,
                payment_method TEXT,
                payment_reference TEXT,
                status TEXT DEFAULT 'pending',
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                period_start DATE,
                period_end DATE,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id)
            )
        ''')

        # Affiliate clicks/visits tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id INTEGER,
                referral_code TEXT,
                ip_address TEXT,
                user_agent TEXT,
                referrer_url TEXT,
                landing_page TEXT,
                converted BOOLEAN DEFAULT 0,
                click_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id)
            )
        ''')

        conn.commit()
        conn.close()

    def render_affiliate_dashboard(self):
        """Render the main affiliate dashboard."""
        current_user = self.auth_manager.get_current_user()

        if not current_user:
            st.warning("🔐 Please login to access the affiliate program")
            return

        st.title("💰 TradeSense Affiliate Program")
        st.markdown("---")

        # Check if user is already an affiliate
        affiliate = self.get_affiliate_by_user_id(current_user['id'])

        if not affiliate:
            self._render_affiliate_signup()
        else:
            self._render_affiliate_portal(affiliate)

    def _render_affiliate_signup(self):
        """Render affiliate program signup."""
        st.subheader("🚀 Join Our Affiliate Program")

        # Program benefits
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### 💰 Earn Commission
            - **Up to 40%** recurring commission
            - **Tiered rewards** based on performance
            - **Monthly payouts** via PayPal/Bank transfer
            - **Real-time tracking** of your earnings
            """)

        with col2:
            st.markdown("""
            ### 🎯 Marketing Support
            - **Custom referral links** and codes
            - **Marketing materials** and banners
            - **Performance analytics** dashboard
            - **Dedicated affiliate support**
            """)

        # Commission structure
        st.subheader("📊 Commission Structure")

        tier_data = [
            {"Tier": "Bronze", "Referrals": "1-10", "Commission": "20%", "Bonus": "-"},
            {"Tier": "Silver", "Referrals": "11-25", "Commission": "25%", "Bonus": "$100"},
            {"Tier": "Gold", "Referrals": "26-50", "Commission": "30%", "Bonus": "$250"},
            {"Tier": "Platinum", "Referrals": "51+", "Commission": "40%", "Bonus": "$500"}
        ]

        df_tiers = pd.DataFrame(tier_data)
        st.table(df_tiers)

        # Signup form
        st.subheader("📝 Application Form")

        with st.form("affiliate_signup"):
            # Get available programs
            programs = self.get_affiliate_programs()

            if programs:
                program_names = [p['name'] for p in programs]
                selected_program = st.selectbox("Select Affiliate Program", program_names)
                program_id = next(p['id'] for p in programs if p['name'] == selected_program)
            else:
                st.error("No affiliate programs available")
                return

            # Application details
            marketing_experience = st.text_area(
                "Tell us about your marketing experience",
                placeholder="Describe your audience, marketing channels, etc."
            )

            website_url = st.text_input("Website/Social Media URL (optional)")

            promotional_methods = st.multiselect(
                "How do you plan to promote TradeSense?",
                ["Social Media", "Blog/Website", "Email Marketing", "YouTube", "Paid Ads", "Other"]
            )

            expected_referrals = st.selectbox(
                "Expected monthly referrals",
                ["1-5", "6-15", "16-30", "31+"]
            )

            agree_terms = st.checkbox("I agree to the affiliate program terms and conditions")

            submitted = st.form_submit_button("🚀 Apply Now")

            if submitted and agree_terms:
                # Create affiliate account
                result = self.create_affiliate(
                    user_id=st.session_state.current_user['id'],
                    program_id=program_id,
                    application_data={
                        'marketing_experience': marketing_experience,
                        'website_url': website_url,
                        'promotional_methods': promotional_methods,
                        'expected_referrals': expected_referrals
                    }
                )

                if result['success']:
                    st.success("🎉 Welcome to the TradeSense Affiliate Program!")
                    st.info(f"Your referral code: **{result['referral_code']}**")
                    st.rerun()
                else:
                    st.error("Application failed. Please try again.")

    def _render_affiliate_portal(self, affiliate: Dict):
        """Render the affiliate portal for existing affiliates."""
        # Affiliate header
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Referral Code", affiliate['referral_code'])

        with col2:
            tier_name = self.get_tier_name(affiliate['current_tier'])
            st.metric("Current Tier", tier_name)

        with col3:
            st.metric("Status", affiliate['status'].title())

        # Dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard",
            "🔗 Marketing Tools",
            "👥 Referrals",
            "💰 Earnings",
            "⚙️ Settings"
        ])

        with tab1:
            self._render_affiliate_stats(affiliate)

        with tab2:
            self._render_marketing_tools(affiliate)

        with tab3:
            self._render_referral_management(affiliate)

        with tab4:
            self._render_earnings_dashboard(affiliate)

        with tab5:
            self._render_affiliate_settings(affiliate)

    def _render_affiliate_stats(self, affiliate: Dict):
        """Render affiliate statistics dashboard."""
        st.subheader("📊 Performance Dashboard")

        # Get affiliate statistics
        stats = self.get_affiliate_stats(affiliate['id'])

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Clicks", stats.get('total_clicks', 0))

        with col2:
            st.metric("Total Referrals", stats.get('total_referrals', 0))

        with col3:
            conversion_rate = stats.get('conversion_rate', 0)
            st.metric("Conversion Rate", f"{conversion_rate:.1f}%")

        with col4:
            st.metric("Total Earned", f"${stats.get('total_earned', 0):.2f}")

        # Performance charts
        col1, col2 = st.columns(2)

        with col1:
            # Clicks over time
            clicks_data = self.get_clicks_over_time(affiliate['id'])
            if not clicks_data.empty:
                fig = px.line(clicks_data, x='date', y='clicks',
                             title="Clicks Over Time")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No click data available yet")

        with col2:
            # Referrals over time
            referrals_data = self.get_referrals_over_time(affiliate['id'])
            if not referrals_data.empty:
                fig = px.bar(referrals_data, x='date', y='referrals',
                           title="Referrals Over Time")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No referral data available yet")

        # Recent activity
        st.subheader("📈 Recent Activity")
        recent_activity = self.get_recent_affiliate_activity(affiliate['id'])

        if recent_activity:
            for activity in recent_activity:
                st.write(f"**{activity['timestamp']}**: {activity['description']}")
        else:
            st.info("No recent activity")

    def _render_marketing_tools(self, affiliate: Dict):
        """Render marketing tools and materials."""
        st.subheader("🔗 Marketing Tools")

        # Referral links
        st.subheader("🔗 Your Referral Links")

        base_url = "https://tradesense.app"  # Replace with actual domain
        referral_code = affiliate['referral_code']

        referral_links = {
            "Main Landing Page": f"{base_url}/?ref={referral_code}",
            "Pricing Page": f"{base_url}/pricing?ref={referral_code}",
            "Demo Page": f"{base_url}/demo?ref={referral_code}",
            "Blog": f"{base_url}/blog?ref={referral_code}"
        }

        for name, link in referral_links.items():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text_input(name, value=link, key=f"link_{name}")
            with col2:
                if st.button("📋 Copy", key=f"copy_{name}"):
                    st.success("Copied!")

        # Custom link builder
        st.subheader("🛠️ Custom Link Builder")

        with st.form("custom_link_builder"):
            page_url = st.text_input("Page URL", value=base_url)
            campaign_name = st.text_input("Campaign Name (optional)")
            medium = st.text_input("Medium (optional)", placeholder="email, social, blog")

            if st.form_submit_button("Generate Link"):
                custom_link = f"{page_url}?ref={referral_code}"
                if campaign_name:
                    custom_link += f"&campaign={campaign_name}"
                if medium:
                    custom_link += f"&medium={medium}"

                st.success(f"Custom link: `{custom_link}`")

        # Marketing materials
        st.subheader("🎨 Marketing Materials")

        # Banner ads
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Banner Ads (Coming Soon)**")
            st.info("Various banner sizes and designs will be available for download")

        with col2:
            st.markdown("**Email Templates (Coming Soon)**")
            st.info("Pre-written email templates for your campaigns")

        # Social media content
        st.subheader("📱 Social Media Content")

        sample_posts = [
            "🚀 Just discovered TradeSense - the most comprehensive trading analytics platform! Track your performance, manage risk, and improve your trading. Check it out: [Your Referral Link]",
            "📊 Finally, a trading analytics tool that actually makes sense! TradeSense has helped me identify my profitable patterns and reduce risk. Highly recommended: [Your Referral Link]",
            "💡 Pro tip: If you're serious about trading, you need proper analytics. TradeSense is the best tool I've found for tracking and improving performance: [Your Referral Link]"
        ]

        for i, post in enumerate(sample_posts, 1):
            st.text_area(f"Sample Post {i}", post.replace("[Your Referral Link]", referral_links["Main Landing Page"]))

    def _render_referral_management(self, affiliate: Dict):
        """Render referral management interface."""
        st.subheader("👥 Your Referrals")

        # Referral statistics
        referral_stats = self.get_referral_stats(affiliate['id'])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Active Referrals", referral_stats.get('active', 0))

        with col2:
            st.metric("Pending Referrals", referral_stats.get('pending', 0))

        with col3:
            st.metric("Total Lifetime", referral_stats.get('total', 0))

        # Referral list
        st.subheader("📋 Referral Details")

        referrals = self.get_affiliate_referrals(affiliate['id'])

        if not referrals.empty:
            # Format data for display
            display_referrals = referrals.copy()
            display_referrals['commission_amount'] = display_referrals['commission_amount'].apply(lambda x: f"${x:.2f}")
            display_referrals['referral_date'] = pd.to_datetime(display_referrals['referral_date']).dt.strftime('%Y-%m-%d')

            st.dataframe(display_referrals[['referral_date', 'conversion_type', 'commission_amount', 'commission_paid']], 
                        use_container_width=True)
        else:
            st.info("No referrals yet. Start sharing your referral link!")

        # Referral insights
        st.subheader("📈 Referral Insights")

        if not referrals.empty:
            # Conversion sources
            conversion_sources = referrals['conversion_type'].value_counts()
            fig = px.pie(values=conversion_sources.values, names=conversion_sources.index,
                        title="Referrals by Conversion Type")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insights will appear once you have referrals")

    def _render_earnings_dashboard(self, affiliate: Dict):
        """Render earnings and commission dashboard."""
        st.subheader("💰 Earnings Dashboard")

        # Earnings overview
        earnings = self.get_affiliate_earnings(affiliate['id'])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Earned", f"${earnings.get('total_earned', 0):.2f}")

        with col2:
            st.metric("Pending Commission", f"${earnings.get('pending', 0):.2f}")

        with col3:
            st.metric("Paid Commission", f"${earnings.get('paid', 0):.2f}")

        with col4:
            st.metric("This Month", f"${earnings.get('current_month', 0):.2f}")

        # Earnings chart
        earnings_history = self.get_earnings_history(affiliate['id'])

        if not earnings_history.empty:
            fig = px.bar(earnings_history, x='month', y='earnings',
                        title="Monthly Earnings")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Earnings history will appear here")

        # Payment history
        st.subheader("💳 Payment History")

        payments = self.get_payment_history(affiliate['id'])

        if not payments.empty:
            st.dataframe(payments, use_container_width=True)
        else:
            st.info("No payments yet")

        # Payment request
        if earnings.get('pending', 0) >= 50:  # Minimum payout threshold
            st.subheader("💸 Request Payment")

            if st.button("Request Payout"):
                # Process payment request
                result = self.request_payout(affiliate['id'])
                if result['success']:
                    st.success("Payout requested! You'll receive payment within 5-7 business days.")
                else:
                    st.error("Payout request failed. Please contact support.")
        else:
            st.info(f"Minimum payout amount is $50. Current pending: ${earnings.get('pending', 0):.2f}")

    def _render_affiliate_settings(self, affiliate: Dict):
        """Render affiliate settings."""
        st.subheader("⚙️ Affiliate Settings")

        # Payment information
        st.subheader("💳 Payment Information")

        current_payment_info = json.loads(affiliate.get('payment_info', '{}'))

        with st.form("payment_settings"):
            payment_method = st.selectbox(
                "Payment Method",
                ["PayPal", "Bank Transfer", "Check"],
                index=["PayPal", "Bank Transfer", "Check"].index(
                    current_payment_info.get('method', 'PayPal')
                )
            )

            if payment_method == "PayPal":
                paypal_email = st.text_input(
                    "PayPal Email",
                    value=current_payment_info.get('paypal_email', '')
                )

            elif payment_method == "Bank Transfer":
                bank_name = st.text_input(
                    "Bank Name",
                    value=current_payment_info.get('bank_name', '')
                )
                account_number = st.text_input(
                    "Account Number",
                    value=current_payment_info.get('account_number', ''),
                    type="password"
                )
                routing_number = st.text_input(
                    "Routing Number",
                    value=current_payment_info.get('routing_number', '')
                )

            else:  # Check
                mailing_address = st.text_area(
                    "Mailing Address",
                    value=current_payment_info.get('mailing_address', '')
                )

            if st.form_submit_button("💾 Save Payment Info"):
                payment_data = {'method': payment_method}

                if payment_method == "PayPal":
                    payment_data['paypal_email'] = paypal_email
                elif payment_method == "Bank Transfer":
                    payment_data.update({
                        'bank_name': bank_name,
                        'account_number': account_number,
                        'routing_number': routing_number
                    })
                else:
                    payment_data['mailing_address'] = mailing_address

                if self.update_payment_info(affiliate['id'], payment_data):
                    st.success("Payment information updated!")
                else:
                    st.error("Failed to update payment information")

        # Notification preferences
        st.subheader("🔔 Notification Preferences")

        with st.form("notification_settings"):
            email_notifications = st.checkbox("Email notifications for new referrals", value=True)
            weekly_reports = st.checkbox("Weekly performance reports", value=True)
            payment_notifications = st.checkbox("Payment notifications", value=True)

            if st.form_submit_button("💾 Save Notifications"):
                st.success("Notification preferences updated!")

    # Helper methods
    def create_affiliate(self, user_id: int, program_id: int, application_data: Dict) -> Dict[str, Any]:
        """Create a new affiliate."""
        try:
            # Generate unique referral code
            referral_code = self._generate_referral_code()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO affiliates (user_id, program_id, referral_code)
                VALUES (?, ?, ?)
            ''', (user_id, program_id, referral_code))

            affiliate_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"Affiliate created: {user_id} with code {referral_code}")

            return {
                "success": True,
                "affiliate_id": affiliate_id,
                "referral_code": referral_code
            }

        except Exception as e:
            logger.error(f"Error creating affiliate: {e}")
            return {"success": False, "message": "Failed to create affiliate"}

    def get_affiliate_by_user_id(self, user_id: int) -> Optional[Dict]:
        """Get affiliate by user ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM affiliates WHERE user_id = ?", (user_id,))
            affiliate = cursor.fetchone()

            if affiliate:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, affiliate))

            conn.close()
            return None

        except Exception as e:
            logger.error(f"Error getting affiliate: {e}")
            return None

    def get_affiliate_programs(self) -> List[Dict]:
        """Get all active affiliate programs."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM affiliate_programs WHERE is_active = 1")
            programs = cursor.fetchall()

            result = []
            if programs:
                columns = [desc[0] for desc in cursor.description]
                result = [dict(zip(columns, program)) for program in programs]

            conn.close()
            return result

        except Exception as e:
            logger.error(f"Error getting affiliate programs: {e}")
            return []

    def _generate_referral_code(self) -> str:
        """Generate unique referral code."""
        while True:
            code = secrets.token_urlsafe(8).upper()

            # Check if code already exists
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM affiliates WHERE referral_code = ?", (code,))

            if not cursor.fetchone():
                conn.close()
                return code

            conn.close()

    def get_tier_name(self, tier_number: int) -> str:
        """Get tier name by number."""
        tier_names = {1: "Bronze", 2: "Silver", 3: "Gold", 4: "Platinum"}
        return tier_names.get(tier_number, "Bronze")

    def get_affiliate_stats(self, affiliate_id: int) -> Dict:
        """Get comprehensive affiliate statistics."""
        try:
            conn = sqlite3.connect(self.db_path)

            # Total clicks
            total_clicks = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM affiliate_clicks WHERE affiliate_id = ?",
                conn, params=[affiliate_id]
            ).iloc[0]['count']

            # Total referrals
            total_referrals = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM referrals WHERE affiliate_id = ?",
                conn, params=[affiliate_id]
            ).iloc[0]['count']

            # Conversion rate
            conversion_rate = (total_referrals / total_clicks * 100) if total_clicks > 0 else 0

            # Total earned
            total_earned = pd.read_sql_query(
                "SELECT COALESCE(SUM(commission_amount), 0) as total FROM referrals WHERE affiliate_id = ?",
                conn, params=[affiliate_id]
            ).iloc[0]['total']

            conn.close()

            return {
                'total_clicks': total_clicks,
                'total_referrals': total_referrals,
                'conversion_rate': conversion_rate,
                'total_earned': total_earned
            }

        except Exception as e:
            logger.error(f"Error getting affiliate stats: {e}")
            return {}

    def get_clicks_over_time(self, affiliate_id: int) -> pd.DataFrame:
        """Get clicks over time data."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT 
                    DATE(click_timestamp) as date,
                    COUNT(*) as clicks
                FROM affiliate_clicks 
                WHERE affiliate_id = ?
                GROUP BY DATE(click_timestamp)
                ORDER BY date DESC
                LIMIT 30
            '''

            df = pd.read_sql_query(query, conn, params=[affiliate_id])
            conn.close()

            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])

            return df

        except Exception as e:
            logger.error(f"Error getting clicks over time: {e}")
            return pd.DataFrame()

    def get_referrals_over_time(self, affiliate_id: int) -> pd.DataFrame:
        """Get referrals over time data."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT 
                    DATE(referral_date) as date,
                    COUNT(*) as referrals
                FROM referrals 
                WHERE affiliate_id = ?
                GROUP BY DATE(referral_date)
                ORDER BY date DESC
                LIMIT 30
            '''

            df = pd.read_sql_query(query, conn, params=[affiliate_id])
            conn.close()

            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])

            return df

        except Exception as e:
            logger.error(f"Error getting referrals over time: {e}")
            return pd.DataFrame()

    def get_recent_affiliate_activity(self, affiliate_id: int) -> List[Dict]:
        """Get recent affiliate activity."""
        try:
            conn = sqlite3.connect(self.db_path)

            # Get recent referrals
            recent_referrals = pd.read_sql_query('''
                SELECT referral_date, commission_amount 
                FROM referrals 
                WHERE affiliate_id = ?
                ORDER BY referral_date DESC 
                LIMIT 5
            ''', conn, params=[affiliate_id])

            conn.close()

            activities = []
            for _, referral in recent_referrals.iterrows():
                activities.append({
                    'timestamp': referral['referral_date'][:19],
                    'description': f"New referral earned ${referral['commission_amount']:.2f}"
                })

            return activities

        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []

    def get_referral_stats(self, affiliate_id: int) -> Dict:
        """Get referral statistics."""
        try:
            conn = sqlite3.connect(self.db_path)

            total = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM referrals WHERE affiliate_id = ?",
                conn, params=[affiliate_id]
            ).iloc[0]['count']

            # For this example, we'll assume all referrals are active
            # In a real system, you'd track user status
            active = total
            pending = 0

            conn.close()

            return {'total': total, 'active': active, 'pending': pending}

        except Exception as e:
            logger.error(f"Error getting referral stats: {e}")
            return {}

    def get_affiliate_referrals(self, affiliate_id: int) -> pd.DataFrame:
        """Get all referrals for an affiliate."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT * FROM referrals WHERE affiliate_id = ? ORDER BY referral_date DESC",
                conn, params=[affiliate_id]
            )
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error getting affiliate referrals: {e}")
            return pd.DataFrame()

    def get_affiliate_earnings(self, affiliate_id: int) -> Dict:
        """Get affiliate earnings summary."""
        try:
            conn = sqlite3.connect(self.db_path)

            # Total earned
            total_earned = pd.read_sql_query(
                "SELECT COALESCE(SUM(commission_amount), 0) as total FROM referrals WHERE affiliate_id = ?",
                conn, params=[affiliate_id]
            ).iloc[0]['total']

            # Paid vs pending (simplified - in real system, track payment status)
            paid = total_earned * 0.8  # Assume 80% has been paid
            pending = total_earned * 0.2

            # Current month
            current_month = pd.read_sql_query('''
                SELECT COALESCE(SUM(commission_amount), 0) as total 
                FROM referrals 
                WHERE affiliate_id = ? AND strftime('%Y-%m', referral_date) = strftime('%Y-%m', 'now')
            ''', conn, params=[affiliate_id]).iloc[0]['total']

            conn.close()

            return {
                'total_earned': total_earned,
                'paid': paid,
                'pending': pending,
                'current_month': current_month
            }

        except Exception as e:
            logger.error(f"Error getting affiliate earnings: {e}")
            return {}

    def get_earnings_history(self, affiliate_id: int) -> pd.DataFrame:
        """Get earnings history by month."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT 
                    strftime('%Y-%m', referral_date) as month,
                    SUM(commission_amount) as earnings
                FROM referrals 
                WHERE affiliate_id = ?
                GROUP BY strftime('%Y-%m', referral_date)
                ORDER BY month DESC
                LIMIT 12
            '''

            df = pd.read_sql_query(query, conn, params=[affiliate_id])
            conn.close()
            return df

        except Exception as e:
            logger.error(f"Error getting earnings history: {e}")
            return pd.DataFrame()

    def get_payment_history(self, affiliate_id: int) -> pd.DataFrame:
        """Get payment history for affiliate."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT * FROM commission_payments WHERE affiliate_id = ? ORDER BY payment_date DESC",
                conn, params=[affiliate_id]
            )
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error getting payment history: {e}")
            return pd.DataFrame()

    def request_payout(self, affiliate_id: int) -> Dict[str, Any]:
        """Request commission payout."""
        try:
            # In a real system, this would integrate with payment processors
            # For now, we'll just create a pending payment record

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get pending commission amount
            cursor.execute('''
                SELECT COALESCE(SUM(commission_amount), 0) 
                FROM referrals 
                WHERE affiliate_id = ? AND commission_paid = 0
            ''', (affiliate_id,))

            pending_amount = cursor.fetchone()[0]

            if pending_amount >= 50:  # Minimum payout threshold
                # Create payment record
                cursor.execute('''
                    INSERT INTO commission_payments (affiliate_id, amount, status)
                    VALUES (?, ?, 'pending')
                ''', (affiliate_id, pending_amount))

                conn.commit()
                conn.close()

                logger.info(f"Payout requested for affiliate {affiliate_id}: ${pending_amount}")
                return {"success": True, "amount": pending_amount}
            else:
                conn.close()
                return {"success": False, "message": "Minimum payout amount not met"}

        except Exception as e:
            logger.error(f"Error requesting payout: {e}")
            return {"success": False, "message": "Payout request failed"}

    def update_payment_info(self, affiliate_id: int, payment_data: Dict) -> bool:
        """Update affiliate payment information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE affiliates SET payment_info = ? WHERE id = ?",
                (json.dumps(payment_data), affiliate_id)
            )

            conn.commit()
            conn.close()

            logger.info(f"Payment info updated for affiliate {affiliate_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating payment info: {e}")
            return False

def main():
    """Main affiliate system entry point."""
    affiliate_system = AffiliateTrackingSystem()
    affiliate_system.render_affiliate_dashboard()

if __name__ == "__main__":
    main()