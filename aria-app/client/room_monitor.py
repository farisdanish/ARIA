"""
Room booking monitor and access control logic.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class RoomMonitor:
    """Monitor room bookings and manage access."""
    
    def __init__(self, api_client, room_id: int):
        """
        Initialize room monitor.
        
        Args:
            api_client: APIClient instance
            room_id: Room ID to monitor
        """
        self.api_client = api_client
        self.room_id = room_id
        self.current_booking: Optional[Dict] = None
    
    def get_current_booking(self, bookings: List[Dict]) -> Optional[Dict]:
        """
        Get current active booking for the room.
        
        Args:
            bookings: List of all bookings
            
        Returns:
            Current booking dict or None
        """
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        for booking in bookings:
            if booking.get('RoomID') != self.room_id:
                continue
            
            start = booking.get('Start')
            end = booking.get('End')
            
            if start and end and start <= now < end:
                # Check if booking is active
                status = booking.get('RBookStatus', '')
                if status in ['Upcoming', 'Ongoing']:
                    return booking
        
        return None
    
    def get_expected_user(self, booking: Dict, students: List[Dict], staff: List[Dict]) -> Optional[str]:
        """
        Get expected user ID from booking.
        
        Args:
            booking: Booking dictionary
            students: List of students
            staff: List of staff
            
        Returns:
            User ID (StudID or StaffID) or None
        """
        stud_id = booking.get('StudID')
        staff_id = booking.get('StaffID')
        
        if stud_id:
            # Verify student exists
            for student in students:
                if student.get('StudID') == stud_id:
                    return stud_id
        
        if staff_id:
            # Verify staff exists
            for staff_member in staff:
                if staff_member.get('StaffID') == staff_id:
                    return staff_id
        
        return None
    
    def refresh_data(self) -> Dict:
        """
        Refresh data from API.
        
        Returns:
            Dictionary with students, staff, bookings, rooms
        """
        logger.info("Refreshing data from API...")
        
        data = {
            'students': self.api_client.get_students(),
            'staff': self.api_client.get_staff(),
            'bookings': self.api_client.get_room_bookings(),
            'rooms': self.api_client.get_rooms()
        }
        
        logger.info(f"Data refreshed: {len(data['students'])} students, "
                   f"{len(data['staff'])} staff, {len(data['bookings'])} bookings")
        
        return data

