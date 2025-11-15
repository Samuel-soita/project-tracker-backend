from flask import Blueprint, request, jsonify
from app.models import db, User
from app.utils.auth import generate_jwt
from app.utils.email_utils import send_2fa_code_email
import random
import string
from datetime import datetime, timedelta
import logging

auth_routes = Blueprint('auth_routes', __name__)

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Temporary storage for 2FA codes (in production, use Redis or database)
two_fa_codes = {}

def generate_2fa_code():
    """Generate a random 6-digit 2FA code"""
    return ''.join(random.choices(string.digits, k=6))

# -----------------------------
# Register new user
# -----------------------------
@auth_routes.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}

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
    # FIX: ensure data is always a dict
    data = request.get_json(silent=True) or {}

    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401

    # 2FA flow
    if user.two_factor_enabled:
        code = generate_2fa_code()
        expiry = datetime.now() + timedelta(minutes=10)

        two_fa_codes[user.id] = { 'code': code, 'expiry': expiry }

        try:
            send_2fa_code_email(user.email, code, user.name)
            logger.info(f"2FA code sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send 2FA code to {user.email}: {str(e)}")
            logger.warning(f"=== DEV MODE: 2FA CODE FOR {user.email}: {code} ===")
            # Continue login instead of returning error
            pass

        return jsonify({
            'message': '2FA code sent to your email',
            'user_id': user.id,
            'two_factor_enabled': True
        }), 200

    # Normal login → generate JWT
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
    data = request.get_json(silent=True) or {}

    user_id = data.get('user_id')
    code = data.get('code')

    if not all([user_id, code]):
        return jsonify({'message': 'User ID and 2FA code are required'}), 400

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid user ID'}), 400

    user = db.session.get(User, user_id)
    if not user or not user.two_factor_enabled:
        return jsonify({'message': '2FA not enabled for this user'}), 400

    if user_id not in two_fa_codes:
        logger.warning(f"No 2FA code found for user_id: {user_id}. Available keys: {list(two_fa_codes.keys())}")
        return jsonify({'message': 'No 2FA code found. Please request a new code.'}), 400

    stored_data = two_fa_codes[user_id]

    if datetime.now() > stored_data['expiry']:
        del two_fa_codes[user_id]
        return jsonify({'message': '2FA code expired. Please login again.'}), 400

    if code != stored_data['code']:
        return jsonify({'message': 'Invalid 2FA code'}), 401

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
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.two_factor_enabled:
        return jsonify({'message': '2FA already enabled'}), 200

    user.two_factor_enabled = True
    user.two_factor_secret = 'email-based-2fa'
    db.session.commit()

    logger.info(f"2FA enabled for user {user.email}")
    return jsonify({'message': '2FA enabled successfully. You will receive a code via email when logging in.'}), 200

# -----------------------------
# Disable 2FA
# -----------------------------
@auth_routes.route('/auth/disable-2fa', methods=['POST'])
def disable_2fa():
    data = request.get_json(silent=True) or {}
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
