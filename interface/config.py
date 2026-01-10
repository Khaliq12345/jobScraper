"""
Application configuration settings
"""
import os
from dataclasses import dataclass

@dataclass
class Settings:
    """Application settings"""
    SESSION_TIMEOUT_MINUTES: int = 300
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
    MIN_PASSWORD_LENGTH: int = 6
    
    # Database settings
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'scraper.db')
    
    # Scraper settings
    DEFAULT_SCRAPER_PLATFORM: str = 'Workday'
