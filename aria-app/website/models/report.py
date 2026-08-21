"""Report model."""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Float, ForeignKey
from .base import db


class Report(db.Model):
    """Report model."""
    __tablename__ = 'report'
    
    ReportID = Column(Integer, primary_key=True, autoincrement=True)
    ReportTitle = Column(String(255), nullable=True)
    RoomID = Column(Integer, ForeignKey('roomlist.RoomID'), nullable=True)
    totalNumBookings = Column(Integer, default=0, nullable=True)
    totalHoursBooked = Column(Float, default=0.0, nullable=True)
    MonthYear = Column(Date, nullable=True)
    
    # Optional / legacy columns
    StudID = Column(String(50), ForeignKey('student.StudID'), nullable=True)
    StaffID = Column(String(50), ForeignKey('staff.StaffID'), nullable=True)
    Subject = Column(String(255), nullable=True)
    Content = Column(Text, nullable=True)
    PostDate = Column(DateTime, default=datetime.utcnow, nullable=True)
    
    def __repr__(self):
        return f'<Report {self.ReportID}: {self.ReportTitle}>'

