"""Booking validation schemas."""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from datetime import datetime


class RoomBookingSchema(Schema):
    """Schema for room booking output."""
    RBookID = fields.Integer(dump_only=True)
    RoomID = fields.Integer(required=True)
    StudID = fields.String(allow_none=True)
    StaffID = fields.String(allow_none=True)
    Start = fields.DateTime(required=True)
    End = fields.DateTime(required=True)
    Purpose = fields.String(required=True, validate=validate.Length(min=1))
    RBookStatus = fields.String(
        validate=validate.OneOf(['Upcoming', 'Ongoing', 'Completed', 'Cancelled']),
        dump_only=True
    )


class RoomBookingCreateSchema(Schema):
    """Schema for creating room bookings."""
    RoomID = fields.Integer(required=True)
    StudID = fields.String(allow_none=True)
    StaffID = fields.String(allow_none=True)
    Start = fields.DateTime(required=True)
    End = fields.DateTime(required=True)
    Purpose = fields.String(required=True, validate=validate.Length(min=1))
    
    @validates_schema
    def validate_booking(self, data, **kwargs):
        """Validate booking constraints."""
        errors = {}
        
        # Check that either StudID or StaffID is provided
        if not data.get('StudID') and not data.get('StaffID'):
            errors['user'] = ['Either StudID or StaffID must be provided']
        
        # Check that Start is before End
        start = data.get('Start')
        end = data.get('End')
        if start and end:
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            if end <= start:
                errors['time'] = ['End time must be after start time']
            
            # Check duration (max 2 hours for room bookings)
            duration = (end - start).total_seconds() / 3600
            if duration > 2:
                errors['duration'] = ['Room booking duration cannot exceed 2 hours']
        
        if errors:
            raise ValidationError(errors)


class EventBookingSchema(Schema):
    """Schema for event booking output."""
    EBookID = fields.Integer(dump_only=True)
    RoomID = fields.Integer(required=True)
    StudID = fields.String(allow_none=True)
    StaffID = fields.String(allow_none=True)
    Start = fields.DateTime(required=True)
    End = fields.DateTime(required=True)
    Purpose = fields.String(required=True, validate=validate.Length(min=1))
    AddDetail = fields.String(allow_none=True)
    EbookStatus = fields.String(
        validate=validate.OneOf(['Upcoming', 'Ongoing', 'Completed', 'Cancelled']),
        dump_only=True
    )


class EventBookingCreateSchema(Schema):
    """Schema for creating event bookings."""
    RoomID = fields.Integer(required=True)
    StudID = fields.String(allow_none=True)
    StaffID = fields.String(allow_none=True)
    Start = fields.DateTime(required=True)
    End = fields.DateTime(required=True)
    Purpose = fields.String(required=True, validate=validate.Length(min=1))
    AddDetail = fields.String(allow_none=True)
    
    @validates_schema
    def validate_booking(self, data, **kwargs):
        """Validate booking constraints."""
        errors = {}
        
        # Check that either StudID or StaffID is provided
        if not data.get('StudID') and not data.get('StaffID'):
            errors['user'] = ['Either StudID or StaffID must be provided']
        
        # Check that Start is before End
        start = data.get('Start')
        end = data.get('End')
        if start and end:
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            if end <= start:
                errors['time'] = ['End time must be after start time']
        
        if errors:
            raise ValidationError(errors)

