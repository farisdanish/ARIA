"""
Configuration management for ARIA application.
Uses environment variables with sensible defaults.
"""
import os
from pathlib import Path
from datetime import timedelta


class Config:
    """Base configuration class."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
    else:
        pass
        
    SQLALCHEMY_DATABASE_URI = db_url or 'mysql+mysqldb://root:@localhost:3306/ariadb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Connection pool settings for Supabase pgBouncer (transaction mode, port 6543).
    # pool_pre_ping checks liveness before handing out a connection — avoids
    # "SSL connection has been closed unexpectedly" errors after idle periods.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 2,
        "pool_recycle": 300,
    }
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        pass
    else:
        pass
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(
        os.environ.get('SESSION_LIFETIME_MINUTES', '480')
    ))
    REMEMBER_COOKIE_DURATION = timedelta(minutes=int(
        os.environ.get('SESSION_LIFETIME_MINUTES', '480')
    ))
    
    # File Uploads
    BASE_DIR = Path(__file__).parent
    UPLOAD_FOLDER = BASE_DIR / 'website' / 'static' / 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '16777216'))  # 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Face Recognition
    FACES_DB_PATH = BASE_DIR / 'website' / 'static' / 'MalaysianFacesDB'
    FACES_EMBEDDINGS_PATH = BASE_DIR / 'website' / 'static' / 'registered-faces-db-embeddings.npz'
    FACES_DB_FILE = BASE_DIR / 'website' / 'static' / 'registered-faces-db.npz'
    FACE_CONFIDENCE_THRESHOLD = float(os.environ.get('FACE_CONFIDENCE_THRESHOLD', '0.85'))
    
    # Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # JSON
    JSONIFY_PRETTYPRINT_REGULAR = True

    # UI rollout
    ARIA_UI_ENABLED = os.environ.get('ARIA_UI_ENABLED', 'False').lower() == 'true'
    ARIA_UI_PHASE = os.environ.get('ARIA_UI_PHASE', 'public').lower()
    
    @staticmethod
    def init_app(app):
        """Initialize configuration for app."""
        # Ensure upload directories exist
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        (Config.UPLOAD_FOLDER / 'roomImages').mkdir(parents=True, exist_ok=True)
        Config.FACES_DB_PATH.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
