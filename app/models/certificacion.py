from datetime import datetime
from app.extensions.database import db

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class Certificacion(db.Model):
    __tablename__ = "certificaciones"

    id = db.Column(ID_TYPE, primary_key=True)
    perfil_id = db.Column(
        ID_TYPE, db.ForeignKey("perfil_profesional.id"), nullable=False, index=True
    )
    tipo = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    documento_path = db.Column(db.String(500))
    documento_nombre = db.Column(db.String(255))
    documento_mime = db.Column(db.String(120))
    estado = db.Column(db.String(20), nullable=False, default="PENDIENTE", index=True)
    fecha_emision = db.Column(db.Date)
    fecha_vencimiento = db.Column(db.Date)
    observaciones = db.Column(db.Text)
    observaciones_admin = db.Column(db.Text)
    evaluador_id = db.Column(ID_TYPE, db.ForeignKey("usuarios.id"), nullable=True)
    evaluado_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    perfil = db.relationship("PerfilProfesional", back_populates="certificaciones")
    evaluador = db.relationship("Usuario", foreign_keys=[evaluador_id])
