from app.extensions import db
from datetime import datetime, timezone


class GoalSheet(db.Model):
    __tablename__ = 'goal_sheets'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey('cycles.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='draft')
    # statuses: draft, submitted, approved, returned, locked
    submitted_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    return_comment = db.Column(db.Text, nullable=True)
    unlock_requested = db.Column(db.Boolean, default=False)
    unlock_reason = db.Column(db.Text, nullable=True)
    unlock_feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    employee = db.relationship('User', foreign_keys=[employee_id], backref='goal_sheets')
    approver = db.relationship('User', foreign_keys=[approved_by])
    goals = db.relationship('Goal', backref='goal_sheet', lazy='dynamic',
                            cascade='all, delete-orphan', order_by='Goal.order')
    checkin_records = db.relationship('CheckinRecord', backref='goal_sheet', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'cycle_id', name='uq_employee_cycle'),
    )

    @property
    def total_weightage(self):
        return sum(g.weightage for g in self.goals)

    @property
    def goal_count(self):
        return self.goals.count()

    def to_dict(self, include_goals=False):
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'employee_email': self.employee.email if self.employee else None,
            'employee_department': self.employee.department.name if self.employee and self.employee.department else None,
            'employee_designation': self.employee.designation if self.employee else None,
            'cycle_id': self.cycle_id,
            'status': self.status,
            'unlock_requested': self.unlock_requested,
            'unlock_reason': self.unlock_reason,
            'unlock_feedback': self.unlock_feedback,
            'total_weightage': self.total_weightage,
            'goal_count': self.goal_count,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by': self.approved_by,
            'approver_name': self.approver.full_name if self.approver else None,
            'return_comment': self.return_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_goals:
            data['goals'] = [g.to_dict() for g in self.goals]
            data['checkin_records'] = [c.to_dict() for c in self.checkin_records]
        return data


class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    goal_sheet_id = db.Column(db.Integer, db.ForeignKey('goal_sheets.id'), nullable=False, index=True)
    thrust_area = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    uom_type = db.Column(db.String(20), nullable=False)
    # uom_types: numeric_min, numeric_max, percent_min, percent_max, timeline, zero
    target_value = db.Column(db.Float, nullable=True)  # For numeric/percent
    target_date = db.Column(db.String(20), nullable=True)  # ISO date string for timeline
    weightage = db.Column(db.Integer, nullable=False)
    is_shared = db.Column(db.Boolean, default=False)
    shared_goal_master_id = db.Column(db.Integer, db.ForeignKey('shared_goal_masters.id'), nullable=True)
    is_title_locked = db.Column(db.Boolean, default=False)
    is_target_locked = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    achievements = db.relationship('QuarterlyAchievement', backref='goal', lazy='dynamic',
                                   cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'goal_sheet_id': self.goal_sheet_id,
            'thrust_area': self.thrust_area,
            'title': self.title,
            'description': self.description,
            'uom_type': self.uom_type,
            'target_value': self.target_value,
            'target_date': self.target_date,
            'weightage': self.weightage,
            'is_shared': self.is_shared,
            'shared_goal_master_id': self.shared_goal_master_id,
            'is_title_locked': self.is_title_locked,
            'is_target_locked': self.is_target_locked,
            'order': self.order,
            'achievements': [a.to_dict() for a in self.achievements],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SharedGoalMaster(db.Model):
    __tablename__ = 'shared_goal_masters'

    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    thrust_area = db.Column(db.String(100), nullable=False)
    uom_type = db.Column(db.String(20), nullable=False)
    target_value = db.Column(db.Float, nullable=True)
    target_date = db.Column(db.String(20), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey('cycles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    creator = db.relationship('User', backref='created_shared_goals')
    department = db.relationship('Department', backref='shared_goals')
    recipients = db.relationship('SharedGoalRecipient', backref='shared_goal_master', lazy='dynamic',
                                 cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'created_by': self.created_by,
            'creator_name': self.creator.full_name if self.creator else None,
            'title': self.title,
            'description': self.description,
            'thrust_area': self.thrust_area,
            'uom_type': self.uom_type,
            'target_value': self.target_value,
            'target_date': self.target_date,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'cycle_id': self.cycle_id,
            'recipient_count': self.recipients.count(),
            'pushed_to': [r.employee_id for r in self.recipients],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SharedGoalRecipient(db.Model):
    __tablename__ = 'shared_goal_recipients'

    id = db.Column(db.Integer, primary_key=True)
    shared_goal_master_id = db.Column(db.Integer, db.ForeignKey('shared_goal_masters.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    employee = db.relationship('User', backref='received_shared_goals')
    goal = db.relationship('Goal', backref='shared_goal_link')

    def to_dict(self):
        return {
            'id': self.id,
            'shared_goal_master_id': self.shared_goal_master_id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'goal_id': self.goal_id,
        }
