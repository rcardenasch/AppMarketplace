
from app.extensions.database import db


class PerfilCategoria(db.Model):

    __tablename__ = "perfil_categorias"

    id = db.Column(db.BigInteger, primary_key=True)

    perfil_id = db.Column(
        db.BigInteger,
        db.ForeignKey("perfil_profesional.id"),
        nullable=False
    )

    categoria_id = db.Column(
        db.BigInteger,
        db.ForeignKey("categorias.id"),
        nullable=False
    )
