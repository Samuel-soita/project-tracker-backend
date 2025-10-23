from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Project, ProjectMember, User
from app.utils.auth import token_required
from app.utils.activity_log import log_activity
from app.utils.email_utils import send_invitation_email

member_routes = Blueprint('member_routes', __name__)

# -----------------------------
# Invite student to project
# -----------------------------
@member_routes.route('/members/projects/<int:project_id>/invite', methods=['POST'])
@token_required
def invite_member(current_user, project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id and current_user.role != 'Admin':
        return jsonify({'message': 'Not authorized'}), 403

    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'collaborator')  # default role
    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    existing = ProjectMember.query.filter_by(project_id=project_id, user_id=user.id).first()
    if existing:
        return jsonify({'message': 'User already invited'}), 400

    try:
        invitation = ProjectMember(project_id=project_id, user_id=user.id, status='pending', role=role)
        db.session.add(invitation)
        db.session.commit()
        log_activity(current_user.id, f"Invited {user.email} as {role} to project {project.name}")
        send_invitation_email(user.email, project.name)
        return jsonify({'message': f'Invitation sent as {role}'}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to send invitation', 'error': str(e)}), 500

# -----------------------------
# Remove member from project
# -----------------------------
@member_routes.route('/members/projects/<int:project_id>/remove', methods=['POST'])
@token_required
def remove_member(current_user, project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id and current_user.role != 'Admin':
        return jsonify({'message': 'Not authorized'}), 403

    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not member:
        return jsonify({'message': 'Member not found'}), 404

    try:
        db.session.delete(member)
        db.session.commit()
        log_activity(current_user.id, f"Removed user {user_id} from project {project.name}")
        return jsonify({'message': 'Member removed'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to remove member', 'error': str(e)}), 500

# -----------------------------
# Respond to invitation (accept/decline)
# -----------------------------
@member_routes.route('/members/projects/<int:project_id>/respond', methods=['POST'])
@token_required
def respond_invitation(current_user, project_id):
    invitation = ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first()
    if not invitation or invitation.status != 'pending':
        return jsonify({'message': 'No pending invitation'}), 404

    action = request.json.get('action')  # accept or decline
    if action not in ['accept', 'decline']:
        return jsonify({'message': 'Invalid action'}), 400

    try:
        invitation.status = 'accepted' if action == 'accept' else 'declined'
        db.session.commit()
        log_activity(current_user.id, f"{action.title()}ed invitation for project {project_id}")
        return jsonify({'message': f'Invitation {action}ed', 'role': invitation.role, 'status': invitation.status}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to respond to invitation', 'error': str(e)}), 500