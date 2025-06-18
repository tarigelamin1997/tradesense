
import streamlit as st
from typing import Dict, Any
from auth import AuthManager
from config import config

class TradeSenseApp:
    """Main application factory with modular structure."""
    
    def __init__(self):
        self.auth_manager = AuthManager()
        self.current_user = None
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize application with proper configuration."""
        # Validate configuration
        config_status = config.validate_config()
        if not config_status['valid']:
            st.error("Configuration validation failed:")
            for issue in config_status['issues']:
                st.error(f"• {issue}")
            st.stop()
        
        # Set page configuration
        st.set_page_config(
            page_title="TradeSense Analytics",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def run(self):
        """Run the main application."""
        try:
            # Authentication
            self.current_user = self._handle_authentication()
            
            if self.current_user:
                self._render_main_interface()
            else:
                self._render_login_interface()
                
        except Exception as e:
            self._handle_application_error(e)
    
    def _handle_authentication(self):
        """Handle user authentication."""
        return self.auth_manager.get_current_user()
    
    def _render_main_interface(self):
        """Render the main application interface."""
        from pages.dashboard import render_dashboard
        from pages.analytics import render_analytics
        from pages.settings import render_settings
        
        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Navigate to:",
            ["Dashboard", "Analytics", "Settings"]
        )
        
        if page == "Dashboard":
            render_dashboard(self.current_user)
        elif page == "Analytics":
            render_analytics(self.current_user)
        elif page == "Settings":
            render_settings(self.current_user)
    
    def _render_login_interface(self):
        """Render login interface."""
        from auth import render_auth_interface
        render_auth_interface()
    
    def _handle_application_error(self, error: Exception):
        """Handle application-level errors."""
        import traceback
        error_id = str(uuid.uuid4())[:8]
        
        st.error(f"Application Error (ID: {error_id})")
        st.error("The application encountered an unexpected error.")
        
        with st.expander("Error Details"):
            st.code(f"Error Type: {type(error).__name__}")
            st.code(f"Error Message: {str(error)}")
            st.code(traceback.format_exc())
        
        # Log error
        logger.error(f"Application error {error_id}: {str(error)}", exc_info=True)
