import os
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    DEBUG = False
    TESTING = False

    # DB settings
    SQLANCHEMY_TRACK_MODIFICATIONS = False

    URL_DB = os.getenv("URL_DB") or os.getenv("DB_ENGINE")
    SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")

    # DB_ENGINE = os.getenv("URL_DB") or os.getenv("DB_ENGINE", "sqlite")
    USER_DB = os.getenv("USER_DB")
    USER_PASSWORD = os.getenv("USER_PASSWORD")
    SERVER_DB = os.getenv("SERVER_DB")
    NAME_DB = os.getenv("NAME_DB")

    # Dinamic url
    if URL_DB and (URL_DB.startswith('postgresql') or URL_DB.startswith('postgres')):
        if URL_DB.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = URL_DB.replace("postgres://", "postgresql://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = URL_DB
    elif URL_DB and URL_DB.startswith('sqlite'):
        SQLALCHEMY_DATABASE_URI = f"{URL_DB}:///{NAME_DB}.db"  # ej: sqlite:///test.db
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///fallback.db"

        # SQLALCHEMY_DATABASE_URI = f"{URL_DB}://{USER_DB}:{USER_PASSWORD}@{SERVER_DB}/{NAME_DB}"

    ###
    #
    # 🧩 File report settings
    #
    ###
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "data")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5 * 1024 * 1024))
    ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "rep").split(','))

class DevelopmentConfig(ProductionConfig):
    DEBUG = True

class TestingConfig(ProductionConfig):
    TESTING = True
    # Using an in-memory test database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'