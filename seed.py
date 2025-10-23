import os
import random
from datetime import datetime
from app.models import db, User, Cohort, Project, ProjectMember, ActivityLog, Task
from run import create_app
from sqlalchemy import text

# -----------------------------
# Load environment variables for passwords
# -----------------------------
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "adminpass")
STUDENT_PASSWORD = os.environ.get("STUDENT_PASSWORD", "studentpass")

# -----------------------------
# Initialize app context
# -----------------------------
app = create_app()

with app.app_context():
    # -----------------------------
    # Truncate tables & reset identities
    # -----------------------------
    print("⚠️ Truncating all tables...")
    db.session.execute(
        text('TRUNCATE TABLE users, cohorts, projects, project_members, tasks, activity_logs RESTART IDENTITY CASCADE')
    )
    db.session.commit()

    # -----------------------------
    # Seed Users
    # -----------------------------
    print("⚡ Seeding users...")
    admin = User(
        name="Admin User",
        email="admin@test.com",
        role="Admin",
        is_verified=True
    )
    admin.set_password(ADMIN_PASSWORD)

    students = []
    for i in range(1, 6):
        student = User(
            name=f"Student {i}",
            email=f"student{i}@example.com",
            role="Student",
            is_verified=True
        )
        student.set_password(STUDENT_PASSWORD)
        students.append(student)

    db.session.add(admin)
    db.session.add_all(students)
    db.session.commit()
    print("✅ Users seeded: 1 Admin + 5 Students")

    # -----------------------------
    # Seed additional test users for pytest (no duplicates!)
    # -----------------------------
    test_users = [
        {"name": "Owner Test", "email": "owner@test.com", "role": "Student", "password": "pass"},
        {"name": "User1 Test", "email": "user1@test.com", "role": "Student", "password": "studentpass"},
        {"name": "Student Test", "email": "student@test.com", "role": "Student", "password": "studentpass"},
    ]

    for u in test_users:
        user = User(name=u["name"], email=u["email"], role=u["role"], is_verified=True)
        user.set_password(u["password"])
        db.session.add(user)
    db.session.commit()
    print("✅ Test users seeded for pytest")

    # -----------------------------
    # Seed Cohorts
    # -----------------------------
    print("⚡ Seeding cohorts...")
    cohorts = [
        Cohort(name="Cohort Alpha", description="Fullstack track cohort"),
        Cohort(name="Cohort Beta", description="Data Science track cohort")
    ]
    db.session.add_all(cohorts)
    db.session.commit()
    print("✅ Cohorts seeded: 2 cohorts")

    # Assign students to cohorts
    for i, student in enumerate(students):
        student.cohort_id = cohorts[i % len(cohorts)].id
    db.session.commit()
    print("✅ Students assigned to cohorts")

    # -----------------------------
    # Seed Projects
    # -----------------------------
    print("⚡ Seeding projects...")
    project_templates = [
        {"name": "Project X", "description": "Fullstack web app", "track": "Fullstack"},
        {"name": "Project Y", "description": "Data analysis project", "track": "Data Science"},
        {"name": "Project Z", "description": "Mobile app", "track": "Mobile"},
    ]

    tags_by_track = {
        "Fullstack": ["Python", "Flask", "React", "PostgreSQL"],
        "Data Science": ["Python", "Pandas", "NumPy", "Machine Learning"],
        "Mobile": ["Android", "Java", "Kotlin", "Flutter"]
    }

    statuses = ["In Progress", "Completed", "Under Review"]
    projects = []

    for i, template in enumerate(project_templates):
        owner = students[i % len(students)]
        project = Project(
            name=template["name"],
            description=template["description"],
            owner_id=owner.id,
            github_link=f"https://github.com/{owner.email.split('@')[0]}/{template['name'].replace(' ', '').lower()}",
            tags=",".join(random.sample(tags_by_track[template["track"]], k=2)),
            status=random.choice(statuses)
        )
        projects.append(project)

    db.session.add_all(projects)
    db.session.commit()
    print(f"✅ Projects seeded: {len(projects)} projects")

    # -----------------------------
    # Seed Project Members + Activity Logs
    # -----------------------------
    print("⚡ Seeding project members & activity logs...")
    for project in projects:
        possible_members = [s for s in students if s.id != project.owner_id]
        members_to_add = random.sample(possible_members, k=random.randint(1, min(2, len(possible_members))))
        for member in members_to_add:
            db.session.add(ProjectMember(project_id=project.id, user_id=member.id, status="accepted"))
            db.session.add(ActivityLog(user_id=member.id, action=f"Joined project {project.name}"))

        # Owner logs
        db.session.add(ActivityLog(user_id=project.owner_id, action=f"Created project {project.name}"))

        if project.status == "Completed":
            db.session.add(ActivityLog(user_id=project.owner_id, action=f"Marked project {project.name} as Completed"))

    db.session.commit()
    print("✅ Project members & activity logs seeded")

    # -----------------------------
    # Seed Tasks for each Project
    # -----------------------------
    print("⚡ Seeding tasks...")
    task_templates = [
        "Setup project repository",
        "Design database schema",
        "Implement authentication",
        "Build REST API endpoints",
        "Connect frontend with backend",
        "Write unit tests",
        "Prepare documentation"
    ]

    task_statuses = ["To Do", "In Progress", "Completed"]

    for project in projects:
        task_count = random.randint(3, 6)
        for i in range(task_count):
            task = Task(
                title=random.choice(task_templates),
                description=f"Task {i+1} for {project.name}",
                status=random.choice(task_statuses),
                project_id=project.id,
                assignee_id=random.choice(students).id,
                created_at=datetime.utcnow()
            )
            db.session.add(task)

        db.session.add(ActivityLog(user_id=project.owner_id, action=f"Created {task_count} tasks for {project.name}"))

    db.session.commit()
    print("✅ Tasks seeded for each project")

    # -----------------------------
    # Seed Admin Activity Logs
    # -----------------------------
    admin_logs = [
        ActivityLog(user_id=admin.id, action="Seeded database with admin, students, and tasks"),
        ActivityLog(user_id=admin.id, action="Reviewed all project submissions")
    ]
    db.session.add_all(admin_logs)
    db.session.commit()

    print("🎉 Database seeded successfully!")
