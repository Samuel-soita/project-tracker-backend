import pytest
from app.models import User, ActivityLog, db
from datetime import datetime, timedelta, timezone
import jwt

# -----------------------------
# Helper: generate JWT token (timezone-aware)
# -----------------------------
def generate_test_token(user_id, secret_key, hours=24):
    return jwt.encode(
        {"user_id": user_id, "exp": datetime.now(timezone.utc) + timedelta(hours=hours)},
        secret_key,
        algorithm="HS256"
    )

# -----------------------------
# Helper: get an admin token
# -----------------------------
def get_admin_token(client, app, email='admin@test.com', password='adminpass'):
    # Login as seeded admin
    login = client.post('/auth/login', json={'email': email, 'password': password})
    assert login.status_code == 200, f"Admin login failed: {login.data}"
    return login.json['token']

# -----------------------------
# Test: Admin can list activities
# -----------------------------
def test_list_activities_admin(client, app):
    token = get_admin_token(client, app)
    headers = {'Authorization': f'Bearer {token}'}

    # Seed activity if none exist
    with app.app_context():
        admin_user = db.session.execute(
            db.select(User).filter_by(email='admin@test.com')
        ).scalar_one()
        if ActivityLog.query.count() == 0:
            db.session.add(ActivityLog(user_id=admin_user.id, action="Test activity"))
            db.session.commit()

    res = client.get('/activities/activities', headers=headers)
    assert res.status_code == 200
    data = res.json
    assert 'items' in data
    assert 'page' in data
    assert 'total_pages' in data
    assert 'total_items' in data

    if data['items']:
        activity = data['items'][0]
        for key in ['id', 'user_id', 'action', 'created_at']:
            assert key in activity

# -----------------------------
# Test: Non-admin cannot list activities
# -----------------------------
def test_list_activities_non_admin_denied(client, app):
    # Login as seeded student
    login = client.post('/auth/login', json={'email': 'student1@example.com', 'password': 'studentpass'})
    assert login.status_code == 200
    token = login.json['token']
    headers = {'Authorization': f'Bearer {token}'}

    res = client.get('/activities/activities', headers=headers)
    assert res.status_code == 403
    assert res.json['message'] == 'You are not authorized to access this resource.'