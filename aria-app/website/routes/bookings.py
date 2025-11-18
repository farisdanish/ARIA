"""Booking management routes."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime
from ..services.booking_service import BookingService
from ..services.room_service import RoomService
from ..services.mail_service import MailService
from ..schemas.booking_schema import RoomBookingCreateSchema, EventBookingCreateSchema
from ..utils.validation import validate_form_data
from ..models.user import Student, Staff
from ..models.room import RoomBooking, EventBooking
from ..models.base import db
from flask import current_app
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
                flash(error_msg, category='error')
                return redirect(url_for('bookings.my_bookings'))
            
            # Create booking
            booking = BookingService.create_room_booking(
                room_id=room_id,
                stud_id=stud_id,
                staff_id=staff_id,
                start=start,
                end=end,
                purpose=purpose
            )
            
            if booking:
                # Send confirmation email
                room = RoomService.get_by_id(room_id)
                if room:
                    mail_service = MailService(current_app.extensions.get('mail'))
                    email = current_user.StudEmail if current_user.is_Student() else current_user.StaffEmail
                    mail_service.send_booking_confirmation(
                        email,
                        room.RoomName,
                        start_date.strftime('%Y-%m-%d')
                    )
                
                flash('Room Booking was Added!', category='success')
            else:
                flash('Room already occupied for that time or booking failed.', category='error')
                
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
                add_detail=add_detail
            )
            
            if booking:
                # Send confirmation email
                room = RoomService.get_by_id(room_id)
                if room:
                    mail_service = MailService(current_app.extensions.get('mail'))
                    email = current_user.StudEmail if current_user.is_Student() else current_user.StaffEmail
                    mail_service.send_booking_confirmation(
                        email,
                        room.RoomName,
                        start_date.strftime('%Y-%m-%d')
                    )
                
                flash('Event Booking was Added!', category='success')
            else:
                flash('Room already occupied for that time or booking failed.', category='error')
                
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', category='error')
        except Exception as e:
            logger.error(f"Error creating event booking: {str(e)}")
            flash('Failed to create booking. Please try again.', category='error')
    
    return redirect(url_for('bookings.my_bookings'))


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
    
    return redirect(url_for('bookings.manage'))


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
    
    return redirect(url_for('bookings.manage'))


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
        "manageRBookings.html",
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
        "manageEBookings.html",
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

