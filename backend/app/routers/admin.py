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

    subprocess.Popen(
        [sys.executable, "run.py", "--year", str(__import__("datetime").datetime.utcnow().year)],
        cwd=str(ETL_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        # En Windows: no mostrar ventana de consola
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return {"status": "iniciado", "mensaje": "El ETL se está ejecutando en segundo plano."}


@router.get("/etl/estado")
def estado_etl(db: Session = Depends(get_db)):
    """Retorna el estado de las últimas 5 corridas del ETL."""
    try:
        rows = db.execute(text("""
            SELECT id, inicio, fin, estado, registros_cargados, registros_error, log_resumen
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
                    "registros_error": r[5],
                    "log_resumen": r[6],
                }
                for r in rows
            ]
        }
    except Exception:
        return {"corridas": []}
