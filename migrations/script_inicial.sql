
-- =====================================================
-- 1. EXTENSIONES
-- =====================================================

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
