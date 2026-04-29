"""Remove stale guest accounts and any legacy guest-linked face assets."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Flask

from ..models.base import db
from ..models.face import RegisteredFace
from ..models.guest import GuestUser


def _delete_paths_for_face_record(app: Flask, face_img_field: str) -> None:
    """Remove face image files listed in FaceIMG (newline-separated, relative to FACES_DB_PATH)."""
    base: Path = Path(app.config['FACES_DB_PATH'])
    for line in (face_img_field or '').splitlines():
        rel = line.strip()
        if not rel:
            continue
        full = (base / rel).resolve()
        try:
            full.relative_to(base.resolve())
        except ValueError:
            app.logger.warning('Skipping face path outside FACES_DB_PATH: %s', rel)
            continue
        if full.is_file():
            full.unlink()
            app.logger.info('Deleted guest face file: %s', full)


def cleanup_expired_guests(app: Flask) -> None:
    """
    Delete expired guest sessions and their guest-only face data.

    Demo guest embeddings live in the database and never enter the shared SGD model,
    so cleanup must not trigger train_model() for these rows.
    """
    now = datetime.utcnow()
    guests = GuestUser.query.filter(
        ((GuestUser.ExpiresAt == None) | (GuestUser.ExpiresAt < datetime.utcnow())) | (GuestUser.Status == 'expired')
    ).all()
    if not guests:
        return

    for guest in guests:
        gid = guest.GuestID
        faces = RegisteredFace.query.filter_by(GuestID=gid).all()
        if not faces:
            db.session.delete(guest)
            app.logger.info('Deleted stale guest user with no face rows: %s', gid)
            continue

        for rf in faces:
            try:
                _delete_paths_for_face_record(app, rf.FaceIMG)
            except OSError as exc:
                app.logger.warning('Could not delete some files for guest %s: %s', gid, exc)
            db.session.delete(rf)
            app.logger.info('Removed RegisteredFace %s for guest %s', rf.FaceID, gid)

        db.session.delete(guest)
        app.logger.info('Deleted expired guest user %s (expires %s)', gid, guest.ExpiresAt)

    db.session.commit()
