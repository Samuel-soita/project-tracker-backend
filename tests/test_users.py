import pytest
from app.models import User, db

# -----------------------------
# Helper: Get JWT token for a user
# -----------------------------
def get_token(client, email, password):
    login = client.post('/auth/login', json={'email': email, 'password': password})
    assert login.status_code == 200
    return login.json['token']

# -----------------------------
# Test: User CRUD
# -----------------------------
def test_user_crud(client):
    # Use seeded admin
    admin_email = "admin@test.com"
    admin_password = "adminpass"
    token = get_token(client, admin_email, admin_password)
    headers = {'Authorization': f'Bearer {token}'}

    # -----------------------------
    # Create new user
    # -----------------------------
    user_data = {'name': 'Test Student', 'email': 'student_test@test.com', 'password': 'pass', 'role': 'Student'}
    res = client.post('/users/', json=user_data, headers=headers)
    assert res.status_code == 201
    user_id = res.json['id']

    # -----------------------------
    # Auto-verify the new user so they can login
    # -----------------------------
    new_user = db.session.execute(
        db.select(User).filter_by(email=user_data['email'])
    ).scalar_one_or_none()
    assert new_user is not None
    new_user.is_verified = True
    db.session.commit()

    # -----------------------------
    # List users (admin only)
    # -----------------------------
    res = client.get('/users/', headers=headers)
    assert res.status_code == 200
    assert any(u['id'] == user_id for u in res.json)

    # -----------------------------
    # Get user (admin access)
    # -----------------------------
    res = client.get(f'/users/{user_id}', headers=headers)
    assert res.status_code == 200
    assert res.json['email'] == user_data['email']

    # -----------------------------
    # Update user (admin)
    # -----------------------------
    updated_data = {'name': 'Student Updated'}
    res = client.put(f'/users/{user_id}', json=updated_data, headers=headers)
    assert res.status_code == 200

    # Verify update
    res = client.get(f'/users/{user_id}', headers=headers)
    assert res.json['name'] == 'Student Updated'

    # -----------------------------
    # Self-update: student can update own name
    # -----------------------------
    student_token = get_token(client, user_data['email'], 'pass')
    student_headers = {'Authorization': f'Bearer {student_token}'}
    res = client.put(f'/users/{user_id}', json={'name': 'Self Updated'}, headers=student_headers)
    assert res.status_code == 200
    res = client.get(f'/users/{user_id}', headers=student_headers)
    assert res.json['name'] == 'Self Updated'

    # -----------------------------
    # Delete user (admin)
    # -----------------------------
    res = client.delete(f'/users/{user_id}', headers=headers)
    assert res.status_code == 200

    # Verify deletion
    res = client.get(f'/users/{user_id}', headers=headers)
    assert res.status_code == 404

# -----------------------------
# Test: Non-admin cannot list all users
# -----------------------------
def test_non_admin_list_users_denied(client):
    # Use seeded student
    student_email = "student1@example.com"
    student_password = "studentpass"
    token = get_token(client, student_email, student_password)
    headers = {'Authorization': f'Bearer {token}'}

    res = client.get('/users/', headers=headers)
    assert res.status_code == 403
    assert 'not authorized' in res.json['message'].lower()
