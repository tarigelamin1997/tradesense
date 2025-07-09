
import streamlit as st
import pandas as pd
import json
import sqlite3
import secrets
import csv
import io
from typing import Dict, List, Optional
from datetime import datetime
from auth import AuthManager, AuthDatabase
from partner_portal import PartnerPortalManager
from logging_manager import log_info, log_error, LogCategory

class BulkProvisioningManager:
    """Manages bulk user account provisioning for partners."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()
        self.portal_manager = PartnerPortalManager()
        self.init_bulk_tables()
    
    def init_bulk_tables(self):
        """Initialize bulk provisioning tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bulk provisioning jobs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bulk_provisioning_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                job_name TEXT NOT NULL,
                total_accounts INTEGER DEFAULT 0,
                successful_accounts INTEGER DEFAULT 0,
                failed_accounts INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_log TEXT,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Bulk account results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bulk_account_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                user_id INTEGER,
                status TEXT NOT NULL,
                error_message TEXT,
                credentials JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES bulk_provisioning_jobs (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Partner account templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_account_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                template_name TEXT NOT NULL,
                default_role TEXT DEFAULT 'user',
                default_subscription TEXT DEFAULT 'free',
                email_domain_restriction TEXT,
                auto_generated_passwords BOOLEAN DEFAULT TRUE,
                welcome_email_template TEXT,
                custom_settings JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_bulk_job(self, partner_id: str, job_name: str, 
                       accounts_data: List[Dict], created_by: str) -> Dict:
        """Create a new bulk provisioning job."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create job record
            cursor.execute('''
                INSERT INTO bulk_provisioning_jobs 
                (partner_id, job_name, total_accounts, created_by)
                VALUES (?, ?, ?, ?)
            ''', (partner_id, job_name, len(accounts_data), created_by))
            
            job_id = cursor.lastrowid
            
            # Process accounts
            successful = 0
            failed = 0
            results = []
            
            for account in accounts_data:
                result = self.create_single_account(partner_id, account)
                
                if result['success']:
                    successful += 1
                    cursor.execute('''
                        INSERT INTO bulk_account_results 
                        (job_id, email, user_id, status, credentials)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (job_id, account['email'], result['user_id'], 'success',
                          json.dumps(result['credentials'])))
                else:
                    failed += 1
                    cursor.execute('''
                        INSERT INTO bulk_account_results 
                        (job_id, email, status, error_message)
                        VALUES (?, ?, ?, ?)
                    ''', (job_id, account['email'], 'failed', result['error']))
                
                results.append(result)
            
            # Update job status
            cursor.execute('''
                UPDATE bulk_provisioning_jobs 
                SET successful_accounts = ?, failed_accounts = ?, 
                    status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (successful, failed, job_id))
            
            conn.commit()
            
            log_info(f"Bulk provisioning job completed: {successful} success, {failed} failed",
                    category=LogCategory.SYSTEM, partner_id=partner_id)
            
            return {
                'success': True,
                'job_id': job_id,
                'successful': successful,
                'failed': failed,
                'results': results
            }
            
        except Exception as e:
            conn.rollback()
            log_error(f"Bulk provisioning failed: {str(e)}", 
                     category=LogCategory.SYSTEM, partner_id=partner_id)
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def create_single_account(self, partner_id: str, account_data: Dict) -> Dict:
        """Create a single user account."""
        try:
            email = account_data['email']
            first_name = account_data.get('first_name', '')
            last_name = account_data.get('last_name', '')
            role = account_data.get('role', 'user')
            
            # Generate password if not provided
            password = account_data.get('password')
            if not password:
                password = self.generate_secure_password()
            
            # Create user account
            result = self.auth_manager.db.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                partner_id=partner_id
            )
            
            if result['success']:
                return {
                    'success': True,
                    'user_id': result['user_id'],
                    'credentials': {
                        'email': email,
                        'password': password,
                        'api_key': result['api_key']
                    }
                }
            else:
                return {'success': False, 'error': result['error']}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_secure_password(self, length: int = 12) -> str:
        """Generate a secure password."""
        import string
        import random
        
        # Ensure password has variety
        chars = string.ascii_letters + string.digits + "!@#$%&*"
        password = ''.join(random.choice(chars) for _ in range(length))
        
        # Ensure at least one of each type
        if not any(c.isupper() for c in password):
            password = password[:-1] + random.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-1] + random.choice(string.ascii_lowercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + random.choice(string.digits)
        
        return password
    
    def get_job_status(self, job_id: int) -> Dict:
        """Get status of a bulk provisioning job."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM bulk_provisioning_jobs WHERE id = ?
        ''', (job_id,))
        
        job = cursor.fetchone()
        
        if job:
            cursor.execute('''
                SELECT email, status, error_message, credentials
                FROM bulk_account_results WHERE job_id = ?
            ''', (job_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            return {
                'job_id': job[0],
                'partner_id': job[1],
                'job_name': job[2],
                'total_accounts': job[3],
                'successful_accounts': job[4],
                'failed_accounts': job[5],
                'status': job[6],
                'created_at': job[8],
                'completed_at': job[9],
                'results': [
                    {
                        'email': r[0],
                        'status': r[1],
                        'error': r[2],
                        'credentials': json.loads(r[3]) if r[3] else None
                    }
                    for r in results
                ]
            }
        
        conn.close()
        return None
    
    def export_credentials(self, job_id: int) -> str:
        """Export credentials as CSV for download."""
        job_status = self.get_job_status(job_id)
        
        if not job_status:
            return None
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Email', 'Password', 'API Key', 'Status', 'Login URL'])
        
        # Data
        for result in job_status['results']:
            if result['status'] == 'success' and result['credentials']:
                creds = result['credentials']
                writer.writerow([
                    creds['email'],
                    creds['password'],
                    creds['api_key'],
                    'Active',
                    'https://your-app.replit.dev/login'
                ])
        
        return output.getvalue()


def render_bulk_provisioning_ui(partner_id: str):
    """Render the bulk provisioning interface."""
    st.subheader("👥 Bulk Account Provisioning")
    st.caption("Create multiple user accounts at once for fast onboarding")
    
    bulk_manager = BulkProvisioningManager()
    
    tabs = st.tabs(["📤 Create Accounts", "📊 Job History", "⚙️ Templates"])
    
    with tabs[0]:
        render_bulk_creation_ui(bulk_manager, partner_id)
    
    with tabs[1]:
        render_job_history_ui(bulk_manager, partner_id)
    
    with tabs[2]:
        render_templates_ui(bulk_manager, partner_id)


def render_bulk_creation_ui(bulk_manager: BulkProvisioningManager, partner_id: str):
    """Render bulk account creation interface."""
    st.subheader("📤 Create Multiple Accounts")
    
    # Method selection
    creation_method = st.radio(
        "Choose creation method:",
        options=['manual_entry', 'csv_upload', 'email_list'],
        format_func=lambda x: {
            'manual_entry': '✏️ Manual Entry',
            'csv_upload': '📁 CSV Upload',
            'email_list': '📧 Email List'
        }[x]
    )
    
    accounts_data = []
    
    if creation_method == 'manual_entry':
        accounts_data = render_manual_entry()
    elif creation_method == 'csv_upload':
        accounts_data = render_csv_upload()
    elif creation_method == 'email_list':
        accounts_data = render_email_list()
    
    if accounts_data:
        st.subheader("👀 Preview Accounts")
        
        # Show preview
        df = pd.DataFrame(accounts_data)
        st.dataframe(df, use_container_width=True)
        
        # Configuration options
        col1, col2 = st.columns(2)
        
        with col1:
            job_name = st.text_input("Job Name", value=f"Bulk Import {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            auto_passwords = st.checkbox("Auto-generate passwords", value=True)
            
        with col2:
            default_role = st.selectbox("Default Role", options=['user', 'admin'], index=0)
            send_welcome = st.checkbox("Send welcome emails", value=True)
        
        # Update accounts with settings
        for account in accounts_data:
            if 'role' not in account:
                account['role'] = default_role
            if auto_passwords and 'password' not in account:
                account['password'] = None  # Will be auto-generated
        
        # Create accounts button
        if st.button("🚀 Create All Accounts", type="primary"):
            with st.spinner("Creating accounts..."):
                result = bulk_manager.create_bulk_job(
                    partner_id=partner_id,
                    job_name=job_name,
                    accounts_data=accounts_data,
                    created_by=st.session_state.get('current_user', {}).get('email', 'system')
                )
                
                if result['success']:
                    st.success(f"✅ Bulk provisioning completed!")
                    st.success(f"Successfully created: {result['successful']} accounts")
                    if result['failed'] > 0:
                        st.warning(f"Failed to create: {result['failed']} accounts")
                    
                    # Show download credentials option
                    if st.button("📥 Download Credentials CSV"):
                        csv_data = bulk_manager.export_credentials(result['job_id'])
                        if csv_data:
                            st.download_button(
                                label="💾 Download Credentials",
                                data=csv_data,
                                file_name=f"credentials_{job_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                else:
                    st.error(f"❌ Bulk provisioning failed: {result['error']}")


def render_manual_entry():
    """Render manual account entry interface."""
    st.write("**Manual Account Entry**")
    
    accounts = []
    
    # Dynamic account entry
    if 'manual_accounts' not in st.session_state:
        st.session_state.manual_accounts = [{}]
    
    for i, account in enumerate(st.session_state.manual_accounts):
        with st.container():
            st.write(f"**Account {i + 1}**")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                email = st.text_input(f"Email", key=f"email_{i}", value=account.get('email', ''))
            
            with col2:
                first_name = st.text_input(f"First Name", key=f"fname_{i}", value=account.get('first_name', ''))
            
            with col3:
                last_name = st.text_input(f"Last Name", key=f"lname_{i}", value=account.get('last_name', ''))
            
            if email:
                accounts.append({
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name
                })
        
        st.divider()
    
    # Add/Remove buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("➕ Add Another Account"):
            st.session_state.manual_accounts.append({})
            st.rerun()
    
    with col2:
        if len(st.session_state.manual_accounts) > 1:
            if st.button("➖ Remove Last Account"):
                st.session_state.manual_accounts.pop()
                st.rerun()
    
    return accounts


def render_csv_upload():
    """Render CSV upload interface."""
    st.write("**CSV Upload**")
    
    # Show expected format
    st.info("""
    **Expected CSV format:**
    - Required columns: email
    - Optional columns: first_name, last_name, role, password
    - First row should contain column headers
    """)
    
    # Sample CSV download
    sample_csv = """email,first_name,last_name,role
trader1@company.com,John,Smith,user
trader2@company.com,Jane,Doe,user
admin@company.com,Admin,User,admin"""
    
    st.download_button(
        "📥 Download Sample CSV",
        data=sample_csv,
        file_name="sample_accounts.csv",
        mime="text/csv"
    )
    
    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            if 'email' not in df.columns:
                st.error("❌ CSV must contain 'email' column")
                return []
            
            # Show preview
            st.write("**Preview:**")
            st.dataframe(df.head(), use_container_width=True)
            
            # Convert to list of dicts
            accounts = df.to_dict('records')
            
            # Clean up NaN values
            for account in accounts:
                for key, value in account.items():
                    if pd.isna(value):
                        account[key] = ''
            
            st.success(f"✅ Loaded {len(accounts)} accounts from CSV")
            return accounts
            
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")
            return []
    
    return []


def render_email_list():
    """Render email list interface."""
    st.write("**Email List**")
    
    email_text = st.text_area(
        "Enter email addresses (one per line):",
        height=200,
        placeholder="trader1@company.com\ntrader2@company.com\nadmin@company.com"
    )
    
    if email_text:
        emails = [email.strip() for email in email_text.split('\n') if email.strip()]
        
        accounts = []
        for email in emails:
            # Extract name from email if possible
            username = email.split('@')[0]
            name_parts = username.replace('.', ' ').replace('_', ' ').split()
            
            first_name = name_parts[0].title() if name_parts else ''
            last_name = name_parts[1].title() if len(name_parts) > 1 else ''
            
            accounts.append({
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            })
        
        st.success(f"✅ Parsed {len(accounts)} email addresses")
        return accounts
    
    return []


def render_job_history_ui(bulk_manager: BulkProvisioningManager, partner_id: str):
    """Render job history interface."""
    st.subheader("📊 Provisioning Job History")
    
    # Get job history (simulated)
    conn = sqlite3.connect(bulk_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, job_name, total_accounts, successful_accounts, 
               failed_accounts, status, created_at, completed_at
        FROM bulk_provisioning_jobs 
        WHERE partner_id = ?
        ORDER BY created_at DESC
    ''', (partner_id,))
    
    jobs = cursor.fetchall()
    conn.close()
    
    if jobs:
        for job in jobs:
            job_id, name, total, success, failed, status, created, completed = job
            
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{name}**")
                    st.caption(f"Created: {created}")
                
                with col2:
                    st.metric("Total", total)
                
                with col3:
                    st.metric("Success", success, delta=f"+{success}")
                
                with col4:
                    if failed > 0:
                        st.metric("Failed", failed, delta=f"+{failed}")
                    else:
                        st.metric("Failed", failed)
                
                # Action buttons
                col5, col6, col7 = st.columns(3)
                
                with col5:
                    if st.button("📋 View Details", key=f"details_{job_id}"):
                        show_job_details(bulk_manager, job_id)
                
                with col6:
                    if st.button("📥 Download Credentials", key=f"download_{job_id}"):
                        csv_data = bulk_manager.export_credentials(job_id)
                        if csv_data:
                            st.download_button(
                                label="💾 Download",
                                data=csv_data,
                                file_name=f"credentials_{name}_{job_id}.csv",
                                mime="text/csv",
                                key=f"dl_btn_{job_id}"
                            )
                
                with col7:
                    if status == 'completed':
                        st.success("✅ Completed")
                    else:
                        st.info("🔄 Processing")
            
            st.divider()
    else:
        st.info("No bulk provisioning jobs found.")


def show_job_details(bulk_manager: BulkProvisioningManager, job_id: int):
    """Show detailed job results."""
    job_status = bulk_manager.get_job_status(job_id)
    
    if job_status:
        with st.modal(f"Job Details: {job_status['job_name']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Accounts", job_status['total_accounts'])
            
            with col2:
                st.metric("Successful", job_status['successful_accounts'])
            
            with col3:
                st.metric("Failed", job_status['failed_accounts'])
            
            # Results table
            st.subheader("Account Results")
            
            results_data = []
            for result in job_status['results']:
                results_data.append({
                    'Email': result['email'],
                    'Status': '✅ Success' if result['status'] == 'success' else '❌ Failed',
                    'Error': result.get('error', '-') if result['status'] == 'failed' else '-'
                })
            
            if results_data:
                df = pd.DataFrame(results_data)
                st.dataframe(df, use_container_width=True)


def render_templates_ui(bulk_manager: BulkProvisioningManager, partner_id: str):
    """Render account templates interface."""
    st.subheader("⚙️ Account Templates")
    st.caption("Create reusable templates for bulk account creation")
    
    # Create new template
    with st.expander("➕ Create New Template"):
        with st.form("create_template"):
            template_name = st.text_input("Template Name")
            
            col1, col2 = st.columns(2)
            
            with col1:
                default_role = st.selectbox("Default Role", options=['user', 'admin'])
                default_subscription = st.selectbox("Default Subscription", options=['free', 'pro', 'enterprise'])
            
            with col2:
                email_domain = st.text_input("Email Domain Restriction (optional)", placeholder="@company.com")
                auto_passwords = st.checkbox("Auto-generate passwords", value=True)
            
            welcome_template = st.text_area(
                "Welcome Email Template",
                value="Welcome to our trading platform! Your account has been created.",
                height=100
            )
            
            if st.form_submit_button("💾 Save Template"):
                st.success(f"✅ Template '{template_name}' saved successfully!")
    
    # Show existing templates (simulated)
    st.subheader("📋 Existing Templates")
    
    sample_templates = [
        {'name': 'Standard Trader', 'role': 'user', 'accounts_created': 127},
        {'name': 'Admin Users', 'role': 'admin', 'accounts_created': 5},
        {'name': 'Demo Accounts', 'role': 'user', 'accounts_created': 89}
    ]
    
    for template in sample_templates:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{template['name']}**")
            
            with col2:
                st.write(f"Role: {template['role']}")
            
            with col3:
                st.metric("Used", template['accounts_created'])
            
            with col4:
                if st.button("🗑️ Delete", key=f"del_template_{template['name']}"):
                    st.success("Template deleted!")
        
        st.divider()


# API endpoint for programmatic bulk provisioning
def bulk_provisioning_api_endpoint():
    """API endpoint for bulk provisioning (for integration)."""
    # This would be implemented as a REST API endpoint
    # Example usage in the partner's system:
    api_example = """
    # POST /api/v1/partner/bulk-provision
    {
        "job_name": "Q1 Trader Onboarding",
        "accounts": [
            {
                "email": "trader1@company.com",
                "first_name": "John",
                "last_name": "Smith",
                "role": "user"
            },
            {
                "email": "trader2@company.com", 
                "first_name": "Jane",
                "last_name": "Doe",
                "role": "user"
            }
        ],
        "settings": {
            "auto_generate_passwords": true,
            "send_welcome_emails": true,
            "default_subscription": "free"
        }
    }
    
    # Response
    {
        "success": true,
        "job_id": 12345,
        "total_accounts": 2,
        "successful_accounts": 2,
        "failed_accounts": 0,
        "credentials_download_url": "/api/v1/partner/jobs/12345/credentials"
    }
    """
    
    return api_example


if __name__ == "__main__":
    # Demo the bulk provisioning interface
    st.set_page_config(page_title="Bulk Provisioning Demo", layout="wide")
    
    # Simulate partner authentication
    partner_id = "demo_partner"
    render_bulk_provisioning_ui(partner_id)
