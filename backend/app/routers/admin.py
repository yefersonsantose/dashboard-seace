"""
Endpoints administrativos: ejecutar ETL, consultar estado de la última corrida.
"""
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

# Ruta absoluta al directorio del ETL (un nivel arriba de backend/)
ETL_DIR = Path(__file__).resolve().parents[3] / "etl"


@router.post("/etl/ejecutar")
def ejecutar_etl(db: Session = Depends(get_db)):
    """
    Lanza el ETL en segundo plano (año actual).
    Devuelve inmediatamente con status 'iniciado'.
    """
    if not ETL_DIR.exists():
        return {"status": "error", "detalle": f"Directorio ETL no encontrado: {ETL_DIR}"}

    import datetime
    year = str(datetime.datetime.utcnow().year)
    subprocess.Popen(
        # --force: siempre re-descarga desde SEACE para obtener convocatorias nuevas
        [sys.executable, "run.py", "--year", year, "--force"],
        cwd=str(ETL_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        # En Windows: no mostrar ventana de consola
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return {"status": "iniciado", "mensaje": "Descargando datos actualizados desde SEACE. Puede tardar varios minutos."}


@router.get("/etl/estado")
def estado_etl(db: Session = Depends(get_db)):
    """Retorna el estado de las últimas 5 corridas del ETL."""
    try:
        rows = db.execute(text("""
            SELECT id, inicio, fin, estado, registros_cargados,
                   COALESCE(registros_nuevos, 0), registros_error, log_resumen
            FROM etl_corridas
            ORDER BY id DESC
            LIMIT 5
        """)).fetchall()
        return {
            "corridas": [
                {
                    "id": r[0],
                    "inicio": r[1],
                    "fin": r[2],
                    "estado": r[3],
                    "registros_cargados": r[4],
                    "registros_nuevos": r[5],
                    "registros_error": r[6],
                    "log_resumen": r[7],
                }
                for r in rows
            ]
        }
    except Exception:
        return {"corridas": []}
