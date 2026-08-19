"""Integration-test-specific conftest.

Overrides the root `app` fixture to ensure DEVICE_API_TOKEN is always set
in app.config, regardless of Python import ordering.  This is necessary
because `config.py` reads os.environ at class-definition time (module import),
which may happen before conftest.py's os.environ assignments propagate when
pytest collects the integration package.
"""
import pytest

_TOKEN = 'test-device-token'


@pytest.fixture
def app(app):  # noqa: F811  -- intentionally shadows the root fixture
    """Extend the root app fixture with a guaranteed DEVICE_API_TOKEN."""
    app.config['DEVICE_API_TOKEN'] = _TOKEN
    yield app
