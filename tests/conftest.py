# tests/conftest.py
import pytest
from unittest.mock import patch
from run import create_app
from app.models import db, User
from flask import request as flask_request
import os

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:newpassword@localhost:5432/projectx_db"
        ),
        "SECRET_KEY": "testsecretkey",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    with app.app_context():
        db.create_all()  # Ensure tables exist
        yield app
        db.session.remove()
        db.drop_all()  # Clean up after tests

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

# -----------------------------
# Mock email sending and auto-verify users
# -----------------------------
@pytest.fixture(autouse=True)
def mock_email_and_auto_verify(app):
    """
    1) Patch send_verification_email to avoid external calls.
    2) Auto-verify newly registered users.
    """
    from app.routes import auth_routes

    # patch send_verification_email
    send_patch = patch("app.routes.auth_routes.send_verification_email")
    mock_send = send_patch.start()
    mock_send.return_value = True

    # Wrap register to auto-verify
    original_register = auth_routes.register

    def register_and_verify(*args, **kwargs):
        resp = original_register(*args, **kwargs)
        try:
            data = flask_request.get_json(silent=True) or {}
            email = data.get("email")
            if email:
                user = User.query.filter_by(email=email).first()
                if user and not user.is_verified:
                    user.is_verified = True
                    db.session.commit()
        except Exception:
            pass
        return resp

    auth_routes.register = register_and_verify

    yield mock_send

    auth_routes.register = original_register
    send_patch.stop()

# -----------------------------
# Ensure admin exists
# -----------------------------
@pytest.fixture(autouse=True)
def ensure_admin_exists(app):
    """Ensure an admin user exists in the test DB."""
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.com").first()
        if not admin:
            admin = User(
                name="Admin",
                email="admin@test.com",
                role="Admin",
                is_verified=True
            )
            admin.set_password("adminpass")
            db.session.add(admin)
            db.session.commit()

# -----------------------------
# Seed a test student
# -----------------------------
@pytest.fixture(autouse=True)
def seed_test_users(app):
    """Ensure a test student user exists in the test DB."""
    with app.app_context():
        student = User.query.filter_by(email="student1@example.com").first()
        if not student:
            student = User(
                name="Student 1",
                email="student1@example.com",
                role="Student",
                is_verified=True
            )
            student.set_password("studentpass")
            db.session.add(student)
            db.session.commit()
