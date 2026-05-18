from app.extensions import db
from datetime import datetime, date, timezone


class Cycle(db.Model):
    __tablename__ = 'cycles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "FY 2026-27"
    year = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    windows = db.relationship('CycleWindow', backref='cycle', lazy='dynamic',
                              cascade='all, delete-orphan', order_by='CycleWindow.opens_at')

    def to_dict(self, include_windows=False):
        data = {
            'id': self.id,
            'name': self.name,
            'year': self.year,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_windows:
            data['windows'] = [w.to_dict() for w in self.windows]
        return data


class CycleWindow(db.Model):
    __tablename__ = 'cycle_windows'

    id = db.Column(db.Integer, primary_key=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey('cycles.id'), nullable=False, index=True)
    phase = db.Column(db.String(20), nullable=False)
    # phases: goal_setting, q1_checkin, q2_checkin, q3_checkin, q4_annual
    phase_label = db.Column(db.String(50), nullable=False)  # Human-readable label
    opens_at = db.Column(db.Date, nullable=False)
    closes_at = db.Column(db.Date, nullable=False)

    @property
    def is_open(self):
        today = date.today()
        return self.opens_at <= today <= self.closes_at

    @property
    def status(self):
        today = date.today()
        if today < self.opens_at:
            return 'upcoming'
        elif today > self.closes_at:
            return 'closed'
        return 'active'

    def to_dict(self):
        return {
            'id': self.id,
            'cycle_id': self.cycle_id,
            'phase': self.phase,
            'phase_label': self.phase_label,
            'opens_at': self.opens_at.isoformat() if self.opens_at else None,
            'closes_at': self.closes_at.isoformat() if self.closes_at else None,
            'is_open': self.is_open,
            'status': self.status,
        }
