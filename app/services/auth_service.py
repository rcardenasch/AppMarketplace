from app.extensions.database import db
from app.models import Categoria, IdentidadOAuth, PerfilProfesional, Usuario


class AuthService:
    ROLES_PUBLICOS = {"CLIENTE", "PRESTADOR"}

    @staticmethod
    def autenticar(email, password):
        email = (email or "").strip().lower()
        password = password or ""
        if not email or not password:
            return None
        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario or not usuario.activo or not usuario.check_password(password):
            return None
        return usuario

    @staticmethod
    def _validar_datos_prestador(datos):
        try:
            experiencia = int(datos.get("experiencia_anios") or 0)
        except (TypeError, ValueError):
            raise ValueError("Los años de experiencia deben ser un número entero.")
        if experiencia < 0 or experiencia > 60:
            raise ValueError("Los años de experiencia deben estar entre 0 y 60.")
        ciudad = (datos.get("ciudad") or "Ayacucho").strip()
        if not ciudad:
            raise ValueError("La ciudad del prestador es obligatoria.")
        return experiencia, ciudad

    @staticmethod
    def _categorias_activas(categoria_ids):
        if not categoria_ids:
            return []
        try:
            ids = list({int(value) for value in categoria_ids})
        except (TypeError, ValueError):
            raise ValueError("Una de las categorías seleccionadas no es válida.")
        categorias = Categoria.query.filter(
            Categoria.id.in_(ids), Categoria.activo.is_(True)
        ).all()
        if len(categorias) != len(ids):
            raise ValueError("Selecciona únicamente categorías activas.")
        return categorias

    @classmethod
    def _crear_perfil_prestador(cls, usuario, datos=None):
        datos = datos or {}
        experiencia, ciudad = cls._validar_datos_prestador(datos)
        categorias = cls._categorias_activas(datos.get("categoria_ids") or [])
        perfil = usuario.perfil_profesional
        if perfil is None:
            descripcion = (
                datos.get("descripcion")
                or "Perfil profesional pendiente de completar."
            ).strip()
            embedding = None
            if len(descripcion) >= 10 and not descripcion.lower().startswith("perfil profesional pendiente"):
                from app.services.embedding_service import EmbeddingService
                embedding = EmbeddingService.generar_embedding(descripcion)
            perfil = PerfilProfesional(
                usuario_id=usuario.id,
                descripcion=descripcion,
                embedding=embedding,
                experiencia_anios=experiencia,
                ciudad=ciudad,
                distrito=(datos.get("distrito") or "").strip() or None,
                estado="PENDIENTE",
                certificado=False,
            )
            db.session.add(perfil)
            db.session.flush()
        if categorias:
            perfil.categorias = categorias
        return perfil

    @classmethod
    def registrar(cls, datos):
        nombres = (datos.get("nombres") or "").strip()
        apellidos = (datos.get("apellidos") or "").strip()
        email = (datos.get("email") or "").strip().lower()
        password = datos.get("password") or ""
        rol = (datos.get("rol") or "CLIENTE").upper()

        if not nombres or not apellidos:
            raise ValueError("Ingresa nombres y apellidos.")
        if not email or "@" not in email:
            raise ValueError("Ingresa un correo electrónico válido.")
        if rol not in cls.ROLES_PUBLICOS:
            raise ValueError("Rol de registro no permitido.")
        if len(password) < 10:
            raise ValueError("La contraseña debe tener al menos 10 caracteres.")
        if Usuario.query.filter_by(email=email).first():
            raise ValueError("Ya existe una cuenta con ese correo. Inicia sesión y agrega el otro modo desde tu cuenta.")
        if rol == "PRESTADOR":
            descripcion = (datos.get("descripcion") or "").strip()
            if len(descripcion) < 10:
                raise ValueError("Describe tu experiencia y los servicios que ofreces (mínimo 10 caracteres).")
            if not datos.get("categoria_ids"):
                raise ValueError("Selecciona al menos una especialidad para tu perfil de prestador.")

        try:
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
            usuario.add_role(rol)

            if rol == "PRESTADOR":
                cls._crear_perfil_prestador(usuario, datos)

            db.session.commit()
            return usuario
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def agregar_rol(cls, usuario, rol, datos=None):
        rol = (rol or "").upper()
        datos = datos or {}
        if rol not in cls.ROLES_PUBLICOS:
            raise ValueError("Solo puedes agregar los roles CLIENTE o PRESTADOR.")
        if rol == "PRESTADOR" and not usuario.has_role("PRESTADOR"):
            if len((datos.get("descripcion") or "").strip()) < 10:
                raise ValueError("Describe tu experiencia y los servicios que ofreces (mínimo 10 caracteres).")
            if not datos.get("categoria_ids"):
                raise ValueError("Selecciona al menos una especialidad para tu perfil de prestador.")
        try:
            if usuario.has_role(rol):
                if rol == "PRESTADOR" and usuario.perfil_profesional is None:
                    cls._crear_perfil_prestador(usuario, datos)
                    db.session.commit()
                    return usuario
                raise ValueError("Tu cuenta ya tiene ese rol habilitado.")

            usuario.add_role(rol)
            if rol == "PRESTADOR":
                cls._crear_perfil_prestador(usuario, datos)
            db.session.commit()
            return usuario
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def registrar_google(cls, userinfo, rol="CLIENTE"):
        email = (userinfo.get("email") or "").strip().lower()
        subject = userinfo.get("sub")
        if not email or not subject or userinfo.get("email_verified") is not True:
            raise ValueError("Google no devolvió un correo verificado.")
        rol = (rol or "CLIENTE").upper()
        if rol not in cls.ROLES_PUBLICOS:
            rol = "CLIENTE"
        if Usuario.query.filter_by(email=email).first():
            raise ValueError(
                "Ya existe una cuenta con este correo. Inicia sesión con tu método actual y agrega Google desde tu cuenta."
            )

        nombre = (userinfo.get("given_name") or userinfo.get("name") or "Usuario").strip()
        apellido = (userinfo.get("family_name") or "").strip()
        if not apellido:
            partes = nombre.split()
            if len(partes) > 1:
                nombre, apellido = partes[0], " ".join(partes[1:])
            else:
                apellido = "Google"

        try:
            usuario = Usuario(
                nombres=nombre[:100],
                apellidos=apellido[:100],
                email=email,
                telefono=None,
                password_hash=None,
                rol=rol,
                activo=True,
            )
            db.session.add(usuario)
            db.session.flush()
            usuario.add_role(rol)
            db.session.add(IdentidadOAuth(
                usuario_id=usuario.id,
                proveedor="google",
                proveedor_usuario_id=str(subject),
                email_proveedor=email,
            ))
            if rol == "PRESTADOR":
                cls._crear_perfil_prestador(usuario)
            db.session.commit()
            return usuario
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def vincular_google(usuario, userinfo):
        email = (userinfo.get("email") or "").strip().lower()
        subject = userinfo.get("sub")
        if not subject or userinfo.get("email_verified") is not True:
            raise ValueError("No se pudo verificar la identidad de Google.")
        if email != (usuario.email or "").strip().lower():
            raise ValueError("La cuenta Google debe utilizar el mismo correo de tu cuenta del Marketplace.")

        identidad = IdentidadOAuth.query.filter_by(
            proveedor="google", proveedor_usuario_id=str(subject)
        ).first()
        if identidad:
            if identidad.usuario_id == usuario.id:
                return identidad
            raise ValueError("Esta cuenta Google ya está vinculada a otro usuario.")

        try:
            identidad = IdentidadOAuth(
                usuario_id=usuario.id,
                proveedor="google",
                proveedor_usuario_id=str(subject),
                email_proveedor=email,
            )
            db.session.add(identidad)
            db.session.commit()
            return identidad
        except Exception:
            db.session.rollback()
            raise
