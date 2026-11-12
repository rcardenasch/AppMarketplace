from flask import Blueprint, render_template, request, jsonify
from app.models import Usuario, PerfilProfesional, Certificacion, Categoria, Servicio
from app.services.prestador_service import PrestadorService
from app.services.auditoria_service import AuditoriaService
from app.utils.decorators import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
@roles_required("ADMIN")
def dashboard():
    from app.services.certificacion_service import CertificacionService
    CertificacionService.sincronizar_vencimientos()
    return render_template(
        "admin/dashboard.html",
        total_usuarios=Usuario.query.count(),
        total_prestadores=PerfilProfesional.query.count(),
        prestadores_suspendidos=PerfilProfesional.query.filter_by(estado="SUSPENDIDO").count(),
        pendientes=Certificacion.query.filter_by(estado="PENDIENTE").count(),
        vencidas=Certificacion.query.filter_by(estado="VENCIDA").count(),
        total_categorias=Categoria.query.count(),
        total_servicios=Servicio.query.count(),
    )


@admin_bp.get("/prestadores")
@roles_required("ADMIN")
def prestadores():
    return render_template(
        "admin/prestadores.html",
        prestadores=PrestadorService.listar(
            filtro=request.args.get("q", ""),
            estado=request.args.get("estado"),
        ),
        busqueda=request.args.get("q", ""),
        estado_filtro=request.args.get("estado", ""),
    )


@admin_bp.post("/prestadores/<int:perfil_id>/estado")
@roles_required("ADMIN")
def cambiar_estado_prestador(perfil_id):
    datos = request.get_json(silent=True) or {}
    try:
        perfil = PrestadorService.cambiar_estado(
            perfil_id,
            datos.get("estado"),
            actor_id=current_user_id(),
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        return jsonify({
            "ok": True,
            "message": "Estado del prestador actualizado.",
            "estado": perfil.estado,
        })
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@admin_bp.get("/auditoria")
@roles_required("ADMIN")
def auditoria():
    return render_template(
        "admin/auditoria.html",
        registros=AuditoriaService.listar(
            limite=500,
            accion=request.args.get("accion") or None,
            entidad=request.args.get("entidad") or None,
        ),
    )


def current_user_id():
    from flask_login import current_user
    return current_user.id
