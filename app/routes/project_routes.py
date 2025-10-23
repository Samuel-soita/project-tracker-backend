import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Project, ProjectMember, User
from app.utils.auth import token_required
from app.utils.pagination import paginate
from app.utils.activity_log import log_activity
from functools import wraps

project_routes = Blueprint('project_routes', __name__)

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------
# Decorator: Owner or Admin required
# -----------------------------
def owner_or_admin_required(model_class, id_arg='project_id'):
    def decorator(f):
        @wraps(f)
        def wrapper(current_user, *args, **kwargs):
            obj = model_class.query.get_or_404(kwargs[id_arg])
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

    # Check if student belongs to a cohort
    if current_user.role != 'Admin' and not current_user.cohort_id:
        logger.warning(f"User {current_user.id} attempted to create a project without being in a cohort")
        return jsonify({'message': 'You must belong to a cohort to create a project'}), 403

    project = Project(
        name=data['name'],
        description=data.get('description'),
        owner_id=current_user.id,
        github_link=data.get('github_link'),
        cover_image=data.get('cover_image'),
        tags=','.join([t.strip() for t in data.get('tags', [])]),
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
    track = request.args.get('track')
    query = Project.query

    if current_user.role != 'Admin':
        query = query.filter(
            (Project.owner_id == current_user.id) |
            (Project.status != 'In Progress')
        )

    if track:
        query = query.filter(Project.tags.ilike(f'%{track}%'))

    projects_paginated = paginate(query, request)
    items = []
    for p in projects_paginated['items']:
        members = [{'id': m.user_id, 'email': m.user.email, 'status': m.status} for m in p.members]
        items.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'owner_id': p.owner_id,
            'github_link': p.github_link,
            'tags': p.tags.split(',') if p.tags else [],
            'status': p.status,
            'members': members
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
    project = Project.query.get_or_404(project_id)

    if current_user.role != 'Admin' and project.owner_id != current_user.id and project.status == 'In Progress':
        logger.warning(f"Unauthorized project view attempt by user {current_user.id}")
        return jsonify({'message': 'Not authorized to view this project'}), 403

    members = [{'id': m.user_id, 'email': m.user.email, 'status': m.status} for m in project.members]
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'owner_id': project.owner_id,
        'github_link': project.github_link,
        'tags': project.tags.split(',') if project.tags else [],
        'status': project.status,
        'members': members
    })

# -----------------------------
# Update project (owner or admin)
# -----------------------------
@project_routes.route('/projects/<int:project_id>', methods=['PUT'])
@token_required
@owner_or_admin_required(Project)
def edit_project(current_user, project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()

    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.github_link = data.get('github_link', project.github_link)
    project.tags = ','.join([t.strip() for t in data.get('tags', project.tags.split(','))])

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
    project = Project.query.get_or_404(project_id)
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
    project = Project.query.get_or_404(project_id)
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