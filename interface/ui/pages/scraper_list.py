"""
Scraper list page - Shows available scrapers and allows launching them
"""
from nicegui import ui
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware

class ScraperListPage:
    """Page showing list of available scrapers"""
    
    def __init__(self, db: Database, auth: AuthMiddleware):
        self.db = db
        self.auth = auth
        self._register_page()
    
    def _register_page(self):
        """Register the scraper list page route"""
        # Redirect to login if not authenticated
        if not self.auth.is_authenticated():
            ui.navigate.to('/login')
            return
    
    def main(self):
        """Render the scraper list UI"""
        session_info = self.auth.get_session_info()
        username = session_info['username']
        
        # Get scrapers for the selected type
        scrapers = [
            {'title': 'Test scraper', 'name': 'Test scraper'}
        ]
        
        with ui.column().classes('w-full min-h-screen p-6'):
            # Header
            with ui.row().classes('w-full justify-between items-center mb-6'):
                with ui.row().classes('items-center gap-4'):
                    ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/dashboard')).props('flat round')
                    ui.label('📋 Scrapers').classes('text-3xl font-bold')
                
                with ui.row().classes('items-center gap-4'):
                    ui.label(f'👤 {username}').classes('text-lg')
                    
                    def handle_logout():
                        self.auth.logout()
                        ui.notify('Logged out successfully', type='info')
                        ui.navigate.to('/')
                    
                    ui.button('Logout', on_click=handle_logout, icon='logout').props('flat color=negative')
            
            ui.separator().classes('mb-6')
            
            # Stats bar
            with ui.row().classes('w-full gap-4 mb-6'):
                with ui.card().classes('flex-1 p-4'):
                    with ui.row().classes('items-center gap-4'):
                        ui.icon('list', size='32px').classes('text-blue-500')
                        with ui.column():
                            ui.label('Available Scrapers').classes('text-xs text-gray-500')
                            ui.label(str(len(scrapers))).classes('text-2xl font-bold')
                
                with ui.card().classes('flex-1 p-4'):
                    with ui.row().classes('items-center gap-4'):
                        ui.icon('play_circle', size='32px').classes('text-green-500')
                        with ui.column():
                            ui.label('Active Scrapers').classes('text-xs text-gray-500')
                            active_count = len([p for p in self.db.get_all_process() if p.status == 'running'])
                            ui.label(str(active_count)).classes('text-2xl font-bold')
            
            # Search and filter
            with ui.row().classes('w-full gap-4 mb-6'):
                search_input = ui.input(
                    label='Search scrapers',
                    placeholder='Search by name or description...'
                ).classes('flex-1').props('outlined clearable')
                
                ui.button('Refresh', on_click=lambda: ui.navigate.reload(), icon='refresh').props('color=primary')
            
            # Scrapers grid
            if not scrapers:
                with ui.card().classes('w-full p-12 text-center'):
                    ui.icon('inbox', size='64px').classes('text-gray-400 mb-4')
                    ui.label('No scrapers available').classes('text-xl text-gray-500')
                    ui.label('Check your configuration file').classes('text-sm text-gray-400')
            else:
                scraper_container = ui.column().classes('w-full gap-4')
                
                def filter_scrapers():
                    scraper_container.clear()
                    search_term = search_input.value.lower() if search_input.value else ''
                    
                    filtered = [
                        s for s in scrapers 
                        if search_term in s['name'].lower() or 
                           search_term in s.get('description', '').lower()
                    ]
                    
                    with scraper_container:
                        for scraper in filtered:
                            self._render_scraper_card(scraper)
                
                # Initial render
                for scraper in scrapers:
                    with scraper_container:
                        self._render_scraper_card(scraper)
                
                # Update on search
                search_input.on('input', filter_scrapers)
    
    def _render_scraper_card(self, scraper: dict):
        """Render a single scraper card"""
        with ui.card().classes('w-full p-6 hover:shadow-lg transition-shadow'):
            with ui.row().classes('w-full items-start gap-6'):
                # Icon/Logo
                icon_name = scraper.get('icon', 'settings')
                color = scraper.get('color', 'blue')
                
                with ui.column().classes('items-center'):
                    ui.icon(icon_name, size='48px').classes(f'text-{color}-500')
                
                # Details
                with ui.column().classes('flex-1 gap-2'):
                    # Name and status
                    with ui.row().classes('w-full items-center gap-4'):
                        ui.label(scraper['name']).classes('text-2xl font-bold')
                        
                        if scraper.get('enabled', True):
                            ui.badge('Active', color='green')
                        else:
                            ui.badge('Disabled', color='red')
                    
                    # Description
                    ui.label(scraper.get('description', 'No description available')).classes('text-gray-600 dark:text-gray-400')
                    
                    # Metadata
                    with ui.row().classes('gap-6 mt-2'):
                        if 'version' in scraper:
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('info', size='16px').classes('text-gray-500')
                                ui.label(f"v{scraper['version']}").classes('text-xs text-gray-500')
                        
                        if 'author' in scraper:
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('person', size='16px').classes('text-gray-500')
                                ui.label(scraper['author']).classes('text-xs text-gray-500')
                        
                        if 'category' in scraper:
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('category', size='16px').classes('text-gray-500')
                                ui.label(scraper['category']).classes('text-xs text-gray-500')
                    
                    # Features/Capabilities
                    if 'features' in scraper and scraper['features']:
                        with ui.expansion('Features', icon='stars').classes('mt-2 w-full'):
                            with ui.column().classes('gap-1'):
                                for feature in scraper['features']:
                                    ui.label(f'✓ {feature}').classes('text-sm')
                    
                    # Configuration requirements
                    if 'required_config' in scraper and scraper['required_config']:
                        with ui.expansion('Required Configuration', icon='settings').classes('mt-2 w-full'):
                            with ui.column().classes('gap-1'):
                                for config_key in scraper['required_config']:
                                    ui.label(f'• {config_key}').classes('text-sm text-gray-600 dark:text-gray-400')
                
                # Action buttons
                with ui.column().classes('gap-2 items-end'):
                    # Launch button
                    if scraper.get('enabled', True):
                        ui.button(
                            'Launch Scraper',
                            on_click=lambda s=scraper: self._launch_scraper(s),
                            icon='play_arrow'
                        ).props('color=primary')
                    else:
                        ui.button('Disabled', icon='block').props('disable color=grey')
                    
                    # Configure button
                    ui.button(
                        'Configure',
                        on_click=lambda s=scraper: self._configure_scraper(s),
                        icon='settings'
                    ).props('flat color=secondary')
                    
                    # View details button
                    ui.button(
                        'Details',
                        on_click=lambda s=scraper: self._view_details(s),
                        icon='info'
                    ).props('flat color=grey')
    
    def _launch_scraper(self, scraper: dict):
        """Launch a scraper"""
        # Show configuration dialog
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6'):
            ui.label(f'Launch {scraper["name"]}').classes('text-xl font-bold mb-4')
            
            # Dynamic input fields based on required_config
            inputs = {}
            required_config = scraper.get('required_config', [])
            
            for config_key in required_config:
                if config_key == 'platform_link':
                    inputs[config_key] = ui.input(
                        label='Platform Link',
                        placeholder='https://...'
                    ).classes('w-full').props('outlined')
                elif config_key == 'jobserver_id':
                    inputs[config_key] = ui.input(
                        label='Job Server ID',
                        placeholder='Enter ID'
                    ).classes('w-full').props('outlined')
                else:
                    inputs[config_key] = ui.input(
                        label=config_key.replace('_', ' ').title(),
                        placeholder=f'Enter {config_key}'
                    ).classes('w-full').props('outlined')
            
            # Optional settings
            save_to_db = ui.checkbox('Save to Database', value=True)
            is_test = ui.checkbox('Test Run', value=False)
            
            def start_scraper():
                # Validate inputs
                config = {}
                for key, input_field in inputs.items():
                    if not input_field.value:
                        ui.notify(f'Please fill in {key}', type='negative')
                        return
                    config[key] = input_field.value
                
                # Launch scraper
                try:
                    result = self.scraper_launcher.launch(
                        scraper_id=scraper['id'],
                        scraper_class=scraper['class'],
                        config=config,
                        save_to_db=save_to_db.value,
                        is_test=is_test.value
                    )
                    
                    if result:
                        ui.notify(f'{scraper["name"]} launched successfully!', type='positive')
                        dialog.close()
                        ui.timer(1.0, lambda: ui.navigate.to('/dashboard'), once=True)
                    else:
                        ui.notify('Failed to launch scraper', type='negative')
                except Exception as e:
                    ui.notify(f'Error: {str(e)}', type='negative')
            
            with ui.row().classes('w-full gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Launch', on_click=start_scraper, icon='play_arrow').props('color=primary')
        
        dialog.open()
    
    def _configure_scraper(self, scraper: dict):
        """Open scraper configuration"""
        ui.notify(f'Configure {scraper["name"]} - Coming soon', type='info')
    
    def _view_details(self, scraper: dict):
        """View scraper details"""
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6'):
            ui.label(scraper['name']).classes('text-2xl font-bold mb-4')
            
            ui.separator().classes('mb-4')
            
            ui.label('Description').classes('text-sm font-bold text-gray-500 mb-2')
            ui.label(scraper.get('description', 'No description')).classes('mb-4')
            
            if 'class' in scraper:
                ui.label('Python Class').classes('text-sm font-bold text-gray-500 mb-2')
                ui.label(scraper['class']).classes('font-mono text-sm mb-4')
            
            if 'module' in scraper:
                ui.label('Module').classes('text-sm font-bold text-gray-500 mb-2')
                ui.label(scraper['module']).classes('font-mono text-sm mb-4')
            
            ui.button('Close', on_click=dialog.close).props('flat')
        
        dialog.open()
