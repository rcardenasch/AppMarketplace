from datetime import datetime
from app.extensions.database import db

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class Auditoria(db.Model):
    __tablename__ = "auditoria"

    id = db.Column(ID_TYPE, primary_key=True)
    actor_id = db.Column(ID_TYPE, db.ForeignKey("usuarios.id", ondelete="SET NULL"))
    accion = db.Column(db.String(80), nullable=False, index=True)
    entidad = db.Column(db.String(80), nullable=False, index=True)
    entidad_id = db.Column(db.String(80), index=True)
    detalles = db.Column(db.JSON, nullable=False, default=dict)
    ip = db.Column(db.String(64))
    user_agent = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    actor = db.relationship("Usuario", foreign_keys=[actor_id])
