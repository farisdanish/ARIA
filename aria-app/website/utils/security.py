"""Security helpers for browser and device access control."""
from __future__ import annotations

import hmac
from functools import wraps

from flask import abort, current_app, request
from flask_login import current_user


def _bearer_token() -> str | None:
    header = request.headers.get('Authorization', '').strip()
    if not header.startswith('Bearer '):
        return None
    token = header[7:].strip()
    return token or None


def has_valid_device_token() -> bool:
    """Return whether the request carries the configured device bearer token."""
    expected = current_app.config.get('DEVICE_API_TOKEN')
    provided = _bearer_token()
    if not expected or not provided:
        return False
    return hmac.compare_digest(provided, expected)


def device_api_required(fn):
    """Allow access only to requests carrying a valid device bearer token."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not has_valid_device_token():
            abort(401)
        return fn(*args, **kwargs)

    return wrapper


def admin_api_required(fn):
    """Allow access only to authenticated admin browser sessions."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_Admin():
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


def session_or_device_required(fn):
    """Allow access to authenticated browser sessions or trusted device callers."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated or has_valid_device_token():
            return fn(*args, **kwargs)
        abort(401)

    return wrapper


def booking_owned_by_current_user(booking) -> bool:
    """Return whether the current browser session owns the given booking."""
    if not current_user.is_authenticated:
        return False
    if current_user.is_Admin():
        return True
    if current_user.is_Student():
        return getattr(booking, 'StudID', None) == current_user.StudID
    if current_user.is_Staff():
        return getattr(booking, 'StaffID', None) == current_user.StaffID
    return False
