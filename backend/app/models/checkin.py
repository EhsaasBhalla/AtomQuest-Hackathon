from app.extensions import db
from datetime import datetime, timezone


class QuarterlyAchievement(db.Model):
    __tablename__ = 'quarterly_achievements'

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False, index=True)
    quarter = db.Column(db.String(5), nullable=False)  # q1, q2, q3, q4
    cycle_id = db.Column(db.Integer, db.ForeignKey('cycles.id'), nullable=False)
    planned_target = db.Column(db.Float, nullable=True)
    actual_achievement = db.Column(db.Float, nullable=True)
    actual_date = db.Column(db.String(20), nullable=True)  # For timeline UoM
    status = db.Column(db.String(20), nullable=False, default='not_started')
    # statuses: not_started, on_track, completed
    computed_score = db.Column(db.Float, nullable=True)  # 0-100
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('goal_id', 'quarter', 'cycle_id', name='uq_goal_quarter_cycle'),
    )

    def compute_score(self, uom_type, target_value=None, target_date=None):
        """Compute progress score based on UoM type."""
        if uom_type == 'zero':
            # Zero = Success: If actual is 0, score is 100%, else 0%
            self.computed_score = 100.0 if (self.actual_achievement is not None and self.actual_achievement == 0) else 0.0
        elif uom_type in ('numeric_min', 'percent_min'):
            # Higher is better: Achievement / Target * 100
            if target_value and target_value > 0 and self.actual_achievement is not None:
                self.computed_score = min(round((self.actual_achievement / target_value) * 100, 2), 100.0)
            else:
                self.computed_score = 0.0
        elif uom_type in ('numeric_max', 'percent_max'):
            # Lower is better: Target / Achievement * 100
            if self.actual_achievement and self.actual_achievement > 0 and target_value is not None:
                self.computed_score = min(round((target_value / self.actual_achievement) * 100, 2), 100.0)
            else:
                self.computed_score = 0.0 if self.actual_achievement else 100.0
        elif uom_type == 'timeline':
            # Date-based: If completed on or before deadline, 100%
            if self.actual_date and target_date:
                self.computed_score = 100.0 if self.actual_date <= target_date else 0.0
            else:
                self.computed_score = 0.0
        return self.computed_score

    def to_dict(self):
        return {
            'id': self.id,
            'goal_id': self.goal_id,
            'quarter': self.quarter,
            'cycle_id': self.cycle_id,
            'planned_target': self.planned_target,
            'actual_achievement': self.actual_achievement,
            'actual_date': self.actual_date,
            'status': self.status,
            'computed_score': self.computed_score,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CheckinRecord(db.Model):
    __tablename__ = 'checkin_records'

    id = db.Column(db.Integer, primary_key=True)
    goal_sheet_id = db.Column(db.Integer, db.ForeignKey('goal_sheets.id'), nullable=False, index=True)
    quarter = db.Column(db.String(5), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    manager_comment = db.Column(db.Text, nullable=True)
    checkin_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    employee_acknowledged = db.Column(db.Boolean, default=False)

    # Relationships
    manager = db.relationship('User', backref='checkin_records')

    __table_args__ = (
        db.UniqueConstraint('goal_sheet_id', 'quarter', name='uq_goalsheet_quarter_checkin'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'goal_sheet_id': self.goal_sheet_id,
            'quarter': self.quarter,
            'manager_id': self.manager_id,
            'manager_name': self.manager.full_name if self.manager else None,
            'manager_comment': self.manager_comment,
            'checkin_date': self.checkin_date.isoformat() if self.checkin_date else None,
            'employee_acknowledged': self.employee_acknowledged,
        }
