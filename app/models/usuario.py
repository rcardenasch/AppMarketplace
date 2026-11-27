from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions.database import db
from app.models.rol import Rol, usuario_roles

ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(ID_TYPE, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    # NULL se permite para cuentas creadas exclusivamente con Google.
    password_hash = db.Column(db.String(255), nullable=True)
    # Se conserva como rol principal por compatibilidad con datos y módulos antiguos.
    # La pertenencia real a uno o varios roles está en usuario_roles.
    rol = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    perfil_profesional = db.relationship(
        "PerfilProfesional", back_populates="usuario", uselist=False
    )
    identidades_oauth = db.relationship(
        "IdentidadOAuth",
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy=True,
    )
    roles_rel = db.relationship(
        "Rol",
        secondary=usuario_roles,
        back_populates="usuarios",
        lazy="selectin",
    )

    def set_password(self, password):
        if not password:
            raise ValueError("La contraseña es obligatoria.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not password or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return bool(self.activo)

    @property
    def nombre_completo(self):
        return "{} {}".format(self.nombres, self.apellidos).strip()

    @property
    def roles_codigos(self):
        codigos = {rol.codigo for rol in self.roles_rel}
        if self.rol:
            codigos.add(self.rol.upper())
        return codigos

    def has_role(self, codigo):
        codigo = (codigo or "").upper()
        return codigo in self.roles_codigos

    def add_role(self, codigo):
        codigo = (codigo or "").upper()
        if not codigo:
            raise ValueError("El rol es obligatorio.")
        rol = Rol.query.filter_by(codigo=codigo).first()
        if rol is None:
            nombres = {
                "ADMIN": "Administrador",
                "CLIENTE": "Cliente",
                "PRESTADOR": "Prestador de servicios",
            }
            rol = Rol(codigo=codigo, nombre=nombres.get(codigo, codigo.title()))
            db.session.add(rol)
            db.session.flush()
        if all(item.codigo != codigo for item in self.roles_rel):
            self.roles_rel.append(rol)
        return rol

    def __repr__(self):
        return "<Usuario {}>".format(self.email)
