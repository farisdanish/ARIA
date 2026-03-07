"""UI rollout helpers for ARIA rebrand."""
from __future__ import annotations

from pathlib import Path
from flask import current_app, render_template


VALID_PHASES = {"public", "dashboards", "admin", "all"}


def _phase_order(phase: str) -> int:
    return {
        "public": 1,
        "dashboards": 2,
        "admin": 3,
        "all": 4,
    }.get(phase, 0)


def is_aria_ui_enabled() -> bool:
    """Return whether ARIA UI is enabled globally."""
    return bool(current_app.config.get("ARIA_UI_ENABLED", False))


def ui_phase() -> str:
    """Return the configured rollout phase."""
    phase = str(current_app.config.get("ARIA_UI_PHASE", "public")).lower()
    return phase if phase in VALID_PHASES else "public"


def should_use_aria_ui(group: str = "public") -> bool:
    """Return whether ARIA UI should be used for the given route group."""
    if not is_aria_ui_enabled():
        return False

    group_rank = _phase_order(group)
    active_rank = _phase_order(ui_phase())
    return active_rank >= group_rank


def aria_template_name(template_name: str) -> str:
    """Map legacy template name to ARIA variant name."""
    return template_name.replace(".html", ".aria.html")


def aria_template_exists(template_name: str) -> bool:
    """Check whether ARIA variant exists on disk."""
    template_path = Path(current_app.root_path) / "templates" / aria_template_name(template_name)
    return template_path.exists()


def render_ui_template(template_name: str, ui_group: str = "public", **context):
    """Render ARIA template variant when rollout flags permit it."""
    chosen_template = template_name
    if should_use_aria_ui(ui_group) and aria_template_exists(template_name):
        chosen_template = aria_template_name(template_name)

    return render_template(chosen_template, **context)
