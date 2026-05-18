from app.extensions import db
from datetime import datetime, timezone


class EscalationRule(db.Model):
    __tablename__ = 'escalation_rules'

    id = db.Column(db.Integer, primary_key=True)
    trigger_event = db.Column(db.String(30), nullable=False)
    days_threshold = db.Column(db.Integer, nullable=False, default=3)
    notify_employee = db.Column(db.Boolean, default=True)
    notify_manager = db.Column(db.Boolean, default=True)
    notify_hr = db.Column(db.Boolean, default=False)
    escalation_interval = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    logs = db.relationship('EscalationLog', backref='rule', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'trigger_event': self.trigger_event,
            'days_threshold': self.days_threshold,
            'notify_employee': self.notify_employee,
            'notify_manager': self.notify_manager,
            'notify_hr': self.notify_hr,
            'escalation_interval': self.escalation_interval,
            'is_active': self.is_active,
        }


class EscalationLog(db.Model):
    __tablename__ = 'escalation_logs'

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('escalation_rules.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    triggered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    level = db.Column(db.Integer, default=1)
    message = db.Column(db.String(300), nullable=True)
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)

    target_user = db.relationship('User', backref='escalation_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'trigger_event': self.rule.trigger_event if self.rule else None,
            'target_user_id': self.target_user_id,
            'target_user_name': self.target_user.full_name if self.target_user else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'level': self.level,
            'message': self.message,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
        }
