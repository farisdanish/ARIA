import os
import pytest
from website.app import create_app
from website.models.base import db

# Skip background threads (Redis scheduler/subscriber) during testing
os.environ['FLASK_SKIP_BACKGROUND_THREADS'] = '1'

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
