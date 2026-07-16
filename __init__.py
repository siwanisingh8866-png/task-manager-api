import os
from flask import Flask

from .db import init_db


def create_app(test_config=None):
    """Application factory."""
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-me"),
        DATABASE=os.path.join(app.instance_path, "task_manager.sqlite3"),
        JWT_EXPIRES_MINUTES=int(os.environ.get("JWT_EXPIRES_MINUTES", "60")),
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    init_db(app)

    from .routes.auth import auth_bp
    from .routes.tasks import tasks_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}, 200

    return app
