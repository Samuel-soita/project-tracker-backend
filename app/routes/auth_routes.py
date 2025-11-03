from flask import Blueprint, request, jsonify
from app.models import db, User
from app.utils.auth import generate_jwt
import pyotp
import qrcode
import io
import base64
import logging

auth_routes = Blueprint('auth_routes', __name__)

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
        # Ask user for 2FA code
        return jsonify({
            'message': '2FA required',
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

    user = db.session.get(User, user_id)
    if not user or not user.two_factor_enabled:
        return jsonify({'message': '2FA not enabled for this user'}), 400

    totp = pyotp.TOTP(user.two_factor_secret)
    if totp.verify(code, valid_window=1):  # allow ±30s window
        try:
            token = generate_jwt(user.id, user.role)
        except Exception as e:
            logger.error(f"JWT generation failed for user {user.id}: {str(e)}")
            return jsonify({'message': '2FA verification failed'}), 500
        return jsonify({
            'token': token,
            'user': {'id': user.id, 'name': user.name, 'role': user.role}
        }), 200
    else:
        return jsonify({'message': 'Invalid 2FA code'}), 401

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

    secret = pyotp.random_base32()
    user.two_factor_secret = secret
    user.two_factor_enabled = True
    db.session.commit()

    # Generate OTP URI and QR code
    otp_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="ProjectX")
    qr = qrcode.make(otp_uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    logger.info(f"2FA enabled for user {user.email}")
    return jsonify({
        'message': '2FA enabled',
        'otp_uri': otp_uri,
        'qr_code': f"data:image/png;base64,{qr_b64}"
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
