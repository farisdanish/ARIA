"""Remove stale guest accounts, face DB rows, disk images, and refresh embeddings."""
from __future__ import annotations

from datetime import datetime, timedelta
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
    Delete guest users older than 12 hours (idempotent).

    Removes RegisteredFace rows for those guests, image files on disk, guest rows,
    then retrains the face model so embedding npz files drop stale identities.
    """
    cutoff = datetime.utcnow() - timedelta(hours=12)
    guests = GuestUser.query.filter(GuestUser.CreatedAt < cutoff).all()
    if not guests:
        return

    from .face_service import FaceService

    face_service = FaceService()
    retrain = False

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
        app.logger.info('Deleted guest user %s (created %s)', gid, guest.CreatedAt)
        retrain = True

    db.session.commit()

    if retrain:
        try:
            if face_service.train_model():
                app.logger.info('Face model retrained after guest cleanup.')
            else:
                app.logger.error('Face model retraining failed after guest cleanup.')
        except Exception:
            app.logger.exception('Error retraining face model after guest cleanup.')
