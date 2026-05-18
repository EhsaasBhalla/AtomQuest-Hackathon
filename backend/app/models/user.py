from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    head_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    head = db.relationship('User', foreign_keys=[head_id], backref='headed_departments')
    members = db.relationship('User', foreign_keys='User.department_id', backref='department', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'head_id': self.head_id,
            'head_name': self.head.full_name if self.head else None,
            'member_count': self.members.count(),
        }


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # employee, manager, admin
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    avatar_color = db.Column(db.String(7), default='#3b82f6')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Self-referential relationship for manager hierarchy
    manager = db.relationship('User', remote_side=[id], backref=db.backref('direct_reports', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_reports=False):
        data = {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'manager_id': self.manager_id,
            'manager_name': self.manager.full_name if self.manager else None,
            'designation': self.designation,
            'is_active': self.is_active,
            'avatar_color': self.avatar_color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_reports:
            data['direct_reports'] = [r.to_dict() for r in self.direct_reports]
        return data
