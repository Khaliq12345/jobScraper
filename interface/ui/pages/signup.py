"""
Signup page for the application
"""
from nicegui import ui
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware

class SignupPage:
    """Signup page handler"""
    
    def __init__(self, db: Database, auth: AuthMiddleware):
        self.db = db
        self.auth = auth
        self._register_page()
    
    def _register_page(self):
        """Register the signup page route"""

        # Redirect if already authenticated
        if self.auth.is_authenticated():
            ui.navigate.to('/')
            return

        self.main()
    
    def main(self):
        """Render the signup page UI"""
        with ui.column().classes('w-full items-center justify-center min-h-screen'):
            with ui.card().classes('w-96 p-6'):
                ui.label('🔐 Sign Up').classes('text-2xl font-bold mb-4')
                
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
                
                confirm_password_input = ui.input(
                    label='Confirm Password',
                    placeholder='Confirm password',
                    password=True,
                    password_toggle_button=True
                ).classes('w-full').props('outlined')
                
                # Message container
                message_container = ui.row().classes('w-full')
                
                # Signup button
                def handle_signup():
                    message_container.clear()
                    
                    username = username_input.value
                    password = password_input.value
                    confirm_password = confirm_password_input.value
                    
                    # Validation
                    if not username or not password or not confirm_password:
                        with message_container:
                            ui.notify('Please fill in all fields', type='negative')
                        return
                    
                    if password != confirm_password:
                        with message_container:
                            ui.label('❌ Passwords do not match').classes('text-red-500 text-sm')
                        return
                    
                    if len(password) < self.auth.settings.MIN_PASSWORD_LENGTH:
                        with message_container:
                            ui.label(
                                f'❌ Password must be at least {self.auth.settings.MIN_PASSWORD_LENGTH} characters'
                            ).classes('text-red-500 text-sm')
                        return
                    
                    # Try to create user
                    try:
                        password_hash = self.auth.hash_password(password)
                        self.db.create_user(username, password_hash)
                        
                        with message_container:
                            ui.label('✅ Account created successfully!').classes('text-green-500 text-sm')
                        
                        ui.notify('Account created! Redirecting to login...', type='positive')
                        ui.timer(2.0, lambda: ui.navigate.to('/login'), once=True)
                        
                    except Exception as e:
                        with message_container:
                            ui.label(f'❌ Error creating account: {str(e)}').classes('text-red-500 text-sm')
                
                ui.button('Sign Up', on_click=handle_signup).classes('w-full').props('color=primary')
                
                # Login link
                with ui.row().classes('w-full justify-center mt-4'):
                    ui.label('Already have an account?').classes('text-sm')
                    ui.link('Login', '/login').classes('text-sm text-blue-500')
                
                # Allow Enter key to submit
                confirm_password_input.on('keydown.enter', handle_signup)
