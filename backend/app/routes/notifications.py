from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.notification import Notification
from app.utils.decorators import get_current_user

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    user = get_current_user()
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify({'notifications': [n.to_dict() for n in notifs]}), 200

@notifications_bp.route('/read', methods=['POST'])
@jwt_required()
def mark_read():
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({Notification.is_read: True})
    db.session.commit()
    return jsonify({'message': 'Marked as read'}), 200

@notifications_bp.route('/clear', methods=['POST'])
@jwt_required()
def clear_notifications():
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return jsonify({'message': 'Cleared'}), 200
