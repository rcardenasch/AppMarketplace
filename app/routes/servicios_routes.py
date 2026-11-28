from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user

from app.models import Categoria
from app.services.catalogo_service import CatalogoService
from app.utils.decorators import roles_required

servicios_bp = Blueprint("servicios", __name__, url_prefix="/servicios")


def _audit_args():
    return {
        "actor_id": current_user.id,
        "ip": request.remote_addr,
        "user_agent": request.user_agent.string,
    }


@servicios_bp.get("/")
@roles_required("ADMIN")
def index():
    return render_template(
        "admin/servicios.html",
        servicios=CatalogoService.listar_servicios(),
        categorias=CatalogoService.listar_categorias(solo_activas=True),
    )


@servicios_bp.post("/")
@roles_required("ADMIN")
def crear():
    try:
        servicio = CatalogoService.guardar_servicio(
            request.get_json(silent=True) or {}, **_audit_args()
        )
        payload = _serialize(servicio)
        return jsonify({"ok": True, "message": "Servicio creado correctamente.",
                        "servicio": payload, "data": {"servicio": payload}, "id": payload["id"]}), 201
    except (ValueError, TypeError) as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@servicios_bp.put("/<int:servicio_id>")
@roles_required("ADMIN")
def actualizar(servicio_id):
    try:
        servicio = CatalogoService.guardar_servicio(
            request.get_json(silent=True) or {},
            servicio_id=servicio_id, **_audit_args()
        )
        payload = _serialize(servicio)
        return jsonify({"ok": True, "message": "Servicio actualizado.",
                        "servicio": payload, "data": {"servicio": payload}, "id": payload["id"]})
    except (ValueError, TypeError) as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@servicios_bp.patch("/<int:servicio_id>/estado")
@roles_required("ADMIN")
def cambiar_estado(servicio_id):
    try:
        data = request.get_json(silent=True) or {}
        servicio = CatalogoService.cambiar_estado_servicio(
            servicio_id, data.get("activo"), **_audit_args()
        )
        payload = _serialize(servicio)
        return jsonify({"ok": True, "message": "Estado actualizado.",
                        "servicio": payload, "data": {"servicio": payload}, "id": payload["id"]})
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@servicios_bp.get("/categorias/<int:categoria_id>/opciones")
@roles_required("ADMIN")
def opciones_categoria(categoria_id):
    categoria = Categoria.query.filter_by(id=categoria_id, activo=True).first()
    if not categoria:
        return jsonify({"ok": False, "message": "Categoría no encontrada o inactiva."}), 404
    return jsonify({
        "ok": True,
        "servicios": [
            {"id": s.id, "nombre": s.nombre, "activo": s.activo}
            for s in sorted(categoria.servicios, key=lambda x: x.nombre.lower())
            if s.activo
        ]
    })


def _serialize(servicio):
    return {
        "id": int(servicio.id),
        "nombre": servicio.nombre,
        "descripcion": servicio.descripcion or "",
        "categoria_id": int(servicio.categoria_id),
        "categoria": servicio.categoria.nombre,
        "precio_referencial": (
            str(servicio.precio_referencial)
            if servicio.precio_referencial is not None else ""
        ),
        "activo": bool(servicio.activo),
    }
