# Marketplace Flask – Versión 2

## Implementado en esta entrega

- Administración de prestadores: listado, búsqueda por nombre/correo/ubicación, filtro por estado, suspensión y reactivación.
- La reactivación exige al menos una certificación aprobada y vigente.
- Gestión de categorías y servicios: alta, edición y activación/desactivación.
- La eliminación administrativa ahora es lógica (desactivación) para conservar relaciones e historial.
- Carga de certificaciones PDF/JPG/JPEG/PNG en almacenamiento privado fuera de `static`.
- Descarga de documentos limitada al propietario del perfil o a un administrador.
- Protección CSRF global con Flask-WTF, formularios HTML y cabecera `X-CSRFToken` para AJAX.
- Auditoría de cambios de estado, evaluaciones, solicitudes y cambios del catálogo.
- Sincronización de certificaciones vencidas y actualización del estado del prestador.
- CLI `flask certificaciones-vencidas` para ejecutar la sincronización.
- Interfaz Bootstrap 5, DataTables y SweetAlert2.
- Pruebas automatizadas básicas con pytest.

## No incluido

- Integración con almacenamiento de objetos (S3, Cloudinary privado, MinIO).
- Antivirus/escaneo antimalware de documentos.
- Flujo de reservas, pagos, chat, geolocalización, calificaciones y disputas.
- Notificaciones por correo/SMS/WhatsApp.
- Despliegue o cambios en un entorno productivo.
