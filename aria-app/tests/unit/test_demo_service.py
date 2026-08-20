"""Unit tests for demo_service and DemoVisitLog."""
from website.models.base import db
from website.models.demo_visit import DemoVisitLog
from website.models.guest import GuestUser
from website.services.demo_service import (
    create_demo_session,
    log_demo_activity,
    cleanup_demo_guest,
)


class TestDemoVisitLog:
    """Tests for demo visitor audit logging."""

    def test_log_demo_activity_persists(self, client):
        """Verify log_demo_activity creates a row in DemoVisitLog."""
        log = log_demo_activity(
            guest_id='guest-test1234',
            action='session_started',
            message='VISITOR guest-test1234 started demo session (IP: 127.0.0.1)',
            ip_address='127.0.0.1',
        )
        assert log.id is not None
        assert log.GuestID == 'guest-test1234'
        assert log.Action == 'session_started'
        assert 'VISITOR guest-test1234' in log.Message
        assert log.IPAddress == '127.0.0.1'

        found = db.session.query(DemoVisitLog).filter_by(GuestID='guest-test1234').first()
        assert found is not None
        assert found.Action == 'session_started'

    def test_create_demo_session_logs_activity(self, client):
        """create_demo_session should log the session_started event."""
        app = client.application
        guest, token = create_demo_session(app, ip_address='10.0.0.1')
        assert guest is not None
        assert token is not None

        log = db.session.query(DemoVisitLog).filter_by(GuestID=guest.GuestID, Action='session_started').first()
        assert log is not None
        assert '10.0.0.1' in log.Message


class TestManageDemoLogsRoute:
    """Tests for the /ManageDemoLogs admin route."""

    def test_admin_can_view_demo_logs(self, client, login_as, make_admin):
        """Admin should be able to view /ManageDemoLogs."""
        admin = make_admin(admin_id='admin-demo-test')
        login_as(admin)

        log_demo_activity(
            guest_id='guest-viewtest',
            action='recognition_tested',
            message='VISITOR guest-viewtest tested recognition: MATCHED (confidence: 95.6%)',
            ip_address='192.168.1.50',
        )

        response = client.get('/ManageDemoLogs')
        assert response.status_code == 200
        assert b'Public Demo Visitor Logs' in response.data
        assert b'guest-viewtest' in response.data

    def test_student_cannot_view_demo_logs(self, client, login_as, make_student):
        """Non-admin users should be redirected from /ManageDemoLogs."""
        student = make_student(stud_id='stud-demo-test')
        login_as(student)

        response = client.get('/ManageDemoLogs', follow_redirects=False)
        assert response.status_code == 302
