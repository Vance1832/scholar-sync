import os
from flask import Flask
from .extensions import db, login_manager, csrf
from config import config


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .auth import auth as auth_bp
    from .student import student as student_bp
    from .donor import donor as donor_bp
    from .admin import admin as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(donor_bp, url_prefix="/donor")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    from .models.user import User
    from .extensions import db

    if not User.query.filter_by(role="admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
