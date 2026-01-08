"""
Login page for the application
"""
from nicegui import ui
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware


class LoginPage:
    """Login page handler"""
    
    def __init__(self, db: Database, auth: AuthMiddleware):
        self.db = db
        self.auth = auth
        self._register_page()
    
    def _register_page(self):
        """Register the login page route"""

        # Redirect if already authenticated
        if self.auth.is_authenticated():
            ui.navigate.to('/')
            return

        self.main()
    
    def main(self):
        """Render the login page UI"""
        with ui.column().classes('w-full items-center justify-center min-h-screen'):
            with ui.card().classes('w-96 p-6'):
                ui.label('🔐 Login').classes('text-2xl font-bold mb-4')
                
                # Input fields
                username_input = ui.input(
                    label='Username/Email',
                    placeholder='Enter username or email'
                ).classes('w-full').props('outlined')
                
                password_input = ui.input(
                    label='Password',
                    placeholder='Enter password',
                    password=True,
                    password_toggle_button=True
                ).classes('w-full').props('outlined')
                
                # Error message container
                error_container = ui.row().classes('w-full')
                
                # Login button
                def handle_login():
                    error_container.clear()
                    
                    username = username_input.value
                    password = password_input.value
                    
                    if not username or not password:
                        with error_container:
                            ui.notify('Please enter both username and password', type='negative')
                        return
                    
                    if self.auth.verify_password(username, password):
                        self.auth.login(username)
                        ui.notify('Login successful!', type='positive')
                        ui.navigate.to('/dashboard')
                    else:
                        with error_container:
                            ui.label('😕 Username or password incorrect').classes(
                                'text-red-500 text-sm'
                            )
                
                ui.button('Login', on_click=handle_login).classes('w-full').props('color=primary')
                
                # Signup link
                with ui.row().classes('w-full justify-center mt-4'):
                    ui.label("Don't have an account?").classes('text-sm')
                    ui.link('Sign up', '/signup').classes('text-sm text-blue-500')
                
                # Allow Enter key to submit
                password_input.on('keydown.enter', handle_login)
                username_input.on('keydown.enter', handle_login)
