"""Validate uploaded image bytes (magic numbers) and declared MIME type."""
from __future__ import annotations

import base64
from typing import Optional, Tuple

# JPEG: FF D8 FF; PNG: 89 50 4E 47 0D 0A 1A 0A
_JPEG_PREFIX = b'\xff\xd8\xff'
_PNG_PREFIX = b'\x89PNG\r\n\x1a\n'


def detect_image_kind(data: bytes) -> Optional[str]:
    """Return 'jpeg', 'png', or None if bytes are not a recognized image start."""
    if len(data) < 8:
        return None
    if data.startswith(_JPEG_PREFIX):
        return 'jpeg'
    if data.startswith(_PNG_PREFIX):
        return 'png'
    return None


def normalized_mime(mime: Optional[str]) -> Optional[str]:
    if not mime:
        return None
    m = mime.split(';')[0].strip().lower()
    if m == 'image/jpg':
        return 'image/jpeg'
    return m


def parse_data_url_image(data_url: str) -> Tuple[Optional[str], bytes]:
    """
    Parse a data URL or raw base64 payload from the client.

    Returns (mime_or_none, raw_bytes). If there is no data: prefix, mime is None.
    """
    if not data_url:
        return None, b''
    if ',' in data_url and data_url.strip().startswith('data:'):
        header, _, b64_part = data_url.partition(',')
        meta = header[5:]
        mime = meta.split(';')[0].strip().lower()
        if mime == 'image/jpg':
            mime = 'image/jpeg'
        try:
            raw = base64.b64decode(b64_part, validate=True)
        except (ValueError, TypeError):
            return None, b''
        if mime not in ('image/jpeg', 'image/png'):
            return None, b''
        return mime, raw
    try:
        payload = data_url.split(',', 1)[-1]
        raw = base64.b64decode(payload, validate=True)
    except (ValueError, TypeError, IndexError):
        return None, b''
    return None, raw


def validate_image_upload(
    raw: bytes,
    content_type: Optional[str],
    *,
    require_content_type: bool = True,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate body as JPEG or PNG using magic bytes and optional Content-Type.

    Returns:
        (ok, error_message, canonical_mime) where canonical_mime is image/jpeg or image/png.
    """
    kind = detect_image_kind(raw)
    if kind is None:
        return False, 'File is not a valid JPEG or PNG image.', None

    expected_mime = 'image/jpeg' if kind == 'jpeg' else 'image/png'
    mime = normalized_mime(content_type)
    if require_content_type:
        if mime not in ('image/jpeg', 'image/png'):
            return False, 'Content-Type must be image/jpeg or image/png.', None
        if mime != expected_mime:
            return False, 'File content does not match declared image type.', None

    return True, None, expected_mime
