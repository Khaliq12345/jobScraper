"""
Authentication middleware for session management
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from nicegui import app, ui
from src.storage.database import Database
from interface.config import Settings

class AuthMiddleware:
    """Handles authentication and session management"""
    
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify username and password against database"""
        user = self.db.get_user(username)
        if user:
            password_hash = self.hash_password(password)
            return user.password == password_hash
        return False
    
    def check_session_timeout(self) -> bool:
        """Check if session has timed out"""
        last_activity = app.storage.user.get('last_activity')
        if last_activity:
            last_activity_time = datetime.fromisoformat(last_activity)
            timeout = timedelta(minutes=self.settings.SESSION_TIMEOUT_MINUTES)
            return datetime.now() - last_activity_time > timeout
        return True
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        username = app.storage.user.get('username')
        return username is not None and not self.check_session_timeout()
    
    def login(self, username: str) -> None:
        """Log in a user"""
        app.storage.user['username'] = username
        app.storage.user['login_time'] = datetime.now().isoformat()
        self.update_last_activity()
    
    def logout(self) -> None:
        """Log out the current user"""
        app.storage.user.clear()
    
    def update_last_activity(self) -> None:
        """Update the last activity timestamp"""
        app.storage.user['last_activity'] = datetime.now().isoformat()
    
    def get_username(self) -> Optional[str]:
        """Get the current username"""
        return app.storage.user.get('username')
    
    def get_session_info(self) -> dict:
        """Get session information"""
        login_time = app.storage.user.get('login_time')
        last_activity = app.storage.user.get('last_activity')
        
        minutes_active = 0
        minutes_until_timeout = self.settings.SESSION_TIMEOUT_MINUTES
        
        if login_time:
            login_dt = datetime.fromisoformat(login_time)
            minutes_active = int((datetime.now() - login_dt).total_seconds() / 60)
        
        if last_activity:
            last_activity_dt = datetime.fromisoformat(last_activity)
            time_since = datetime.now() - last_activity_dt
            minutes_until_timeout = self.settings.SESSION_TIMEOUT_MINUTES - int(time_since.total_seconds() / 60)
        
        return {
            'username': self.get_username(),
            'minutes_active': minutes_active,
            'minutes_until_timeout': max(0, minutes_until_timeout)
        }
    
    def require_auth(self, target_page: str = '/'):
        """Decorator/helper to require authentication"""
        if not self.is_authenticated():
            ui.navigate.to(target_page)
            return False
        self.update_last_activity()
        return True
