
import streamlit as st
import time
from datetime import datetime
import uuid

def show_toast(message, toast_type="info", duration=3000):
    """
    Show toast notification.
    
    Args:
        message: Toast message text
        toast_type: success, error, warning, info
        duration: Duration in milliseconds
    """
    toast_id = str(uuid.uuid4())
    
    # Color schemes for different toast types
    colors = {
        "success": {"bg": "#10b981", "border": "#059669"},
        "error": {"bg": "#ef4444", "border": "#dc2626"},
        "warning": {"bg": "#f59e0b", "border": "#d97706"},
        "info": {"bg": "#3b82f6", "border": "#2563eb"}
    }
    
    # Icons for different toast types
    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    
    color_scheme = colors.get(toast_type, colors["info"])
    icon = icons.get(toast_type, icons["info"])
    
    # Toast HTML and CSS
    toast_html = f"""
    <div id="toast-{toast_id}" class="toast-notification" style="
        position: fixed;
        top: 20px;
        right: 20px;
        background: {color_scheme['bg']};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        border-left: 4px solid {color_scheme['border']};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        min-width: 300px;
        max-width: 500px;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        cursor: pointer;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px;">{icon}</span>
            <span>{message}</span>
            <span style="margin-left: auto; font-size: 18px; opacity: 0.7;">&times;</span>
        </div>
    </div>
    
    <script>
    (function() {{
        const toast = document.getElementById('toast-{toast_id}');
        if (toast) {{
            // Show toast
            setTimeout(() => {{
                toast.style.opacity = '1';
                toast.style.transform = 'translateX(0)';
            }}, 100);
            
            // Auto hide after duration
            setTimeout(() => {{
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => {{
                    if (toast.parentNode) {{
                        toast.parentNode.removeChild(toast);
                    }}
                }}, 300);
            }}, {duration});
            
            // Click to dismiss
            toast.addEventListener('click', function() {{
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => {{
                    if (toast.parentNode) {{
                        toast.parentNode.removeChild(toast);
                    }}
                }}, 300);
            }});
        }}
    }})();
    </script>
    """
    
    # Use Streamlit's HTML component to render the toast
    st.markdown(toast_html, unsafe_allow_html=True)

def success_toast(message, duration=3000):
    """Show success toast."""
    show_toast(message, "success", duration)

def error_toast(message, duration=4000):
    """Show error toast."""
    show_toast(message, "error", duration)

def warning_toast(message, duration=3000):
    """Show warning toast."""
    show_toast(message, "warning", duration)

def info_toast(message, duration=3000):
    """Show info toast."""
    show_toast(message, "info", duration)

# Toast system integration functions
def toast_on_upload_success(filename, num_records):
    """Show toast when file upload succeeds."""
    success_toast(f"✅ {filename} uploaded successfully! {num_records:,} records processed.")

def toast_on_upload_error(error_msg):
    """Show toast when file upload fails."""
    error_toast(f"❌ Upload failed: {error_msg}")

def toast_on_settings_saved():
    """Show toast when settings are saved."""
    success_toast("⚙️ Settings saved successfully!")

def toast_on_export_complete(export_type):
    """Show toast when export completes."""
    success_toast(f"📄 {export_type} export completed successfully!")

def toast_on_login_success(username):
    """Show toast on successful login."""
    success_toast(f"👋 Welcome back, {username}!")

def toast_on_login_error():
    """Show toast on login error."""
    error_toast("🔐 Invalid credentials. Please try again.")

def toast_on_sync_complete(num_trades):
    """Show toast when data sync completes."""
    success_toast(f"🔄 Sync completed! {num_trades:,} trades updated.")

def toast_on_analytics_ready():
    """Show toast when analytics are ready."""
    info_toast("📊 Analytics updated! View your latest performance metrics.")

# Integration with existing components
def integrate_toasts_with_app():
    """Add toast integration CSS and JavaScript."""
    st.markdown("""
    <style>
    /* Global toast container styling */
    .toast-notification {
        font-weight: 500;
        backdrop-filter: blur(10px);
    }
    
    .toast-notification:hover {
        transform: translateX(-5px) !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Ensure toasts appear above all content */
    .toast-notification {
        z-index: 999999 !important;
    }
    
    /* Stack multiple toasts */
    .toast-notification:nth-child(2) { top: 80px !important; }
    .toast-notification:nth-child(3) { top: 140px !important; }
    .toast-notification:nth-child(4) { top: 200px !important; }
    </style>
    """, unsafe_allow_html=True)
