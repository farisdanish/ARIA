from datetime import datetime, timedelta, date
from unittest.mock import patch
from website.models.base import db
from website.models.room import RoomList, RoomBooking, EventBooking
from website.models.feedback import Feedback
from website.models.report import Report
from website.services.scheduler import BookingScheduler


def test_feedback_page_and_submission(client, make_student, make_admin, login_as):
    # Unauthenticated redirect
    res = client.get('/feedback')
    assert res.status_code == 302
    assert '/login' in res.headers['Location']

    # Login student
    student = make_student('S1001')
    admin = make_admin('A1001')
    room = RoomList(AdminID=admin.AdminID, RoomName='Lab 101', RoomType='Lab', RoomStatus='Available')
    db.session.add(room)
    db.session.commit()

    login_as(student)

    # GET feedback
    res = client.get('/feedback')
    assert res.status_code == 200
    assert b'Feedback' in res.data

    # POST feedback
    res = client.post('/feedback', data={
        'FeedbackContent': 'The room was well equipped.',
        'feedbackType': 'Room',
        'rbook': '1'
    }, follow_redirects=True)
    assert res.status_code == 200

    # Verify Feedback saved in DB
    fb = Feedback.query.filter_by(StudID='S1001').first()
    assert fb is not None
    assert 'The room was well equipped.' in fb.Content


def test_view_feedback_admin(client, make_student, make_admin, login_as):
    student = make_student('S2002')
    admin = make_admin('A2002')

    # Non-admin forbidden / redirected
    login_as(student)
    res = client.get('/ViewFeedback')
    assert res.status_code == 302

    # Admin access
    login_as(admin)
    res = client.get('/ViewFeedback')
    assert res.status_code == 200
    assert b'User Feedback' in res.data


def test_profile_and_settings_routes(client, make_student, login_as):
    student = make_student('S3003')
    login_as(student)

    # Profile
    res = client.get('/profile')
    assert res.status_code == 200
    assert b'S3003' in res.data

    # Settings redirects to profile
    res = client.get('/settings')
    assert res.status_code == 302
    assert '/profile' in res.headers['Location']


def test_get_report_admin(client, make_admin, login_as):
    admin = make_admin('A4004')
    room = RoomList(AdminID=admin.AdminID, RoomName='Conference Room A', RoomType='Conference', RoomStatus='Available')
    db.session.add(room)
    db.session.commit()

    # Create completed booking in August 2026
    start_dt = datetime(2026, 8, 10, 10, 0, 0)
    end_dt = datetime(2026, 8, 10, 12, 0, 0)
    booking = RoomBooking(
        RoomID=room.RoomID,
        StudID='S1001',
        Start=start_dt,
        End=end_dt,
        Purpose='Meeting',
        RBookStatus='Completed'
    )
    db.session.add(booking)
    db.session.commit()

    login_as(admin)

    # Trigger report compilation
    res = client.post('/getReport', data={'reportmonth': '2026-08'}, follow_redirects=True)
    assert res.status_code == 200

    # Verify Report in DB
    rep = Report.query.filter_by(RoomID=room.RoomID).first()
    assert rep is not None
    assert rep.totalNumBookings == 1
    assert rep.totalHoursBooked == 2.0
    assert rep.MonthYear == date(2026, 8, 1)


def test_scheduler_deduplication(app, make_admin):
    with app.app_context():
        admin = make_admin('A5005')
        room = RoomList(AdminID=admin.AdminID, RoomName='Lab 202', RoomType='Lab', RoomStatus='Available')
        db.session.add(room)
        db.session.commit()

        now = datetime.now()
        upcoming_start = now + timedelta(minutes=5)
        upcoming_end = now + timedelta(minutes=65)

        booking = RoomBooking(
            RoomID=room.RoomID,
            StudID='S1001',
            Start=upcoming_start,
            End=upcoming_end,
            Purpose='Study',
            RBookStatus='Upcoming'
        )
        db.session.add(booking)
        db.session.commit()

        BookingScheduler._notified_bookings.clear()

        with patch('website.services.redis_service.RedisService.publish_watch_room') as mock_publish:
            # 1st run: Should publish notification
            BookingScheduler._check_upcoming_bookings()
            assert mock_publish.call_count == 1

            # 2nd run: Should be suppressed by deduplication
            BookingScheduler._check_upcoming_bookings()
            assert mock_publish.call_count == 1
