from app.extensions.database import db, migrate
from app.extensions.login_manager import login_manager
from app.extensions.csrf import csrf

__all__ = ["db", "migrate", "login_manager", "csrf", "oauth"]
from app.extensions.oauth import oauth
