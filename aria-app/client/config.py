"""
Configuration for ARIA Edge Device Client.
"""
import os
from pathlib import Path


class ClientConfig:
    """Configuration for the edge device client."""
    
    # API Configuration
    API_BASE_URL = os.environ.get('ARIA_API_URL', 'http://localhost:5000/api')
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', '30'))
    
    # Hardware Configuration
    RELAY_GPIO_PIN = int(os.environ.get('RELAY_GPIO_PIN', '17'))
    UNLOCK_DURATION_SECONDS = int(os.environ.get('UNLOCK_DURATION_SECONDS', '5'))
    
    # Face Recognition Configuration
    FACE_CONFIDENCE_THRESHOLD = float(os.environ.get('FACE_CONFIDENCE_THRESHOLD', '0.70'))
    FACE_DETECTION_COUNT_THRESHOLD = int(os.environ.get('FACE_DETECTION_COUNT_THRESHOLD', '3'))
    FACES_DB_FILE = Path(os.environ.get('FACES_DB_FILE', 'registered-faces-db.npz'))
    FACES_EMBEDDINGS_FILE = Path(os.environ.get('FACES_EMBEDDINGS_FILE', 'registered-faces-db-embeddings.npz'))
    
    # Camera Configuration
    CAMERA_INDEX = int(os.environ.get('CAMERA_INDEX', '0'))
    CAMERA_FOURCC = os.environ.get('CAMERA_FOURCC', 'MJPG')
    
    # Polling Configuration
    BOOKING_CHECK_INTERVAL = int(os.environ.get('BOOKING_CHECK_INTERVAL', '30'))  # seconds
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'aria_client.log')
    
    @classmethod
    def validate(cls):
        """Validate configuration."""
        errors = []
        
        if not cls.API_BASE_URL:
            errors.append("API_BASE_URL is required")
        
        if cls.RELAY_GPIO_PIN < 1 or cls.RELAY_GPIO_PIN > 40:
            errors.append("RELAY_GPIO_PIN must be between 1 and 40")
        
        if cls.FACE_CONFIDENCE_THRESHOLD < 0 or cls.FACE_CONFIDENCE_THRESHOLD > 1:
            errors.append("FACE_CONFIDENCE_THRESHOLD must be between 0 and 1")
        
        return errors

