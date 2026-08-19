"""Integration tests for Pi-facing API routes (routes/api/routes.py).

All tests use the existing conftest.py fixtures (client, auth_headers,
make_student, make_staff, make_admin, make_room, login_as).

Coverage:
- /api/roomlist         — device auth boundary (valid / missing / wrong)
- /api/rbooklists       — device auth boundary
- /api/studentlist      — admin-only; device token must be rejected
- /api/accesslogs GET   — admin-only
- /api/accesslogs POST  — device auth, valid/missing fields
- /api/recognize_frame  — session or device auth, missing key, invalid payload,
                          no-face path, match-above-threshold, below-threshold
"""
import base64
import numpy as np
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from website.models.base import db
from website.models.room import RoomBooking


# ---------------------------------------------------------------------------
# /api/roomlist
# ---------------------------------------------------------------------------

class TestRoomListAPI:
    def test_requires_auth(self, client):
        response = client.get("/api/roomlist")
        assert response.status_code == 401

    def test_valid_device_token_returns_200(self, client, auth_headers):
        response = client.get("/api/roomlist", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)

    def test_wrong_token_returns_401(self, client):
        response = client.get("/api/roomlist", headers={"Authorization": "Bearer bad-token"})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# /api/rbooklists
# ---------------------------------------------------------------------------

class TestRBookListAPI:
    def test_requires_auth(self, client):
        assert client.get("/api/rbooklists").status_code == 401

    def test_valid_device_token_returns_list(self, client, auth_headers, app, make_room, make_student):
        with app.app_context():
            room = make_room()
            make_student()
            booking = RoomBooking(
                RoomID=room.RoomID,
                StudID="stud1",
                Start=datetime.utcnow(),
                End=datetime.utcnow() + timedelta(hours=1),
                Purpose="API test",
                RBookStatus="Upcoming",
                CheckInMethod="QR",
            )
            db.session.add(booking)
            db.session.commit()

        response = client.get("/api/rbooklists", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1


# ---------------------------------------------------------------------------
# /api/studentlist  (admin-only)
# ---------------------------------------------------------------------------

class TestStudentListAPI:
    def test_device_token_rejected(self, client, auth_headers):
        """Device token must NOT grant access to admin-only endpoints."""
        assert client.get("/api/studentlist", headers=auth_headers).status_code == 401

    def test_unauthenticated_rejected(self, client):
        assert client.get("/api/studentlist").status_code == 401

    def test_admin_session_granted(self, client, make_admin, login_as):
        admin = make_admin()
        login_as(admin)
        response = client.get("/api/studentlist")
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)


# ---------------------------------------------------------------------------
# /api/accesslogs GET
# ---------------------------------------------------------------------------

class TestAccessLogsGetAPI:
    def test_device_token_rejected_on_get(self, client, auth_headers):
        assert client.get("/api/accesslogs", headers=auth_headers).status_code == 401

    def test_admin_can_read_access_logs(self, client, make_admin, login_as):
        admin = make_admin()
        login_as(admin)
        response = client.get("/api/accesslogs")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# /api/accesslogs POST
# ---------------------------------------------------------------------------

class TestAccessLogsPostAPI:
    def _valid_payload(self, room_id):
        return {"RoomID": room_id, "Status": 1}

    def test_no_auth_returns_401(self, client, make_room):
        room = make_room()
        response = client.post(
            "/api/accesslogs",
            json=self._valid_payload(room.RoomID),
        )
        assert response.status_code == 401

    def test_device_token_creates_log_entry(self, client, auth_headers, make_room):
        room = make_room()
        with patch("website.routes.api.routes.MailService") as mock_mail_cls:
            mock_mail_cls.return_value.send_access_notification = MagicMock()
            response = client.post(
                "/api/accesslogs",
                json=self._valid_payload(room.RoomID),
                headers=auth_headers,
            )
        assert response.status_code == 201
        data = response.get_json()
        assert data["RoomID"] == room.RoomID
        assert data["Status"] == 1

    def test_missing_room_id_returns_400(self, client, auth_headers):
        response = client.post(
            "/api/accesslogs",
            json={"Status": 1},  # missing RoomID
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_missing_status_returns_400(self, client, auth_headers, make_room):
        room = make_room()
        response = client.post(
            "/api/accesslogs",
            json={"RoomID": room.RoomID},  # missing Status
            headers=auth_headers,
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# /api/recognize_frame
# ---------------------------------------------------------------------------

def _encode_fake_frame():
    """Return a data-URI string containing a minimal base64-encoded PNG-like blob.

    The actual bytes don't matter — we mock cv2.imdecode in all paths so the
    real codec is never invoked.
    """
    fake_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    b64 = base64.b64encode(fake_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


class TestRecognizeFrameAPI:
    """
    All tests in this class patch the module-level `face_service` singleton
    inside `website.routes.api.routes` to avoid any real ML model loading.
    cv2.imdecode is also patched to return a fake numpy frame.
    """

    _patch_imdecode = "website.routes.api.routes.cv2.imdecode"
    _patch_fs = "website.routes.api.routes.face_service"

    # Fake numpy frame returned by the mocked imdecode
    FAKE_FRAME = np.zeros((480, 640, 3), dtype=np.uint8)
    FAKE_FACE = np.zeros((50, 50, 3), dtype=np.uint8)

    def test_requires_auth(self, client):
        response = client.post("/api/recognize_frame", json={"image": _encode_fake_frame()})
        assert response.status_code == 401

    def test_missing_image_key_returns_400(self, client, auth_headers):
        response = client.post("/api/recognize_frame", json={}, headers=auth_headers)
        assert response.status_code == 400

    def test_invalid_base64_returns_500(self, client, auth_headers):
        """A data URI with no comma separator causes an IndexError in the route.

        The route catches all exceptions generically and returns 500.  This
        test documents the current behavior — if the route is ever hardened
        to return 400 for malformed input, this assertion should be updated
        to 400 accordingly.
        """
        response = client.post(
            "/api/recognize_frame",
            json={"image": "not-a-valid-data-uri"},
            headers=auth_headers,
        )
        assert response.status_code == 500

    def test_no_face_detected_returns_searching(self, client, auth_headers):
        with patch(self._patch_imdecode, return_value=self.FAKE_FRAME):
            with patch(self._patch_fs) as mock_fs:
                mock_fs.load_trained_model.return_value = True
                mock_fs.get_face.return_value = (None, 0, 0, 0, 0)

                response = client.post(
                    "/api/recognize_frame",
                    json={"image": _encode_fake_frame()},
                    headers=auth_headers,
                )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "searching"

    def test_face_matched_above_threshold(self, client, auth_headers, make_student):
        """High-confidence match should return status=success and access=granted."""
        make_student(stud_id="known_stud")

        with patch(self._patch_imdecode, return_value=self.FAKE_FRAME):
            with patch(self._patch_fs) as mock_fs:
                mock_fs.load_trained_model.return_value = True
                mock_fs.get_face.return_value = (self.FAKE_FACE, 10, 60, 20, 70)
                mock_fs.recognize_face.return_value = ("known_stud", 0.95)

                response = client.post(
                    "/api/recognize_frame",
                    json={"image": _encode_fake_frame()},
                    headers=auth_headers,
                )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["access"] == "granted"
        assert data["confidence"] == pytest.approx(0.95, abs=1e-5)

    def test_face_below_threshold_returns_denied(self, client, auth_headers):
        """Low-confidence recognition must return access=denied."""
        with patch(self._patch_imdecode, return_value=self.FAKE_FRAME):
            with patch(self._patch_fs) as mock_fs:
                mock_fs.load_trained_model.return_value = True
                mock_fs.get_face.return_value = (self.FAKE_FACE, 10, 60, 20, 70)
                mock_fs.recognize_face.return_value = (None, 0.4)

                response = client.post(
                    "/api/recognize_frame",
                    json={"image": _encode_fake_frame()},
                    headers=auth_headers,
                )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["access"] == "denied"

    def test_invalid_image_bytes_returns_400(self, client, auth_headers):
        """imdecode returning None (corrupt payload) → 400."""
        with patch(self._patch_imdecode, return_value=None):
            response = client.post(
                "/api/recognize_frame",
                json={"image": _encode_fake_frame()},
                headers=auth_headers,
            )
        assert response.status_code == 400
