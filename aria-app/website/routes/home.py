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
from ..services.face_service import FaceService
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


@home.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    """User feedback submission page."""
    if current_user.is_Admin():
        return redirect(url_for('home.view_feedback'))

    from ..models.feedback import Feedback

    if request.method == 'POST':
        content = request.form.get('FeedbackContent', '').strip()
        feedback_type = request.form.get('feedbackType', '').strip()
        rbook_id = request.form.get('rbook')
        ebook_id = request.form.get('ebook')

        if not content:
            flash('Please provide your feedback comments.', category='error')
            return redirect(url_for('home.feedback'))

        booking_ref = f"{feedback_type} #{rbook_id if feedback_type == 'Room' else ebook_id}" if feedback_type else "General Feedback"
        subject = f"Booking Experience: {booking_ref}"

        new_fb = Feedback(
            StudID=current_user.StudID if current_user.is_Student() else None,
            StaffID=current_user.StaffID if current_user.is_Staff() else None,
            Subject=subject,
            Content=content,
            PostDate=datetime.utcnow()
        )
        db.session.add(new_fb)
        db.session.commit()
        flash('Thank you! Your feedback has been submitted successfully.', category='success')
        return redirect(url_for('home.index'))

    # GET request
    rooms = RoomService.get_all()
    if current_user.is_Student():
        rbook_list = RoomBooking.query.filter_by(StudID=current_user.StudID).all()
        ebook_list = EventBooking.query.filter_by(StudID=current_user.StudID).all()
        stud_list = db.session.query(Student).all()
        staff_list = []
    else:
        rbook_list = RoomBooking.query.filter_by(StaffID=current_user.StaffID).all()
        ebook_list = EventBooking.query.filter_by(StaffID=current_user.StaffID).all()
        stud_list = []
        staff_list = db.session.query(Staff).all()

    announcements = AnnouncementService.get_all()

    return render_ui_template(
        "Feedback.html",
        ui_group="student" if current_user.is_Student() else "staff",
        user=current_user,
        roomlist=rooms,
        student=stud_list,
        staff=staff_list,
        roombookings=rbook_list,
        eventbookings=ebook_list,
        announcements=announcements,
        is_Student=current_user.is_Student(),
        is_Staff=current_user.is_Staff(),
        is_Admin=False
    )


@home.route('/ViewFeedback', methods=['GET'])
@login_required
def view_feedback():
    """Admin view for user feedback submissions."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))

    from ..models.feedback import Feedback
    feedbacks = db.session.query(Feedback).order_by(Feedback.PostDate.desc()).all()
    rooms = RoomService.get_all()
    students = {s.StudID: s.StudName for s in db.session.query(Student).all()}
    staff_members = {s.StaffID: s.StaffName for s in db.session.query(Staff).all()}

    return render_ui_template(
        "ViewFeedback.html",
        ui_group="admin",
        user=current_user,
        feedbacks=feedbacks,
        students=students,
        staff_members=staff_members,
        roomlist=rooms,
        is_Student=False,
        is_Staff=False,
        is_Admin=True
    )


@home.route('/profile', methods=['GET'])
@login_required
def profile():
    """User profile details view."""
    reg_face_exist = False
    if current_user.is_Student():
        reg_face_exist = db.session.query(RegisteredFace).filter_by(StudID=current_user.StudID).first() is not None
    elif current_user.is_Staff():
        reg_face_exist = db.session.query(RegisteredFace).filter_by(StaffID=current_user.StaffID).first() is not None

    return render_ui_template(
        "profile.html",
        ui_group="admin" if current_user.is_Admin() else ("student" if current_user.is_Student() else "staff"),
        user=current_user,
        regFaceExist=reg_face_exist,
        is_Student=current_user.is_Student(),
        is_Staff=current_user.is_Staff(),
        is_Admin=current_user.is_Admin()
    )


@home.route('/settings', methods=['GET'])
@login_required
def settings():
    """User settings redirect."""
    return redirect(url_for('home.profile'))


@home.route('/getReport', methods=['POST'])
@login_required
def get_report():
    """Generate or update monthly room usage statistics report (admin only)."""
    if not current_user.is_Admin():
        flash('Only admin allowed on that URL.', category='error')
        return redirect(url_for('home.index'))

    month_year_str = request.form.get('reportmonth', '').strip()
    if not month_year_str:
        flash('Please select a valid month and year.', category='error')
        return redirect(url_for('home.manage_reports'))

    try:
        month_date = datetime.strptime(month_year_str, '%Y-%m').date()
    except ValueError:
        flash('Invalid month/year format.', category='error')
        return redirect(url_for('home.manage_reports'))

    from ..models.report import Report
    rooms = RoomService.get_all()
    rbook_list = RoomBooking.query.all()
    ebook_list = EventBooking.query.all()

    month_name = month_date.strftime('%B')
    title = f"{month_date.year}-{month_name}"

    reports_created = 0
    reports_updated = 0

    for rm in rooms:
        total_bookings = 0
        total_seconds = 0.0

        for r in rbook_list:
            if r.RoomID == rm.RoomID and r.Start:
                r_ym = f"{r.Start.year:04d}-{r.Start.month:02d}"
                if r_ym == month_year_str and r.RBookStatus != 'Cancelled':
                    total_bookings += 1
                    if r.End and r.Start:
                        delta = r.End - r.Start
                        total_seconds += max(0.0, delta.total_seconds())

        for e in ebook_list:
            if e.RoomID == rm.RoomID and e.Start:
                e_ym = f"{e.Start.year:04d}-{e.Start.month:02d}"
                if e_ym == month_year_str and e.EbookStatus != 'Cancelled':
                    total_bookings += 1
                    if e.End and e.Start:
                        delta = e.End - e.Start
                        total_seconds += max(0.0, delta.total_seconds())

        total_hours = round(total_seconds / 3600.0, 2)

        existing_report = db.session.query(Report).filter(
            Report.RoomID == rm.RoomID,
            Report.MonthYear == month_date
        ).first()

        if existing_report:
            existing_report.totalNumBookings = total_bookings
            existing_report.totalHoursBooked = total_hours
            existing_report.ReportTitle = title
            reports_updated += 1
        else:
            new_rep = Report(
                ReportTitle=title,
                RoomID=rm.RoomID,
                totalNumBookings=total_bookings,
                totalHoursBooked=total_hours,
                MonthYear=month_date
            )
            db.session.add(new_rep)
            reports_created += 1

    db.session.commit()
    flash(f"Report compiled for {month_name} {month_date.year}! ({reports_created} generated, {reports_updated} updated)", category="success")
    return redirect(url_for('home.manage_reports'))
