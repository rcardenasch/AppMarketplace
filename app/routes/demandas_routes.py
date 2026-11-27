from typing import Optional

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from pydantic import BaseModel, Field, ValidationError

from app.extensions.database import db
from app.models import Categoria, Demanda, Matching
from app.services.demanda_service import DemandaService
from app.utils.decorators import roles_required


demandas_bp = Blueprint("demandas", __name__, url_prefix="/demandas")


class DemandaRequest(BaseModel):
    categoria_id: int = Field(gt=0)
    servicio_id: Optional[int] = Field(default=None, gt=0)
    titulo: str = Field(min_length=5, max_length=200)
    descripcion: str = Field(min_length=10)
    ciudad: str = Field(min_length=2, max_length=100)
    distrito: str = Field(min_length=2, max_length=100)
    direccion: Optional[str] = None
    referencia: Optional[str] = None
    latitud: Optional[float] = Field(default=None, ge=-90, le=90)
    longitud: Optional[float] = Field(default=None, ge=-180, le=180)


@demandas_bp.route("/nueva", methods=["GET", "POST"])
@login_required
@roles_required("CLIENTE")
def nueva_demanda():
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    if request.method == "POST":
        try:
            datos = {
                "categoria_id": request.form.get("categoria_id"),
                "servicio_id": request.form.get("servicio_id") or None,
                "titulo": request.form.get("titulo", ""),
                "descripcion": request.form.get("descripcion", ""),
                "ciudad": request.form.get("ciudad", ""),
                "distrito": request.form.get("distrito", ""),
                "direccion": request.form.get("direccion", ""),
                "referencia": request.form.get("referencia", ""),
                "latitud": request.form.get("latitud") or None,
                "longitud": request.form.get("longitud") or None,
            }
            resultado = DemandaService.crear_demanda(datos, cliente_id=current_user.id)
            demanda = db.session.get(Demanda, resultado["demanda_id"])
            flash("Solicitud publicada. Encontramos {} prestadores compatibles.".format(
                resultado["total_prestadores"]
            ), "success")
            return render_template(
                "demandas/resultado.html",
                demanda=demanda,
                matches=resultado["prestadores"],
            )
        except ValueError as exc:
            flash(str(exc), "warning")
        except Exception:
            current_app.logger.exception("Error al registrar demanda")
            flash("No fue posible registrar la solicitud. Inténtalo nuevamente.", "danger")
    return render_template("demandas/nueva.html", categorias=categorias)


@demandas_bp.post("/")
@login_required
@roles_required("CLIENTE")
def crear_demanda_api():
    try:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"success": False, "message": "Se requiere un objeto JSON válido."}), 400
        datos = DemandaRequest.model_validate(payload).model_dump()
        resultado = DemandaService.crear_demanda(datos, cliente_id=current_user.id)
        return jsonify({
            "success": True,
            "message": "Demanda registrada correctamente.",
            "data": {
                **resultado,
                "resultado_url": url_for("demandas.ver_matches", demanda_id=resultado["demanda_id"])
            },
        }), 201
    except ValidationError as exc:
        return jsonify({"success": False, "message": "Error de validación.", "errors": exc.errors()}), 422
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Error en API de creación de demanda")
        return jsonify({"success": False, "message": "Error interno al registrar la demanda."}), 500


@demandas_bp.get("/<int:demanda_id>/matches")
@login_required
@roles_required("CLIENTE", "ADMIN")
def ver_matches(demanda_id):
    demanda = db.session.get(Demanda, demanda_id)
    if not demanda:
        return jsonify({"ok": False, "message": "Demanda no encontrada."}), 404
    if not current_user.has_role("ADMIN") and demanda.cliente_id != current_user.id:
        return jsonify({"ok": False, "message": "No tienes permiso para consultar esta demanda."}), 403

    from app.models import PerfilProfesional, Usuario
    filas = (
        db.session.query(Matching, PerfilProfesional, Usuario)
        .join(PerfilProfesional, PerfilProfesional.id == Matching.perfil_id)
        .join(Usuario, Usuario.id == PerfilProfesional.usuario_id)
        .filter(Matching.demanda_id == demanda.id)
        .order_by(Matching.score.desc())
        .all()
    )
    candidatos = []
    for match, perfil, usuario in filas:
        candidatos.append({
            "nombre": "{} {}".format(usuario.nombres, usuario.apellidos).strip(),
            "descripcion": perfil.descripcion,
            "ciudad": perfil.ciudad,
            "distrito": perfil.distrito,
            "puntuacion": float(perfil.puntuacion or 0),
            "trabajos_completados": perfil.trabajos_completados or 0,
            "score": float(match.score or 0),
            "distancia_km": float(match.distancia_km) if match.distancia_km is not None else None,
            "estado": match.estado,
        })
    return render_template("demandas/resultado.html", demanda=demanda, matches=candidatos)


@demandas_bp.get("/mis-oportunidades")
@login_required
@roles_required("PRESTADOR")
def mis_oportunidades():
    perfil = current_user.perfil_profesional
    if perfil is None:
        flash("Completa primero tu perfil profesional.", "warning")
        return redirect(url_for("auth.gestionar_roles"))
    filas = (
        db.session.query(Matching, Demanda)
        .join(Demanda, Demanda.id == Matching.demanda_id)
        .filter(
            Matching.perfil_id == perfil.id,
            Demanda.estado.in_(["PUBLICADA", "EN_MATCHING"]),
            Matching.estado.in_(["PENDIENTE", "NOTIFICADO"]),
        )
        .order_by(Matching.score.desc(), Matching.created_at.desc())
        .all()
    )
    items = [{"match": match, "demanda": demanda} for match, demanda in filas]
    return render_template("demandas/oportunidades.html", items=items)
