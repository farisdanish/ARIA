"""Announcement model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from .base import db


class Announcement(db.Model):
    """Announcement model."""
    __tablename__ = 'announcement'
    
    AnnounceID = Column(Integer, primary_key=True, autoincrement=True)
    AdminID = Column(String(50), ForeignKey('admin.AdminID'), nullable=False)
    PostDate = Column(DateTime, default=datetime.utcnow, nullable=False)
    Title = Column(String(255), nullable=False)
    Content = Column(Text, nullable=False)
    
    def __repr__(self):
        return f'<Announcement {self.AnnounceID}: {self.Title}>'

