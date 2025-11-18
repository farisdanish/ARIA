"""Room validation schemas."""
from marshmallow import Schema, fields, validate


class RoomSchema(Schema):
    """Schema for room output."""
    RoomID = fields.Integer(dump_only=True)
    AdminID = fields.String(allow_none=True)
    RoomName = fields.String(required=True, validate=validate.Length(min=1, max=255))
    roomIMG = fields.String(allow_none=True)
    RoomInfo = fields.String(allow_none=True)
    RoomType = fields.String(allow_none=True)
    RoomStatus = fields.String(validate=validate.OneOf(['Available', 'Occupied', 'Maintenance']))


class RoomCreateSchema(Schema):
    """Schema for creating rooms."""
    RoomName = fields.String(required=True, validate=validate.Length(min=1, max=255))
    RoomInfo = fields.String(allow_none=True)
    RoomType = fields.String(allow_none=True)
    RoomStatus = fields.String(
        validate=validate.OneOf(['Available', 'Occupied', 'Maintenance']),
        missing='Available'
    )


class RoomUpdateSchema(Schema):
    """Schema for updating rooms."""
    RoomName = fields.String(validate=validate.Length(min=1, max=255))
    RoomInfo = fields.String(allow_none=True)
    RoomType = fields.String(allow_none=True)
    RoomStatus = fields.String(validate=validate.OneOf(['Available', 'Occupied', 'Maintenance']))

