import uuid
from datetime import date, datetime
from pathlib import Path
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions.database import db
from app.models import Certificacion
from app.models.perfil_profesional import PerfilProfesional
from app.services.auditoria_service import AuditoriaService

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


class CertificacionService:

    @staticmethod
    def listar_certificaciones(estado=None):
        query = Certificacion.query
        if estado:
            query = query.filter(Certificacion.estado == estado)
        return query.order_by(Certificacion.created_at.desc()).all()

    @staticmethod
    def listar_por_perfil(perfil_id: int, solo_activas: bool = False):
        query = Certificacion.query.filter_by(perfil_id=perfil_id)
        if solo_activas:
            query = query.filter(Certificacion.estado == "APROBADA")
        return query.order_by(Certificacion.created_at.desc()).all()

    @staticmethod
    def obtener(certificacion_id: int) -> Certificacion:
        cert = Certificacion.query.get(certificacion_id)
        if not cert:
            raise ValueError("Certificación no encontrada.")
        return cert

    @staticmethod
    def crear(perfil_id: int, datos, archivo, actor_id: int, ip=None, user_agent=None) -> Certificacion:
        tipo = (datos.get("tipo") or "").strip()
        if not tipo:
            raise ValueError("El tipo de certificación es obligatorio.")

        descripcion = (datos.get("descripcion") or "").strip() or None
        fecha_emision = CertificacionService._parse_fecha(datos.get("fecha_emision"))
        fecha_vencimiento = CertificacionService._parse_fecha(datos.get("fecha_vencimiento"))

        if fecha_emision and fecha_vencimiento and fecha_vencimiento < fecha_emision:
            raise ValueError("La fecha de vencimiento no puede ser anterior a la fecha de emisión.")

        doc_path = doc_nombre = doc_mime = None
        if archivo and archivo.filename:
            doc_path, doc_nombre, doc_mime = CertificacionService._guardar_archivo(perfil_id, archivo)

        cert = Certificacion(
            perfil_id=perfil_id,
            tipo=tipo,
            descripcion=descripcion,
            documento_path=doc_path,
            documento_nombre=doc_nombre,
            documento_mime=doc_mime,
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            estado="PENDIENTE",
        )
        db.session.add(cert)
        db.session.commit()

        AuditoriaService.registrar(
            actor_id=actor_id,
            accion="SOLICITAR_CERTIFICACION",
            entidad="certificaciones",
            entidad_id=cert.id,
            ip=ip,
            user_agent=user_agent,
        )
        return cert

    @staticmethod
    def evaluar(certificacion_id: int, estado: str, observaciones: str, evaluador_id: int, ip=None, user_agent=None) -> Certificacion:
        if estado not in ("APROBADA", "RECHAZADA"):
            raise ValueError("Estado de evaluación inválido.")

        cert = CertificacionService.obtener(certificacion_id)
        cert.estado = estado
        cert.observaciones_admin = (observaciones or "").strip() or None
        cert.evaluador_id = evaluador_id
        cert.evaluado_at = datetime.utcnow()

        CertificacionService._actualizar_badge_perfil(cert.perfil_id)
        db.session.commit()

        AuditoriaService.registrar(
            actor_id=evaluador_id,
            accion=f"CERTIFICACION_{estado}",
            entidad="certificaciones",
            entidad_id=cert.id,
            ip=ip,
            user_agent=user_agent,
        )
        return cert

    @staticmethod
    def sincronizar_vencimientos() -> int:
        hoy = date.today()
        vencidas = (
            Certificacion.query
            .filter(
                Certificacion.estado == "APROBADA",
                Certificacion.fecha_vencimiento.isnot(None),
                Certificacion.fecha_vencimiento < hoy,
            )
            .all()
        )
        perfiles_afectados = set()
        for cert in vencidas:
            cert.estado = "VENCIDA"
            perfiles_afectados.add(cert.perfil_id)

        for perfil_id in perfiles_afectados:
            CertificacionService._actualizar_badge_perfil(perfil_id)

        db.session.commit()
        return len(vencidas)

    @staticmethod
    def _actualizar_badge_perfil(perfil_id: int):
        """Marca perfil.certificado = True si tiene al menos una certificación APROBADA vigente."""
        tiene_aprobada = (
            Certificacion.query
            .filter_by(perfil_id=perfil_id, estado="APROBADA")
            .first()
            is not None
        )
        perfil = PerfilProfesional.query.get(perfil_id)
        if perfil:
            perfil.certificado = tiene_aprobada

    @staticmethod
    def _parse_fecha(valor):
        if not valor:
            return None
        try:
            return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Formato de fecha inválido. Use AAAA-MM-DD.")

    @staticmethod
    def _guardar_archivo(perfil_id: int, archivo):
        nombre_original = secure_filename(archivo.filename)
        ext = nombre_original.rsplit(".", 1)[-1].lower() if "." in nombre_original else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError("Formato no permitido. Solo se aceptan archivos PDF, PNG, JPG o JPEG.")

        root = Path(current_app.config["PRIVATE_UPLOAD_FOLDER"]).resolve()
        subcarpeta = Path("certificaciones") / str(perfil_id)
        destino_dir = root / subcarpeta
        destino_dir.mkdir(parents=True, exist_ok=True)

        nombre_unico = f"{uuid.uuid4().hex}.{ext}"
        archivo.save(str(destino_dir / nombre_unico))

        ruta_relativa = (subcarpeta / nombre_unico).as_posix()
        return ruta_relativa, nombre_original, archivo.mimetype
