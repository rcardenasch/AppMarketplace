from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, current_app, abort, send_from_directory
from flask_login import current_user
from app.services.certificacion_service import CertificacionService
from app.utils.decorators import roles_required

certificaciones_bp = Blueprint(
    "certificaciones", __name__, url_prefix="/admin/certificaciones"
)


@certificaciones_bp.get("/")
@roles_required("ADMIN")
def index():
    estado = request.args.get("estado")
    return render_template(
        "admin/certificaciones.html",
        certificaciones=CertificacionService.listar(estado),
        estado_filtro=estado or "",
    )


@certificaciones_bp.post("/<int:certificacion_id>/evaluar")
@roles_required("ADMIN")
def evaluar(certificacion_id):
    datos = request.get_json(silent=True) or {}
    try:
        cert = CertificacionService.evaluar(
            certificacion_id,
            datos.get("estado"),
            datos.get("observaciones", ""),
            current_user.id,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        return jsonify({
            "ok": True,
            "message": "Evaluación registrada.",
            "estado": cert.estado,
        })
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@certificaciones_bp.get("/<int:certificacion_id>/documento")
@roles_required("ADMIN")
def documento(certificacion_id):
    cert = CertificacionService.obtener(certificacion_id)
    if not cert.documento_path:
        abort(404)
    relative = Path(cert.documento_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        abort(404)
    root = Path(current_app.config["PRIVATE_UPLOAD_FOLDER"]).resolve()
    directory = (root / relative.parent).resolve()
    try:
        directory.relative_to(root)
    except ValueError:
        abort(404)
    return send_from_directory(
        str(directory),
        relative.name,
        as_attachment=True,
        download_name=cert.documento_nombre or relative.name,
        mimetype=cert.documento_mime or "application/octet-stream",
    )


@certificaciones_bp.post("/sincronizar-vencimientos")
@roles_required("ADMIN")
def sincronizar_vencimientos():
    total = CertificacionService.sincronizar_vencimientos()
    return jsonify({
        "ok": True,
        "message": f"Se actualizaron {total} certificaciones vencidas.",
        "total": total,
    })
