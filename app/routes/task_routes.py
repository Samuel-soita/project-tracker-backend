import logging
from flask import Blueprint, request, jsonify, abort
from app.models import db, Task, Project, User

# Blueprint
task_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------
# Get all tasks
# -----------------------------
@task_bp.route("/", methods=["GET"])
def get_tasks():
    tasks = db.session.query(Task).all()
    return jsonify(
        [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "project_id": t.project_id,
                "assignee_id": t.assignee_id,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ]
    ), 200


# -----------------------------
# Get a single task
# -----------------------------
@task_bp.route("/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404, description="Task not found")

    return jsonify(
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "project_id": task.project_id,
            "assignee_id": task.assignee_id,
            "created_at": task.created_at.isoformat(),
        }
    ), 200


# -----------------------------
# Create a new task
# -----------------------------
@task_bp.route("/", methods=["POST"])
def create_task():
    data = request.get_json() or {}
    required = ["title", "project_id"]
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    project = db.session.get(Project, data["project_id"])
    if not project:
        return jsonify({"error": "Project not found"}), 404

    assignee_id = None
    if "assignee_id" in data:
        assignee = db.session.get(User, data["assignee_id"])
        if not assignee:
            return jsonify({"error": "Assignee not found"}), 404
        assignee_id = assignee.id

    task = Task(
        title=data["title"],
        description=data.get("description"),
        project_id=project.id,
        assignee_id=assignee_id,
        status=data.get("status", "To Do"),
    )

    try:
        db.session.add(task)
        db.session.commit()
        logger.info(f"Task {task.id} created for project {project.id}")
        return jsonify({"message": "Task created successfully", "task_id": task.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create task: {str(e)}")
        return jsonify({"error": "Failed to create task", "details": str(e)}), 500


# -----------------------------
# Update a task
# -----------------------------
@task_bp.route("/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404, description="Task not found")

    data = request.get_json() or {}

    for field in ["title", "description", "status"]:
        if field in data:
            setattr(task, field, data[field])

    if "assignee_id" in data:
        assignee = db.session.get(User, data["assignee_id"])
        if not assignee:
            return jsonify({"error": "Assignee not found"}), 404
        task.assignee_id = assignee.id

    try:
        db.session.commit()
        logger.info(f"Task {task.id} updated")
        return jsonify({"message": "Task updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update task: {str(e)}")
        return jsonify({"error": "Failed to update task", "details": str(e)}), 500


# -----------------------------
# Delete a task
# -----------------------------
@task_bp.route("/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404, description="Task not found")

    try:
        db.session.delete(task)
        db.session.commit()
        logger.info(f"Task {task.id} deleted")
        return jsonify({"message": "Task deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete task: {str(e)}")
        return jsonify({"error": "Failed to delete task", "details": str(e)}), 500


# -----------------------------
# Get all tasks for a project
# -----------------------------
@task_bp.route("/project/<int:project_id>", methods=["GET"])
def get_tasks_by_project(project_id):
    tasks = db.session.query(Task).filter_by(project_id=project_id).all()
    return jsonify(
        {
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "assignee_id": t.assignee_id,
                    "assignee": {
                        "id": t.assignee.id,
                        "name": t.assignee.name,
                        "email": t.assignee.email,
                    }
                    if t.assignee
                    else None,
                }
                for t in tasks
            ]
        }
    ), 200
