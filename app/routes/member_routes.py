from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Project, ProjectMember, User
from app.utils.auth import token_required
from app.utils.activity_log import log_activity
from app.utils.email_utils import send_invitation_email

member_routes = Blueprint('member_routes', _name_)

# -----------------------------
# Invite student to project
# -----------------------------
@member_routes.route('/members/projects/<int:project_id>/invite', methods=['POST'])
@token_required
def invite_member(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    if project.owner_id != current_user.id and current_user.role != 'Admin':
        return jsonify({'message': 'Not authorized'}), 403

    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'collaborator')
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

        # Attempt to send email notification
        email_sent = False
        email_error = None
        try:
            send_invitation_email(user.email, project.name, current_user.name, project.id, user.id)
            email_sent = True
        except ValueError as ve:
            # Invalid API key or configuration error
            email_error = str(ve)
        except Exception as e:
            # SendGrid API error or other issues
            email_error = f"Email service error: {str(e)}"

        response_message = f'Invitation created as {role}'
        if email_sent:
            response_message += ' and email notification sent'
        else:
            response_message += f' but email notification failed: {email_error}'

        return jsonify({
            'message': response_message,
            'email_sent': email_sent,
            'email_error': email_error
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create invitation', 'error': str(e)}), 500

# -----------------------------
# Remove member from project
# -----------------------------
@member_routes.route('/members/projects/<int:project_id>/remove', methods=['POST'])
@token_required
def remove_member(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

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
# Get pending invitations for current user
# -----------------------------
@member_routes.route('/members/invitations/pending', methods=['GET'])
@token_required
def get_pending_invitations(current_user):
    """Get all pending project invitations for the current user"""
    try:
        invitations = ProjectMember.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).all()

        result = []
        for invitation in invitations:
            project = db.session.get(Project, invitation.project_id)
            owner = db.session.get(User, project.owner_id) if project else None

            result.append({
                'id': invitation.id,
                'project_id': invitation.project_id,
                'project_name': project.name if project else 'Unknown Project',
                'project_description': project.description if project else '',
                'owner_name': owner.name if owner else 'Unknown',
                'role': invitation.role,
                'created_at': invitation.id  # Using id as proxy for creation order
            })

        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({'message': 'Failed to fetch invitations', 'error': str(e)}), 500

# -----------------------------
# Respond to invitation (accept/decline)
# -----------------------------
@member_routes.route('/members/projects/<int:project_id>/respond', methods=['POST'])
@token_required
def respond_invitation(current_user, project_id):
    invitation = ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first()
    if not invitation or invitation.status != 'pending':
        return jsonify({'message': 'No pending invitation'}), 404

    action = request.json.get('action')
    if action not in ['accept', 'decline']:
        return jsonify({'message': 'Invalid action'}), 400

    try:
        if action == 'decline':
            # Remove the member if they decline
            db.session.delete(invitation)
        else:
            invitation.status = 'accepted'

        db.session.commit()
        log_activity(current_user.id, f"{action.title()}ed invitation for project {project_id}")
        return jsonify({'message': f'Invitation {action}ed', 'role': invitation.role if action == 'accept' else None, 'status': invitation.status if action == 'accept' else 'removed'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to respond to invitation', 'error': str(e)}), 500

# -----------------------------
# Respond to invitation via email link (no auth required)
# -----------------------------
@member_routes.route('/members/projects/<int:project_id>/respond-email/<int:user_id>/<action>', methods=['GET'])
def respond_invitation_email(project_id, user_id, action):
    """Handle invitation response from email link"""
    from flask import render_template_string

    if action not in ['accept', 'reject']:
        return "Invalid action", 400

    project = db.session.get(Project, project_id)
    user = db.session.get(User, user_id)

    if not project or not user:
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head><title>Invitation Not Found</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #EF4444;">❌ Invitation Not Found</h1>
                <p>This invitation link is invalid or has expired.</p>
            </body>
            </html>
        """), 404

    invitation = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()

    if not invitation or invitation.status != 'pending':
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head><title>Invitation Already Responded</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #F59E0B;">⚠️ Already Responded</h1>
                <p>You have already responded to this invitation.</p>
            </body>
            </html>
        """), 400

    try:
        if action == 'reject':
            # Remove the member if they reject
            db.session.delete(invitation)
            db.session.commit()
            log_activity(user_id, f"Rejected invitation for project {project.name}")

            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head><title>Invitation Rejected</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #EF4444;">❌ Invitation Rejected</h1>
                    <p>You have successfully rejected the invitation to join <strong>{{ project_name }}</strong>.</p>
                    <p style="margin-top: 30px;"><a href="{{ frontend_url }}/login" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Go to Dashboard</a></p>
                </body>
                </html>
            """, project_name=project.name, frontend_url="http://127.0.0.1:5173")
        else:
            # Accept the invitation
            invitation.status = 'accepted'
            db.session.commit()
            log_activity(user_id, f"Accepted invitation for project {project.name}")

            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head><title>Invitation Accepted</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #10B981;">✅ Invitation Accepted!</h1>
                    <p>You have successfully joined the project <strong>{{ project_name }}</strong>.</p>
                    <p>You can now view this project in your dashboard.</p>
                    <p style="margin-top: 30px;"><a href="{{ frontend_url }}/login" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Go to Dashboard</a></p>
                </body>
                </html>
            """, project_name=project.name, frontend_url="http://127.0.0.1:5173")

    except SQLAlchemyError as e:
        db.session.rollback()
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head><title>Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #EF4444;">❌ Error</h1>
                <p>Failed to process your response. Please try again later.</p>
            </body>
            </html>
        """), 500