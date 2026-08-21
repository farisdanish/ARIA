"""Home page routes."""
from flask import Blueprint, redirect, url_for, render_template, request, flash
from flask_login import login_required, current_user
from datetime import datetime
from ..models.user import Student, Staff, Admin
from ..models.announcement import Announcement
from ..models.room import RoomList, RoomBooking, EventBooking
from ..models.face import RegisteredFace
from ..models.base import db
from ..services.announcement_service import AnnouncementService
from ..services.room_service import RoomService
from ..utils.ui import render_ui_template
import logging

logger = logging.getLogger(__name__)

home = Blueprint('home', __name__)


@home.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        if current_user.is_Staff():
            return redirect(url_for('home.staff'))
        elif current_user.is_Admin():
            return redirect(url_for('home.admin'))
        elif current_user.is_Student():
            return redirect(url_for('home.student'))

    announcements = AnnouncementService.get_all()
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    room_bookings = db.session.query(RoomBooking).all()
    event_bookings = db.session.query(EventBooking).all()
    
    return render_ui_template(
        "home.html",
        ui_group="public",
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
    
    return render_ui_template(
        "homeStud.html",
        ui_group="dashboards",
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
    
    return render_ui_template(
        "homeStaff.html",
        ui_group="dashboards",
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
    
    from ..models.feedback import Feedback
    from ..models.announcement import Announcement
    feedbacks = db.session.query(Feedback).all()
    announcements = db.session.query(Announcement).all()
    
    return render_ui_template(
        "homeAdmin.html",
        ui_group="admin",
        user=current_user,
        roomlist=rooms,
        staff=staff_list,
        student=students,
        roombookings=room_bookings,
        eventbookings=event_bookings,
        feedbacks=feedbacks,
        announcements=announcements,
        is_Student=False,
        is_Staff=False,
        is_Admin=True
    )


@home.route('/toast-partial')
def toast_partial():
    """Returns a toast partial for HTMX."""
    message = request.args.get('message', '')
    type = request.args.get('type', 'info')
    return render_template('partials/_toast.html', message=message, type=type)


@home.route('/api/ui/pulse')
@login_required
def ui_pulse():
    """Lightweight endpoint for periodic UI state synchronization."""
    from flask import make_response
    import json
    
    triggers = {}
    
    # 1. Check for upcoming bookings or status changes
    # For now, we signal a refresh of the room discovery sidebar
    triggers['refreshRoomStatus'] = True
    
    # 2. Admin specific pulses (Feedback, reports)
    if current_user.is_Admin():
        from ..models.feedback import Feedback
        feedback_count = db.session.query(Feedback).count()
        triggers['updateFeedbackCount'] = feedback_count
        
    response = make_response("", 204) # No content
    response.headers['HX-Trigger'] = json.dumps(triggers)
    return response


@home.route('/ViewRoomAccessLog', methods=['GET'])
@login_required
def view_access_log():
    """View room access audit logs (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))

    from ..models.access import RoomAccessLog
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    logs = db.session.query(RoomAccessLog).order_by(RoomAccessLog.Timestamp.desc()).all()

    return render_ui_template(
        "AccessLogView.html",
        ui_group="admin",
        user=current_user,
        roomlist=rooms,
        staff=staff_list,
        student=students,
        roomaccesslog=logs,
        is_Student=False,
        is_Staff=False,
        is_Admin=True
    )


@home.route('/deleteRAccessLog/<int:rma_id>/', methods=['POST'])
@login_required
def delete_access_log(rma_id):
    """Delete a room access log entry (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))

    from ..models.access import RoomAccessLog
    rma = db.session.query(RoomAccessLog).filter_by(rmaID=rma_id).first()
    if rma:
        db.session.delete(rma)
        db.session.commit()
        flash("Room access log record has been deleted", category="success")
    else:
        flash("Record not found", category="error")

    return redirect(url_for('home.view_access_log'))


@home.route('/ManageReport', methods=['GET'])
@login_required
def manage_reports():
    """View usage reports (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))

    from ..models.report import Report
    rooms = RoomService.get_all()
    students = db.session.query(Student).all()
    staff_list = db.session.query(Staff).all()
    reports = db.session.query(Report).all()

    return render_ui_template(
        "ManageReport.html",
        ui_group="admin",
        user=current_user,
        roomlist=rooms,
        staff=staff_list,
        student=students,
        report=reports,
        is_Student=False,
        is_Staff=False,
        is_Admin=True
    )


@home.route('/deleteReport/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    """Delete a report (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))

    from ..models.report import Report
    rep = db.session.query(Report).filter_by(ReportID=report_id).first()
    if rep:
        db.session.delete(rep)
        db.session.commit()
        flash("Report deleted successfully", category="success")
    else:
        flash("Report not found", category="error")

    return redirect(url_for('home.manage_reports'))
