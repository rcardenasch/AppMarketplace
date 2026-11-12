from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, current_app, abort, send_from_directory
from flask_login import current_user
from app.models import Categoria
from app.services.prestador_service import PrestadorService
from app.services.certificacion_service import CertificacionService
from app.utils.decorators import roles_required

prestadores_bp = Blueprint("prestadores", __name__, url_prefix="/prestadores")


@prestadores_bp.get("/mi-perfil")
@roles_required("PRESTADOR")
def mi_perfil():
    perfil = current_user.perfil_profesional
    if not perfil:
        abort(404)
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    certificaciones = CertificacionService.listar_por_perfil(perfil.id)
    return render_template(
        "prestador/perfil.html",
        perfil=perfil,
        categorias=categorias,
        certificaciones=certificaciones,
    )


@prestadores_bp.post("/mi-perfil")
@roles_required("PRESTADOR")
def actualizar_mi_perfil():
    try:
        datos = request.get_json(silent=True) or {}
        perfil = PrestadorService.actualizar(current_user.perfil_profesional.id, datos)
        return jsonify({
            "ok": True,
            "message": "Perfil actualizado.",
            "estado": perfil.estado,
        })
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@prestadores_bp.post("/certificaciones")
@roles_required("PRESTADOR")
def solicitar_certificacion():
    perfil = current_user.perfil_profesional
    if not perfil:
        abort(404)
    try:
        cert = CertificacionService.crear(
            perfil_id=perfil.id,
            datos=request.form,
            archivo=request.files.get("documento"),
            actor_id=current_user.id,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        return jsonify({
            "ok": True,
            "message": "Documento enviado. La certificación quedó pendiente de revisión.",
            "id": cert.id,
        }), 201
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


@prestadores_bp.get("/certificaciones/<int:certificacion_id>/documento")
@roles_required("PRESTADOR")
def descargar_mi_documento(certificacion_id):
    cert = CertificacionService.obtener(certificacion_id)
    perfil = current_user.perfil_profesional
    if not perfil or cert.perfil_id != perfil.id:
        abort(403)
    return _enviar_documento(cert)


def _enviar_documento(cert):
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
