"""Home page routes."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from ..models.user import Student, Staff, Admin
from ..models.announcement import Announcement
from ..models.room import RoomList, RoomBooking, EventBooking
from ..models.face import RegisteredFace
from ..models.base import db
from ..services.announcement_service import AnnouncementService
from ..services.room_service import RoomService
import logging

logger = logging.getLogger(__name__)

home = Blueprint('home', __name__)


@home.route('/')
def index():
    """Home page."""
    announcements = AnnouncementService.get_all()
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    room_bookings = db.session.query(RoomBooking).all()
    event_bookings = db.session.query(EventBooking).all()
    
    if current_user.is_authenticated:
        if current_user.is_Staff():
            return redirect(url_for('home.staff'))
        elif current_user.is_Admin():
            return redirect(url_for('home.admin'))
        elif current_user.is_Student():
            return redirect(url_for('home.student'))
    
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


@home.route('/homeStud')
@login_required
def student():
    """Student home page."""
    if not current_user.is_Student():
        from flask import flash
        flash('Only students allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('home.staff'))
        elif current_user.is_Admin():
            return redirect(url_for('home.admin'))
        return redirect(url_for('home.index'))
    
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


@home.route('/homeStaff')
@login_required
def staff():
    """Staff home page."""
    if not current_user.is_Staff():
        from flask import flash
        flash('Only staff members allowed on that URL.', category='error')
        if current_user.is_Student():
            return redirect(url_for('home.student'))
        elif current_user.is_Admin():
            return redirect(url_for('home.admin'))
        return redirect(url_for('home.index'))
    
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


@home.route('/homeAdmin')
@login_required
def admin():
    """Admin home page."""
    if not current_user.is_Admin():
        from flask import flash
        flash('Only admin allowed on that URL.', category='error')
        if current_user.is_Staff():
            return redirect(url_for('home.staff'))
        elif current_user.is_Student():
            return redirect(url_for('home.student'))
        return redirect(url_for('home.index'))
    
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

