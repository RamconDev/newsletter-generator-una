import logging
import os

from flask import Flask

from .extensions import cors, db, migrate
from .config import ProductionConfig, DevelopmentConfig, TestingConfig
from .errors import register_error_handlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app():
    app = Flask(__name__)

    cors.init_app(app)

    env = os.getenv('FLASK_ENV', 'development')

    if env == 'development':
        _db_url = DevelopmentConfig.DATABASE_URL
        if not _db_url:
            raise RuntimeError("DATABASE_URL environment variable is required in Development")
        if not _db_url.startswith("postgresql"):
            raise RuntimeError("DATABASE_URL must be a PostgreSQL URI (postgresql://...)")
        app.config.from_object(DevelopmentConfig)
    elif env == 'production':
        _db_url = ProductionConfig.DATABASE_URL
        if not _db_url:
            raise RuntimeError("DATABASE_URL environment variable is required in Production")
        if not _db_url.startswith("postgresql"):
            raise RuntimeError("DATABASE_URL must be a PostgreSQL URI (postgresql://...)")
        app.config.from_object(ProductionConfig)
    elif env == 'testing':
        app.config.from_object(TestingConfig)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.auth.models import User, Role, roles_users
    from app.models import Major, Student, Subject, Grade

    from .blueprints import register_blueprints
    register_blueprints(app)

    register_error_handlers(app)

    @app.route("/")
    def index():
        from app.reports.services import get_reports_list
        return f"Initialized App! {get_reports_list()}"

    return app
