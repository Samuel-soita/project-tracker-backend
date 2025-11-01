from flask import Blueprint, jsonify, request
from app.models import ActivityLog
from app.utils.auth import token_required, role_required
from app.utils.pagination import paginate
import logging

activity_routes = Blueprint('activity_routes', __name__)

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------
# List activity logs (Admin only)
# -----------------------------
@activity_routes.route('/activities/activities', methods=['GET'])
@token_required
@role_required(['Admin'])
def list_activities(current_user):
    try:
        activities_paginated = paginate(ActivityLog.query.order_by(ActivityLog.created_at.desc()), request)
        result = [
            {
                'id': a.id,
                'user_id': a.user_id,
                'action': a.action,
                'created_at': a.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for a in activities_paginated['items']
        ]

        return jsonify({
            'items': result,
            'page': activities_paginated['page'],
            'total_pages': activities_paginated['total_pages'],
            'total_items': activities_paginated['total_items']
        }), 200

    except Exception as e:
        logger.error(f"Failed to fetch activities: {str(e)}")
        return jsonify({'message': 'Failed to fetch activities', 'error': str(e)}), 500