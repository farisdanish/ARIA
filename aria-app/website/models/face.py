"""Face recognition models."""
from sqlalchemy import Column, Integer, String, ForeignKey
from .base import db


class RegisteredFace(db.Model):
    """Registered face model."""
    __tablename__ = 'registeredfaces'
    
    FaceID = Column(Integer, primary_key=True, autoincrement=True)
    FaceIMG = Column(Text, nullable=False)  # Paths to face images
    StudID = Column(String(50), ForeignKey('student.StudID'), nullable=True)
    StaffID = Column(String(50), ForeignKey('staff.StaffID'), nullable=True)
    
    def __repr__(self):
        user_id = self.StudID or self.StaffID
        return f'<RegisteredFace {self.FaceID}: {user_id}>'

