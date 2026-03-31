"""
Módulo de extracción — Fuente: Portal OCDS de OSCE (Contrataciones Abiertas).

Estrategia (Fase 1):
  - Descarga archivos JSONL.GZ por año desde data.open-contracting.org
  - No requiere autenticación, no tiene CAPTCHA
  - Actualización diaria disponible
  - Cobertura: 2004–presente (SEACE v1/v2/v3)

URL base: https://data.open-contracting.org/en/publication/135/download
Parámetro: name=<YYYY>.jsonl.gz  o  name=full.jsonl.gz
"""
import gzip
import json
import logging
from datetime import datetime
from pathlib import Path

import requests
from config import settings

logger = logging.getLogger(__name__)

OCDS_BASE_URL = "https://data.open-contracting.org/en/publication/135/download"

HEADERS = {
    "User-Agent": "SEACE-Dashboard-ETL/1.0 (contacto@example.com)",
    "Accept": "application/octet-stream",
}


class OcdsExtractor:
    """Descarga y lee archivos OCDS (JSONL.GZ) del portal de Contrataciones Abiertas."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ── Descarga ──────────────────────────────────────────────

    def _download_url(self, name: str) -> str:
        return f"{OCDS_BASE_URL}?name={name}"

    def download_year(self, year: int, force: bool = False) -> Path:
        """Descarga el archivo JSONL.GZ de un año y lo guarda en raw/."""
        return self._download(f"{year}.jsonl.gz", force=force)

    def download_full(self, force: bool = False) -> Path:
        """Descarga el histórico completo (solo para carga inicial)."""
        logger.warning("Descargando histórico completo — puede tardar varios minutos.")
        return self._download("full.jsonl.gz", force=force)

    def _download(self, name: str, force: bool = False) -> Path:
        settings.ensure_dirs()
        destino = Path(settings.etl_raw_dir) / name

        if destino.exists() and not force:
            logger.info("Archivo en caché (use --force para re-descargar): %s", destino)
            return destino

        if destino.exists() and force:
            logger.info("Forzando re-descarga — eliminando caché: %s", destino)
            destino.unlink()

        url = self._download_url(name)
        logger.info("Descargando datos actualizados desde SEACE: %s → %s", url, destino)
        try:
            with self.session.get(url, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("Content-Length", 0))
                descargado = 0
                with open(destino, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 256):
                        f.write(chunk)
                        descargado += len(chunk)
                if total:
                    logger.info("Descarga completa: %.1f MB", descargado / 1024 / 1024)
        except requests.RequestException as exc:
            logger.error("Error al descargar %s: %s", name, exc)
            if destino.exists():
                destino.unlink()
            raise
        return destino

    # ── Lectura ───────────────────────────────────────────────

    def iter_releases(self, archivo: Path):
        """
        Itera sobre los releases OCDS en un archivo JSONL.GZ.
        Cada línea puede ser:
          - Un release individual (dict con 'ocid')
          - Un release package (dict con 'releases': [...])
        """
        logger.info("Leyendo releases de %s", archivo)
        with gzip.open(archivo, "rt", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    obj = json.loads(linea)
                except json.JSONDecodeError as exc:
                    logger.warning("Línea JSON inválida: %s", exc)
                    continue
                if "releases" in obj:
                    yield from obj["releases"]
                elif "ocid" in obj:
                    yield obj
                # release packages con 'records'
                elif "records" in obj:
                    for record in obj["records"]:
                        if "compiledRelease" in record:
                            yield record["compiledRelease"]
                        elif "releases" in record:
                            yield from record["releases"]

    def extract_batch(self, year: int | None = None, full: bool = False,
                      corrida_id: int = 0, force: bool = False):
        """
        Descarga y retorna todos los releases del año indicado (o histórico).
        force=True siempre re-descarga desde SEACE aunque exista caché local.
        Retorna un iterador para no cargar todo en memoria.
        """
        if full:
            archivo = self.download_full(force=force)
        else:
            archivo = self.download_year(year or datetime.utcnow().year, force=force)
        return self.iter_releases(archivo)

    def save_raw(self, releases: list[dict], corrida_id: int) -> Path:
        """Persiste una muestra de releases crudos para trazabilidad."""
        settings.ensure_dirs()
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archivo = Path(settings.etl_raw_dir) / f"sample_{corrida_id}_{ts}.json"
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(releases[:100], f, ensure_ascii=False, indent=2, default=str)
        logger.info("Muestra raw guardada: %s", archivo)
        return archivo
