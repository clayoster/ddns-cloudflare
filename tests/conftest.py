# Set Environment Variables
os.environ["AUTH_USER"] = "testuser"
os.environ["AUTH_PASS"] = "testpass"

import pytest
import os
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()
