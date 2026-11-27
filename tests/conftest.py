import pytest
from pathlib import Path
from app import create_app
from app.extensions.database import db


@pytest.fixture()
def app(tmp_path):
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test-secret-key"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        WTF_CSRF_ENABLED = False
        MAX_CONTENT_LENGTH = 10 * 1024 * 1024
        MAX_CERT_FILE_SIZE = 8 * 1024 * 1024
        PRIVATE_UPLOAD_FOLDER = Path(tmp_path) / "private_uploads"
        SESSION_COOKIE_SECURE = False

    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
