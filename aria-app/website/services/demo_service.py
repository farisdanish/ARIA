"""Guest-only public demo flow using per-guest FaceNet embeddings."""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from flask import current_app
from itsdangerous import BadSignature, URLSafeSerializer
from PIL import Image

from ..models.base import db
from ..models.face import RegisteredFace
from ..models.guest import GuestUser
from ..services.face_service import FaceService
from ..utils.upload_validation import validate_image_upload


DEMO_COOKIE_NAME = 'demo_token'
_face_service = FaceService()
_MAX_DEMO_IMAGE_BYTES = 5 * 1024 * 1024


class DemoBusyError(RuntimeError):
    """Raised when the public demo is unavailable for a new guest session."""


class DemoEnrollmentCompleteError(RuntimeError):
    """Raised when a guest already has the required number of embeddings."""


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _serializer(secret_key: str) -> URLSafeSerializer:
    return URLSafeSerializer(secret_key, salt='aria-demo-cookie')


def sign_demo_cookie(token: str) -> str:
    """Sign a raw demo token before writing it to a browser cookie."""
    return _serializer(current_app.secret_key).dumps(token)


def unsign_demo_cookie(value: str) -> Optional[str]:
    """Return the raw demo token from a signed cookie, or None if invalid."""
    if not value:
        return None
    try:
        return _serializer(current_app.secret_key).loads(value)
    except BadSignature:
        return None


def _embedding_list(record: Optional[RegisteredFace]) -> list[list[float]]:
    if record is None or not record.EmbeddingsJSON:
        return []
    try:
        data = json.loads(record.EmbeddingsJSON)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [embedding for embedding in data if isinstance(embedding, list)]


def get_embedding_count(guest: GuestUser) -> int:
    """Return how many demo embeddings are currently stored for this guest."""
    record = db.session.query(RegisteredFace).filter_by(GuestID=guest.GuestID).first()
    return len(_embedding_list(record))


def _demo_face_record(guest: GuestUser) -> RegisteredFace:
    record = db.session.query(RegisteredFace).filter_by(GuestID=guest.GuestID).first()
    if record is None:
        record = RegisteredFace(FaceIMG='', GuestID=guest.GuestID, EmbeddingsJSON='[]')
        db.session.add(record)
        db.session.flush()
    return record


def _decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    if len(image_bytes) > _MAX_DEMO_IMAGE_BYTES:
        raise ValueError('Image exceeds maximum size limit.')

    ok, err_msg, _ = validate_image_upload(image_bytes, None, require_content_type=False)
    if not ok:
        raise ValueError(err_msg or 'Invalid image file.')

    cv2 = _face_service._cv2()
    frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError('Invalid image payload.')
    return frame


def _extract_embedding(image_bytes: bytes) -> np.ndarray:
    frame = _decode_image_bytes(image_bytes)
    face, _, _, _, _ = _face_service.get_face(frame)
    if face is None:
        raise ValueError('No face detected.')

    face = np.asarray(Image.fromarray(np.asarray(face)).resize((160, 160)))
    return _face_service.get_embedding(face)


def cosine_similarity_np(a, b):
    """Compute cosine similarity with numpy only."""
    a_vec = np.asarray(a, dtype=np.float32)
    b_vec = np.asarray(b, dtype=np.float32)
    denom = np.linalg.norm(a_vec) * np.linalg.norm(b_vec)
    if denom == 0:
        return 0.0
    return float(np.dot(a_vec, b_vec) / denom)


def create_demo_session(app) -> tuple[GuestUser, str]:
    """
    Create a guest demo session and return the DB row plus raw token.

    A session is refused if the demo is busy or if the guest row cap is reached.
    """
    now = datetime.utcnow()
    active_query = GuestUser.query.filter(
        GuestUser.ExpiresAt > now,
        GuestUser.Status.in_(('enrolling', 'ready')),
    )
    if active_query.count() >= app.config['DEMO_MAX_CONCURRENT_SESSIONS']:
        raise DemoBusyError('The public demo is currently busy.')

    if GuestUser.query.filter(GuestUser.ExpiresAt > now).count() >= app.config['DEMO_MAX_GUEST_ROWS']:
        raise DemoBusyError('The public demo is currently at capacity.')

    raw_token = secrets.token_hex(32)
    guest = GuestUser(
        GuestID=f"guest-{secrets.token_hex(6)}",
        TokenHash=_token_hash(raw_token),
        ExpiresAt=now + timedelta(hours=app.config['DEMO_SESSION_HOURS']),
        Status='pending',
    )
    db.session.add(guest)
    db.session.commit()
    return guest, raw_token


def get_guest_from_cookie(token: str) -> GuestUser | None:
    """
    Look up a guest from a raw demo token.

    Expired rows are marked as expired and treated as invalid.
    """
    if not token:
        return None

    guest = GuestUser.query.filter_by(TokenHash=_token_hash(token)).first()
    if guest is None:
        return None

    if guest.Status == 'expired' or guest.ExpiresAt is None or guest.ExpiresAt < datetime.utcnow():
        if guest.Status != 'expired':
            guest.Status = 'expired'
            db.session.commit()
        return None

    return guest


def load_guest_from_signed_cookie(cookie_value: str, *, include_expired: bool = False) -> GuestUser | None:
    """Resolve a guest from the signed cookie value."""
    raw_token = unsign_demo_cookie(cookie_value)
    if not raw_token:
        return None

    guest = GuestUser.query.filter_by(TokenHash=_token_hash(raw_token)).first()
    if guest is None:
        return None

    if guest.Status == 'expired' or guest.ExpiresAt is None or guest.ExpiresAt < datetime.utcnow():
        if guest.Status != 'expired':
            guest.Status = 'expired'
            db.session.commit()
        return guest if include_expired else None

    return guest


def add_demo_frame(guest: GuestUser, image_bytes: bytes) -> dict:
    """
    Extract one embedding for a guest demo session and persist it in JSON form.
    """
    required = current_app.config['DEMO_SAMPLES_REQUIRED']
    record = _demo_face_record(guest)
    embeddings = _embedding_list(record)
    if len(embeddings) >= required:
        raise DemoEnrollmentCompleteError('Enrollment already complete.')

    embedding = _extract_embedding(image_bytes)
    embeddings.append(np.asarray(embedding, dtype=np.float32).tolist())
    record.EmbeddingsJSON = json.dumps(embeddings)
    guest.Status = 'enrolling'
    db.session.commit()
    return {'sample_count': len(embeddings), 'required': required}


def complete_demo_enrollment(guest: GuestUser) -> None:
    """
    Mark a guest as ready once the required embeddings are present.
    """
    record = db.session.query(RegisteredFace).filter_by(GuestID=guest.GuestID).first()
    embeddings = _embedding_list(record)
    required = current_app.config['DEMO_SAMPLES_REQUIRED']
    if len(embeddings) != required:
        raise ValueError(f'Expected exactly {required} embeddings before completion.')

    guest.Status = 'ready'
    db.session.commit()


def recognize_demo_guest(guest: GuestUser, image_bytes: bytes) -> dict:
    """
    Run guest-only embedding similarity without touching the shared SGD model.
    """
    now = datetime.utcnow()
    debounce_seconds = current_app.config['DEMO_RECOGNITION_DEBOUNCE_SECONDS']
    if guest.LastRecognizedAt and (now - guest.LastRecognizedAt).total_seconds() < debounce_seconds:
        return {
            'matched': bool(guest.LastRecognitionResult),
            'confidence': float(guest.LastRecognitionConfidence or 0.0),
            'cached': True,
        }

    record = db.session.query(RegisteredFace).filter_by(GuestID=guest.GuestID).first()
    embeddings = _embedding_list(record)
    if len(embeddings) != current_app.config['DEMO_SAMPLES_REQUIRED']:
        raise ValueError('Guest enrollment is incomplete.')

    live_embedding = _extract_embedding(image_bytes)
    similarities = [
        cosine_similarity_np(live_embedding, stored_embedding)
        for stored_embedding in embeddings
    ]
    confidence = max(similarities) if similarities else 0.0
    matched = confidence >= current_app.config['DEMO_SIMILARITY_THRESHOLD']

    guest.LastRecognizedAt = now
    guest.LastRecognitionResult = matched
    guest.LastRecognitionConfidence = confidence
    db.session.commit()

    return {
        'matched': matched,
        'confidence': confidence,
        'cached': False,
    }


def cleanup_demo_guest(guest: GuestUser) -> None:
    """
    Delete one guest demo session and any guest-only embedding row.
    """
    records = db.session.query(RegisteredFace).filter_by(GuestID=guest.GuestID).all()
    for record in records:
        db.session.delete(record)

    db.session.delete(guest)
    db.session.commit()
    current_app.logger.info('Deleted demo guest session %s', guest.GuestID)
