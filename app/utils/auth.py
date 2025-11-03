

from flask import Blueprint, request, jsonify
from app.models import db, User
from app.utils.auth import generate_jwt
from app.utils.email_utils import send_2fa_code_email
import random
import string
from datetime import datetime, timedelta
import logging

auth_routes = Blueprint('auth_routes', _name_)
import jwt
import os
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app
from app.models import User, db

# -----------------------------
# Configure logger
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

    logger.info(f"New user registered: {email}")
    return jsonify({'message': 'User registered successfully.'}), 201

# -----------------------------
# Login endpoint
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

    if user.two_factor_enabled:
        # Generate and send 2FA code via email
        code = generate_2fa_code()
        expiry = datetime.now() + timedelta(minutes=10)

        # Store code with expiry
        two_fa_codes[user.id] = {
            'code': code,
            'expiry': expiry
        }

        # Send code via email
        try:
            send_2fa_code_email(user.email, code, user.name)
            logger.info(f"2FA code sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send 2FA code to {user.email}: {str(e)}")
            # For development: log the code to console as fallback
            logger.warning(f"=== DEVELOPMENT MODE: 2FA CODE FOR {user.email} ===")
            logger.warning(f"=== CODE: {code} ===")
            logger.warning(f"=== This code will expire in 10 minutes ===")
            # Continue with login instead of returning error
            pass

        return jsonify({
            'message': '2FA code sent to your email',
            'user_id': user.id,
            'two_factor_enabled': True
        }), 200

    # Generate JWT for users without 2FA
    try:
        token = generate_jwt(user.id, user.role)
    except Exception as e:
        logger.error(f"JWT generation failed for user {user.id}: {str(e)}")
        return jsonify({'message': 'Login failed'}), 500

    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'name': user.name,
            'role': user.role,
            'two_factor_enabled': user.two_factor_enabled,
            'class_id': user.class_id,
            'cohort_id': user.cohort_id
        }
    }), 200

# -----------------------------
# Verify 2FA code
# -----------------------------
@auth_routes.route('/auth/verify-2fa', methods=['POST'])
def verify_2fa():
    data = request.get_json()
    user_id = data.get('user_id')
    code = data.get('code')

    if not all([user_id, code]):
        return jsonify({'message': 'User ID and 2FA code are required'}), 400

    # Convert user_id to int if it's a string
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid user ID'}), 400

    user = db.session.get(User, user_id)
    if not user or not user.two_factor_enabled:
        return jsonify({'message': '2FA not enabled for this user'}), 400

    # Check if code exists and is not expired
    if user_id not in two_fa_codes:
        logger.warning(f"No 2FA code found for user_id: {user_id}. Available keys: {list(two_fa_codes.keys())}")
        return jsonify({'message': 'No 2FA code found. Please request a new code.'}), 400

    stored_data = two_fa_codes[user_id]

    if datetime.now() > stored_data['expiry']:
        del two_fa_codes[user_id]
        return jsonify({'message': '2FA code expired. Please login again.'}), 400

    if code != stored_data['code']:
        return jsonify({'message': 'Invalid 2FA code'}), 401

    # Code is valid - clear it and generate token
    del two_fa_codes[user_id]

    try:
        token = generate_jwt(user.id, user.role)
    except Exception as e:
        logger.error(f"JWT generation failed for user {user.id}: {str(e)}")
        return jsonify({'message': '2FA verification failed'}), 500

    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'class_id': user.class_id,
            'cohort_id': user.cohort_id,
            'two_factor_enabled': user.two_factor_enabled
        }
    }), 200

# -----------------------------
# Enable 2FA
# -----------------------------
@auth_routes.route('/auth/enable-2fa', methods=['POST'])
def enable_2fa():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.two_factor_enabled:
        return jsonify({'message': '2FA already enabled'}), 200

    user.two_factor_enabled = True
    user.two_factor_secret = 'email-based-2fa'  # Placeholder since we're not using TOTP
    db.session.commit()

    logger.info(f"2FA enabled for user {user.email}")
    return jsonify({
        'message': '2FA enabled successfully. You will receive a code via email when logging in.'
    }), 200

# -----------------------------
# Disable 2FA
# -----------------------------
@auth_routes.route('/auth/disable-2fa', methods=['POST'])
def disable_2fa():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.two_factor_enabled = False
    user.two_factor_secret = None
    db.session.commit()
    logger.info(f"2FA disabled for user {user.email}")

    return jsonify({'message': '2FA disabled'}), 200


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------
# Generate JWT Access Token
# -----------------------------
def generate_jwt(user_id, role, expires_hours=1):
    """
    Generates a JWT access token with user_id and role.
    Default expiration: 1 hour
    """
    secret_key = current_app.config.get("SECRET_KEY") or os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY not configured in environment or Flask config")

    payload = {
        "user_id": user_id,
        "role": role,
        # Use timezone-aware datetime to avoid DeprecationWarning
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

# -----------------------------
# Token verification decorator
# -----------------------------
def token_required(f):
    """
    Decorator to protect routes requiring JWT authentication.
    Adds 'current_user' as the first argument to the route.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # JWT expected in 'Authorization: Bearer <token>'
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            response = jsonify({"message": "Token is missing!"})
            response.status_code = 401
            return response

        try:
            secret_key = current_app.config.get("SECRET_KEY") or os.environ.get("SECRET_KEY")
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            # Use SQLAlchemy 2.x Session.get() instead of legacy Query.get()
            current_user = db.session.get(User, data["user_id"])
            if not current_user:
                raise Exception("User not found")
        except jwt.ExpiredSignatureError:
            response = jsonify({"message": "Token has expired. Please log in again."})
            response.status_code = 401
            return response
        except jwt.InvalidTokenError:
            response = jsonify({"message": "Invalid token. Please log in again."})
            response.status_code = 401
            return response
        except Exception as e:
            logger.error(f"JWT verification error: {str(e)}")
            response = jsonify({"message": "Token verification failed."})
            response.status_code = 401
            return response

        return f(current_user, *args, **kwargs)

    return decorated

# -----------------------------
# Role verification decorator
# -----------------------------
def role_required(allowed_roles):
    """
    Decorator to restrict access based on user roles.
    Example: @role_required(['Admin', 'Moderator'])
    """
    def decorator(f):
        @wraps(f)
        def wrapper(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({"message": "You are not authorized to access this resource."}), 403
            return f(current_user, *args, **kwargs)
        return wrapper
    return decorator
