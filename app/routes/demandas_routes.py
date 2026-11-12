
from flask import Blueprint, request, jsonify

from pydantic import BaseModel, ValidationError, Field

from app.services.demanda_service import DemandaService


demandas_bp = Blueprint(
    "demandas",
    __name__
)


# =====================================================
# ESQUEMA DE ENTRADA
# =====================================================

class DemandaRequest(BaseModel):

    cliente_id: int = Field(gt=0)

    categoria_id: int = Field(gt=0)

    titulo: str = Field(min_length=5, max_length=200)

    descripcion: str = Field(min_length=10)

    ciudad: str = Field(min_length=2)

    distrito: str = Field(min_length=2)


# =====================================================
# REGISTRAR DEMANDA
# =====================================================

@demandas_bp.route(
    "/",
    methods=["POST"]
)
def crear_demanda():

    try:

        # 1. Recibir JSON.

        payload = request.get_json(silent=True)

        if not isinstance(payload, dict):

            return jsonify({
                "success": False,
                "message": "Se requiere un objeto JSON válido"
            }), 400

        # 2. Validar estructura.

        datos = DemandaRequest.model_validate(
            payload
        )

        # 3. Ejecutar caso de uso.

        resultado = DemandaService.crear_demanda(
            datos.model_dump()
        )

        # 4. Responder.

        return jsonify({
            "success": True,
            "message": "Demanda registrada correctamente",
            "data": resultado
        }), 201

    except ValidationError as e:

        return jsonify({
            "success": False,
            "message": "Error de validación",
            "errors": e.errors()
        }), 422

    except ValueError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception:

        # El detalle técnico debe registrarse
        # mediante el sistema de logging.

        return jsonify({
            "success": False,
            "message": "Error interno al registrar la demanda"
        }), 500
