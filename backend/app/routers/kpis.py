from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Proceso, Entidad, CatEstado
from app.schemas import KPIs

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("", response_model=KPIs)
def get_kpis(db: Session = Depends(get_db)):
    total_procesos = db.query(func.count(Proceso.id)).scalar() or 0
    monto_total = db.query(func.sum(Proceso.valor_referencial)).scalar()
    hace_7d = datetime.utcnow() - timedelta(days=7)
    procesos_nuevos_7d = db.query(func.count(Proceso.id)).filter(Proceso.ingested_at >= hace_7d).scalar() or 0
    entidades_activas = db.query(func.count(Entidad.id)).filter(Entidad.activa == True).scalar() or 0
    ultima_actualizacion = db.query(func.max(Proceso.ingested_at)).scalar()

    return KPIs(
        total_procesos=total_procesos,
        monto_total=monto_total,
        procesos_nuevos_7d=procesos_nuevos_7d,
        entidades_activas=entidades_activas,
        ultima_actualizacion=ultima_actualizacion,
    )
