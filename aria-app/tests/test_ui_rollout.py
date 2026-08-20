from website.utils.ui import should_use_aria_ui, aria_template_name


def test_aria_template_name_maps_html_suffix():
    assert aria_template_name("home.html") == "home.aria.html"


def test_ui_flag_disabled_blocks_aria(app):
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "all"
    with app.app_context():
        assert should_use_aria_ui("public") is False
        assert should_use_aria_ui("dashboards") is False


def test_ui_phase_gates_groups(app):
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "dashboards"
    with app.app_context():
        assert should_use_aria_ui("public") is True
        assert should_use_aria_ui("dashboards") is True
        assert should_use_aria_ui("admin") is False


def test_home_uses_aria_template_when_enabled(app):
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "public"
    client = app.test_client()

    response = client.get("/")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    # home.aria.html + base_aria branding (footer string lives on auth templates only)
    assert "ARIA is an intelligent room booking" in text


def test_home_falls_back_to_legacy_when_disabled(app):
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "all"
    client = app.test_client()

    response = client.get("/")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Smart Access for the Modern Campus" in text
    assert 'data-bs-toggle="offcanvas"' in text


def test_student_dashboard_uses_aria_template_when_enabled(app, client, make_student, login_as):
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "dashboards"
    student = make_student(stud_id="rollout_stud")
    login_as(student)

    response = client.get("/homeStud")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Simplify Your Campus Life" in text
    assert "@click=\"$dispatch('open-rbook-modal')\"" in text


def test_student_dashboard_falls_back_to_legacy_when_disabled(app, client, make_student, login_as):
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "dashboards"
    student = make_student(stud_id="rollout_stud_leg")
    login_as(student)

    response = client.get("/homeStud")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-bs-target=\"#modaladdRBook\"" in text


def test_staff_dashboard_uses_aria_template_when_enabled(app, client, make_staff, login_as):
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "dashboards"
    staff_user = make_staff(staff_id="rollout_staff")
    login_as(staff_user)

    response = client.get("/homeStaff")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Manage Campus Resources" in text
    assert "@click=\"$dispatch('open-rbook-modal')\"" in text


def test_staff_dashboard_falls_back_to_legacy_when_disabled(app, client, make_staff, login_as):
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "dashboards"
    staff_user = make_staff(staff_id="rollout_staff_leg")
    login_as(staff_user)

    response = client.get("/homeStaff")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-bs-target=\"#modaladdRBook\"" in text


def test_bookings_page_uses_aria_template_when_enabled(app, client, make_student, login_as):
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "dashboards"
    student = make_student(stud_id="rollout_book_stud")
    login_as(student)

    response = client.get("/MyBookings")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Booking History" in text
    assert "rbookTablePart" in text


def test_bookings_page_falls_back_to_legacy_when_disabled(app, client, make_student, login_as):
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "dashboards"
    student = make_student(stud_id="rollout_book_leg")
    login_as(student)

    response = client.get("/MyBookings")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-bs-target=\"#modaladdRBook\"" in text


def test_admin_home_uses_aria_template_when_enabled(app, client, make_admin, login_as):
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "admin"
    admin_user = make_admin(admin_id="rollout_admin")
    login_as(admin_user)

    response = client.get("/homeAdmin")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Campus Operations Control" in text
    assert "Live Operational Schedule" in text


def test_admin_home_falls_back_to_legacy_when_disabled(app, client, make_admin, login_as):
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "admin"
    admin_user = make_admin(admin_id="rollout_admin_leg")
    login_as(admin_user)

    response = client.get("/homeAdmin")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Command Center" in text
    assert "aria-hero" in text


def test_admin_rooms_uses_aria_template_when_enabled(app, client, make_admin, login_as):
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "admin"
    admin_user = make_admin(admin_id="rollout_admin_rm")
    login_as(admin_user)

    response = client.get("/ManageRooms")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Room Inventory" in text
    assert "openAddModal" in text


def test_admin_rooms_falls_back_to_legacy_when_disabled(app, client, make_admin, login_as):
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "admin"
    admin_user = make_admin(admin_id="rollout_admin_rm_leg")
    login_as(admin_user)

    response = client.get("/ManageRooms")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-bs-target=\"#insert_room_modal\"" in text
