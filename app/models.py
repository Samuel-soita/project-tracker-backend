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
    status = db.Column(db.String(20), default='pending')  # pending, accepted
    role = db.Column(db.String(50), default='collaborator')  # collaborator, viewer, etc.
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

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
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# -----------------------------
# Classes / Specializations
# -----------------------------
class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)  # e.g., Fullstack Android
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    students = db.relationship('User', back_populates='class_model', lazy=True)

# -----------------------------
# Users
# -----------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(50), default='Student')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    cohort_id = db.Column(db.Integer, db.ForeignKey('cohorts.id'), nullable=True)
    cohort = db.relationship('Cohort', backref='students')

    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)

    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(255), nullable=True)

    owned_projects = db.relationship('Project', backref='owner', lazy=True)
    project_memberships = db.relationship('ProjectMember', back_populates='user', cascade="all, delete-orphan")
    activities = db.relationship('ActivityLog', backref='user', lazy=True)
    tasks = db.relationship('Task', back_populates='assignee', lazy=True, cascade="all, delete-orphan")
    class_model = db.relationship('Class', back_populates='students') 

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
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    cohort_id = db.Column(db.Integer, db.ForeignKey('cohorts.id', ondelete='SET NULL'), nullable=True)
    github_link = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='In Progress')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    members = db.relationship('ProjectMember', back_populates='project', lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship('Task', back_populates='project', lazy=True, cascade="all, delete-orphan")
    class_ref = db.relationship('Class', backref='projects', lazy=True)
    cohort = db.relationship('Cohort', backref='projects', lazy=True)

# -----------------------------
# Tasks
# -----------------------------
class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(50), default='To Do')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = db.relationship('Project', back_populates='tasks')
    assignee = db.relationship('User', back_populates='tasks')

# -----------------------------
# Cohorts
# -----------------------------
class Cohort(db.Model):
    __tablename__ = 'cohorts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
