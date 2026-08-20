"""Public face demo visitor logging model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from .base import db


class DemoVisitLog(db.Model):
    """Anonymous audit logs for public face demo sessions and recognition attempts."""

    __tablename__ = 'demo_visit_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    Timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    GuestID = Column(String(50), nullable=False)
    Action = Column(String(50), nullable=False)
    Message = Column(String(255), nullable=False)
    IPAddress = Column(String(45), nullable=True)

    def __repr__(self):
        return f'<DemoVisitLog {self.id}: {self.GuestID} {self.Action}>'
