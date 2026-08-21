"""
Configuration management for ARIA application.
Secrets and database URLs must come from the environment — no production-safe fallbacks.
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load production env if readable, then fallback to local .env
if os.path.exists('/etc/aria/.env') and os.access('/etc/aria/.env', os.R_OK):
    try:
        load_dotenv('/etc/aria/.env')
    except (PermissionError, OSError):
        pass
else:
    load_dotenv()


BOOKING_ACTIVE_STATUSES = ('Upcoming', 'Ongoing')
BOOKING_CANCELLED_STATUS = 'Cancelled'


def _normalize_database_url(url: str) -> str:
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    """Base configuration class."""

    # Flask — must be set via SECRET_KEY env (see TestingConfig for tests)
    SECRET_KEY = os.environ.get('SECRET_KEY')

    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # Database — required for non-testing runs (set DATABASE_URL)
    _raw_db = os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(_raw_db) if _raw_db else None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_size': 5,
        'max_overflow': 2,
        'pool_recycle': 300,
    }

    # Redis — optional in development (rate limiter falls back to memory)
    REDIS_URL = os.environ.get('REDIS_URL')

    # Device/API access
    DEVICE_API_TOKEN = os.environ.get('DEVICE_API_TOKEN')

    # Rate limiting storage (Flask-Limiter reads RATELIMIT_STORAGE_URI)
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI')

    # UI Modernization Rollout Flags (Phase 3)
    ARIA_UI_ENABLED = os.environ.get('ARIA_UI_ENABLED', 'True').lower() == 'true'
    ARIA_UI_PHASE = os.environ.get('ARIA_UI_PHASE', 'all')

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.environ.get('SESSION_LIFETIME_MINUTES', '60'))
    )
    REMEMBER_COOKIE_DURATION = timedelta(
        minutes=int(os.environ.get('SESSION_LIFETIME_MINUTES', '60'))
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False

    # Application data outside website/static (uploads, face training data, npz artifacts)
    BASE_DIR = Path(__file__).parent.resolve()
    INSTANCE_DIR = Path(
        os.environ.get('ARIA_INSTANCE_DIR', str(BASE_DIR / 'instance'))
    ).resolve()
    UPLOAD_FOLDER = INSTANCE_DIR / 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', str(5 * 1024 * 1024)))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    FACES_DB_PATH = INSTANCE_DIR / 'MalaysianFacesDB'
    FACES_EMBEDDINGS_PATH = INSTANCE_DIR / 'registered-faces-db-embeddings.npz'
    FACES_DB_FILE = INSTANCE_DIR / 'registered-faces-db.npz'
    FACE_CONFIDENCE_THRESHOLD = float(os.environ.get('FACE_CONFIDENCE_THRESHOLD', '0.85'))
    DEMO_MAX_CONCURRENT_SESSIONS = int(os.environ.get('DEMO_MAX_CONCURRENT_SESSIONS', '5'))
    DEMO_MAX_GUEST_ROWS = int(os.environ.get('DEMO_MAX_GUEST_ROWS', '20'))
    DEMO_SESSION_HOURS = int(os.environ.get('DEMO_SESSION_HOURS', '2'))
    DEMO_SAMPLES_REQUIRED = int(os.environ.get('DEMO_SAMPLES_REQUIRED', '5'))
    DEMO_FRAME_INTERVAL_MS = int(os.environ.get('DEMO_FRAME_INTERVAL_MS', '1500'))
    DEMO_SIMILARITY_THRESHOLD = float(os.environ.get('DEMO_SIMILARITY_THRESHOLD', '0.70'))
    DEMO_RECOGNITION_DEBOUNCE_SECONDS = int(
        os.environ.get('DEMO_RECOGNITION_DEBOUNCE_SECONDS', '3')
    )

    # Mail — no credentials in code
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME

    JSONIFY_PRETTYPRINT_REGULAR = True

    @staticmethod
    def init_app(app):
        """Initialize configuration for app."""
        Config.INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        (Config.UPLOAD_FOLDER / 'roomImages').mkdir(parents=True, exist_ok=True)
        Config.FACES_DB_PATH.mkdir(parents=True, exist_ok=True)
        (Config.FACES_DB_PATH / 'train').mkdir(parents=True, exist_ok=True)
        (Config.FACES_DB_PATH / 'test').mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Longer dev sessions unless overridden
        mins = int(os.environ.get('SESSION_LIFETIME_MINUTES', '480'))
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=mins)
        app.config['REMEMBER_COOKIE_DURATION'] = timedelta(minutes=mins)
        if not app.config.get('RATELIMIT_STORAGE_URI'):
            app.config['RATELIMIT_STORAGE_URI'] = (
                app.config.get('REDIS_URL') or 'memory://'
            )


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    REMEMBER_COOKIE_DURATION = timedelta(hours=1)
    SESSION_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        app.config['PERMANENT_SESSION_LIFETIME'] = cls.PERMANENT_SESSION_LIFETIME
        app.config['REMEMBER_COOKIE_DURATION'] = cls.REMEMBER_COOKIE_DURATION
        redis_url = app.config.get('REDIS_URL')
        if not redis_url:
            raise RuntimeError(
                'REDIS_URL must be set in production for rate limiting and background services.'
            )
        if not app.config.get('DEVICE_API_TOKEN'):
            raise RuntimeError(
                'DEVICE_API_TOKEN must be set in production for device and API authentication.'
            )
        app.config['RATELIMIT_STORAGE_URI'] = redis_url


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'test-secret-key-not-for-production')
    DEVICE_API_TOKEN = os.environ.get('DEVICE_API_TOKEN', 'test-device-token')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # In-memory SQLite cannot use connection pool options meant for Postgres.
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    RATELIMIT_STORAGE_URI = 'memory://'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def assert_production_ready():
    """Validate mandatory settings when FLASK_ENV=production."""
    if os.environ.get('FLASK_ENV') != 'production':
        return
    if not os.environ.get('SECRET_KEY'):
        raise RuntimeError(
            'SECRET_KEY must be set when FLASK_ENV=production. '
            'Generate a strong random value and set it in the environment.'
        )
    if not os.environ.get('DATABASE_URL'):
        raise RuntimeError(
            'DATABASE_URL must be set when FLASK_ENV=production.'
        )
    if not os.environ.get('DEVICE_API_TOKEN'):
        raise RuntimeError(
            'DEVICE_API_TOKEN must be set when FLASK_ENV=production.'
        )
