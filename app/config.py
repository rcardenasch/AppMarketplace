import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:123456@localhost:5433/App_MarketPlace"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    DEBUG = env_bool("FLASK_DEBUG", False)

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))
    MAX_CERT_FILE_SIZE = int(os.getenv("MAX_CERT_FILE_SIZE", 8 * 1024 * 1024))
    PRIVATE_UPLOAD_FOLDER = Path(
        os.getenv("PRIVATE_UPLOAD_FOLDER", str(BASE_DIR / "private_uploads"))
    ).expanduser().resolve()

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
