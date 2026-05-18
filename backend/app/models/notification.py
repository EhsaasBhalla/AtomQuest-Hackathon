from app.extensions import db
from datetime import datetime, timezone

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    message = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(10), default='🔔')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    link = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        # Format relative time if we want, or just ISO
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'icon': self.icon,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

def create_notification(user_id, message, icon='🔔', link=None):
    n = Notification(user_id=user_id, message=message, icon=icon, link=link)
    db.session.add(n)
    # the caller should commit
    return n
