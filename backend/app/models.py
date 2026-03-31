from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, Boolean,
    ForeignKey, Text, func
)
from sqlalchemy import JSON as JSONB  # JSON works on SQLite dev + PostgreSQL prod
from sqlalchemy.orm import relationship
from app.database import Base


class CatRegion(Base):
    __tablename__ = "cat_regiones"
    id = Column(Integer, primary_key=True)
    codigo = Column(String(2), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)


class CatProvincia(Base):
    __tablename__ = "cat_provincias"
    id = Column(Integer, primary_key=True)
    codigo = Column(String(4), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    region_id = Column(Integer, ForeignKey("cat_regiones.id"))
    region = relationship("CatRegion")


class CatDistrito(Base):
    __tablename__ = "cat_distritos"
    id = Column(Integer, primary_key=True)
    ubigeo = Column(String(6), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    provincia_id = Column(Integer, ForeignKey("cat_provincias.id"))
    provincia = relationship("CatProvincia")


class CatTipoProceso(Base):
    __tablename__ = "cat_tipos_proceso"
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)


class CatEstado(Base):
    __tablename__ = "cat_estados"
    id = Column(Integer, primary_key=True)
    codigo = Column(String(30), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)


class Entidad(Base):
    __tablename__ = "entidades"
    id = Column(Integer, primary_key=True)
    ruc = Column(String(11), unique=True)
    nombre = Column(String(500), nullable=False)
    nombre_norm = Column(String(500))
    tipo_entidad = Column(String(20), default="GOB_NACIONAL")  # GOB_NACIONAL|GOB_REGIONAL|MUN_PROVINCIAL|MUN_DISTRITAL
    ubigeo = Column(String(6), ForeignKey("cat_distritos.ubigeo"))
    sector = Column(String(200))
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    distrito = relationship("CatDistrito")
    procesos = relationship("Proceso", back_populates="entidad")


class Proceso(Base):
    __tablename__ = "procesos"
    id = Column(Integer, primary_key=True)
    nro_expediente = Column(String(50))
    codigo_seace = Column(String(100), unique=True, nullable=False)
    entidad_id = Column(Integer, ForeignKey("entidades.id"), nullable=False)
    tipo_proceso_id = Column(Integer, ForeignKey("cat_tipos_proceso.id"))
    estado_id = Column(Integer, ForeignKey("cat_estados.id"))
    objeto_contratacion = Column(String(2000))
    descripcion = Column(Text)
    valor_referencial = Column(Numeric(18, 2))
    moneda = Column(String(10), default="PEN")
    fecha_convocatoria = Column(Date)
    fecha_buena_pro = Column(Date)
    fecha_suscripcion = Column(Date)
    ubigeo = Column(String(6), ForeignKey("cat_distritos.ubigeo"))
    url_seace = Column(Text)
    fuente_raw = Column(JSONB)
    nivel_gobierno = Column(String(30))        # Gobierno Nacional|Regional|Municipal Provincial|Distrital
    entidad_departamento = Column(String(100))
    entidad_provincia = Column(String(100))
    entidad_distrito = Column(String(100))
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    entidad = relationship("Entidad", back_populates="procesos")
    tipo_proceso = relationship("CatTipoProceso")
    estado = relationship("CatEstado")
    distrito = relationship("CatDistrito")
