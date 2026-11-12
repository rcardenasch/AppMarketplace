
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.services.ubicacion_service import UbicacionService
from app.decorators import roles_required


ubicacion_bp = Blueprint(
    "ubicacion",
    __name__,
    url_prefix="/ubicaciones"
)


@ubicacion_bp.route("/mi-ubicacion", methods=["GET", "POST"])
@login_required
@roles_required("PRESTADOR")
def mi_ubicacion():

    perfil = current_user.perfil_profesional

    if request.method == "POST":
        try:
            UbicacionService.guardar(
                perfil.id,
                request.form
            )

            flash("Ubicación guardada correctamente.", "success")

            return redirect(
                url_for("ubicacion.mi_ubicacion")
            )

        except ValueError as e:
            flash(str(e), "danger")

    ubicacion = UbicacionService.obtener_por_perfil(
        perfil.id
    )

    return render_template(
        "ubicacion/formulario.html",
        ubicacion=ubicacion
    )


@ubicacion_bp.route("/api/mi-ubicacion", methods=["GET"])
@login_required
@roles_required("PRESTADOR")
def api_mi_ubicacion():

    perfil = current_user.perfil_profesional

    ubicacion = UbicacionService.obtener_por_perfil(
        perfil.id
    )

    if not ubicacion:
        return jsonify({
            "ok": False,
            "message": "No existe una ubicación registrada."
        }), 404

    return jsonify({
        "ok": True,
        "ubicacion": {
            "departamento": ubicacion.departamento,
            "provincia": ubicacion.provincia,
            "distrito": ubicacion.distrito,
            "direccion": ubicacion.direccion,
            "referencia": ubicacion.referencia,
            "latitud": float(ubicacion.latitud) if ubicacion.latitud is not None else None,
            "longitud": float(ubicacion.longitud) if ubicacion.longitud is not None else None,
            "radio_atencion_km": float(ubicacion.radio_atencion_km)
        }
    })


@ubicacion_bp.route("/<int:perfil_id>", methods=["GET"])
@login_required
@roles_required("ADMIN")
def detalle(perfil_id):

    ubicacion = UbicacionService.obtener_por_perfil(
        perfil_id
    )

    if not ubicacion:
        return jsonify({
            "ok": False,
            "message": "Ubicación no encontrada."
        }), 404

    return jsonify({
        "ok": True,
        "departamento": ubicacion.departamento,
        "provincia": ubicacion.provincia,
        "distrito": ubicacion.distrito,
        "direccion": ubicacion.direccion,
        "latitud": float(ubicacion.latitud) if ubicacion.latitud is not None else None,
        "longitud": float(ubicacion.longitud) if ubicacion.longitud is not None else None
    })
