"""Unit tests for AuthService.

Tests cover:
- Password hashing and verification (bcrypt round-trip)
- find_user across Student, Staff, Admin tables
- authenticate_user: correct / wrong password, Pending / Rejected status blocking
- create_student / create_staff: status defaults and password storage
"""
from website.models.user import Student, Staff, Admin
from website.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_password_produces_bcrypt_hash(self, app):
        with app.app_context():
            hashed = AuthService.hash_password("secret")
            assert isinstance(hashed, bytes)
            assert hashed.startswith(b"$2b$")

    def test_check_password_correct(self, app):
        with app.app_context():
            hashed = AuthService.hash_password("mysecret")
            assert AuthService.check_password("mysecret", hashed.decode("utf-8")) is True

    def test_check_password_wrong(self, app):
        with app.app_context():
            hashed = AuthService.hash_password("correct")
            assert AuthService.check_password("wrong", hashed.decode("utf-8")) is False

    def test_check_password_invalid_hash_does_not_raise(self, app):
        with app.app_context():
            # Malformed hash must return False, not raise
            result = AuthService.check_password("password", "not-a-valid-hash")
            assert result is False


# ---------------------------------------------------------------------------
# find_user
# ---------------------------------------------------------------------------

class TestFindUser:
    def test_find_user_returns_student(self, app, make_student):
        with app.app_context():
            make_student(stud_id="s001")
            user = AuthService.find_user("s001")
            assert isinstance(user, Student)
            assert user.StudID == "s001"

    def test_find_user_returns_staff(self, app, make_staff):
        with app.app_context():
            make_staff(staff_id="staff001")
            user = AuthService.find_user("staff001")
            assert isinstance(user, Staff)
            assert user.StaffID == "staff001"

    def test_find_user_returns_admin(self, app, make_admin):
        with app.app_context():
            make_admin(admin_id="admin001")
            user = AuthService.find_user("admin001")
            assert isinstance(user, Admin)
            assert user.AdminID == "admin001"

    def test_find_user_returns_none_for_unknown(self, app):
        with app.app_context():
            assert AuthService.find_user("nobody") is None


# ---------------------------------------------------------------------------
# authenticate_user
# ---------------------------------------------------------------------------

class TestAuthenticateUser:
    def test_authenticate_student_correct_password(self, app, make_student):
        with app.app_context():
            make_student(stud_id="sa01", password="pass123", status="Approved")
            user = AuthService.authenticate_user("sa01", "pass123")
            assert user is not None
            assert isinstance(user, Student)

    def test_authenticate_student_wrong_password(self, app, make_student):
        with app.app_context():
            make_student(stud_id="sa02", password="correct", status="Approved")
            user = AuthService.authenticate_user("sa02", "wrong")
            assert user is None

    def test_authenticate_pending_user_blocked(self, app, make_student):
        with app.app_context():
            make_student(stud_id="pend01", password="pass123", status="Pending")
            user = AuthService.authenticate_user("pend01", "pass123")
            assert user is None

    def test_authenticate_rejected_user_blocked(self, app, make_student):
        with app.app_context():
            make_student(stud_id="rej01", password="pass123", status="Rejected")
            user = AuthService.authenticate_user("rej01", "pass123")
            assert user is None

    def test_authenticate_nonexistent_user_returns_none(self, app):
        with app.app_context():
            assert AuthService.authenticate_user("ghost", "anything") is None

    def test_authenticate_staff_correct_password(self, app, make_staff):
        with app.app_context():
            make_staff(staff_id="sf01", password="staffpass", status="Approved")
            user = AuthService.authenticate_user("sf01", "staffpass")
            assert user is not None
            assert isinstance(user, Staff)

    def test_authenticate_admin_correct_password(self, app, make_admin):
        with app.app_context():
            make_admin(admin_id="adm01", password="adminpass")
            user = AuthService.authenticate_user("adm01", "adminpass")
            assert user is not None
            assert isinstance(user, Admin)


# ---------------------------------------------------------------------------
# Account creation
# ---------------------------------------------------------------------------

class TestAccountCreation:
    def test_create_student_sets_pending_status(self, app):
        with app.app_context():
            student = AuthService.create_student(
                stud_id="new_s01",
                stud_name="New Student",
                stud_email="new@example.com",
                stud_contact="0123456789",
                password="pass",
            )
            assert student.AccountStatus == "Pending"

    def test_create_student_hashes_password(self, app):
        with app.app_context():
            student = AuthService.create_student(
                stud_id="new_s02",
                stud_name="Another Student",
                stud_email="another@example.com",
                stud_contact="0123456789",
                password="plaintext",
            )
            # Stored password must not be the plaintext value
            assert student.StudPassword != "plaintext"
            # But it must verify correctly
            assert AuthService.check_password("plaintext", student.StudPassword)

    def test_create_staff_sets_pending_status(self, app):
        with app.app_context():
            staff = AuthService.create_staff(
                staff_id="new_sf01",
                staff_name="New Staff",
                staff_email="newstaff@example.com",
                staff_contact="0123456789",
                password="pass",
            )
            assert staff.AccountStatus == "Pending"

    def test_create_staff_hashes_password(self, app):
        with app.app_context():
            staff = AuthService.create_staff(
                staff_id="new_sf02",
                staff_name="Another Staff",
                staff_email="anotherstaff@example.com",
                staff_contact="0123456789",
                password="plaintext",
            )
            assert staff.StaffPassword != "plaintext"
            assert AuthService.check_password("plaintext", staff.StaffPassword)
