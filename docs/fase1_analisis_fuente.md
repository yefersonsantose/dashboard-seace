# Fase 1 — Análisis de Fuente SEACE

## Resultado: Fuente seleccionada

**Portal de Contrataciones Abiertas (OSCE) — formato OCDS**

### ¿Por qué esta fuente?

| Criterio | OCDS / Contrataciones Abiertas | Scraping SEACE directo |
|---|---|---|
| Formato | JSON estructurado (OCDS estándar) | HTML + CAPTCHA manual |
| Autenticación | No requiere | No requiere |
| Estabilidad | Alta (API oficial) | Baja (depende de HTML del sitio) |
| Actualización | Diaria | Depende del scraper |
| Cobertura | 2004–presente (SEACE v1/v2/v3) | SEACE 3.0 actual |
| Esfuerzo | Bajo (descarga + parse) | Alto (Scrapy + Selenium) |

---

## URLs de descarga

| Tipo | URL |
|---|---|
| Año actual (2026) | `https://data.open-contracting.org/en/publication/135/download?name=2026.jsonl.gz` |
| Año anterior (2025) | `https://data.open-contracting.org/en/publication/135/download?name=2025.jsonl.gz` |
| Histórico completo | `https://data.open-contracting.org/en/publication/135/download?name=full.jsonl.gz` |
| CSV (2026) | `https://data.open-contracting.org/en/publication/135/download?name=2026.csv.tar.gz` |

Fuente original: `https://contratacionesabiertas.osce.gob.pe/descargas`

---

## Estructura OCDS de un registro (release)

```json
{
  "ocid": "ocds-p6t3ii-...",
  "date": "2025-03-15T10:00:00Z",
  "tag": ["tender"],
  "parties": [
    {
      "id": "PE-RUC-20123456789",
      "name": "MUNICIPALIDAD DISTRITAL DE...",
      "roles": ["buyer"],
      "address": { "region": "Lima", "locality": "..." }
    }
  ],
  "tender": {
    "id": "...",
    "title": "Adquisición de...",
    "description": "...",
    "procurementMethod": "open",
    "procurementMethodDetails": "Licitación Pública",
    "status": "active",
    "value": { "amount": 500000.0, "currency": "PEN" },
    "tenderPeriod": {
      "startDate": "2025-03-01",
      "endDate": "2025-04-01"
    },
    "items": [{ "description": "...", "classification": { "id": "...", "description": "..." } }]
  },
  "awards": [
    {
      "id": "...",
      "status": "active",
      "date": "2025-05-01",
      "value": { "amount": 480000.0, "currency": "PEN" },
      "suppliers": [{ "name": "PROVEEDOR SA", "id": "PE-RUC-..." }]
    }
  ]
}
```

---

## Mapeo OCDS → Modelo propio

| Campo OCDS | Campo PostgreSQL |
|---|---|
| `ocid` | `codigo_seace` |
| `tender.title` | `objeto_contratacion` |
| `tender.description` | `descripcion` |
| `tender.procurementMethodDetails` | `tipo_proceso` → `cat_tipos_proceso` |
| `tender.status` | `estado` → `cat_estados` |
| `tender.value.amount` | `valor_referencial` |
| `tender.value.currency` | `moneda` |
| `tender.tenderPeriod.startDate` | `fecha_convocatoria` |
| `awards[0].date` | `fecha_buena_pro` |
| `parties[role=buyer].name` | `entidad.nombre` |
| `parties[role=buyer].id` | `entidad.ruc` (parte numérica) |
| `parties[role=buyer].address.region` | → resolución de ubigeo |

---

## Estrategia de actualización

1. Descarga diaria del archivo JSONL del año en curso (comprimido ~50–200 MB).
2. Comparar `ocid` contra registros existentes → upsert.
3. Bitácora de corrida en `etl_corridas`.
4. El archivo histórico (`full.jsonl.gz`) solo se descarga en la carga inicial.

---

## Fuentes secundarias (descartadas por ahora)

- **SEACE 3.0 Buscador** (`prod2.seace.gob.pe`): JSF/Seam, requiere sesión y CAPTCHA.
- **SEACE prod6** (`prod6.seace.gob.pe`): Contratos ≤ 8 UIT, micro-frontend SPA sin API pública documentada.
- **GitHub Ed1123/seace-scraper**: Scrapy + Selenium, CAPTCHA manual. Útil como referencia de campos.
