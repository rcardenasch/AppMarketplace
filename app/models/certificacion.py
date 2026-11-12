
from app.extensions.database import db


class Certificacion(db.Model):

    __tablename__ = "certificaciones"

    id = db.Column(db.BigInteger, primary_key=True)

    perfil_id = db.Column(
        db.BigInteger,
        db.ForeignKey("perfil_profesional.id"),
        nullable=False
    )

    tipo = db.Column(db.String(100), nullable=False)

    estado = db.Column(db.String(20), nullable=False)

    fecha_vencimiento = db.Column(db.Date)
