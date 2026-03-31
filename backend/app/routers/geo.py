from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Proceso
from app.schemas import GeoResumen

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/regiones", response_model=list[GeoResumen])
def resumen_por_region(db: Session = Depends(get_db)):
    """Agregación por departamento usando columna directa (compatible SQLite y PostgreSQL)."""
    rows = (
        db.query(
            Proceso.entidad_departamento.label("nombre"),
            func.count(Proceso.id).label("total_procesos"),
            func.sum(Proceso.valor_referencial).label("monto_total"),
        )
        .filter(Proceso.entidad_departamento.isnot(None))
        .group_by(Proceso.entidad_departamento)
        .order_by(func.count(Proceso.id).desc())
        .all()
    )
    return [
        GeoResumen(ubigeo=r.nombre or "", nombre=r.nombre or "",
                   total_procesos=r.total_procesos, monto_total=r.monto_total)
        for r in rows
    ]
