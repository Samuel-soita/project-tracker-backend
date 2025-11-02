import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Project, ProjectMember, User, Class
from app.utils.auth import token_required
from app.utils.pagination import paginate
from app.utils.activity_log import log_activity
from functools import wraps

project_routes = Blueprint('project_routes', _name_)

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(_name_)
logger.setLevel(logging.INFO)

# -----------------------------
# Decorator: Owner or Admin required
# -----------------------------
def owner_or_admin_required(model_class, id_arg='project_id'):
    def decorator(f):
        @wraps(f)
        def wrapper(current_user, *args, **kwargs):
            obj = db.session.get(model_class, kwargs[id_arg])
            if not obj:
                return jsonify({'message': f"{model_class._name_} not found"}), 404
            if current_user.role != 'Admin' and getattr(obj, 'owner_id', None) != current_user.id:
                logger.warning(f"Unauthorized access by user {current_user.id}")
                return jsonify({'message': 'Not authorized'}), 403
            return f(current_user, *args, **kwargs)
        return wrapper
    return decorator

# -----------------------------
# Create project (Student must be in a cohort, Admin exempt)
# -----------------------------
@project_routes.route('/projects', methods=['POST'])
@token_required
def add_project(current_user):
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'message': 'Project name is required'}), 400

    # Validate that class_id and cohort_id are provided
    if not data.get('class_id'):
        return jsonify({'message': 'Class is required'}), 400
    if not data.get('cohort_id'):
        return jsonify({'message': 'Cohort is required'}), 400

    project = Project(
        name=data['name'],
        description=data.get('description'),
        owner_id=current_user.id,
        class_id=data['class_id'],
        cohort_id=data['cohort_id'],
        github_link=data.get('github_link'),
        status='In Progress'
    )

    try:
        db.session.add(project)
        db.session.commit()
        log_activity(current_user.id, f"Created project: {project.name}")
        logger.info(f"Project {project.id} created by user {current_user.id}")
        return jsonify({'message': 'Project created', 'id': project.id}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to create project by user {current_user.id}: {str(e)}")
        return jsonify({'message': 'Failed to create project'}), 500

# -----------------------------
# List projects (pagination + filtering)
# -----------------------------
@project_routes.route('/projects', methods=['GET'])
@token_required
def list_projects(current_user):
    query = db.session.query(Project)

    # Students can see all projects (no filtering by status)
    # Admins can see all projects
    # No restrictions - everyone can see all projects

    projects_paginated = paginate(query, request)
    items = []
    for p in projects_paginated['items']:
        members = [{'id': m.user_id, 'name': m.user.name, 'email': m.user.email, 'status': m.status} for m in p.members]

        # Get owner information
        owner = db.session.get(User, p.owner_id) if p.owner_id else None
        owner_name = owner.name if owner else 'Unknown'

        # Get class information
        class_info = None
        if p.class_id:
            project_class = db.session.get(Class, p.class_id)
            if project_class:
                class_info = {
                    'id': project_class.id,
                    'name': project_class.name
                }

        # Get cohort information
        cohort_info = None
        if p.cohort_id:
            from app.models import Cohort
            project_cohort = db.session.get(Cohort, p.cohort_id)
            if project_cohort:
                cohort_info = {
                    'id': project_cohort.id,
                    'name': project_cohort.name
                }

        items.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'owner_id': p.owner_id,
            'owner_name': owner_name,
            'github_link': p.github_link,
            'status': p.status,
            'members': members,
            'class': class_info,
            'cohort': cohort_info
        })

    return jsonify({
        'items': items,
        'page': projects_paginated['page'],
        'total_pages': projects_paginated['total_pages'],
        'total_items': projects_paginated['total_items']
    }), 200

# -----------------------------
# Get single project
# -----------------------------
@project_routes.route('/projects/<int:project_id>', methods=['GET'])
@token_required
def get_project(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    # Allow all users to view any project (no authorization check)

    # Get owner information
    owner = db.session.get(User, project.owner_id) if project.owner_id else None
    owner_data = None
    if owner:
        owner_data = {
            'id': owner.id,
            'name': owner.name,
            'email': owner.email
        }
        # Get owner's cohort information
        if owner.cohort:
            owner_data['cohort'] = {
                'id': owner.cohort.id,
                'name': owner.cohort.name
            }
        # Get owner's class information
        if owner.class_id:
            owner_class = db.session.get(Class, owner.class_id)
            if owner_class:
                owner_data['class'] = {
                    'id': owner_class.id,
                    'name': owner_class.name
                }

    # Get project's class information
    class_info = None
    if project.class_id:
        project_class = db.session.get(Class, project.class_id)
        if project_class:
            class_info = {
                'id': project_class.id,
                'name': project_class.name
            }

    # Get project's cohort information
    cohort_info = None
    if project.cohort_id:
        from app.models import Cohort
        project_cohort = db.session.get(Cohort, project.cohort_id)
        if project_cohort:
            cohort_info = {
                'id': project_cohort.id,
                'name': project_cohort.name
            }

    members = [{'id': m.user_id, 'name': m.user.name, 'email': m.user.email, 'status': m.status} for m in project.members]
    return jsonify({
        'project': {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'owner_id': project.owner_id,
            'owner': owner_data,
            'class_id': project.class_id,
            'cohort_id': project.cohort_id,
            'class': class_info,
            'cohort': cohort_info,
            'github_link': project.github_link,
            'status': project.status,
            'members': members,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None
        }
    })

# -----------------------------
# Update project (owner or admin)
# -----------------------------
@project_routes.route('/projects/<int:project_id>', methods=['PUT'])
@token_required
@owner_or_admin_required(Project)
def edit_project(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    data = request.get_json()
    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.github_link = data.get('github_link', project.github_link)

    # Update class_id and cohort_id if provided
    if 'class_id' in data:
        project.class_id = data.get('class_id')
    if 'cohort_id' in data:
        project.cohort_id = data.get('cohort_id')

    try:
        db.session.commit()
        log_activity(current_user.id, f"Updated project: {project.name}")
        logger.info(f"Project {project.id} updated by user {current_user.id}")
        return jsonify({'message': 'Project updated'})
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to update project {project.id}: {str(e)}")
        return jsonify({'message': 'Failed to update project'}), 500

# -----------------------------
# Delete project (owner or admin)
# -----------------------------
@project_routes.route('/projects/<int:project_id>', methods=['DELETE'])
@token_required
@owner_or_admin_required(Project)
def remove_project(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    try:
        db.session.delete(project)
        db.session.commit()
        log_activity(current_user.id, f"Deleted project: {project.name}")
        logger.info(f"Project {project.id} deleted by user {current_user.id}")
        return jsonify({'message': 'Project deleted'})
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to delete project {project.id}: {str(e)}")
        return jsonify({'message': 'Failed to delete project'}), 500

# -----------------------------
# Update project status (Kanban)
# -----------------------------
@project_routes.route('/projects/<int:project_id>/status', methods=['PATCH'])
@token_required
@owner_or_admin_required(Project)
def change_project_status(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    status = request.json.get('status')
    allowed_statuses = ['In Progress', 'Under Review', 'Completed']

    if status not in allowed_statuses:
        logger.warning(f"User {current_user.id} provided invalid status '{status}' for project {project.id}")
        return jsonify({'message': f"Invalid status. Allowed: {', '.join(allowed_statuses)}"}), 400

    project.status = status
    try:
        db.session.commit()
        log_activity(current_user.id, f"Changed status of project {project.name} to {status}")
        logger.info(f"Project {project.id} status changed to {status} by user {current_user.id}")
        return jsonify({'message': 'Project status updated'})
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to update project status {project.id}: {str(e)}")
        return jsonify({'message': 'Failed to update project status'}), 500