"""Seed database with demo data for hackathon evaluation."""
from app.extensions import db
from app.models.user import User, Department
from app.models.cycle import Cycle, CycleWindow
from app.models.goal import GoalSheet, Goal, SharedGoalMaster, SharedGoalRecipient
from app.models.checkin import QuarterlyAchievement, CheckinRecord
from app.models.escalation import EscalationRule
from datetime import date, datetime, timezone


def seed_all():
    """Run all seed functions."""
    print("[SEED] Seeding database...")
    seed_departments()
    seed_users()
    seed_cycles()
    seed_escalation_rules()
    seed_demo_goals()
    print("[SEED] Seeding complete!")


def seed_departments():
    if Department.query.first():
        return
    depts = [
        Department(name='Engineering'),
        Department(name='Sales'),
        Department(name='Human Resources'),
        Department(name='Marketing'),
    ]
    db.session.add_all(depts)
    db.session.commit()
    print("  [OK] Departments created")


def seed_users():
    if User.query.first():
        return
    eng = Department.query.filter_by(name='Engineering').first()
    sales = Department.query.filter_by(name='Sales').first()
    hr = Department.query.filter_by(name='Human Resources').first()

    # Admin / HR — Priya Sharma
    admin = User(email='admin@company.com', full_name='Priya Sharma',
                 role='admin', department_id=hr.id, designation='HR Director',
                 avatar_color='#8b5cf6')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.flush()

    # Manager — Rajesh Kumar (Engineering)
    mgr = User(email='manager@company.com', full_name='Rajesh Kumar',
               role='manager', department_id=eng.id, designation='Engineering Manager',
               avatar_color='#0ea5e9')
    mgr.set_password('manager123')
    db.session.add(mgr)
    db.session.flush()

    # Employee — Amit Patel (under Rajesh)
    emp = User(email='employee@company.com', full_name='Amit Patel',
               role='employee', department_id=eng.id, manager_id=mgr.id,
               designation='Software Engineer', avatar_color='#10b981')
    emp.set_password('emp123')
    db.session.add(emp)

    db.session.commit()

    # Set department heads
    eng.head_id = mgr.id
    hr.head_id = admin.id
    db.session.commit()
    print("  [OK] Users created (3 demo accounts)")


def seed_cycles():
    if Cycle.query.first():
        return
    cycle = Cycle(name='FY 2026-27', year=2026, is_active=True)
    db.session.add(cycle)
    db.session.flush()

    # Windows per problem statement schedule:
    # Goal Setting: May 1 – June 30
    # Q1 Check-in: July (progress update)
    # Q2 Check-in: October (progress update)
    # Q3 Check-in: January (progress update)
    # Q4 / Annual Review: March – April (final achievement capture)
    windows = [
        ('goal_setting', 'Goal Setting', '2026-05-01', '2026-06-30'),
        ('q1_checkin', 'Q1 Check-in', '2026-07-01', '2026-07-31'),
        ('q2_checkin', 'Q2 Check-in', '2026-10-01', '2026-10-31'),
        ('q3_checkin', 'Q3 Check-in', '2027-01-01', '2027-01-31'),
        ('q4_annual', 'Q4 / Annual Review', '2027-03-01', '2027-04-30'),
    ]
    for phase, label, opens, closes in windows:
        w = CycleWindow(cycle_id=cycle.id, phase=phase, phase_label=label,
                        opens_at=date.fromisoformat(opens),
                        closes_at=date.fromisoformat(closes))
        db.session.add(w)
    db.session.commit()
    print("  [OK] Cycle & windows created")


def seed_escalation_rules():
    if EscalationRule.query.first():
        return
    rules = [
        EscalationRule(trigger_event='goal_not_submitted', days_threshold=7,
                       notify_employee=True, notify_manager=True, notify_hr=False,
                       escalation_interval=3),
        EscalationRule(trigger_event='goal_not_approved', days_threshold=5,
                       notify_employee=False, notify_manager=True, notify_hr=True,
                       escalation_interval=3),
        EscalationRule(trigger_event='checkin_overdue', days_threshold=7,
                       notify_employee=True, notify_manager=True, notify_hr=True,
                       escalation_interval=5),
    ]
    db.session.add_all(rules)
    db.session.commit()
    print("  [OK] Escalation rules created")


def seed_demo_goals():
    """Create sample goal sheets with realistic demo data for evaluation."""
    cycle = Cycle.query.filter_by(is_active=True).first()
    if not cycle:
        return
    emp = User.query.filter_by(email='employee@company.com').first()
    mgr = User.query.filter_by(email='manager@company.com').first()
    if not emp or GoalSheet.query.filter_by(employee_id=emp.id).first():
        return

    # Employee: Approved sheet with 4 goals (weightage = 100%)
    sheet = GoalSheet(employee_id=emp.id, cycle_id=cycle.id, status='approved',
                      submitted_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
                      approved_at=datetime(2026, 5, 18, tzinfo=timezone.utc),
                      approved_by=mgr.id)
    db.session.add(sheet)
    db.session.flush()

    goals = [
        Goal(goal_sheet_id=sheet.id, thrust_area='Revenue Growth',
             title='Increase quarterly sales pipeline',
             description='Build and maintain sales pipeline worth 2x of quarterly quota through outreach and relationship management',
             uom_type='numeric_min', target_value=200, weightage=30, order=0),
        Goal(goal_sheet_id=sheet.id, thrust_area='Product Quality',
             title='Reduce critical production bugs by 40%',
             description='Identify, triage, and fix critical P1/P2 bugs reported by customers in the production environment',
             uom_type='percent_max', target_value=40, weightage=25, order=1),
        Goal(goal_sheet_id=sheet.id, thrust_area='Innovation',
             title='Deliver AI-powered recommendation module',
             description='Design, develop, and ship the ML-based recommendation engine for the platform by end of year',
             uom_type='timeline', target_date='2026-12-31', weightage=25, order=2),
        Goal(goal_sheet_id=sheet.id, thrust_area='Operational Excellence',
             title='Maintain zero P1 production incidents',
             description='Ensure zero critical production incidents through proactive monitoring and code reviews',
             uom_type='zero', target_value=0, weightage=20, order=3),
    ]
    db.session.add_all(goals)
    db.session.flush()

    db.session.commit()
    print("  [OK] Demo goal sheet created for employee")
