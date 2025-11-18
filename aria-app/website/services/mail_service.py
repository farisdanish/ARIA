"""Mail service for sending emails."""
from flask_mail import Mail, Message
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class MailService:
    """Service for sending emails."""
    
    def __init__(self, mail: Mail):
        self.mail = mail
    
    def send_mail(self, subject: str, recipients: str | list, content: str) -> bool:
        """
        Send an email.
        
        Args:
            subject: Email subject
            recipients: Email recipient(s) - string or list
            content: Email body content
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if isinstance(recipients, str):
                recipients = [recipients]
            
            msg = Message(
                subject=subject,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
                recipients=recipients,
                body=content
            )
            self.mail.send(msg)
            logger.info(f"Email sent to {recipients}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipients}: {str(e)}")
            return False
    
    def send_booking_confirmation(self, recipient: str, room_name: str, booking_date: str) -> bool:
        """Send booking confirmation email."""
        subject = f'Room Booking on {booking_date} is CONFIRMED'
        content = f'Your Room Booking on {booking_date} at {room_name} is confirmed!'
        return self.send_mail(subject, recipient, content)
    
    def send_access_notification(self, recipient: str, user_name: str, room_name: str, timestamp: str) -> bool:
        """Send room access notification email."""
        subject = f'Room Access Notification at {room_name} Issued'
        content = f'You ({user_name}) have just been cleared to enter room: {room_name} at {timestamp}'
        return self.send_mail(subject, recipient, content)

