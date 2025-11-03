import pytest
from app.models import Cohort, db

def test_cohort_crud(client, app):
    # Login admin
    login = client.post('/auth/login', json={'email': 'admin@test.com', 'password': 'adminpass'})
    token = login.json['token']
    headers = {'Authorization': f'Bearer {token}'}

    # Create cohort
    res = client.post('/cohorts/', json={'name': 'Cohort 1', 'description': 'Desc'}, headers=headers)
    assert res.status_code == 201
    cohort_id = res.json['id']

    # List cohorts (normalize response)
    res = client.get('/cohorts/', headers=headers)
    assert res.status_code == 200
    cohorts_list = res.json.get('items', [res.json]) if isinstance(res.json, dict) else res.json
    assert any(c['id'] == cohort_id for c in cohorts_list)

    # Update cohort
    updated_data = {'name': 'Cohort 1 Updated', 'description': 'Updated Desc'}
    res = client.put(f'/cohorts/{cohort_id}', json=updated_data, headers=headers)
    assert res.status_code == 200

    # Modern SQLAlchemy 2.x style: Session.get()
    updated_cohort = db.session.get(Cohort, cohort_id)
    assert updated_cohort.name == updated_data['name']

    # Delete cohort
    res = client.delete(f'/cohorts/{cohort_id}', headers=headers)
    assert res.status_code == 200

    # Verify deletion
    deleted_cohort = db.session.get(Cohort, cohort_id)
    assert deleted_cohort is None

    # Ensure cohort not in list anymore
    res = client.get('/cohorts/', headers=headers)
    cohorts_list = res.json.get('items', [res.json]) if isinstance(res.json, dict) else res.json
    assert all(c['id'] != cohort_id for c in cohorts_list)