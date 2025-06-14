
import streamlit as st
from auth import AuthManager
from partner_management import PartnerManager

def setup_partner_demo():
    """Set up demo partners for testing."""
    auth_manager = AuthManager()
    
    # Create demo partners
    demo_partners = [
        {
            'partner_id': 'demo_broker',
            'name': 'Demo Brokerage',
            'type': 'broker',
            'contact_email': 'admin@demobroker.com',
            'settings': {
                'commission_rate': 3.50,
                'platform': 'TradingPlatform Pro',
                'custom_logo': 'https://via.placeholder.com/200x50?text=Demo+Broker'
            }
        },
        {
            'partner_id': 'demo_propfirm',
            'name': 'Elite Prop Trading',
            'type': 'prop_firm',
            'contact_email': 'admin@eliteprop.com',
            'settings': {
                'daily_loss_limit': 1000,
                'max_drawdown': 5000,
                'profit_target': 10000,
                'custom_logo': 'https://via.placeholder.com/200x50?text=Elite+Prop'
            }
        },
        {
            'partner_id': 'demo_trading_group',
            'name': 'Alpha Trading Group',
            'type': 'trading_group',
            'contact_email': 'admin@alphagroup.com',
            'settings': {
                'member_count': 45,
                'group_performance': 12.5,
                'custom_logo': 'https://via.placeholder.com/200x50?text=Alpha+Group'
            }
        }
    ]
    
    for partner in demo_partners:
        result = auth_manager.db.create_partner(
            partner_id=partner['partner_id'],
            name=partner['name'],
            partner_type=partner['type'],
            contact_email=partner['contact_email'],
            settings=partner['settings']
        )
        
        if result['success']:
            st.success(f"✅ Created partner: {partner['name']} (API Key: {result['api_key'][:20]}...)")
        else:
            st.warning(f"⚠️ Partner {partner['name']} already exists")

def render_partner_onboarding():
    """Render partner onboarding interface."""
    st.title("🤝 Partner Onboarding")
    st.caption("Integrate your brokerage, prop firm, or trading group with TradeSense")
    
    # Demo setup button
    if st.button("🚀 Setup Demo Partners"):
        setup_partner_demo()
    
    st.divider()
    
    # Partner type selection
    partner_type = st.selectbox(
        "Partner Type",
        options=['broker', 'prop_firm', 'trading_group'],
        format_func=lambda x: {
            'broker': '🏦 Brokerage',
            'prop_firm': '🏢 Prop Trading Firm',
            'trading_group': '👥 Trading Group'
        }[x]
    )
    
    # Partner registration form
    with st.form("partner_registration"):
        st.subheader(f"Register as {partner_type.replace('_', ' ').title()}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            partner_id = st.text_input("Partner ID", help="Unique identifier for your organization")
            partner_name = st.text_input("Organization Name")
            contact_email = st.text_input("Contact Email")
        
        with col2:
            if partner_type == 'broker':
                commission_rate = st.number_input("Commission Rate ($)", value=3.50, step=0.25)
                platform = st.text_input("Trading Platform", value="Custom Platform")
                
            elif partner_type == 'prop_firm':
                daily_loss_limit = st.number_input("Daily Loss Limit ($)", value=1000.0, step=100.0)
                max_drawdown = st.number_input("Max Drawdown ($)", value=5000.0, step=500.0)
                profit_target = st.number_input("Profit Target ($)", value=10000.0, step=1000.0)
                
            elif partner_type == 'trading_group':
                member_count = st.number_input("Initial Member Count", value=1, step=1)
                group_type = st.selectbox("Group Type", ["Educational", "Signal Provider", "Community"])
        
        custom_logo = st.text_input("Custom Logo URL (Optional)")
        webhook_url = st.text_input("Webhook URL (Optional)", help="For real-time notifications")
        
        if st.form_submit_button("🔗 Register Partner", type="primary"):
            if partner_id and partner_name and contact_email:
                auth_manager = AuthManager()
                
                # Build settings based on partner type
                settings = {'custom_logo': custom_logo} if custom_logo else {}
                
                if partner_type == 'broker':
                    settings.update({
                        'commission_rate': commission_rate,
                        'platform': platform
                    })
                elif partner_type == 'prop_firm':
                    settings.update({
                        'daily_loss_limit': daily_loss_limit,
                        'max_drawdown': max_drawdown,
                        'profit_target': profit_target
                    })
                elif partner_type == 'trading_group':
                    settings.update({
                        'member_count': member_count,
                        'group_type': group_type
                    })
                
                result = auth_manager.db.create_partner(
                    partner_id=partner_id,
                    name=partner_name,
                    partner_type=partner_type,
                    contact_email=contact_email,
                    settings=settings
                )
                
                if result['success']:
                    st.success("🎉 Partner registration successful!")
                    st.success(f"**API Key:** `{result['api_key']}`")
                    st.warning("⚠️ Save this API key securely - it won't be shown again!")
                    
                    # Show integration instructions
                    show_integration_instructions(partner_type, result['api_key'])
                else:
                    st.error(f"Registration failed: {result['error']}")
            else:
                st.error("Please fill in all required fields")

def show_integration_instructions(partner_type: str, api_key: str):
    """Show integration instructions for partners."""
    st.subheader("📚 Integration Instructions")
    
    st.write("**Step 1: API Authentication**")
    st.code(f"""
# Use this API key for all requests
API_KEY = "{api_key}"

headers = {{
    'Authorization': f'Bearer {{API_KEY}}',
    'Content-Type': 'application/json'
}}
""", language="python")
    
    st.write("**Step 2: User Invitation**")
    st.info(f"Share this partner code with your users: `{api_key.split('_')[1][:8]}`")
    st.write("Users can enter this code during registration to be automatically linked to your organization.")
    
    if partner_type == 'broker':
        st.write("**Step 3: Commission Tracking**")
        st.code("""
# Automatically tag trades with commission info
trade_data = {
    'symbol': 'AAPL',
    'entry_price': 150.00,
    'exit_price': 152.00,
    'quantity': 100,
    'commission': 3.50,  # Your commission rate
    'broker_tags': ['demo_broker', 'commission_tracked']
}
""", language="python")
    
    elif partner_type == 'prop_firm':
        st.write("**Step 3: Risk Monitoring**")
        st.code("""
# Monitor trader risk levels
risk_check = {
    'daily_pnl': -750,
    'total_drawdown': -2500,
    'risk_alerts': ['approaching_daily_limit']
}

# Send webhook notification if limits approached
if risk_check['daily_pnl'] < -900:
    send_risk_alert(trader_id, risk_check)
""", language="python")
    
    elif partner_type == 'trading_group':
        st.write("**Step 3: Group Analytics**")
        st.code("""
# Track group performance
group_stats = {
    'total_members': 45,
    'active_traders': 32,
    'group_pnl': 15420.50,
    'top_performers': ['trader_1', 'trader_2']
}
""", language="python")

if __name__ == "__main__":
    render_partner_onboarding()
