from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.user import User
from app.models.goal import GoalSheet, Goal
from app.models.checkin import QuarterlyAchievement, CheckinRecord
from app.models.audit import log_audit
from app.utils.decorators import role_required, get_current_user
from datetime import datetime, timezone

manager_bp = Blueprint('manager', __name__)


@manager_bp.route('/team', methods=['GET'])
@jwt_required()
@role_required('manager', 'admin')
def get_team():
    user = get_current_user()
    if user.role == 'admin':
        reports = User.query.filter(User.role.in_(['employee', 'manager']), User.is_active==True).all()
    else:
        reports = User.query.filter_by(manager_id=user.id, is_active=True).all()
        if user.department_id:
            reports = [r for r in reports if r.department_id == user.department_id]
    cycle_id = request.args.get('cycle_id', type=int)
    if not cycle_id:
        from app.models.cycle import Cycle
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    team = []
    for emp in reports:
        emp_data = emp.to_dict()
        sheet = GoalSheet.query.filter_by(employee_id=emp.id, cycle_id=cycle_id).first() if cycle_id else None
        emp_data['goal_sheet'] = sheet.to_dict() if sheet else None
        emp_data['goal_sheet_status'] = sheet.status if sheet else 'not_started'
        team.append(emp_data)
    return jsonify({'team': team, 'cycle_id': cycle_id}), 200


@manager_bp.route('/team/<int:employee_id>/sheet', methods=['GET'])
@jwt_required()
@role_required('manager', 'admin')
def get_employee_sheet(employee_id):
    user = get_current_user()
    employee = User.query.get_or_404(employee_id)
    if employee.manager_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Not your direct report'}), 403

    cycle_id = request.args.get('cycle_id', type=int)
    if not cycle_id:
        from app.models.cycle import Cycle
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    sheet = GoalSheet.query.filter_by(employee_id=employee_id, cycle_id=cycle_id).first()
    if not sheet:
        return jsonify({'error': 'No goal sheet found'}), 404
    return jsonify({
        'sheet': sheet.to_dict(include_goals=True),
        'employee': employee.to_dict()
    }), 200


@manager_bp.route('/team/<int:employee_id>/sheet/resolve-unlock', methods=['POST'])
@jwt_required()
@role_required('manager', 'admin')
def resolve_unlock(employee_id):
    user = get_current_user()
    data = request.get_json()
    action = data.get('action') # 'accept' or 'reject'
    feedback = data.get('feedback', '')
    
    cycle_id = data.get('cycle_id')
    if not cycle_id:
        from app.models.cycle import Cycle
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    sheet = GoalSheet.query.filter_by(employee_id=employee_id, cycle_id=cycle_id).first()
    if not sheet or not sheet.unlock_requested:
        return jsonify({'error': 'No pending unlock request found'}), 404
        
    if action == 'accept':
        sheet.status = 'draft'
        sheet.unlock_requested = False
        sheet.unlock_feedback = feedback
        log_audit('goal_sheet', sheet.id, 'unlock_accepted', user.id, description='Unlock request approved')
        
        from app.models.notification import create_notification
        create_notification(sheet.employee_id, f"Your unlock request was approved. You can now edit your goals. Feedback: {feedback}", "✅", link="/goals")
        
    elif action == 'reject':
        sheet.unlock_requested = False
        sheet.unlock_feedback = feedback
        log_audit('goal_sheet', sheet.id, 'unlock_rejected', user.id, description='Unlock request rejected')
        
        from app.models.notification import create_notification
        create_notification(sheet.employee_id, f"Your unlock request was declined. Feedback: {feedback}", "❌", link="/goals")
        
    else:
        return jsonify({'error': 'Invalid action'}), 400
        
    db.session.commit()
    return jsonify({'message': f'Unlock request {action}ed', 'sheet': sheet.to_dict()}), 200


@manager_bp.route('/team/<int:employee_id>/goals/<int:goal_id>', methods=['PUT'])
@jwt_required()
@role_required('manager', 'admin')
def edit_employee_goal(employee_id, goal_id):
    """Inline edit during approval review."""
    user = get_current_user()
    goal = Goal.query.get_or_404(goal_id)
    sheet = goal.goal_sheet
    if sheet.employee_id != employee_id:
        return jsonify({'error': 'Goal does not belong to this employee'}), 400
    if sheet.status != 'submitted':
        return jsonify({'error': 'Can only edit goals during review'}), 400

    data = request.get_json()
    old_values = goal.to_dict()

    goal.target_value = data.get('target_value', goal.target_value)
    goal.target_date = data.get('target_date', goal.target_date)
    goal.weightage = data.get('weightage', goal.weightage)
    if goal.weightage < 10:
        return jsonify({'error': 'Minimum weightage is 10%'}), 400

    db.session.commit()
    log_audit('goal', goal.id, 'updated', user.id,
              old_values=old_values, new_values=goal.to_dict(),
              description=f'Manager edited goal during review')
    db.session.commit()
    return jsonify({'goal': goal.to_dict()}), 200


@manager_bp.route('/team/<int:employee_id>/sheet/approve', methods=['POST'])
@jwt_required()
@role_required('manager', 'admin')
def approve_sheet(employee_id):
    user = get_current_user()
    cycle_id = request.get_json().get('cycle_id') if request.get_json() else None
    if not cycle_id:
        from app.models.cycle import Cycle
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    sheet = GoalSheet.query.filter_by(employee_id=employee_id, cycle_id=cycle_id).first()
    if not sheet:
        return jsonify({'error': 'No goal sheet found'}), 404
    if sheet.status != 'submitted':
        return jsonify({'error': 'Only submitted sheets can be approved'}), 400

    # Validate totals
    total = sum(g.weightage for g in sheet.goals)
    if total != 100:
        return jsonify({'error': f'Total weightage is {total}%, must be 100%'}), 400

    from app.models.notification import create_notification
    sheet.status = 'approved'
    sheet.approved_at = datetime.now(timezone.utc)
    sheet.approved_by = user.id
    db.session.commit()
    log_audit('goal_sheet', sheet.id, 'approved', user.id,
              description=f'Goal sheet approved for {sheet.employee.full_name}')
    link = "/goals"
    create_notification(sheet.employee_id, f"Your goal sheet was approved by {user.full_name}.", "✅", link=link)
    db.session.commit()
    return jsonify({'sheet': sheet.to_dict(include_goals=True)}), 200


@manager_bp.route('/team/<int:employee_id>/sheet/return', methods=['POST'])
@jwt_required()
@role_required('manager', 'admin')
def return_sheet(employee_id):
    user = get_current_user()
    data = request.get_json()
    cycle_id = data.get('cycle_id')
    if not cycle_id:
        from app.models.cycle import Cycle
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    sheet = GoalSheet.query.filter_by(employee_id=employee_id, cycle_id=cycle_id).first()
    if not sheet:
        return jsonify({'error': 'No goal sheet found'}), 404
    if sheet.status != 'submitted':
        return jsonify({'error': 'Only submitted sheets can be returned'}), 400

    from app.models.notification import create_notification
    sheet.status = 'returned'
    sheet.return_comment = data.get('comment', '')
    db.session.commit()
    log_audit('goal_sheet', sheet.id, 'returned', user.id,
              description=f'Goal sheet returned: {sheet.return_comment}')
    link = "/goals"
    create_notification(sheet.employee_id, f"Your goal sheet was returned for revision by {user.full_name}.", "⚠️", link=link)
    db.session.commit()
    return jsonify({'sheet': sheet.to_dict(include_goals=True)}), 200


@manager_bp.route('/checkin', methods=['POST'])
@jwt_required()
@role_required('manager', 'admin')
def submit_checkin():
    user = get_current_user()
    data = request.get_json()
    sheet_id = data.get('goal_sheet_id')
    quarter = data.get('quarter')
    comment = data.get('comment', '')

    sheet = GoalSheet.query.get_or_404(sheet_id)

    from app.models.notification import create_notification
    existing = CheckinRecord.query.filter_by(goal_sheet_id=sheet_id, quarter=quarter).first()
    if existing:
        existing.manager_comment = comment
        existing.checkin_date = datetime.now(timezone.utc)
        db.session.commit()
        link = f"/achievements"
        create_notification(sheet.employee_id, f"{user.full_name} provided a check-in update for {quarter.upper()}.", "📝", link=link)
        db.session.commit()
        return jsonify({'checkin': existing.to_dict()}), 200

    checkin = CheckinRecord(
        goal_sheet_id=sheet_id, quarter=quarter,
        manager_id=user.id, manager_comment=comment
    )
    db.session.add(checkin)
    db.session.commit()
    log_audit('checkin', checkin.id, 'created', user.id,
              description=f'{quarter.upper()} check-in for {sheet.employee.full_name}')
    link = f"/achievements"
    create_notification(sheet.employee_id, f"{user.full_name} provided a check-in update for {quarter.upper()}.", "📝", link=link)
    db.session.commit()
    return jsonify({'checkin': checkin.to_dict()}), 201


@manager_bp.route('/team/<int:employee_id>/checkin/<string:quarter>', methods=['GET'])
@jwt_required()
@role_required('manager', 'admin')
def get_checkin_data(employee_id, quarter):
    cycle_id = request.args.get('cycle_id', type=int)
    if not cycle_id:
        from app.models.cycle import Cycle
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    sheet = GoalSheet.query.filter_by(employee_id=employee_id, cycle_id=cycle_id).first()
    if not sheet:
        return jsonify({'error': 'No goal sheet found'}), 404

    goals_data = []
    for goal in sheet.goals:
        g = goal.to_dict()
        ach = QuarterlyAchievement.query.filter_by(
            goal_id=goal.id, quarter=quarter, cycle_id=cycle_id).first()
        g['achievement'] = ach.to_dict() if ach else None
        goals_data.append(g)

    checkin = CheckinRecord.query.filter_by(goal_sheet_id=sheet.id, quarter=quarter).first()

    return jsonify({
        'employee': User.query.get(employee_id).to_dict(),
        'goals': goals_data,
        'checkin': checkin.to_dict() if checkin else None,
        'sheet_status': sheet.status,
    }), 200
