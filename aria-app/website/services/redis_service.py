"""Redis service for event-driven communication."""
import redis
import json
import os
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class RedisService:
    """Service to handle Redis pub/sub operations."""
    
    _client = None

    @classmethod
    def get_client(cls):
        """Lazy initialization of Redis client."""
        if cls._client is None:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            try:
                cls._client = redis.from_url(redis_url, decode_responses=True)
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
        return cls._client

    @staticmethod
    def publish_event(channel: str, data: dict):
        """
        Publish an event to a Redis channel.
        
        Args:
            channel: Redis channel name
            data: Dictionary containing event data
        """
        client = RedisService.get_client()
        if client:
            try:
                payload = json.dumps(data)
                client.publish(channel, payload)
                logger.info(f"Published event to {channel}: {data}")
                return True
            except Exception as e:
                logger.error(f"Error publishing to Redis: {str(e)}")
        return False

    @staticmethod
    def publish_watch_room(room_id: int):
        """Helper to publish watch_room event."""
        return RedisService.publish_event(f"watch_room:{room_id}", {
            "room_id": room_id,
            "action": "start_monitoring"
        })

    @staticmethod
    def publish_token_validated(room_id: int, booking_id: int, booking_type: str = "room"):
        """Helper to publish token_validated event."""
        return RedisService.publish_event(f"token_validated:{room_id}", {
            "room_id": room_id,
            "booking_id": booking_id,
            "booking_type": booking_type,
            "action": "unlock_door"
        })
