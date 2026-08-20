"""Playwright E2E Smoke Tests for ARIA UI Modernization."""
import pytest
from playwright.sync_api import Page, expect


def check_no_console_errors(page: Page):
    """Attach listener to catch JS uncaught exceptions on page."""
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    return errors


@pytest.mark.e2e
def test_public_home_flag_on(live_server, page: Page):
    """Public home renders .aria.html without console errors when ARIA_UI_ENABLED=True."""
    app = live_server["app"]
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "public"

    errors = check_no_console_errors(page)
    page.goto(live_server["base_url"] + "/")

    # Modern Tailwind UI Assertions
    expect(page.locator("h1")).to_contain_text("Smart Access for the Modern Campus")
    expect(page.locator("text=Next-Gen Campus Technology")).to_be_visible()
    expect(page.locator("text=Try Face ID Demo")).to_be_visible()
    assert len(errors) == 0, f"Unexpected JS errors: {errors}"


@pytest.mark.e2e
def test_public_home_flag_off_rollback(live_server, page: Page):
    """Public home rolls back to legacy Bootstrap template when ARIA_UI_ENABLED=False."""
    app = live_server["app"]
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "all"

    page.goto(live_server["base_url"] + "/")

    # Legacy Bootstrap assertions
    expect(page.locator(".aria-hero")).to_be_visible()
    expect(page.locator("h1")).to_contain_text("Smart Access for the Modern Campus")


@pytest.mark.e2e
def test_login_page_flag_on(live_server, page: Page):
    """Login page renders Tailwind auth card."""
    app = live_server["app"]
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "public"

    errors = check_no_console_errors(page)
    page.goto(live_server["base_url"] + "/login")

    expect(page.locator("h2")).to_contain_text("Welcome Back")
    expect(page.locator("text=User ID / Matric Number")).to_be_visible()
    assert len(errors) == 0, f"Unexpected JS errors: {errors}"


@pytest.mark.e2e
def test_student_dashboard_flag_on(live_server, context, page: Page, session_injector):
    """Student dashboard renders Tailwind layout, stat cards, and calendar."""
    app = live_server["app"]
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "dashboards"

    session_injector(context, user_id="e2e_stud_1", role="student")

    errors = check_no_console_errors(page)
    page.goto(live_server["base_url"] + "/homeStud")

    expect(page.locator("h1")).to_contain_text("Simplify Your Campus Life")
    expect(page.get_by_text("Upcoming Bookings", exact=True)).to_be_visible()
    expect(page.locator("#calendar")).to_be_visible()
    assert len(errors) == 0, f"Unexpected JS errors: {errors}"


@pytest.mark.e2e
def test_student_dashboard_flag_off_rollback(live_server, context, page: Page, session_injector):
    """Student dashboard rolls back to legacy Bootstrap view when flag is off."""
    app = live_server["app"]
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "dashboards"

    session_injector(context, user_id="e2e_stud_2", role="student")

    page.goto(live_server["base_url"] + "/homeStud")

    expect(page.locator("#calendar")).to_be_visible()


@pytest.mark.e2e
def test_staff_dashboard_flag_on(live_server, context, page: Page, session_injector):
    """Staff dashboard renders Tailwind layout."""
    app = live_server["app"]
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "dashboards"

    session_injector(context, user_id="e2e_staff_1", role="staff")

    errors = check_no_console_errors(page)
    page.goto(live_server["base_url"] + "/homeStaff")

    expect(page.locator("h1")).to_contain_text("Manage Campus Resources")
    expect(page.locator("#calendar")).to_be_visible()
    assert len(errors) == 0, f"Unexpected JS errors: {errors}"


@pytest.mark.e2e
def test_bookings_view_flag_on(live_server, context, page: Page, session_injector):
    """Bookings history renders modern table with HTMX filter targets."""
    app = live_server["app"]
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "dashboards"

    session_injector(context, user_id="e2e_stud_3", role="student")

    errors = check_no_console_errors(page)
    page.goto(live_server["base_url"] + "/MyBookings")

    expect(page.locator("h1")).to_contain_text("Booking History")
    expect(page.locator("#rbookTablePart")).to_be_visible()
    assert len(errors) == 0, f"Unexpected JS errors: {errors}"


@pytest.mark.e2e
def test_admin_home_flag_on(live_server, context, page: Page, session_injector):
    """Admin command center renders modern grid and stat cards."""
    app = live_server["app"]
    app.config["ARIA_UI_ENABLED"] = True
    app.config["ARIA_UI_PHASE"] = "admin"

    session_injector(context, user_id="e2e_admin_1", role="admin")

    errors = check_no_console_errors(page)
    page.goto(live_server["base_url"] + "/homeAdmin")

    expect(page.locator("h1")).to_contain_text("Campus Operations Control")
    expect(page.locator("text=Room Inventory")).to_be_visible()
    expect(page.locator("#calendar")).to_be_visible()
    assert len(errors) == 0, f"Unexpected JS errors: {errors}"


@pytest.mark.e2e
def test_admin_home_flag_off_rollback(live_server, context, page: Page, session_injector):
    """Admin command center rolls back to legacy Bootstrap hero when flag is off."""
    app = live_server["app"]
    app.config["ARIA_UI_ENABLED"] = False
    app.config["ARIA_UI_PHASE"] = "admin"

    session_injector(context, user_id="e2e_admin_2", role="admin")

    page.goto(live_server["base_url"] + "/homeAdmin")

    expect(page.locator(".aria-hero")).to_be_visible()
