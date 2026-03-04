"""
Configuration settings for the Fashion Wardrobe application
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://giaphuc:password@localhost:5432/fashion_wardrobe')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Admin login (Option A: single admin, credentials in .env)
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')
    ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', '')  # Set in .env; returned on successful login
    
    # Paths
    BASE_DIR = Path(__file__).resolve().parent
    UPLOAD_FOLDER = Path(os.getenv('UPLOAD_FOLDER', './data/uploads'))
    OUTPUT_FOLDER = Path(os.getenv('OUTPUT_FOLDER', './output'))
    
    # Ensure directories exist
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Server
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    
    # File upload settings
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.avif'}
    
    @classmethod
    def get_upload_path(cls, filename: str) -> Path:
        """Get full upload path for a filename"""
        return cls.UPLOAD_FOLDER / filename
    
    @classmethod
    def get_output_path(cls, filename: str) -> Path:
        """Get full output path for a filename"""
        return cls.OUTPUT_FOLDER / filename
