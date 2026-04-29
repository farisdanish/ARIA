"""Route blueprints."""
from .demo import demo_bp
from .home import home
from .auth import auth
from .face import facenet
from .announcements import announcements
from .rooms import rooms
from .bookings import bookings

__all__ = ['demo_bp', 'home', 'auth', 'facenet', 'announcements', 'rooms', 'bookings']
