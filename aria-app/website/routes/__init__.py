"""Route blueprints."""
from .home import home
from .auth import auth
from .face import facenet
from .announcements import announcements
from .rooms import rooms
from .bookings import bookings

__all__ = ['home', 'auth', 'facenet', 'announcements', 'rooms', 'bookings']

