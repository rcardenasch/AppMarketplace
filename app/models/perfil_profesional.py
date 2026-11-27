from datetime import datetime

from app.extensions.database import db
from pgvector.sqlalchemy import Vector

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class PerfilProfesional(db.Model):

    __tablename__ = "perfil_profesional"
    id = db.Column(ID_TYPE, primary_key=True)
    usuario_id = db.Column(
        ID_TYPE,
        db.ForeignKey("usuarios.id"),
        unique=True,
        nullable=False
    )
    descripcion = db.Column(db.Text, nullable=False)
    embedding = db.Column(Vector(384))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    experiencia_anios = db.Column(db.Integer, nullable=False, default=0)
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

    estado = db.Column(db.String(20), default="PENDIENTE")

    usuario = db.relationship("Usuario", back_populates="perfil_profesional")
    categorias = db.relationship(
        "Categoria",
        secondary="perfil_categorias",
        back_populates="perfiles"
    )
    certificaciones = db.relationship(
        "Certificacion",
        back_populates="perfil",
        cascade="all, delete-orphan",
        order_by="desc(Certificacion.created_at)"
    )
