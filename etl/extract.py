"""
Módulo de extracción — Fuente primaria: Portal Contrataciones Abiertas (oece.gob.pe)
                       Fuente secundaria: data.open-contracting.org (respaldo histórico)

Fuente primaria (mensual, más actualizada):
  URL: https://contratacionesabiertas.oece.gob.pe/api/v1/file/seace_v3/json/{year}/{month}
  Formato: ZIP que contiene un JSON con array de contratos OCDS
  Actualización: mensual, con el mes en curso disponible desde el primer día

Fuente secundaria (anual, histórico):
  URL: https://data.open-contracting.org/en/publication/135/download?name={year}.jsonl.gz
  Formato: JSONL.GZ (una línea = un release o release package)
  Actualización: mensual con ~3 semanas de retraso
"""
import gzip
import io
import json
import logging
import zipfile
from datetime import datetime
from pathlib import Path

import requests
from config import settings

logger = logging.getLogger(__name__)

# Fuente primaria: portal oficial OECE (mensual, más fresca)
OECE_BASE_URL = "https://contratacionesabiertas.oece.gob.pe/api/v1/file/seace_v3/json"

# Fuente secundaria: OCP Data Registry (anual, respaldo histórico)
OCDS_BASE_URL = "https://data.open-contracting.org/en/publication/135/download"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://contratacionesabiertas.oece.gob.pe/descargas",
}


class OcdsExtractor:
    """
    Descarga y lee archivos OCDS del portal oficial de Contrataciones Abiertas del Perú.

    Estrategia de actualización (--force):
      - Descarga los archivos ZIP mensuales del año actual desde oece.gob.pe
      - Cada mes es un ZIP que contiene un JSON con releases OCDS
      - Si un mes ya está en caché y no es el mes actual, no se re-descarga
      - El mes actual siempre se re-descarga (puede tener datos nuevos)
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ── Descarga fuente primaria (OECE mensual) ──────────────────

    def _oece_url(self, year: int, month: int) -> str:
        return f"{OECE_BASE_URL}/{year}/{month:02d}"

    def _download_month(self, year: int, month: int, force: bool = False) -> Path:
        """Descarga el ZIP mensual de oece.gob.pe y lo guarda en raw/."""
        settings.ensure_dirs()
        name = f"oece_{year}_{month:02d}.zip"
        destino = Path(settings.etl_raw_dir) / name

        ahora = datetime.utcnow()
        es_mes_actual = (year == ahora.year and month == ahora.month)

        # Re-descargar si: --force, es el mes actual, o no existe en caché
        if destino.exists() and not force and not es_mes_actual:
            logger.info("Mes %d/%02d en caché: %s", year, month, destino)
            return destino

        if destino.exists():
            logger.info("Re-descargando mes %d/%02d desde oece.gob.pe...", year, month)
            destino.unlink()

        url = self._oece_url(year, month)
        logger.info("Descargando %d/%02d desde %s", year, month, url)
        try:
            with self.session.get(url, stream=True, timeout=180) as resp:
                resp.raise_for_status()
                descargado = 0
                with open(destino, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 256):
                        f.write(chunk)
                        descargado += len(chunk)
                logger.info("Descarga completa: %.1f MB", descargado / 1024 / 1024)
        except requests.RequestException as exc:
            logger.error("Error al descargar %d/%02d: %s", year, month, exc)
            if destino.exists():
                destino.unlink()
            raise
        return destino

    def iter_releases_from_zip(self, archivo: Path):
        """
        Lee releases OCDS desde un ZIP que contiene un archivo JSON.
        El JSON puede ser:
          - Array de releases: [{ocid:...}, ...]
          - Release package: {releases: [...]}
          - Array de contratos: [{releases: [...], ...}, ...]
        """
        logger.info("Leyendo releases de ZIP: %s", archivo)
        try:
            with zipfile.ZipFile(archivo, "r") as zf:
                json_files = [n for n in zf.namelist() if n.endswith(".json")]
                if not json_files:
                    logger.warning("ZIP sin archivos JSON: %s", archivo)
                    return
                for json_name in json_files:
                    logger.info("  Procesando: %s", json_name)
                    with zf.open(json_name) as jf:
                        data = json.load(jf)
                    yield from self._iter_from_json(data)
        except (zipfile.BadZipFile, json.JSONDecodeError) as exc:
            logger.error("Error leyendo ZIP %s: %s", archivo, exc)

    def _iter_from_json(self, data):
        """Itera releases desde cualquier estructura JSON OCDS."""
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if "ocid" in item:
                        yield item
                    elif "releases" in item:
                        yield from item["releases"]
                    elif "compiledRelease" in item:
                        yield item["compiledRelease"]
        elif isinstance(data, dict):
            if "releases" in data:
                yield from data["releases"]
            elif "records" in data:
                for record in data["records"]:
                    if "compiledRelease" in record:
                        yield record["compiledRelease"]
                    elif "releases" in record:
                        yield from record["releases"]
            elif "ocid" in data:
                yield data

    # ── Descarga fuente secundaria (OCDS anual, respaldo) ────────

    def _download_year_legacy(self, year: int, force: bool = False) -> Path:
        """Descarga el JSONL.GZ anual de data.open-contracting.org (respaldo)."""
        settings.ensure_dirs()
        destino = Path(settings.etl_raw_dir) / f"{year}.jsonl.gz"

        if destino.exists() and not force:
            logger.info("Archivo anual en caché: %s", destino)
            return destino
        if destino.exists():
            destino.unlink()

        url = f"{OCDS_BASE_URL}?name={year}.jsonl.gz"
        logger.info("Descargando histórico anual %d desde OCP: %s", year, url)
        try:
            with self.session.get(url, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                descargado = 0
                with open(destino, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 256):
                        f.write(chunk)
                        descargado += len(chunk)
                logger.info("Descarga completa: %.1f MB", descargado / 1024 / 1024)
        except requests.RequestException as exc:
            logger.error("Error al descargar %d anual: %s", year, exc)
            if destino.exists():
                destino.unlink()
            raise
        return destino

    def iter_releases_from_jsonlgz(self, archivo: Path):
        """Itera releases desde JSONL.GZ (formato legacy OCP)."""
        logger.info("Leyendo JSONL.GZ: %s", archivo)
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
                yield from self._iter_from_json(obj)

    # ── Punto de entrada principal ───────────────────────────────

    def extract_batch(self, year: int | None = None, full: bool = False,
                      corrida_id: int = 0, force: bool = False):
        """
        Descarga todos los meses disponibles del año indicado desde oece.gob.pe.
        Usa la fuente secundaria (OCP) solo para carga histórica (--full).

        force=True: re-descarga el mes actual aunque exista en caché.
        """
        año = year or datetime.utcnow().year

        if full:
            # Carga histórica completa: usar fuente legacy anual
            archivo = self._download_year_legacy(año, force=force)
            return self.iter_releases_from_jsonlgz(archivo)

        # Fuente primaria: descargar todos los meses del año hasta el actual
        ahora = datetime.utcnow()
        mes_final = ahora.month if año == ahora.year else 12

        def _generar():
            for mes in range(1, mes_final + 1):
                try:
                    archivo = self._download_month(año, mes, force=force)
                    yield from self.iter_releases_from_zip(archivo)
                except Exception as exc:
                    logger.warning("No se pudo obtener %d/%02d: %s", año, mes, exc)

        return _generar()

    def save_raw(self, releases: list[dict], corrida_id: int) -> Path:
        """Persiste una muestra de releases crudos para trazabilidad."""
        settings.ensure_dirs()
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archivo = Path(settings.etl_raw_dir) / f"sample_{corrida_id}_{ts}.json"
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(releases[:100], f, ensure_ascii=False, indent=2, default=str)
        logger.info("Muestra raw guardada: %s", archivo)
        return archivo
