def success_toast(message, duration=3000):
    """Show a success toast notification."""
    return show_toast(message, "success", duration)

def error_toast(message, duration=5000):
    """Show an error toast notification."""
    return show_toast(message, "error", duration)

def info_toast(message, duration=3000):
    """Show an info toast notification."""
    return show_toast(message, "info", duration)

def show_toast(message, toast_type="info", duration=3000):
    """Show a toast notification."""
    toast_id = f"toast_{int(time.time() * 1000)}"