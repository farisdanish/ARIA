from datetime import datetime, timedelta

from website.models.base import db
from website.models.room import RoomBooking
from website.services.qr_service import QRService


def test_api_routes_require_authentication(client):
    response = client.get('/api/studentlist')
    assert response.status_code == 401

    response = client.get('/api/rbooklists')
    assert response.status_code == 401

    response = client.post('/api/accesslogs', json={'RoomID': 1, 'Status': 1})
    assert response.status_code == 401

    response = client.get('/api/faces')
    assert response.status_code == 401

    response = client.post('/api/recognize_frame', json={'image': 'bad'})
    assert response.status_code == 401


def test_admin_can_access_admin_api(client, make_admin, login_as):
    admin = make_admin()
    login_as(admin)

    response = client.get('/api/studentlist')
    assert response.status_code == 200


def test_device_token_can_access_device_api_but_not_admin_api(client, auth_headers):
    response = client.get('/api/roomlist', headers=auth_headers)
    assert response.status_code == 200

    response = client.get('/api/studentlist', headers=auth_headers)
    assert response.status_code == 401


def test_pending_user_cannot_log_in(client, make_student):
    make_student(stud_id='pending1', status='Pending')

    response = client.post('/login', data={
        'userID': 'pending1',
        'userPassword': 'password123',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Invalid user ID or password' in response.get_data(as_text=True)


def test_approved_user_can_log_in(client, make_student):
    make_student(stud_id='approved1', status='Approved')

    response = client.post('/login', data={
        'userID': 'approved1',
        'userPassword': 'password123',
    })

    assert response.status_code == 302
    assert '/homeStud' in response.headers['Location']


def test_user_cannot_cancel_other_users_booking(client, make_student, make_room, login_as):
    attacker = make_student(stud_id='stud_a')
    victim = make_student(stud_id='stud_b')
    room = make_room()
    booking = RoomBooking(
        RoomID=room.RoomID,
        StudID=victim.StudID,
        Start=datetime.utcnow(),
        End=datetime.utcnow() + timedelta(hours=1),
        Purpose='Victim booking',
        RBookStatus='Upcoming',
        CheckInMethod='QR',
    )
    db.session.add(booking)
    db.session.commit()

    login_as(attacker)
    response = client.post(f'/cancel-booking/room/{booking.RBookID}')

    assert response.status_code == 403
    db.session.refresh(booking)
    assert booking.RBookStatus == 'Upcoming'


def test_destructive_routes_reject_get(client):
    assert client.get('/deleteRoom/1/').status_code == 405
    assert client.get('/deleteRBook/1/').status_code == 405
    assert client.get('/deleteEBook/1/').status_code == 405
    assert client.get('/train_data').status_code == 405


def test_qr_checkin_is_owner_bound_and_one_time_use(client, make_student, make_room, login_as):
    owner = make_student(stud_id='qr_owner')
    other = make_student(stud_id='qr_other')
    room = make_room(room_name='QR Room')
    booking = RoomBooking(
        RoomID=room.RoomID,
        StudID=owner.StudID,
        Start=datetime.utcnow() - timedelta(minutes=5),
        End=datetime.utcnow() + timedelta(minutes=30),
        Purpose='QR booking',
        RBookStatus='Upcoming',
        CheckInMethod='QR',
    )
    db.session.add(booking)
    db.session.commit()
    token = QRService.attach_token_to_room_booking(booking)

    login_as(other)
    response = client.get(f'/checkin/qr?token={token}&booking_id={booking.RBookID}&type=room')
    assert response.status_code == 403
    db.session.refresh(booking)
    assert booking.qr_token_redeemed_at is None

    login_as(owner)
    response = client.get(f'/checkin/qr?token={token}&booking_id={booking.RBookID}&type=room')
    assert response.status_code == 200
    assert 'Check-in successful' in response.get_data(as_text=True)

    response = client.get(f'/checkin/qr?token={token}&booking_id={booking.RBookID}&type=room')
    assert response.status_code == 200
    assert 'already been used' in response.get_data(as_text=True)
