
from app.extensions.database import db
from pgvector.sqlalchemy import Vector


class Demanda(db.Model):

    __tablename__ = "demandas"

    id = db.Column(db.BigInteger, primary_key=True)

    cliente_id = db.Column(
        db.BigInteger,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    categoria_id = db.Column(
        db.BigInteger,
        db.ForeignKey("categorias.id"),
        nullable=False
    )

    titulo = db.Column(db.String(200), nullable=False)

    descripcion = db.Column(db.Text, nullable=False)

    embedding = db.Column(Vector(384))

    ciudad = db.Column(db.String(100), nullable=False)

    distrito = db.Column(db.String(100), nullable=False)

    estado = db.Column(
        db.String(25),
        default="PUBLICADA"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
