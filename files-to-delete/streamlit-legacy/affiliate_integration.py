
import streamlit as st
from affiliate_system import AffiliateTrackingSystem
from auth import AuthManager
from typing import Dict, Optional

class AffiliateIntegration:
    """Integration layer for affiliate tracking throughout the app."""
    
    def __init__(self):
        self.affiliate_system = AffiliateTrackingSystem()
        self.auth_manager = AuthManager()
    
    def track_signup_conversion(self, user_id: int, referral_code: Optional[str] = None) -> Dict:
        """Track user signup as affiliate conversion."""
        if not referral_code:
            # Check if referral code is in session from URL parameter
            referral_code = st.session_state.get('referral_code')
        
        if referral_code:
            return self.affiliate_system.track_conversion(
                user_id=user_id,
                referral_code=referral_code,
                conversion_type='signup',
                conversion_value=0.0
            )
        
        return {'success': False, 'error': 'No referral code'}
    
    def track_subscription_conversion(self, user_id: int, subscription_tier: str, amount: float) -> Dict:
        """Track subscription purchase as affiliate conversion."""
        # Get user's referral info
        conn = self.affiliate_system.db_path
        cursor = conn.cursor()
        
        # Find the affiliate who referred this user
        cursor.execute('''
            SELECT affiliate_id FROM referrals 
            WHERE referred_user_id = ? AND status = 'confirmed'
            ORDER BY converted_at DESC LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            affiliate_id = result[0]
            
            # Get affiliate's referral code
            conn = sqlite3.connect(self.affiliate_system.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT referral_code FROM affiliates WHERE id = ?', (affiliate_id,))
            referral_code = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            return self.affiliate_system.track_conversion(
                user_id=user_id,
                referral_code=referral_code,
                conversion_type=f'subscription_{subscription_tier}',
                conversion_value=amount
            )
        
        return {'success': False, 'error': 'No referring affiliate found'}
    
    def process_url_parameters(self):
        """Process URL parameters for affiliate tracking."""
        # Get URL parameters
        query_params = st.experimental_get_query_params()
        
        # Check for referral code
        ref_code = query_params.get('ref', [None])[0]
        if ref_code:
            st.session_state.referral_code = ref_code
            
            # Track the click
            request_data = {
                'ip_address': st.experimental_get_query_params().get('ip', ['unknown'])[0],
                'user_agent': 'streamlit_app',
                'utm_source': query_params.get('utm_source', [None])[0],
                'utm_medium': query_params.get('utm_medium', [None])[0],
                'utm_campaign': query_params.get('utm_campaign', [None])[0]
            }
            
            self.affiliate_system.track_referral_click(ref_code, request_data)
    
    def display_referral_widget(self, user_id: int):
        """Display referral widget for users to share."""
        st.subheader("🤝 Refer Friends & Earn")
        
        # Check if user can be an affiliate
        user = self.auth_manager.get_current_user()
        if not user:
            return
        
        # Generate or get user's referral code
        conn = sqlite3.connect(self.affiliate_system.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM affiliates WHERE email = ?', (user['email'],))
        affiliate = cursor.fetchone()
        
        if not affiliate:
            # Auto-create affiliate account for user
            result = self.affiliate_system.create_affiliate(
                name=f"{user['first_name']} {user['last_name']}",
                email=user['email'],
                affiliate_type='individual',
                commission_rate=0.15  # Lower rate for user referrals
            )
            
            if result['success']:
                referral_code = result['referral_code']
            else:
                st.error("Unable to create referral account")
                return
        else:
            cursor.execute('SELECT referral_code FROM affiliates WHERE id = ?', (affiliate[0],))
            referral_code = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        # Display referral information
        referral_url = f"https://tradesense.com/signup?ref={referral_code}"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Your Referral Link", value=referral_url, disabled=True)
        
        with col2:
            if st.button("📋 Copy Link"):
                st.success("Link copied to clipboard!")
        
        st.info("💰 Earn 15% commission on all referrals who upgrade to paid plans!")
        
        # Show referral stats
        stats = self.affiliate_system.get_affiliate_stats(affiliate[0] if affiliate else result['affiliate_id'])
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            st.metric("Total Referrals", stats['affiliate_info']['lifetime_referrals'])
        
        with col4:
            st.metric("Pending Earnings", f"${stats['affiliate_info']['pending_earnings']:.2f}")
        
        with col5:
            st.metric("Total Earned", f"${stats['affiliate_info']['total_earnings']:.2f}")


# Helper function to integrate with auth system
def integrate_affiliate_tracking():
    """Add affiliate tracking to the authentication flow."""
    integration = AffiliateIntegration()
    
    # Process URL parameters on every page load
    integration.process_url_parameters()
    
    return integration

# Add to user registration process
def track_new_user_conversion(user_id: int):
    """Track new user registration as conversion."""
    integration = AffiliateIntegration()
    result = integration.track_signup_conversion(user_id)
    
    if result['success']:
        st.success(f"🎉 Referral bonus earned: ${result['commission_earned']:.2f}")
