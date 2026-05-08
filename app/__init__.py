import logging
import os

from flask import Flask

from .extensions import cors, db
from .config import ProductionConfig, DevelopmentConfig, TestingConfig
from .errors import register_error_handlers, api_success


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _validate_secrets(app):
    weak = {'secret_key', 'jwt_secret_key', ''}
    secret = app.config.get('SECRET_KEY', '')
    jwt_secret = app.config.get('JWT_SECRET_KEY', '')
    if not secret or secret in weak or len(secret) < 16:
        raise RuntimeError(
            "SECRET_KEY must be a strong, unique value (min 16 chars). "
            "Set it in your .env file."
        )
    if not jwt_secret or jwt_secret in weak or len(jwt_secret) < 16:
        raise RuntimeError(
            "JWT_SECRET_KEY must be a strong, unique value (min 16 chars). "
            "Set it in your .env file."
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
        _validate_secrets(app)
    elif env == 'production':
        _db_url = ProductionConfig.DATABASE_URL
        if not _db_url:
            raise RuntimeError("DATABASE_URL environment variable is required in Production")
        if not _db_url.startswith("postgresql"):
            raise RuntimeError("DATABASE_URL must be a PostgreSQL URI (postgresql://...)")
        app.config.from_object(ProductionConfig)
        _validate_secrets(app)
    elif env == 'testing':
        app.config.from_object(TestingConfig)

    db.init_app(app)
    from app.auth.models import User, Role, roles_users
    from app.auth.models.revoked_token import RevokedToken
    from app.models import Major, Student, Subject, Grade

    from .blueprints import register_blueprints
    register_blueprints(app)

    from app.auth import login_manager
    login_manager.init_app(app)

    register_error_handlers(app)

    @app.route("/")
    def index():
        return api_success(
            data={"app": "Newsletter Generator UNA", "version": "1.0"},
            mensaje="API operativa.",
        )

    return app
