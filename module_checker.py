import streamlit as st
import sys
import logging

logger = logging.getLogger(__name__)


class ModuleChecker:
    """Simple module availability checker."""

    def __init__(self):
        self.required_modules = [
            'pandas',
            'numpy', 
            'plotly',
            'streamlit',
            'datetime',
            'sqlite3'
        ]
        self.warnings_shown = False

    def check_modules(self):
        """Check if required modules are available."""
        missing_modules = []

        for module_name in self.required_modules:
            try:
                __import__(module_name)
            except ImportError:
                missing_modules.append(module_name)
                logger.warning(f"Missing module: {module_name}")

        return missing_modules

    def display_warnings_if_needed(self):
        """Display warnings if modules are missing."""
        if self.warnings_shown:
            return

        missing = self.check_modules()
        if missing:
            st.warning(f"⚠️ Some features may be limited. Missing: {', '.join(missing)}")
            self.warnings_shown = True


# Global instance
module_checker = ModuleChecker()