

from app.extensions.database import db

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class PerfilCategoria(db.Model):

    __tablename__ = "perfil_categorias"

    id = db.Column(ID_TYPE, primary_key=True)

    perfil_id = db.Column(
        ID_TYPE,
        db.ForeignKey("perfil_profesional.id"),
        nullable=False
    )

    categoria_id = db.Column(
        ID_TYPE,
        db.ForeignKey("categorias.id"),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint("perfil_id", "categoria_id", name="uq_perfil_categoria"),
    )