-- SCRIPT INICIAL
-- =====================================================
-- 1. EXTENSIONES
-- =====================================================
SELECT version(); --PostgreSQL 18.3 on x86_64-windows, compiled by msvc-19.44.35223, 64-bit

CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- 2. USUARIOS
-- =====================================================

CREATE TABLE usuarios (
    id BIGSERIAL PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    telefono VARCHAR(20),

    rol VARCHAR(20) NOT NULL
        CHECK (rol IN ('ADMIN', 'CLIENTE', 'PRESTADOR')),

    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. CATEGORIAS
-- =====================================================

CREATE TABLE categorias (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

-- =====================================================
-- 4. SERVICIOS
-- =====================================================

CREATE TABLE servicios (
    id BIGSERIAL PRIMARY KEY,
    categoria_id BIGINT NOT NULL
        REFERENCES categorias(id),

    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

-- =====================================================
-- 5. PERFIL PROFESIONAL
-- =====================================================

CREATE TABLE perfil_profesional (
    id BIGSERIAL PRIMARY KEY,

    usuario_id BIGINT UNIQUE NOT NULL
        REFERENCES usuarios(id),

    descripcion TEXT NOT NULL,

    experiencia_anios INTEGER DEFAULT 0,

    ciudad VARCHAR(100) NOT NULL,
    distrito VARCHAR(100),

    latitud NUMERIC(10,7),
    longitud NUMERIC(10,7),

    embedding VECTOR(384),

    puntuacion NUMERIC(3,2) DEFAULT 0,
    trabajos_completados INTEGER DEFAULT 0,

    certificado BOOLEAN DEFAULT FALSE,

    estado VARCHAR(20) DEFAULT 'PENDIENTE'
        CHECK (estado IN (
            'PENDIENTE',
            'ACTIVO',
            'SUSPENDIDO',
            'RECHAZADO'
        )),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 6. ESPECIALIDADES DEL PRESTADOR
-- =====================================================

CREATE TABLE perfil_categorias (
    id BIGSERIAL PRIMARY KEY,

    perfil_id BIGINT NOT NULL
        REFERENCES perfil_profesional(id),

    categoria_id BIGINT NOT NULL
        REFERENCES categorias(id),

    UNIQUE(perfil_id, categoria_id)
);

-- =====================================================
-- 7. CERTIFICACIONES
-- =====================================================

CREATE TABLE certificaciones (
    id BIGSERIAL PRIMARY KEY,

    perfil_id BIGINT NOT NULL
        REFERENCES perfil_profesional(id),

    tipo VARCHAR(100) NOT NULL,
    observaciones TEXT,

    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN (
            'PENDIENTE',
            'APROBADA',
            'RECHAZADA',
            'VENCIDA'
        )),

    fecha_emision DATE,
    fecha_vencimiento DATE,

    evaluador_id BIGINT REFERENCES usuarios(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 8. DEMANDAS
-- =====================================================

CREATE TABLE demandas (
    id BIGSERIAL PRIMARY KEY,

    cliente_id BIGINT NOT NULL
        REFERENCES usuarios(id),

    categoria_id BIGINT NOT NULL
        REFERENCES categorias(id),

    servicio_id BIGINT REFERENCES servicios(id),

    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,

    embedding VECTOR(384),

    ciudad VARCHAR(100) NOT NULL,
    distrito VARCHAR(100) NOT NULL,

    latitud NUMERIC(10,7),
    longitud NUMERIC(10,7),

    presupuesto NUMERIC(12,2),

    estado VARCHAR(25) DEFAULT 'PUBLICADA'
        CHECK (estado IN (
            'BORRADOR',
            'PUBLICADA',
            'EN_MATCHING',
            'ASIGNADA',
            'EN_PROCESO',
            'COMPLETADA',
            'CANCELADA'
        )),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 9. MATCHES
-- =====================================================

CREATE TABLE matches (
    id BIGSERIAL PRIMARY KEY,

    demanda_id BIGINT NOT NULL
        REFERENCES demandas(id),

    perfil_id BIGINT NOT NULL
        REFERENCES perfil_profesional(id),

    similitud NUMERIC(8,6),
    score NUMERIC(8,6),

    estado VARCHAR(20) DEFAULT 'PENDIENTE'
        CHECK (estado IN (
            'PENDIENTE',
            'NOTIFICADO',
            'ACEPTADO',
            'RECHAZADO',
            'EXPIRADO'
        )),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(demanda_id, perfil_id)
);

-- =====================================================
-- 10. CONTRATOS
-- =====================================================

CREATE TABLE contratos (
    id BIGSERIAL PRIMARY KEY,

    demanda_id BIGINT NOT NULL
        REFERENCES demandas(id),

    prestador_id BIGINT NOT NULL
        REFERENCES usuarios(id),

    monto NUMERIC(12,2) NOT NULL,

    estado VARCHAR(20) DEFAULT 'PENDIENTE'
        CHECK (estado IN (
            'PENDIENTE',
            'ACEPTADO',
            'EN_PROCESO',
            'COMPLETADO',
            'CANCELADO'
        )),

    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 11. CALIFICACIONES
-- =====================================================

CREATE TABLE calificaciones (
    id BIGSERIAL PRIMARY KEY,

    contrato_id BIGINT UNIQUE NOT NULL
        REFERENCES contratos(id),

    cliente_id BIGINT NOT NULL
        REFERENCES usuarios(id),

    prestador_id BIGINT NOT NULL
        REFERENCES usuarios(id),

    estrellas INTEGER NOT NULL
        CHECK (estrellas BETWEEN 1 AND 5),

    comentario TEXT,

    hitos JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 12. INDICES
-- =====================================================

CREATE INDEX idx_perfil_estado
ON perfil_profesional(estado, certificado);

CREATE INDEX idx_perfil_ciudad
ON perfil_profesional(ciudad, distrito);

CREATE INDEX idx_perfil_categorias
ON perfil_categorias(categoria_id, perfil_id);

CREATE INDEX idx_demanda_cliente
ON demandas(cliente_id);

CREATE INDEX idx_demanda_estado
ON demandas(estado);

CREATE INDEX idx_matches_demanda
ON matches(demanda_id, score DESC);

CREATE INDEX idx_certificaciones_vigencia
ON certificaciones(perfil_id, estado, fecha_vencimiento);

-- Índices vectoriales para búsqueda aproximada.
CREATE INDEX idx_perfil_embedding
ON perfil_profesional
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_demanda_embedding
ON demandas
USING hnsw (embedding vector_cosine_ops);

-- SCRIPT CAMIOS

CREATE TABLE ubicaciones (
    id SERIAL PRIMARY KEY,
    perfil_id INTEGER NOT NULL UNIQUE,
    departamento VARCHAR(100) NOT NULL,
    provincia VARCHAR(100) NOT NULL,
    distrito VARCHAR(100) NOT NULL,
    direccion VARCHAR(250),
    referencia VARCHAR(250),
    latitud NUMERIC(10, 7),
    longitud NUMERIC(10, 7),
    radio_atencion_km NUMERIC(6, 2) NOT NULL DEFAULT 10,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    
    CONSTRAINT fk_ubicaciones_perfil
        FOREIGN KEY (perfil_id)
        REFERENCES perfil_profesional (id)
        ON DELETE CASCADE
);



-- Índice explícito (aunque UNIQUE ya crea un índice automático en PostgreSQL)
CREATE INDEX idx_ubicaciones_perfil_id ON ubicaciones (perfil_id);

-- Función y trigger para replicar el comportamiento de onupdate=datetime.utcnow
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = (NOW() AT TIME ZONE 'utc');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_ubicaciones_updated_at
    BEFORE UPDATE ON ubicaciones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    Descripcion VARCHAR(100) NOT NULL
	
    CONSTRAINT fk_ubicaciones_perfil
        FOREIGN KEY (perfil_id)
        REFERENCES perfil_profesional (id)
        ON DELETE CASCADE
);

select * from perfil_profesional;
select * from perfil_categorias;
select * from usuarios;

select * from categorias;
select * from servicios;

-- Agregamos la columnas faltantes a servicios
-- 1. Agregar las columnas (usando IF NOT EXISTS por seguridad)
ALTER TABLE servicios
    ADD COLUMN IF NOT EXISTS categoria_id INTEGER,
    ADD COLUMN IF NOT EXISTS nombre VARCHAR(150),
    ADD COLUMN IF NOT EXISTS descripcion TEXT,
    ADD COLUMN IF NOT EXISTS precio_referencial NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC');

-- 2. Asegurar valores por defecto en registros existentes antes de aplicar NOT NULL
UPDATE servicios SET activo = TRUE WHERE activo IS NULL;
UPDATE servicios SET created_at = (NOW() AT TIME ZONE 'UTC') WHERE created_at IS NULL;

-- 3. Aplicar restricciones NOT NULL y DEFAULT
-- (Asegúrate de que 'categoria_id' y 'nombre' no tengan valores NULL en filas previas)
ALTER TABLE servicios
    ALTER COLUMN categoria_id SET NOT NULL,
    ALTER COLUMN nombre SET NOT NULL,
    ALTER COLUMN activo SET NOT NULL,
    ALTER COLUMN activo SET DEFAULT TRUE,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN created_at SET DEFAULT (NOW() AT TIME ZONE 'UTC');

-- 4. Agregar la llave primaria (solo si tu tabla aún no tiene una)
-- ALTER TABLE servicios ADD PRIMARY KEY (id);

-- 5. Agregar la llave foránea hacia categorías
ALTER TABLE servicios
    ADD CONSTRAINT fk_servicios_categoria
    FOREIGN KEY (categoria_id)
    REFERENCES categorias (id)
    ON DELETE RESTRICT;

-- 6. Crear los índices correspondientes
CREATE INDEX IF NOT EXISTS idx_servicios_categoria_id ON servicios (categoria_id);
CREATE INDEX IF NOT EXISTS idx_servicios_activo ON servicios (activo);

-- Agregamos 
-- 1. Crear la columna permitiendo nulos temporalmente
ALTER TABLE perfil_profesional 
ADD COLUMN categoria_id INTEGER;

-- 2. (Opcional) Si ya tienes filas en la tabla, asígnales un ID de categoría existente (ej. 1)
UPDATE perfil_profesional 
SET categoria_id = 1 
WHERE categoria_id IS NULL;

-- 3. Marcar la columna como NOT NULL
ALTER TABLE perfil_profesional 
ALTER COLUMN categoria_id SET NOT NULL;

-- 4. Crear la llave foránea hacia la tabla categorias
ALTER TABLE perfil_profesional
ADD CONSTRAINT fk_perfil_profesional_categoria
FOREIGN KEY (categoria_id) 
REFERENCES categorias(id);


-- 1. Migrar categorías existentes de perfil_profesional a perfil_categorias (si ya tienes datos)
INSERT INTO perfil_categorias (perfil_id, categoria_id)
SELECT id, categoria_id 
FROM perfil_profesional 
WHERE categoria_id IS NOT NULL
ON CONFLICT DO NOTHING;


-- 2. Eliminar la columna redundante categoria_id
ALTER TABLE perfil_profesional DROP COLUMN IF EXISTS categoria_id;

-- 3. Asegurar restricción única en tabla intermedia
ALTER TABLE perfil_categorias
ADD CONSTRAINT uq_perfil_categoria UNIQUE (perfil_id, categoria_id);

--
ALTER TABLE usuarios
    ALTER COLUMN password_hash DROP NOT NULL;

CREATE TABLE IF NOT EXISTS identidades_oauth (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL
        REFERENCES usuarios(id) ON DELETE CASCADE,
    proveedor VARCHAR(30) NOT NULL,
    proveedor_usuario_id VARCHAR(255) NOT NULL,
    email_proveedor VARCHAR(150),
    creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_identidad_oauth_proveedor_usuario
        UNIQUE (proveedor, proveedor_usuario_id)
);

CREATE INDEX IF NOT EXISTS ix_identidades_oauth_usuario_id
    ON identidades_oauth(usuario_id);

-- crea tabla auditoria
CREATE TABLE auditoria (
    -- Nota: Cambia SERIAL/INTEGER por UUID o BIGINT según el tipo real de tu variable ID_TYPE
    id SERIAL PRIMARY KEY,
    actor_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    accion VARCHAR(80) NOT NULL,
    entidad VARCHAR(80) NOT NULL,
    entidad_id VARCHAR(80),
    detalles JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip VARCHAR(64),
    user_agent VARCHAR(300),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- Índices definidos en el modelo (index=True)
CREATE INDEX ix_auditoria_accion ON auditoria (accion);
CREATE INDEX ix_auditoria_entidad ON auditoria (entidad);
CREATE INDEX ix_auditoria_entidad_id ON auditoria (entidad_id);
CREATE INDEX ix_auditoria_created_at ON auditoria (created_at);

-- version 3:

-- 2. Asegurar valores por defecto en registros existentes antes de aplicar NOT NULL
UPDATE servicios SET activo = TRUE WHERE activo IS NULL;
UPDATE servicios SET created_at = (NOW() AT TIME ZONE 'UTC') WHERE created_at IS NULL;

-- 3. Aplicar restricciones NOT NULL y DEFAULT
-- (Asegúrate de que 'categoria_id' y 'nombre' no tengan valores NULL en filas previas)
ALTER TABLE servicios
    ALTER COLUMN categoria_id SET NOT NULL,
    ALTER COLUMN nombre SET NOT NULL,
    ALTER COLUMN activo SET NOT NULL,
    ALTER COLUMN activo SET DEFAULT TRUE,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN created_at SET DEFAULT (NOW() AT TIME ZONE 'UTC');

-- 4. Agregar la llave primaria (solo si tu tabla aún no tiene una)
-- ALTER TABLE servicios ADD PRIMARY KEY (id);

-- 6. Crear los índices correspondientes
CREATE INDEX IF NOT EXISTS idx_servicios_categoria_id ON servicios (categoria_id);
CREATE INDEX IF NOT EXISTS idx_servicios_activo ON servicios (activo);

-- Agregamos 
-- 1. Crear la columna permitiendo nulos temporalmente
ALTER TABLE perfil_profesional 
ADD COLUMN categoria_id INTEGER;

-- 2. (Opcional) Si ya tienes filas en la tabla, asígnales un ID de categoría existente (ej. 1)
UPDATE perfil_profesional 
SET categoria_id = 1 
WHERE categoria_id IS NULL;

-- 3. Marcar la columna como NOT NULL
ALTER TABLE perfil_profesional 
ALTER COLUMN categoria_id SET NOT NULL;

-- 4. Crear la llave foránea hacia la tabla categorias
ALTER TABLE perfil_profesional
ADD CONSTRAINT fk_perfil_profesional_categoria
FOREIGN KEY (categoria_id) 
REFERENCES categorias(id);


-- 1. Migrar categorías existentes de perfil_profesional a perfil_categorias (si ya tienes datos)
INSERT INTO perfil_categorias (perfil_id, categoria_id)
SELECT id, categoria_id 
FROM perfil_profesional 
WHERE categoria_id IS NOT NULL
ON CONFLICT DO NOTHING;


-- 2. Eliminar la columna redundante categoria_id
ALTER TABLE perfil_profesional DROP COLUMN IF EXISTS categoria_id;


-- SCRIPT MACTCHING_GEOLOCALIZATION

-- ================================================================
-- AppMarketplace: roles múltiples + matching geográfico
-- Ejecutar UNA SOLA VEZ sobre la base existente, después de backup.
-- Compatible con PostgreSQL.
-- ================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Catálogo de roles. Se conserva usuarios.rol como rol principal
-- para compatibilidad; usuario_roles almacena todos los roles asignados.
CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(80) NOT NULL
);

ALTER TABLE roles ADD COLUMN IF NOT EXISTS codigo VARCHAR(20);
ALTER TABLE roles ADD COLUMN IF NOT EXISTS nombre VARCHAR(80);

-- Si existía una tabla roles antigua/incompleta, conservar sus filas.
UPDATE roles
SET codigo = 'ROL_' || id::text
WHERE codigo IS NULL OR btrim(codigo) = '';

UPDATE roles
SET nombre = COALESCE(NULLIF(btrim(nombre), ''), codigo)
WHERE nombre IS NULL OR btrim(nombre) = '';

ALTER TABLE roles ALTER COLUMN codigo SET NOT NULL;
ALTER TABLE roles ALTER COLUMN nombre SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_codigo ON roles(codigo);

INSERT INTO roles (codigo, nombre) VALUES
    ('ADMIN', 'Administrador'),
    ('CLIENTE', 'Cliente'),
    ('PRESTADOR', 'Prestador de servicios')
ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre;

-- Normalizar el valor heredado y conservarlo como rol principal.
UPDATE usuarios SET rol = upper(rol) WHERE rol IS NOT NULL;

-- Incluir también cualquier rol principal adicional que ya exista.
INSERT INTO roles (codigo, nombre)
SELECT DISTINCT upper(u.rol), initcap(lower(u.rol))
FROM usuarios u
WHERE u.rol IS NOT NULL AND btrim(u.rol) <> ''
ON CONFLICT (codigo) DO NOTHING;

CREATE TABLE IF NOT EXISTS usuario_roles (
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    rol_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, rol_id)
);

CREATE INDEX IF NOT EXISTS ix_usuario_roles_rol_id ON usuario_roles(rol_id);

-- Migración de rol único actual a relación de roles.
INSERT INTO usuario_roles (usuario_id, rol_id)
SELECT u.id, r.id
FROM usuarios u
JOIN roles r ON r.codigo = upper(u.rol)
ON CONFLICT (usuario_id, rol_id) DO NOTHING;

-- 2. Google puede crear usuarios sin contraseña local.
ALTER TABLE usuarios ALTER COLUMN password_hash DROP NOT NULL;

-- 3. Coordenadas de la demanda y referencias de dirección.
ALTER TABLE demandas ADD COLUMN IF NOT EXISTS latitud NUMERIC(10,7);
ALTER TABLE demandas ADD COLUMN IF NOT EXISTS longitud NUMERIC(10,7);
ALTER TABLE demandas ADD COLUMN IF NOT EXISTS direccion VARCHAR(250);
ALTER TABLE demandas ADD COLUMN IF NOT EXISTS referencia VARCHAR(250);

-- 4. Desglose del score de matching.
ALTER TABLE matches ADD COLUMN IF NOT EXISTS reputacion NUMERIC(8,6);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS proximidad NUMERIC(8,6);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS distancia_km NUMERIC(10,3);

-- 5. Tabla de ubicaciones por prestador, si aún no existe.
drop table ubicaciones;
--
CREATE TABLE IF NOT EXISTS ubicaciones (
    id BIGSERIAL PRIMARY KEY,
    perfil_id BIGINT NOT NULL UNIQUE REFERENCES perfil_profesional(id) ON DELETE CASCADE,
    departamento VARCHAR(100) NOT NULL,
    provincia VARCHAR(100) NOT NULL,
    distrito VARCHAR(100) NOT NULL,
    direccion VARCHAR(250),
    referencia VARCHAR(250),
    latitud NUMERIC(10,7),
    longitud NUMERIC(10,7),
    radio_atencion_km NUMERIC(6,2) NOT NULL DEFAULT 10,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_ubicaciones_perfil_id ON ubicaciones(perfil_id);
CREATE INDEX IF NOT EXISTS ix_ubicaciones_coordenadas
    ON ubicaciones(latitud, longitud) WHERE activo = TRUE;
CREATE INDEX IF NOT EXISTS ix_demandas_cliente_id ON demandas(cliente_id);
CREATE INDEX IF NOT EXISTS ix_matches_demanda_score ON matches(demanda_id, score DESC);

-- Impide duplicar al mismo prestador dentro de una misma demanda.
-- Si existen duplicados históricos, revisar antes de crear este índice.
CREATE UNIQUE INDEX IF NOT EXISTS uq_matches_demanda_perfil
    ON matches(demanda_id, perfil_id);


-- Ejecutar una sola vez sobre la base de datos existente de AppMarketplace.
-- Las cuentas locales conservan su hash; las cuentas exclusivamente sociales
-- pueden tener password_hash = NULL.

ALTER TABLE usuarios
    ALTER COLUMN password_hash DROP NOT NULL;

CREATE TABLE IF NOT EXISTS identidades_oauth (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL
        REFERENCES usuarios(id) ON DELETE CASCADE,
    proveedor VARCHAR(30) NOT NULL,
    proveedor_usuario_id VARCHAR(255) NOT NULL,
    email_proveedor VARCHAR(150),
    creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_identidad_oauth_proveedor_usuario
        UNIQUE (proveedor, proveedor_usuario_id)
);

CREATE INDEX IF NOT EXISTS ix_identidades_oauth_usuario_id
    ON identidades_oauth(usuario_id);

-- Migración incremental: soporte de dirección y geolocalización en demandas.
-- Ejecutar una sola vez sobre la base PostgreSQL del proyecto.


ALTER TABLE demandas
    ADD COLUMN IF NOT EXISTS direccion VARCHAR(250),
    ADD COLUMN IF NOT EXISTS referencia VARCHAR(250),
    ADD COLUMN IF NOT EXISTS latitud NUMERIC(10, 7),
    ADD COLUMN IF NOT EXISTS longitud NUMERIC(10, 7);

-- Evita guardar solo una coordenada. Las dos pueden quedar NULL.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_demandas_coordenadas_pareadas'
    ) THEN
        ALTER TABLE demandas
            ADD CONSTRAINT ck_demandas_coordenadas_pareadas
            CHECK ((latitud IS NULL AND longitud IS NULL)
                OR (latitud IS NOT NULL AND longitud IS NOT NULL));
    END IF;
END $$;


-- icono a categoria

ALTER TABLE categorias
 ADD COLUMN IF NOT EXISTS icono VARCHAR(250);


--
-- Ejecutar una sola vez en PostgreSQL.
-- Guarda el servicio específico elegido dentro de la solicitud.
ALTER TABLE demandas
    ADD COLUMN IF NOT EXISTS servicio_id BIGINT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_demandas_servicio_id'
    ) THEN
        ALTER TABLE demandas
            ADD CONSTRAINT fk_demandas_servicio_id
            FOREIGN KEY (servicio_id) REFERENCES servicios(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_demandas_servicio_id
    ON demandas(servicio_id);


--
-- El modelo Servicio ya contempla precio_referencial; el script inicial no lo crea.
ALTER TABLE servicios
    ADD COLUMN IF NOT EXISTS precio_referencial NUMERIC(10,2);

-- Asegurar columnas de descripción/icono en categorías para que el modelo coincida.
ALTER TABLE categorias
    ADD COLUMN IF NOT EXISTS descripcion TEXT;
ALTER TABLE categorias
    ADD COLUMN IF NOT EXISTS icono VARCHAR(100);

-- Datos de respaldo documental y evaluación de certificaciones.
ALTER TABLE certificaciones
    ADD COLUMN IF NOT EXISTS descripcion TEXT;
ALTER TABLE certificaciones
    ADD COLUMN IF NOT EXISTS documento_path VARCHAR(500);
ALTER TABLE certificaciones
    ADD COLUMN IF NOT EXISTS documento_nombre VARCHAR(255);
ALTER TABLE certificaciones
    ADD COLUMN IF NOT EXISTS documento_mime VARCHAR(120);
ALTER TABLE certificaciones
    ADD COLUMN IF NOT EXISTS observaciones_admin TEXT;
ALTER TABLE certificaciones
    ADD COLUMN IF NOT EXISTS evaluado_at TIMESTAMP;

-- La solicitud inicial la registra el prestador; el evaluador solo existe al evaluar.
ALTER TABLE certificaciones
    ALTER COLUMN evaluador_id DROP NOT NULL;

CREATE INDEX IF NOT EXISTS ix_servicios_categoria_activo
    ON servicios (categoria_id, activo);
CREATE INDEX IF NOT EXISTS ix_certificaciones_estado_created
    ON certificaciones (estado, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_certificaciones_perfil
    ON certificaciones (perfil_id);


select * from usuarios;
select * from perfil_profesional;
select * from perfil_categorias;
select * from servicios;
select * from categorias;
select * from certificaciones;
select * from auditoria;



