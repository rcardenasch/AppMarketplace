
from app.extensions.database import db


class Matching(db.Model):

    __tablename__ = "matches"

    id = db.Column(db.BigInteger, primary_key=True)

    demanda_id = db.Column(
        db.BigInteger,
        db.ForeignKey("demandas.id"),
        nullable=False
    )

    perfil_id = db.Column(
        db.BigInteger,
        db.ForeignKey("perfil_profesional.id"),
        nullable=False
    )

    similitud = db.Column(db.Numeric(8, 6))

    score = db.Column(db.Numeric(8, 6))

    estado = db.Column(
        db.String(20),
        default="PENDIENTE"
    )
