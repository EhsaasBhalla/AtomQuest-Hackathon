from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app.models.user import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=data['email'].lower().strip()).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=str(user_id))
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/switch-role', methods=['POST'])
@jwt_required()
def switch_role():
    """Demo feature: switch to a different user role for evaluation."""
    data = request.get_json()
    target_role = data.get('role', 'employee')
    target_user = User.query.filter_by(role=target_role, is_active=True).first()
    if not target_user:
        return jsonify({'error': f'No active user with role {target_role}'}), 404

    access_token = create_access_token(identity=str(target_user.id))
    refresh_token = create_refresh_token(identity=str(target_user.id))
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': target_user.to_dict()
    }), 200


@auth_bp.route('/users-by-role', methods=['GET'])
@jwt_required()
def users_by_role():
    """Get all users grouped by role for demo switching."""
    users = User.query.filter_by(is_active=True).all()
    grouped = {}
    for u in users:
        if u.role not in grouped:
            grouped[u.role] = []
        grouped[u.role].append({'id': u.id, 'full_name': u.full_name, 'email': u.email})
    return jsonify(grouped), 200
@auth_bp.route('/register-metadata', methods=['GET'])
def get_register_metadata():
    from app.extensions import cache
    cached = cache.get('register_metadata')
    if cached:
        return cached
    from app.models.user import Department
    departments = Department.query.all()
    managers = User.query.filter(User.role.in_(['manager', 'admin']), User.is_active == True).all()
    
    result = jsonify({
        'departments': [{'id': d.id, 'name': d.name} for d in departments],
        'managers': [{'id': m.id, 'full_name': m.full_name, 'department_id': m.department_id} for m in managers]
    }), 200
    cache.set('register_metadata', result, timeout=3600)
    return result


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validation
    required_fields = ['full_name', 'email', 'password', 'department_id', 'manager_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
            
    email = data['email'].lower().strip()
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered'}), 409
        
    # Generate avatar color
    colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']
    import random
    
    user = User(
        full_name=data['full_name'],
        email=email,
        role='employee',
        department_id=data['department_id'],
        manager_id=data['manager_id'],
        designation=data.get('designation', 'Employee'),
        is_active=True,
        avatar_color=random.choice(colors)
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Registration successful', 'user': user.to_dict()}), 201
