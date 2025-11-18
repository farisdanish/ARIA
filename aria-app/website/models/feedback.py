"""Feedback model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from .base import db


class Feedback(db.Model):
    """Feedback model."""
    __tablename__ = 'feedback'
    
    FeedbackID = Column(Integer, primary_key=True, autoincrement=True)
    StudID = Column(String(50), ForeignKey('student.StudID'), nullable=True)
    StaffID = Column(String(50), ForeignKey('staff.StaffID'), nullable=True)
    Subject = Column(String(255), nullable=False)
    Content = Column(Text, nullable=False)
    PostDate = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Feedback {self.FeedbackID}>'

