"""Playwright E2E configuration and fixtures."""
import os
import tempfile
import threading
import time
import socket
import pytest
from flask import Flask
from werkzeug.serving import make_server
from website.app import create_app
from website.models.base import db
from website.models.user import Student, Staff, Admin
from website.models.room import RoomList


def get_free_port() -> int:
    """Find a free local port for live test server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class ServerThread(threading.Thread):
    def __init__(self, app: Flask, port: int):
        super().__init__(daemon=True)
        self.server = make_server('127.0.0.1', port, app)
        self.port = port

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


@pytest.fixture(scope="session")
def live_server():
    """Start live test Flask server for Playwright browser."""
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    os.environ["TESTING"] = "true"
    os.environ["FLASK_SKIP_BACKGROUND_THREADS"] = "1"
    os.environ["AUTO_CREATE_DB"] = "1"
    os.environ["DATABASE_URL"] = f"sqlite:///{temp_db.name}"

    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{temp_db.name}"
    app.config['SERVER_NAME'] = None

    with app.app_context():
        db.create_all()

    port = get_free_port()
    server_thread = ServerThread(app, port)
    server_thread.start()
    time.sleep(0.5)

    base_url = f"http://127.0.0.1:{port}"
    yield {"app": app, "base_url": base_url, "port": port}

    server_thread.shutdown()
    if os.path.exists(temp_db.name):
        try:
            os.unlink(temp_db.name)
        except OSError:
            pass


@pytest.fixture
def session_injector(live_server):
    """Factory fixture to authenticate Playwright context via signed session cookies."""
    app = live_server["app"]

    def _inject(context, user_id: str, role: str = "student"):
        with app.app_context():
            # Ensure user exists
            if role == "student":
                user = db.session.query(Student).filter_by(StudID=user_id).first()
                if not user:
                    user = Student(
                        StudID=user_id,
                        StudName=f"E2E {user_id}",
                        StudEmail=f"{user_id}@e2e.test",
                        StudPassword="password",
                        StudContactNum="0123456789",
                        AccountStatus="Approved"
                    )
                    db.session.add(user)
                    db.session.commit()
            elif role == "staff":
                user = db.session.query(Staff).filter_by(StaffID=user_id).first()
                if not user:
                    user = Staff(
                        StaffID=user_id,
                        StaffName=f"E2E {user_id}",
                        StaffEmail=f"{user_id}@e2e.test",
                        StaffPassword="password",
                        StaffContactNum="0123456789",
                        AccountStatus="Approved"
                    )
                    db.session.add(user)
                    db.session.commit()
            elif role == "admin":
                user = db.session.query(Admin).filter_by(AdminID=user_id).first()
                if not user:
                    user = Admin(
                        AdminID=user_id,
                        AdminName=f"E2E Admin {user_id}",
                        AdminEmail=f"{user_id}@e2e.test",
                        AdminPassword="password",
                        AdminContactNum="0123456789"
                    )
                    db.session.add(user)
                    db.session.commit()

            # Seed a sample room if none exists
            if not db.session.query(RoomList).first():
                room = RoomList(
                    RoomName="E2E Study Room",
                    RoomType="Normal Room",
                    RoomStatus="Available",
                    RoomInfo="Room for E2E testing"
                )
                db.session.add(room)
                db.session.commit()

            # Sign session cookie
            signer = app.session_interface.get_signing_serializer(app)
            cookie_val = signer.dumps({'_user_id': user.get_id(), '_fresh': True})

            context.add_cookies([{
                'name': 'session',
                'value': cookie_val,
                'domain': '127.0.0.1',
                'path': '/',
                'httpOnly': True
            }])

    return _inject
