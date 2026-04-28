"""File utility functions."""
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app
from typing import Optional
import logging

from .upload_validation import validate_image_upload

logger = logging.getLogger(__name__)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg'})


def save_uploaded_file(file, subfolder: str = '', filename: str = None) -> Optional[str]:
    """
    Save an uploaded file.

    Args:
        file: FileStorage object from request
        subfolder: Subfolder within upload directory
        filename: Optional custom filename (if None, uses secure_filename)

    Returns:
        Relative path to saved file, or None if save failed
    """
    if not file or not file.filename:
        return None

    if not allowed_file(file.filename):
        logger.warning('File type not allowed: %s', file.filename)
        return None

    if not file.content_type:
        logger.warning('Upload rejected: missing Content-Type for %s', file.filename)
        return None

    raw = file.read()
    ok, err_msg, _ = validate_image_upload(raw, file.content_type)
    if not ok:
        logger.warning('Image validation failed for %s: %s', file.filename, err_msg)
        return None

    if filename is None:
        filename = secure_filename(file.filename)

    upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
    if subfolder:
        upload_folder = upload_folder / subfolder
        upload_folder.mkdir(parents=True, exist_ok=True)

    filepath = upload_folder / filename

    try:
        filepath.write_bytes(raw)
        logger.info('File saved: %s', filepath)

        if subfolder:
            return f'{subfolder}/{filename}'
        return filename
    except Exception as e:
        logger.error('Failed to save file %s: %s', filename, e)
        return None


def delete_file(filepath: str) -> bool:
    """
    Delete a file.

    Args:
        filepath: Relative path to file (from upload folder)

    Returns:
        True if deleted, False otherwise
    """
    try:
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        full_path = upload_folder / filepath

        if full_path.exists():
            full_path.unlink()
            logger.info('File deleted: %s', full_path)
            return True
        logger.warning('File not found: %s', full_path)
        return False
    except Exception as e:
        logger.error('Failed to delete file %s: %s', filepath, e)
        return False
