"""
Sidebar component for navigation and user info
"""
from nicegui import ui
from src.storage.database import Database
from interface.middleware.auth import AuthMiddleware

class Sidebar:
    """Sidebar component"""
    
    def __init__(self, db: Database, auth: AuthMiddleware):
        self.db = db
        self.auth = auth
        self._render()
    
    def _render(self):
        """Render the sidebar"""
        session_info = self.auth.get_session_info()
        username = session_info['username']
        minutes_active = session_info['minutes_active']
        minutes_until_timeout = session_info['minutes_until_timeout']
        
        # User info
        ui.label(f'👤 {username}').classes('text-xl font-bold mb-2')
        ui.label(f'⏱️ Session active: {minutes_active} min').classes('caption text-sm mb-1')
        ui.label(f'🔒 Auto-logout in: {minutes_until_timeout} min').classes('caption text-sm mb-4')
        
        ui.separator()
        
        # Change password section
        with ui.expansion('Change Password', icon='key').classes('w-full mb-4'):
            current_password = ui.input(
                label='Current Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full').props('outlined dense')
            
            new_password = ui.input(
                label='New Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full').props('outlined dense')
            
            confirm_password = ui.input(
                label='Confirm Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full').props('outlined dense')
            
            message_container = ui.row().classes('w-full')
            
            def change_password():
                message_container.clear()
                
                if not current_password.value or not new_password.value or not confirm_password.value:
                    with message_container:
                        ui.notify('Please fill in all fields', type='negative')
                    return
                
                # Verify current password
                if not self.auth.verify_password(username, current_password.value):
                    with message_container:
                        ui.label('❌ Current password is incorrect').classes('text-red-500 text-xs')
                    return
                
                # Validate new password
                if len(new_password.value) < self.auth.settings.MIN_PASSWORD_LENGTH:
                    with message_container:
                        ui.label(
                            f'❌ Password must be at least {self.auth.settings.MIN_PASSWORD_LENGTH} characters'
                        ).classes('text-red-500 text-xs')
                    return
                
                if new_password.value != confirm_password.value:
                    with message_container:
                        ui.label('❌ New passwords do not match').classes('text-red-500 text-xs')
                    return
                
                # Update password
                try:
                    hashed_password = self.auth.hash_password(new_password.value)
                    result = self.db.update_user(username, hashed_password)
                    
                    if result:
                        with message_container:
                            ui.label('✅ Password updated!').classes('text-green-500 text-xs')
                        ui.notify('Password updated successfully!', type='positive')
                        
                        # Clear inputs
                        current_password.value = ''
                        new_password.value = ''
                        confirm_password.value = ''
                    else:
                        with message_container:
                            ui.label('❌ Failed to update').classes('text-red-500 text-xs')
                except Exception as e:
                    with message_container:
                        ui.label(f'❌ Error: {str(e)}').classes('text-red-500 text-xs')
            
            ui.button('Update Password', on_click=change_password).props('color=primary size=sm').classes('w-full')
        
        ui.separator()
        
        # Logout button
        def handle_logout():
            self.auth.logout()
            ui.notify('Logged out successfully', type='info')
            ui.navigate.to('/')
        
        ui.button('Logout', on_click=handle_logout, icon='logout').props('color=negative').classes('w-full')
