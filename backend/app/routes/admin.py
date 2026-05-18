from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.user import User, Department
from app.models.goal import GoalSheet, Goal
from app.models.cycle import Cycle, CycleWindow
from app.models.audit import AuditLog, log_audit
from app.models.checkin import CheckinRecord, QuarterlyAchievement
from app.models.escalation import EscalationRule, EscalationLog
from app.utils.decorators import role_required, get_current_user
from datetime import datetime, date, timezone

admin_bp = Blueprint('admin', __name__)


# --- Cycle Management ---
@admin_bp.route('/cycles', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_cycles():
    cycles = Cycle.query.order_by(Cycle.year.desc()).all()
    return jsonify({'cycles': [c.to_dict(include_windows=True) for c in cycles]}), 200


@admin_bp.route('/cycles', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_cycle():
    user = get_current_user()
    data = request.get_json()
    cycle = Cycle(name=data['name'], year=data['year'], is_active=data.get('is_active', False))
    if cycle.is_active:
        Cycle.query.update({Cycle.is_active: False})
    db.session.add(cycle)
    db.session.flush()

    default_windows = [
        ('goal_setting', 'Goal Setting', f"{data['year']}-05-01", f"{data['year']}-06-30"),
        ('q1_checkin', 'Q1 Check-in', f"{data['year']}-07-01", f"{data['year']}-07-31"),
        ('q2_checkin', 'Q2 Check-in', f"{data['year']}-10-01", f"{data['year']}-10-31"),
        ('q3_checkin', 'Q3 Check-in', f"{data['year']+1}-01-01", f"{data['year']+1}-01-31"),
        ('q4_annual', 'Q4 / Annual Review', f"{data['year']+1}-03-01", f"{data['year']+1}-04-30"),
    ]
    for phase, label, opens, closes in default_windows:
        w = CycleWindow(cycle_id=cycle.id, phase=phase, phase_label=label,
                        opens_at=date.fromisoformat(opens), closes_at=date.fromisoformat(closes))
        db.session.add(w)

    db.session.commit()
    log_audit('cycle', cycle.id, 'created', user.id, description=f'Cycle "{cycle.name}" created')
    db.session.commit()
    return jsonify({'cycle': cycle.to_dict(include_windows=True)}), 201


@admin_bp.route('/cycles/<int:cycle_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_cycle(cycle_id):
    user = get_current_user()
    cycle = Cycle.query.get_or_404(cycle_id)
    data = request.get_json()
    cycle.name = data.get('name', cycle.name)
    cycle.year = data.get('year', cycle.year)
    if data.get('is_active'):
        Cycle.query.filter(Cycle.id != cycle.id).update({Cycle.is_active: False})
        cycle.is_active = True
    db.session.commit()
    return jsonify({'cycle': cycle.to_dict(include_windows=True)}), 200


@admin_bp.route('/cycles/<int:cycle_id>/windows', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_windows(cycle_id):
    user = get_current_user()
    data = request.get_json()
    for w_data in data.get('windows', []):
        window = CycleWindow.query.get(w_data['id'])
        if window and window.cycle_id == cycle_id:
            window.opens_at = date.fromisoformat(w_data['opens_at'])
            window.closes_at = date.fromisoformat(w_data['closes_at'])
            window.phase_label = w_data.get('phase_label', window.phase_label)
    db.session.commit()
    cycle = Cycle.query.get(cycle_id)
    return jsonify({'cycle': cycle.to_dict(include_windows=True)}), 200


@admin_bp.route('/cycles/<int:cycle_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_cycle(cycle_id):
    user = get_current_user()
    cycle = Cycle.query.get_or_404(cycle_id)
    if cycle.is_active:
        return jsonify({'error': 'Cannot delete the active cycle. Deactivate it first.'}), 400
    # Check if any goal sheets exist for this cycle
    sheet_count = GoalSheet.query.filter_by(cycle_id=cycle_id).count()
    if sheet_count > 0:
        return jsonify({'error': f'Cannot delete cycle with {sheet_count} linked goal sheets.'}), 400
    cycle_name = cycle.name
    db.session.delete(cycle)
    db.session.commit()
    log_audit('cycle', cycle_id, 'deleted', user.id, description=f'Cycle "{cycle_name}" deleted')
    db.session.commit()
    return jsonify({'message': f'Cycle "{cycle_name}" deleted'}), 200


# --- User Management ---
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_users():
    users = User.query.order_by(User.full_name).all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_user():
    data = request.get_json()
    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already exists'}), 409
    user = User(
        email=data['email'].lower(), full_name=data['full_name'],
        role=data.get('role', 'employee'), department_id=data.get('department_id'),
        manager_id=data.get('manager_id'), designation=data.get('designation', ''),
    )
    user.set_password(data.get('password', 'password123'))
    db.session.add(user)
    db.session.commit()
    return jsonify({'user': user.to_dict()}), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.full_name = data.get('full_name', user.full_name)
    user.role = data.get('role', user.role)
    user.department_id = data.get('department_id', user.department_id)
    user.manager_id = data.get('manager_id', user.manager_id)
    user.designation = data.get('designation', user.designation)
    user.is_active = data.get('is_active', user.is_active)
    db.session.commit()
    return jsonify({'user': user.to_dict()}), 200


# --- Department Management ---
@admin_bp.route('/departments', methods=['GET'])
@jwt_required()
@role_required('admin', 'manager')
def get_departments():
    depts = Department.query.all()
    return jsonify({'departments': [d.to_dict() for d in depts]}), 200


@admin_bp.route('/departments', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_department():
    data = request.get_json()
    dept = Department(name=data['name'], head_id=data.get('head_id'))
    db.session.add(dept)
    db.session.commit()
    return jsonify({'department': dept.to_dict()}), 201


# --- Goal Unlock ---
@admin_bp.route('/goals/<int:goal_id>/unlock', methods=['POST'])
@jwt_required()
@role_required('admin')
def unlock_goal(goal_id):
    user = get_current_user()
    goal = Goal.query.get_or_404(goal_id)
    sheet = goal.goal_sheet
    old_status = sheet.status
    sheet.status = 'returned'
    db.session.commit()
    log_audit('goal_sheet', sheet.id, 'unlocked', user.id,
              old_values={'status': old_status}, new_values={'status': 'returned'},
              description=f'Admin unlocked goal sheet for {sheet.employee.full_name}')
    db.session.commit()
    return jsonify({'sheet': sheet.to_dict(include_goals=True)}), 200


# --- Audit Logs ---
@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_audit_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    entity_type = request.args.get('entity_type')
    action = request.args.get('action')

    query = AuditLog.query.order_by(AuditLog.timestamp.desc())
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if action:
        query = query.filter_by(action=action)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'logs': [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
    }), 200


# --- Completion Dashboard ---
@admin_bp.route('/completion-dashboard', methods=['GET'])
@jwt_required()
@role_required('admin', 'manager')
def completion_dashboard():
    cycle_id = request.args.get('cycle_id', type=int)
    if not cycle_id:
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    total_employees = User.query.filter_by(role='employee', is_active=True).count()
    sheets = GoalSheet.query.filter_by(cycle_id=cycle_id).all() if cycle_id else []

    stats = {
        'total_employees': total_employees,
        'sheets_created': len(sheets),
        'draft': sum(1 for s in sheets if s.status == 'draft'),
        'submitted': sum(1 for s in sheets if s.status == 'submitted'),
        'approved': sum(1 for s in sheets if s.status == 'approved'),
        'returned': sum(1 for s in sheets if s.status == 'returned'),
        'not_started': total_employees - len(sheets),
    }

    # Check-in completion per quarter
    for q in ['q1', 'q2', 'q3', 'q4']:
        checkins = CheckinRecord.query.filter_by(quarter=q).join(GoalSheet).filter(
            GoalSheet.cycle_id == cycle_id).count() if cycle_id else 0
        achievements_entered = db.session.query(QuarterlyAchievement.goal_id).filter(
            QuarterlyAchievement.quarter == q, QuarterlyAchievement.cycle_id == cycle_id
        ).distinct().count() if cycle_id else 0
        stats[f'{q}_checkins'] = checkins
        stats[f'{q}_achievements'] = achievements_entered

    return jsonify({'stats': stats, 'cycle_id': cycle_id}), 200


# --- Escalation Rules ---
@admin_bp.route('/escalation-rules', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_escalation_rules():
    rules = EscalationRule.query.all()
    return jsonify({'rules': [r.to_dict() for r in rules]}), 200


@admin_bp.route('/escalation-rules', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_escalation_rule():
    data = request.get_json()
    rule = EscalationRule(
        trigger_event=data['trigger_event'],
        days_threshold=data.get('days_threshold', 3),
        notify_employee=data.get('notify_employee', True),
        notify_manager=data.get('notify_manager', True),
        notify_hr=data.get('notify_hr', False),
        escalation_interval=data.get('escalation_interval', 3),
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify({'rule': rule.to_dict()}), 201


@admin_bp.route('/escalation-logs', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_escalation_logs():
    logs = EscalationLog.query.order_by(EscalationLog.triggered_at.desc()).limit(100).all()
    return jsonify({'logs': [l.to_dict() for l in logs]}), 200


# --- Analytics ---
@admin_bp.route('/analytics/overview', methods=['GET'])
@jwt_required()
@role_required('admin', 'manager')
def analytics_overview():
    cycle_id = request.args.get('cycle_id', type=int)
    if not cycle_id:
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    # QoQ achievement trends
    qoq = {}
    for q in ['q1', 'q2', 'q3', 'q4']:
        achs = QuarterlyAchievement.query.filter_by(quarter=q, cycle_id=cycle_id).all() if cycle_id else []
        scores = [a.computed_score for a in achs if a.computed_score is not None]
        qoq[q] = {
            'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'count': len(achs),
            'completed': sum(1 for a in achs if a.status == 'completed'),
        }

    # Department breakdown
    depts = Department.query.all()
    dept_stats = []
    for dept in depts:
        emp_ids = [u.id for u in dept.members]
        sheets = GoalSheet.query.filter(
            GoalSheet.employee_id.in_(emp_ids), GoalSheet.cycle_id == cycle_id
        ).all() if emp_ids and cycle_id else []
        dept_stats.append({
            'department': dept.name,
            'total_employees': len(emp_ids),
            'sheets_approved': sum(1 for s in sheets if s.status == 'approved'),
            'sheets_submitted': sum(1 for s in sheets if s.status == 'submitted'),
        })

    return jsonify({'qoq': qoq, 'departments': dept_stats}), 200
