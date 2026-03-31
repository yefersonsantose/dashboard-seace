from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ProcesoListItem(BaseModel):
    id: int
    codigo_seace: str
    entidad: str
    objeto_contratacion: Optional[str]
    tipo_proceso: Optional[str]
    estado: Optional[str]
    valor_referencial: Optional[Decimal]
    moneda: Optional[str]
    fecha_convocatoria: Optional[date]
    nivel_gobierno: Optional[str]
    departamento: Optional[str]
    provincia: Optional[str]
    url_seace: Optional[str]

    model_config = {"from_attributes": True}


class ProcesoDetalle(ProcesoListItem):
    nro_expediente: Optional[str]
    descripcion: Optional[str]
    fecha_buena_pro: Optional[date]
    fecha_suscripcion: Optional[date]
    distrito: Optional[str]
    ubigeo: Optional[str]
    ingested_at: Optional[datetime]

    model_config = {"from_attributes": True}


class KPIs(BaseModel):
    total_procesos: int
    monto_total: Optional[Decimal]
    procesos_nuevos_7d: int
    entidades_activas: int
    ultima_actualizacion: Optional[datetime]


class GeoResumen(BaseModel):
    ubigeo: str
    nombre: str
    total_procesos: int
    monto_total: Optional[Decimal]


class Paginacion(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    paginas: int


class ProcesosPaginados(BaseModel):
    data: list[ProcesoListItem]
    paginacion: Paginacion
