"""
Flask application factory and initialization.
"""
import os
import logging
from flask import Flask
from flask_mail import Mail
from flask_executor import Executor
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from config import assert_production_ready, config
from .models.base import db
from .models import Student, Staff, Admin
from .extensions import limiter

# Initialize extensions
mail = Mail()
executor = Executor()
csrf = CSRFProtect()
migrate = Migrate()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name: str = None) -> Flask:
    """
    Application factory pattern.

    Args:
        config_name: Configuration name (development, production, testing)
                    If None, uses FLASK_ENV or defaults to 'development'
    """
    assert_production_ready()

    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    config_obj = config.get(config_name, config['default'])
    app.config.from_object(config_obj)

    if config_name != 'testing' and not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise RuntimeError('DATABASE_URL must be set.')

    # Initialize configuration (paths, rate-limit URI, production overrides)
    config_obj.init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    executor.init_app(app)
    csrf.init_app(app)

    app.config['RATELIMIT_STORAGE_URI'] = (
        app.config.get('RATELIMIT_STORAGE_URI') or 'memory://'
    )
    limiter.init_app(app)

    # Bootstrap database tables for local/dev environments when missing.
    auto_create_db = os.environ.get('AUTO_CREATE_DB', 'True').lower() == 'true'
    if auto_create_db:
        with app.app_context():
            db.create_all()
        logger.info('Database tables ensured via db.create_all()')

    # Register blueprints
    from .routes import demo_bp, home, auth, facenet, announcements, rooms, bookings
    from .routes.api import apiroute

    app.register_blueprint(demo_bp)
    app.register_blueprint(home)
    app.register_blueprint(auth)
    app.register_blueprint(facenet)
    app.register_blueprint(announcements)
    app.register_blueprint(rooms)
    app.register_blueprint(bookings)
    app.register_blueprint(apiroute, url_prefix='/api')

    # Note: API is already initialized with the blueprint in routes/api/__init__.py
    # and namespace is already added there. No need for init_app or add_namespace here.

    # Initialize login manager
    from flask_login import LoginManager

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login."""
        user = db.session.query(Student).filter_by(StudID=user_id).first()
        if user:
            return user

        user = db.session.query(Staff).filter_by(StaffID=user_id).first()
        if user:
            return user

        user = db.session.query(Admin).filter_by(AdminID=user_id).first()
        if user:
            return user

        return None

    # Register error handlers
    register_error_handlers(app)

    @app.after_request
    def security_headers(response):
        """Set security headers (HSTS is set by Caddy)."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        _csp_hosts = (
            'https://stackpath.bootstrapcdn.com '
            'https://cdnjs.cloudflare.com '
            'https://cdn.jsdelivr.net '
            'https://cdn.datatables.net '
            'https://code.jquery.com '
            'https://ajax.googleapis.com '
            'https://unpkg.com'
        )
        response.headers['Content-Security-Policy'] = (
            f"default-src 'self'; "
            f"connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            f"img-src 'self' data:; "
            f"font-src 'self' data: https://cdnjs.cloudflare.com https://cdn.jsdelivr.net;"
            f"script-src 'self' 'unsafe-inline' 'unsafe-eval' {_csp_hosts}; "
            f"style-src 'self' 'unsafe-inline' {_csp_hosts}"
        )
        return response

    @app.context_processor
    def inject_ui_flags():
        """Expose UI rollout flags to templates."""
        return {
            'aria_ui_enabled': app.config.get('ARIA_UI_ENABLED', True),
            'aria_ui_phase': app.config.get('ARIA_UI_PHASE', 'all'),
        }

    # Start background scheduler and Redis subscriber
    if not os.environ.get('FLASK_SKIP_BACKGROUND_THREADS'):
        from .services.scheduler import BookingScheduler
        from .services.subscriber import RedisSubscriber

        BookingScheduler.start(app)
        RedisSubscriber.start(app)

    logger.info('Application initialized with %s configuration', config_name)
    return app


def register_error_handlers(app: Flask):
    """Register error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template

        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template

        db.session.rollback()
        return render_template('errors/500.html'), 500
