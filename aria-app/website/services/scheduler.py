"""Background APScheduler jobs: booking notifications and guest cleanup."""
from __future__ import annotations

import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from .redis_service import RedisService
from ..models.room import RoomBooking, EventBooking

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


class BookingScheduler:
    """Schedules booking checks and periodic guest face cleanup."""

    CHECK_INTERVAL_SECONDS = 60
    LEAD_TIME_MINUTES = 10

    @classmethod
    def start(cls, app):
        """Start APScheduler jobs."""
        global _scheduler
        if _scheduler is not None:
            return

        sched = BackgroundScheduler(timezone='UTC')

        def booking_job():
            with app.app_context():
                try:
                    cls._check_upcoming_bookings()
                except Exception as e:
                    logger.error('Error in booking scheduler job: %s', e)

        def guest_cleanup_job():
            with app.app_context():
                try:
                    from .guest_cleanup import cleanup_expired_guests

                    cleanup_expired_guests(app)
                except Exception:
                    logger.exception('Error in guest cleanup job.')

        sched.add_job(
            booking_job,
            'interval',
            seconds=cls.CHECK_INTERVAL_SECONDS,
            id='booking_notifications',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        sched.add_job(
            guest_cleanup_job,
            'interval',
            hours=1,
            id='guest_face_cleanup',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        sched.start()
        _scheduler = sched
        logger.info('APScheduler started (booking notifications + hourly guest cleanup).')

    _notified_bookings = set()

    @classmethod
    def stop(cls):
        """Stop the scheduler (e.g. tests)."""
        global _scheduler
        if _scheduler is not None:
            _scheduler.shutdown(wait=False)
            _scheduler = None
            cls._notified_bookings.clear()
            logger.info('APScheduler stopped.')

    @classmethod
    def _check_upcoming_bookings(cls):
        """Query DB for bookings starting soon and publish Redis events."""
        from datetime import datetime, timedelta

        now = datetime.now()
        threshold = now + timedelta(minutes=cls.LEAD_TIME_MINUTES)

        upcoming_rooms = RoomBooking.query.filter(
            RoomBooking.RBookStatus == 'Upcoming',
            RoomBooking.Start >= now,
            RoomBooking.Start <= threshold,
        ).all()

        for booking in upcoming_rooms:
            key = ('room', booking.RBookID)
            if key not in cls._notified_bookings:
                logger.info(
                    'Notify Pi: Upcoming room booking %s starting at %s',
                    booking.RBookID,
                    booking.Start,
                )
                RedisService.publish_watch_room(booking.RoomID)
                cls._notified_bookings.add(key)

        upcoming_events = EventBooking.query.filter(
            EventBooking.EbookStatus == 'Upcoming',
            EventBooking.Start >= now,
            EventBooking.Start <= threshold,
        ).all()

        for booking in upcoming_events:
            key = ('event', booking.EBookID)
            if key not in cls._notified_bookings:
                logger.info(
                    'Notify Pi: Upcoming event booking %s starting at %s',
                    booking.EBookID,
                    booking.Start,
                )
                RedisService.publish_watch_room(booking.RoomID)
                cls._notified_bookings.add(key)
