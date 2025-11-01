from flask import Blueprint, request, jsonify
from app.models import db, User
from app.utils.auth import token_required, role_required

user_routes = Blueprint('user_routes', __name__)

# -----------------------------
# List all users (admin only)
# -----------------------------
@user_routes.route('/users/', methods=['GET'])
@token_required
@role_required(['Admin'])
def list_users(current_user):
    users = User.query.all()
    result = [{'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role} for u in users]
    return jsonify(result), 200

# -----------------------------
# Get single user (admin only)
# -----------------------------
@user_routes.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    user = User.query.get_or_404(user_id)

    # Allow self-access or admin
    if current_user.id != user.id and current_user.role != 'Admin':
        return jsonify({'message': 'You are not authorized to access this resource.'}), 403

    return jsonify({'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role})
#     # Note: Password is not returned for security reasons

# -----------------------------
# Create user (admin only)
# -----------------------------
@user_routes.route('/users/', methods=['POST'])
@token_required
@role_required(['Admin'])
def create_user(current_user):
    data = request.get_json()
    user = User(name=data['name'], email=data['email'], role=data.get('role', 'Student'))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'id': user.id}), 201

# -----------------------------
# Update user (admin or self)
# -----------------------------
@user_routes.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    # Allow self-update or admin
    if current_user.id != user.id and current_user.role != 'Admin':
        return jsonify({'message': 'Not authorized'}), 403

    data = request.get_json()
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    # Only admin can change roles
    if current_user.role == 'Admin':
        user.role = data.get('role', user.role)
    if data.get('password'):
        user.set_password(data['password'])
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

# -----------------------------
# Delete user (admin or self)
# -----------------------------
@user_routes.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    # Allow self-delete or admin
    if current_user.id != user.id and current_user.role != 'Admin':
        return jsonify({'message': 'Not authorized'}), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})