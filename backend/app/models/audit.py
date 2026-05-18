from app.extensions import db
from datetime import datetime, timezone
import json


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(30), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    old_values = db.Column(db.Text, nullable=True)
    new_values = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(300), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = db.relationship('User', backref='audit_logs')

    def set_old_values(self, data):
        self.old_values = json.dumps(data) if data else None

    def set_new_values(self, data):
        self.new_values = json.dumps(data) if data else None

    def get_old_values(self):
        return json.loads(self.old_values) if self.old_values else None

    def get_new_values(self):
        return json.loads(self.new_values) if self.new_values else None

    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'changed_by': self.changed_by,
            'changed_by_name': self.user.full_name if self.user else None,
            'old_values': self.get_old_values(),
            'new_values': self.get_new_values(),
            'description': self.description,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


def log_audit(entity_type, entity_id, action, user_id, old_values=None,
              new_values=None, description=None, ip_address=None):
    audit = AuditLog(
        entity_type=entity_type, entity_id=entity_id, action=action,
        changed_by=user_id, description=description, ip_address=ip_address,
    )
    audit.set_old_values(old_values)
    audit.set_new_values(new_values)
    db.session.add(audit)
    return audit
