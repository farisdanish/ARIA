"""Booking service."""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import and_, desc
from ..models.room import RoomBooking, EventBooking
from ..models.base import db
import logging

logger = logging.getLogger(__name__)


class BookingService:
    """Service for booking operations."""
    
    @staticmethod
    def check_room_availability(room_id: int, start: datetime, end: datetime, 
                               exclude_booking_id: int = None) -> bool:
        """
        Check if a room is available for the given time slot.
        
        Args:
            room_id: Room ID
            start: Start datetime
            end: End datetime
            exclude_booking_id: Booking ID to exclude from check (for updates)
            
        Returns:
            True if available, False if conflicting bookings exist
        """
        query = db.session.query(RoomBooking).filter(
            and_(
                RoomBooking.RoomID == room_id,
                RoomBooking.Start <= end,
                RoomBooking.End >= start,
                RoomBooking.RBookStatus.in_(['Upcoming', 'Ongoing'])
            )
        )
        
        if exclude_booking_id:
            query = query.filter(RoomBooking.RBookID != exclude_booking_id)
        
        conflicting = query.first()
        return conflicting is None
    
    @staticmethod
    def check_event_availability(room_id: int, start: datetime, end: datetime,
                                exclude_booking_id: int = None) -> bool:
        """Check if a room is available for event booking."""
        query = db.session.query(EventBooking).filter(
            and_(
                EventBooking.RoomID == room_id,
                EventBooking.Start <= end,
                EventBooking.End >= start,
                EventBooking.EbookStatus.in_(['Upcoming', 'Ongoing'])
            )
        )
        
        if exclude_booking_id:
            query = query.filter(EventBooking.EBookID != exclude_booking_id)
        
        conflicting = query.first()
        return conflicting is None
    
    @staticmethod
    def validate_booking_duration(start: datetime, end: datetime, max_hours: int = 2) -> tuple[bool, str]:
        """
        Validate booking duration.
        
        Returns:
            (is_valid, error_message)
        """
        if end < start:
            return False, "Booking time invalid"
        
        delta = end - start
        hours = delta.total_seconds() / 3600
        
        if hours > max_hours:
            return False, f"Booking time must be {max_hours} hours or less"
        
        return True, ""
    
    @staticmethod
    def create_room_booking(room_id: int, stud_id: str = None, staff_id: str = None,
                           start: datetime = None, end: datetime = None,
                           purpose: str = None) -> Optional[RoomBooking]:
        """Create a room booking."""
        # Validate duration
        is_valid, error_msg = BookingService.validate_booking_duration(start, end)
        if not is_valid:
            logger.warning(f"Invalid booking duration: {error_msg}")
            return None
        
        # Check availability
        if not BookingService.check_room_availability(room_id, start, end):
            logger.warning(f"Room {room_id} not available for {start} - {end}")
            return None
        
        booking = RoomBooking(
            RoomID=room_id,
            StudID=stud_id,
            StaffID=staff_id,
            Start=start,
            End=end,
            Purpose=purpose,
            RBookStatus='Upcoming'
        )
        db.session.add(booking)
        db.session.commit()
        logger.info(f"Room booking created: {booking.RBookID}")
        return booking
    
    @staticmethod
    def create_event_booking(room_id: int, stud_id: str = None, staff_id: str = None,
                            start: datetime = None, end: datetime = None,
                            purpose: str = None, add_detail: str = None) -> Optional[EventBooking]:
        """Create an event booking."""
        if end < start:
            logger.warning("Invalid booking time")
            return None
        
        # Check availability
        if not BookingService.check_event_availability(room_id, start, end):
            logger.warning(f"Room {room_id} not available for event {start} - {end}")
            return None
        
        booking = EventBooking(
            RoomID=room_id,
            StudID=stud_id,
            StaffID=staff_id,
            Start=start,
            End=end,
            Purpose=purpose,
            AddDetail=add_detail,
            EbookStatus='Upcoming'
        )
        db.session.add(booking)
        db.session.commit()
        logger.info(f"Event booking created: {booking.EBookID}")
        return booking
    
    @staticmethod
    def get_user_room_bookings(user_id: str, is_student: bool = True) -> List[RoomBooking]:
        """Get room bookings for a user."""
        if is_student:
            return db.session.query(RoomBooking).filter_by(StudID=user_id).order_by(desc(RoomBooking.Start)).all()
        else:
            return db.session.query(RoomBooking).filter_by(StaffID=user_id).order_by(desc(RoomBooking.Start)).all()
    
    @staticmethod
    def get_user_event_bookings(user_id: str, is_student: bool = True) -> List[EventBooking]:
        """Get event bookings for a user."""
        if is_student:
            return db.session.query(EventBooking).filter_by(StudID=user_id).order_by(desc(EventBooking.Start)).all()
        else:
            return db.session.query(EventBooking).filter_by(StaffID=user_id).order_by(desc(EventBooking.Start)).all()
    
    @staticmethod
    def get_all_room_bookings() -> List[RoomBooking]:
        """Get all room bookings."""
        return db.session.query(RoomBooking).order_by(desc(RoomBooking.Start)).all()
    
    @staticmethod
    def get_all_event_bookings() -> List[EventBooking]:
        """Get all event bookings."""
        return db.session.query(EventBooking).order_by(desc(EventBooking.Start)).all()
    
    @staticmethod
    def delete_room_booking(booking_id: int) -> bool:
        """Delete a room booking."""
        booking = db.session.query(RoomBooking).filter_by(RBookID=booking_id).first()
        if not booking:
            return False
        
        db.session.delete(booking)
        db.session.commit()
        logger.info(f"Room booking deleted: {booking_id}")
        return True
    
    @staticmethod
    def delete_event_booking(booking_id: int) -> bool:
        """Delete an event booking."""
        booking = db.session.query(EventBooking).filter_by(EBookID=booking_id).first()
        if not booking:
            return False
        
        db.session.delete(booking)
        db.session.commit()
        logger.info(f"Event booking deleted: {booking_id}")
        return True

