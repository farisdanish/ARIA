"""QR code check-in service."""
import secrets
import qrcode
import io
import base64
from datetime import datetime
from typing import Optional, Tuple
from ..models.room import RoomBooking, EventBooking
from ..models.base import db
import logging

logger = logging.getLogger(__name__)

# How many minutes before booking start the QR is valid for scanning
QR_EARLY_CHECKIN_MINUTES = 10


class QRService:
    """Service for QR code check-in operations."""

    # -------------------------------------------------------------------------
    # Token generation — called when a booking is created
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def attach_token_to_room_booking(booking: RoomBooking) -> RoomBooking:
        """
        Generate and attach a QR token to a room booking.
        Call this right after create_room_booking() in BookingService.

        Args:
            booking: RoomBooking instance (already committed)

        Returns:
            Updated booking with qr_token set
        """
        booking.qr_token = QRService.generate_token()
        db.session.commit()
        logger.info(f"QR token attached to room booking {booking.RBookID}")
        return booking

    @staticmethod
    def attach_token_to_event_booking(booking: EventBooking) -> EventBooking:
        """
        Generate and attach a QR token to an event booking.
        Call this right after create_event_booking() in BookingService.

        Args:
            booking: EventBooking instance (already committed)

        Returns:
            Updated booking with qr_token set
        """
        booking.qr_token = QRService.generate_token()
        db.session.commit()
        logger.info(f"QR token attached to event booking {booking.EBookID}")
        return booking

    # -------------------------------------------------------------------------
    # QR image generation — for emailing or displaying to the user
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_qr_image_base64(token: str, booking_id: int, booking_type: str = "room") -> str:
        """
        Generate a QR code image as a base64 string.
        The QR encodes a URL that the Pi scanner (or a phone) will hit.

        Args:
            token: The qr_token from the booking
            booking_id: RBookID or EBookID
            booking_type: "room" or "event"

        Returns:
            Base64-encoded PNG string (embed directly in <img> tags or emails)
        """
        # The payload the QR encodes — your Flask check-in route
        payload = f"/checkin/qr?token={token}&booking_id={booking_id}&type={booking_type}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    # -------------------------------------------------------------------------
    # Check-in validation — called by the /checkin/qr route
    # -------------------------------------------------------------------------

    @staticmethod
    def validate_room_checkin(token: str, booking_id: int) -> Tuple[bool, str, Optional[RoomBooking]]:
        """
        Validate a QR check-in attempt for a room booking.

        Args:
            token: Token scanned from QR code
            booking_id: RBookID from QR payload

        Returns:
            (success, message, booking_or_None)
        """
        booking = db.session.query(RoomBooking).filter_by(RBookID=booking_id).first()

        if not booking:
            return False, "Booking not found.", None

        if booking.qr_token != token:
            logger.warning(f"Invalid QR token attempt for room booking {booking_id}")
            return False, "Invalid QR code.", None

        if booking.RBookStatus == "Completed":
            return False, "This booking has already been checked in.", None

        if booking.RBookStatus == "Cancelled":
            return False, "This booking has been cancelled.", None

        now = datetime.now()
        window_open = booking.Start - \
            __import__('datetime').timedelta(minutes=QR_EARLY_CHECKIN_MINUTES)

        if now < window_open:
            return False, f"Check-in opens {QR_EARLY_CHECKIN_MINUTES} minutes before your booking.", None

        if now > booking.End:
            return False, "Booking window has expired.", None

        # All checks passed — mark as checked in
        booking.RBookStatus = "Ongoing"
        db.session.commit()
        logger.info(f"QR check-in successful for room booking {booking_id}")
        return True, "Check-in successful.", booking

    @staticmethod
    def validate_event_checkin(token: str, booking_id: int) -> Tuple[bool, str, Optional[EventBooking]]:
        """
        Validate a QR check-in attempt for an event booking.

        Args:
            token: Token scanned from QR code
            booking_id: EBookID from QR payload

        Returns:
            (success, message, booking_or_None)
        """
        booking = db.session.query(EventBooking).filter_by(EBookID=booking_id).first()

        if not booking:
            return False, "Booking not found.", None

        if booking.qr_token != token:
            logger.warning(f"Invalid QR token attempt for event booking {booking_id}")
            return False, "Invalid QR code.", None

        if booking.EbookStatus == "Completed":
            return False, "This booking has already been checked in.", None

        if booking.EbookStatus == "Cancelled":
            return False, "This booking has been cancelled.", None

        now = datetime.now()
        window_open = booking.Start - \
            __import__('datetime').timedelta(minutes=QR_EARLY_CHECKIN_MINUTES)

        if now < window_open:
            return False, f"Check-in opens {QR_EARLY_CHECKIN_MINUTES} minutes before your booking.", None

        if now > booking.End:
            return False, "Booking window has expired.", None

        booking.EbookStatus = "Ongoing"
        db.session.commit()
        logger.info(f"QR check-in successful for event booking {booking_id}")
        return True, "Check-in successful.", booking
