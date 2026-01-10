"""
Scraper list page - Shows available scrapers and allows launching them
"""
from nicegui import ui
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware
from interface.utils.start_scraper import start_generic_scraper

scrapers = [
    {
        'name': 'Wise', 
        'color': 'green', 
        'enabled': True,
        'platform_link': 'https://wise.jobs/jobs',
        'id': 18
    },
    {
        'name': 'Adidas', 
        'color': 'green', 
        'enabled': True,
        'platform_link': 'https://careers.adidas-group.com/jobs',
        'id': 41
    },
    {
        'name': 'Airbnb', 
        'color': 'green', 
        'enabled': True,
        'platform_link': 'https://careers.airbnb.com/positions',
        'id': 19
    },
    {
        'name': 'Apple',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://jobs.apple.com/en-us/search',
        'id': 21
    },
    {
        'name': 'ATT',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://att.jobs/search',
        'id': 30
    },
    {
        'name': 'Bank of America',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://careers.bankofamerica.com/en-us/job-search',
        'id': 33
    },
    {
        'name': 'Capitec Bank',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://www.capitecbank.co.za/careers',
        'id': 35
    },
    {
        'name': 'Cisco',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://jobs.cisco.com/jobs/SearchJobs',
        'id': 34
    },
    {
        'name': 'Coinbase',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://www.coinbase.com/careers/positions',
        'id': 32
    },
    {
        'name': 'Ecolab',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://ecolab.wd5.myworkdayjobs.com/Ecolab_Careers',
        'id': 15
    },
    {
        'name': 'Google',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://www.google.com/about/careers/applications',
        'id': 22
    },
    {
        'name': 'Capgemini',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://www.capgemini.com/careers/job-search',
        'id': 47
    },
    {
        'name': 'Dangote',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://careers.dangote.com/jobs',
        'id': 54
    },
    {
        'name': 'Huawei',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://career.huawei.com/reccampportal/portal5/campus-recruitment.html',
        'id': 900
    },
    {
        'name': 'Julius Berger',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://www.juliusberger.com/careers',
        'id': 199
    },
    {
        'name': 'Sanofi',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://jobs.sanofi.com/en/jobs',
        'id': 899
    },
    {
        'name': 'Siemens',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://jobs.siemens.com/careers',
        'id': 10
    },
    {
        'name': 'Sysco',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://sysco.wd1.myworkdayjobs.com/SyscoJobs',
        'id': 75
    },
    {
        'name': 'Verizon',
        'color': 'green',
        'enabled': True,
        'platform_link': 'https://www.verizon.com/about/work/jobs',
        'id': 31
    },
]


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
                search_input.on_value_change(filter_scrapers)
    
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

                with ui.row().classes('w-full items-start gap-6'):
                    scraper_info = self.db.get_process(scraper['id'])
                    # Progress Information (if scraper is running) - In Expansion
                    if scraper_info:
                        with ui.expansion('Current Progress', icon='analytics').classes('mt-2 w-full'):
                            with ui.column().classes('w-full gap-2 p-3 bg-blue-50 dark:bg-blue-900 rounded'):
                                # Status header
                                with ui.row().classes('w-full items-center justify-between mb-2'):
                                    ui.label('Status').classes('text-sm font-bold')
                                    ui.chip(scraper_info.status.upper())
                                
                                # Progress bar
                                if scraper_info.total > 0:
                                    progress = scraper_info.current / scraper_info.total
                                    with ui.column().classes('w-full gap-1 mt-2'):
                                        ui.linear_progress(progress).props('stripe rounded color=primary')
                                        ui.label(
                                            f'{scraper_info.current}/{scraper_info.total} ({progress*100:.1f}%)'
                                        ).classes('text-xs text-gray-600 dark:text-gray-300')
                                
                                # Stats row
                                with ui.row().classes('w-full gap-4 mt-2'):
                                    with ui.column().classes('items-center'):
                                        ui.label('✅ Success').classes('text-xs text-gray-600 dark:text-gray-300')
                                        ui.label(str(scraper_info.successful)).classes('text-lg font-bold text-green-600 dark:text-green-400')
                                    
                                    with ui.column().classes('items-center'):
                                        ui.label('❌ Failed').classes('text-xs text-gray-600 dark:text-gray-300')
                                        ui.label(str(scraper_info.failed)).classes('text-lg font-bold text-red-600 dark:text-red-400')
                                    
                                    with ui.column().classes('flex-1'):
                                        ui.label('🕐 Last Updated').classes('text-xs text-gray-600 dark:text-gray-300')
                                        ui.label(str(scraper_info.last_updated)).classes('text-xs text-gray-700 dark:text-gray-300')
                                
                                # Platform info
                                ui.separator().classes('my-2')
                                with ui.column().classes('w-full gap-1'):
                                    ui.label(f'Platform: {scraper_info.platform}').classes('text-xs text-gray-600 dark:text-gray-300')
                                    ui.label(f'Process ID: {scraper_info.process_id}').classes('text-xs text-gray-600 dark:text-gray-300')
                                    if scraper_info.platform_url:
                                        ui.label('URL:').classes('text-xs text-gray-600 dark:text-gray-300 mt-1')
                                        ui.label(str(scraper_info.platform_url)).classes('text-xs break-all text-gray-700 dark:text-gray-300')
                
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
    
    def _launch_scraper(self, scraper: dict):
        """Launch a scraper"""
        # Show configuration dialog
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6'):
            ui.label(f'Launch {scraper["name"]}').classes('text-xl font-bold mb-4')
            
            # Dynamic input fields based on required_config
            inputs = {}

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
                # try:
                result = start_generic_scraper(
                    db=self.db, 
                    jobserver_id=scraper['id'],
                    is_test=is_test.value,
                    save_to_db=save_to_db.value,
                    name=scraper['name'],
                    platform_link=scraper['platform_link']
                )
                
                if result:
                    ui.notify(f'{scraper["name"]} launched successfully!', type='positive')
                    dialog.close()
                    ui.timer(1.0, lambda: ui.navigate.to('/generic-scraper'), once=True)
                else:
                    ui.notify('Failed to launch scraper', type='negative')
                # except Exception as e:
                #     ui.notify(f'Error: {str(e)}', type='negative')
            
            with ui.row().classes('w-full gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Launch', on_click=start_scraper, icon='play_arrow').props('color=primary')
        
        dialog.open()

