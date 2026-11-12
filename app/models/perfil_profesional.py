
from app.extensions.database import db
from pgvector.sqlalchemy import Vector


class PerfilProfesional(db.Model):

    __tablename__ = "perfil_profesional"

    id = db.Column(db.BigInteger, primary_key=True)

    usuario_id = db.Column(
        db.BigInteger,
        db.ForeignKey("usuarios.id"),
        unique=True,
        nullable=False
    )

    descripcion = db.Column(db.Text, nullable=False)

    embedding = db.Column(Vector(384))

    ciudad = db.Column(db.String(100), nullable=False)

    distrito = db.Column(db.String(100))

    puntuacion = db.Column(db.Numeric(3, 2), default=0)

    trabajos_completados = db.Column(
        db.Integer,
        default=0
    )

    certificado = db.Column(
        db.Boolean,
        default=False
    )

    estado = db.Column(
        db.String(20),
        default="PENDIENTE"
    )

    usuario = db.relationship("Usuario")
