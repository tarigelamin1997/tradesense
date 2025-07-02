
#!/usr/bin/env python3
"""
Core Module Initializer
Ensures all core components are available
"""

# Import all core components to ensure they're available
try:
    from .app_factory import AppFactory
    from .data_upload_handler import render_data_upload_section
    from .analysis_engine import render_analysis_controls, run_analysis
    from .dashboard_manager import render_dashboard_tabs
    from .dashboard_components import render_dashboard
    from .analytics_components import render_analytics
    from .trade_data_components import render_trade_data
    from .settings_components import render_settings
    
    __all__ = [
        'AppFactory',
        'render_data_upload_section',
        'render_analysis_controls',
        'run_analysis',
        'render_dashboard_tabs',
        'render_dashboard',
        'render_analytics',
        'render_trade_data',
        'render_settings'
    ]
    
except ImportError as e:
    # Fallback imports
    print(f"Warning: Some core components unavailable: {e}")
    from .app_factory import AppFactory
    __all__ = ['AppFactory']
