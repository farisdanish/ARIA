"""Ephemeral guest accounts (e.g. kiosk / temporary face enrollment)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, String

from .base import db


class GuestUser(db.Model):
    """Guest user row; role is implicitly guest (only guests use this table)."""

    __tablename__ = 'guest_user'

    GuestID = Column(String(50), primary_key=True)
    CreatedAt = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<GuestUser {self.GuestID}>'
