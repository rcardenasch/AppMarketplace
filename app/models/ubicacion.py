
from datetime import datetime

from app.extensions import db

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class Ubicacion(db.Model):
    __tablename__ = "ubicaciones"

    id = db.Column(ID_TYPE, primary_key=True)

    perfil_id = db.Column(
        ID_TYPE,
        db.ForeignKey("perfil_profesional.id"),
        nullable=False,
        unique=True,
        index=True
    )

    departamento = db.Column(db.String(100), nullable=False)
    provincia = db.Column(db.String(100), nullable=False)
    distrito = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(250))
    referencia = db.Column(db.String(250))
    latitud = db.Column(db.Numeric(10, 7))
    longitud = db.Column(db.Numeric(10, 7))

    radio_atencion_km = db.Column(
        db.Numeric(6, 2),
        nullable=False,
        default=10
    )

    activo = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    perfil = db.relationship(
        "PerfilProfesional",
        backref=db.backref(
            "ubicacion",
            uselist=False,
            cascade="all, delete-orphan"
        )
    )

    def __repr__(self):
        return f"<Ubicacion {self.distrito}, {self.provincia}>"
