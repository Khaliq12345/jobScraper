from multiprocessing import Process
import os
import time
from urllib.parse import urlparse
import signal
import hashlib
from datetime import datetime, timedelta
from fasthtml.common import fast_app, Script, Div, P, RedirectResponse, Style, Title, Body, Form, H1, Label, Input, serve, Button, Select, Option, H3, Hr, Details, Summary, A, H2, Span
from src.scrapers.workdayjobs import Workday
from src.storage.database import Database
from src.storage.model import scraperStatus

# Initialize database
db = Database()

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 30



def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username: str, password: str) -> bool:
    """Verify username and password against database"""
    user = db.get_user(username)
    if user:
        password_hash = hash_password(password)
        return user.password == password_hash
    return False

def check_session_timeout(session):
    """Check if session has timed out"""
    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        if datetime.now() - last_activity > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            return True
    return False

# Styles
css = Style("""
/* Checkbox override - place at the END of your CSS file */
.form-group input[type="checkbox"] {
    width: 18px !important;
    height: 18px !important;
    padding: 0 !important;
    margin: 0 8px 0 0 !important;
    cursor: pointer;
    accent-color: #0066cc;
    vertical-align: middle;
}

@media (prefers-color-scheme: dark) {
    .form-group input[type="checkbox"] {
        accent-color: #4d9fff;
    }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0;
    padding: 0;
    background: #f5f5f5;
    color: #333;
}

@media (prefers-color-scheme: dark) {
    body {
        background: #1a1a1a;
        color: #e0e0e0;
    }
}

/* Layout */
.sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 250px;
    background: white;
    padding: 20px;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
    overflow-y: auto;
    transition: transform 0.3s ease;
    z-index: 1000;
}

@media (prefers-color-scheme: dark) {
    .sidebar {
        background: #2d2d2d;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.5);
    }
}

/* Mobile: Hide sidebar off-screen by default */
@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-100%);
        width: 280px;
    }
    
    .sidebar.active {
        transform: translateX(0);
    }
    
    /* Overlay when sidebar is open */
    body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
        z-index: 999;
    }
    
    body.sidebar-open::before {
        opacity: 1;
        pointer-events: auto;
    }
}

.main-content {
    margin-left: 290px;
    padding: 20px;
    transition: margin-left 0.3s ease;
}

@media (max-width: 768px) {
    .main-content {
        margin-left: 0;
        padding: 60px 15px 15px;
    }
}

/* Mobile menu toggle button */
.menu-toggle {
    display: none;
    position: fixed;
    top: 15px;
    left: 15px;
    z-index: 1001;
    background: #0066cc;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 18px;
}

@media (max-width: 768px) {
    .menu-toggle {
        display: block;
    }
}

@media (prefers-color-scheme: dark) {
    .menu-toggle {
        background: #4d9fff;
    }
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

@media (max-width: 768px) {
    .container {
        padding: 15px;
    }
}

.login-container {
    max-width: 400px;
    margin: 100px auto;
    padding: 0 20px;
}

@media (max-width: 480px) {
    .login-container {
        margin: 50px auto;
        max-width: 100%;
    }
}

/* Cards */
.card {
    background: white;
    padding: 24px;
    margin: 20px 0;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

@media (max-width: 768px) {
    .card {
        padding: 16px;
        margin: 15px 0;
    }
}

@media (prefers-color-scheme: dark) {
    .card {
        background: #2d2d2d;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
}

/* Forms */
.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    font-size: 14px;
    color: #333;
}

@media (prefers-color-scheme: dark) {
    .form-group label {
        color: #e0e0e0;
    }
}

.form-group input,
select {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    box-sizing: border-box;
    font-size: 14px;
    transition: border-color 0.2s;
    background: white;
    color: #333;
}

@media (prefers-color-scheme: dark) {
    .form-group input,
    select {
        background: #3d3d3d;
        border-color: #555;
        color: #e0e0e0;
    }
}

.form-group input:focus,
select:focus {
    outline: none;
    border-color: #0066cc;
}

@media (prefers-color-scheme: dark) {
    .form-group input:focus,
    select:focus {
        border-color: #4d9fff;
    }
}

/* Buttons */
button {
    padding: 10px 20px;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background 0.2s;
}

button:hover {
    background: #0052a3;
}

@media (prefers-color-scheme: dark) {
    button {
        background: #4d9fff;
    }
    
    button:hover {
        background: #3d8fef;
    }
}

button.danger {
    background: #dc3545;
}

button.danger:hover {
    background: #c82333;
}

@media (prefers-color-scheme: dark) {
    button.danger {
        background: #ff4d5e;
    }
    
    button.danger:hover {
        background: #ef3d4e;
    }
}

button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

/* Metrics */
.metric {
    display: inline-block;
    margin: 10px 20px 10px 0;
}

@media (max-width: 768px) {
    .metric {
        display: block;
        margin: 15px 0;
    }
}

.metric-label {
    font-size: 12px;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

@media (prefers-color-scheme: dark) {
    .metric-label {
        color: #999;
    }
}

.metric-value {
    font-size: 28px;
    font-weight: bold;
    color: #333;
}

@media (max-width: 768px) {
    .metric-value {
        font-size: 24px;
    }
}

@media (prefers-color-scheme: dark) {
    .metric-value {
        color: #e0e0e0;
    }
}

/* Progress Bar */
.progress-bar {
    width: 100%;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
    margin: 15px 0;
}

@media (prefers-color-scheme: dark) {
    .progress-bar {
        background: #3d3d3d;
    }
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #0066cc, #0099ff);
    transition: width 0.3s ease;
}

@media (prefers-color-scheme: dark) {
    .progress-fill {
        background: linear-gradient(90deg, #4d9fff, #6db3ff);
    }
}

/* Alerts */
.alert {
    padding: 12px 16px;
    margin: 12px 0;
    border-radius: 6px;
    font-size: 14px;
}

.alert-success {
    background: #d4edda;
    color: #155724;
    border-left: 4px solid #28a745;
}

@media (prefers-color-scheme: dark) {
    .alert-success {
        background: #1e3a23;
        color: #7dff9d;
        border-left-color: #4dff6d;
    }
}

.alert-error {
    background: #f8d7da;
    color: #721c24;
    border-left: 4px solid #dc3545;
}

@media (prefers-color-scheme: dark) {
    .alert-error {
        background: #3a1e1e;
        color: #ff8d9d;
        border-left-color: #ff5d6e;
    }
}

.alert-info {
    background: #d1ecf1;
    color: #0c5460;
    border-left: 4px solid #17a2b8;
}

@media (prefers-color-scheme: dark) {
    .alert-info {
        background: #1e2e3a;
        color: #7dd8ed;
        border-left-color: #4db8cd;
    }
}

/* Badges */
.badge {
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

@media (prefers-color-scheme: dark) {
    .badge-running { background: #4dff6d; color: #1a1a1a; }
    .badge-stopped { background: #8c959d; color: #1a1a1a; }
    .badge-completed { background: #4db8cd; color: #1a1a1a; }
    .badge-failed { background: #ff5d6e; color: #1a1a1a; }
}

/* Details/Summary */
details {
    border: 1px solid #ddd;
    border-radius: 6px;
    margin: 12px 0;
    overflow: hidden;
}

@media (prefers-color-scheme: dark) {
    details {
        border-color: #555;
    }
}

summary {
    padding: 12px 16px;
    cursor: pointer;
    background: #f8f9fa;
    font-weight: 500;
    user-select: none;
    transition: background 0.2s;
}

@media (prefers-color-scheme: dark) {
    summary {
        background: #3d3d3d;
    }
}

summary:hover {
    background: #e9ecef;
}

@media (prefers-color-scheme: dark) {
    summary:hover {
        background: #4d4d4d;
    }
}

details[open] summary {
    border-bottom: 1px solid #ddd;
}

@media (prefers-color-scheme: dark) {
    details[open] summary {
        border-bottom-color: #555;
    }
}

details > *:not(summary) {
    padding: 16px;
}

/* Utility Classes */
.divider {
    border: none;
    border-top: 1px solid #ddd;
    margin: 20px 0;
}

@media (prefers-color-scheme: dark) {
    .divider {
        border-top-color: #555;
    }
}

.caption {
    font-size: 13px;
    color: #666;
    margin: 6px 0;
}

@media (prefers-color-scheme: dark) {
    .caption {
        color: #999;
    }
}

/* Links */
a {
    text-decoration: none;
    color: inherit;
}

a:hover {
    opacity: 0.8;
}

/* Pagination */
.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e0e0e0;
}

@media (max-width: 480px) {
    .pagination {
        flex-direction: column;
        gap: 10px;
    }
    
    .pagination button {
        width: 100%;
    }
}

.pagination button {
    padding: 10px 20px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s ease;
}

.pagination button:hover:not(:disabled) {
    background: #5568d3;
    transform: translateY(-1px);
}

.pagination button:disabled {
    background: #ccc;
    cursor: not-allowed;
    opacity: 0.6;
}

.page-info {
    color: #666;
    font-weight: 500;
}
""")

# Create FastHTML app with sessions
app, rt = fast_app(
    hdrs=(
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        css
    ),
    # live=True
)

# Login page
@rt('/')
def get(session):
    # Check if already logged in
    if session.get('username') and not check_session_timeout(session):
        return RedirectResponse('/dashboard')

    return (
        Title("Login - Scraper App"),
        Body(
            Div(cls="login-container")(
                Div(cls="card")(
                    H1("🔐 Login"),
                    Form(action="/login", method="post")(
                        Div(cls="form-group")(
                            Label("Username/Email", fr="username"),
                            Input(type="text", name="username", id="username", required=True)
                        ),
                        Div(cls="form-group")(
                            Label("Password", fr="password"),
                            Input(type="password", name="password", id="password", required=True)
                        ),
                        Button("Login", type="submit")
                    ),
                    Div(id="error-msg")
                )
            )
        )
    )

@rt('/login')
def post(session, username: str, password: str):
    if verify_password(username, password):
        # Set session data
        session['username'] = username
        session['login_time'] = datetime.now().isoformat()
        session['last_activity'] = datetime.now().isoformat()
        return RedirectResponse('/dashboard', status_code=303)

    return (
        Title("Login - Scraper App"),
        Body(
            Div(cls="login-container")(
                Div(cls="card")(
                    H1("🔐 Login"),
                    Div(cls="alert alert-error")("😕 Username or password incorrect"),
                    Form(action="/login", method="post")(
                        Div(cls="form-group")(
                            Label("Username/Email", fr="username"),
                            Input(type="text", name="username", id="username", required=True, value=username)
                        ),
                        Div(cls="form-group")(
                            Label("Password", fr="password"),
                            Input(type="password", name="password", id="password", required=True)
                        ),
                        Button("Login", type="submit")
                    )
                )
            )
        )
    )

@rt('/signup')
def get(session):
    # # Check authentication
    # if not session.get('username') or check_session_timeout(session):
    #     return RedirectResponse('/')

    return (
        Title("Signup - Scraper App"),
        Body(
            Div(id="signup_info"),
            Div(id="login-container", cls="login-container")(
                Div(cls="card")(
                    H1("🔐 Signup"),
                    Form(action="/signup", hx_post="/signup", hx_target="#login-container", hx_swap="outerHTML")(
                        Div(cls="form-group")(
                            Label("Username/Email", fr="username"),
                            Input(type="text", name="username", id="username", required=True)
                        ),
                        Div(cls="form-group")(
                            Label("Password", fr="password"),
                            Input(type="password", name="password", id="password", required=True)
                        ),
                        Div(cls="form-group")(
                            Label("Confirm Password", fr="confirm_password"),
                            Input(type="password", name="confirm_password", id="confirm_password", required=True)
                        ),
                        Button("Signup", type="submit")
                    )
                )
            )
        )
    )

@rt('/signup')
def post(session, username: str, password: str, confirm_password: str):
    if not (password == confirm_password):
        return Div(id="login-container", cls="alert alert-error")("Password must match")

    try:
        db.create_user(username, hash_password(password))
    except Exception as e:
        print(f"Error - {e}")
        return Div(id="login-container", cls="alert alert-error")("Password must match")
    return Div(id="login-container", cls="alert alert-success")(
        ("Account Created. Login now"),
        Hr(),
        A(Button("Login"), href="/")
    )


@rt('/logout')
def get(session):
    # Clear session
    session.clear()
    return RedirectResponse('/', status_code=303)

# Dashboard
@rt('/dashboard')
def get(session):
    # Check authentication
    if not session.get('username') or check_session_timeout(session):
        return RedirectResponse('/')
    
    # Update last activity
    session['last_activity'] = datetime.now().isoformat()
    
    username = session['username']
    login_time = datetime.fromisoformat(session['login_time'])
    last_activity = datetime.fromisoformat(session['last_activity'])

    session_duration = datetime.now() - login_time
    minutes_active = int(session_duration.total_seconds() / 60)

    time_since_activity = datetime.now() - last_activity
    minutes_until_timeout = SESSION_TIMEOUT_MINUTES - int(time_since_activity.total_seconds() / 60)


    return (
        Title("Scraper Dashboard"),
        Div(cls="sidebar")(
            H3(f"👤 {username}"),
            P(cls="caption")(f"⏱️ Session active: {minutes_active} min"),
            P(cls="caption")(f"🔒 Auto-logout in: {max(0, minutes_until_timeout)} min"),
            Hr(),
            Details(
                Summary("🔑 Change Password"),
                Form(method="post", hx_post="/change-password", hx_target="#pwd-msg", hx_swap="outerHTML", hx_on__after_request="console.log('Form submitted'); this.reset()")(
                    Div(cls="form-group")(
                        Label("Current Password"),
                        Input(type="password", name="current_password", required=True)
                    ),
                    Div(cls="form-group")(
                        Label("New Password"),
                        Input(type="password", name="new_password", required=True)
                    ),
                    Div(cls="form-group")(
                        Label("Confirm Password"),
                        Input(type="password", name="confirm_password", required=True)
                    ),
                    Button("Update Password", type="submit")
                ),
            ),
            Div(id="pwd-msg"),
            Hr(),
            A(Button("Logout"), href="/logout")
        ),

        Div(cls="main-content")(
            Div(cls="container")( 
                H1("Myworkdayjobs Scraper 👋"),
                Div(id="scraper-error"),
                Div(cls="card")(
                    H2("Start New Scraper"),
                    Form(action="/start-scraper", method="post", hx_target="#scraper-error")(
                        Div(cls="form-group")(
                            Label("Platform Link"),
                            Input(type="url", name="platform_link", placeholder="https://...", required=True)
                        ),
                        Div(cls="form-group")(
                            Label("Job Server ID"),
                            Input(type="number", name="jobserver_id", required=True)
                        ),
                        Label(
                            Input(type="checkbox", name="save_to_db", value="true"),
                            " Save to DB",
                        ),
                        Label(Input(type="checkbox", name="is_test", value="true"), "Perform Test run"),

                        Button("Submit", type="submit")
                    )
                ),

                # Progress display
                Div(cls="card", id="progress-section")(
                    H2("Scraper Progress"),
                    get_progress_content()
                )
            )
        ),
        Script("""
            document.addEventListener('DOMContentLoaded', function() {
                document.querySelectorAll('.expander-header').forEach(header => {
                    header.addEventListener('click', () => {
                        header.parentElement.classList.toggle('open');
                    });
                });
            });
            
            // Re-attach event listeners after HTMX swaps
            document.body.addEventListener('htmx:afterSwap', function() {
                document.querySelectorAll('.expander-header').forEach(header => {
                    header.addEventListener('click', () => {
                        header.parentElement.classList.toggle('open');
                    });
                });
            });
        """)
        )

def get_progress_content(status_filter="all"):
    all_progress = db.get_all_process()
    if not all_progress:
        return P(cls="alert alert-info")("No progress data available yet.")

    statuses = ["all"] + list(set(data.status for data in all_progress))

    filtered = [d for d in all_progress if status_filter == "all" or d.status == status_filter]

    return Div(
        Hr(),
        Button("⟳ Refresh", cls="refresh", 
               hx_get="/refresh",
               hx_target="#progress-section",
               hx_swap="innerHTML"
        ),
        Hr(),
        Label("Filter by status: "),
        Select(
            *[Option(s.capitalize(), value=s, selected=(s==status_filter)) for s in statuses],
            name="status_filter",
            hx_get="/filter-progress",
            hx_target="#progress-list",
            hx_include="[name='status_filter']"
        ),
        Hr(),
        Div(id="progress-list")(
            *[process_card(data) for data in filtered] if filtered else P(cls="alert alert-info")(f"No sites with status: {status_filter}")
        ),
    )

def process_card(data):
    progress = data.current / data.total if data.total > 0 else 0
    badge_class = f"badge-{data.status}"
    
    return Div(cls="expander")(
        Div(cls="expander-header")(
            f"📊 {data.platform} ",
            Span(cls=f"badge {badge_class}")(data.status.upper())
        ),
        Div(cls="expander-content")(
            # Main visible metrics
            Div(
                Div(cls="metric")(
                    Div(cls="metric-label")("Platform"),
                    Div(cls="metric-value")(str(data.platform))
                ),
                Div(cls="metric")(
                    Div(cls="metric-label")("ID"),
                    Div(cls="metric-value")(str(data.id))
                ),
                Div(cls="metric")(
                    Div(cls="metric-label")("URL"),
                    Div(cls="metric-value", style="font-size: 14px; word-break: break-all;")(
                        str(data.platform_url)
                    )
                ),
            ),
            
            # Nested expander for detailed metrics
            Details(
                Summary("📈 View Details"),
                Div(style="padding: 16px 0;")(
                    Div(cls="progress-bar")(
                        Div(cls="progress-fill", style=f"width: {progress*100}%")
                    ),
                    Div(
                        Div(cls="metric")(
                            Div(cls="metric-label")("Progress"),
                            Div(cls="metric-value")(f"{data.current}/{data.total}")
                        ),
                        Div(cls="metric")(
                            Div(cls="metric-label")("Completion"),
                            Div(cls="metric-value")(f"{progress*100:.1f}%")
                        ),
                        Div(cls="metric")(
                            Div(cls="metric-label")("✅ Successful"),
                            Div(cls="metric-value")(str(data.successful))
                        ),
                        Div(cls="metric")(
                            Div(cls="metric-label")("❌ Failed"),
                            Div(cls="metric-value")(str(data.failed))
                        ),
                    ),
                    P(cls="caption")(f"Last updated: {data.last_updated}"),
                    P(cls="caption")(f"Process ID: {data.process_id}")
                )
            ),
            
            # Action buttons
            Div(style="margin-top: 16px; display: flex; gap: 10px; flex-wrap: wrap;")(
                Button("🛑 Stop", cls="danger", 
                       hx_post=f"/stop-process/{data.platform}",
                       hx_target="#progress-section",
                       hx_swap="innerHTML") if data.status == "running" and data.process_id > 0 else None,
                Button("🗑️ Delete", cls="danger", 
                       hx_get=f"/delete-process/{data.process_id}",
                       hx_target="#progress-section",
                       hx_swap="innerHTML")
            ),
            Hr()
        )
    )

@rt('/filter-progress')
def get(status_filter: str = "all"):
    all_progress = db.get_all_process()
    filtered = [d for d in all_progress if status_filter == "all" or d.status == status_filter]

    if not filtered:
        return P(cls="alert alert-info")(f"No sites with status: {status_filter}")

    return Div(*[process_card(data) for data in filtered])

@rt('/change-password')
def post(session, current_password: str, new_password: str, confirm_password: str):
    # Check authentication
    if not session.get('username') or check_session_timeout(session):
        return Div(cls="alert alert-error")("Session expired. Please login again.")

    username = session['username']
    print(username, current_password, new_password, confirm_password)
    
    # Verify current password
    password_verified = verify_password(username, current_password)
    print(f"Password verified - {password_verified}")
    if not password_verified:
        return Div(cls="alert alert-error", id="pwd-msg")("Current password is incorrect")
    
    # Validate new password
    if len(new_password) < 6:
        return Div(cls="alert alert-error", id="pwd-msg")("Password must be at least 6 characters")
    
    if new_password != confirm_password:
        return Div(cls="alert alert-error", id="pwd-msg")("New passwords do not match")
    
    # Update password
    hashed_password = hash_password(new_password)
    result = db.update_user(username, hashed_password)

    if result:
        return Div(cls="alert alert-success", id="pwd-msg")("✅ Password updated successfully!")
    else:
        return Div(cls="alert alert-error", id="pwd-msg")("❌ Failed to update password")

def run_scraper_task(save_to_db, jobserver_id, platform_link, name, is_test):
    # This now exists in the global scope and can be pickled

    db.delete_jobs_by_company(jobserver_id)
    scraper = Workday(
        save=save_to_db == "true",
        companyid=int(jobserver_id),
        user_link=platform_link,
        name=name,
        is_test=is_test == "true",
        process_id=0
    )
    scraper.main()

@rt('/start-scraper')
def post(session, platform_link: str, jobserver_id: int, 
         save_to_db: str = "", is_test: str = ""):
    print(platform_link, jobserver_id, save_to_db, is_test)
    # Check authentication
    if not session.get('username') or check_session_timeout(session):
        return RedirectResponse('/')
    
    # Update last activity
    session['last_activity'] = datetime.now().isoformat()
    
    
    parsed_url = urlparse(platform_link)
    username = parsed_url.netloc.split(".")[0]
    name = f'Workday-{username}'

    p = Process(
            target=run_scraper_task, 
            args=(save_to_db, jobserver_id, platform_link, name, is_test)
        )
    p.start()

    time.sleep(5)
    try:
        if not p.pid:
            print("process ID is null")
            return Div(cls="alert alert-error", id="scraper-error")("Process ID is null")
        db.update_status(scraperStatus(
            id=jobserver_id,
            platform=name,
            platform_url=platform_link,
            status='running',
            process_id=p.pid
        ))
    except Exception as e:
        print(f"Error updating process ID: {e}")

    return RedirectResponse('/dashboard', status_code=303)

@rt('/stop-process/{platform}')
def post(session, platform: str):
    print('Platform', platform)
    # Check authentication
    if not session.get('username') or check_session_timeout(session):
        return RedirectResponse('/')
    
    # Update last activity
    session['last_activity'] = datetime.now().isoformat()
    
    try:
        all_progress = db.get_all_process()
        process = next((p for p in all_progress if p.platform == platform), None)

        if process and process.process_id > 0:
            try:
                os.kill(process.process_id, signal.SIGKILL)
            except ProcessLookupError:
                print(f"Process {process.process_id} not found")
            except Exception as e:
                print(f"Error killing process: {e}")
            
            db.update_process_status("stopped", platform)
    except Exception as e:
        print(f"Error stopping process: {e}")

    return Div(
        H2("Scraper Progress"),
        get_progress_content()
    )


@rt('/delete-process/{process_id}')
def get(session, process_id: int):
    print('Process ID', process_id)
    # Check authentication
    if not session.get('username') or check_session_timeout(session):
        return RedirectResponse('/')
    
    # Update last activity
    session['last_activity'] = datetime.now().isoformat()
    
    try:            
        db.delete_process(process_id)
    except Exception as e:
        print(f"Error stopping process: {e}")

    return Div(
        H2("Scraper Progress"),
        get_progress_content()
    )

@rt('/refresh')
def get(session):
    # Check authentication
    if not session.get('username') or check_session_timeout(session):
        return RedirectResponse('/')
    return Div(
        H2("Scraper Progress"),
        get_progress_content()
    )

serve()
