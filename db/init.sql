-- =============================================================
-- DASHBOARD SEACE — Modelo relacional inicial
-- =============================================================

-- Extensiones
CREATE EXTENSION IF NOT EXISTS unaccent;

-- -------------------------------------------------------------
-- Catálogos
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cat_regiones (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(2)  NOT NULL UNIQUE,
    nombre      VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_provincias (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(4)  NOT NULL UNIQUE,
    nombre      VARCHAR(100) NOT NULL,
    region_id   INTEGER REFERENCES cat_regiones(id)
);

CREATE TABLE IF NOT EXISTS cat_distritos (
    id          SERIAL PRIMARY KEY,
    ubigeo      VARCHAR(6)  NOT NULL UNIQUE,
    nombre      VARCHAR(100) NOT NULL,
    provincia_id INTEGER REFERENCES cat_provincias(id)
);

CREATE TABLE IF NOT EXISTS cat_tipos_proceso (
    id      SERIAL PRIMARY KEY,
    codigo  VARCHAR(20) NOT NULL UNIQUE,
    nombre  VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_estados (
    id      SERIAL PRIMARY KEY,
    codigo  VARCHAR(30) NOT NULL UNIQUE,
    nombre  VARCHAR(100) NOT NULL
);

-- -------------------------------------------------------------
-- Entidades contratantes
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS entidades (
    id              SERIAL PRIMARY KEY,
    ruc             VARCHAR(11) UNIQUE,
    nombre          VARCHAR(500) NOT NULL,
    nombre_norm     VARCHAR(500),   -- normalizado para búsqueda
    ubigeo          VARCHAR(6) REFERENCES cat_distritos(ubigeo),
    sector          VARCHAR(200),
    activa          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------
-- Procesos de contratación
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS procesos (
    id                  SERIAL PRIMARY KEY,
    nro_expediente      VARCHAR(50),
    codigo_seace        VARCHAR(100) NOT NULL UNIQUE,
    entidad_id          INTEGER NOT NULL REFERENCES entidades(id),
    tipo_proceso_id     INTEGER REFERENCES cat_tipos_proceso(id),
    estado_id           INTEGER REFERENCES cat_estados(id),
    objeto_contratacion VARCHAR(2000),
    descripcion         TEXT,
    valor_referencial   NUMERIC(18,2),
    moneda              VARCHAR(10) DEFAULT 'PEN',
    fecha_convocatoria  DATE,
    fecha_buena_pro     DATE,
    fecha_suscripcion   DATE,
    ubigeo              VARCHAR(6) REFERENCES cat_distritos(ubigeo),
    url_seace           TEXT,
    fuente_raw          JSONB,       -- datos originales sin transformar
    ingested_at         TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------
-- Control de corridas ETL
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS etl_corridas (
    id              SERIAL PRIMARY KEY,
    inicio          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fin             TIMESTAMPTZ,
    estado          VARCHAR(20) DEFAULT 'running',  -- running | success | error
    registros_raw   INTEGER DEFAULT 0,
    registros_cargados INTEGER DEFAULT 0,
    registros_error INTEGER DEFAULT 0,
    parametros      JSONB,
    log_resumen     TEXT,
    error_detalle   TEXT
);

-- -------------------------------------------------------------
-- Índices para consulta intensiva
-- -------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_procesos_entidad      ON procesos(entidad_id);
CREATE INDEX IF NOT EXISTS idx_procesos_estado        ON procesos(estado_id);
CREATE INDEX IF NOT EXISTS idx_procesos_tipo          ON procesos(tipo_proceso_id);
CREATE INDEX IF NOT EXISTS idx_procesos_fecha_conv    ON procesos(fecha_convocatoria);
CREATE INDEX IF NOT EXISTS idx_procesos_valor         ON procesos(valor_referencial);
CREATE INDEX IF NOT EXISTS idx_procesos_ubigeo        ON procesos(ubigeo);
CREATE INDEX IF NOT EXISTS idx_procesos_objeto        ON procesos USING gin(to_tsvector('spanish', coalesce(objeto_contratacion,'')));
CREATE INDEX IF NOT EXISTS idx_entidades_nombre_norm  ON entidades(nombre_norm);
CREATE INDEX IF NOT EXISTS idx_etl_corridas_estado    ON etl_corridas(estado);
