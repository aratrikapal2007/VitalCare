import os
from flask import Flask
from .db import init_db, close_db


def create_app(test_config=None):
    root = os.path.dirname(os.path.dirname(__file__))
    app = Flask(__name__, instance_relative_config=True,
                 template_folder=os.path.join(root, "templates"),
                 static_folder=os.path.join(root, "static"))
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("VITALCARE_SECRET_KEY", "local-development-secret-change-before-deployment"),
        DATABASE=os.path.join(app.instance_path, "vitalcare.db"),
        ADMIN_OVERRIDE_CODE="override-2024",
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    with app.app_context():
        init_db()
    app.teardown_appcontext(close_db)
    from .routes import bp
    app.register_blueprint(bp)
    return app
