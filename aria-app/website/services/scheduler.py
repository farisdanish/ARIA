"""Background scheduler to monitor bookings and publish Redis events."""
import time
import threading
import logging
from datetime import datetime, timedelta
from .redis_service import RedisService
from ..models.room import RoomBooking, EventBooking
from .base import db

logger = logging.getLogger(__name__)

class BookingScheduler:
    """Background thread that watches for upcoming bookings."""
    
    _thread = None
    _stop_event = threading.Event()
    
    # How often to check for new bookings (seconds)
    CHECK_INTERVAL = 60
    # How many minutes before start to notify the Pi (lead time)
    LEAD_TIME_MINUTES = 10

    @classmethod
    def start(cls, app):
        """Start the scheduler in a background thread."""
        if cls._thread is not None:
            return

        cls._stop_event.clear()
        cls._thread = threading.Thread(
            target=cls._run_loop,
            args=(app,),
            daemon=True,
            name="BookingSchedulerThread"
        )
        cls._thread.start()
        logger.info("Booking scheduler background thread started.")

    @classmethod
    def stop(cls):
        """Stop the scheduler."""
        cls._stop_event.set()
        if cls._thread:
            cls._thread.join(timeout=2)
            cls._thread = None
        logger.info("Booking scheduler background thread stopped.")

    @classmethod
    def _run_loop(cls, app):
        """Main loop for the background thread."""
        while not cls._stop_event.is_set():
            try:
                with app.app_context():
                    cls._check_upcoming_bookings()
            except Exception as e:
                logger.error(f"Error in booking scheduler loop: {str(e)}")
            
            # Sleep until next check
            time.sleep(cls.CHECK_INTERVAL)

    @classmethod
    def _check_upcoming_bookings(cls):
        """Query DB for bookings starting soon and publish Redis events."""
        now = datetime.now()
        threshold = now + timedelta(minutes=cls.LEAD_TIME_MINUTES)
        
        # 1. Check Room Bookings
        # We look for "Upcoming" bookings that are about to start
        upcoming_rooms = RoomBooking.query.filter(
            RoomBooking.RBookStatus == 'Upcoming',
            RoomBooking.Start >= now,
            RoomBooking.Start <= threshold
        ).all()
        
        for booking in upcoming_rooms:
            logger.info(f"Notify Pi: Upcoming room booking {booking.RBookID} starting at {booking.Start}")
            RedisService.publish_watch_room(booking.RoomID)
            
        # 2. Check Event Bookings
        upcoming_events = EventBooking.query.filter(
            EventBooking.EbookStatus == 'Upcoming',
            EventBooking.Start >= now,
            EventBooking.Start <= threshold
        ).all()
        
        for booking in upcoming_events:
            logger.info(f"Notify Pi: Upcoming event booking {booking.EBookID} starting at {booking.Start}")
            RedisService.publish_watch_room(booking.RoomID)
