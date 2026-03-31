"""
Módulo de transformación — Mapeo OCDS → Modelo de datos propio.

Referencia de campos OCDS: https://standard.open-contracting.org/latest/es/
Mapeo documentado en: docs/fase1_analisis_fuente.md
"""
import logging
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

logger = logging.getLogger(__name__)

# ── Mapas de normalización ────────────────────────────────────

# Clasificación de entidades por nivel de gobierno (basado en nombre)
_TIPO_ENTIDAD_REGLAS = [
    ("MUN_DISTRITAL",  ["MUNICIPALIDAD DISTRITAL", "M.D. DE", "MUNI. DISTRITAL"]),
    ("MUN_PROVINCIAL", ["MUNICIPALIDAD PROVINCIAL", "MUNICIPALIDAD METROPOLITANA", "M.P. DE"]),
    ("GOB_REGIONAL",   ["GOBIERNO REGIONAL", "SUB REGION ", "SUBREGION ", "AUTORIDAD REGIONAL",
                        "GERENCIA REGIONAL", "DIRECCIÓN REGIONAL DE"]),
]

NIVEL_GOBIERNO_DISPLAY = {
    "GOB_NACIONAL":   "Gobierno Nacional",
    "GOB_REGIONAL":   "Gobierno Regional",
    "MUN_PROVINCIAL": "Municipal Provincial",
    "MUN_DISTRITAL":  "Municipal Distrital",
}


def _tipo_entidad(nombre: str) -> str:
    """Clasifica una entidad por su nivel de gobierno según el nombre."""
    n = (nombre or "").upper()
    for tipo, patrones in _TIPO_ENTIDAD_REGLAS:
        if any(p in n for p in patrones):
            return tipo
    return "GOB_NACIONAL"


ESTADOS_OCDS = {
    "planning": "PLANIFICACION",
    "planned": "PLANIFICACION",
    "active": "ACTIVO",
    "cancelled": "CANCELADO",
    "unsuccessful": "DESIERTO",
    "complete": "COMPLETADO",
    "withdrawn": "RETIRADO",
    # Estados adicionales usados por SEACE/OSCE
    "convocado": "CONVOCADO",
    "en_proceso": "EN_PROCESO",
    "buena_pro": "BUENA_PRO",
    "desierto": "DESIERTO",
    "cancelado": "CANCELADO",
    "nulo": "NULO",
    "suspendido": "SUSPENDIDO",
}

TIPOS_PROCESO_OCDS = {
    "open": "LICITACION_PUBLICA",
    "selective": "CONCURSO_PUBLICO",
    "limited": "ADJUDICACION_SIMPLIFICADA",
    "direct": "CONTRATACION_DIRECTA",
}


# ── Helpers ───────────────────────────────────────────────────

def _texto(valor) -> Optional[str]:
    if not valor:
        return None
    return re.sub(r"\s+", " ", str(valor).strip()) or None


def _monto(valor) -> Optional[Decimal]:
    if valor is None:
        return None
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError):
        logger.debug("Monto no convertible: %s", valor)
        return None


def _fecha(valor) -> Optional[date]:
    if not valor:
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    s = str(valor).strip()
    # Intentar fromisoformat (maneja timezone +/-HH:MM y Z desde Python 3.11)
    try:
        s_iso = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s_iso).date()
    except (ValueError, TypeError):
        pass
    # Fallback formatos simples
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
        try:
            return datetime.strptime(s[:10], fmt).date()
        except (ValueError, TypeError):
            continue
    logger.debug("Fecha no parseada: %s", valor)
    return None


def _ruc_de_id(party_id: Optional[str]) -> Optional[str]:
    """Extrae el RUC (11 dígitos) de un identificador OCDS como 'PE-RUC-20123456789'."""
    if not party_id:
        return None
    m = re.search(r"\d{11}", str(party_id))
    return m.group(0) if m else None


def _estado(tender_status: Optional[str], awards: list = None) -> str:
    """
    Deriva el estado del proceso.
    SEACE OCDS no siempre rellena tender.status; se infiere de awards.
    """
    if tender_status:
        return ESTADOS_OCDS.get(tender_status.lower(), tender_status.upper().replace(" ", "_"))
    # Inferir desde awards
    for award in (awards or []):
        items_status = {i.get("statusDetails", "").upper() for i in award.get("items") or []}
        if "CONTRATADO" in items_status:
            return "CONTRATADO"
        if "DESIERTO" in items_status:
            return "DESIERTO"
        status = award.get("status", "")
        if status:
            return ESTADOS_OCDS.get(status.lower(), status.upper().replace(" ", "_"))
    return "CONVOCADO"  # default para procesos sin awards


def _tipo_proceso(method: Optional[str], method_details: Optional[str]) -> Optional[str]:
    """Devuelve el tipo de proceso normalizado a partir de los campos OCDS."""
    if method_details:
        return _texto(method_details)
    if method:
        return TIPOS_PROCESO_OCDS.get(method.lower(), _texto(method))
    return None


# ── Transformación principal ──────────────────────────────────

def _get_buyer(release: dict) -> dict:
    """
    Extrae la entidad compradora con todos sus datos (incluyendo address).
    parties tiene el objeto completo; buyer raíz solo tiene id+name.
    """
    # Buscar en parties (tiene address completo)
    for p in release.get("parties") or []:
        if "buyer" in (p.get("roles") or []) or "procuringEntity" in (p.get("roles") or []):
            return p
    # Fallback al campo buyer raíz
    return release.get("buyer") or {}


def _get_award_date(awards: list[dict]) -> Optional[date]:
    """Fecha del primer award activo."""
    for award in awards or []:
        if award.get("status") in ("active", "unsuccessful", "cancelled"):
            return _fecha(award.get("date"))
    return None


def transformar_release(release: dict) -> Optional[dict]:
    """
    Transforma un release OCDS en el formato del modelo propio.
    Retorna None si faltan campos mínimos obligatorios.
    """
    ocid = _texto(release.get("ocid"))
    if not ocid:
        return None

    tender = release.get("tender") or {}
    awards = release.get("awards") or []

    buyer = _get_buyer(release)
    tender_value = tender.get("value") or {}
    tender_period = tender.get("tenderPeriod") or {}

    entidad_nombre = _texto(buyer.get("name"))
    if not entidad_nombre:
        entidad_nombre = _texto(tender.get("procuringEntity", {}).get("name"))

    # Extraer dirección completa del buyer (departamento, provincia, distrito)
    buyer_address = buyer.get("address") or {}
    departamento = _texto(buyer_address.get("department"))
    # En OCDS de SEACE: address.region = provincia, address.locality = distrito
    provincia  = _texto(buyer_address.get("region"))
    distrito   = _texto(buyer_address.get("locality"))

    # Clasificar tipo de entidad por nombre
    tipo_ent = _tipo_entidad(entidad_nombre or "")
    nivel    = NIVEL_GOBIERNO_DISPLAY.get(tipo_ent, "Gobierno Nacional")

    # Extraer RUC desde additionalIdentifiers (scheme PE-RUC)
    ruc = None
    for ident in buyer.get("additionalIdentifiers") or []:
        if ident.get("scheme") == "PE-RUC":
            ruc = _texto(ident.get("id"))
            break
    if not ruc:
        ruc = _ruc_de_id(buyer.get("id"))

    return {
        "codigo_seace": ocid,
        "nro_expediente": _texto(tender.get("id")),
        "entidad_nombre": entidad_nombre,
        "entidad_ruc": ruc,
        "tipo_entidad": tipo_ent,
        "nivel_gobierno": nivel,
        "entidad_departamento": departamento,
        "entidad_provincia": provincia,
        "entidad_distrito": distrito,
        "objeto_contratacion": _texto(tender.get("description")) or _texto(tender.get("title")),
        "descripcion": _texto(tender.get("description")),
        "tipo_proceso": _tipo_proceso(
            tender.get("procurementMethod"),
            tender.get("procurementMethodDetails"),
        ),
        "estado": _estado(tender.get("status"), awards),
        "valor_referencial": _monto(tender_value.get("amount")),
        "moneda": _texto(tender_value.get("currency")) or "PEN",
        "fecha_convocatoria": _fecha(tender_period.get("startDate") or release.get("date")),
        "fecha_buena_pro": _get_award_date(awards),
        "ubigeo": None,
        "url_seace": _texto(release.get("url")),
        "fuente_raw": {**release, "_meta": {
            "departamento": departamento,
            "provincia": provincia,
            "distrito": distrito,
            "nivel_gobierno": nivel,
        }},
    }


def transformar_lote(releases) -> tuple[list[dict], list[dict]]:
    """
    Transforma un iterable de releases OCDS.
    Retorna (válidos, errores).
    """
    validos, errores = [], []
    for release in releases:
        try:
            resultado = transformar_release(release)
            if resultado:
                validos.append(resultado)
            else:
                errores.append({"ocid": release.get("ocid"), "motivo": "campos_minimos_faltantes"})
        except Exception as exc:
            logger.error("Error transformando release %s: %s", release.get("ocid"), exc)
            errores.append({"ocid": release.get("ocid"), "motivo": str(exc)})
    return validos, errores
