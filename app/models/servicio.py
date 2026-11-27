from datetime import datetime
from app.extensions.database import db

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class Servicio(db.Model):
    __tablename__ = "servicios"

    id = db.Column(ID_TYPE, primary_key=True)
    categoria_id = db.Column(ID_TYPE, db.ForeignKey("categorias.id"), nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    precio_referencial = db.Column(db.Numeric(10, 2))
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    categoria = db.relationship("Categoria", back_populates="servicios")
