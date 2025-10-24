from app.models import db, ActivityLog

def log_activity(user_id, action):
    """
    Logs any action performed by a user
    """
    log = ActivityLog(user_id=user_id, action=action)
    db.session.add(log)
    db.session.commit()