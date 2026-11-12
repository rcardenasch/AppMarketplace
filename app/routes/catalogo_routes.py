from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from app.services.catalogo_service import CatalogoService
from app.utils.decorators import roles_required

catalogo_bp = Blueprint("catalogo", __name__)


def _audit_args():
    return {
        "actor_id": current_user.id,
        "ip": request.remote_addr,
        "user_agent": request.user_agent.string,
    }


@catalogo_bp.get("/catalogo")
def catalogo_publico():
    categorias = CatalogoService.listar_categorias(solo_activas=True)
    servicios = CatalogoService.listar_servicios(solo_activos=True)
    return render_template(
        "catalogo.html",
        categorias=categorias,
        servicios=servicios,
    )


@catalogo_bp.get("/admin/categorias")
@roles_required("ADMIN")
def categorias():
    return render_template(
        "admin/categorias.html",
        categorias=CatalogoService.listar_categorias(),
    )


@catalogo_bp.post("/admin/categorias")
@roles_required("ADMIN")
def guardar_categoria():
    try:
        categoria = CatalogoService.guardar_categoria(
            request.get_json(silent=True) or {}, **_audit_args()
        )
        return jsonify({
            "ok": True,
            "message": "Categoría guardada.",
            "id": categoria.id,
        })
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@catalogo_bp.put("/admin/categorias/<int:categoria_id>")
@roles_required("ADMIN")
def actualizar_categoria(categoria_id):
    try:
        categoria = CatalogoService.guardar_categoria(
            request.get_json(silent=True) or {},
            categoria_id=categoria_id,
            **_audit_args(),
        )
        return jsonify({
            "ok": True,
            "message": "Categoría actualizada.",
            "id": categoria.id,
        })
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@catalogo_bp.patch("/admin/categorias/<int:categoria_id>/estado")
@roles_required("ADMIN")
def cambiar_estado_categoria(categoria_id):
    datos = request.get_json(silent=True) or {}
    try:
        categoria = CatalogoService.cambiar_estado_categoria(
            categoria_id, datos.get("activo"), **_audit_args()
        )
        return jsonify({
            "ok": True,
            "message": "Estado de la categoría actualizado.",
            "activo": categoria.activo,
        })
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@catalogo_bp.delete("/admin/categorias/<int:categoria_id>")
@roles_required("ADMIN")
def eliminar_categoria(categoria_id):
    try:
        CatalogoService.eliminar_categoria(categoria_id, **_audit_args())
        return jsonify({
            "ok": True,
            "message": "Categoría desactivada para conservar el historial.",
        })
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@catalogo_bp.get("/admin/servicios")
@roles_required("ADMIN")
def servicios():
    return render_template(
        "admin/servicios.html",
        servicios=CatalogoService.listar_servicios(),
        categorias=CatalogoService.listar_categorias(solo_activas=True),
    )


@catalogo_bp.post("/admin/servicios")
@roles_required("ADMIN")
def guardar_servicio():
    try:
        servicio = CatalogoService.guardar_servicio(
            request.get_json(silent=True) or {}, **_audit_args()
        )
        return jsonify({
            "ok": True,
            "message": "Servicio guardado.",
            "id": servicio.id,
        })
    except (ValueError, TypeError) as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@catalogo_bp.put("/admin/servicios/<int:servicio_id>")
@roles_required("ADMIN")
def actualizar_servicio(servicio_id):
    try:
        servicio = CatalogoService.guardar_servicio(
            request.get_json(silent=True) or {},
            servicio_id=servicio_id,
            **_audit_args(),
        )
        return jsonify({
            "ok": True,
            "message": "Servicio actualizado.",
            "id": servicio.id,
        })
    except (ValueError, TypeError) as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@catalogo_bp.patch("/admin/servicios/<int:servicio_id>/estado")
@roles_required("ADMIN")
def cambiar_estado_servicio(servicio_id):
    datos = request.get_json(silent=True) or {}
    try:
        servicio = CatalogoService.cambiar_estado_servicio(
            servicio_id, datos.get("activo"), **_audit_args()
        )
        return jsonify({
            "ok": True,
            "message": "Estado del servicio actualizado.",
            "activo": servicio.activo,
        })
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@catalogo_bp.delete("/admin/servicios/<int:servicio_id>")
@roles_required("ADMIN")
def eliminar_servicio(servicio_id):
    try:
        CatalogoService.eliminar_servicio(servicio_id, **_audit_args())
        return jsonify({
            "ok": True,
            "message": "Servicio desactivado para conservar el historial.",
        })
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
