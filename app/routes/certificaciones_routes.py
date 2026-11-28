from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, current_app, abort, send_from_directory
from flask_login import current_user
from app.extensions.database import db
from sqlalchemy import or_
from app.models import Certificacion, PerfilProfesional, Usuario
from app.services.certificacion_service import CertificacionService
from app.utils.decorators import roles_required

certificaciones_bp = Blueprint(
    "certificaciones", __name__, url_prefix="/admin/certificaciones"
)


@certificaciones_bp.get("/")
@roles_required("ADMIN")
def index():
    estado = request.args.get("estado", "").upper()
    q = (request.args.get("q") or "").strip()
    query = Certificacion.query.join(PerfilProfesional).join(
        Usuario, Usuario.id == PerfilProfesional.usuario_id
    )
    if estado in {"PENDIENTE", "APROBADA", "RECHAZADA", "VENCIDA"}:
        query = query.filter(Certificacion.estado == estado)
    if q:
        term = f"%{q}%"
        query = query.filter(or_(
            Usuario.nombres.ilike(term), Usuario.apellidos.ilike(term),
            Usuario.email.ilike(term), Certificacion.tipo.ilike(term)
        ))
    certificaciones = query.order_by(Certificacion.created_at.desc()).all()
    return render_template(
        "admin/certificaciones.html",
        certificaciones=certificaciones,
        perfiles=PerfilProfesional.query.join(Usuario).order_by(Usuario.nombres, Usuario.apellidos).all(),
        estado_filtro=estado,
        busqueda=q,
    )


@certificaciones_bp.post("/prestadores/<int:perfil_id>/registrar")
@roles_required("ADMIN")
def registrar_para_prestador(perfil_id):
    """Permite al administrador cargar un certificado para un prestador ya registrado.

    La solicitud queda PENDIENTE y debe pasar por la evaluación habitual.
    """
    perfil = db.session.get(PerfilProfesional, perfil_id)
    if not perfil:
        return jsonify({"ok": False, "message": "No se encontró el perfil profesional."}), 404
    archivo = request.files.get("documento")
    try:
        cert = CertificacionService.crear(
            perfil_id=perfil.id,
            datos=request.form,
            archivo=archivo,
            actor_id=current_user.id,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        return jsonify({
            "ok": True,
            "message": "Certificado registrado. Quedó pendiente de evaluación.",
            "certificacion": _serialize_certificacion(cert),
        }), 201
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400


def _serialize_certificacion(cert):
    return {
        "id": int(cert.id),
        "perfil_id": int(cert.perfil_id),
        "prestador": cert.perfil.usuario.nombre_completo,
        "email": cert.perfil.usuario.email,
        "tipo": cert.tipo,
        "descripcion": cert.descripcion or "",
        "fecha_emision": cert.fecha_emision.isoformat() if cert.fecha_emision else "",
        "fecha_vencimiento": cert.fecha_vencimiento.isoformat() if cert.fecha_vencimiento else "",
        "estado": cert.estado,
        "documento_url": f"/admin/certificaciones/{cert.id}/documento",
    }


@certificaciones_bp.post("/<int:certificacion_id>/evaluar")
@roles_required("ADMIN")
def evaluar(certificacion_id):
    datos = request.get_json(silent=True) or {}
    try:
        cert = CertificacionService.evaluar(
            certificacion_id, datos.get("estado"),
            datos.get("observaciones", ""), current_user.id,
            ip=request.remote_addr, user_agent=request.user_agent.string,
        )
        return jsonify({
            "ok": True, "message": "Evaluación registrada.",
            "estado": cert.estado, "observaciones": cert.observaciones_admin or "—",
            "perfil_certificado": bool(cert.perfil.certificado),
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
        str(directory), relative.name, as_attachment=True,
        download_name=cert.documento_nombre or relative.name,
        mimetype=cert.documento_mime or "application/octet-stream",
    )


@certificaciones_bp.post("/sincronizar-vencimientos")
@roles_required("ADMIN")
def sincronizar_vencimientos():
    total = CertificacionService.sincronizar_vencimientos()
    return jsonify({
        "ok": True, "message": f"Se actualizaron {total} certificaciones vencidas.",
        "total": total,
    })
