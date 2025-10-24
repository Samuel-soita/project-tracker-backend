from flask import Blueprint, request, jsonify, current_app
from app.models import db, User
from app.utils.auth import generate_jwt
from app.utils.email_utils import send_verification_email
import jwt
from datetime import datetime, timedelta, timezone
import logging

auth_routes = Blueprint('auth_routes', __name__)

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------
# Helper: Generate verification token
# -----------------------------
def create_verification_token(user_id, hours_valid=24):
    secret_key = current_app.config.get('SECRET_KEY')
    exp_time = datetime.now(timezone.utc) + timedelta(hours=hours_valid)
    token = jwt.encode({"user_id": user_id, "exp": exp_time}, secret_key, algorithm="HS256")
    return token

# -----------------------------
# Register new user
# -----------------------------
@auth_routes.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'Student')

    if not all([name, email, password]):
        return jsonify({'message': 'Name, email, and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Send verification email
    try:
        token = create_verification_token(user.id)
        send_verification_email(user.email, token, user_name=user.name)
        logger.info(f"Verification email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return jsonify({'message': 'User registered, but verification email failed'}), 500

    return jsonify({'message': 'User registered successfully. Please verify your email.'}), 201

# -----------------------------
# Login
# -----------------------------
@auth_routes.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401

    if not user.is_verified:
        return jsonify({'message': 'Please verify your email before logging in'}), 403

    try:
        token = generate_jwt(user.id, user.role)
    except Exception as e:
        logger.error(f"JWT generation failed for user {user.id}: {str(e)}")
        return jsonify({'message': 'Login failed'}), 500

    return jsonify({
        'token': token,
        'user': {'id': user.id, 'name': user.name, 'role': user.role}
    }), 200

# -----------------------------
# Email verification
# -----------------------------
@auth_routes.route('/auth/verify-email', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    if not token:
        return jsonify({'message': 'Verification token is missing'}), 400

    secret_key = current_app.config.get('SECRET_KEY')
    try:
        data = jwt.decode(token, secret_key, algorithms=['HS256'])
        # Use db.session.get() instead of Query.get() (SQLAlchemy 2.0)
        user = db.session.get(User, data['user_id'])
        if not user:
            return jsonify({'message': 'User not found'}), 404
        if user.is_verified:
            return jsonify({'message': 'Email already verified'}), 200

        user.is_verified = True
        db.session.commit()
        logger.info(f"User {user.email} verified their email")
        return jsonify({'message': 'Email verified successfully!'}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Verification token has expired'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid verification token'}), 400
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return jsonify({'message': 'Email verification failed'}), 500

# -----------------------------
# Resend verification email
# -----------------------------
@auth_routes.route('/auth/resend-verification', methods=['POST'])
def resend_verification():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.is_verified:
        return jsonify({'message': 'Email already verified'}), 200

    try:
        token = create_verification_token(user.id)
        send_verification_email(user.email, token, user_name=user.name)
        logger.info(f"Resent verification email to {user.email}")
        return jsonify({'message': 'Verification email resent successfully'}), 200
    except Exception as e:
        logger.error(f"Failed to resend verification email: {str(e)}")
        return jsonify({'message': 'Failed to resend verification email'}), 500
