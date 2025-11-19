"""File utility functions."""
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app
from typing import Optional
import logging

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
        logger.warning(f"File type not allowed: {file.filename}")
        return None
    
    if filename is None:
        filename = secure_filename(file.filename)
    
    upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
    if subfolder:
        upload_folder = upload_folder / subfolder
        upload_folder.mkdir(parents=True, exist_ok=True)
    
    filepath = upload_folder / filename
    
    try:
        file.save(str(filepath))
        logger.info(f"File saved: {filepath}")
        
        # Return relative path
        if subfolder:
            return f"{subfolder}/{filename}"
        return filename
    except Exception as e:
        logger.error(f"Failed to save file {filename}: {str(e)}")
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
            logger.info(f"File deleted: {full_path}")
            return True
        else:
            logger.warning(f"File not found: {full_path}")
            return False
    except Exception as e:
        logger.error(f"Failed to delete file {filepath}: {str(e)}")
        return False

