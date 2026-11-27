# Autenticación local y Google

## 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

Se incorpora Authlib para OAuth 2.0 / OpenID Connect.

## 2. Configurar Google Cloud

En Google Cloud Console:

1. Crear o seleccionar un proyecto.
2. Configurar la pantalla de consentimiento OAuth.
3. Crear un ID de cliente OAuth de tipo Aplicación web.
4. Agregar los orígenes autorizados de JavaScript:
   - `http://127.0.0.1:5005`
   - `http://localhost:5005` (si se utiliza esta dirección)
5. Agregar URI de redirección autorizada:
   - `http://127.0.0.1:5005/auth/google/callback`
   - En producción, `https://TU-DOMINIO/auth/google/callback`.

La URI debe coincidir exactamente con la dirección desde la que se abre la aplicación.

## 3. Variables de entorno

Copiar `.env.example` a `.env` y completar:

```env
SECRET_KEY=una-clave-larga-aleatoria
DATABASE_URL=postgresql+psycopg://usuario:clave@localhost:5432/App_MarketPlace
GOOGLE_CLIENT_ID=valor-del-cliente
GOOGLE_CLIENT_SECRET=secreto-del-cliente
SESSION_COOKIE_SECURE=false
```

En producción usar HTTPS y `SESSION_COOKIE_SECURE=true`.
No subir `.env` al repositorio ni compartir el secreto de Google.

## 4. Aplicar cambio en PostgreSQL

Ejecutar una sola vez el archivo:

`migrations/oauth_social.sql`

El cambio permite que `password_hash` sea NULL para usuarios que se autentican exclusivamente con Google y crea la tabla de identidades externas.

Antes de ejecutarlo, realizar un respaldo de la base de datos.

## 5. Rutas disponibles

- `GET /auth/google?rol=CLIENTE`: acceso/registro Google como cliente.
- `GET /auth/google?rol=PRESTADOR`: acceso/registro Google como prestador.
- `GET /auth/google/callback`: retorno autorizado de Google.
- `GET /auth/google/link`: requiere sesión iniciada y vincula Google a la cuenta actual.

Si el correo Google ya pertenece a una cuenta local, no se fusionan cuentas automáticamente. El usuario debe iniciar sesión primero con su método actual y usar **Vincular Google**. La vinculación exige que Google confirme el correo y que coincida con el correo de la cuenta autenticada.

## 6. Pruebas manuales

1. Crear una cuenta CLIENTE con correo y contraseña.
2. Cerrar sesión e iniciar sesión con esa cuenta.
3. Pulsar **Vincular Google** y autorizar el mismo correo.
4. Cerrar sesión e ingresar con Google.
5. Probar el registro Google como CLIENTE con un correo nuevo.
6. Repetir el registro Google como PRESTADOR y comprobar que se crea `perfil_profesional` en estado `PENDIENTE`.
7. Probar un usuario desactivado y confirmar que no puede iniciar sesión.

Facebook, Apple y Microsoft todavía no están habilitados; el modelo de identidades permite agregarlos después, pero cada proveedor necesita su propia configuración y callback validado.
