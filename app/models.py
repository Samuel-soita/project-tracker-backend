from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()

# -----------------------------
# Association table for Project Members
# -----------------------------
class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    role = db.Column(db.String(50), default='collaborator')  # collaborator / viewer / editor
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='project_memberships', foreign_keys=[user_id])
    project = db.relationship('Project', back_populates='members')

# -----------------------------
# Activity Logs
# -----------------------------
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------------
# Users
# -----------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(50), default='Student')  # Student or Admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cohort_id = db.Column(db.Integer, db.ForeignKey('cohorts.id'), nullable=True)
    cohort = db.relationship('Cohort', backref='students')

    # Relationships
    owned_projects = db.relationship('Project', backref='owner', lazy=True)
    project_memberships = db.relationship('ProjectMember', back_populates='user', cascade="all, delete-orphan")
    activities = db.relationship('ActivityLog', backref='user', lazy=True)
    tasks = db.relationship('Task', back_populates='assignee', lazy=True, cascade="all, delete-orphan")

    # Password utilities
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# -----------------------------
# Projects
# -----------------------------
class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    github_link = db.Column(db.String(255), nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)  # Cloudinary URL
    tags = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='In Progress')  # In Progress, Under Review, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = db.relationship('ProjectMember', back_populates='project', lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship('Task', back_populates='project', lazy=True, cascade="all, delete-orphan")

# -----------------------------
# Tasks (for Kanban board)
# -----------------------------
class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(50), default='To Do')  # To Do, In Progress, Completed
    due_date = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = db.relationship('Project', back_populates='tasks')
    assignee = db.relationship('User', back_populates='tasks')
# -----------------------------
# Cohorts
# -----------------------------
class Cohort(db.Model):
    __tablename__ = 'cohorts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
