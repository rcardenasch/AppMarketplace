from app.extensions.database import db

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")

usuario_roles = db.Table(
    "usuario_roles",
    db.Column(
        "usuario_id",
        ID_TYPE,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "rol_id",
        ID_TYPE,
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    ),
)


class Rol(db.Model):
    __tablename__ = "roles"

    id = db.Column(ID_TYPE, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True, index=True)
    nombre = db.Column(db.String(80), nullable=False)

    usuarios = db.relationship(
        "Usuario",
        secondary=usuario_roles,
        back_populates="roles_rel",
        lazy="select",
    )

    def __repr__(self):
        return "<Rol {}>".format(self.codigo)
