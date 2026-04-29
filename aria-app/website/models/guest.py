"""Ephemeral guest accounts (e.g. kiosk / temporary face enrollment)."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, String

from .base import db


class GuestUser(db.Model):
    """Guest user row; role is implicitly guest (only guests use this table)."""

    __tablename__ = 'guest_user'

    GuestID = Column(String(50), primary_key=True)
    TokenHash = Column(String(64), nullable=False)
    CreatedAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    ExpiresAt = Column(DateTime, nullable=False)
    Status = Column(
        Enum('pending', 'enrolling', 'ready', 'expired', name='guest_user_status'),
        nullable=False,
        default='pending',
    )
    LastRecognizedAt = Column(DateTime, nullable=True)
    LastRecognitionResult = Column(Boolean, nullable=True)
    LastRecognitionConfidence = Column(Float, nullable=True)

    def __repr__(self):
        return f'<GuestUser {self.GuestID}>'
