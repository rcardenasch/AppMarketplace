from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app, session,
)
from flask_login import login_user, logout_user, login_required, current_user

from app.models import Categoria, IdentidadOAuth, Usuario
from app.services.auth_service import AuthService
from app.extensions.oauth import oauth

auth_bp = Blueprint("auth", __name__)


def _home_for(user):
    if user.has_role("ADMIN"):
        return url_for("admin.dashboard")
    rol_activo = session.get("rol_activo")
    if rol_activo not in user.roles_codigos:
        rol_activo = user.rol
    if rol_activo == "PRESTADOR" and user.has_role("PRESTADOR"):
        return url_for("prestadores.mi_perfil")
    return url_for("catalogo.catalogo_publico")


def _google_client():
    if not current_app.config.get("GOOGLE_CLIENT_ID") or not current_app.config.get("GOOGLE_CLIENT_SECRET"):
        flash("El acceso con Google todavía no está configurado.", "warning")
        return None
    google = oauth.create_client("google")
    if google is None:
        current_app.logger.error("El cliente OAuth de Google no fue registrado.")
        flash("No se pudo inicializar el acceso con Google. Revisa la configuración del servidor.", "danger")
        return None
    return google


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    if request.method == "POST":
        usuario = AuthService.autenticar(
            request.form.get("email", ""), request.form.get("password", "")
        )
        if not usuario:
            flash("Credenciales incorrectas o cuenta desactivada.", "danger")
        else:
            session["rol_activo"] = usuario.rol
            login_user(usuario, remember=bool(request.form.get("remember")))
            flash("Bienvenido al marketplace.", "success")
            return redirect(_home_for(usuario))
    return render_template("auth/login.html")


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    if request.method == "POST":
        datos = {
            "nombres": request.form.get("nombres", ""),
            "apellidos": request.form.get("apellidos", ""),
            "email": request.form.get("email", ""),
            "telefono": request.form.get("telefono", ""),
            "password": request.form.get("password", ""),
            "rol": request.form.get("rol", "CLIENTE"),
            "descripcion": request.form.get("descripcion", ""),
            "experiencia_anios": request.form.get("experiencia_anios", 0),
            "ciudad": request.form.get("ciudad", "Ayacucho"),
            "distrito": request.form.get("distrito", ""),
            "categoria_ids": request.form.getlist("categoria_ids", type=int),
        }
        try:
            usuario = AuthService.registrar(datos)
            session["rol_activo"] = usuario.rol
            flash("Cuenta creada correctamente. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            current_app.logger.exception("Error al registrar usuario")
            flash("No fue posible completar el registro.", "danger")
    return render_template("auth/registro.html", categorias=categorias)


@auth_bp.get("/google")
def google_login():
    google = _google_client()
    if google is None:
        return redirect(url_for("auth.login"))
    rol = (request.args.get("rol") or "CLIENTE").upper()
    session["google_rol"] = rol if rol in AuthService.ROLES_PUBLICOS else "CLIENTE"
    session["google_action"] = "login"
    return google.authorize_redirect(url_for("auth.google_callback", _external=True))


@auth_bp.get("/google/link")
@login_required
def google_link():
    google = _google_client()
    if google is None:
        return redirect(_home_for(current_user))
    session["google_action"] = "link"
    return google.authorize_redirect(url_for("auth.google_callback", _external=True))


@auth_bp.get("/google/callback")
def google_callback():
    google = _google_client()
    if google is None:
        return redirect(url_for("auth.login"))
    try:
        token = google.authorize_access_token()
        userinfo = token.get("userinfo")
        if not userinfo:
            response = google.get("userinfo")
            response.raise_for_status()
            userinfo = response.json()

        email = (userinfo.get("email") or "").strip().lower()
        subject = userinfo.get("sub")
        if not email or not subject or userinfo.get("email_verified") is not True:
            raise ValueError("Google no devolvió una identidad con correo verificado.")

        action = session.pop("google_action", "login")
        rol = session.pop("google_rol", "CLIENTE")
        if action == "link":
            if not current_user.is_authenticated:
                flash("Inicia sesión antes de vincular una cuenta externa.", "warning")
                return redirect(url_for("auth.login"))
            AuthService.vincular_google(current_user, userinfo)
            flash("Tu cuenta de Google quedó vinculada correctamente.", "success")
            return redirect(_home_for(current_user))

        identidad = IdentidadOAuth.query.filter_by(
            proveedor="google", proveedor_usuario_id=str(subject)
        ).first()
        if identidad:
            usuario = identidad.usuario
            if not usuario or not usuario.activo:
                flash("La cuenta está desactivada o no disponible.", "danger")
                return redirect(url_for("auth.login"))
        else:
            usuario = Usuario.query.filter_by(email=email).first()
            if usuario:
                flash(
                    "Este correo ya tiene una cuenta. Inicia sesión con tu método actual y agrega Google desde tu cuenta.",
                    "warning",
                )
                return redirect(url_for("auth.login"))
            usuario = AuthService.registrar_google(userinfo, rol=rol)

        if not usuario.activo:
            flash("Tu cuenta está desactivada. Contacta con administración.", "danger")
            return redirect(url_for("auth.login"))
        if rol in usuario.roles_codigos:
            session["rol_activo"] = rol
        elif session.get("rol_activo") not in usuario.roles_codigos:
            session["rol_activo"] = usuario.rol
        login_user(usuario)
        flash("Has iniciado sesión con Google.", "success")
        return redirect(_home_for(usuario))
    except ValueError as exc:
        current_app.logger.warning("Autenticación Google no completada: %s", exc)
        flash(str(exc), "warning")
    except Exception:
        current_app.logger.exception("Error en callback de Google")
        flash("No fue posible completar la autenticación con Google.", "danger")
    return redirect(url_for("auth.login"))


@auth_bp.route("/roles", methods=["GET", "POST"])
@login_required
def gestionar_roles():
    if request.method == "POST":
        rol = (request.form.get("rol") or "").upper()
        datos = {
            "descripcion": request.form.get("descripcion", ""),
            "experiencia_anios": request.form.get("experiencia_anios", 0),
            "ciudad": request.form.get("ciudad", "Ayacucho"),
            "distrito": request.form.get("distrito", ""),
            "categoria_ids": request.form.getlist("categoria_ids", type=int),
        }
        try:
            AuthService.agregar_rol(current_user, rol, datos)
            session["rol_activo"] = rol
            flash("El modo {} se habilitó correctamente.".format(rol.lower()), "success")
            return redirect(_home_for(current_user))
        except ValueError as exc:
            flash(str(exc), "warning")
        except Exception:
            current_app.logger.exception("No fue posible agregar el rol")
            flash("No fue posible actualizar los roles de tu cuenta.", "danger")

    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    return render_template("auth/roles.html", categorias=categorias)


@auth_bp.post("/cambiar-rol")
@login_required
def cambiar_rol():
    rol = (request.form.get("rol") or "").upper()
    if not current_user.has_role(rol):
        flash("Tu cuenta no tiene habilitado ese modo.", "danger")
        return redirect(url_for("auth.gestionar_roles"))
    session["rol_activo"] = rol
    flash("Cambiaste al modo {}.".format(rol.lower()), "success")
    return redirect(_home_for(current_user))


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    session.pop("rol_activo", None)
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("auth.login"))
