import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app import models  # noqa: F401 — registra todos los modelos
from app.routers import procesos, kpis, geo, catalogos, analytics, admin

# Crea tablas si no existen (SQLite dev y PostgreSQL prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Dashboard SEACE — API",
    description="API de consulta de procesos de contratación pública del SEACE",
    version="0.1.0",
)

# CORS: permitir frontend local + dominio de producción (Vercel u otro)
_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        _frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(procesos.router)
app.include_router(kpis.router)
app.include_router(geo.router)
app.include_router(catalogos.router)
app.include_router(analytics.router)
app.include_router(admin.router)


@app.get("/health", tags=["salud"])
def health():
    return {"status": "ok"}
