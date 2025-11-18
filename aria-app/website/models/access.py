"""Access log models."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from .base import db


class RoomAccessLog(db.Model):
    """Room access log model."""
    __tablename__ = 'roomaccesslog'
    
    rmaID = Column(Integer, primary_key=True, autoincrement=True)
    RoomID = Column(Integer, ForeignKey('roomlist.RoomID'), nullable=False)
    StudID = Column(String(50), ForeignKey('student.StudID'), nullable=True)
    StaffID = Column(String(50), ForeignKey('staff.StaffID'), nullable=True)
    Status = Column(Integer, nullable=False)  # 0 = denied, 1 = granted
    Timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<RoomAccessLog {self.rmaID}: Room {self.RoomID}>'

