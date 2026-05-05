import os
from dotenv import load_dotenv

load_dotenv()


def _normalize_pg_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+pg8000://", 1)
    return url


class BaseConfig:
    DEBUG = False
    TESTING = False

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")

    # JWT settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt_secret_key")
    JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", 1))
    JWT_REFRESH_EXP_HOURS = int(os.getenv("JWT_REFRESH_EXP_HOURS", JWT_EXP_HOURS * 2))

    # File report settings
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "data")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5 * 1024 * 1024))
    ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "rep").split(','))


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

    # Prefer a single DATABASE_URL env var. Backwards compatible fallbacks: URL_DB or DB_ENGINE.
    DATABASE_URL = _normalize_pg_url(
        os.getenv("DATABASE_URL") or os.getenv("URL_DB") or os.getenv("DB_ENGINE")
    )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or ""


class DevelopmentConfig(BaseConfig):
    DEBUG = True

    DATABASE_URL = _normalize_pg_url(
        os.getenv("DATABASE_URL") or os.getenv("URL_DB") or os.getenv("DB_ENGINE")
    )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///dev.db"


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"