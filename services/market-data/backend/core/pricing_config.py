"""
Pricing configuration for TradeSense
Maps frontend plan names to backend plan names and Stripe product/price IDs
"""

# Plan name mapping
PLAN_MAPPING = {
    'free': 'free',
    'pro': 'professional',
    'enterprise': 'team'
}

# Stripe Product and Price IDs
# These should be created in Stripe Dashboard and added to environment variables
STRIPE_PRODUCTS = {
    'professional': {
        'name': 'TradeSense Pro',
        'monthly_price_id': 'price_1234567890abcdef',  # Replace with actual Stripe price ID
        'annual_price_id': 'price_0987654321fedcba',   # Replace with actual Stripe price ID
        'features': {
            'trades_per_month': -1,  # Unlimited
            'journal_entries_per_month': -1,
            'playbooks': 10,
            'advanced_analytics': True,
            'real_time_data': True,
            'api_access': True,
            'priority_support': False
        }
    },
    'team': {
        'name': 'TradeSense Enterprise',
        'monthly_price_id': 'price_abcdef1234567890',  # Replace with actual Stripe price ID
        'annual_price_id': 'price_fedcba0987654321',   # Replace with actual Stripe price ID
        'features': {
            'trades_per_month': -1,  # Unlimited
            'journal_entries_per_month': -1,
            'playbooks': -1,  # Unlimited
            'advanced_analytics': True,
            'real_time_data': True,
            'api_access': True,
            'ai_insights': True,
            'priority_support': True,
            'custom_integrations': True,
            'dedicated_account_manager': True
        }
    }
}

def get_stripe_price_id(plan_name: str, billing_cycle: str = 'monthly') -> str:
    """Get Stripe price ID for a plan"""
    # Map frontend plan name to backend plan name
    backend_plan = PLAN_MAPPING.get(plan_name, plan_name)
    
    if backend_plan == 'free':
        return None
    
    product = STRIPE_PRODUCTS.get(backend_plan)
    if not product:
        raise ValueError(f"Unknown plan: {plan_name}")
    
    if billing_cycle == 'annual' or billing_cycle == 'yearly':
        return product['annual_price_id']
    else:
        return product['monthly_price_id']

def get_plan_features(plan_name: str) -> dict:
    """Get features for a plan"""
    backend_plan = PLAN_MAPPING.get(plan_name, plan_name)
    
    if backend_plan == 'free':
        return {
            'trades_per_month': 10,
            'journal_entries_per_month': 20,
            'playbooks': 2,
            'advanced_analytics': False,
            'real_time_data': False,
            'api_access': False,
            'priority_support': False
        }
    
    product = STRIPE_PRODUCTS.get(backend_plan)
    if not product:
        raise ValueError(f"Unknown plan: {plan_name}")
    
    return product['features']