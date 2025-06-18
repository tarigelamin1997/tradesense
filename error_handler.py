
import functools
import traceback
from typing import Optional, Dict, Any, Callable
import streamlit as st
from logging_manager import log_error, log_critical, log_warning, LogCategory

class ErrorHandler:
    """Context manager and decorator for error handling."""
    
    def __init__(self, 
                 category: LogCategory = LogCategory.SYSTEM_ERROR,
                 user_friendly_message: str = "An error occurred. Please try again.",
                 show_in_ui: bool = True,
                 reraise: bool = False,
                 user_id: Optional[int] = None,
                 partner_id: Optional[str] = None):
        self.category = category
        self.user_friendly_message = user_friendly_message
        self.show_in_ui = show_in_ui
        self.reraise = reraise
        self.user_id = user_id
        self.partner_id = partner_id
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            self.handle_error(exc_value, exc_traceback)
            return not self.reraise
        return False
    
    def handle_error(self, error: Exception, exc_traceback):
        """Handle an error by logging it and optionally displaying in UI."""
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': ''.join(traceback.format_tb(exc_traceback)),
            'include_trace': True
        }
        
        # Determine log level based on error type
        if isinstance(error, (ConnectionError, TimeoutError)):
            log_warning(
                f"Connection issue: {str(error)}",
                details=error_details,
                user_id=self.user_id,
                partner_id=self.partner_id,
                category=self.category
            )
        elif isinstance(error, (MemoryError, SystemError)):
            log_critical(
                f"System error: {str(error)}",
                details=error_details,
                user_id=self.user_id,
                partner_id=self.partner_id,
                category=self.category
            )
        else:
            log_error(
                f"Application error: {str(error)}",
                details=error_details,
                user_id=self.user_id,
                partner_id=self.partner_id,
                category=self.category
            )
        
        # Display in UI if requested
        if self.show_in_ui:
            st.error(f"❌ {self.user_friendly_message}")
            
            # Show technical details in expander for debugging
            with st.expander("🔍 Technical Details", expanded=False):
                st.code(f"Error Type: {type(error).__name__}")
                st.code(f"Error Message: {str(error)}")
                if hasattr(st, 'session_state') and getattr(st.session_state, 'show_debug', False):
                    st.code(f"Traceback:\n{''.join(traceback.format_tb(exc_traceback))}")

def handle_errors(category: LogCategory = LogCategory.SYSTEM_ERROR,
                 user_friendly_message: str = "An error occurred. Please try again.",
                 show_in_ui: bool = True,
                 reraise: bool = False):
    """Decorator for automatic error handling."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get user context
            user_id = None
            partner_id = None
            
            try:
                if hasattr(st, 'session_state'):
                    user_id = getattr(st.session_state, 'user_id', None)
                    partner_id = getattr(st.session_state, 'partner_id', None)
            except:
                pass
            
            with ErrorHandler(
                category=category,
                user_friendly_message=user_friendly_message,
                show_in_ui=show_in_ui,
                reraise=reraise,
                user_id=user_id,
                partner_id=partner_id
            ):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def safe_execute(func: Callable, 
                error_message: str = "Operation failed",
                default_return=None,
                category: LogCategory = LogCategory.SYSTEM_ERROR,
                show_error: bool = True) -> Any:
    """Safely execute a function with error handling."""
    try:
        return func()
    except Exception as e:
        # Get user context
        user_id = None
        partner_id = None
        
        try:
            if hasattr(st, 'session_state'):
                user_id = getattr(st.session_state, 'user_id', None)
                partner_id = getattr(st.session_state, 'partner_id', None)
        except:
            pass
        
        # Log error
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'function_name': func.__name__ if hasattr(func, '__name__') else 'anonymous',
            'include_trace': True
        }
        
        log_error(
            f"{error_message}: {str(e)}",
            details=error_details,
            user_id=user_id,
            partner_id=partner_id,
            category=category
        )
        
        # Show error in UI
        if show_error:
            st.error(f"❌ {error_message}")
            with st.expander("🔍 Error Details"):
                st.code(f"{type(e).__name__}: {str(e)}")
        
        return default_return

class StreamlitErrorDisplay:
    """Helper class for displaying errors in Streamlit UI."""
    
    @staticmethod
    def show_error_summary(errors: list, title: str = "Recent Errors"):
        """Display a summary of recent errors."""
        if not errors:
            st.success("✅ No recent errors found")
            return
        
        st.subheader(f"🚨 {title}")
        
        # Group errors by severity
        critical_errors = [e for e in errors if e['level'] == 'CRITICAL']
        regular_errors = [e for e in errors if e['level'] == 'ERROR']
        
        if critical_errors:
            st.error(f"🔥 **{len(critical_errors)} Critical Issues** - Immediate attention required")
            
        if regular_errors:
            st.warning(f"⚠️ **{len(regular_errors)} Errors** - Need investigation")
        
        # Display errors in expandable sections
        for i, error in enumerate(errors[:10]):  # Show top 10
            severity_icon = "🔥" if error['level'] == 'CRITICAL' else "❌"
            
            with st.expander(f"{severity_icon} {error['message'][:80]}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Time:** {error['timestamp']}")
                    st.write(f"**Level:** {error['level']}")
                    st.write(f"**Category:** {error['category']}")
                
                with col2:
                    if error.get('user_id'):
                        st.write(f"**User ID:** {error['user_id']}")
                    if error.get('partner_id'):
                        st.write(f"**Partner:** {error['partner_id']}")
                
                st.write(f"**Message:** {error['message']}")
                
                if error.get('details'):
                    st.json(error['details'])
    
    @staticmethod
    def show_error_patterns(patterns: list):
        """Display recurring error patterns."""
        if not patterns:
            st.success("✅ No recurring error patterns detected")
            return
        
        st.subheader("🔄 Recurring Error Patterns")
        st.write("These errors have occurred multiple times and may indicate systemic issues.")
        
        for pattern in patterns:
            severity_color = "🔥" if pattern['severity'] == 'CRITICAL' else "⚠️"
            
            with st.expander(f"{severity_color} {pattern['description'][:80]} (x{pattern['count']})", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Occurrences:** {pattern['count']}")
                    st.write(f"**Severity:** {pattern['severity']}")
                    st.write(f"**First Seen:** {pattern['first_occurrence']}")
                
                with col2:
                    st.write(f"**Last Seen:** {pattern['last_occurrence']}")
                
                st.write(f"**Pattern:** {pattern['signature']}")
                
                if st.button(f"Mark as Resolved", key=f"resolve_{pattern['signature'][:20]}"):
                    # TODO: Implement pattern resolution
                    st.success("Pattern marked for investigation")
    
    @staticmethod
    def show_critical_alerts():
        """Show critical alerts in the UI."""
        if hasattr(st, 'session_state') and 'critical_alerts' in st.session_state:
            alerts = st.session_state.critical_alerts
            
            if alerts:
                # Show most recent critical alert
                latest_alert = max(alerts, key=lambda x: x['timestamp'])
                
                st.error(f"🚨 **CRITICAL ALERT** - {latest_alert['message']}")
                
                with st.expander("Alert Details"):
                    st.write(f"**Time:** {latest_alert['timestamp']}")
                    if latest_alert.get('details'):
                        st.json(latest_alert['details'])
                
                # Button to acknowledge alert
                if st.button("✅ Acknowledge Alert"):
                    st.session_state.critical_alerts = []
                    st.success("Alert acknowledged")
                    st.rerun()
