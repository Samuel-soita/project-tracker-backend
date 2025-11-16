import pytest
from app.models import User, db

def test_login_seeded_users(client):
    # Login seeded admin
    res = client.post('/auth/login', json={'email': 'admin@test.com', 'password': 'adminpass'})
    assert res.status_code == 200

    # Login seeded student
    res = client.post('/auth/login', json={'email': 'student1@example.com', 'password': 'studentpass'})
    assert res.status_code == 200

def test_register_new_user(client):
    email = 'newuser@test.com'
    password = 'password123'

    # Register
    res = client.post('/auth/register', json={'name': 'New User', 'email': email, 'password': password})
    assert res.status_code == 201

    # User should exist in DB (modern SQLAlchemy 2.x style)
    user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()
    assert user is not None

    # Login should succeed since there's no verification step now
    res = client.post('/auth/login', json={'email': email, 'password': password})
    assert res.status_code == 200
