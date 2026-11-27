
from datetime import datetime

from app.extensions.database import db


class Certificacion(db.Model):

    __tablename__ = "certificaciones"

    id = db.Column(db.Integer, primary_key=True)

    perfil_id = db.Column(
        db.Integer,
        db.ForeignKey("perfil_profesional.id"),
        nullable=False
    )

    tipo = db.Column(db.String(100), nullable=False)
    
    estado = db.Column(db.String(50), nullable=False, default="PENDIENTE")  # PENDIENTE, APROBADA, RECHAZADA
    fecha_emision = db.Column(db.Date)
    fecha_vencimiento = db.Column(db.Date)
    observaciones = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    evaluador_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    perfil = db.relationship("PerfilProfesional", back_populates="certificaciones")