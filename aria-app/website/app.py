"""
Flask application factory and initialization.
"""
import os
import logging
from flask import Flask
from flask_mail import Mail
from flask_executor import Executor
from config import config
from .models.base import db
from .models import Student, Staff, Admin

# Initialize extensions
mail = Mail()
executor = Executor()

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
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_obj = config.get(config_name, config['default'])
    app.config.from_object(config_obj)
    
    # Initialize configuration
    config_obj.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    executor.init_app(app)
    
    # Register blueprints
    from .routes import home, auth, facenet, announcements, rooms, bookings
    from .routes.api import apiroute
    
    app.register_blueprint(home)
    app.register_blueprint(auth)
    app.register_blueprint(facenet)
    app.register_blueprint(announcements)
    app.register_blueprint(rooms)
    app.register_blueprint(bookings)
    app.register_blueprint(apiroute, url_prefix='/api')
    
    # Register API namespace
    from .routes.api import api, ns
    api.init_app(app)
    api.add_namespace(ns)
    
    # Initialize login manager
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login."""
        # Try to find user in all user tables
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
    
    logger.info(f"Application initialized with {config_name} configuration")
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
