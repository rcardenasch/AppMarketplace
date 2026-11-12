import click
from flask import Flask, redirect, url_for, render_template, request, jsonify
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from app.config import Config
from app.extensions.database import db, migrate
from app.extensions.login_manager import login_manager
from app.extensions.csrf import csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        try:
            return db.session.get(Usuario, int(user_id))
        except (TypeError, ValueError):
            return None

    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.prestadores_routes import prestadores_bp
    from app.routes.certificaciones_routes import certificaciones_bp
    from app.routes.catalogo_routes import catalogo_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(prestadores_bp)
    app.register_blueprint(certificaciones_bp)
    app.register_blueprint(catalogo_bp)

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            if current_user.rol == "ADMIN":
                return redirect(url_for("admin.dashboard"))
            if current_user.rol == "PRESTADOR":
                return redirect(url_for("prestadores.mi_perfil"))
            return redirect(url_for("catalogo.catalogo_publico"))
        return redirect(url_for("auth.login"))

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        message = "La sesión del formulario venció o el token CSRF no es válido. Recarga la página e inténtalo nuevamente."
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "message": message}), 400
        return render_template("errors/csrf.html", message=message), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(error):
        message = "El archivo supera el tamaño máximo permitido."
        if request.is_json:
            return jsonify({"ok": False, "message": message}), 413
        return render_template("errors/413.html", message=message), 413

    @app.cli.command("certificaciones-vencidas")
    def sincronizar_certificaciones_vencidas():
        """Marca como vencidas las certificaciones cuya fecha ya pasó."""
        from app.services.certificacion_service import CertificacionService
        total = CertificacionService.sincronizar_vencimientos()
        click.echo(f"Certificaciones actualizadas: {total}")

    @app.cli.command("crear-admin")
    @click.option("--email", prompt="Correo del administrador")
    @click.option("--nombres", prompt="Nombres")
    @click.option("--apellidos", prompt="Apellidos")
    def crear_admin(email, nombres, apellidos):
        """Crea un usuario administrador desde la consola."""
        from werkzeug.security import generate_password_hash
        from app.models import Usuario

        email = email.strip().lower()
        if Usuario.query.filter_by(email=email).first():
            raise click.ClickException("Ya existe una cuenta con ese correo.")
        password = click.prompt("Contraseña (mínimo 12 caracteres)", hide_input=True, confirmation_prompt=True)
        if len(password) < 12:
            raise click.ClickException("La contraseña debe tener al menos 12 caracteres.")
        admin = Usuario(
            nombres=nombres.strip(),
            apellidos=apellidos.strip(),
            email=email,
            rol="ADMIN",
            activo=True,
            password_hash=generate_password_hash(password),
        )
        db.session.add(admin)
        db.session.commit()
        click.echo("Administrador creado correctamente.")

    return app
