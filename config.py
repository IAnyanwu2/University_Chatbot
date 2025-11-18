# Production Configuration for GSU CS Chatbot

import os
from pathlib import Path

class ProductionConfig:
    """Production configuration for university deployment"""
    
    # Core Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    DEBUG = False
    TESTING = False
    
    # Server configuration
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Ollama configuration
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'localhost')
    OLLAMA_PORT = int(os.environ.get('OLLAMA_PORT', 11434))
    OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', 60))
    
    # Cache and data settings
    CACHE_DIR = Path(os.environ.get('CACHE_DIR', '/app/data'))
    MAX_CACHE_SIZE = int(os.environ.get('MAX_CACHE_SIZE_MB', 1024))  # 1GB default
    REFRESH_SCHEDULE = os.environ.get('REFRESH_SCHEDULE', '0 3 * * *')  # 3 AM daily
    
    # Security settings
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Request limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    RATELIMIT_DEFAULT = "60 per minute"
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = Path(os.environ.get('LOG_DIR', '/app/logs'))
    
    # Performance
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache for static files
    
    @staticmethod
    def init_app(app):
        """Initialize production configuration"""
        # Create required directories
        ProductionConfig.CACHE_DIR.mkdir(exist_ok=True)
        ProductionConfig.LOG_DIR.mkdir(exist_ok=True)
        
        # Configure logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            # File logging
            file_handler = RotatingFileHandler(
                ProductionConfig.LOG_DIR / 'chatbot.log',
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('GSU CS Chatbot startup')

class DevelopmentConfig:
    """Development configuration"""
    DEBUG = True
    SECRET_KEY = 'dev-secret-key'
    OLLAMA_HOST = 'localhost'
    CACHE_DIR = Path('./data')
    LOG_LEVEL = 'DEBUG'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}