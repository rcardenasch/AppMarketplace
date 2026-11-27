from datetime import date
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import exists, or_, select

from app.extensions.database import db
from app.models import (
    Certificacion,
    Matching,
    PerfilCategoria,
    PerfilProfesional,
    Rol,
    Ubicacion,
    Usuario,
)


class MatchingService:
    """Matching semántico, reputacional y geográfico de prestadores."""

    PESO_COMPATIBILIDAD = 0.60
    PESO_REPUTACION = 0.20
    PESO_PROXIMIDAD = 0.20

    @staticmethod
    def distancia_km(lat1, lon1, lat2, lon2):
        """Distancia geodésica aproximada entre dos puntos (Haversine)."""
        radio_tierra_km = 6371.0088
        lat1, lon1, lat2, lon2 = map(
            radians, [float(lat1), float(lon1), float(lat2), float(lon2)]
        )
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        )
        return 2 * radio_tierra_km * asin(sqrt(a))

    @staticmethod
    def _normalizar(valor):
        return max(0.0, min(1.0, float(valor or 0)))

    @classmethod
    def calcular_score(cls, similitud, reputacion, proximidad):
        return (
            cls._normalizar(similitud) * cls.PESO_COMPATIBILIDAD
            + cls._normalizar(reputacion) * cls.PESO_REPUTACION
            + cls._normalizar(proximidad) * cls.PESO_PROXIMIDAD
        )

    @classmethod
    def buscar_prestadores(
        cls,
        embedding,
        categoria_id,
        ciudad,
        distrito=None,
        latitud=None,
        longitud=None,
        limite=10,
    ):
        """Busca prestadores certificados, compatibles y dentro de cobertura.

        Si la demanda tiene coordenadas, solo considera prestadores con
        ubicación georreferenciada y dentro de su radio de atención.
        Si la demanda no tiene coordenadas, utiliza ciudad/distrito y asigna
        proximidad neutral (0.5), sin inventar una distancia.
        """
        if (latitud is None) != (longitud is None):
            raise ValueError("La demanda debe incluir latitud y longitud juntas.")

        distancia_vector = PerfilProfesional.embedding.cosine_distance(embedding)
        certificacion_valida = exists(
            select(Certificacion.id).where(
                Certificacion.perfil_id == PerfilProfesional.id,
                Certificacion.estado == "APROBADA",
                or_(
                    Certificacion.fecha_vencimiento.is_(None),
                    Certificacion.fecha_vencimiento >= date.today(),
                ),
            )
        )
        tiene_rol_prestador = or_(
            Usuario.rol == "PRESTADOR",  # compatibilidad durante transición
            Usuario.roles_rel.any(Rol.codigo == "PRESTADOR"),
        )

        query = (
            db.session.query(
                PerfilProfesional,
                Usuario,
                Ubicacion,
                distancia_vector.label("distancia_vector"),
            )
            .join(Usuario, Usuario.id == PerfilProfesional.usuario_id)
            .join(PerfilCategoria, PerfilCategoria.perfil_id == PerfilProfesional.id)
            .outerjoin(
                Ubicacion,
                db.and_(
                    Ubicacion.perfil_id == PerfilProfesional.id,
                    Ubicacion.activo.is_(True),
                ),
            )
            .filter(
                Usuario.activo.is_(True),
                tiene_rol_prestador,
                PerfilProfesional.estado == "ACTIVO",
                PerfilProfesional.certificado.is_(True),
                PerfilProfesional.embedding.isnot(None),
                PerfilCategoria.categoria_id == categoria_id,
                certificacion_valida,
            )
        )

        if latitud is None:
            query = query.filter(PerfilProfesional.ciudad.ilike(ciudad.strip()))
            if distrito:
                query = query.filter(PerfilProfesional.distrito.ilike(distrito.strip()))
        else:
            query = query.filter(
                Ubicacion.id.isnot(None),
                Ubicacion.latitud.isnot(None),
                Ubicacion.longitud.isnot(None),
            )

        filas = query.order_by(distancia_vector.asc()).limit(500).all()
        candidatos = []

        for perfil, usuario, ubicacion, distancia_vector_value in filas:
            similitud = cls._normalizar(1.0 - float(distancia_vector_value))
            rating = float(perfil.puntuacion or 0)
            # Sin calificaciones aún: valor neutral para no castigar a perfiles nuevos.
            reputacion_estrellas = (
                0.5 if rating <= 0 else cls._normalizar(rating / 5.0)
            )
            distancia = None

            if latitud is not None:
                distancia = cls.distancia_km(
                    latitud,
                    longitud,
                    ubicacion.latitud,
                    ubicacion.longitud,
                )
                radio = float(ubicacion.radio_atencion_km or 0)
                if radio <= 0 or distancia > radio:
                    continue
                proximidad = cls._normalizar(1.0 - (distancia / radio))
            else:
                # Neutral: no se penaliza al prestador cuando el cliente aún
                # no proporciona coordenadas; tampoco se afirma una distancia.
                proximidad = 0.5

            score = cls.calcular_score(
                similitud, reputacion_estrellas, proximidad
            )
            candidatos.append({
                "perfil_id": perfil.id,
                "usuario_id": usuario.id,
                "nombre": "{} {}".format(usuario.nombres, usuario.apellidos).strip(),
                "descripcion": perfil.descripcion,
                "ciudad": perfil.ciudad,
                "distrito": perfil.distrito,
                "puntuacion": float(perfil.puntuacion or 0),
                "trabajos_completados": perfil.trabajos_completados or 0,
                "similitud": round(similitud, 6),
                "reputacion": round(reputacion_estrellas, 6),
                "proximidad": round(proximidad, 6),
                "distancia_km": round(distancia, 3) if distancia is not None else None,
                "radio_atencion_km": (
                    float(ubicacion.radio_atencion_km)
                    if ubicacion and ubicacion.radio_atencion_km is not None
                    else None
                ),
                "score": round(score, 6),
            })

        candidatos.sort(
            key=lambda item: (
                item["score"],
                -(item["distancia_km"] if item["distancia_km"] is not None else 0),
            ),
            reverse=True,
        )
        return candidatos[:min(50, max(1, int(limite)))]

    @classmethod
    def generar_matches(cls, demanda, limite=10):
        candidatos = cls.buscar_prestadores(
            embedding=demanda.embedding,
            categoria_id=demanda.categoria_id,
            ciudad=demanda.ciudad,
            distrito=demanda.distrito,
            latitud=demanda.latitud,
            longitud=demanda.longitud,
            limite=limite,
        )

        for candidato in candidatos:
            match = Matching.query.filter_by(
                demanda_id=demanda.id,
                perfil_id=candidato["perfil_id"],
            ).first()
            if match is None:
                match = Matching(
                    demanda_id=demanda.id,
                    perfil_id=candidato["perfil_id"],
                    estado="PENDIENTE",
                )
                db.session.add(match)

            # No sobrescribir decisiones que el prestador ya haya tomado.
            if match.estado in (None, "PENDIENTE", "NOTIFICADO"):
                match.similitud = Decimal(str(candidato["similitud"]))
                match.reputacion = Decimal(str(candidato["reputacion"]))
                match.proximidad = Decimal(str(candidato["proximidad"]))
                match.distancia_km = (
                    Decimal(str(candidato["distancia_km"]))
                    if candidato["distancia_km"] is not None else None
                )
                match.score = Decimal(str(candidato["score"]))

        return candidatos
