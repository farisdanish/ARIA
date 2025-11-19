"""Room-related models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from .base import db


class RoomList(db.Model):
    """Room list model."""
    __tablename__ = 'roomlist'
    
    RoomID = Column(Integer, primary_key=True, autoincrement=True)
    AdminID = Column(String(50), ForeignKey('admin.AdminID'), nullable=True)
    RoomName = Column(String(255), nullable=False, unique=True)
    roomIMG = Column(String(500), nullable=True)
    RoomInfo = Column(Text, nullable=True)
    RoomType = Column(String(100), nullable=True)
    RoomStatus = Column(Enum('Available', 'Occupied', 'Maintenance', name='room_status'),
                       default='Available', nullable=False)
    
    # Relationships
    room_bookings = db.relationship('RoomBooking', backref='room', lazy=True)
    event_bookings = db.relationship('EventBooking', backref='room', lazy=True)
    
    def __repr__(self):
        return f'<Room {self.RoomID}: {self.RoomName}>'


class RoomBooking(db.Model):
    """Room booking model."""
    __tablename__ = 'roombookings'
    
    RBookID = Column(Integer, primary_key=True, autoincrement=True)
    RoomID = Column(Integer, ForeignKey('roomlist.RoomID'), nullable=False)
    StudID = Column(String(50), ForeignKey('student.StudID'), nullable=True)
    StaffID = Column(String(50), ForeignKey('staff.StaffID'), nullable=True)
    Start = Column(DateTime, nullable=False)
    End = Column(DateTime, nullable=False)
    Purpose = Column(Text, nullable=False)
    RBookStatus = Column(Enum('Upcoming', 'Ongoing', 'Completed', 'Cancelled', name='booking_status'),
                        default='Upcoming', nullable=False)
    
    def __repr__(self):
        return f'<RoomBooking {self.RBookID}: Room {self.RoomID}>'


class EventBooking(db.Model):
    """Event booking model."""
    __tablename__ = 'eventbookings'
    
    EBookID = Column(Integer, primary_key=True, autoincrement=True)
    RoomID = Column(Integer, ForeignKey('roomlist.RoomID'), nullable=False)
    StudID = Column(String(50), ForeignKey('student.StudID'), nullable=True)
    StaffID = Column(String(50), ForeignKey('staff.StaffID'), nullable=True)
    Start = Column(DateTime, nullable=False)
    End = Column(DateTime, nullable=False)
    Purpose = Column(Text, nullable=False)
    AddDetail = Column(Text, nullable=True)
    EbookStatus = Column(Enum('Upcoming', 'Ongoing', 'Completed', 'Cancelled', name='booking_status'),
                        default='Upcoming', nullable=False)
    
    def __repr__(self):
        return f'<EventBooking {self.EBookID}: Room {self.RoomID}>'

