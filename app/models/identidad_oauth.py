from datetime import datetime

from app.extensions.database import db

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class IdentidadOAuth(db.Model):
    __tablename__ = "identidades_oauth"

    id = db.Column(ID_TYPE, primary_key=True)
    usuario_id = db.Column(
        ID_TYPE,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proveedor = db.Column(db.String(30), nullable=False)
    proveedor_usuario_id = db.Column(db.String(255), nullable=False)
    email_proveedor = db.Column(db.String(150), nullable=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    usuario = db.relationship("Usuario", back_populates="identidades_oauth")

    __table_args__ = (
        db.UniqueConstraint(
            "proveedor", "proveedor_usuario_id",
            name="uq_identidad_oauth_proveedor_usuario",
        ),
    )
