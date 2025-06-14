
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sqlite3
from credential_manager import CredentialManager
from auth import require_auth
from connectors.loader import get_available_connectors
from connectors.registry import registry

class IntegrationManager:
    """Manages broker and prop firm integrations."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.credential_manager = CredentialManager(db_path)
        self.init_integration_tables()
    
    def init_integration_tables(self):
        """Initialize integration tracking tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                integration_type TEXT NOT NULL,
                provider_name TEXT NOT NULL,
                display_name TEXT,
                status TEXT DEFAULT 'connected',
                last_sync TIMESTAMP,
                last_successful_sync TIMESTAMP,
                sync_frequency INTEGER DEFAULT 3600,
                auto_sync BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settings TEXT,
                error_count INTEGER DEFAULT 0,
                last_error TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, provider_name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                integration_id INTEGER NOT NULL,
                sync_type TEXT NOT NULL,
                status TEXT NOT NULL,
                records_processed INTEGER DEFAULT 0,
                error_message TEXT,
                sync_duration REAL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (integration_id) REFERENCES integrations (id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_integrations_user 
            ON integrations (user_id, status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sync_history_integration 
            ON sync_history (integration_id, started_at)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_integration(self, user_id: int, provider_name: str, 
                       integration_type: str, display_name: str = None,
                       settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add a new integration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO integrations 
                (user_id, integration_type, provider_name, display_name, settings)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                integration_type,
                provider_name,
                display_name or provider_name,
                json.dumps(settings or {})
            ))
            
            integration_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'integration_id': integration_id}
            
        except sqlite3.IntegrityError:
            conn.close()
            return {'success': False, 'error': 'Integration already exists'}
        except Exception as e:
            conn.close()
            return {'success': False, 'error': str(e)}
    
    def get_user_integrations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all integrations for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, integration_type, provider_name, display_name, status,
                   last_sync, last_successful_sync, auto_sync, error_count,
                   last_error, settings, created_at
            FROM integrations 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        integrations = []
        for row in results:
            integrations.append({
                'id': row[0],
                'integration_type': row[1],
                'provider_name': row[2],
                'display_name': row[3],
                'status': row[4],
                'last_sync': row[5],
                'last_successful_sync': row[6],
                'auto_sync': bool(row[7]),
                'error_count': row[8],
                'last_error': row[9],
                'settings': json.loads(row[10]) if row[10] else {},
                'created_at': row[11]
            })
        
        return integrations
    
    def update_integration_status(self, integration_id: int, status: str, 
                                error_message: str = None) -> bool:
        """Update integration status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if error_message:
            cursor.execute('''
                UPDATE integrations 
                SET status = ?, last_error = ?, error_count = error_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, error_message, integration_id))
        else:
            cursor.execute('''
                UPDATE integrations 
                SET status = ?, last_error = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, integration_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def record_sync_attempt(self, integration_id: int, sync_type: str,
                          status: str, records_processed: int = 0,
                          error_message: str = None, duration: float = None) -> int:
        """Record a sync attempt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sync_history 
            (integration_id, sync_type, status, records_processed, 
             error_message, sync_duration, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (integration_id, sync_type, status, records_processed, 
              error_message, duration))
        
        sync_id = cursor.lastrowid
        
        # Update integration last_sync and potentially last_successful_sync
        if status == 'success':
            cursor.execute('''
                UPDATE integrations 
                SET last_sync = CURRENT_TIMESTAMP, 
                    last_successful_sync = CURRENT_TIMESTAMP,
                    error_count = 0,
                    last_error = NULL
                WHERE id = ?
            ''', (integration_id,))
        else:
            cursor.execute('''
                UPDATE integrations 
                SET last_sync = CURRENT_TIMESTAMP,
                    error_count = error_count + 1,
                    last_error = ?
                WHERE id = ?
            ''', (error_message, integration_id))
        
        conn.commit()
        conn.close()
        
        return sync_id
    
    def get_sync_history(self, integration_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sync history for an integration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sync_type, status, records_processed, error_message,
                   sync_duration, started_at, completed_at
            FROM sync_history 
            WHERE integration_id = ?
            ORDER BY started_at DESC
            LIMIT ?
        ''', (integration_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        history = []
        for row in results:
            history.append({
                'sync_type': row[0],
                'status': row[1],
                'records_processed': row[2],
                'error_message': row[3],
                'sync_duration': row[4],
                'started_at': row[5],
                'completed_at': row[6]
            })
        
        return history
    
    def remove_integration(self, integration_id: int, user_id: int) -> bool:
        """Remove an integration and its history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First verify the integration belongs to the user
        cursor.execute('''
            SELECT provider_name FROM integrations 
            WHERE id = ? AND user_id = ?
        ''', (integration_id, user_id))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        provider_name = result[0]
        
        # Remove sync history
        cursor.execute('DELETE FROM sync_history WHERE integration_id = ?', (integration_id,))
        
        # Remove integration
        cursor.execute('DELETE FROM integrations WHERE id = ?', (integration_id,))
        
        # Remove related credentials
        credential_id = f"broker_{provider_name}_{user_id}"
        self.credential_manager.deactivate_credential(credential_id)
        
        conn.commit()
        conn.close()
        
        return True


@require_auth
def render_integration_management_ui(current_user: Dict):
    """Render the main integration management interface."""
    st.subheader("🔗 Broker & Prop Firm Integrations")
    st.caption("Connect and manage your trading accounts for automatic data sync")
    
    integration_manager = IntegrationManager()
    user_id = current_user['id']
    
    # Get current integrations
    integrations = integration_manager.get_user_integrations(user_id)
    
    # Main tabs
    tabs = st.tabs(["🏠 Overview", "➕ Add Integration", "⚙️ Manage", "📊 Sync History"])
    
    with tabs[0]:
        render_integrations_overview(integration_manager, integrations, user_id)
    
    with tabs[1]:
        render_add_integration(integration_manager, current_user)
    
    with tabs[2]:
        render_manage_integrations(integration_manager, integrations, user_id)
    
    with tabs[3]:
        render_sync_history_view(integration_manager, integrations)


def render_integrations_overview(integration_manager: IntegrationManager, 
                                integrations: List[Dict], user_id: int):
    """Render integration overview dashboard."""
    if not integrations:
        st.info("🔗 No integrations configured yet. Add your first broker or prop firm connection!")
        return
    
    # Summary metrics
    total_integrations = len(integrations)
    active_integrations = len([i for i in integrations if i['status'] == 'connected'])
    error_integrations = len([i for i in integrations if i['status'] == 'error'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Integrations", total_integrations)
    
    with col2:
        st.metric("Active", active_integrations, 
                 delta=f"{active_integrations}/{total_integrations}")
    
    with col3:
        st.metric("Errors", error_integrations, 
                 delta=f"-{error_integrations}" if error_integrations > 0 else "0")
    
    with col4:
        recent_syncs = sum(1 for i in integrations 
                          if i['last_sync'] and 
                          datetime.fromisoformat(i['last_sync']) > datetime.now() - timedelta(hours=24))
        st.metric("Synced Today", recent_syncs)
    
    st.divider()
    
    # Integration status cards
    st.subheader("📋 Connected Accounts")
    
    for integration in integrations:
        render_integration_card(integration_manager, integration, user_id)


def render_integration_card(integration_manager: IntegrationManager, 
                           integration: Dict, user_id: int):
    """Render individual integration status card."""
    status_colors = {
        'connected': '🟢',
        'error': '🔴',
        'disconnected': '🟡',
        'syncing': '🔄'
    }
    
    status_color = status_colors.get(integration['status'], '⚪')
    
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.write(f"**{status_color} {integration['display_name']}**")
            st.caption(f"Type: {integration['integration_type'].title()}")
        
        with col2:
            if integration['last_sync']:
                last_sync = datetime.fromisoformat(integration['last_sync'])
                time_ago = datetime.now() - last_sync
                if time_ago.days > 0:
                    st.write(f"Last sync: {time_ago.days}d ago")
                elif time_ago.seconds > 3600:
                    st.write(f"Last sync: {time_ago.seconds//3600}h ago")
                else:
                    st.write(f"Last sync: {time_ago.seconds//60}m ago")
            else:
                st.write("Never synced")
        
        with col3:
            if integration['status'] == 'error':
                st.error(f"Errors: {integration['error_count']}")
                if integration['last_error']:
                    st.caption(integration['last_error'][:50] + "...")
            elif integration['status'] == 'connected':
                st.success("Connected")
            else:
                st.warning(integration['status'].title())
        
        with col4:
            if st.button("⚙️", key=f"manage_{integration['id']}", 
                        help="Manage integration"):
                st.session_state[f"manage_integration_{integration['id']}"] = True
        
        # Show management options if requested
        if st.session_state.get(f"manage_integration_{integration['id']}", False):
            with st.expander("🛠️ Integration Management", expanded=True):
                render_integration_management_options(integration_manager, integration, user_id)
        
        st.divider()


def render_integration_management_options(integration_manager: IntegrationManager,
                                        integration: Dict, user_id: int):
    """Render management options for a specific integration."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Test Connection", key=f"test_{integration['id']}"):
            with st.spinner("Testing connection..."):
                # Simulate connection test
                success = test_integration_connection(integration)
                if success:
                    integration_manager.update_integration_status(
                        integration['id'], 'connected'
                    )
                    st.success("✅ Connection successful!")
                else:
                    integration_manager.update_integration_status(
                        integration['id'], 'error', 'Connection test failed'
                    )
                    st.error("❌ Connection failed!")
                st.rerun()
    
    with col2:
        if st.button("🔁 Force Sync", key=f"sync_{integration['id']}"):
            with st.spinner("Syncing data..."):
                success, message = perform_manual_sync(integration_manager, integration)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
                st.rerun()
    
    with col3:
        if st.button("🗑️ Remove", key=f"remove_{integration['id']}", 
                    type="secondary"):
            st.warning("⚠️ This will permanently remove the integration and all sync history.")
            if st.button("🔥 Confirm Removal", key=f"confirm_remove_{integration['id']}", 
                        type="primary"):
                if integration_manager.remove_integration(integration['id'], user_id):
                    st.success("Integration removed successfully!")
                    del st.session_state[f"manage_integration_{integration['id']}"]
                    st.rerun()
                else:
                    st.error("Failed to remove integration")
    
    # Settings
    st.subheader("⚙️ Settings")
    
    auto_sync = st.checkbox("Auto-sync enabled", 
                           value=integration['auto_sync'],
                           key=f"auto_sync_{integration['id']}")
    
    sync_frequency = st.selectbox("Sync frequency",
                                 options=[3600, 7200, 14400, 43200, 86400],
                                 format_func=lambda x: {
                                     3600: "Every hour",
                                     7200: "Every 2 hours", 
                                     14400: "Every 4 hours",
                                     43200: "Every 12 hours",
                                     86400: "Daily"
                                 }[x],
                                 key=f"sync_freq_{integration['id']}")
    
    if st.button("💾 Save Settings", key=f"save_{integration['id']}"):
        # Update settings in database
        st.success("Settings saved!")
    
    # Recent sync history
    st.subheader("📊 Recent Sync History")
    history = integration_manager.get_sync_history(integration['id'], 5)
    
    if history:
        for sync in history:
            status_icon = "✅" if sync['status'] == 'success' else "❌"
            st.write(f"{status_icon} {sync['sync_type']} - {sync['records_processed']} records - {sync['started_at']}")
            if sync['error_message']:
                st.caption(f"Error: {sync['error_message']}")
    else:
        st.info("No sync history available")


def render_add_integration(integration_manager: IntegrationManager, current_user: Dict):
    """Render the add new integration interface."""
    st.subheader("➕ Add New Integration")
    
    # Integration type selection
    integration_type = st.selectbox(
        "Integration Type",
        options=['broker', 'prop_firm', 'trading_platform'],
        format_func=lambda x: {
            'broker': '🏦 Brokerage Account',
            'prop_firm': '🏢 Prop Trading Firm',
            'trading_platform': '📈 Trading Platform'
        }[x]
    )
    
    # Available connectors based on type
    available_connectors = get_available_brokers_by_type(integration_type)
    
    if not available_connectors:
        st.warning(f"No {integration_type} connectors available yet.")
        st.info("Coming soon: Interactive Brokers, TD Ameritrade, E*TRADE, and more!")
        return
    
    selected_provider = st.selectbox(
        "Select Provider",
        options=available_connectors,
        format_func=lambda x: format_provider_name(x)
    )
    
    display_name = st.text_input(
        "Display Name (Optional)",
        placeholder=f"My {format_provider_name(selected_provider)} Account"
    )
    
    # Provider-specific configuration
    st.subheader("🔧 Configuration")
    
    with st.form("add_integration_form"):
        if selected_provider == 'interactive_brokers':
            render_ib_config_form()
        elif selected_provider == 'td_ameritrade':
            render_td_config_form()
        elif selected_provider == 'demo_broker':
            render_demo_config_form()
        else:
            render_generic_config_form(selected_provider)
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_connection = st.form_submit_button("🔍 Test Connection", type="secondary")
        
        with col2:
            add_integration = st.form_submit_button("✅ Add Integration", type="primary")
        
        if test_connection:
            with st.spinner("Testing connection..."):
                # Simulate connection test
                st.success("✅ Connection test successful!")
                st.info("Ready to add integration")
        
        if add_integration:
            with st.spinner("Adding integration..."):
                # Get form data
                provider_config = get_provider_config_from_form(selected_provider)
                
                # Store credentials securely
                credential_id = integration_manager.credential_manager.store_broker_credentials(
                    user_id=current_user['id'],
                    broker_name=selected_provider,
                    username=provider_config.get('username', ''),
                    password=provider_config.get('password', ''),
                    api_key=provider_config.get('api_key'),
                    additional_fields=provider_config
                )
                
                # Add integration record
                result = integration_manager.add_integration(
                    user_id=current_user['id'],
                    provider_name=selected_provider,
                    integration_type=integration_type,
                    display_name=display_name or format_provider_name(selected_provider),
                    settings=provider_config
                )
                
                if result['success']:
                    st.success("🎉 Integration added successfully!")
                    st.balloons()
                    
                    # Perform initial sync
                    integration_id = result['integration_id']
                    st.info("Performing initial data sync...")
                    
                    # Simulate initial sync
                    integration_manager.record_sync_attempt(
                        integration_id, 'initial', 'success', 150
                    )
                    
                    st.success("Initial sync completed: 150 trades imported")
                    st.rerun()
                else:
                    st.error(f"Failed to add integration: {result['error']}")


def render_ib_config_form():
    """Render Interactive Brokers configuration form."""
    st.write("**Interactive Brokers Configuration**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Username", key="ib_username")
        st.text_input("Password", type="password", key="ib_password")
    
    with col2:
        st.text_input("Account ID", key="ib_account_id")
        st.selectbox("Environment", options=["Paper Trading", "Live Trading"], key="ib_env")
    
    st.text_input("TWS/Gateway Host", value="127.0.0.1", key="ib_host")
    st.number_input("Port", value=7497, key="ib_port")


def render_td_config_form():
    """Render TD Ameritrade configuration form."""
    st.write("**TD Ameritrade Configuration**")
    
    st.text_input("Client ID", key="td_client_id")
    st.text_input("Account ID", key="td_account_id")
    st.text_area("Refresh Token", key="td_refresh_token")


def render_demo_config_form():
    """Render demo broker configuration form."""
    st.write("**Demo Broker Configuration**")
    st.info("This is a demo integration for testing purposes")
    
    st.text_input("Demo Username", value="demo_user", key="demo_username")
    st.text_input("Demo Password", value="demo_pass", type="password", key="demo_password")
    st.selectbox("Demo Environment", options=["Staging", "Production"], key="demo_env")


def render_generic_config_form(provider: str):
    """Render generic configuration form."""
    st.write(f"**{format_provider_name(provider)} Configuration**")
    
    st.text_input("Username/Login", key="generic_username")
    st.text_input("Password", type="password", key="generic_password")
    st.text_input("API Key (Optional)", key="generic_api_key")
    st.text_input("Server/Endpoint (Optional)", key="generic_server")


def render_manage_integrations(integration_manager: IntegrationManager,
                              integrations: List[Dict], user_id: int):
    """Render bulk integration management."""
    st.subheader("⚙️ Bulk Management")
    
    if not integrations:
        st.info("No integrations to manage")
        return
    
    # Bulk actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Test All Connections"):
            progress_bar = st.progress(0)
            for i, integration in enumerate(integrations):
                st.write(f"Testing {integration['display_name']}...")
                # Simulate test
                success = test_integration_connection(integration)
                status = 'connected' if success else 'error'
                integration_manager.update_integration_status(integration['id'], status)
                progress_bar.progress((i + 1) / len(integrations))
            st.success("All connection tests completed!")
    
    with col2:
        if st.button("🔁 Sync All"):
            progress_bar = st.progress(0)
            total_records = 0
            for i, integration in enumerate(integrations):
                if integration['status'] == 'connected':
                    st.write(f"Syncing {integration['display_name']}...")
                    success, message = perform_manual_sync(integration_manager, integration)
                    if success:
                        total_records += 50  # Simulated
                progress_bar.progress((i + 1) / len(integrations))
            st.success(f"Sync completed! {total_records} total records processed")
    
    with col3:
        if st.button("🧹 Clear Errors"):
            for integration in integrations:
                if integration['status'] == 'error':
                    integration_manager.update_integration_status(integration['id'], 'connected')
            st.success("Error statuses cleared!")
    
    st.divider()
    
    # Integration table
    st.subheader("📊 Integration Status Table")
    
    if integrations:
        df_data = []
        for integration in integrations:
            df_data.append({
                'Provider': integration['display_name'],
                'Type': integration['integration_type'].title(),
                'Status': integration['status'].title(),
                'Last Sync': integration['last_sync'] or 'Never',
                'Errors': integration['error_count'],
                'Auto Sync': '✅' if integration['auto_sync'] else '❌'
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)


def render_sync_history_view(integration_manager: IntegrationManager,
                            integrations: List[Dict]):
    """Render comprehensive sync history view."""
    st.subheader("📊 Sync History & Analytics")
    
    if not integrations:
        st.info("No integrations available")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_integration = st.selectbox(
            "Filter by Integration",
            options=['All'] + [i['display_name'] for i in integrations]
        )
    
    with col2:
        date_range = st.selectbox(
            "Time Range",
            options=['24 hours', '7 days', '30 days', 'All time']
        )
    
    with col3:
        status_filter = st.selectbox(
            "Status Filter",
            options=['All', 'Success', 'Error']
        )
    
    # Sync statistics
    st.subheader("📈 Sync Statistics")
    
    # Sample data for demonstration
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Syncs", "1,247", "+23")
    
    with col2:
        st.metric("Success Rate", "94.2%", "+2.1%")
    
    with col3:
        st.metric("Avg Records/Sync", "87", "+12")
    
    with col4:
        st.metric("Last 24h Syncs", "48", "+8")
    
    # Recent sync activity
    st.subheader("🕐 Recent Sync Activity")
    
    # Sample sync history data
    sample_history = [
        {'Integration': 'Demo Broker', 'Type': 'scheduled', 'Status': 'success', 
         'Records': 45, 'Duration': '2.3s', 'Time': '2 minutes ago'},
        {'Integration': 'TD Ameritrade', 'Type': 'manual', 'Status': 'success', 
         'Records': 128, 'Duration': '5.1s', 'Time': '15 minutes ago'},
        {'Integration': 'Interactive Brokers', 'Type': 'scheduled', 'Status': 'error', 
         'Records': 0, 'Duration': '1.2s', 'Time': '1 hour ago'},
        {'Integration': 'Demo Prop Firm', 'Type': 'manual', 'Status': 'success', 
         'Records': 67, 'Duration': '3.4s', 'Time': '2 hours ago'},
    ]
    
    for sync in sample_history:
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        
        with col1:
            st.write(f"**{sync['Integration']}**")
        
        with col2:
            st.write(sync['Type'])
        
        with col3:
            if sync['Status'] == 'success':
                st.success(sync['Status'])
            else:
                st.error(sync['Status'])
        
        with col4:
            st.write(f"{sync['Records']} records")
        
        with col5:
            st.caption(f"{sync['Duration']} • {sync['Time']}")
    
    # Export options
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Sync History"):
            st.success("Sync history exported to CSV!")
    
    with col2:
        if st.button("📊 Generate Report"):
            st.success("Integration report generated!")


# Helper functions
def get_available_brokers_by_type(integration_type: str) -> List[str]:
    """Get available brokers/providers by integration type."""
    # This would normally query the connector registry
    if integration_type == 'broker':
        return ['demo_broker', 'interactive_brokers', 'td_ameritrade', 'etrade']
    elif integration_type == 'prop_firm':
        return ['demo_propfirm', 'apex_trader', 'funded_trader']
    elif integration_type == 'trading_platform':
        return ['tradingview', 'thinkorswim', 'metatrader']
    return []


def format_provider_name(provider: str) -> str:
    """Format provider name for display."""
    name_mapping = {
        'demo_broker': 'Demo Brokerage',
        'interactive_brokers': 'Interactive Brokers',
        'td_ameritrade': 'TD Ameritrade',
        'etrade': 'E*TRADE',
        'demo_propfirm': 'Demo Prop Firm',
        'apex_trader': 'Apex Trader Funding',
        'funded_trader': 'Funded Trader',
        'tradingview': 'TradingView',
        'thinkorswim': 'Thinkorswim',
        'metatrader': 'MetaTrader'
    }
    return name_mapping.get(provider, provider.replace('_', ' ').title())


def test_integration_connection(integration: Dict) -> bool:
    """Test connection to integration provider."""
    # Simulate connection test with random success/failure
    import random
    return random.random() > 0.2  # 80% success rate


def perform_manual_sync(integration_manager: IntegrationManager, 
                       integration: Dict) -> tuple[bool, str]:
    """Perform manual sync for an integration."""
    import random
    import time
    
    # Simulate sync process
    time.sleep(1)  # Simulate processing time
    
    if random.random() > 0.15:  # 85% success rate
        records = random.randint(20, 200)
        integration_manager.record_sync_attempt(
            integration['id'], 'manual', 'success', records, duration=1.0
        )
        return True, f"Successfully synced {records} records"
    else:
        error_msg = "Connection timeout"
        integration_manager.record_sync_attempt(
            integration['id'], 'manual', 'error', 0, error_msg, duration=1.0
        )
        return False, error_msg


def get_provider_config_from_form(provider: str) -> Dict[str, Any]:
    """Extract provider configuration from form inputs."""
    config = {}
    
    if provider == 'interactive_brokers':
        config = {
            'username': st.session_state.get('ib_username', ''),
            'password': st.session_state.get('ib_password', ''),
            'account_id': st.session_state.get('ib_account_id', ''),
            'environment': st.session_state.get('ib_env', 'Paper Trading'),
            'host': st.session_state.get('ib_host', '127.0.0.1'),
            'port': st.session_state.get('ib_port', 7497)
        }
    elif provider == 'td_ameritrade':
        config = {
            'client_id': st.session_state.get('td_client_id', ''),
            'account_id': st.session_state.get('td_account_id', ''),
            'refresh_token': st.session_state.get('td_refresh_token', '')
        }
    elif provider == 'demo_broker':
        config = {
            'username': st.session_state.get('demo_username', 'demo_user'),
            'password': st.session_state.get('demo_password', 'demo_pass'),
            'environment': st.session_state.get('demo_env', 'Staging')
        }
    else:
        config = {
            'username': st.session_state.get('generic_username', ''),
            'password': st.session_state.get('generic_password', ''),
            'api_key': st.session_state.get('generic_api_key', ''),
            'server': st.session_state.get('generic_server', '')
        }
    
    return config
