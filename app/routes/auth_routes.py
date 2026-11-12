from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


def _home_for(user):
    if user.rol == "ADMIN":
        return url_for("admin.dashboard")
    if user.rol == "PRESTADOR":
        return url_for("prestadores.mi_perfil")
    return url_for("catalogo.catalogo_publico")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))

    if request.method == "POST":
        usuario = AuthService.autenticar(
            request.form.get("email", ""),
            request.form.get("password", ""),
        )
        if not usuario:
            flash("Credenciales incorrectas o cuenta desactivada.", "danger")
        else:
            login_user(usuario, remember=bool(request.form.get("remember")))
            flash("Bienvenido al marketplace.", "success")
            return redirect(_home_for(usuario))
    return render_template("auth/login.html")


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
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
        }
        try:
            AuthService.registrar(datos)
            flash("Cuenta creada correctamente. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            from flask import current_app
            current_app.logger.exception("Error al registrar usuario")
            flash("No fue posible completar el registro.", "danger")
    return render_template("auth/registro.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("auth.login"))
