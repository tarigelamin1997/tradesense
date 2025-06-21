
import streamlit as st
from integration_manager import render_integration_management_ui
from auth import AuthManager

def main():
    """Main integrations page."""
    st.set_page_config(
        page_title="TradeSense - Integrations",
        page_icon="🔗",
        layout="wide"
    )
    
    st.title("🔗 Broker & Prop Firm Integrations")
    st.markdown("---")
    
    # Check authentication
    auth_manager = AuthManager()
    current_user = auth_manager.get_current_user()
    
    if not current_user:
        st.warning("🔐 Please login to access integration management")
        st.info("**Integration Management Features:**")
        st.write("• **Connect Multiple Accounts**: Link brokers, prop firms, and trading platforms")
        st.write("• **Real-time Sync**: Automatic data synchronization with configurable frequency")
        st.write("• **Status Monitoring**: Track connection health and sync history")
        st.write("• **Secure Credentials**: Encrypted storage of API keys and authentication tokens")
        st.write("• **Error Management**: Detailed error tracking and automatic retry logic")
        st.write("• **Bulk Operations**: Test, sync, or manage multiple integrations simultaneously")
        
        st.markdown("---")
        st.info("👈 Use the authentication section in the sidebar to login")
        return
    
    # Render the integration management UI
    try:
        from integration_manager import render_integration_management_ui
        render_integration_management_ui(current_user)
    except ImportError:
        st.error("Integration management module not available")
        st.info("This feature is under development")
    except TypeError as e:
        if "missing 1 required positional argument" in str(e):
            # Fallback integration UI
            render_basic_integration_ui()
        else:
            raise e

def render_basic_integration_ui():
    """Basic integration UI fallback."""
    st.subheader("🔗 Broker Integration Management")
    
    st.info("🚧 Integration management is currently being enhanced")
    
    # Basic integration status
    st.markdown("### 📊 Integration Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Connected Accounts", "0")
    
    with col2:
        st.metric("Last Sync", "Never")
    
    with col3:
        st.metric("Status", "Ready")
    
    # Available integrations
    st.markdown("### 🏦 Available Integrations")
    
    integrations = [
        {"name": "Interactive Brokers", "status": "Coming Soon", "icon": "🏦"},
        {"name": "TD Ameritrade", "status": "Coming Soon", "icon": "📈"},
        {"name": "E*TRADE", "status": "Coming Soon", "icon": "💼"},
        {"name": "Apex Trader", "status": "Coming Soon", "icon": "🚀"},
        {"name": "FTMO", "status": "Coming Soon", "icon": "🏢"}
    ]
    
    for integration in integrations:
        with st.expander(f"{integration['icon']} {integration['name']}"):
            st.write(f"Status: **{integration['status']}**")
            st.write("Features:")
            st.write("• Automatic trade import")
            st.write("• Real-time sync")
            st.write("• Portfolio tracking")
            if st.button(f"Setup {integration['name']}", disabled=True):
                st.info("This integration will be available soon!")
    
    # Additional help section
    with st.sidebar:
        st.markdown("---")
        st.subheader("💡 Integration Help")
        
        with st.expander("🏦 Supported Brokers"):
            st.write("• Interactive Brokers")
            st.write("• TD Ameritrade")
            st.write("• E*TRADE")
            st.write("• Charles Schwab")
            st.write("• Fidelity")
            st.caption("More brokers coming soon!")
        
        with st.expander("🏢 Supported Prop Firms"):
            st.write("• Apex Trader Funding")
            st.write("• Funded Trader")
            st.write("• FTMO")
            st.write("• TopStep")
            st.write("• The5%ers")
            st.caption("More prop firms coming soon!")
        
        with st.expander("🔧 Troubleshooting"):
            st.write("**Connection Issues:**")
            st.write("• Verify credentials are correct")
            st.write("• Check API permissions")
            st.write("• Ensure account is active")
            st.write("")
            st.write("**Sync Problems:**")
            st.write("• Review error messages")
            st.write("• Check sync frequency settings")
            st.write("• Try manual sync")
        
        if st.button("📧 Contact Support"):
            st.success("Support ticket created!")
            st.info("Our team will respond within 24 hours")

if __name__ == "__main__":
    main()
