"""Announcement service."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import desc
from ..models.announcement import Announcement
from ..models.base import db
import logging

logger = logging.getLogger(__name__)


class AnnouncementService:
    """Service for announcement operations."""
    
    @staticmethod
    def get_all(order_by_date: bool = True) -> List[Announcement]:
        """Get all announcements."""
        query = db.session.query(Announcement)
        if order_by_date:
            query = query.order_by(desc(Announcement.PostDate))
        return query.all()

    @staticmethod
    def get_feed(search: str = None, page: int = 1, per_page: int = 10) -> tuple[List[Announcement], bool]:
        """
        Get paginated and filtered announcements.
        Returns (list of announcements, has_more_boolean)
        """
        query = db.session.query(Announcement)
        
        if search:
            query = query.filter(
                (Announcement.Title.ilike(f'%{search}%')) | 
                (Announcement.Content.ilike(f'%{search}%'))
            )
            
        query = query.order_by(desc(Announcement.PostDate))
        
        # Paginate
        offset = (page - 1) * per_page
        results = query.offset(offset).limit(per_page + 1).all()
        
        has_more = len(results) > per_page
        return results[:per_page], has_more
    
    @staticmethod
    def get_by_id(announce_id: int) -> Optional[Announcement]:
        """Get announcement by ID."""
        return db.session.query(Announcement).filter_by(AnnounceID=announce_id).first()
    
    @staticmethod
    def create(admin_id: str, title: str, content: str) -> Announcement:
        """Create a new announcement."""
        announcement = Announcement(
            AdminID=admin_id,
            PostDate=datetime.utcnow(),
            Title=title,
            Content=content
        )
        db.session.add(announcement)
        db.session.commit()
        logger.info(f"Announcement created: {announcement.AnnounceID}")
        return announcement
    
    @staticmethod
    def update(announce_id: int, title: str, content: str) -> Optional[Announcement]:
        """Update an announcement."""
        announcement = AnnouncementService.get_by_id(announce_id)
        if not announcement:
            return None
        
        announcement.Title = title
        announcement.Content = content
        db.session.commit()
        logger.info(f"Announcement updated: {announce_id}")
        return announcement
    
    @staticmethod
    def delete(announce_id: int) -> bool:
        """Delete an announcement."""
        announcement = AnnouncementService.get_by_id(announce_id)
        if not announcement:
            return False
        
        db.session.delete(announcement)
        db.session.commit()
        logger.info(f"Announcement deleted: {announce_id}")
        return True

