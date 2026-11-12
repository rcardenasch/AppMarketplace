
from app.extensions.database import db


class Categoria(db.Model):

    __tablename__ = "categorias"

    id = db.Column(db.BigInteger, primary_key=True)

    nombre = db.Column(db.String(100), nullable=False)

    slug = db.Column(db.String(120), unique=True)
