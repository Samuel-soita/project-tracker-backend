from flask import Blueprint, request, jsonify
from app.models import db, Class, User

class_bp = Blueprint('class_bp', __name__, url_prefix='/classes')

# -----------------------------
# CREATE a new class
# -----------------------------
@class_bp.route('/', methods=['POST'])
def create_class():
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'Class name is required'}), 400

    # Check for duplicate
    existing = db.session.execute(
        db.select(Class).filter_by(name=name)
    ).scalar_one_or_none()
    if existing:
        return jsonify({'error': 'Class with this name already exists'}), 409

    new_class = Class(name=name)
    db.session.add(new_class)
    db.session.commit()

    return jsonify({
        'message': 'Class created successfully',
        'class': {
            'id': new_class.id,
            'name': new_class.name
        }
    }), 201


# -----------------------------
# READ all classes
# -----------------------------
@class_bp.route('/', methods=['GET'])
def get_classes():
    query = db.select(Class)
    classes = db.session.execute(query).scalars().all()
    result = [{
        'id': cls.id,
        'name': cls.name,
        'created_at': cls.created_at.isoformat()
    } for cls in classes]

    return jsonify(result), 200


# -----------------------------
# READ single class by ID (with students)
# -----------------------------
@class_bp.route('/<int:class_id>', methods=['GET'])
def get_class(class_id):
    cls = db.session.get(Class, class_id)
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    students = [{
        'id': s.id,
        'name': s.name,
        'email': s.email,
        'role': s.role
    } for s in cls.students]

    return jsonify({
        'id': cls.id,
        'name': cls.name,
        'created_at': cls.created_at.isoformat(),
        'students': students
    }), 200


# -----------------------------
# UPDATE class by ID
# -----------------------------
@class_bp.route('/<int:class_id>', methods=['PUT'])
def update_class(class_id):
    cls = db.session.get(Class, class_id)
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    data = request.get_json()
    name = data.get('name')

    if name:
        duplicate = db.session.execute(
            db.select(Class).filter(Class.name == name, Class.id != class_id)
        ).scalar_one_or_none()
        if duplicate:
            return jsonify({'error': 'Another class with this name already exists'}), 409
        cls.name = name

    db.session.commit()
    return jsonify({'message': 'Class updated successfully'}), 200


# -----------------------------
# DELETE class by ID
# -----------------------------
@class_bp.route('/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    cls = db.session.get(Class, class_id)
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    db.session.delete(cls)
    db.session.commit()
    return jsonify({'message': 'Class deleted successfully'}), 200


# -----------------------------
# LIST all students in a class
# -----------------------------
@class_bp.route('/<int:class_id>/students', methods=['GET'])
def get_class_students(class_id):
    cls = db.session.get(Class, class_id)
    if not cls:
        return jsonify({'error': 'Class not found'}), 404

    students = [{
        'id': s.id,
        'name': s.name,
        'email': s.email,
        'role': s.role
    } for s in cls.students]

    return jsonify({'class': {'id': cls.id, 'name': cls.name}, 'students': students}), 200
