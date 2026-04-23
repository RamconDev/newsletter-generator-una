import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv

db = SQLAlchemy()
migrate = Migrate()

from .config import ProductionConfig, DevelopmentConfig, TestingConfig
from .utils import get_reports_list

def create_app():
    app = Flask(__name__)

    CORS(app)

    env = os.getenv('FLASK_ENV', 'development')

    if env == 'development':
        app.config.from_object(DevelopmentConfig)
    elif env == 'production':
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