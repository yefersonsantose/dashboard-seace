"""
Módulo de carga con upsert compatible con SQLite (dev) y PostgreSQL (prod).
"""
import json
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

logger = logging.getLogger(__name__)

IS_SQLITE = settings.database_url.startswith("sqlite")


def get_engine():
    args = {"check_same_thread": False} if IS_SQLITE else {}
    return create_engine(settings.database_url, pool_pre_ping=True, connect_args=args)


def upsert_catalogo(session, tabla: str, codigo: str, nombre: str | None = None) -> int | None:
    """Inserta o recupera un registro de catálogo (estado, tipo_proceso); retorna id."""
    if not codigo:
        return None
    row = session.execute(
        text(f"SELECT id FROM {tabla} WHERE codigo = :c LIMIT 1"), {"c": codigo}
    ).fetchone()
    if row:
        return row[0]
    # Usar nombre explícito para evitar mojibake con .title() en Windows
    nombre_final = nombre or codigo
    session.execute(
        text(f"INSERT OR IGNORE INTO {tabla} (codigo, nombre) VALUES (:c, :n)"),
        {"c": codigo, "n": nombre_final},
    )
    row = session.execute(
        text(f"SELECT id FROM {tabla} WHERE codigo = :c LIMIT 1"), {"c": codigo}
    ).fetchone()
    return row[0] if row else None


def upsert_entidad(
    session,
    nombre: str,
    ruc: str | None,
    tipo_entidad: str | None = None,
    departamento: str | None = None,
    provincia: str | None = None,
    distrito: str | None = None,
) -> int:
    """Inserta o actualiza una entidad; retorna su id."""
    nombre_norm = nombre.lower().strip() if nombre else ""
    row = session.execute(
        text("SELECT id FROM entidades WHERE nombre_norm = :n LIMIT 1"),
        {"n": nombre_norm},
    ).fetchone()

    if row:
        # Actualizar campos de clasificación geográfica en cada run
        session.execute(
            text("""UPDATE entidades SET
                tipo_entidad = COALESCE(:tipo, tipo_entidad),
                ruc = COALESCE(ruc, :ruc)
                WHERE id = :id"""),
            {"tipo": tipo_entidad, "ruc": ruc, "id": row[0]},
        )
        return row[0]

    if IS_SQLITE:
        session.execute(
            text("""INSERT OR IGNORE INTO entidades
                (ruc, nombre, nombre_norm, tipo_entidad, activa)
                VALUES (:ruc, :nombre, :nombre_norm, :tipo, 1)"""),
            {"ruc": ruc, "nombre": nombre, "nombre_norm": nombre_norm,
             "tipo": tipo_entidad or "GOB_NACIONAL"},
        )
        row = session.execute(
            text("SELECT id FROM entidades WHERE nombre_norm = :n LIMIT 1"),
            {"n": nombre_norm},
        ).fetchone()
        return row[0]
    else:
        result = session.execute(
            text(
                "INSERT INTO entidades (ruc, nombre, nombre_norm, tipo_entidad) "
                "VALUES (:ruc, :nombre, :nombre_norm, :tipo) "
                "ON CONFLICT (ruc) DO UPDATE SET nombre = EXCLUDED.nombre, "
                "tipo_entidad = EXCLUDED.tipo_entidad RETURNING id"
            ),
            {"ruc": ruc, "nombre": nombre, "nombre_norm": nombre_norm,
             "tipo": tipo_entidad or "GOB_NACIONAL"},
        )
        session.flush()
        return result.fetchone()[0]


def cargar_lote(registros: list[dict], corrida_id: int) -> tuple[int, int]:
    """
    Carga un lote de registros transformados usando upsert.
    Retorna (cargados, omitidos).
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    cargados = omitidos = 0

    try:
        for reg in registros:
            entidad_id = upsert_entidad(
                session,
                reg.get("entidad_nombre") or "",
                reg.get("entidad_ruc"),
                tipo_entidad=reg.get("tipo_entidad"),
                departamento=reg.get("entidad_departamento"),
                provincia=reg.get("entidad_provincia"),
                distrito=reg.get("entidad_distrito"),
            )
            estado_id = upsert_catalogo(session, "cat_estados", reg.get("estado"))
            tipo_id = upsert_catalogo(session, "cat_tipos_proceso", reg.get("tipo_proceso"))
            raw_json = json.dumps(reg.get("fuente_raw") or {}, default=str)

            if IS_SQLITE:
                session.execute(
                    text("""
                        INSERT INTO procesos (
                            codigo_seace, nro_expediente, entidad_id,
                            estado_id, tipo_proceso_id,
                            objeto_contratacion, valor_referencial, moneda,
                            fecha_convocatoria, fecha_buena_pro,
                            ubigeo, url_seace, fuente_raw,
                            nivel_gobierno, entidad_departamento,
                            entidad_provincia, entidad_distrito
                        ) VALUES (
                            :codigo_seace, :nro_expediente, :entidad_id,
                            :estado_id, :tipo_id,
                            :objeto, :valor, :moneda,
                            :fecha_conv, :fecha_bp,
                            :ubigeo, :url, :raw,
                            :nivel, :departamento, :provincia, :distrito
                        )
                        ON CONFLICT (codigo_seace) DO UPDATE SET
                            objeto_contratacion = excluded.objeto_contratacion,
                            valor_referencial = excluded.valor_referencial,
                            fecha_buena_pro = excluded.fecha_buena_pro,
                            estado_id = excluded.estado_id,
                            tipo_proceso_id = excluded.tipo_proceso_id,
                            fecha_convocatoria = excluded.fecha_convocatoria,
                            nivel_gobierno = excluded.nivel_gobierno,
                            entidad_departamento = excluded.entidad_departamento,
                            entidad_provincia = excluded.entidad_provincia,
                            entidad_distrito = excluded.entidad_distrito,
                            fuente_raw = excluded.fuente_raw
                    """),
                    {
                        "codigo_seace": reg["codigo_seace"],
                        "nro_expediente": reg.get("nro_expediente"),
                        "entidad_id": entidad_id,
                        "estado_id": estado_id,
                        "tipo_id": tipo_id,
                        "objeto": reg.get("objeto_contratacion"),
                        "valor": float(reg["valor_referencial"]) if reg.get("valor_referencial") else None,
                        "moneda": reg.get("moneda", "PEN"),
                        "fecha_conv": str(reg["fecha_convocatoria"]) if reg.get("fecha_convocatoria") else None,
                        "fecha_bp": str(reg["fecha_buena_pro"]) if reg.get("fecha_buena_pro") else None,
                        "ubigeo": reg.get("ubigeo"),
                        "url": reg.get("url_seace"),
                        "raw": raw_json,
                        "nivel": reg.get("nivel_gobierno"),
                        "departamento": reg.get("entidad_departamento"),
                        "provincia": reg.get("entidad_provincia"),
                        "distrito": reg.get("entidad_distrito"),
                    },
                )
            else:
                session.execute(
                    text("""
                        INSERT INTO procesos (
                            codigo_seace, nro_expediente, entidad_id,
                            objeto_contratacion, valor_referencial, moneda,
                            fecha_convocatoria, fecha_buena_pro,
                            ubigeo, url_seace, fuente_raw
                        ) VALUES (
                            :codigo_seace, :nro_expediente, :entidad_id,
                            :objeto, :valor, :moneda,
                            :fecha_conv, :fecha_bp,
                            :ubigeo, :url, :raw::jsonb
                        )
                        ON CONFLICT (codigo_seace) DO UPDATE SET
                            objeto_contratacion = EXCLUDED.objeto_contratacion,
                            valor_referencial = EXCLUDED.valor_referencial,
                            fecha_buena_pro = EXCLUDED.fecha_buena_pro,
                            updated_at = NOW()
                    """),
                    {
                        "codigo_seace": reg["codigo_seace"],
                        "nro_expediente": reg.get("nro_expediente"),
                        "entidad_id": entidad_id,
                        "objeto": reg.get("objeto_contratacion"),
                        "valor": reg.get("valor_referencial"),
                        "moneda": reg.get("moneda", "PEN"),
                        "fecha_conv": reg.get("fecha_convocatoria"),
                        "fecha_bp": reg.get("fecha_buena_pro"),
                        "ubigeo": reg.get("ubigeo"),
                        "url": reg.get("url_seace"),
                        "raw": raw_json,
                    },
                )
            cargados += 1

        session.commit()
        logger.info("Lote cargado: %d registros", cargados)
    except Exception as exc:
        session.rollback()
        logger.error("Error en carga: %s", exc)
        raise
    finally:
        session.close()

    return cargados, omitidos
