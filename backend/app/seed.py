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

    # Admin
    admin = User(email='admin@company.com', full_name='Priya Sharma',
                 role='admin', department_id=hr.id, designation='HR Director',
                 avatar_color='#8b5cf6')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.flush()

    # Managers
    mgr1 = User(email='manager@company.com', full_name='Rajesh Kumar',
                role='manager', department_id=eng.id, designation='Engineering Manager',
                avatar_color='#0ea5e9')
    mgr1.set_password('manager123')
    db.session.add(mgr1)

    mgr2 = User(email='manager2@company.com', full_name='Anita Desai',
                role='manager', department_id=sales.id, designation='Sales Manager',
                avatar_color='#f43f5e')
    mgr2.set_password('manager123')
    db.session.add(mgr2)
    db.session.flush()

    # Employees under mgr1 (Engineering)
    employees_eng = [
        ('employee1@company.com', 'Amit Patel', '#10b981'),
        ('employee2@company.com', 'Sneha Reddy', '#f59e0b'),
        ('employee3@company.com', 'Vikram Singh', '#6366f1'),
    ]
    for email, name, color in employees_eng:
        emp = User(email=email, full_name=name, role='employee',
                   department_id=eng.id, manager_id=mgr1.id,
                   designation='Software Engineer', avatar_color=color)
        emp.set_password('emp123')
        db.session.add(emp)

    # Employees under mgr2 (Sales)
    employees_sales = [
        ('employee4@company.com', 'Meera Nair', '#ec4899'),
        ('employee5@company.com', 'Arjun Gupta', '#14b8a6'),
    ]
    for email, name, color in employees_sales:
        emp = User(email=email, full_name=name, role='employee',
                   department_id=sales.id, manager_id=mgr2.id,
                   designation='Sales Executive', avatar_color=color)
        emp.set_password('emp123')
        db.session.add(emp)

    db.session.commit()

    # Set department heads
    eng.head_id = mgr1.id
    sales.head_id = mgr2.id
    hr.head_id = admin.id
    db.session.commit()
    print("  [OK] Users created")


def seed_cycles():
    if Cycle.query.first():
        return
    cycle = Cycle(name='FY 2026-27', year=2026, is_active=True)
    db.session.add(cycle)
    db.session.flush()

    windows = [
        ('goal_setting', 'Phase 1 - Goal Setting', '2026-05-01', '2026-06-30'),
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
    """Create sample goal sheets in various states for demo."""
    cycle = Cycle.query.filter_by(is_active=True).first()
    if not cycle:
        return
    emp1 = User.query.filter_by(email='employee1@company.com').first()
    emp2 = User.query.filter_by(email='employee2@company.com').first()
    emp3 = User.query.filter_by(email='employee3@company.com').first()
    mgr = User.query.filter_by(email='manager@company.com').first()
    if not emp1 or GoalSheet.query.filter_by(employee_id=emp1.id).first():
        return

    # Employee 1: Approved sheet with Q1 achievements
    sheet1 = GoalSheet(employee_id=emp1.id, cycle_id=cycle.id, status='approved',
                       submitted_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
                       approved_at=datetime(2026, 5, 18, tzinfo=timezone.utc),
                       approved_by=mgr.id)
    db.session.add(sheet1)
    db.session.flush()

    goals1 = [
        Goal(goal_sheet_id=sheet1.id, thrust_area='Revenue Growth',
             title='Increase quarterly sales pipeline', description='Build and maintain sales pipeline worth 2x quota',
             uom_type='numeric_min', target_value=200, weightage=30, order=0),
        Goal(goal_sheet_id=sheet1.id, thrust_area='Product Quality',
             title='Reduce critical bugs by 40%', description='Identify and fix critical bugs in production',
             uom_type='percent_max', target_value=40, weightage=25, order=1),
        Goal(goal_sheet_id=sheet1.id, thrust_area='Innovation',
             title='Deliver AI-powered feature module', description='Design and ship the ML recommendation engine',
             uom_type='timeline', target_date='2026-12-31', weightage=25, order=2),
        Goal(goal_sheet_id=sheet1.id, thrust_area='Operational Excellence',
             title='Zero production incidents', description='Maintain zero P1 incidents in production',
             uom_type='zero', target_value=0, weightage=20, order=3),
    ]
    db.session.add_all(goals1)
    db.session.flush()

    # Add Q1 achievements for emp1
    achievements = [
        QuarterlyAchievement(goal_id=goals1[0].id, quarter='q1', cycle_id=cycle.id,
                             planned_target=200, actual_achievement=165, status='on_track', computed_score=82.5),
        QuarterlyAchievement(goal_id=goals1[1].id, quarter='q1', cycle_id=cycle.id,
                             planned_target=40, actual_achievement=28, status='on_track', computed_score=70.0),
        QuarterlyAchievement(goal_id=goals1[2].id, quarter='q1', cycle_id=cycle.id,
                             planned_target=None, actual_achievement=None, status='on_track', computed_score=None),
        QuarterlyAchievement(goal_id=goals1[3].id, quarter='q1', cycle_id=cycle.id,
                             planned_target=0, actual_achievement=0, status='completed', computed_score=100.0),
    ]
    db.session.add_all(achievements)

    # Add check-in record for emp1 Q1
    checkin1 = CheckinRecord(goal_sheet_id=sheet1.id, quarter='q1', manager_id=mgr.id,
                             manager_comment='Good progress on sales pipeline. Bug reduction needs acceleration. Keep up the momentum on the AI module.',
                             checkin_date=datetime(2026, 7, 20, tzinfo=timezone.utc))
    db.session.add(checkin1)

    # Employee 2: Submitted (pending approval)
    sheet2 = GoalSheet(employee_id=emp2.id, cycle_id=cycle.id, status='submitted',
                       submitted_at=datetime(2026, 5, 20, tzinfo=timezone.utc))
    db.session.add(sheet2)
    db.session.flush()

    goals2 = [
        Goal(goal_sheet_id=sheet2.id, thrust_area='Customer Satisfaction',
             title='Achieve NPS score of 85+', description='Improve customer satisfaction through better support',
             uom_type='numeric_min', target_value=85, weightage=35, order=0),
        Goal(goal_sheet_id=sheet2.id, thrust_area='Revenue Growth',
             title='Onboard 50 enterprise clients', description='Close deals with enterprise-tier clients',
             uom_type='numeric_min', target_value=50, weightage=35, order=1),
        Goal(goal_sheet_id=sheet2.id, thrust_area='Operational Excellence',
             title='Complete compliance training', description='100% team compliance training completion',
             uom_type='percent_min', target_value=100, weightage=30, order=2),
    ]
    db.session.add_all(goals2)

    # Employee 3: Draft
    sheet3 = GoalSheet(employee_id=emp3.id, cycle_id=cycle.id, status='draft')
    db.session.add(sheet3)
    db.session.flush()

    goals3 = [
        Goal(goal_sheet_id=sheet3.id, thrust_area='Innovation',
             title='Launch internal developer portal', description='Build and launch a self-service dev portal',
             uom_type='timeline', target_date='2026-09-30', weightage=40, order=0),
        Goal(goal_sheet_id=sheet3.id, thrust_area='Product Quality',
             title='Improve test coverage to 90%', description='Increase unit test coverage across all modules',
             uom_type='percent_min', target_value=90, weightage=30, order=1),
    ]
    db.session.add_all(goals3)

    db.session.commit()
    print("  [OK] Demo goal sheets created")
