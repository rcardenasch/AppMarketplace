
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models.ubicacion import Ubicacion


class UbicacionService:

    @staticmethod
    def guardar(perfil_id, datos):

        departamento = (datos.get("departamento") or "").strip()
        provincia = (datos.get("provincia") or "").strip()
        distrito = (datos.get("distrito") or "").strip()

        if not departamento or not provincia or not distrito:
            raise ValueError(
                "Departamento, provincia y distrito son obligatorios."
            )

        def convertir_decimal(valor, campo):
            if valor in (None, ""):
                return None

            try:
                return Decimal(str(valor))
            except InvalidOperation:
                raise ValueError(f"El campo {campo} no es válido.")

        latitud = convertir_decimal(datos.get("latitud"), "latitud")
        longitud = convertir_decimal(datos.get("longitud"), "longitud")

        if (latitud is None) != (longitud is None):
            raise ValueError(
                "Debes proporcionar latitud y longitud juntas."
            )

        if latitud is not None and not (
            Decimal("-90") <= latitud <= Decimal("90")
        ):
            raise ValueError("Latitud fuera de rango.")

        if longitud is not None and not (
            Decimal("-180") <= longitud <= Decimal("180")
        ):
            raise ValueError("Longitud fuera de rango.")

        radio = convertir_decimal(
            datos.get("radio_atencion_km", 10),
            "radio de atención"
        )

        if radio is None or radio <= 0 or radio > 500:
            raise ValueError("El radio debe estar entre 0 y 500 km.")

        ubicacion = Ubicacion.query.filter_by(
            perfil_id=perfil_id
        ).first()

        if ubicacion is None:
            ubicacion = Ubicacion(perfil_id=perfil_id)
            db.session.add(ubicacion)

        ubicacion.departamento = departamento
        ubicacion.provincia = provincia
        ubicacion.distrito = distrito
        ubicacion.direccion = datos.get("direccion")
        ubicacion.referencia = datos.get("referencia")
        ubicacion.latitud = latitud
        ubicacion.longitud = longitud
        ubicacion.radio_atencion_km = radio
        ubicacion.activo = True

        db.session.commit()

        return ubicacion

    @staticmethod
    def obtener_por_perfil(perfil_id):
        return Ubicacion.query.filter_by(
            perfil_id=perfil_id,
            activo=True
        ).first()

    @staticmethod
    def listar():
        return Ubicacion.query.filter_by(
            activo=True
        ).all()

    @staticmethod
    def eliminar(perfil_id):
        ubicacion = Ubicacion.query.filter_by(
            perfil_id=perfil_id
        ).first()

        if not ubicacion:
            raise ValueError("No se encontró la ubicación.")

        ubicacion.activo = False
        db.session.commit()

        return ubicacion
