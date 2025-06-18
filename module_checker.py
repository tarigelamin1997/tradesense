
"""
Module availability checker for TradeSense
Checks module availability without displaying UI warnings prematurely
"""

import logging

logger = logging.getLogger(__name__)

class ModuleChecker:
    """Check module availability without premature UI warnings."""
    
    def __init__(self):
        self._analytics_available = None
        self._interactive_table_available = None
        self._checked = False
    
    def check_analytics_availability(self):
        """Check if analytics modules are available."""
        if self._analytics_available is None:
            try:
                import pandas as pd
                import numpy as np
                import streamlit as st
                from analytics import compute_basic_stats
                self._analytics_available = True
                logger.debug("Analytics module available")
            except ImportError as e:
                self._analytics_available = False
                logger.debug(f"Analytics module not available: {e}")
        
        return self._analytics_available
    
    def check_interactive_table_availability(self):
        """Check if interactive table modules are available."""
        if self._interactive_table_available is None:
            try:
                from st_aggrid import AgGrid
                import interactive_table
                self._interactive_table_available = True
                logger.debug("Interactive table module available")
            except ImportError as e:
                self._interactive_table_available = False
                logger.debug(f"Interactive table module not available: {e}")
        
        return self._interactive_table_available
    
    def get_availability_message(self):
        """Get availability message only when explicitly requested."""
        messages = []
        
        if not self.check_analytics_availability():
            messages.append("Analytics module not fully available - some features may be limited")
        
        if not self.check_interactive_table_availability():
            messages.append("Interactive table module not available - using basic displays")
        
        return messages
    
    def display_warnings_if_needed(self):
        """Display warnings only when modules are actually needed."""
        import streamlit as st
        
        messages = self.get_availability_message()
        for message in messages:
            st.warning(message)

# Global instance
module_checker = ModuleChecker()
