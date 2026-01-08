"""
Dashboard page for the application
"""
from nicegui import ui
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware
from interface.ui.components.sidebar import Sidebar
from interface.ui.components.scraper_form import ScraperForm
from interface.ui.components.progress_display import ProgressDisplay

class DashboardPage:
    """Dashboard page handler"""
    
    def __init__(self, db: Database, auth: AuthMiddleware):
        self.db = db
        self.auth = auth
        self._register_page()
    
    def _register_page(self):
        """Register the dashboard page route"""
        # Redirect to login if not authenticated
        if not self.auth.is_authenticated():
            ui.navigate.to('/login')
            return

    
    def main(self):
        """Render the dashboard UI"""
        with ui.row().classes('w-full min-h-screen'):
            # Sidebar
            with ui.column().classes('w-64 bg-gray-100 dark:bg-gray-800 p-4'):
                Sidebar(self.db, self.auth)
            
            # Main content
            with ui.column().classes('flex-1 p-6'):
                ui.label('Myworkdayjobs Scraper 👋').classes('text-3xl font-bold mb-6')
                
                # Scraper form
                with ui.card().classes('w-full p-6 mb-6'):
                    ui.label('Start New Scraper').classes('text-xl font-bold mb-4')
                    ScraperForm(self.db, self.auth)
                
                # Progress display
                with ui.card().classes('w-full p-6'):
                    ui.label('Scraper Progress').classes('text-xl font-bold mb-4')
                    ProgressDisplay(self.db, self.auth)
