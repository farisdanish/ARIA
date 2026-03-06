#!/usr/bin/env python3
"""
ARIA Pi Simulator - Redis Driven Access Control
Mimics a Raspberry Pi by listening to Redis events and performing mock recognition.
"""
import sys
import time
import logging
import json
import redis
import threading
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

# Adjust path to allow importing from parent package if needed
sys.path.append(str(Path(__file__).parent.parent))

from client.config import ClientConfig
from client.api_client import APIClient
from client.face_recognition import FaceRecognizer
from client.hardware import DoorController

logger = logging.getLogger("PiSimulator")

class PiSimulator:
    def __init__(self):
        self.api_client = APIClient()
        self.face_recognizer = FaceRecognizer()
        self.door_controller = DoorController()
        self.redis_client = redis.from_url(ClientConfig.REDIS_URL, decode_responses=True)
        self.active_watches = {} # room_id -> thread
        self.stop_events = {}    # room_id -> stop_event

    def setup(self):
        """Initialize components and download models."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info("Starting ARIA Pi Simulator...")
        
        # Download models if they don't exist
        faces_db = ClientConfig.FACES_DB_FILE
        embeddings = ClientConfig.FACES_EMBEDDINGS_FILE
        
        if not faces_db.exists() or not embeddings.exists():
            logger.info("Downloading models from server...")
            self.api_client.get_face_database(str(faces_db))
            self.api_client.get_face_embeddings(str(embeddings))
            
        if not self.face_recognizer.load_model():
            logger.error("Failed to load face recognition model.")
            return False
            
        logger.info("Simulator setup complete.")
        return True

    def listen_to_events(self):
        """Listen to Redis pub/sub events."""
        pubsub = self.redis_client.pubsub()
        pubsub.psubscribe("watch_room:*", "token_validated:*")
        
        logger.info("Listening for events on Redis...")
        
        for message in pubsub.listen():
            if message['type'] == 'pmessage':
                channel = message['channel']
                data = json.loads(message['data'])
                
                if channel.startswith("watch_room:"):
                    room_id = int(channel.split(":")[1])
                    self.start_watching(room_id)
                
                elif channel.startswith("token_validated:"):
                    room_id = int(channel.split(":")[1])
                    logger.info(f"QR Token Validated for Room {room_id}. Unlocking door.")
                    self.door_controller.unlock()

    def start_watching(self, room_id):
        """Start a recognition loop for a specific room."""
        if room_id in self.active_watches:
            logger.info(f"Already watching room {room_id}")
            return

        logger.info(f"Started monitoring room {room_id} for face recognition.")
        stop_event = threading.Event()
        thread = threading.Thread(
            target=self.recognition_loop, 
            args=(room_id, stop_event),
            daemon=True
        )
        self.active_watches[room_id] = thread
        self.stop_events[room_id] = stop_event
        thread.start()

    def recognition_loop(self, room_id, stop_event):
        """Loop through test images to find a match for the current booking."""
        try:
            while not stop_event.is_set():
                # Get current booking for this room to know who to look for
                bookings = self.api_client.get_room_bookings()
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                
                current_booking = None
                for b in bookings:
                    if b.get('RoomID') == room_id and b.get('Start') <= now < b.get('End'):
                        current_booking = b
                        break
                
                if not current_booking:
                    logger.info(f"No active booking for Room {room_id}. Stopping monitor.")
                    break
                
                expected_user = current_booking.get('StudID') or current_booking.get('StaffID')
                if not expected_user:
                    break

                # Iterate through test images
                test_dir = ClientConfig.TEST_IMAGES_PATH
                if not test_dir.exists():
                    logger.warning(f"Test images directory {test_dir} not found.")
                    time.sleep(10)
                    continue

                for img_path in test_dir.glob("*.jpg"):
                    if stop_event.is_set(): break
                    
                    frame = cv2.imread(str(img_path))
                    if frame is None: continue
                    
                    face, _, _, _, _ = self.face_recognizer.get_face(frame)
                    if face is not None:
                        identity, confidence = self.face_recognizer.recognize_face(face, expected_user)
                        
                        if identity == expected_user:
                            logger.info(f"MATCH FOUND for {expected_user} in room {room_id}! Unlocking.")
                            # Publish success back to Redis
                            self.redis_client.publish(f"face_matched:{room_id}", json.dumps({
                                "room_id": room_id,
                                "user_id": expected_user,
                                "action": "unlock_door"
                            }))
                            self.door_controller.unlock()
                            stop_event.set() # Stop watching once unlocked
                            break
                
                time.sleep(5) # Delay between image loop passes
        finally:
            del self.active_watches[room_id]
            del self.stop_events[room_id]

    def run(self):
        if self.setup():
            try:
                self.listen_to_events()
            except KeyboardInterrupt:
                logger.info("Shutting down simulator...")
            finally:
                self.redis_client.close()

if __name__ == "__main__":
    sim = PiSimulator()
    sim.run()
