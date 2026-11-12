
from datetime import date
from decimal import Decimal

from sqlalchemy import select, exists

from app.extensions.database import db

from app.models.demanda import Demanda
from app.models.perfil_profesional import PerfilProfesional
from app.models.usuario import Usuario
from app.models.certificacion import Certificacion
from app.models.perfil_categoria import PerfilCategoria

from app.services.embedding_service import EmbeddingService


class DemandaService:
    """
    Gestiona el registro de demandas y la selección
    de prestadores profesionales mediante pgvector.
    """

    @staticmethod
    def buscar_prestadores(
        embedding,
        categoria_id,
        ciudad,
        distrito=None,
        limite=3
    ):
        """
        Recupera los profesionales certificados más aptos.

        Criterios:
        - Usuario activo.
        - Perfil activo.
        - Certificación aprobada y vigente.
        - Especialidad compatible.
        - Ciudad y distrito compatibles.
        - Similitud semántica.
        """

        distancia = PerfilProfesional.embedding.cosine_distance(
            embedding
        )

        certificacion_valida = exists(
            select(Certificacion.id).where(
                Certificacion.perfil_id == PerfilProfesional.id,
                Certificacion.estado == "APROBADA",
                db.or_(
                    Certificacion.fecha_vencimiento.is_(None),
                    Certificacion.fecha_vencimiento >= date.today()
                )
            )
        )

        query = (
            db.session.query(
                PerfilProfesional,
                Usuario,
                distancia.label("distancia")
            )
            .join(
                Usuario,
                Usuario.id == PerfilProfesional.usuario_id
            )
            .join(
                PerfilCategoria,
                PerfilCategoria.perfil_id == PerfilProfesional.id
            )
            .filter(
                Usuario.activo.is_(True),
                Usuario.rol == "PRESTADOR",

                PerfilProfesional.estado == "ACTIVO",
                PerfilProfesional.certificado.is_(True),

                PerfilProfesional.embedding.isnot(None),

                PerfilProfesional.ciudad.ilike(ciudad),

                PerfilCategoria.categoria_id == categoria_id,

                certificacion_valida
            )
        )

        if distrito:
            query = query.filter(
                PerfilProfesional.distrito.ilike(distrito)
            )

        resultados = (
            query
            .order_by(distancia.asc())
            .limit(limite)
            .all()
        )

        candidatos = []

        for perfil, usuario, distancia_value in resultados:

            similitud = max(
                0.0,
                min(1.0, 1.0 - float(distancia_value))
            )

            reputacion = float(
                perfil.puntuacion or 0
            ) / 5.0

            # Ponderación inicial:
            # 80% compatibilidad semántica.
            # 20% reputación del profesional.

            score = (
                similitud * 0.80
                +
                reputacion * 0.20
            )

            candidatos.append({
                "perfil_id": perfil.id,
                "usuario_id": usuario.id,

                "nombre": (
                    f"{usuario.nombres} "
                    f"{usuario.apellidos}"
                ),

                "descripcion": perfil.descripcion,

                "puntuacion": float(
                    perfil.puntuacion or 0
                ),

                "trabajos_completados":
                    perfil.trabajos_completados,

                "similitud": round(similitud, 4),

                "score": round(score, 4)
            })

        # Ordenar según puntuación combinada.
        candidatos.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return candidatos[:limite]

    @classmethod
    def crear_demanda(cls, datos):
        """
        Caso de uso:
        Registrar demanda y ejecutar matching.
        """

        try:

            # 1. Validar información obligatoria.

            campos = [
                "cliente_id",
                "categoria_id",
                "titulo",
                "descripcion",
                "ciudad",
                "distrito"
            ]

            for campo in campos:

                if not datos.get(campo):
                    raise ValueError(
                        f"El campo {campo} es obligatorio"
                    )

            # 2. Verificar cliente.

            cliente = db.session.get(
                Usuario,
                datos["cliente_id"]
            )

            if (
                not cliente
                or not cliente.activo
                or cliente.rol != "CLIENTE"
            ):
                raise ValueError(
                    "El cliente no existe o no está habilitado"
                )

            # 3. Generar embedding.

            texto = (
                f"{datos['titulo']}. "
                f"{datos['descripcion']}"
            )

            embedding = (
                EmbeddingService.generar_embedding(texto)
            )

            # 4. Crear demanda.

            demanda = Demanda(
                cliente_id=datos["cliente_id"],
                categoria_id=datos["categoria_id"],
                titulo=datos["titulo"],
                descripcion=datos["descripcion"],
                ciudad=datos["ciudad"],
                distrito=datos["distrito"],
                embedding=embedding,
                estado="EN_MATCHING"
            )

            db.session.add(demanda)

            # Obtener ID sin realizar commit prematuro.
            db.session.flush()

            # 5. Buscar los tres mejores profesionales.

            prestadores = cls.buscar_prestadores(
                embedding=embedding,
                categoria_id=datos["categoria_id"],
                ciudad=datos["ciudad"],
                distrito=datos.get("distrito"),
                limite=3
            )

            # 6. Registrar candidatos encontrados.

            from app.models.matching import Matching

            for prestador in prestadores:

                matching = Matching(
                    demanda_id=demanda.id,
                    perfil_id=prestador["perfil_id"],
                    similitud=Decimal(
                        str(prestador["similitud"])
                    ),
                    score=Decimal(
                        str(prestador["score"])
                    ),
                    estado="PENDIENTE"
                )

                db.session.add(matching)

            # 7. Actualizar estado.

            if prestadores:
                demanda.estado = "PUBLICADA"
            else:
                demanda.estado = "PUBLICADA"

            # 8. Confirmar transacción.

            db.session.commit()

            return {
                "success": True,
                "demanda_id": demanda.id,
                "estado": demanda.estado,
                "total_prestadores": len(prestadores),
                "prestadores": prestadores
            }

        except Exception:

            db.session.rollback()

            raise
