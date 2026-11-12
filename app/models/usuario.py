
from app.extensions.database import db


class Usuario(db.Model):

    __tablename__ = "usuarios"

    id = db.Column(db.BigInteger, primary_key=True)

    nombres = db.Column(db.String(100), nullable=False)

    apellidos = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(150), unique=True)

    rol = db.Column(db.String(20), nullable=False)

    activo = db.Column(db.Boolean, default=True)
