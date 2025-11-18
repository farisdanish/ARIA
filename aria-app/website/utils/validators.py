"""Validation utilities."""
from typing import Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number (basic check)."""
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if it's digits and reasonable length
    return cleaned.isdigit() and len(cleaned) >= 10


def validate_student_registration(stud_id: str, stud_name: str, stud_email: str,
                                 stud_contact: str, password1: str, password2: str) -> Tuple[bool, Optional[str]]:
    """
    Validate student registration data.
    
    Returns:
        (is_valid, error_message)
    """
    if len(stud_id) < 10:
        return False, "Matric Number must be at least 10 characters"
    
    if not stud_name or len(stud_name.strip()) == 0:
        return False, "Please submit your name"
    
    if len(stud_email) < 4 or not validate_email(stud_email):
        return False, "Please enter a valid email address"
    
    if not validate_phone(stud_contact):
        return False, "Please enter a valid contact number (at least 10 digits)"
    
    if password1 != password2:
        return False, "Passwords entered are not identical"
    
    if len(password1) < 8:
        return False, "Password must be at least 8 characters long"
    
    return True, None


def validate_staff_registration(staff_id: str, staff_name: str, staff_email: str,
                                staff_contact: str, password1: str, password2: str) -> Tuple[bool, Optional[str]]:
    """
    Validate staff registration data.
    
    Returns:
        (is_valid, error_message)
    """
    if len(staff_id) < 10:
        return False, "Staff ID must be at least 10 characters"
    
    if not staff_name or len(staff_name.strip()) == 0:
        return False, "Please submit your name"
    
    if len(staff_email) < 4 or not validate_email(staff_email):
        return False, "Please enter a valid email address"
    
    if not validate_phone(staff_contact):
        return False, "Please enter a valid contact number (at least 10 digits)"
    
    if password1 != password2:
        return False, "Passwords entered are not identical"
    
    if len(password1) < 8:
        return False, "Password must be at least 8 characters long"
    
    return True, None

