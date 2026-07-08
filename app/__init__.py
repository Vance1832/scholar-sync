import os
from flask import Flask
from .extensions import db, login_manager, csrf, mail
from config import config


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    from .main import main as main_bp
    from .auth import auth as auth_bp
    from .student import student as student_bp
    from .donor import donor as donor_bp
    from .admin import admin as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(donor_bp, url_prefix="/donor")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        db.create_all()
        _migrate_schema()
        _seed_admin()

    _register_error_handlers(app)
    _register_cli(app)

    @app.context_processor
    def inject_globals():
        from datetime import date
        return {"current_year": date.today().year}

    return app


def _register_cli(app: Flask) -> None:
    import click

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Populate the database with realistic demo data for portfolio demos."""
        from .seed_demo import seed_demo
        seed_demo()

    @app.cli.command("set-admin-password")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def set_admin_password_command(password):
        """Reset the admin account password (prompts securely)."""
        from .models.user import User
        from .extensions import db

        admin = User.query.filter_by(role="admin").first()
        if not admin:
            click.echo("No admin account exists yet — it is seeded on first app start.")
            return
        if len(password) < 8:
            click.echo("Password must be at least 8 characters.")
            return
        admin.set_password(password)
        db.session.commit()
        click.echo(f"Password updated for admin user '{admin.username}'.")


def _migrate_schema() -> None:
    from sqlalchemy import text
    from .extensions import db

    migrations = [
        "ALTER TABLE applications ADD COLUMN star_rating INTEGER",
        "ALTER TABLE applications ADD COLUMN personal_statement TEXT",
        "ALTER TABLE applications ADD COLUMN financial_need TEXT",
        "ALTER TABLE applications ADD COLUMN intended_use TEXT",
        "ALTER TABLE applications ADD COLUMN rejection_reason TEXT",
        "ALTER TABLE applications ADD COLUMN reviewer_notes TEXT",
        "ALTER TABLE applications ADD COLUMN date_reviewed TIMESTAMP",
        "ALTER TABLE scholarships ADD COLUMN effort_level VARCHAR(16) DEFAULT 'essay'",
        "ALTER TABLE awards ADD COLUMN recipient_account VARCHAR(512)",
        "ALTER TABLE awards ADD COLUMN disbursement_proof TEXT",
        "ALTER TABLE awards ADD COLUMN student_accepted BOOLEAN DEFAULT FALSE",
        "ALTER TABLE awards ADD COLUMN student_payment_info TEXT",
        "ALTER TABLE awards ADD COLUMN accepted_at TIMESTAMP",
        "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE",
    ]

    for sql in migrations:
        try:
            db.session.execute(text(sql))
            db.session.commit()
        except Exception:
            db.session.rollback()


def _register_error_handlers(app: Flask) -> None:
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500


def _seed_admin():
    """Create the initial admin account.

    The password comes from the ADMIN_PASSWORD env var; if unset, a random
    one is generated and printed to the console once. There is deliberately
    no hardcoded default — this repo is public.
    """
    import secrets
    from .models.user import User
    from .extensions import db

    if not User.query.filter_by(role="admin").first():
        password = os.environ.get("ADMIN_PASSWORD")
        if not password:
            password = secrets.token_urlsafe(12)
            print(f" * Seeded admin account — username 'admin', password: {password}")
            print(" * (set the ADMIN_PASSWORD env var to choose it yourself)")
        admin = User(username="admin", role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
