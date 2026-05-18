from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.goal import GoalSheet, Goal
from app.models.checkin import QuarterlyAchievement, CheckinRecord
from app.models.cycle import Cycle
from app.models.user import User, Department
from app.utils.decorators import role_required
import csv
import io

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/achievement', methods=['GET'])
@jwt_required()
@role_required('admin', 'manager')
def achievement_report():
    cycle_id = request.args.get('cycle_id', type=int)
    fmt = request.args.get('format', 'json')
    department_id = request.args.get('department_id', type=int)

    if not cycle_id:
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    query = GoalSheet.query.filter_by(cycle_id=cycle_id)
    if department_id:
        emp_ids = [u.id for u in User.query.filter_by(department_id=department_id)]
        query = query.filter(GoalSheet.employee_id.in_(emp_ids))

    sheets = query.all()
    rows = []
    for sheet in sheets:
        for goal in sheet.goals:
            for q in ['q1', 'q2', 'q3', 'q4']:
                ach = QuarterlyAchievement.query.filter_by(
                    goal_id=goal.id, quarter=q, cycle_id=cycle_id).first()
                rows.append({
                    'employee_name': sheet.employee.full_name,
                    'employee_email': sheet.employee.email,
                    'department': sheet.employee.department.name if sheet.employee.department else '',
                    'goal_title': goal.title,
                    'thrust_area': goal.thrust_area,
                    'uom_type': goal.uom_type,
                    'weightage': goal.weightage,
                    'quarter': q.upper(),
                    'planned_target': ach.planned_target if ach else goal.target_value,
                    'actual_achievement': ach.actual_achievement if ach else None,
                    'status': ach.status if ach else 'not_started',
                    'score': ach.computed_score if ach else None,
                })

    if fmt == 'csv':
        if not rows:
            return Response('No data', mimetype='text/csv')
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=achievement_report.csv'}
        )

    return jsonify({'report': rows, 'total': len(rows)}), 200


@reports_bp.route('/completion-status', methods=['GET'])
@jwt_required()
@role_required('admin', 'manager')
def completion_status():
    cycle_id = request.args.get('cycle_id', type=int)
    if not cycle_id:
        cycle = Cycle.query.filter_by(is_active=True).first()
        cycle_id = cycle.id if cycle else None

    employees = User.query.filter_by(role='employee', is_active=True).all()
    result = []
    for emp in employees:
        sheet = GoalSheet.query.filter_by(employee_id=emp.id, cycle_id=cycle_id).first()
        checkins = {}
        if sheet:
            for q in ['q1', 'q2', 'q3', 'q4']:
                cr = CheckinRecord.query.filter_by(goal_sheet_id=sheet.id, quarter=q).first()
                has_achievements = QuarterlyAchievement.query.filter(
                    QuarterlyAchievement.goal_id.in_([g.id for g in sheet.goals]),
                    QuarterlyAchievement.quarter == q
                ).count() > 0
                checkins[q] = {
                    'achievement_entered': has_achievements,
                    'manager_checkin': cr is not None,
                }
        result.append({
            'employee': emp.to_dict(),
            'sheet_status': sheet.status if sheet else 'not_started',
            'checkins': checkins,
        })

    return jsonify({'employees': result}), 200
