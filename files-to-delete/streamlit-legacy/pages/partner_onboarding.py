
import streamlit as st
from partner_portal import PartnerPortalManager, render_partner_registration_form
from auth import AuthManager

def main():
    """Partner onboarding landing page."""
    st.set_page_config(
        page_title="TradeSense Partner Program",
        page_icon="🤝",
        layout="wide"
    )
    
    # Header
    st.title("🤝 TradeSense Partner Program")
    st.subheader("White-Label Trading Analytics for Your Business")
    
    # Value proposition
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🏦 For Brokerages
        - **White-label analytics** for your clients
        - **Branded experience** with your logo and colors
        - **Revenue sharing** on user subscriptions
        - **API integration** with your platforms
        """)
    
    with col2:
        st.markdown("""
        ### 🏢 For Prop Firms
        - **Risk monitoring** dashboards
        - **Performance tracking** for traders
        - **Custom rule enforcement**
        - **Automated reporting**
        """)
    
    with col3:
        st.markdown("""
        ### 👥 For Trading Communities
        - **Group analytics** and leaderboards
        - **Social trading features**
        - **Educational content delivery**
        - **Member management tools**
        """)
    
    st.divider()
    
    # Partnership benefits
    st.subheader("🎯 Partnership Benefits")
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.markdown("""
        **🚀 Technical Benefits:**
        - Complete white-label solution
        - Custom branding and domains
        - API access and webhooks
        - SSO integration support
        - Mobile-responsive design
        
        **📊 Analytics Features:**
        - Professional trading analytics
        - Risk management tools
        - Performance reporting
        - Custom dashboards
        - Data export capabilities
        """)
    
    with col5:
        st.markdown("""
        **💼 Business Benefits:**
        - New revenue stream
        - Enhanced client value
        - Reduced development costs
        - Professional analytics platform
        - Ongoing support and updates
        
        **🤝 Partnership Support:**
        - Dedicated account manager
        - Technical integration support
        - Marketing materials
        - Co-marketing opportunities
        - Regular product updates
        """)
    
    st.divider()
    
    # Pricing plans
    st.subheader("💳 Partnership Plans")
    
    col6, col7, col8 = st.columns(3)
    
    with col6:
        st.markdown("""
        ### 🌱 Starter
        **$99/month**
        - Up to 50 users
        - Basic white-labeling
        - Email support
        - Standard analytics
        - API access
        """)
        
        if st.button("Choose Starter", key="starter", type="secondary"):
            st.session_state.selected_plan = "starter"
    
    with col7:
        st.markdown("""
        ### 🚀 Professional
        **$299/month**
        - Up to 200 users
        - Full white-labeling
        - Priority support
        - Advanced analytics
        - Custom integrations
        - Revenue sharing
        """)
        
        if st.button("Choose Professional", key="professional", type="primary"):
            st.session_state.selected_plan = "professional"
    
    with col8:
        st.markdown("""
        ### 🏢 Enterprise
        **Custom Pricing**
        - Unlimited users
        - Complete customization
        - Dedicated support
        - Custom features
        - On-premise deployment
        - SLA guarantees
        """)
        
        if st.button("Contact Sales", key="enterprise"):
            st.session_state.selected_plan = "enterprise"
    
    st.divider()
    
    # Registration form
    if st.session_state.get('selected_plan'):
        st.subheader("🚀 Get Started Today")
        render_partner_registration_form()
    else:
        # Call to action
        st.subheader("🚀 Ready to Get Started?")
        
        col9, col10, col11 = st.columns([1, 2, 1])
        
        with col10:
            if st.button("🤝 Become a Partner Today", type="primary", use_container_width=True):
                st.session_state.selected_plan = "professional"
                st.rerun()
            
            st.markdown("---")
            st.markdown("**Questions?** Contact our partner team at partners@tradesense.com")

if __name__ == "__main__":
    main()
