-- migration: add qr_token to booking tables
-- Run this once against your ariadb database.
-- When you add Alembic later, convert these into a proper migration file.

ALTER TABLE roombookings
    ADD COLUMN qr_token VARCHAR(64) NULL UNIQUE;

ALTER TABLE eventbookings
    ADD COLUMN qr_token VARCHAR(64) NULL UNIQUE;


-- ============================================================
-- bookings.py  (add these routes into your existing blueprint)
-- ============================================================

# Place this at the top of bookings.py alongside existing imports
from ..services.qr_service import QRService
from ..services.mail_service import MailService  # for emailing the QR
from flask import request, jsonify, render_template
from flask_login import login_required, current_user

# ------------------------------------------------------------
# 1. Hook QR token generation into room booking creation.
#    Find your existing room booking POST route and add the
#    two QRService lines after BookingService.create_room_booking().
# ------------------------------------------------------------

# EXISTING (your current code, roughly):
#   booking = BookingService.create_room_booking(...)
#
# UPDATED — add directly after:
#   if booking:
#       QRService.attach_token_to_room_booking(booking)
#       qr_image = QRService.generate_qr_image_base64(
#           token=booking.qr_token,
#           booking_id=booking.RBookID,
#           booking_type="room"
#       )
#       MailService.send_qr_checkin_email(current_user.email, qr_image, booking)

# Same pattern applies for event bookings using attach_token_to_event_booking().

# ------------------------------------------------------------
# 2. New check-in route — add to bookings.py blueprint
# ------------------------------------------------------------

@bookings_bp.route("/checkin/qr", methods=["GET", "POST"])
@login_required
def qr_checkin():
    """
    Handle QR code check-in for both room and event bookings.

    GET  — rendered when user scans QR on their phone
    POST — called by the Pi simulator scanner service
    """
    token = request.args.get("token") or request.form.get("token")
    booking_id = request.args.get("booking_id") or request.form.get("booking_id")
    booking_type = request.args.get("type", "room")

    if not token or not booking_id:
        if request.is_json:
            return jsonify({"success": False, "message": "Missing token or booking ID."}), 400
        return render_template("checkin_qr.html", success=False,
                               message="Invalid QR code.")

    try:
        booking_id = int(booking_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid booking ID."}), 400

    if booking_type == "event":
        success, message, booking = QRService.validate_event_checkin(token, booking_id)
    else:
        success, message, booking = QRService.validate_room_checkin(token, booking_id)

    if request.is_json or request.method == "POST":
        # Pi simulator / API consumer path
        return jsonify({
            "success": success,
            "message": message,
            "booking_id": booking_id,
            "booking_type": booking_type,
            "unlock_door": success,   # Pi reads this to trigger GPIO
        }), 200 if success else 400

    # Browser / phone scan path
    return render_template("checkin_qr.html", success=success, message=message)
