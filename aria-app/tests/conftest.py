import os
import pytest
from website.app import create_app
from website.models.base import db
from website.models.user import Admin, Student, Staff
from website.models.room import RoomList
from website.services.auth_service import AuthService

# Skip background threads (Redis scheduler/subscriber) during testing
os.environ['FLASK_SKIP_BACKGROUND_THREADS'] = '1'
os.environ['DEVICE_API_TOKEN'] = 'test-device-token'
os.environ['SECRET_KEY'] = 'test-secret-key'

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers():
    return {'Authorization': 'Bearer test-device-token'}


@pytest.fixture
def make_admin(app):
    def _make(admin_id='admin1', password='password123'):
        admin = Admin(
            AdminID=admin_id,
            AdminPassword=AuthService.hash_password(password).decode('utf-8'),
            AdminName='Admin User',
            AdminEmail=f'{admin_id}@example.com',
            AdminContactNum='0123456789',
        )
        db.session.add(admin)
        db.session.commit()
        return admin
    return _make


@pytest.fixture
def make_student(app):
    def _make(stud_id='stud1', password='password123', status='Approved'):
        student = Student(
            StudID=stud_id,
            StudPassword=AuthService.hash_password(password).decode('utf-8'),
            StudName=f'Student {stud_id}',
            StudEmail=f'{stud_id}@example.com',
            StudContactNum='0123456789',
            AccountStatus=status,
        )
        db.session.add(student)
        db.session.commit()
        return student
    return _make


@pytest.fixture
def make_staff(app):
    def _make(staff_id='staff1', password='password123', status='Approved'):
        staff = Staff(
            StaffID=staff_id,
            StaffPassword=AuthService.hash_password(password).decode('utf-8'),
            StaffName=f'Staff {staff_id}',
            StaffEmail=f'{staff_id}@example.com',
            StaffContactNum='0123456789',
            AccountStatus=status,
        )
        db.session.add(staff)
        db.session.commit()
        return staff
    return _make


@pytest.fixture
def make_room(app):
    def _make(room_name='Room A', room_type='Normal Room'):
        room = RoomList(
            RoomName=room_name,
            RoomInfo='Test room',
            RoomType=room_type,
            RoomStatus='Available',
        )
        db.session.add(room)
        db.session.commit()
        return room
    return _make


@pytest.fixture
def login_as(client):
    def _login(user):
        from flask import g
        if hasattr(g, '_login_user'):
            delattr(g, '_login_user')
        with client.session_transaction() as session:
            session['_user_id'] = user.get_id()
            session['_fresh'] = True
    return _login
