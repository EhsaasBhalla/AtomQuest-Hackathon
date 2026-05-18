from flask import Flask
from flask_cors import CORS
from app.extensions import db, jwt, migrate, cache
from app.config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.employee import employee_bp
    from app.routes.manager import manager_bp
    from app.routes.admin import admin_bp
    from app.routes.shared_goals import shared_goals_bp
    from app.routes.reports import reports_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(employee_bp, url_prefix='/api/goals')
    app.register_blueprint(manager_bp, url_prefix='/api/manager')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(shared_goals_bp, url_prefix='/api/shared-goals')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    # Create tables
    with app.app_context():
        from app.models import user, goal, checkin, cycle, audit, escalation  # noqa
        db.create_all()

    return app
