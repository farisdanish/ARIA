"""Validation schemas using Marshmallow."""
from .announcement_schema import AnnouncementSchema, AnnouncementCreateSchema
from .room_schema import RoomSchema, RoomCreateSchema, RoomUpdateSchema
from .booking_schema import RoomBookingSchema, RoomBookingCreateSchema, EventBookingSchema, EventBookingCreateSchema

__all__ = [
    'AnnouncementSchema',
    'AnnouncementCreateSchema',
    'RoomSchema',
    'RoomCreateSchema',
    'RoomUpdateSchema',
    'RoomBookingSchema',
    'RoomBookingCreateSchema',
    'EventBookingSchema',
    'EventBookingCreateSchema',
]

