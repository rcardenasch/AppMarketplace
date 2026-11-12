import re
import unicodedata
from decimal import Decimal, InvalidOperation
from sqlalchemy import or_
from app.extensions.database import db
from app.models import Categoria, Servicio
from app.services.auditoria_service import AuditoriaService


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.lower().strip())
    return ascii_value.strip("-")


class CatalogoService:
    @staticmethod
    def listar_categorias(solo_activas=False):
        query = Categoria.query
        if solo_activas:
            query = query.filter(Categoria.activo.is_(True))
        return query.order_by(Categoria.nombre.asc()).all()

    @staticmethod
    def guardar_categoria(
        datos, categoria_id=None, actor_id=None, ip=None, user_agent=None
    ):
        nombre = (datos.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre de la categoría es obligatorio.")
        if len(nombre) > 100:
            raise ValueError("El nombre no debe superar 100 caracteres.")

        categoria = db.session.get(Categoria, categoria_id) if categoria_id else Categoria()
        if categoria_id and not categoria:
            raise ValueError("Categoría no encontrada.")

        duplicada = Categoria.query.filter(
            Categoria.nombre.ilike(nombre),
            Categoria.id != (categoria.id or 0),
        ).first()
        if duplicada:
            raise ValueError("Ya existe una categoría con ese nombre.")

        slug = slugify(nombre) or "categoria"
        slug_query = Categoria.query.filter(Categoria.slug == slug)
        if categoria.id:
            slug_query = slug_query.filter(Categoria.id != categoria.id)
        if slug_query.first():
            slug = f"{slug}-{categoria.id or 'nueva'}"

        anterior = {
            "nombre": categoria.nombre,
            "activo": categoria.activo,
        } if categoria.id else None

        categoria.nombre = nombre
        categoria.slug = slug
        categoria.descripcion = (datos.get("descripcion") or "").strip() or None
        categoria.activo = bool(datos.get("activo", True))
        db.session.add(categoria)
        db.session.flush()

        AuditoriaService.registrar(
            actor_id=actor_id,
            accion="CATEGORIA_GUARDADA",
            entidad="Categoria",
            entidad_id=categoria.id,
            detalles={"anterior": anterior, "nombre": nombre, "activo": categoria.activo},
            ip=ip,
            user_agent=user_agent,
        )
        db.session.commit()
        return categoria

    @staticmethod
    def cambiar_estado_categoria(
        categoria_id, activo, actor_id=None, ip=None, user_agent=None
    ):
        categoria = db.session.get(Categoria, categoria_id)
        if not categoria:
            raise ValueError("Categoría no encontrada.")
        anterior = categoria.activo
        categoria.activo = bool(activo)
        AuditoriaService.registrar(
            actor_id=actor_id,
            accion="CATEGORIA_ESTADO_CAMBIADO",
            entidad="Categoria",
            entidad_id=categoria.id,
            detalles={"activo_anterior": anterior, "activo_nuevo": categoria.activo},
            ip=ip,
            user_agent=user_agent,
        )
        db.session.commit()
        return categoria

    @staticmethod
    def eliminar_categoria(categoria_id, actor_id=None, ip=None, user_agent=None):
        # Compatibilidad con la ruta antigua: ahora se desactiva para preservar historial.
        return CatalogoService.cambiar_estado_categoria(
            categoria_id, False, actor_id, ip, user_agent
        )

    @staticmethod
    def listar_servicios(solo_activos=False):
        query = Servicio.query.join(Categoria)
        if solo_activos:
            query = query.filter(
                Servicio.activo.is_(True), Categoria.activo.is_(True)
            )
        return query.order_by(Categoria.nombre, Servicio.nombre).all()

    @staticmethod
    def guardar_servicio(
        datos, servicio_id=None, actor_id=None, ip=None, user_agent=None
    ):
        nombre = (datos.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre del servicio es obligatorio.")
        if len(nombre) > 150:
            raise ValueError("El nombre no debe superar 150 caracteres.")
        try:
            categoria_id = int(datos.get("categoria_id"))
        except (TypeError, ValueError):
            raise ValueError("Selecciona una categoría válida.")

        categoria = db.session.get(Categoria, categoria_id)
        if not categoria or not categoria.activo:
            raise ValueError("Selecciona una categoría activa.")

        servicio = db.session.get(Servicio, servicio_id) if servicio_id else Servicio()
        if servicio_id and not servicio:
            raise ValueError("Servicio no encontrado.")

        precio_raw = datos.get("precio_referencial")
        if precio_raw in ("", None):
            precio = None
        else:
            try:
                precio = Decimal(str(precio_raw)).quantize(Decimal("0.01"))
            except (InvalidOperation, ValueError):
                raise ValueError("El precio referencial no es válido.")
            if precio < 0:
                raise ValueError("El precio no puede ser negativo.")

        anterior = {
            "nombre": servicio.nombre,
            "categoria_id": servicio.categoria_id,
            "activo": servicio.activo,
        } if servicio.id else None

        servicio.categoria_id = categoria.id
        servicio.nombre = nombre
        servicio.descripcion = (datos.get("descripcion") or "").strip() or None
        servicio.precio_referencial = precio
        servicio.activo = bool(datos.get("activo", True))
        db.session.add(servicio)
        db.session.flush()

        AuditoriaService.registrar(
            actor_id=actor_id,
            accion="SERVICIO_GUARDADO",
            entidad="Servicio",
            entidad_id=servicio.id,
            detalles={
                "anterior": anterior,
                "nombre": nombre,
                "categoria_id": categoria.id,
                "activo": servicio.activo,
            },
            ip=ip,
            user_agent=user_agent,
        )
        db.session.commit()
        return servicio

    @staticmethod
    def cambiar_estado_servicio(
        servicio_id, activo, actor_id=None, ip=None, user_agent=None
    ):
        servicio = db.session.get(Servicio, servicio_id)
        if not servicio:
            raise ValueError("Servicio no encontrado.")
        anterior = servicio.activo
        servicio.activo = bool(activo)
        AuditoriaService.registrar(
            actor_id=actor_id,
            accion="SERVICIO_ESTADO_CAMBIADO",
            entidad="Servicio",
            entidad_id=servicio.id,
            detalles={"activo_anterior": anterior, "activo_nuevo": servicio.activo},
            ip=ip,
            user_agent=user_agent,
        )
        db.session.commit()
        return servicio

    @staticmethod
    def eliminar_servicio(servicio_id, actor_id=None, ip=None, user_agent=None):
        return CatalogoService.cambiar_estado_servicio(
            servicio_id, False, actor_id, ip, user_agent
        )
