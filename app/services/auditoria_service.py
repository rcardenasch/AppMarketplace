from app.extensions.database import db
from app.models import Auditoria


class AuditoriaService:
    @staticmethod
    def registrar(
        actor_id,
        accion,
        entidad,
        entidad_id=None,
        detalles=None,
        ip=None,
        user_agent=None,
    ):
        registro = Auditoria(
            actor_id=actor_id,
            accion=accion,
            entidad=entidad,
            entidad_id=str(entidad_id) if entidad_id is not None else None,
            detalles=detalles or {},
            ip=ip,
            user_agent=(user_agent or "")[:300] or None,
        )
        db.session.add(registro)
        return registro

    @staticmethod
    def listar(limite=500, accion=None, entidad=None):
        query = Auditoria.query
        if accion:
            query = query.filter(Auditoria.accion == accion)
        if entidad:
            query = query.filter(Auditoria.entidad == entidad)
        return query.order_by(Auditoria.created_at.desc()).limit(limite).all()
