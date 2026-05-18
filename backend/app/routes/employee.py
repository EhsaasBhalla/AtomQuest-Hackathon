from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.goal import GoalSheet, Goal
from app.models.checkin import QuarterlyAchievement
from app.models.cycle import Cycle, CycleWindow
from app.models.audit import log_audit
from app.utils.decorators import get_current_user

employee_bp = Blueprint('employee', __name__)


@employee_bp.route('/sheet', methods=['GET'])
@jwt_required()
def get_goal_sheet():
    user = get_current_user()
    cycle_id = request.args.get('cycle_id', type=int)
    if not cycle_id:
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None
    if not cycle_id:
        return jsonify({'error': 'No active cycle found'}), 404

    sheet = GoalSheet.query.filter_by(employee_id=user.id, cycle_id=cycle_id).first()
    
    # Also fetch the cycle to get its windows
    cycle_obj = Cycle.query.get(cycle_id)
    windows = [w.to_dict() for w in cycle_obj.windows] if cycle_obj else []

    if not sheet:
        return jsonify({'sheet': None, 'cycle_id': cycle_id, 'windows': windows}), 200
    return jsonify({'sheet': sheet.to_dict(include_goals=True), 'windows': windows}), 200


@employee_bp.route('/sheet', methods=['POST'])
@jwt_required()
def create_goal_sheet():
    user = get_current_user()
    data = request.get_json()
    cycle_id = data.get('cycle_id')
    if not cycle_id:
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None
    if not cycle_id:
        return jsonify({'error': 'No active cycle'}), 400

    existing = GoalSheet.query.filter_by(employee_id=user.id, cycle_id=cycle_id).first()
    if existing:
        return jsonify({'error': 'Goal sheet already exists for this cycle'}), 409

    sheet = GoalSheet(employee_id=user.id, cycle_id=cycle_id, status='draft')
    db.session.add(sheet)
    db.session.commit()
    log_audit('goal_sheet', sheet.id, 'created', user.id, description='Goal sheet created')
    db.session.commit()
    return jsonify({'sheet': sheet.to_dict(include_goals=True)}), 201


@employee_bp.route('/sheet/<int:sheet_id>/goals', methods=['POST'])
@jwt_required()
def add_goal(sheet_id):
    user = get_current_user()
    sheet = GoalSheet.query.get_or_404(sheet_id)
    if sheet.employee_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    if sheet.status not in ('draft', 'returned'):
        return jsonify({'error': 'Cannot add goals to a locked/submitted sheet'}), 400
    if sheet.goal_count >= 8:
        return jsonify({'error': 'Maximum 8 goals allowed per sheet'}), 400

    data = request.get_json()
    weightage = data.get('weightage', 0)
    if weightage < 10:
        return jsonify({'error': 'Minimum weightage per goal is 10%'}), 400

    goal = Goal(
        goal_sheet_id=sheet_id,
        thrust_area=data.get('thrust_area', ''),
        title=data.get('title', ''),
        description=data.get('description', ''),
        uom_type=data.get('uom_type', 'numeric_min'),
        target_value=data.get('target_value'),
        target_date=data.get('target_date'),
        weightage=weightage,
        order=sheet.goal_count,
    )
    db.session.add(goal)
    db.session.commit()
    log_audit('goal', goal.id, 'created', user.id,
              new_values=goal.to_dict(), description=f'Goal "{goal.title}" created')
    db.session.commit()
    return jsonify({'goal': goal.to_dict()}), 201


@employee_bp.route('/goals/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    user = get_current_user()
    goal = Goal.query.get_or_404(goal_id)
    sheet = goal.goal_sheet
    if sheet.employee_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    if sheet.status not in ('draft', 'returned'):
        return jsonify({'error': 'Cannot edit goals on a locked sheet'}), 400

    data = request.get_json()
    old_values = goal.to_dict()

    if not goal.is_title_locked:
        goal.thrust_area = data.get('thrust_area', goal.thrust_area)
        goal.title = data.get('title', goal.title)
        goal.description = data.get('description', goal.description)
    if not goal.is_target_locked:
        goal.uom_type = data.get('uom_type', goal.uom_type)
        goal.target_value = data.get('target_value', goal.target_value)
        goal.target_date = data.get('target_date', goal.target_date)

    new_weightage = data.get('weightage', goal.weightage)
    if new_weightage < 10:
        return jsonify({'error': 'Minimum weightage is 10%'}), 400
    goal.weightage = new_weightage

    db.session.commit()
    log_audit('goal', goal.id, 'updated', user.id,
              old_values=old_values, new_values=goal.to_dict())
    db.session.commit()
    return jsonify({'goal': goal.to_dict()}), 200


@employee_bp.route('/goals/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    user = get_current_user()
    goal = Goal.query.get_or_404(goal_id)
    sheet = goal.goal_sheet
    if sheet.employee_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    if sheet.status not in ('draft', 'returned', 'approved'):
        return jsonify({'error': 'Cannot delete goals on a locked sheet'}), 400

    log_audit('goal', goal.id, 'deleted', user.id,
              old_values=goal.to_dict(), description=f'Goal "{goal.title}" deleted')
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'message': 'Goal deleted'}), 200


@employee_bp.route('/sheet/<int:sheet_id>/submit', methods=['POST'])
@jwt_required()
def submit_sheet(sheet_id):
    user = get_current_user()
    sheet = GoalSheet.query.get_or_404(sheet_id)
    if sheet.employee_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    if sheet.status not in ('draft', 'returned'):
        return jsonify({'error': 'Sheet cannot be submitted in current state'}), 400

    # Validate: total weightage == 100
    total = sum(g.weightage for g in sheet.goals)
    if total != 100:
        return jsonify({'error': f'Total weightage must be 100%. Current: {total}%'}), 400
    # Validate: max 8 goals
    if sheet.goal_count > 8:
        return jsonify({'error': 'Maximum 8 goals allowed'}), 400
    # Validate: min 10% each
    for g in sheet.goals:
        if g.weightage < 10:
            return jsonify({'error': f'Goal "{g.title}" has weightage below 10%'}), 400

    from datetime import datetime, timezone
    from app.models.notification import create_notification
    sheet.status = 'submitted'
    sheet.submitted_at = datetime.now(timezone.utc)
    sheet.return_comment = None
    db.session.commit()
    log_audit('goal_sheet', sheet.id, 'submitted', user.id, description='Goal sheet submitted for approval')
    if user.manager_id:
        link = f"/team/{user.id}/review"
        create_notification(user.manager_id, f"{user.full_name} submitted their goal sheet for approval.", "📄", link=link)
    db.session.commit()
    return jsonify({'sheet': sheet.to_dict(include_goals=True)}), 200


@employee_bp.route('/achievements', methods=['POST'])
@jwt_required()
def log_achievement():
    user = get_current_user()
    data = request.get_json()
    goal_id = data.get('goal_id')
    quarter = data.get('quarter')

    goal = Goal.query.get_or_404(goal_id)
    sheet = goal.goal_sheet
    if sheet.employee_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    if sheet.status != 'approved':
        return jsonify({'error': 'Goals must be approved before logging achievements'}), 400

    # Check if window is open
    cycle = Cycle.query.get(sheet.cycle_id)
    phase_map = {'q1': 'q1_checkin', 'q2': 'q2_checkin', 'q3': 'q3_checkin', 'q4': 'q4_annual'}
    window = CycleWindow.query.filter_by(cycle_id=cycle.id, phase=phase_map.get(quarter, '')).first()
    if window and not window.is_open:
        return jsonify({'error': f'The {quarter.upper()} check-in window is not currently open'}), 400

    existing = QuarterlyAchievement.query.filter_by(
        goal_id=goal_id, quarter=quarter, cycle_id=sheet.cycle_id).first()
    if existing:
        old = existing.to_dict()
        existing.actual_achievement = data.get('actual_achievement', existing.actual_achievement)
        existing.actual_date = data.get('actual_date', existing.actual_date)
        existing.status = data.get('status', existing.status)
        existing.planned_target = data.get('planned_target', goal.target_value)
        existing.compute_score(goal.uom_type, goal.target_value, goal.target_date)
        db.session.commit()
        log_audit('achievement', existing.id, 'updated', user.id, old_values=old, new_values=existing.to_dict())
        db.session.commit()
        _sync_shared_achievement(goal, quarter, sheet.cycle_id, existing)
        return jsonify({'achievement': existing.to_dict()}), 200

    achievement = QuarterlyAchievement(
        goal_id=goal_id, quarter=quarter, cycle_id=sheet.cycle_id,
        planned_target=data.get('planned_target', goal.target_value),
        actual_achievement=data.get('actual_achievement'),
        actual_date=data.get('actual_date'),
        status=data.get('status', 'not_started'),
    )
    achievement.compute_score(goal.uom_type, goal.target_value, goal.target_date)
    db.session.add(achievement)
    db.session.commit()
    log_audit('achievement', achievement.id, 'created', user.id, new_values=achievement.to_dict())
    db.session.commit()
    _sync_shared_achievement(goal, quarter, sheet.cycle_id, achievement)
    return jsonify({'achievement': achievement.to_dict()}), 201


def _sync_shared_achievement(goal, quarter, cycle_id, source_ach):
    """Sync achievement data across all recipients of the same shared goal."""
    if not goal.shared_goal_master_id:
        return
    from app.models.goal import SharedGoalRecipient
    siblings = SharedGoalRecipient.query.filter(
        SharedGoalRecipient.shared_goal_master_id == goal.shared_goal_master_id,
        SharedGoalRecipient.goal_id != goal.id
    ).all()
    for sib in siblings:
        existing = QuarterlyAchievement.query.filter_by(
            goal_id=sib.goal_id, quarter=quarter, cycle_id=cycle_id).first()
        if existing:
            existing.actual_achievement = source_ach.actual_achievement
            existing.actual_date = source_ach.actual_date
            existing.status = source_ach.status
            existing.computed_score = source_ach.computed_score
        else:
            synced = QuarterlyAchievement(
                goal_id=sib.goal_id, quarter=quarter, cycle_id=cycle_id,
                planned_target=source_ach.planned_target,
                actual_achievement=source_ach.actual_achievement,
                actual_date=source_ach.actual_date,
                status=source_ach.status,
                computed_score=source_ach.computed_score,
            )
            db.session.add(synced)
    db.session.commit()


@employee_bp.route('/sheet/<int:sheet_id>/achievements', methods=['GET'])
@jwt_required()
def get_sheet_achievements(sheet_id):
    user = get_current_user()
    sheet = GoalSheet.query.get_or_404(sheet_id)
    quarter = request.args.get('quarter')
    result = []
    for goal in sheet.goals:
        g_data = goal.to_dict()
        if quarter:
            achs = QuarterlyAchievement.query.filter_by(goal_id=goal.id, quarter=quarter).all()
        else:
            achs = QuarterlyAchievement.query.filter_by(goal_id=goal.id).all()
        g_data['achievements'] = [a.to_dict() for a in achs]
        result.append(g_data)
    return jsonify({'goals': result}), 200
