"""Redis subscriber for the Flask application."""
import time
import threading
import logging
import json
import os
from .redis_service import RedisService
from ..models.room import RoomBooking, EventBooking
from ..models.access import AccessLog
from ..models.base import db
from datetime import datetime

logger = logging.getLogger(__name__)

class RedisSubscriber:
    """Background thread that listens for Redis events."""
    
    _thread = None
    _stop_event = threading.Event()

    @classmethod
    def start(cls, app):
        """Start the subscriber in a background thread."""
        if cls._thread is not None:
            return

        cls._stop_event.clear()
        cls._thread = threading.Thread(
            target=cls._run_loop,
            args=(app,),
            daemon=True,
            name="RedisSubscriberThread"
        )
        cls._thread.start()
        logger.info("Redis subscriber background thread started.")

    @classmethod
    def stop(cls):
        """Stop the subscriber."""
        cls._stop_event.set()
        if cls._thread:
            cls._thread.join(timeout=2)
            cls._thread = None
        logger.info("Redis subscriber background thread stopped.")

    @classmethod
    def _run_loop(cls, app):
        """Main loop for the background thread."""
        client = RedisService.get_client()
        if not client:
            logger.error("Could not get Redis client for subscriber.")
            return

        pubsub = client.pubsub()
        pubsub.psubscribe("face_matched:*")
        
        while not cls._stop_event.is_set():
            try:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message['type'] == 'pmessage':
                    with app.app_context():
                        cls._handle_message(message)
            except Exception as e:
                logger.error(f"Error in Redis subscriber loop: {str(e)}")
                time.sleep(5) # Delay before retry

    @classmethod
    def _handle_message(cls, message):
        """Handle incoming Redis message."""
        try:
            channel = message['channel']
            data = json.loads(message['data'])
            
            if channel.startswith("face_matched:"):
                room_id = data.get('room_id')
                user_id = data.get('user_id')
                
                logger.info(f"Received face_matched event: Room {room_id}, User {user_id}")
                cls._update_booking_and_log_access(room_id, user_id)
                
        except Exception as e:
            logger.error(f"Error handling Redis message: {str(e)}")

    @classmethod
    def _update_booking_and_log_access(cls, room_id, user_id):
        """Update DB status and write access log."""
        now = datetime.now()
        
        # Find active booking for this room and user
        # 1. Room Bookings
        booking = RoomBooking.query.filter(
            RoomBooking.RoomID == room_id,
            (RoomBooking.StudID == user_id) | (RoomBooking.StaffID == user_id),
            RoomBooking.RBookStatus.in_(['Upcoming', 'Ongoing']),
            RoomBooking.Start <= now,
            RoomBooking.End > now
        ).first()
        
        if booking:
            booking.RBookStatus = 'Ongoing'
            # Create access log
            access = AccessLog(
                RoomID=room_id,
                StudID=booking.StudID,
                StaffID=booking.StaffID,
                Status=1, # Granted
                Timestamp=now
            )
            db.session.add(access)
            db.session.commit()
            logger.info(f"Updated RoomBooking {booking.RBookID} to Ongoing and logged access.")
            return

        # 2. Event Bookings
        event = EventBooking.query.filter(
            EventBooking.RoomID == room_id,
            (EventBooking.StudID == user_id) | (EventBooking.StaffID == user_id),
            EventBooking.EbookStatus.in_(['Upcoming', 'Ongoing']),
            EventBooking.Start <= now,
            EventBooking.End > now
        ).first()
        
        if event:
            event.EbookStatus = 'Ongoing'
            access = AccessLog(
                RoomID=room_id,
                StudID=event.StudID,
                StaffID=event.StaffID,
                Status=1,
                Timestamp=now
            )
            db.session.add(access)
            db.session.commit()
            logger.info(f"Updated EventBooking {event.EBookID} to Ongoing and logged access.")
            return

        logger.warning(f"No active booking found for Room {room_id} and User {user_id} to update.")
