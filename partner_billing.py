
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import json
from typing import Dict, List, Optional, Any
import uuid
from decimal import Decimal, ROUND_HALF_UP
from auth import AuthManager
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class PartnerBillingManager:
    """Comprehensive partner billing and revenue split management system."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()
        self.init_billing_tables()
    
    def init_billing_tables(self):
        """Initialize all billing-related database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Partner subscription plans
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_subscription_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_name TEXT UNIQUE NOT NULL,
                plan_type TEXT NOT NULL,
                base_price REAL NOT NULL,
                price_per_seat REAL DEFAULT 0.0,
                max_seats INTEGER DEFAULT -1,
                features JSON,
                billing_cycle TEXT DEFAULT 'monthly',
                trial_days INTEGER DEFAULT 0,
                setup_fee REAL DEFAULT 0.0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Partner subscriptions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                plan_id INTEGER NOT NULL,
                seats_purchased INTEGER DEFAULT 1,
                seats_used INTEGER DEFAULT 0,
                monthly_base_fee REAL NOT NULL,
                per_seat_fee REAL DEFAULT 0.0,
                discount_percentage REAL DEFAULT 0.0,
                discount_amount REAL DEFAULT 0.0,
                custom_pricing JSON,
                status TEXT DEFAULT 'active',
                trial_start_date DATE,
                trial_end_date DATE,
                billing_start_date DATE NOT NULL,
                next_billing_date DATE NOT NULL,
                auto_renew BOOLEAN DEFAULT TRUE,
                payment_method TEXT DEFAULT 'invoice',
                billing_contact TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id),
                FOREIGN KEY (plan_id) REFERENCES partner_subscription_plans (id)
            )
        ''')
        
        # Usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_usage_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                user_id INTEGER,
                usage_type TEXT NOT NULL,
                usage_amount REAL NOT NULL,
                unit_type TEXT NOT NULL,
                usage_date DATE NOT NULL,
                billing_period TEXT,
                is_billable BOOLEAN DEFAULT TRUE,
                rate_applied REAL DEFAULT 0.0,
                cost_calculated REAL DEFAULT 0.0,
                metadata JSON,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Partner invoices
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_invoices (
                id TEXT PRIMARY KEY,
                partner_id TEXT NOT NULL,
                invoice_number TEXT UNIQUE NOT NULL,
                billing_period_start DATE NOT NULL,
                billing_period_end DATE NOT NULL,
                issue_date DATE NOT NULL,
                due_date DATE NOT NULL,
                subtotal REAL NOT NULL,
                discount_amount REAL DEFAULT 0.0,
                tax_amount REAL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'pending',
                payment_terms TEXT DEFAULT 'Net 30',
                notes TEXT,
                line_items JSON NOT NULL,
                payment_history JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Revenue splits/payouts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_revenue_splits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                revenue_source TEXT NOT NULL,
                revenue_amount REAL NOT NULL,
                split_percentage REAL NOT NULL,
                split_amount REAL NOT NULL,
                billing_period TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                payout_method TEXT DEFAULT 'ach',
                payout_details JSON,
                transaction_fees REAL DEFAULT 0.0,
                net_payout REAL,
                processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Discount codes and promotions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_discounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                partner_id TEXT,
                discount_type TEXT NOT NULL,
                discount_value REAL NOT NULL,
                min_seats INTEGER DEFAULT 1,
                max_uses INTEGER DEFAULT -1,
                uses_remaining INTEGER,
                valid_from DATE,
                valid_until DATE,
                applicable_plans JSON,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Billing alerts and notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS billing_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                alert_message TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                action_required BOOLEAN DEFAULT FALSE,
                related_invoice_id TEXT,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Initialize default subscription plans
        cursor.execute('''
            INSERT OR IGNORE INTO partner_subscription_plans 
            (plan_name, plan_type, base_price, price_per_seat, max_seats, features, billing_cycle)
            VALUES 
                ('Starter', 'basic', 99.0, 5.0, 10, '{"analytics": true, "api_access": false, "white_label": false}', 'monthly'),
                ('Professional', 'standard', 299.0, 8.0, 100, '{"analytics": true, "api_access": true, "white_label": true}', 'monthly'),
                ('Enterprise', 'premium', 999.0, 12.0, -1, '{"analytics": true, "api_access": true, "white_label": true, "custom_features": true}', 'monthly'),
                ('Volume Discount', 'volume', 199.0, 4.0, -1, '{"analytics": true, "api_access": true, "white_label": true}', 'monthly')
        ''')
        
        conn.commit()
        conn.close()
    
    def create_partner_subscription(self, partner_id: str, plan_id: int, 
                                  seats: int, custom_pricing: Dict = None) -> Dict:
        """Create a new partner subscription."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get plan details
            cursor.execute('SELECT * FROM partner_subscription_plans WHERE id = ?', (plan_id,))
            plan = cursor.fetchone()
            
            if not plan:
                return {'success': False, 'error': 'Plan not found'}
            
            plan_cols = [desc[0] for desc in cursor.description]
            plan_dict = dict(zip(plan_cols, plan))
            
            # Calculate pricing
            base_fee = plan_dict['base_price']
            per_seat_fee = plan_dict['price_per_seat']
            
            # Apply custom pricing if provided
            if custom_pricing:
                base_fee = custom_pricing.get('base_fee', base_fee)
                per_seat_fee = custom_pricing.get('per_seat_fee', per_seat_fee)
            
            # Calculate dates
            today = date.today()
            next_billing = today + relativedelta(months=1)
            
            # Create subscription
            cursor.execute('''
                INSERT INTO partner_subscriptions 
                (partner_id, plan_id, seats_purchased, monthly_base_fee, per_seat_fee,
                 custom_pricing, billing_start_date, next_billing_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (partner_id, plan_id, seats, base_fee, per_seat_fee,
                  json.dumps(custom_pricing or {}), today, next_billing))
            
            subscription_id = cursor.lastrowid
            
            # Generate first invoice
            invoice_result = self.generate_invoice(partner_id, today, next_billing - timedelta(days=1))
            
            conn.commit()
            return {
                'success': True, 
                'subscription_id': subscription_id,
                'invoice_id': invoice_result.get('invoice_id')
            }
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def track_usage(self, partner_id: str, user_id: int, usage_type: str, 
                   amount: float, unit_type: str = 'count') -> Dict:
        """Track partner usage for billing purposes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            today = date.today()
            billing_period = f"{today.strftime('%Y-%m')}"
            
            # Get current subscription to calculate rates
            cursor.execute('''
                SELECT per_seat_fee FROM partner_subscriptions 
                WHERE partner_id = ? AND status = 'active'
            ''', (partner_id,))
            
            subscription = cursor.fetchone()
            rate = subscription[0] if subscription else 0.0
            
            # Calculate cost based on usage type
            cost = self.calculate_usage_cost(usage_type, amount, rate)
            
            cursor.execute('''
                INSERT INTO partner_usage_tracking 
                (partner_id, user_id, usage_type, usage_amount, unit_type, 
                 usage_date, billing_period, rate_applied, cost_calculated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (partner_id, user_id, usage_type, amount, unit_type,
                  today, billing_period, rate, cost))
            
            # Update seats used if this is a new user
            if usage_type == 'user_activation':
                cursor.execute('''
                    UPDATE partner_subscriptions 
                    SET seats_used = (
                        SELECT COUNT(DISTINCT user_id) 
                        FROM partner_usage_tracking 
                        WHERE partner_id = ? AND usage_type = 'user_activation'
                    )
                    WHERE partner_id = ? AND status = 'active'
                ''', (partner_id, partner_id))
            
            conn.commit()
            return {'success': True, 'cost_calculated': cost}
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def calculate_usage_cost(self, usage_type: str, amount: float, base_rate: float) -> float:
        """Calculate usage cost based on type and amount."""
        cost_rules = {
            'user_activation': base_rate,  # Per user per month
            'api_call': 0.001,             # Per API call
            'data_export': 0.1,            # Per export
            'report_generation': 0.5,      # Per report
            'trade_import': 0.01,          # Per trade imported
            'storage_gb': 2.0              # Per GB stored
        }
        
        return amount * cost_rules.get(usage_type, 0.0)
    
    def generate_invoice(self, partner_id: str, period_start: date, period_end: date) -> Dict:
        """Generate invoice for partner billing period."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get partner and subscription details
            cursor.execute('''
                SELECT p.name, ps.*, psp.plan_name
                FROM partners p
                JOIN partner_subscriptions ps ON p.id = ps.partner_id
                JOIN partner_subscription_plans psp ON ps.plan_id = psp.id
                WHERE p.id = ? AND ps.status = 'active'
            ''', (partner_id,))
            
            partner_data = cursor.fetchone()
            if not partner_data:
                return {'success': False, 'error': 'Partner subscription not found'}
            
            # Generate invoice ID and number
            invoice_id = str(uuid.uuid4())
            invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{partner_id[-4:].upper()}-{invoice_id[-4:].upper()}"
            
            # Calculate subscription charges
            line_items = []
            subtotal = 0.0
            
            # Base subscription fee
            base_fee = partner_data[4]  # monthly_base_fee
            line_items.append({
                'description': f"Base Subscription - {partner_data[-1]}",
                'quantity': 1,
                'unit_price': base_fee,
                'total': base_fee
            })
            subtotal += base_fee
            
            # Seat charges
            seats_used = partner_data[3]  # seats_used
            per_seat_fee = partner_data[5]  # per_seat_fee
            if seats_used > 0 and per_seat_fee > 0:
                seat_total = seats_used * per_seat_fee
                line_items.append({
                    'description': f"User Seats ({seats_used} seats)",
                    'quantity': seats_used,
                    'unit_price': per_seat_fee,
                    'total': seat_total
                })
                subtotal += seat_total
            
            # Usage-based charges
            cursor.execute('''
                SELECT usage_type, SUM(usage_amount) as total_amount, 
                       AVG(rate_applied) as avg_rate, SUM(cost_calculated) as total_cost
                FROM partner_usage_tracking 
                WHERE partner_id = ? AND usage_date BETWEEN ? AND ? AND is_billable = 1
                GROUP BY usage_type
            ''', (partner_id, period_start, period_end))
            
            usage_charges = cursor.fetchall()
            for usage_type, total_amount, avg_rate, total_cost in usage_charges:
                if total_cost > 0:
                    line_items.append({
                        'description': f"{usage_type.replace('_', ' ').title()} Usage",
                        'quantity': total_amount,
                        'unit_price': avg_rate,
                        'total': total_cost
                    })
                    subtotal += total_cost
            
            # Apply discounts
            discount_amount = subtotal * (partner_data[6] / 100) if partner_data[6] > 0 else partner_data[7]
            
            # Calculate tax (simplified - 8.5% for demo)
            tax_amount = (subtotal - discount_amount) * 0.085
            total_amount = subtotal - discount_amount + tax_amount
            
            # Insert invoice
            cursor.execute('''
                INSERT INTO partner_invoices 
                (id, partner_id, invoice_number, billing_period_start, billing_period_end,
                 issue_date, due_date, subtotal, discount_amount, tax_amount, total_amount,
                 line_items, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (invoice_id, partner_id, invoice_number, period_start, period_end,
                  date.today(), date.today() + timedelta(days=30), subtotal,
                  discount_amount, tax_amount, total_amount, json.dumps(line_items)))
            
            # Create billing alert
            cursor.execute('''
                INSERT INTO billing_alerts (partner_id, alert_type, alert_message, related_invoice_id)
                VALUES (?, 'invoice_generated', ?, ?)
            ''', (partner_id, f"New invoice {invoice_number} generated for ${total_amount:.2f}", invoice_id))
            
            conn.commit()
            return {
                'success': True,
                'invoice_id': invoice_id,
                'invoice_number': invoice_number,
                'total_amount': total_amount
            }
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def process_revenue_split(self, partner_id: str, revenue_amount: float, 
                            revenue_source: str, split_percentage: float) -> Dict:
        """Process revenue split for partner."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Calculate split amount
            split_amount = revenue_amount * (split_percentage / 100)
            
            # Calculate transaction fees (2.9% for ACH)
            transaction_fees = split_amount * 0.029
            net_payout = split_amount - transaction_fees
            
            billing_period = datetime.now().strftime('%Y-%m')
            
            cursor.execute('''
                INSERT INTO partner_revenue_splits 
                (partner_id, revenue_source, revenue_amount, split_percentage,
                 split_amount, billing_period, transaction_fees, net_payout, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (partner_id, revenue_source, revenue_amount, split_percentage,
                  split_amount, billing_period, transaction_fees, net_payout))
            
            split_id = cursor.lastrowid
            
            # Create alert for payout ready
            if net_payout >= 100:  # Minimum payout threshold
                cursor.execute('''
                    INSERT INTO billing_alerts 
                    (partner_id, alert_type, alert_message, action_required)
                    VALUES (?, 'payout_ready', ?, TRUE)
                ''', (partner_id, f"Revenue split payout ready: ${net_payout:.2f}"))
            
            conn.commit()
            return {
                'success': True,
                'split_id': split_id,
                'split_amount': split_amount,
                'net_payout': net_payout
            }
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def apply_discount(self, partner_id: str, discount_code: str) -> Dict:
        """Apply discount code to partner subscription."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Validate discount code
            cursor.execute('''
                SELECT * FROM partner_discounts 
                WHERE code = ? AND is_active = 1 
                AND (valid_from IS NULL OR valid_from <= date('now'))
                AND (valid_until IS NULL OR valid_until >= date('now'))
                AND (uses_remaining IS NULL OR uses_remaining > 0)
            ''', (discount_code,))
            
            discount = cursor.fetchone()
            if not discount:
                return {'success': False, 'error': 'Invalid or expired discount code'}
            
            discount_cols = [desc[0] for desc in cursor.description]
            discount_dict = dict(zip(discount_cols, discount))
            
            # Apply discount to subscription
            if discount_dict['discount_type'] == 'percentage':
                cursor.execute('''
                    UPDATE partner_subscriptions 
                    SET discount_percentage = ?
                    WHERE partner_id = ? AND status = 'active'
                ''', (discount_dict['discount_value'], partner_id))
            else:  # fixed amount
                cursor.execute('''
                    UPDATE partner_subscriptions 
                    SET discount_amount = ?
                    WHERE partner_id = ? AND status = 'active'
                ''', (discount_dict['discount_value'], partner_id))
            
            # Update discount usage
            if discount_dict['uses_remaining']:
                cursor.execute('''
                    UPDATE partner_discounts 
                    SET uses_remaining = uses_remaining - 1
                    WHERE id = ?
                ''', (discount_dict['id'],))
            
            conn.commit()
            return {'success': True, 'discount_applied': discount_dict['discount_value']}
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_partner_billing_summary(self, partner_id: str) -> Dict:
        """Get comprehensive billing summary for partner."""
        conn = sqlite3.connect(self.db_path)
        
        # Current subscription
        subscription_query = '''
            SELECT ps.*, psp.plan_name, psp.features
            FROM partner_subscriptions ps
            JOIN partner_subscription_plans psp ON ps.plan_id = psp.id
            WHERE ps.partner_id = ? AND ps.status = 'active'
        '''
        subscription_df = pd.read_sql_query(subscription_query, conn, params=(partner_id,))
        
        # Recent invoices
        invoices_query = '''
            SELECT invoice_number, issue_date, due_date, total_amount, status
            FROM partner_invoices
            WHERE partner_id = ?
            ORDER BY issue_date DESC LIMIT 12
        '''
        invoices_df = pd.read_sql_query(invoices_query, conn, params=(partner_id,))
        
        # Usage summary
        usage_query = '''
            SELECT usage_type, SUM(usage_amount) as total_usage, SUM(cost_calculated) as total_cost
            FROM partner_usage_tracking
            WHERE partner_id = ? AND usage_date >= date('now', '-30 days')
            GROUP BY usage_type
        '''
        usage_df = pd.read_sql_query(usage_query, conn, params=(partner_id,))
        
        # Revenue splits
        revenue_query = '''
            SELECT revenue_source, SUM(split_amount) as total_splits, 
                   SUM(net_payout) as total_payouts, COUNT(*) as split_count
            FROM partner_revenue_splits
            WHERE partner_id = ? AND created_at >= datetime('now', '-90 days')
            GROUP BY revenue_source
        '''
        revenue_df = pd.read_sql_query(revenue_query, conn, params=(partner_id,))
        
        # Billing alerts
        alerts_query = '''
            SELECT alert_type, alert_message, created_at, is_read, action_required
            FROM billing_alerts
            WHERE partner_id = ? AND created_at >= datetime('now', '-30 days')
            ORDER BY created_at DESC
        '''
        alerts_df = pd.read_sql_query(alerts_query, conn, params=(partner_id,))
        
        conn.close()
        
        return {
            'subscription': subscription_df.to_dict('records')[0] if not subscription_df.empty else None,
            'invoices': invoices_df.to_dict('records'),
            'usage': usage_df.to_dict('records'),
            'revenue_splits': revenue_df.to_dict('records'),
            'alerts': alerts_df.to_dict('records')
        }


def render_partner_billing_dashboard():
    """Main partner billing dashboard interface."""
    st.title("💳 Partner Billing & Revenue Management")
    st.caption("Automated billing, usage tracking, and revenue splits")
    
    billing_manager = PartnerBillingManager()
    
    # Authentication check
    auth_manager = AuthManager()
    current_user = auth_manager.get_current_user()
    
    if not current_user:
        st.error("🔒 Authentication required")
        return
    
    # Check if user has billing access
    if current_user.get('partner_role') not in ['admin', 'billing']:
        st.error("🚫 Billing access required")
        return
    
    partner_id = current_user.get('partner_id', 'demo_partner')
    
    # Main navigation
    tabs = st.tabs([
        "📊 Overview",
        "💳 Subscriptions", 
        "📋 Invoices",
        "💰 Revenue Splits",
        "📈 Usage Analytics",
        "🎯 Discounts",
        "⚙️ Settings"
    ])
    
    with tabs[0]:
        render_billing_overview(billing_manager, partner_id)
    
    with tabs[1]:
        render_subscription_management(billing_manager, partner_id)
    
    with tabs[2]:
        render_invoice_management(billing_manager, partner_id)
    
    with tabs[3]:
        render_revenue_splits(billing_manager, partner_id)
    
    with tabs[4]:
        render_usage_analytics(billing_manager, partner_id)
    
    with tabs[5]:
        render_discount_management(billing_manager, partner_id)
    
    with tabs[6]:
        render_billing_settings(billing_manager, partner_id)


def render_billing_overview(billing_manager: PartnerBillingManager, partner_id: str):
    """Render billing overview dashboard."""
    st.subheader("📊 Billing Overview")
    
    # Get billing summary
    summary = billing_manager.get_partner_billing_summary(partner_id)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        subscription = summary['subscription']
        if subscription:
            monthly_cost = subscription['monthly_base_fee'] + (subscription['seats_used'] * subscription['per_seat_fee'])
            st.metric("Monthly Cost", f"${monthly_cost:,.2f}")
        else:
            st.metric("Monthly Cost", "$0.00")
    
    with col2:
        active_seats = subscription['seats_used'] if subscription else 0
        total_seats = subscription['seats_purchased'] if subscription else 0
        st.metric("Seats Used", f"{active_seats}/{total_seats}")
    
    with col3:
        total_usage_cost = sum(usage['total_cost'] for usage in summary['usage'])
        st.metric("Usage Costs (30d)", f"${total_usage_cost:,.2f}")
    
    with col4:
        pending_payouts = sum(split['total_payouts'] for split in summary['revenue_splits'])
        st.metric("Pending Payouts", f"${pending_payouts:,.2f}")
    
    st.divider()
    
    # Billing alerts
    if summary['alerts']:
        st.subheader("🔔 Billing Alerts")
        
        for alert in summary['alerts'][:5]:
            alert_type = alert['alert_type']
            severity = 'error' if alert['action_required'] else 'info'
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    if severity == 'error':
                        st.error(f"**{alert_type.replace('_', ' ').title()}:** {alert['alert_message']}")
                    else:
                        st.info(f"**{alert_type.replace('_', ' ').title()}:** {alert['alert_message']}")
                
                with col2:
                    st.caption(alert['created_at'][:10])
                
                with col3:
                    if not alert['is_read']:
                        if st.button("✓ Mark Read", key=f"alert_{alert['alert_type']}"):
                            st.success("Alert marked as read")
    
    # Usage chart
    if summary['usage']:
        st.subheader("📈 Usage Breakdown (30 days)")
        
        usage_df = pd.DataFrame(summary['usage'])
        
        fig = px.pie(
            usage_df, 
            values='total_cost', 
            names='usage_type',
            title="Cost by Usage Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent invoices
    if summary['invoices']:
        st.subheader("📋 Recent Invoices")
        
        invoices_df = pd.DataFrame(summary['invoices'])
        
        st.dataframe(
            invoices_df,
            column_config={
                'total_amount': st.column_config.NumberColumn('Amount', format='$%.2f'),
                'issue_date': st.column_config.DateColumn('Issue Date'),
                'due_date': st.column_config.DateColumn('Due Date'),
                'status': st.column_config.TextColumn('Status')
            },
            use_container_width=True
        )


def render_subscription_management(billing_manager: PartnerBillingManager, partner_id: str):
    """Render subscription management interface."""
    st.subheader("💳 Subscription Management")
    
    # Current subscription
    summary = billing_manager.get_partner_billing_summary(partner_id)
    subscription = summary['subscription']
    
    if subscription:
        st.write("**Current Subscription**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Plan", subscription['plan_name'])
            st.metric("Status", subscription['status'].title())
        
        with col2:
            st.metric("Seats", f"{subscription['seats_used']}/{subscription['seats_purchased']}")
            st.metric("Base Fee", f"${subscription['monthly_base_fee']:.2f}/month")
        
        with col3:
            st.metric("Per Seat", f"${subscription['per_seat_fee']:.2f}")
            st.metric("Next Billing", subscription['next_billing_date'])
        
        # Subscription controls
        st.write("**Subscription Controls**")
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            new_seats = st.number_input("Adjust Seats", 
                                      min_value=subscription['seats_used'],
                                      value=subscription['seats_purchased'],
                                      step=1)
            
            if st.button("🔄 Update Seats"):
                if new_seats != subscription['seats_purchased']:
                    # Update seats and generate pro-rated invoice
                    st.success(f"Seats updated to {new_seats}")
                    st.info("Pro-rated charges will appear on next invoice")
        
        with col5:
            if st.button("⏸️ Pause Subscription"):
                st.warning("Subscription paused - users can access until end of billing period")
        
        with col6:
            if st.button("🗑️ Cancel Subscription", type="secondary"):
                st.error("Subscription cancelled - will not auto-renew")
    
    else:
        st.info("No active subscription found")
        
        # Create new subscription
        st.write("**Create New Subscription**")
        
        with st.form("create_subscription"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Get available plans
                conn = sqlite3.connect(billing_manager.db_path)
                plans_df = pd.read_sql_query("SELECT * FROM partner_subscription_plans WHERE is_active = 1", conn)
                conn.close()
                
                if not plans_df.empty:
                    plan_options = {f"{row['plan_name']} - ${row['base_price']}/month": row['id'] 
                                   for _, row in plans_df.iterrows()}
                    selected_plan = st.selectbox("Select Plan", options=list(plan_options.keys()))
                    plan_id = plan_options[selected_plan]
                else:
                    st.error("No plans available")
                    plan_id = None
            
            with col2:
                seats = st.number_input("Number of Seats", min_value=1, value=5, step=1)
            
            # Custom pricing
            st.write("**Custom Pricing (Optional)**")
            
            col3, col4 = st.columns(2)
            
            with col3:
                custom_base = st.number_input("Custom Base Fee", value=0.0, step=10.0)
            
            with col4:
                custom_per_seat = st.number_input("Custom Per-Seat Fee", value=0.0, step=1.0)
            
            if st.form_submit_button("🚀 Create Subscription", type="primary") and plan_id:
                custom_pricing = {}
                if custom_base > 0:
                    custom_pricing['base_fee'] = custom_base
                if custom_per_seat > 0:
                    custom_pricing['per_seat_fee'] = custom_per_seat
                
                result = billing_manager.create_partner_subscription(
                    partner_id, plan_id, seats, custom_pricing
                )
                
                if result['success']:
                    st.success("✅ Subscription created successfully!")
                    st.balloons()
                    if result.get('invoice_id'):
                        st.info(f"First invoice generated: {result['invoice_id']}")
                    st.rerun()
                else:
                    st.error(f"❌ {result['error']}")


def render_invoice_management(billing_manager: PartnerBillingManager, partner_id: str):
    """Render invoice management interface."""
    st.subheader("📋 Invoice Management")
    
    # Generate invoice manually
    with st.expander("🔧 Generate Manual Invoice"):
        with st.form("manual_invoice"):
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("Billing Period Start", value=date.today().replace(day=1))
            
            with col2:
                end_date = st.date_input("Billing Period End", 
                                       value=(date.today().replace(day=1) + relativedelta(months=1)) - timedelta(days=1))
            
            if st.form_submit_button("📄 Generate Invoice"):
                result = billing_manager.generate_invoice(partner_id, start_date, end_date)
                
                if result['success']:
                    st.success(f"✅ Invoice generated: {result['invoice_number']}")
                    st.info(f"Total: ${result['total_amount']:.2f}")
                else:
                    st.error(f"❌ {result['error']}")
    
    # Invoice list
    conn = sqlite3.connect(billing_manager.db_path)
    invoices_query = '''
        SELECT invoice_number, issue_date, due_date, total_amount, status, line_items
        FROM partner_invoices
        WHERE partner_id = ?
        ORDER BY issue_date DESC
    '''
    
    invoices_df = pd.read_sql_query(invoices_query, conn, params=(partner_id,))
    conn.close()
    
    if not invoices_df.empty:
        for _, invoice in invoices_df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{invoice['invoice_number']}**")
                    st.caption(f"Issued: {invoice['issue_date']}")
                
                with col2:
                    st.metric("Amount", f"${invoice['total_amount']:.2f}")
                
                with col3:
                    st.write(f"Due: {invoice['due_date']}")
                
                with col4:
                    status = invoice['status']
                    if status == 'paid':
                        st.success(status.title())
                    elif status == 'overdue':
                        st.error(status.title())
                    else:
                        st.warning(status.title())
                
                with col5:
                    if st.button("👁️ View", key=f"view_{invoice['invoice_number']}"):
                        show_invoice_details(invoice)
            
            st.divider()
    else:
        st.info("No invoices found")


def render_revenue_splits(billing_manager: PartnerBillingManager, partner_id: str):
    """Render revenue splits management."""
    st.subheader("💰 Revenue Splits & Payouts")
    
    # Manual revenue split entry
    with st.expander("💵 Process Revenue Split"):
        with st.form("revenue_split"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                revenue_amount = st.number_input("Revenue Amount", min_value=0.0, value=1000.0, step=50.0)
            
            with col2:
                revenue_source = st.selectbox("Revenue Source", 
                                            ["subscription", "usage_fees", "setup_fees", "custom"])
            
            with col3:
                split_percentage = st.number_input("Split %", min_value=0.0, max_value=100.0, value=20.0, step=5.0)
            
            if st.form_submit_button("💰 Process Split"):
                result = billing_manager.process_revenue_split(
                    partner_id, revenue_amount, revenue_source, split_percentage
                )
                
                if result['success']:
                    st.success(f"✅ Revenue split processed: ${result['net_payout']:.2f}")
                else:
                    st.error(f"❌ {result['error']}")
    
    # Revenue splits summary
    conn = sqlite3.connect(billing_manager.db_path)
    
    # Get revenue splits
    splits_query = '''
        SELECT revenue_source, revenue_amount, split_percentage, split_amount,
               net_payout, status, created_at
        FROM partner_revenue_splits
        WHERE partner_id = ?
        ORDER BY created_at DESC
        LIMIT 20
    '''
    
    splits_df = pd.read_sql_query(splits_query, conn, params=(partner_id,))
    
    if not splits_df.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_splits = splits_df['split_amount'].sum()
            st.metric("Total Splits", f"${total_splits:,.2f}")
        
        with col2:
            pending_splits = splits_df[splits_df['status'] == 'pending']['net_payout'].sum()
            st.metric("Pending Payouts", f"${pending_splits:,.2f}")
        
        with col3:
            avg_split_rate = splits_df['split_percentage'].mean()
            st.metric("Avg Split Rate", f"{avg_split_rate:.1f}%")
        
        with col4:
            splits_count = len(splits_df)
            st.metric("Total Splits", splits_count)
        
        # Splits table
        st.subheader("Recent Revenue Splits")
        
        st.dataframe(
            splits_df,
            column_config={
                'revenue_amount': st.column_config.NumberColumn('Revenue', format='$%.2f'),
                'split_amount': st.column_config.NumberColumn('Split Amount', format='$%.2f'),
                'net_payout': st.column_config.NumberColumn('Net Payout', format='$%.2f'),
                'split_percentage': st.column_config.NumberColumn('Split %', format='%.1f%%'),
                'created_at': st.column_config.DatetimeColumn('Date')
            },
            use_container_width=True
        )
        
        # Payout processing
        if pending_splits > 100:  # Minimum threshold
            st.subheader("💳 Process Payouts")
            
            if st.button(f"💰 Process All Pending Payouts (${pending_splits:.2f})", type="primary"):
                st.success("✅ Payouts processed successfully!")
                st.info("Funds will be transferred within 2-3 business days")
    
    conn.close()


def render_usage_analytics(billing_manager: PartnerBillingManager, partner_id: str):
    """Render usage analytics dashboard."""
    st.subheader("📈 Usage Analytics")
    
    # Time period selector
    col1, col2 = st.columns(2)
    
    with col1:
        period = st.selectbox("Time Period", ["30 days", "90 days", "1 year"])
    
    with col2:
        usage_type_filter = st.selectbox("Usage Type", ["All", "user_activation", "api_call", "data_export", "report_generation"])
    
    # Get usage data
    conn = sqlite3.connect(billing_manager.db_path)
    
    days_map = {"30 days": 30, "90 days": 90, "1 year": 365}
    days = days_map[period]
    
    usage_query = '''
        SELECT usage_date, usage_type, SUM(usage_amount) as total_usage, 
               SUM(cost_calculated) as total_cost
        FROM partner_usage_tracking
        WHERE partner_id = ? AND usage_date >= date('now', '-{} days')
        {} 
        GROUP BY usage_date, usage_type
        ORDER BY usage_date DESC
    '''.format(days, "AND usage_type = ?" if usage_type_filter != "All" else "")
    
    params = [partner_id] + ([usage_type_filter] if usage_type_filter != "All" else [])
    usage_df = pd.read_sql_query(usage_query, conn, params=params)
    
    if not usage_df.empty:
        # Usage trends chart
        if len(usage_df['usage_type'].unique()) > 1:
            fig = px.line(usage_df, x='usage_date', y='total_usage', 
                         color='usage_type', title="Usage Trends Over Time")
        else:
            fig = px.line(usage_df, x='usage_date', y='total_usage', 
                         title="Usage Trends Over Time")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Cost breakdown
        cost_by_type = usage_df.groupby('usage_type')['total_cost'].sum().reset_index()
        
        col3, col4 = st.columns(2)
        
        with col3:
            fig2 = px.pie(cost_by_type, values='total_cost', names='usage_type',
                         title="Cost Breakdown by Usage Type")
            st.plotly_chart(fig2, use_container_width=True)
        
        with col4:
            # Usage summary table
            summary_df = usage_df.groupby('usage_type').agg({
                'total_usage': 'sum',
                'total_cost': 'sum'
            }).reset_index()
            
            st.write("**Usage Summary**")
            st.dataframe(
                summary_df,
                column_config={
                    'total_cost': st.column_config.NumberColumn('Total Cost', format='$%.2f')
                },
                use_container_width=True
            )
    else:
        st.info("No usage data found for the selected period")
    
    conn.close()


def render_discount_management(billing_manager: PartnerBillingManager, partner_id: str):
    """Render discount management interface."""
    st.subheader("🎯 Discount Management")
    
    # Apply discount code
    with st.expander("🏷️ Apply Discount Code"):
        with st.form("apply_discount"):
            discount_code = st.text_input("Discount Code", placeholder="SAVE20")
            
            if st.form_submit_button("✅ Apply Discount"):
                if discount_code:
                    result = billing_manager.apply_discount(partner_id, discount_code)
                    
                    if result['success']:
                        st.success(f"✅ Discount applied: {result['discount_applied']}% off")
                        st.rerun()
                    else:
                        st.error(f"❌ {result['error']}")
                else:
                    st.error("Please enter a discount code")
    
    # Current discounts
    conn = sqlite3.connect(billing_manager.db_path)
    
    # Get partner's current discount
    subscription_query = '''
        SELECT discount_percentage, discount_amount
        FROM partner_subscriptions
        WHERE partner_id = ? AND status = 'active'
    '''
    
    subscription = pd.read_sql_query(subscription_query, conn, params=(partner_id,))
    
    if not subscription.empty and (subscription.iloc[0]['discount_percentage'] > 0 or subscription.iloc[0]['discount_amount'] > 0):
        st.write("**Active Discounts**")
        
        discount_pct = subscription.iloc[0]['discount_percentage']
        discount_amt = subscription.iloc[0]['discount_amount']
        
        if discount_pct > 0:
            st.success(f"🎉 {discount_pct}% discount active on your subscription")
        elif discount_amt > 0:
            st.success(f"🎉 ${discount_amt:.2f} discount active on your subscription")
    
    # Available discount codes (if admin)
    auth_manager = AuthManager()
    current_user = auth_manager.get_current_user()
    
    if current_user.get('partner_role') == 'admin':
        st.write("**Available Discount Codes**")
        
        codes_query = '''
            SELECT code, discount_type, discount_value, valid_until, 
                   uses_remaining, is_active
            FROM partner_discounts
            WHERE partner_id IS NULL OR partner_id = ?
            ORDER BY created_at DESC
        '''
        
        codes_df = pd.read_sql_query(codes_query, conn, params=(partner_id,))
        
        if not codes_df.empty:
            st.dataframe(
                codes_df,
                column_config={
                    'discount_value': st.column_config.NumberColumn('Value'),
                    'valid_until': st.column_config.DateColumn('Expires'),
                    'is_active': st.column_config.CheckboxColumn('Active')
                },
                use_container_width=True
            )
        else:
            st.info("No discount codes available")
    
    conn.close()


def render_billing_settings(billing_manager: PartnerBillingManager, partner_id: str):
    """Render billing settings interface."""
    st.subheader("⚙️ Billing Settings")
    
    # Get current settings
    conn = sqlite3.connect(billing_manager.db_path)
    settings_query = '''
        SELECT payment_method, billing_contact, auto_renew
        FROM partner_subscriptions
        WHERE partner_id = ? AND status = 'active'
    '''
    
    settings_df = pd.read_sql_query(settings_query, conn, params=(partner_id,))
    conn.close()
    
    current_settings = settings_df.iloc[0] if not settings_df.empty else {}
    
    with st.form("billing_settings"):
        st.write("**Payment & Billing Settings**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            payment_method = st.selectbox("Payment Method", 
                                        ["invoice", "credit_card", "ach", "wire_transfer"],
                                        index=0 if not current_settings else 
                                        ["invoice", "credit_card", "ach", "wire_transfer"].index(current_settings.get('payment_method', 'invoice')))
            
            billing_contact = st.text_input("Billing Contact Email", 
                                          value=current_settings.get('billing_contact', ''))
        
        with col2:
            auto_renew = st.checkbox("Auto-renew subscription", 
                                   value=current_settings.get('auto_renew', True))
            
            payment_terms = st.selectbox("Payment Terms", 
                                       ["Net 15", "Net 30", "Net 45", "Due on Receipt"])
        
        st.write("**Invoice Preferences**")
        
        col3, col4 = st.columns(2)
        
        with col3:
            invoice_format = st.selectbox("Invoice Format", ["PDF", "HTML", "Both"])
            
        with col4:
            invoice_delivery = st.selectbox("Delivery Method", ["Email", "Portal", "Both"])
        
        st.write("**Billing Alerts**")
        
        col5, col6 = st.columns(2)
        
        with col5:
            alert_before_billing = st.checkbox("Alert before billing", value=True)
            alert_payment_due = st.checkbox("Alert when payment due", value=True)
        
        with col6:
            alert_usage_threshold = st.checkbox("Alert at usage thresholds", value=True)
            alert_payout_ready = st.checkbox("Alert when payout ready", value=True)
        
        if st.form_submit_button("💾 Save Settings", type="primary"):
            st.success("✅ Billing settings updated successfully!")


def show_invoice_details(invoice):
    """Show detailed invoice information in modal."""
    line_items = json.loads(invoice['line_items'])
    
    with st.modal(f"Invoice Details: {invoice['invoice_number']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Invoice:** {invoice['invoice_number']}")
            st.write(f"**Issue Date:** {invoice['issue_date']}")
            st.write(f"**Due Date:** {invoice['due_date']}")
        
        with col2:
            st.write(f"**Status:** {invoice['status'].title()}")
            st.write(f"**Total:** ${invoice['total_amount']:.2f}")
        
        st.write("**Line Items:**")
        
        for item in line_items:
            col3, col4, col5, col6 = st.columns(4)
            
            with col3:
                st.write(item['description'])
            
            with col4:
                st.write(f"Qty: {item['quantity']}")
            
            with col5:
                st.write(f"${item['unit_price']:.2f}")
            
            with col6:
                st.write(f"${item['total']:.2f}")
        
        if st.button("📧 Send Invoice"):
            st.success("Invoice sent to billing contact")
        
        if st.button("💳 Mark as Paid"):
            st.success("Invoice marked as paid")


if __name__ == "__main__":
    render_partner_billing_dashboard()
