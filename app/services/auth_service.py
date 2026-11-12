from app.extensions.database import db
from app.models import Usuario, PerfilProfesional


class AuthService:
    ROLES_PUBLICOS = {"CLIENTE", "PRESTADOR"}

    @staticmethod
    def autenticar(email, password):
        usuario = Usuario.query.filter_by(email=(email or "").strip().lower()).first()
        if not usuario or not usuario.check_password(password or ""):
            return None
        if not usuario.activo:
            return None
        return usuario

    @staticmethod
    def registrar(datos):
        nombres = (datos.get("nombres") or "").strip()
        apellidos = (datos.get("apellidos") or "").strip()
        email = (datos.get("email") or "").strip().lower()
        password = datos.get("password") or ""
        rol = (datos.get("rol") or "CLIENTE").upper()

        if not nombres or not apellidos:
            raise ValueError("Ingresa nombres y apellidos.")
        if not email or "@" not in email:
            raise ValueError("Ingresa un correo electrónico válido.")
        if rol not in AuthService.ROLES_PUBLICOS:
            raise ValueError("Rol de registro no permitido.")
        if len(password) < 10:
            raise ValueError("La contraseña debe tener al menos 10 caracteres.")
        if Usuario.query.filter_by(email=email).first():
            raise ValueError("Ya existe una cuenta con ese correo.")

        try:
            experiencia = int(datos.get("experiencia_anios") or 0)
        except (TypeError, ValueError):
            raise ValueError("Los años de experiencia deben ser un número entero.")
        if experiencia < 0 or experiencia > 60:
            raise ValueError("Los años de experiencia deben estar entre 0 y 60.")

        usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            telefono=(datos.get("telefono") or "").strip() or None,
            rol=rol,
            activo=True,
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.flush()

        if rol == "PRESTADOR":
            perfil = PerfilProfesional(
                usuario_id=usuario.id,
                descripcion=(datos.get("descripcion") or "").strip(),
                experiencia_anios=experiencia,
                ciudad=(datos.get("ciudad") or "Ayacucho").strip(),
                distrito=(datos.get("distrito") or "").strip() or None,
                estado="PENDIENTE",
                certificado=False,
            )
            db.session.add(perfil)

        db.session.commit()
        return usuario
