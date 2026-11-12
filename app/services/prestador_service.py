from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from app.extensions.database import db
from app.models import Usuario, PerfilProfesional, Categoria, Certificacion
from app.services.auditoria_service import AuditoriaService


class PrestadorService:
    @staticmethod
    def listar(filtro=None, estado=None):
        query = (
            PerfilProfesional.query
            .join(Usuario, Usuario.id == PerfilProfesional.usuario_id)
            .options(
                joinedload(PerfilProfesional.usuario),
                joinedload(PerfilProfesional.categorias),
                joinedload(PerfilProfesional.certificaciones),
            )
            .filter(Usuario.rol == "PRESTADOR")
        )
        if filtro:
            term = f"%{filtro.strip()}%"
            query = query.filter(or_(
                Usuario.nombres.ilike(term),
                Usuario.apellidos.ilike(term),
                Usuario.email.ilike(term),
                PerfilProfesional.ciudad.ilike(term),
                PerfilProfesional.distrito.ilike(term),
            ))
        if estado in {"PENDIENTE", "ACTIVO", "SUSPENDIDO", "RECHAZADO"}:
            query = query.filter(PerfilProfesional.estado == estado)
        return query.order_by(PerfilProfesional.created_at.desc()).all()

    @staticmethod
    def obtener(perfil_id):
        perfil = db.session.get(PerfilProfesional, perfil_id)
        if not perfil:
            raise ValueError("No se encontró el perfil profesional.")
        return perfil

    @staticmethod
    def actualizar(perfil_id, datos):
        perfil = PrestadorService.obtener(perfil_id)
        descripcion = datos.get("descripcion", perfil.descripcion)
        ciudad = datos.get("ciudad", perfil.ciudad)
        distrito = datos.get("distrito", perfil.distrito or "")
        try:
            experiencia = int(datos.get("experiencia_anios", perfil.experiencia_anios))
        except (TypeError, ValueError):
            raise ValueError("Los años de experiencia deben ser un número entero.")
        if experiencia < 0 or experiencia > 60:
            raise ValueError("Los años de experiencia deben estar entre 0 y 60.")
        if not str(ciudad).strip():
            raise ValueError("La ciudad es obligatoria.")

        categoria_ids = datos.get("categoria_ids", [])
        if not isinstance(categoria_ids, list):
            raise ValueError("La lista de especialidades no es válida.")
        if categoria_ids:
            try:
                ids = [int(value) for value in categoria_ids]
            except (TypeError, ValueError):
                raise ValueError("Una de las categorías seleccionadas no es válida.")
            categorias = Categoria.query.filter(
                Categoria.id.in_(ids), Categoria.activo.is_(True)
            ).all()
            if len(categorias) != len(set(ids)):
                raise ValueError("Selecciona únicamente categorías activas.")
        else:
            categorias = []

        perfil.descripcion = str(descripcion or "").strip()
        perfil.experiencia_anios = experiencia
        perfil.ciudad = str(ciudad).strip()
        perfil.distrito = str(distrito or "").strip() or None
        perfil.categorias = categorias
        db.session.commit()
        return perfil

    @staticmethod
    def tiene_certificacion_vigente(perfil):
        from datetime import date
        hoy = date.today()
        return any(
            cert.estado == "APROBADA"
            and (cert.fecha_vencimiento is None or cert.fecha_vencimiento >= hoy)
            for cert in perfil.certificaciones
        )

    @staticmethod
    def cambiar_estado(
        perfil_id, estado, actor_id=None, ip=None, user_agent=None
    ):
        permitidos = {"PENDIENTE", "ACTIVO", "SUSPENDIDO", "RECHAZADO"}
        if estado not in permitidos:
            raise ValueError("Estado no permitido.")

        perfil = PrestadorService.obtener(perfil_id)
        anterior = perfil.estado

        if estado == "ACTIVO" and not PrestadorService.tiene_certificacion_vigente(perfil):
            raise ValueError(
                "No se puede activar el prestador: necesita al menos una certificación aprobada y vigente."
            )

        perfil.estado = estado
        AuditoriaService.registrar(
            actor_id=actor_id,
            accion="PRESTADOR_ESTADO_CAMBIADO",
            entidad="PerfilProfesional",
            entidad_id=perfil.id,
            detalles={
                "estado_anterior": anterior,
                "estado_nuevo": estado,
                "usuario_id": perfil.usuario_id,
            },
            ip=ip,
            user_agent=user_agent,
        )
        db.session.commit()
        return perfil
