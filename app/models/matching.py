from app.extensions.database import db

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class Matching(db.Model):
    __tablename__ = "matches"

    id = db.Column(ID_TYPE, primary_key=True)
    demanda_id = db.Column(
        ID_TYPE, db.ForeignKey("demandas.id"), nullable=False, index=True
    )
    perfil_id = db.Column(
        ID_TYPE,
        db.ForeignKey("perfil_profesional.id"),
        nullable=False,
        index=True,
    )
    similitud = db.Column(db.Numeric(8, 6))
    reputacion = db.Column(db.Numeric(8, 6))
    proximidad = db.Column(db.Numeric(8, 6))
    distancia_km = db.Column(db.Numeric(10, 3))
    score = db.Column(db.Numeric(8, 6))
    estado = db.Column(db.String(20), default="PENDIENTE", index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("demanda_id", "perfil_id", name="uq_match_demanda_perfil"),
    )
