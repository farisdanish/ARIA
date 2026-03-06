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

    def send_qr_checkin_email(self, recipient: str, qr_image_base64: str, booking) -> bool:
        """
        Send an email containing the QR code for check-in.
        
        Args:
            recipient: Recipient email
            qr_image_base64: Base64-encoded PNG of the QR code
            booking: RoomBooking or EventBooking instance
        """
        booking_id = getattr(booking, 'RBookID', getattr(booking, 'EBookID', 'Unknown'))
        booking_type = "Room" if hasattr(booking, 'RBookID') else "Event"
        
        subject = f'Your {booking_type} Booking QR Code - ID: {booking_id}'
        
        # HTML body with embedded image
        html_content = f"""
        <html>
            <body>
                <h2>QR Code for Your Booking</h2>
                <p>Thank you for booking with ARIA. Please use the QR code below to check in at the laboratory.</p>
                <div style="margin: 20px 0;">
                    <img src="data:image/png;base64,{qr_image_base64}" alt="Booking QR Code" style="border: 1px solid #ccc; padding: 10px;" />
                </div>
                <p><strong>Booking Type:</strong> {booking_type}</p>
                <p><strong>Booking ID:</strong> {booking_id}</p>
                <p><strong>Start:</strong> {booking.Start}</p>
                <p><strong>End:</strong> {booking.End}</p>
                <p>Scan this code at the door scanner or on your mobile device to unlock the door.</p>
            </body>
        </html>
        """
        
        try:
            msg = Message(
                subject=subject,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
                recipients=[recipient],
                html=html_content
            )
            self.mail.send(msg)
            logger.info(f"QR Email sent to {recipient} for booking {booking_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send QR email to {recipient}: {str(e)}")
            return False

