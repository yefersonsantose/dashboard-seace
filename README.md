# Dashboard SEACE

Dashboard de oportunidades y seguimiento de procesos de contratación pública del SEACE (Peru).

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Backend | FastAPI + SQLAlchemy |
| Base de datos | PostgreSQL 15 |
| ETL | Python 3.11 |
| Infra | Docker Compose |

## Estructura

```
├── frontend/     # Next.js dashboard
├── backend/      # FastAPI REST API
├── etl/          # Pipeline de extracción y carga
├── db/           # Scripts SQL de inicialización
└── docker-compose.yml
```

## Inicio rápido

### 1. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus valores
```

### 2. Levantar con Docker Compose
```bash
docker compose up -d db backend frontend
```

### 3. Ejecutar ETL inicial
```bash
docker compose run --rm etl python run.py
```

### 4. Acceder
- Dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs

## Desarrollo local

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### ETL
```bash
cd etl
pip install -r requirements.txt
python run.py
```

## Fases de implementación

- [x] Fase 0 — Scaffolding y configuración base
- [ ] Fase 1 — Análisis de fuente SEACE
- [ ] Fase 2 — Modelo de datos
- [ ] Fase 3 — ETL MVP
- [ ] Fase 4 — Backend API
- [ ] Fase 5 — Frontend dashboard
- [ ] Fase 6 — Mapa y georreferenciación
- [ ] Fase 7 — Calidad y despliegue
