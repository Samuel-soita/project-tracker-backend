from flask import Blueprint, request, jsonify, current_app
from app.models import db, Cohort
from app.utils.auth import token_required, role_required
from app.utils.pagination import paginate
from app.utils.activity_log import log_activity
import logging

cohort_routes = Blueprint('cohort_routes', __name__)

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------
# Add new cohort (Admin only)
# -----------------------------
@cohort_routes.route('/cohorts/', methods=['POST'])
@token_required
@role_required(['Admin'])
def add_cohort(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'message': 'Cohort name is required'}), 400

    cohort = Cohort(
        name=data['name'],
        description=data.get('description')
    )

    try:
        db.session.add(cohort)
        db.session.commit()
        log_activity(current_user.id, f"Created cohort: {cohort.name}")
        logger.info(f"Admin {current_user.email} created cohort {cohort.name}")
        return jsonify({'message': 'Cohort created', 'id': cohort.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create cohort: {str(e)}")
        return jsonify({'message': 'Failed to create cohort', 'error': str(e)}), 500

# -----------------------------
# List cohorts (Students can view)
# -----------------------------
@cohort_routes.route('/cohorts/', methods=['GET'])
@token_required
def list_cohorts(current_user):
    try:
        cohorts_paginated = paginate(Cohort.query, request)
        items = []
        for c in cohorts_paginated['items']:
            items.append({
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'created_at': c.created_at.isoformat(),
                'updated_at': c.updated_at.isoformat()
            })
        return jsonify({
            'items': items,
            'page': cohorts_paginated['page'],
            'total_pages': cohorts_paginated['total_pages'],
            'total_items': cohorts_paginated['total_items']
        }), 200
    except Exception as e:
        logger.error(f"Failed to list cohorts: {str(e)}")
        return jsonify({'message': 'Failed to fetch cohorts', 'error': str(e)}), 500

# -----------------------------
# Edit cohort (Admin only)
# -----------------------------
@cohort_routes.route('/cohorts/<int:cohort_id>', methods=['PUT'])
@token_required
@role_required(['Admin'])
def edit_cohort(current_user, cohort_id):
    cohort = Cohort.query.get_or_404(cohort_id)
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'message': 'Cohort name is required'}), 400

    cohort.name = data.get('name', cohort.name)
    cohort.description = data.get('description', cohort.description)

    try:
        db.session.commit()
        log_activity(current_user.id, f"Edited cohort: {cohort.name}")
        logger.info(f"Admin {current_user.email} edited cohort {cohort.name}")
        return jsonify({'message': 'Cohort updated'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update cohort: {str(e)}")
        return jsonify({'message': 'Failed to update cohort', 'error': str(e)}), 500

# -----------------------------
# Remove cohort (Admin only)
# -----------------------------
@cohort_routes.route('/cohorts/<int:cohort_id>', methods=['DELETE'])
@token_required
@role_required(['Admin'])
def remove_cohort(current_user, cohort_id):
    cohort = Cohort.query.get_or_404(cohort_id)

    try:
        db.session.delete(cohort)
        db.session.commit()
        log_activity(current_user.id, f"Deleted cohort: {cohort.name}")
        logger.info(f"Admin {current_user.email} deleted cohort {cohort.name}")
        return jsonify({'message': 'Cohort deleted'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete cohort: {str(e)}")
        return jsonify({'message': 'Failed to delete cohort', 'error': str(e)}), 500


# Student joins a cohort
# -----------------------------
@cohort_routes.route('/cohorts/<int:cohort_id>/join', methods=['POST'])
@token_required
def join_cohort(current_user, cohort_id):
    """
    Allows a student to join a cohort dynamically.
    """
    if current_user.role != 'Student':
        return jsonify({"message": "Only students can join cohorts"}), 403

    cohort = Cohort.query.get(cohort_id)
    if not cohort:
        return jsonify({"message": "Cohort not found"}), 404

    # Assign the student to the cohort
    current_user.cohort_id = cohort.id
    try:
        db.session.commit()
        log_activity(current_user.id, f"Joined cohort: {cohort.name}")
        logger.info(f"Student {current_user.email} joined cohort {cohort.name}")
        return jsonify({
            "message": f"{current_user.name} has joined {cohort.name}",
            "cohort": {"id": cohort.id, "name": cohort.name}
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to join cohort: {str(e)}")
        return jsonify({'message': 'Failed to join cohort', 'error': str(e)}), 500