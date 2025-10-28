import pytest
from app.models import User, Project, Cohort, db

# -----------------------------
# Helper: Get JWT token for a user
# -----------------------------
def get_auth_token(client, email, password, cohort_id=None):
    user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

    if not user:
        # If user not seeded, create
        user = User(name=email.split('@')[0], email=email, role='Student', is_verified=True)
        user.set_password(password)
        if cohort_id:
            user.cohort_id = cohort_id
        db.session.add(user)
        db.session.commit()

    login = client.post('/auth/login', json={'email': email, 'password': password})
    assert login.status_code == 200
    return login.json['token']

# -----------------------------
# Test Project CRUD
# -----------------------------
def test_project_crud(client):
    # -----------------------------
    # Prepare cohort for student
    # -----------------------------
    cohort = db.session.execute(
        db.select(Cohort).filter_by(name='Fullstack 101')
    ).scalar_one_or_none()

    if not cohort:
        cohort = Cohort(name='Fullstack 101')
        db.session.add(cohort)
        db.session.commit()

    # -----------------------------
    # Student with cohort
    # -----------------------------
    token = get_auth_token(client, 'user1@test.com', 'pass', cohort_id=cohort.id)
    headers = {'Authorization': f'Bearer {token}'}

    project_data = {
        'name': 'Project X',
        'description': 'Test project',
        'tags': ['Fullstack']
    }

    # Create project (should succeed)
    res = client.post('/projects', json=project_data, headers=headers)
    assert res.status_code == 201
    project_id = res.json['id']

    # -----------------------------
    # Student without cohort
    # -----------------------------
    token_no_cohort = get_auth_token(client, 'user2@test.com', 'pass')
    headers_no_cohort = {'Authorization': f'Bearer {token_no_cohort}'}
    res = client.post('/projects', json=project_data, headers=headers_no_cohort)
    assert res.status_code == 403
    assert 'cohort' in res.json['message'].lower()

    # -----------------------------
    # Retrieve project
    # -----------------------------
    res = client.get(f'/projects/{project_id}', headers=headers)
    assert res.status_code == 200
    assert res.json['name'] == project_data['name']

    # -----------------------------
    # Update project
    # -----------------------------
    updated_data = {'name': 'Project X Updated', 'tags': ['Fullstack', 'Python']}
    res = client.put(f'/projects/{project_id}', json=updated_data, headers=headers)
    assert res.status_code == 200
    res = client.get(f'/projects/{project_id}', headers=headers)
    assert res.json['name'] == 'Project X Updated'

    # -----------------------------
    # Change project status
    # -----------------------------
    res = client.patch(f'/projects/{project_id}/status', json={'status': 'Under Review'}, headers=headers)
    assert res.status_code == 200
    res = client.get(f'/projects/{project_id}', headers=headers)
    assert res.json['status'] == 'Under Review'

    # -----------------------------
    # Delete project
    # -----------------------------
    res = client.delete(f'/projects/{project_id}', headers=headers)
    assert res.status_code == 200

    # Verify deletion
    res = client.get(f'/projects/{project_id}', headers=headers)
    assert res.status_code == 404