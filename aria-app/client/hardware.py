"""
Hardware control for Raspberry Pi.
"""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import RPi.GPIO, but handle gracefully if not on Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available. Running in simulation mode.")


class DoorController:
    """Controller for door lock/unlock via GPIO relay."""
    
    def __init__(self, gpio_pin: int = None, unlock_duration: int = None):
        """
        Initialize door controller.
        
        Args:
            gpio_pin: GPIO pin number for relay
            unlock_duration: Duration to keep door unlocked (seconds)
        """
        from .config import ClientConfig
        
        self.gpio_pin = gpio_pin or ClientConfig.RELAY_GPIO_PIN
        self.unlock_duration = unlock_duration or ClientConfig.UNLOCK_DURATION_SECONDS
        self.is_unlocked = False
        self.unlock_time = None
        
        if GPIO_AVAILABLE:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            GPIO.output(self.gpio_pin, GPIO.LOW)
            logger.info(f"GPIO initialized on pin {self.gpio_pin}")
        else:
            logger.warning("Running in simulation mode (no GPIO hardware)")
    
    def unlock(self) -> bool:
        """Unlock the door."""
        try:
            if GPIO_AVAILABLE:
                GPIO.output(self.gpio_pin, GPIO.HIGH)
            self.is_unlocked = True
            self.unlock_time = time.time()
            logger.info("Door unlocked")
            return True
        except Exception as e:
            logger.error(f"Error unlocking door: {str(e)}")
            return False
    
    def lock(self) -> bool:
        """Lock the door."""
        try:
            if GPIO_AVAILABLE:
                GPIO.output(self.gpio_pin, GPIO.LOW)
            self.is_unlocked = False
            self.unlock_time = None
            logger.info("Door locked")
            return True
        except Exception as e:
            logger.error(f"Error locking door: {str(e)}")
            return False
    
    def should_lock(self) -> bool:
        """Check if door should be locked based on duration."""
        if not self.is_unlocked or self.unlock_time is None:
            return False
        
        elapsed = time.time() - self.unlock_time
        return elapsed >= self.unlock_duration
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
                logger.info("GPIO cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up GPIO: {str(e)}")

