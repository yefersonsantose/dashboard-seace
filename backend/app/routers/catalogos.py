from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CatEstado, CatTipoProceso, CatRegion

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@router.get("/estados")
def get_estados(db: Session = Depends(get_db)):
    return [{"codigo": e.codigo, "nombre": e.nombre} for e in db.query(CatEstado).order_by(CatEstado.nombre)]


@router.get("/tipos-proceso")
def get_tipos_proceso(db: Session = Depends(get_db)):
    return [{"codigo": t.codigo, "nombre": t.nombre} for t in db.query(CatTipoProceso).order_by(CatTipoProceso.nombre)]


@router.get("/regiones")
def get_regiones(db: Session = Depends(get_db)):
    return [{"codigo": r.codigo, "nombre": r.nombre} for r in db.query(CatRegion).order_by(CatRegion.nombre)]


@router.get("/niveles-gobierno")
def get_niveles_gobierno():
    """Catálogo estático de niveles de gobierno para filtros."""
    return [
        {"codigo": "Gobierno Nacional",   "nombre": "Gobierno Nacional"},
        {"codigo": "Gobierno Regional",   "nombre": "Gobierno Regional"},
        {"codigo": "Municipal Provincial","nombre": "Municipal Provincial"},
        {"codigo": "Municipal Distrital", "nombre": "Municipal Distrital"},
    ]
