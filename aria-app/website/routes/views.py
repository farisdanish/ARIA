"""Main view routes."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime
from ..models.user import Student, Staff, Admin
from ..models.announcement import Announcement
from ..models.room import RoomList, RoomBooking, EventBooking
from ..models.face import RegisteredFace
from ..models.base import db
from ..services.announcement_service import AnnouncementService
from ..services.room_service import RoomService
from ..services.booking_service import BookingService
import logging

logger = logging.getLogger(__name__)

views = Blueprint('views', __name__)


@views.route('/')
def home():
    """Home page."""
    announcements = AnnouncementService.get_all()
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    room_bookings = db.session.query(RoomBooking).all()
    event_bookings = db.session.query(EventBooking).all()
    
    if current_user.is_authenticated:
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Admin():
            return redirect(url_for('views.homeAdmin'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))
    
    return render_template(
        "home.html",
        user=current_user,
        roomlist=rooms,
        staff=staff_list,
        student=students,
        roombookings=room_bookings,
        eventbookings=event_bookings,
        announcements=announcements
    )


@views.route('/homeStud')
@login_required
def homeStud():
    """Student home page."""
    if not current_user.is_Student():
        flash('Only students allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Admin():
            return redirect(url_for('views.homeAdmin'))
        return redirect(url_for('views.home'))
    
    curr_date = datetime.now().strftime("%d-%m-%Y")
    announcements = AnnouncementService.get_all()
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    room_bookings = db.session.query(RoomBooking).all()
    event_bookings = db.session.query(EventBooking).all()
    
    reg_face = db.session.query(RegisteredFace).filter_by(StudID=current_user.StudID).first()
    
    return render_template(
        "homeStud.html",
        user=current_user,
        roomlist=rooms,
        staff=staff_list,
        student=students,
        roombookings=room_bookings,
        eventbookings=event_bookings,
        currentDate=curr_date,
        regFaceExist=reg_face,
        announcements=announcements,
        is_Student=True,
        is_Staff=False,
        is_Admin=False
    )


@views.route('/homeStaff')
@login_required
def homeStaff():
    """Staff home page."""
    if not current_user.is_Staff():
        flash('Only staff members allowed on that URL.', category='error')
        if current_user.is_Student():
            return redirect(url_for('views.homeStud'))
        elif current_user.is_Admin():
            return redirect(url_for('views.homeAdmin'))
        return redirect(url_for('views.home'))
    
    curr_date = datetime.now().strftime("%d-%m-%Y")
    announcements = AnnouncementService.get_all()
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    room_bookings = db.session.query(RoomBooking).all()
    event_bookings = db.session.query(EventBooking).all()
    
    reg_face = db.session.query(RegisteredFace).filter_by(StaffID=current_user.StaffID).first()
    
    return render_template(
        "homeStaff.html",
        user=current_user,
        roomlist=rooms,
        staff=staff_list,
        student=students,
        roombookings=room_bookings,
        eventbookings=event_bookings,
        currentDate=curr_date,
        regFaceExist=reg_face,
        announcements=announcements,
        is_Student=False,
        is_Staff=True,
        is_Admin=False
    )


@views.route('/homeAdmin')
@login_required
def homeAdmin():
    """Admin home page."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('views.homeStaff'))
        elif current_user.is_Student():
            return redirect(url_for('views.homeStud'))
        return redirect(url_for('views.home'))
    
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    room_bookings = db.session.query(RoomBooking).all()
    event_bookings = db.session.query(EventBooking).all()
    
    return render_template(
        "homeAdmin.html",
        user=current_user,
        roomlist=rooms,
        staff=staff_list,
        student=students,
        roombookings=room_bookings,
        eventbookings=event_bookings,
        is_Student=False,
        is_Staff=False,
        is_Admin=True
    )


# Note: Additional routes for announcements, rooms, bookings, etc. 
# should be added here or split into separate blueprint modules
# This is a basic structure - the full views.py would need to be
# refactored into smaller modules for better maintainability

