import pytest
from app.models import db, Task, Project, User
from datetime import datetime
import json

@pytest.fixture
def seeded_project(app):
    """Seed a project and task for testing."""
    with app.app_context():
        student = User.query.filter_by(email="student1@example.com").first()
        # Seed a project
        project = Project(name="Test Project", owner_id=student.id)
        db.session.add(project)
        db.session.commit()

        # Seed a task
        task = Task(title="Initial Task", project_id=project.id, assignee_id=student.id)
        db.session.add(task)
        db.session.commit()

        # Return only IDs to avoid DetachedInstanceError
        return {
            "student_id": student.id,
            "project_id": project.id,
            "task_id": task.id
        }

def test_get_all_tasks(client, seeded_project):
    resp = client.get("/tasks/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert any(t["title"] == "Initial Task" for t in data)

def test_get_task_by_id(client, seeded_project):
    task_id = seeded_project["task_id"]
    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "Initial Task"

def test_create_task(client, seeded_project):
    project_id = seeded_project["project_id"]
    student_id = seeded_project["student_id"]
    payload = {
        "title": "New Task",
        "project_id": project_id,
        "assignee_id": student_id,
        "status": "In Progress"
    }
    resp = client.post("/tasks/", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 201
    data = resp.get_json()
    assert "task_id" in data

def test_update_task(client, seeded_project, app):
    task_id = seeded_project["task_id"]
    payload = {"title": "Updated Task", "status": "Completed"}
    resp = client.put(f"/tasks/{task_id}", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200

    # Query the task inside app context to avoid DetachedInstanceError
    with app.app_context():
        updated_task = Task.query.get(task_id)
        assert updated_task.title == "Updated Task"
        assert updated_task.status == "Completed"

def test_delete_task(client, seeded_project, app):
    task_id = seeded_project["task_id"]
    resp = client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 200

    with app.app_context():
        deleted_task = Task.query.get(task_id)
        assert deleted_task is None

def test_get_tasks_by_project(client, seeded_project):
    project_id = seeded_project["project_id"]
    resp = client.get(f"/tasks/project/{project_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert all("assignee_id" in t for t in data)