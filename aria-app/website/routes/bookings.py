"""Booking management routes."""
from flask import Blueprint, request, flash, redirect, url_for, jsonify, render_template, make_response
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime
from ..services.booking_service import BookingService
from ..services.room_service import RoomService
from ..services.mail_service import MailService
from ..services.qr_service import QRService
from ..schemas.booking_schema import RoomBookingCreateSchema, EventBookingCreateSchema
from ..utils.validation import validate_form_data
from ..models.user import Student, Staff
from ..models.room import RoomBooking, EventBooking
from ..models.base import db
from flask import current_app
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

bookings = Blueprint('bookings', __name__)


def format_booking_times(bookings_list):
    """Format booking times for template display."""
    time_list = []
    for booking in bookings_list:
        time_dict = {
            'ID': booking.RBookID if hasattr(booking, 'RBookID') else booking.EBookID,
            'StartDate': booking.Start.date().strftime("%Y-%m-%d"),
            'StartTime': booking.Start.time().strftime("%H:%M:%S"),
            'EndDate': booking.End.date().strftime("%Y-%m-%d"),
            'EndTime': booking.End.time().strftime("%H:%M:%S")
        }
        time_list.append(time_dict)
    return time_list


def _redirect_after_booking_update():
    """Return role-aware redirect target after booking updates."""
    if current_user.is_Admin():
        return redirect(url_for('home.admin'))
    return redirect(url_for('bookings.my_bookings'))


@bookings.route('/cancel-booking/<string:booking_type>/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_type, booking_id):
    """Cancel a booking via HTMX."""
    try:
        if booking_type == 'room':
            booking = db.session.query(RoomBooking).filter_by(RBookID=booking_id).first()
            if booking:
                booking.RBookStatus = 'Canceled'
                db.session.commit()
        else:
            booking = db.session.query(EventBooking).filter_by(EBookID=booking_id).first()
            if booking:
                booking.EbookStatus = 'Canceled'
                db.session.commit()
        
        # Determine if we should trigger other updates
        response_headers = {'HX-Trigger': 'bookingUpdated'}
        
        # Return the updated table
        if current_user.is_Student():
            room_bookings = BookingService.get_user_room_bookings(current_user.StudID, is_student=True)
            event_bookings = BookingService.get_user_event_bookings(current_user.StudID, is_student=True)
            student = db.session.query(Student).all()
            staff = []
            is_student = True
        else:
            room_bookings = BookingService.get_user_room_bookings(current_user.StaffID, is_student=False)
            event_bookings = BookingService.get_user_event_bookings(current_user.StaffID, is_student=False)
            student = []
            staff = db.session.query(Staff).all()
            is_student = False

        rooms = RoomService.get_all()
        
        if booking_type == 'room':
            template = 'partials/_room_bookings_table.html'
            html = render_template(template, 
                                   roombookings=room_bookings,
                                   roomlist=rooms,
                                   student=student,
                                   staff=staff,
                                   is_Student=is_student)
        else:
            template = 'partials/_event_bookings_table.html'
            html = render_template(template, 
                                   eventbookings=event_bookings,
                                   roomlist=rooms,
                                   student=student,
                                   staff=staff,
                                   is_Student=is_student)
        
        res = make_response(html)
        for k, v in response_headers.items():
            res.headers[k] = v
        return res

    except Exception as e:
        logger.error(f"Error canceling booking: {str(e)}")
        return "Error canceling booking", 500


@bookings.route('/filter-bookings', methods=['GET'])
@login_required
def filter_bookings():
    """Filter bookings via HTMX."""
    status = request.args.get('status', 'all')
    booking_type = request.args.get('type', 'room')
    
    if current_user.is_Student():
        room_bookings = BookingService.get_user_room_bookings(current_user.StudID, is_student=True)
        event_bookings = BookingService.get_user_event_bookings(current_user.StudID, is_student=True)
        student = db.session.query(Student).all()
        staff = []
        is_student = True
    else:
        room_bookings = BookingService.get_user_room_bookings(current_user.StaffID, is_student=False)
        event_bookings = BookingService.get_user_event_bookings(current_user.StaffID, is_student=False)
        student = []
        staff = db.session.query(Staff).all()
        is_student = False

    rooms = RoomService.get_all()
    
    if booking_type == 'room':
        if status != 'all':
            room_bookings = [b for b in room_bookings if b.RBookStatus == status]
        return render_template('partials/_room_bookings_table.html', 
                               roombookings=room_bookings, 
                               roomlist=rooms,
                               student=student,
                               staff=staff,
                               is_Student=is_student)
    else:
        if status != 'all':
            event_bookings = [b for b in event_bookings if b.EbookStatus == status]
        return render_template('partials/_event_bookings_table.html', 
                               eventbookings=event_bookings,
                               roomlist=rooms,
                               student=student,
                               staff=staff,
                               is_Student=is_student)


@bookings.route('/MyBookings', methods=['GET', 'POST'])
@login_required
def my_bookings():
    """View user's bookings."""
    if current_user.is_Admin():
        flash('Admin not allowed on this URL', category='error')
        return redirect(url_for('home.admin'))
    
    curr_date = datetime.now().strftime("%d-%m-%Y")
    
    # Get user bookings
    if current_user.is_Student():
        room_bookings = BookingService.get_user_room_bookings(current_user.StudID, is_student=True)
        event_bookings = BookingService.get_user_event_bookings(current_user.StudID, is_student=True)
        template = "studBookings.html"
        is_student = True
    else:  # Staff
        room_bookings = BookingService.get_user_room_bookings(current_user.StaffID, is_student=False)
        event_bookings = BookingService.get_user_event_bookings(current_user.StaffID, is_student=False)
        template = "staffBookings.html"
        is_student = False
    
    room_time_list = format_booking_times(room_bookings)
    event_time_list = format_booking_times(event_bookings)
    
    rooms = RoomService.get_all()
    students = db.session.query(Student).all() if is_student else []
    staff_list = db.session.query(Staff).all() if not is_student else []
    
    from ..services.announcement_service import AnnouncementService
    announcements = AnnouncementService.get_all()
    
    return render_template(
        template,
        user=current_user,
        roomlist=rooms,
        student=students if is_student else [],
        staff=staff_list if not is_student else [],
        roombookings=room_bookings,
        eventbookings=event_bookings,
        currentDate=curr_date,
        rBookTimeList=room_time_list,
        eBookTimeList=event_time_list,
        is_Student=is_student,
        is_Staff=not is_student,
        is_Admin=False,
        announcements=announcements
    )


@bookings.route('/AddRBook', methods=['GET', 'POST'])
@login_required
def add_room_booking():
    """Add a room booking."""
    if current_user.is_Admin():
        flash('Admin not allowed on this URL', category='error')
        return redirect(url_for('home.admin'))
    
    if request.method == 'POST':
        try:
            # Parse form data
            room_id = int(request.form.get('roomSelect'))
            stud_id = current_user.StudID if current_user.is_Student() else None
            staff_id = current_user.StaffID if current_user.is_Staff() else None
            purpose = request.form.get('RBookPurpose')
            checkin_method = request.form.get('checkinMethod', 'QR')
            
            # Parse dates and times
            start_date = datetime.strptime(request.form.get('rbookstart'), '%Y-%m-%d').date()
            start_time = datetime.strptime(request.form.get('rbooktimeStart'), '%H:%M:%S').time()
            start = datetime.combine(start_date, start_time)
            
            end_date = datetime.strptime(request.form.get('rbookend'), '%Y-%m-%d').date()
            end_time = datetime.strptime(request.form.get('rbooktimeEnd'), '%H:%M:%S').time()
            end = datetime.combine(end_date, end_time)
            
            # Validate booking
            is_valid, error_msg = BookingService.validate_booking_duration(start, end, max_hours=2)
            if not is_valid:
                if request.headers.get('HX-Request'):
                    return render_template('partials/_toast.html', message=error_msg, type='error')
                flash(error_msg, category='error')
                return redirect(url_for('bookings.my_bookings'))
            
            # Create booking
            booking = BookingService.create_room_booking(
                room_id=room_id,
                stud_id=stud_id,
                staff_id=staff_id,
                start=start,
                end=end,
                purpose=purpose,
                checkin_method=checkin_method
            )
            
            if booking:
                # Generate and attach QR token
                QRService.attach_token_to_room_booking(booking)
                
                # Generate QR image
                qr_image = QRService.generate_qr_image_base64(
                    token=booking.qr_token,
                    booking_id=booking.RBookID,
                    booking_type="room"
                )
                
                # Send confirmation email with QR
                room = RoomService.get_by_id(room_id)
                if room:
                    mail_service = MailService(current_app.extensions.get('mail'))
                    email = current_user.StudEmail if current_user.is_Student() else current_user.StaffEmail
                    mail_service.send_qr_checkin_email(email, qr_image, booking)
                
                success_msg = 'Room Booking was Added! Check your email for the QR code.'
                if request.headers.get('HX-Request'):
                    response = render_template('partials/_booking_success.html')
                    res = make_response(response)
                    res.headers['HX-Trigger'] = 'bookingUpdated'
                    return res
                flash(success_msg, category='success')
            else:
                error_msg = 'Room already occupied for that time or booking failed.'
                if request.headers.get('HX-Request'):
                    return render_template('partials/_toast.html', message=error_msg, type='error')
                flash(error_msg, category='error')
                
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', category='error')
        except Exception as e:
            logger.error(f"Error creating room booking: {str(e)}")
            flash('Failed to create booking. Please try again.', category='error')
    
    return redirect(url_for('bookings.my_bookings'))


@bookings.route('/AddEBook', methods=['GET', 'POST'])
@login_required
def add_event_booking():
    """Add an event booking."""
    if current_user.is_Admin():
        flash('Admin not allowed on this URL', category='error')
        return redirect(url_for('home.admin'))
    
    if request.method == 'POST':
        try:
            # Parse form data
            room_id = int(request.form.get('roomSelect'))
            stud_id = current_user.StudID if current_user.is_Student() else None
            staff_id = current_user.StaffID if current_user.is_Staff() else None
            purpose = request.form.get('EBookPurpose')
            add_detail = request.form.get('EBookAddDetails')
            checkin_method = request.form.get('checkinMethod', 'QR')
            
            # Parse dates and times
            start_date = datetime.strptime(request.form.get('ebookstart'), '%Y-%m-%d').date()
            start_time = datetime.strptime(request.form.get('ebooktimeStart'), '%H:%M:%S').time()
            start = datetime.combine(start_date, start_time)
            
            end_date = datetime.strptime(request.form.get('ebookend'), '%Y-%m-%d').date()
            end_time = datetime.strptime(request.form.get('ebooktimeEnd'), '%H:%M:%S').time()
            end = datetime.combine(end_date, end_time)
            
            # Create booking
            booking = BookingService.create_event_booking(
                room_id=room_id,
                stud_id=stud_id,
                staff_id=staff_id,
                start=start,
                end=end,
                purpose=purpose,
                add_detail=add_detail,
                checkin_method=checkin_method
            )
            
            if booking:
                # Generate and attach QR token
                QRService.attach_token_to_event_booking(booking)
                
                # Generate QR image
                qr_image = QRService.generate_qr_image_base64(
                    token=booking.qr_token,
                    booking_id=booking.EBookID,
                    booking_type="event"
                )
                
                # Send confirmation email with QR
                room = RoomService.get_by_id(room_id)
                if room:
                    mail_service = MailService(current_app.extensions.get('mail'))
                    email = current_user.StudEmail if current_user.is_Student() else current_user.StaffEmail
                    mail_service.send_qr_checkin_email(email, qr_image, booking)
                
                success_msg = 'Event Booking was Added! Check your email for the QR code.'
                if request.headers.get('HX-Request'):
                    response = render_template('partials/_booking_success.html')
                    res = make_response(response)
                    res.headers['HX-Trigger'] = 'bookingUpdated'
                    return res
                flash(success_msg, category='success')
            else:
                error_msg = 'Room already occupied for that time or booking failed.'
                if request.headers.get('HX-Request'):
                    return render_template('partials/_toast.html', message=error_msg, type='error')
                flash(error_msg, category='error')
                
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', category='error')
        except Exception as e:
            logger.error(f"Error creating event booking: {str(e)}")
            flash('Failed to create booking. Please try again.', category='error')
    
    return redirect(url_for('bookings.my_bookings'))


@bookings.route('/updateRBook/', methods=['POST'])
@login_required
def update_room_booking():
    """Update room booking details from legacy modal forms."""
    try:
        booking = db.session.query(RoomBooking).filter_by(RBookID=request.form.get('RBookID')).first()
        if not booking:
            flash('Room booking not found.', category='error')
            return _redirect_after_booking_update()

        start = datetime.combine(
            datetime.strptime(request.form.get('rbookstart'), '%Y-%m-%d').date(),
            datetime.strptime(request.form.get('rbooktimeStart'), '%H:%M:%S').time()
        )
        end = datetime.combine(
            datetime.strptime(request.form.get('rbookend'), '%Y-%m-%d').date(),
            datetime.strptime(request.form.get('rbooktimeEnd'), '%H:%M:%S').time()
        )
        room_id = int(request.form.get('roomSelect'))
        purpose = request.form.get('RBookPurpose', '').strip()
        status = request.form.get('rBookStatusType') or booking.RBookStatus

        is_valid, error_msg = BookingService.validate_booking_duration(start, end, max_hours=2)
        if not is_valid:
            flash(error_msg, category='error')
            return _redirect_after_booking_update()

        conflicting = db.session.query(RoomBooking).filter(
            and_(
                RoomBooking.RoomID == room_id,
                RoomBooking.Start <= end,
                RoomBooking.End >= start,
                RoomBooking.RBookID != booking.RBookID,
            )
        ).first()
        if conflicting:
            flash('Room already occupied for that time.', category='error')
            return _redirect_after_booking_update()

        if not purpose:
            flash('Please provide booking purpose.', category='error')
            return _redirect_after_booking_update()

        booking.Start = start
        booking.End = end
        booking.RoomID = room_id
        booking.Purpose = purpose
        booking.RBookStatus = status
        db.session.commit()
        flash('Room booking updated successfully.', category='success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update room booking: {str(e)}")
        flash('Failed to update room booking.', category='error')

    return _redirect_after_booking_update()


@bookings.route('/updateEBook/', methods=['POST'])
@login_required
def update_event_booking():
    """Update event booking details from legacy modal forms."""
    try:
        booking = db.session.query(EventBooking).filter_by(EBookID=request.form.get('EBookID')).first()
        if not booking:
            flash('Event booking not found.', category='error')
            return _redirect_after_booking_update()

        start = datetime.combine(
            datetime.strptime(request.form.get('ebookstart'), '%Y-%m-%d').date(),
            datetime.strptime(request.form.get('ebooktimeStart'), '%H:%M:%S').time()
        )
        end = datetime.combine(
            datetime.strptime(request.form.get('ebookend'), '%Y-%m-%d').date(),
            datetime.strptime(request.form.get('ebooktimeEnd'), '%H:%M:%S').time()
        )
        room_id = int(request.form.get('roomSelect'))
        purpose = request.form.get('EBookPurpose', '').strip()
        add_detail = request.form.get('EBookAddDetail')
        status = request.form.get('eBookStatusType') or booking.EbookStatus

        conflicting = db.session.query(EventBooking).filter(
            and_(
                EventBooking.RoomID == room_id,
                EventBooking.Start <= end,
                EventBooking.End >= start,
                EventBooking.EBookID != booking.EBookID,
            )
        ).first()
        if conflicting:
            flash('Room already occupied for that time.', category='error')
            return _redirect_after_booking_update()

        if end < start:
            flash('Booking end time must be after start time.', category='error')
            return _redirect_after_booking_update()

        if not purpose:
            flash('Please provide booking purpose.', category='error')
            return _redirect_after_booking_update()

        booking.Start = start
        booking.End = end
        booking.RoomID = room_id
        booking.Purpose = purpose
        booking.AddDetail = add_detail
        booking.EbookStatus = status
        db.session.commit()
        flash('Event booking updated successfully.', category='success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update event booking: {str(e)}")
        flash('Failed to update event booking.', category='error')

    return _redirect_after_booking_update()


@bookings.route('/deleteRBook/<int:booking_id>/', methods=['GET', 'POST'])
@login_required
def delete_room_booking(booking_id):
    """Delete a room booking (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))
    
    success = BookingService.delete_room_booking(booking_id)
    if success:
        flash('Room booking deleted successfully!', category='success')
    else:
        flash('Failed to delete booking.', category='error')
    
    return redirect(url_for('bookings.manage_room_bookings'))


@bookings.route('/deleteEBook/<int:booking_id>/', methods=['GET', 'POST'])
@login_required
def delete_event_booking(booking_id):
    """Delete an event booking (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))
    
    success = BookingService.delete_event_booking(booking_id)
    if success:
        flash('Event booking deleted successfully!', category='success')
    else:
        flash('Failed to delete booking.', category='error')
    
    return redirect(url_for('bookings.manage_event_bookings'))


@bookings.route('/ManageRBookings', methods=['GET', 'POST'])
@login_required
def manage_room_bookings():
    """Manage all room bookings (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))
    
    room_bookings = BookingService.get_all_room_bookings()
    room_time_list = format_booking_times(room_bookings)
    
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    
    return render_template(
        "manageRBooking.html",
        user=current_user,
        roomlist=rooms,
        staff=staff_list,
        student=students,
        roombookings=room_bookings,
        rBookTimeList=room_time_list,
        is_Student=False,
        is_Staff=False,
        is_Admin=True
    )


@bookings.route('/ManageEBookings', methods=['GET', 'POST'])
@login_required
def manage_event_bookings():
    """Manage all event bookings (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))
    
    event_bookings = BookingService.get_all_event_bookings()
    event_time_list = format_booking_times(event_bookings)
    
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    
    return render_template(
        "manageEBooking.html",
        user=current_user,
        roomlist=rooms,
        staff=staff_list,
        student=students,
        eventbookings=event_bookings,
        eBookTimeList=event_time_list,
        is_Student=False,
        is_Staff=False,
        is_Admin=True
    )

@bookings.route("/checkin/qr", methods=["GET", "POST"])
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
        return render_template("checkin_qr.html", success=False, message="Invalid QR code.")

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
        if success and booking:
            # Publish event to Redis for Pi simulator to unlock door
            from ..services.redis_service import RedisService
            RedisService.publish_token_validated(
                room_id=booking.RoomID,
                booking_id=booking_id,
                booking_type=booking_type
            )

        return jsonify({
            "success": success,
            "message": message,
            "booking_id": booking_id,
            "booking_type": booking_type,
            "unlock_door": success,   # Still return true for legacy support
        }), 200 if success else 400

    # Browser / phone scan path
    if success and booking:
        # Also publish here for phone scans
        from ..services.redis_service import RedisService
        RedisService.publish_token_validated(
            room_id=booking.RoomID,
            booking_id=booking_id,
            booking_type=booking_type
        )
    return render_template("checkin_qr.html", success=success, message=message)
