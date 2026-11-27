from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from werkzeug.datastructures import FileStorage
from app.extensions.database import db
from app.models import Usuario, PerfilProfesional, Certificacion, Categoria, Servicio, Auditoria
from app.services.prestador_service import PrestadorService
from app.services.certificacion_service import CertificacionService
from app.services.catalogo_service import CatalogoService


def crear_usuario_prestador():
    user = Usuario(
        nombres="Ana",
        apellidos="Prueba",
        email="ana@example.test",
        rol="PRESTADOR",
        activo=True,
    )
    user.set_password("ClaveSegura123")
    db.session.add(user)
    db.session.flush()
    perfil = PerfilProfesional(
        usuario_id=user.id,
        ciudad="Ayacucho",
        distrito="Ayacucho",
        estado="PENDIENTE",
        certificado=False,
    )
    db.session.add(perfil)
    db.session.commit()
    return user, perfil


def test_rutas_v2_registradas(app):
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/admin/prestadores" in rules
    assert "/admin/auditoria" in rules
    assert "/prestadores/certificaciones" in rules
    assert "/admin/certificaciones/<int:certificacion_id>/documento" in rules
    assert "/admin/servicios/<int:servicio_id>" in rules


def test_no_permite_activar_prestador_sin_certificacion(app):
    with app.app_context():
        _, perfil = crear_usuario_prestador()
        try:
            PrestadorService.cambiar_estado(perfil.id, "ACTIVO", actor_id=None)
            assert False, "Debió exigir una certificación vigente."
        except ValueError as exc:
            assert "certificación aprobada y vigente" in str(exc)


def test_suspender_y_reactivar_prestador_con_certificacion_vigente(app):
    with app.app_context():
        _, perfil = crear_usuario_prestador()
        cert = Certificacion(
            perfil_id=perfil.id,
            tipo="Certificado técnico",
            estado="APROBADA",
            fecha_vencimiento=date.today() + timedelta(days=60),
        )
        db.session.add(cert)
        perfil.certificado = True
        db.session.commit()

        PrestadorService.cambiar_estado(perfil.id, "ACTIVO")
        assert db.session.get(PerfilProfesional, perfil.id).estado == "ACTIVO"

        PrestadorService.cambiar_estado(perfil.id, "SUSPENDIDO")
        assert db.session.get(PerfilProfesional, perfil.id).estado == "SUSPENDIDO"

        PrestadorService.cambiar_estado(perfil.id, "ACTIVO")
        assert db.session.get(PerfilProfesional, perfil.id).estado == "ACTIVO"
        assert Auditoria.query.filter_by(accion="PRESTADOR_ESTADO_CAMBIADO").count() == 3


def test_sincroniza_certificacion_vencida(app):
    with app.app_context():
        _, perfil = crear_usuario_prestador()
        cert = Certificacion(
            perfil_id=perfil.id,
            tipo="Carné vencido",
            estado="APROBADA",
            fecha_vencimiento=date.today() - timedelta(days=1),
        )
        db.session.add(cert)
        perfil.estado = "ACTIVO"
        perfil.certificado = True
        db.session.commit()

        total = CertificacionService.sincronizar_vencimientos()
        db.session.refresh(cert)
        db.session.refresh(perfil)
        assert total == 1
        assert cert.estado == "VENCIDA"
        assert perfil.certificado is False
        assert perfil.estado == "PENDIENTE"
        assert Auditoria.query.filter_by(accion="CERTIFICACION_VENCIDA").count() == 1


def test_catalogo_crud_logico_y_auditoria(app):
    with app.app_context():
        categoria = CatalogoService.guardar_categoria({"nombre": "Gasfitería"})
        servicio = CatalogoService.guardar_servicio({
            "nombre": "Reparación de grifo",
            "categoria_id": categoria.id,
            "precio_referencial": "45.50",
        })
        assert servicio.categoria_id == categoria.id
        CatalogoService.cambiar_estado_servicio(servicio.id, False)
        CatalogoService.cambiar_estado_categoria(categoria.id, False)
        db.session.refresh(servicio)
        db.session.refresh(categoria)
        assert servicio.activo is False
        assert categoria.activo is False
        assert Auditoria.query.count() >= 4


def test_documento_se_guarda_en_almacenamiento_privado(app):
    with app.app_context():
        _, perfil = crear_usuario_prestador()
        archivo = FileStorage(
            stream=BytesIO(b"%PDF-1.7\nDocumento de prueba"),
            filename="certificado.pdf",
            content_type="application/pdf",
        )
        cert = CertificacionService.crear(
            perfil.id,
            {"tipo": "Certificado de prueba", "fecha_emision": "2026-01-01"},
            archivo,
        )
        ruta = Path(app.config["PRIVATE_UPLOAD_FOLDER"]) / cert.documento_path
        assert ruta.exists()
        assert ruta.is_file()
        assert cert.documento_mime == "application/pdf"
        assert cert.documento_size > 0
        assert "static" not in ruta.parts
