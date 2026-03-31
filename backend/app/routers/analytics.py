from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String, text

from app.database import get_db, IS_SQLITE
from app.models import Proceso, Entidad, CatEstado, CatTipoProceso
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

router = APIRouter(prefix="/analytics", tags=["analytics"])


class ItemConteo(BaseModel):
    nombre: str
    total_procesos: int
    monto_total: Optional[Decimal]


class ItemMes(BaseModel):
    periodo: str
    total_procesos: int
    monto_total: Optional[Decimal]


@router.get("/por-estado", response_model=list[ItemConteo])
def por_estado(db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.coalesce(CatEstado.nombre, Proceso.estado_id.cast(String), "Sin estado").label("nombre"),
            func.count(Proceso.id).label("total_procesos"),
            func.sum(Proceso.valor_referencial).label("monto_total"),
        )
        .outerjoin(CatEstado, Proceso.estado_id == CatEstado.id)
        .group_by(func.coalesce(CatEstado.nombre, Proceso.estado_id.cast(String), "Sin estado"))
        .order_by(func.count(Proceso.id).desc())
        .limit(10)
        .all()
    )
    return [ItemConteo(**r._asdict()) for r in rows]


@router.get("/por-tipo", response_model=list[ItemConteo])
def por_tipo(db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.coalesce(CatTipoProceso.nombre, "Sin tipo").label("nombre"),
            func.count(Proceso.id).label("total_procesos"),
            func.sum(Proceso.valor_referencial).label("monto_total"),
        )
        .outerjoin(CatTipoProceso, Proceso.tipo_proceso_id == CatTipoProceso.id)
        .group_by(func.coalesce(CatTipoProceso.nombre, "Sin tipo"))
        .order_by(func.count(Proceso.id).desc())
        .limit(10)
        .all()
    )
    return [ItemConteo(**r._asdict()) for r in rows]


@router.get("/por-mes", response_model=list[ItemMes])
def por_mes(db: Session = Depends(get_db)):
    """Tendencia mensual de los últimos 12 meses (compatible SQLite y PostgreSQL)."""
    if IS_SQLITE:
        periodo_expr = func.strftime("%Y-%m", Proceso.fecha_convocatoria)
    else:
        periodo_expr = func.to_char(Proceso.fecha_convocatoria, "YYYY-MM")

    rows = (
        db.query(
            periodo_expr.label("periodo"),
            func.count(Proceso.id).label("total_procesos"),
            func.sum(Proceso.valor_referencial).label("monto_total"),
        )
        .filter(Proceso.fecha_convocatoria.isnot(None))
        .group_by(periodo_expr)
        .order_by(periodo_expr.desc())
        .limit(12)
        .all()
    )
    return [ItemMes(**r._asdict()) for r in reversed(rows)]


@router.get("/por-nivel", response_model=list[ItemConteo])
def por_nivel(db: Session = Depends(get_db)):
    """Distribución por nivel de gobierno (Nacional, Regional, Municipal)."""
    rows = (
        db.query(
            func.coalesce(Proceso.nivel_gobierno, "Sin clasificar").label("nombre"),
            func.count(Proceso.id).label("total_procesos"),
            func.sum(Proceso.valor_referencial).label("monto_total"),
        )
        .group_by(func.coalesce(Proceso.nivel_gobierno, "Sin clasificar"))
        .order_by(func.count(Proceso.id).desc())
        .all()
    )
    return [ItemConteo(**r._asdict()) for r in rows]


@router.get("/top-entidades", response_model=list[ItemConteo])
def top_entidades(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Entidad.nombre.label("nombre"),
            func.count(Proceso.id).label("total_procesos"),
            func.sum(Proceso.valor_referencial).label("monto_total"),
        )
        .join(Entidad, Proceso.entidad_id == Entidad.id)
        .group_by(Entidad.nombre)
        .order_by(func.sum(Proceso.valor_referencial).desc())
        .limit(10)
        .all()
    )
    return [ItemConteo(**r._asdict()) for r in rows]
