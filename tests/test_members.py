import pytest
from app.models import Cohort, User, Project, db

def test_member_crud(client, app):
    # Ensure cohort exists
    cohort = Cohort.query.filter_by(name='Test Cohort').first()
    if not cohort:
        cohort = Cohort(name='Test Cohort', description='Cohort for testing')
        db.session.add(cohort)
        db.session.commit()

    # Register owner if not exists
    owner_email = 'owner@test.com'
    owner = User.query.filter_by(email=owner_email).first()
    if not owner:
        owner = User(name='Owner', email=owner_email, role='Student', is_verified=True)
        owner.set_password('pass')
        db.session.add(owner)
        db.session.commit()

    # Ensure owner is in cohort
    if owner not in cohort.students:
        owner.cohort_id = cohort.id
        db.session.commit()