from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.goal import GoalSheet, Goal, SharedGoalMaster, SharedGoalRecipient
from app.models.cycle import Cycle
from app.models.audit import log_audit
from app.utils.decorators import role_required, get_current_user

shared_goals_bp = Blueprint('shared_goals', __name__)


@shared_goals_bp.route('/', methods=['GET'])
@jwt_required()
@role_required('admin', 'manager')
def list_shared_goals():
    cycle_id = request.args.get('cycle_id', type=int)
    if not cycle_id:
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None
    goals = SharedGoalMaster.query.filter_by(cycle_id=cycle_id).all() if cycle_id else []
    return jsonify({'shared_goals': [g.to_dict() for g in goals]}), 200


@shared_goals_bp.route('/', methods=['POST'])
@jwt_required()
@role_required('admin', 'manager')
def create_shared_goal():
    user = get_current_user()
    data = request.get_json()
    cycle_id = data.get('cycle_id')
    if not cycle_id:
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    sg = SharedGoalMaster(
        created_by=user.id, title=data['title'],
        description=data.get('description', ''),
        thrust_area=data['thrust_area'], uom_type=data['uom_type'],
        target_value=data.get('target_value'), target_date=data.get('target_date'),
        department_id=data.get('department_id'), cycle_id=cycle_id,
    )
    db.session.add(sg)
    db.session.commit()
    log_audit('shared_goal', sg.id, 'created', user.id, description=f'Shared goal "{sg.title}" created')
    db.session.commit()
    return jsonify({'shared_goal': sg.to_dict()}), 201


@shared_goals_bp.route('/<int:sg_id>/push', methods=['POST'])
@jwt_required()
@role_required('admin', 'manager')
def push_shared_goal(sg_id):
    user = get_current_user()
    sg = SharedGoalMaster.query.get_or_404(sg_id)
    data = request.get_json()
    employee_ids = data.get('employee_ids', [])

    pushed = []
    for emp_id in employee_ids:
        existing = SharedGoalRecipient.query.filter_by(
            shared_goal_master_id=sg_id, employee_id=emp_id).first()
        if existing:
            continue

        # Get or create goal sheet
        sheet = GoalSheet.query.filter_by(employee_id=emp_id, cycle_id=sg.cycle_id).first()
        if not sheet:
            sheet = GoalSheet(employee_id=emp_id, cycle_id=sg.cycle_id, status='draft')
            db.session.add(sheet)
            db.session.flush()

        # Create goal in employee's sheet
        goal = Goal(
            goal_sheet_id=sheet.id, thrust_area=sg.thrust_area,
            title=sg.title, description=sg.description,
            uom_type=sg.uom_type, target_value=sg.target_value,
            target_date=sg.target_date, weightage=10,
            is_shared=True, shared_goal_master_id=sg.id,
            is_title_locked=True, is_target_locked=True,
            order=sheet.goal_count,
        )
        db.session.add(goal)
        db.session.flush()

        recipient = SharedGoalRecipient(
            shared_goal_master_id=sg.id, employee_id=emp_id, goal_id=goal.id)
        db.session.add(recipient)
        pushed.append(emp_id)
        
        from app.models.notification import create_notification
        link = "/goals"
        create_notification(emp_id, f"A new shared goal '{sg.title}' has been added to your goal sheet.", "🔗", link=link)

    db.session.commit()
    log_audit('shared_goal', sg.id, 'updated', user.id,
              description=f'Shared goal pushed to {len(pushed)} employees')
    db.session.commit()
    return jsonify({'pushed_to': pushed, 'shared_goal': sg.to_dict()}), 200


@shared_goals_bp.route('/<int:sg_id>/recipients', methods=['GET'])
@jwt_required()
@role_required('admin', 'manager')
def get_recipients(sg_id):
    sg = SharedGoalMaster.query.get_or_404(sg_id)
    recipients = SharedGoalRecipient.query.filter_by(shared_goal_master_id=sg_id).all()
    return jsonify({'recipients': [r.to_dict() for r in recipients]}), 200
