"""
API Client for communicating with ARIA server.
"""
import requests
import logging
from typing import Optional, Dict, List
from datetime import datetime
from .config import ClientConfig

logger = logging.getLogger(__name__)


class APIClient:
    """Client for ARIA API."""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or ClientConfig.API_BASE_URL
        self.timeout = timeout or ClientConfig.API_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _get(self, endpoint: str) -> Optional[Dict]:
        """Make GET request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed for {url}: {str(e)}")
            return None
    
    def _post(self, endpoint: str, data: Dict) -> bool:
        """Make POST request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed for {url}: {str(e)}")
            return False
    
    def get_students(self) -> List[Dict]:
        """Get all students."""
        result = self._get('studentlist')
        return result if result else []
    
    def get_staff(self) -> List[Dict]:
        """Get all staff."""
        result = self._get('stafflist')
        return result if result else []
    
    def get_rooms(self) -> List[Dict]:
        """Get all rooms."""
        result = self._get('roomlist')
        return result if result else []
    
    def get_room_bookings(self) -> List[Dict]:
        """Get all room bookings."""
        result = self._get('rbooklists')
        return result if result else []
    
    def get_face_database(self, save_path: str) -> bool:
        """Download face database file."""
        url = f"{self.base_url}/faces"
        try:
            response = self.session.get(url, timeout=self.timeout * 2, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Face database downloaded to {save_path}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download face database: {str(e)}")
            return False
    
    def get_face_embeddings(self, save_path: str) -> bool:
        """Download face embeddings file."""
        url = f"{self.base_url}/facesembeds"
        try:
            response = self.session.get(url, timeout=self.timeout * 2, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Face embeddings downloaded to {save_path}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download face embeddings: {str(e)}")
            return False
    
    def log_access(self, room_id: int, stud_id: str = None, staff_id: str = None, 
                   status: int = 1, timestamp: str = None) -> bool:
        """
        Log room access.
        
        Args:
            room_id: Room ID
            stud_id: Student ID (if student)
            staff_id: Staff ID (if staff)
            status: Access status (0=denied, 1=granted)
            timestamp: Timestamp (ISO format), defaults to now
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data = {
            'RoomID': room_id,
            'StudID': stud_id,
            'StaffID': staff_id,
            'Status': status,
            'Timestamp': timestamp
        }
        
        return self._post('accesslogs', data)

