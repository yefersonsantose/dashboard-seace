"""
Punto de entrada del ETL.
Orquesta: descarga OCDS → transformación → carga PostgreSQL → bitácora.

Uso:
  python run.py                  # año actual
  python run.py --year 2025      # año específico
  python run.py --full           # histórico completo (solo primera vez)
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import settings

IS_SQLITE = settings.database_url.startswith("sqlite")
from extract import OcdsExtractor
from transform import transformar_lote
from load import cargar_lote

# ─── Logging ──────────────────────────────────────────────────
settings.ensure_dirs()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path(settings.etl_log_dir) / f"etl_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("etl.run")


def _ensure_corridas_table(session):
    """Crea la tabla etl_corridas si no existe (SQLite dev mode)."""
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS etl_corridas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inicio TEXT,
            fin TEXT,
            estado TEXT,
            parametros TEXT,
            registros_cargados INTEGER DEFAULT 0,
            registros_nuevos INTEGER DEFAULT 0,
            registros_error INTEGER DEFAULT 0,
            log_resumen TEXT,
            error_detalle TEXT
        )
    """))
    # Añadir columna si ya existía la tabla sin ella
    try:
        session.execute(text("ALTER TABLE etl_corridas ADD COLUMN registros_nuevos INTEGER DEFAULT 0"))
    except Exception:
        pass
    session.commit()


def _contar_procesos(session) -> int:
    """Cuenta el total actual de procesos en la base de datos."""
    row = session.execute(text("SELECT COUNT(*) FROM procesos")).fetchone()
    return row[0] if row else 0


def registrar_corrida_inicio(session, parametros: dict) -> int:
    _ensure_corridas_table(session)
    if IS_SQLITE:
        session.execute(
            text("INSERT INTO etl_corridas (inicio, estado, parametros) VALUES (datetime('now'), 'running', :p)"),
            {"p": json.dumps(parametros)},
        )
        session.commit()
        row = session.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]
    else:
        result = session.execute(
            text("INSERT INTO etl_corridas (inicio, estado, parametros) VALUES (NOW(), 'running', :p::jsonb) RETURNING id"),
            {"p": json.dumps(parametros)},
        )
        session.commit()
        return result.fetchone()[0]


def actualizar_corrida(session, corrida_id: int, estado: str, cargados: int,
                       errores: int, log: str, error_det: str = None, nuevos: int = 0):
    ts = "datetime('now')" if IS_SQLITE else "NOW()"
    session.execute(
        text(f"""
            UPDATE etl_corridas
            SET fin = {ts}, estado = :estado,
                registros_cargados = :cargados,
                registros_nuevos = :nuevos,
                registros_error = :errores,
                log_resumen = :log,
                error_detalle = :error_det
            WHERE id = :id
        """),
        {"estado": estado, "cargados": cargados, "nuevos": nuevos,
         "errores": errores, "log": log, "error_det": error_det, "id": corrida_id},
    )
    session.commit()


def parse_args():
    parser = argparse.ArgumentParser(description="ETL SEACE — fuente OCDS")
    parser.add_argument("--year", type=int, default=datetime.utcnow().year,
                        help="Año a procesar (default: año actual)")
    parser.add_argument("--full", action="store_true",
                        help="Descargar histórico completo (solo carga inicial)")
    parser.add_argument("--force", action="store_true",
                        help="Forzar re-descarga desde SEACE aunque exista caché local")
    parser.add_argument("--batch-size", type=int, default=settings.etl_batch_size,
                        help=f"Registros por lote de carga (default: {settings.etl_batch_size})")
    return parser.parse_args()


def main():
    args = parse_args()
    parametros = {"year": args.year, "full": args.full, "force": args.force,
                  "batch_size": args.batch_size}

    _args = {"check_same_thread": False} if IS_SQLITE else {}
    engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=_args)
    Session = sessionmaker(bind=engine)
    session = Session()

    corrida_id = registrar_corrida_inicio(session, parametros)
    logger.info("=== ETL iniciado | corrida_id=%s | params=%s ===", corrida_id, parametros)

    # Contar procesos ANTES para saber cuántos son nuevos al final
    total_antes = _contar_procesos(session)
    logger.info("Procesos en BD antes del ETL: %d", total_antes)

    total_cargados = total_errores = 0
    try:
        extractor = OcdsExtractor()
        releases_iter = extractor.extract_batch(
            year=args.year,
            full=args.full,
            corrida_id=corrida_id,
            force=args.force,
        )

        # Procesar en lotes para no saturar memoria
        lote = []
        for release in releases_iter:
            lote.append(release)
            if len(lote) >= args.batch_size:
                validos, errores = transformar_lote(lote)
                if validos:
                    cargados, _ = cargar_lote(validos, corrida_id)
                    total_cargados += cargados
                total_errores += len(errores)
                logger.info("Progreso: %d cargados, %d errores acumulados", total_cargados, total_errores)
                lote = []

        # Último lote parcial
        if lote:
            validos, errores = transformar_lote(lote)
            extractor.save_raw(validos[:100], corrida_id)
            if validos:
                cargados, _ = cargar_lote(validos, corrida_id)
                total_cargados += cargados
            total_errores += len(errores)

        # Calcular nuevas convocatorias reales
        total_despues = _contar_procesos(session)
        registros_nuevos = max(0, total_despues - total_antes)
        logger.info("Procesos en BD después del ETL: %d | Nuevos: %d", total_despues, registros_nuevos)

        actualizar_corrida(
            session, corrida_id, "success", total_cargados, total_errores,
            f"Año: {args.year} | Procesados: {total_cargados} | Nuevos: {registros_nuevos} | Errores: {total_errores}",
            nuevos=registros_nuevos,
        )
        logger.info("=== ETL finalizado | cargados=%d nuevos=%d errores=%d ===",
                    total_cargados, registros_nuevos, total_errores)

    except Exception as exc:
        logger.exception("ETL falló con error crítico")
        actualizar_corrida(
            session, corrida_id, "error", total_cargados, total_errores,
            "ETL abortado por error crítico", str(exc),
        )
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
