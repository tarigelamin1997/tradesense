
import streamlit as st
from urllib.parse import urlparse, parse_qs
from auth import AuthManager

def handle_oauth_callback():
    """Handle OAuth2 callback from Google."""
    # Get the authorization response from URL
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        auth_manager = AuthManager()
        
        # Reconstruct authorization response URL
        current_url = st.get_option("browser.serverAddress") or "localhost"
        port = st.get_option("server.port") or 8501
        authorization_response = f"https://{current_url}/oauth2callback?code={query_params['code']}&state={query_params['state']}"
        
        # Handle the callback
        result = auth_manager.handle_oauth_callback(
            authorization_response=authorization_response,
            state=query_params['state']
        )
        
        if result['success']:
            st.session_state.session_id = result['session_id']
            st.success("🎉 Login successful!")
            st.rerun()
        else:
            st.error(f"Login failed: {result['error']}")
    
    else:
        st.error("Invalid OAuth callback parameters")

# Handle OAuth callback if we're on the callback page
if st.query_params.get('code'):
    handle_oauth_callback()
