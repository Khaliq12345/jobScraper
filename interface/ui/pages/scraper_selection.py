"""
Scraper selection page - Choose between Generic and Workday scrapers
"""
from nicegui import ui
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware

class ScraperSelectionPage:
    """Main dashboard for selecting scraper type"""
    
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
        """Render the scraper selection UI"""
        session_info = self.auth.get_session_info()
        username = session_info['username']
        
        with ui.column().classes('w-full min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-8'):
            # Header with user info
            with ui.row().classes('w-full max-w-6xl justify-between items-center mb-8'):
                ui.label(f'👤 {username}').classes('text-lg font-semibold')
                
                def handle_logout():
                    self.auth.logout()
                    ui.notify('Logged out successfully', type='info')
                    ui.navigate.to('/')
                
                ui.button('Logout', on_click=handle_logout, icon='logout').props('flat color=negative')
            
            # Main content card
            with ui.card().classes('w-full max-w-4xl p-12 shadow-2xl'):
                # Title
                ui.label('🚀 Welcome to Scraper Dashboard').classes('text-4xl font-bold text-center mb-4')
                ui.label('Choose your scraper type to get started').classes('text-xl text-gray-600 dark:text-gray-400 text-center mb-12')
                
                ui.separator().classes('mb-12')
                
                # Scraper options
                with ui.row().classes('w-full gap-8 justify-center items-stretch'):
                    # Generic Scraper Card
                    with ui.card().classes('flex-1 max-w-md p-8 hover:shadow-xl transition-shadow cursor-pointer border-2 border-transparent hover:border-blue-500'):
                        with ui.column().classes('w-full items-center gap-6'):
                            # Icon
                            ui.icon('language', size='64px').classes('text-blue-500')
                            
                            # Title
                            ui.label('Generic Scraper').classes('text-2xl font-bold text-center')
                            
                            # Button
                            ui.button(
                                'Select Generic Scraper',
                                on_click=lambda: ui.navigate.to('/generic-scraper'),
                                icon='arrow_forward'
                            ).props('size=lg color=blue').classes('w-full mt-6')
                    
                    # Workday Scraper Card
                    with ui.card().classes('flex-1 max-w-md p-8 hover:shadow-xl transition-shadow cursor-pointer border-2 border-transparent hover:border-green-500'):
                        with ui.column().classes('w-full items-center gap-6'):
                            # Icon
                            ui.icon('work', size='64px').classes('text-green-500')
                            
                            # Title
                            ui.label('Workday Scraper').classes('text-2xl font-bold text-center')
                            
                            # Button
                            ui.button(
                                'Select Workday Scraper',
                                on_click=lambda: ui.navigate.to('/workday-scraper'),
                                icon='arrow_forward'
                            ).props('size=lg color=green').classes('w-full mt-6')
                
    
    def _render_feature(self, text: str):
        """Render a feature item"""
        ui.label(text).classes('text-sm text-gray-700 dark:text-gray-300')
    
    def _render_stat(self, label: str, value: str, icon: str):
        """Render a stat card"""
        with ui.column().classes('items-center gap-2'):
            ui.icon(icon, size='32px').classes('text-gray-500')
            ui.label(value).classes('text-2xl font-bold')
            ui.label(label).classes('text-xs text-gray-500 uppercase')
