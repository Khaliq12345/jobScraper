"""
Main entry point for the NiceGUI Scraper Application
"""
from nicegui import app, ui
from interface.config import Settings
from interface.ui.pages.login import LoginPage
from interface.middleware.auth import AuthMiddleware
from interface.ui.pages.scraper_list import ScraperListPage
from interface.ui.pages.signup import SignupPage
from interface.ui.pages.dashboard import DashboardPage
from interface.ui.pages.scraper_selection import ScraperSelectionPage
from src.storage.database import Database

# Initialize database
db = Database()
settings = Settings()

# Initialize authentication middleware
auth = AuthMiddleware(db, settings)


@ui.page('/login')
def login():
    LoginPage(db, auth).main()

@ui.page('/signup')
def signup():
    SignupPage(db, auth).main()

@ui.page('/workday-scraper')
def workday_dashboard():
    DashboardPage(db, auth).main()

@ui.page('/generic-scraper')
def generic_dashboard():
    ScraperListPage(db, auth).main()

@ui.page('/dashboard')
def dashboard():
    ScraperSelectionPage(db, auth).main()


@ui.page('/')
def root():
    """Initialize the application"""
    # Apply dark mode based on user preference
    ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
    ui.navigate.to('/dashboard')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        root=root,
        title="Scraper Dashboard",
        port=8080,
        reload=True,
        show=False,
        storage_secret=settings.SECRET_KEY
    )
