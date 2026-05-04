from flask import Flask
import os

from .extensions import cors, db, migrate

from .config import ProductionConfig, DevelopmentConfig, TestingConfig
from .reports.services import get_reports_list

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

    # Import models
    from app.auth.models import User, Role, roles_users
    from app.models import Major, Student, Subject, Grade

    # Register blueprints
    from .blueprints import register_blueprints
    register_blueprints(app)
    
    @app.route("/")
    def index():
        files_reports = get_reports_list()
        return f"Initialiced App! { files_reports }"
    
    return app

def read_reports():
    pass