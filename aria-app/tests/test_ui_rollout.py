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
    assert "UMS Library Room Booking System" in text
