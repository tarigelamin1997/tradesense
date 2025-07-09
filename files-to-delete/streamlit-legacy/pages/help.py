
import streamlit as st
from documentation.help_center import render_help_center
from documentation.auto_support import render_auto_support_widget, quick_help_sidebar
from auth import AuthManager

def main():
    """Main help page."""
    st.set_page_config(
        page_title="TradeSense - Help Center",
        page_icon="🆘",
        layout="wide"
    )
    
    # Add quick help to sidebar
    quick_help_sidebar()
    
    # Main help content
    render_help_center()
    
    # Auto-support demo section
    st.markdown("---")
    st.subheader("🤖 Try Auto-Support")
    st.write("Describe your issue and get instant help suggestions:")
    
    issue_description = st.text_area(
        "Describe your problem:",
        placeholder="e.g., 'I can't connect to my Interactive Brokers account'"
    )
    
    if issue_description:
        render_auto_support_widget(user_description=issue_description)

if __name__ == "__main__":
    main()
