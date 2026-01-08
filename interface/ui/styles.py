"""
UI styles and theme configuration
"""

CUSTOM_CSS = """
<style>
/* Main container styling */
.main-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* Card styling */
.custom-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    padding: 24px;
    margin: 20px 0;
}

/* Dark mode card */
body.body--dark .custom-card {
    background: #2d2d2d;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* Metric display */
.metric {
    display: inline-block;
    margin: 10px 20px 10px 0;
}

.metric-label {
    font-size: 12px;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-value {
    font-size: 28px;
    font-weight: bold;
    color: #333;
}

body.body--dark .metric-label {
    color: #999;
}

body.body--dark .metric-value {
    color: #e0e0e0;
}

/* Status badges */
.status-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.badge-running { background: #28a745; color: white; }
.badge-stopped { background: #6c757d; color: white; }
.badge-completed { background: #17a2b8; color: white; }
.badge-failed { background: #dc3545; color: white; }

body.body--dark .badge-running { background: #4dff6d; color: #1a1a1a; }
body.body--dark .badge-stopped { background: #8c959d; color: #1a1a1a; }
body.body--dark .badge-completed { background: #4db8cd; color: #1a1a1a; }
body.body--dark .badge-failed { background: #ff5d6e; color: #1a1a1a; }

/* Progress bar */
.progress-container {
    width: 100%;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
    margin: 15px 0;
}

body.body--dark .progress-container {
    background: #3d3d3d;
}

/* Login container */
.login-container {
    max-width: 400px;
    margin: 100px auto;
    padding: 20px;
}

/* Sidebar styling */
.sidebar-container {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

body.body--dark .sidebar-container {
    background: #2d2d2d;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* Caption text */
.caption {
    font-size: 13px;
    color: #666;
    margin: 6px 0;
}

body.body--dark .caption {
    color: #999;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .main-container {
        padding: 15px;
    }
    
    .custom-card {
        padding: 16px;
        margin: 15px 0;
    }
    
    .metric {
        display: block;
        margin: 15px 0;
    }
    
    .metric-value {
        font-size: 24px;
    }
}
</style>
"""

def apply_custom_styles():
    """Apply custom CSS styles to the page"""
    from nicegui import ui
    ui.add_head_html(CUSTOM_CSS)
