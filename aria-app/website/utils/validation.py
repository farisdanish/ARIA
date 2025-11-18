"""Validation utilities using Marshmallow."""
from marshmallow import ValidationError
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def validate_request(schema_class, data: Dict[str, Any], partial: bool = False) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate request data using a Marshmallow schema.
    
    Args:
        schema_class: Marshmallow schema class
        data: Data to validate
        partial: Allow partial validation (for updates)
        
    Returns:
        (is_valid, validated_data, error_message)
    """
    try:
        schema = schema_class()
        validated_data = schema.load(data, partial=partial)
        return True, validated_data, None
    except ValidationError as e:
        error_msg = "; ".join([f"{field}: {', '.join(messages)}" 
                               for field, messages in e.messages.items()])
        logger.warning(f"Validation failed: {error_msg}")
        return False, None, error_msg
    except Exception as e:
        logger.error(f"Unexpected validation error: {str(e)}")
        return False, None, f"Validation error: {str(e)}"


def validate_form_data(schema_class, form_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate form data (from Flask request.form).
    
    Args:
        schema_class: Marshmallow schema class
        form_data: Form data dictionary
        
    Returns:
        (is_valid, validated_data, error_message)
    """
    # Convert form data to dict if needed
    if hasattr(form_data, 'to_dict'):
        data = form_data.to_dict()
    else:
        data = dict(form_data)
    
    return validate_request(schema_class, data)

