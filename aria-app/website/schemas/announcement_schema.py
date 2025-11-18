"""Announcement validation schemas."""
from marshmallow import Schema, fields, validate, ValidationError


class AnnouncementSchema(Schema):
    """Schema for announcement output."""
    AnnounceID = fields.Integer(dump_only=True)
    AdminID = fields.String(required=True)
    PostDate = fields.DateTime(dump_only=True)
    Title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    Content = fields.String(required=True, validate=validate.Length(min=1))


class AnnouncementCreateSchema(Schema):
    """Schema for creating announcements."""
    Title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    Content = fields.String(required=True, validate=validate.Length(min=1))


class AnnouncementUpdateSchema(Schema):
    """Schema for updating announcements."""
    Title = fields.String(validate=validate.Length(min=1, max=255))
    Content = fields.String(validate=validate.Length(min=1))

