
#!/usr/bin/env python3
"""
TradeSense - Advanced Trading Analytics Platform
Main Application Entry Point
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Check for required modules before importing Streamlit
missing_modules = []
required_modules = ['streamlit', 'pandas', 'numpy', 'plotly']

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing_modules.append(module)

if missing_modules:
    print(f"❌ Missing required modules: {', '.join(missing_modules)}")
    print("Please install dependencies with:")
    print("python3 -m pip install --user streamlit pandas numpy plotly")
    sys.exit(1)

# Now safely import Streamlit
import streamlit as st
import logging

# Configure Streamlit page FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="TradeSense - Trading Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://tradesense.app/help',
        'Report a bug': 'https://tradesense.app/support',
        'About': """
        # TradeSense Trading Analytics

        Advanced trading performance analytics platform.

        **Version:** 2.0.0
        **Contact:** support@tradesense.app
        """
    }
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables."""
    if 'data_uploaded' not in st.session_state:
        st.session_state.data_uploaded = False
    if 'trade_data' not in st.session_state:
        st.session_state.trade_data = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None

def main():
    """Main application function."""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Try to import the main app factory
        try:
            from core.app_factory import create_app
            create_app()
        except ImportError as e:
            logger.warning(f"Could not import app_factory: {e}")
            # Fallback to basic app structure
            st.title("🏆 TradeSense - Trading Analytics")
            st.info("Welcome to TradeSense! The application is starting up...")
            
            # Basic file uploader as fallback
            uploaded_file = st.file_uploader(
                "Upload your trading data",
                type=['csv', 'xlsx', 'xls'],
                help="Upload your trade history file to get started with analytics"
            )
            
            if uploaded_file:
                st.success("File uploaded successfully!")
                st.info("Analytics engine is initializing...")
            else:
                st.markdown("""
                ### Getting Started
                1. Upload your trading data using the file uploader above
                2. Review and map your data columns
                3. Analyze your trading performance with interactive charts
                4. Get risk management recommendations
                """)
                
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"Application Error: {str(e)}")
        st.info("Please check the logs for more details or contact support.")

# Run the application
if __name__ == "__main__":
    main()
