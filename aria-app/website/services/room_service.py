"""Room service."""
from typing import List, Optional
from ..models.room import RoomList
from ..models.base import db
import logging

logger = logging.getLogger(__name__)


class RoomService:
    """Service for room operations."""
    
    @staticmethod
    def get_all() -> List[RoomList]:
        """Get all rooms."""
        return db.session.query(RoomList).all()
    
    @staticmethod
    def get_by_id(room_id: int) -> Optional[RoomList]:
        """Get room by ID."""
        return db.session.query(RoomList).filter_by(RoomID=room_id).first()
    
    @staticmethod
    def get_by_name(room_name: str) -> Optional[RoomList]:
        """Get room by name."""
        return db.session.query(RoomList).filter_by(RoomName=room_name).first()
    
    @staticmethod
    def create(admin_id: str, room_name: str, room_info: str, 
              room_type: str, room_status: str, room_img: str = None) -> RoomList:
        """Create a new room."""
        room = RoomList(
            AdminID=admin_id,
            RoomName=room_name,
            roomIMG=room_img,
            RoomInfo=room_info,
            RoomType=room_type,
            RoomStatus=room_status
        )
        db.session.add(room)
        db.session.commit()
        logger.info(f"Room created: {room.RoomID}")
        return room
    
    @staticmethod
    def update(room_id: int, room_name: str = None, room_info: str = None,
              room_type: str = None, room_status: str = None, 
              room_img: str = None) -> Optional[RoomList]:
        """Update a room."""
        room = RoomService.get_by_id(room_id)
        if not room:
            return None
        
        if room_name is not None:
            room.RoomName = room_name
        if room_info is not None:
            room.RoomInfo = room_info
        if room_type is not None:
            room.RoomType = room_type
        if room_status is not None:
            room.RoomStatus = room_status
        if room_img is not None:
            room.roomIMG = room_img
        
        db.session.commit()
        logger.info(f"Room updated: {room_id}")
        return room
    
    @staticmethod
    def delete(room_id: int) -> bool:
        """Delete a room."""
        room = RoomService.get_by_id(room_id)
        if not room:
            return False
        
        db.session.delete(room)
        db.session.commit()
        logger.info(f"Room deleted: {room_id}")
        return True

