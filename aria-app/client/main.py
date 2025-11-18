#!/usr/bin/env python3
"""
ARIA Edge Device Client - Main Entry Point
Raspberry Pi application for room access control.
"""
import sys
import time
import logging
import cv2
from pathlib import Path
from datetime import datetime

from .config import ClientConfig
from .api_client import APIClient
from .face_recognition import FaceRecognizer
from .hardware import DoorController
from .room_monitor import RoomMonitor


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, ClientConfig.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(ClientConfig.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )


def download_face_models(api_client: APIClient) -> bool:
    """Download face recognition models from server."""
    logger = logging.getLogger(__name__)
    
    logger.info("Downloading face recognition models...")
    
    faces_db_path = ClientConfig.FACES_DB_FILE
    embeddings_path = ClientConfig.FACES_EMBEDDINGS_FILE
    
    success = True
    
    if not faces_db_path.exists():
        success = api_client.get_face_database(str(faces_db_path)) and success
    
    if not embeddings_path.exists():
        success = api_client.get_face_embeddings(str(embeddings_path)) and success
    
    if success:
        logger.info("Face models downloaded successfully")
    else:
        logger.error("Failed to download face models")
    
    return success


def select_room(rooms: list) -> int:
    """Interactive room selection."""
    print("\n=== Room Selection ===")
    normal_rooms = [r for r in rooms if r.get('RoomType') == 'Normal Room']
    
    if not normal_rooms:
        print("No normal rooms available.")
        return None
    
    for room in normal_rooms:
        print(f"{room.get('RoomID')}. {room.get('RoomName')}")
    
    while True:
        try:
            room_id = int(input("\nPlease enter room number: "))
            if any(r.get('RoomID') == room_id for r in normal_rooms):
                return room_id
            else:
                print("Invalid room number. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            return None


def detect_and_verify_face(face_recognizer: FaceRecognizer, door_controller: DoorController,
                          expected_identity: str, room_id: int, api_client: APIClient,
                          students: list, staff: list) -> bool:
    """
    Detect and verify face for access.
    
    Returns:
        True if access granted, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    cap = cv2.VideoCapture(ClientConfig.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*ClientConfig.CAMERA_FOURCC))
    
    detection_count = 0
    required_detections = ClientConfig.FACE_DETECTION_COUNT_THRESHOLD
    
    try:
        logger.info(f"Starting face recognition for user: {expected_identity}")
        
        while detection_count < required_detections:
            ret, frame = cap.read()
            if not ret:
                break
            
            face, x1, x2, y1, y2 = face_recognizer.get_face(frame)
            
            if face is not None:
                identity, confidence = face_recognizer.recognize_face(face, expected_identity)
                
                if identity == expected_identity and confidence >= ClientConfig.FACE_CONFIDENCE_THRESHOLD:
                    detection_count += 1
                    logger.info(f"Face verified: {identity} (confidence: {confidence:.2%}, count: {detection_count}/{required_detections})")
                    
                    # Draw green rectangle
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{identity} ({confidence:.1%})", (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    # Draw red rectangle
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    if identity:
                        cv2.putText(frame, f"Unknown ({confidence:.1%})", (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "No face found", (50, 50),
                           cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('Face Recognition', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("Face recognition cancelled by user")
                break
        
        if detection_count >= required_detections:
            # Grant access
            logger.info("Access granted - unlocking door")
            
            # Determine user type
            stud_id = None
            staff_id = None
            
            for student in students:
                if student.get('StudID') == expected_identity:
                    stud_id = expected_identity
                    break
            
            if not stud_id:
                for staff_member in staff:
                    if staff_member.get('StaffID') == expected_identity:
                        staff_id = expected_identity
                        break
            
            # Log access
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            api_client.log_access(room_id, stud_id, staff_id, status=1, timestamp=timestamp)
            
            # Unlock door
            door_controller.unlock()
            
            return True
        else:
            logger.warning(f"Access denied - insufficient detections ({detection_count}/{required_detections})")
            return False
            
    finally:
        cv2.destroyAllWindows()
        cap.release()


def main():
    """Main application loop."""
    logger = logging.getLogger(__name__)
    
    # Validate configuration
    config_errors = ClientConfig.validate()
    if config_errors:
        logger.error("Configuration errors:")
        for error in config_errors:
            logger.error(f"  - {error}")
        return 1
    
    # Initialize components
    api_client = APIClient()
    face_recognizer = FaceRecognizer()
    door_controller = DoorController()
    
    # Download face models if needed
    if not download_face_models(api_client):
        logger.error("Failed to download face models. Exiting.")
        return 1
    
    # Load face recognition model
    if not face_recognizer.load_model():
        logger.error("Failed to load face recognition model. Exiting.")
        return 1
    
    # Get initial data
    monitor = RoomMonitor(api_client, None)  # room_id set later
    data = monitor.refresh_data()
    
    # Select room
    room_id = select_room(data['rooms'])
    if room_id is None:
        logger.info("Room selection cancelled")
        return 0
    
    monitor.room_id = room_id
    logger.info(f"Monitoring room {room_id}")
    
    try:
        print("\n=== ARIA Access Control Started ===")
        print("Press Ctrl+C to stop\n")
        
        while True:
            # Refresh data periodically
            data = monitor.refresh_data()
            
            # Check for current booking
            booking = monitor.get_current_booking(data['bookings'])
            
            if not booking:
                logger.info("No active booking for this room")
                time.sleep(ClientConfig.BOOKING_CHECK_INTERVAL)
                continue
            
            # Get expected user
            expected_identity = monitor.get_expected_user(
                booking, data['students'], data['staff']
            )
            
            if not expected_identity:
                logger.warning("Could not determine expected user from booking")
                time.sleep(ClientConfig.BOOKING_CHECK_INTERVAL)
                continue
            
            logger.info(f"Active booking found for user: {expected_identity}")
            
            # Perform face recognition
            access_granted = detect_and_verify_face(
                face_recognizer, door_controller, expected_identity,
                room_id, api_client, data['students'], data['staff']
            )
            
            if access_granted:
                logger.info("Access granted - waiting for door to lock...")
                
                # Wait for door to auto-lock
                while door_controller.should_lock():
                    time.sleep(1)
                
                door_controller.lock()
                logger.info("Door locked")
            
            # Wait before next check
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("\nApplication stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1
    finally:
        door_controller.cleanup()
        logger.info("Application shutdown complete")
    
    return 0


if __name__ == '__main__':
    setup_logging()
    sys.exit(main())

