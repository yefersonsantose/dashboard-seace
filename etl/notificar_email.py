"""
Notificador de convocatorias SEACE por email.

Lee palabras clave desde alertas_config.json, consulta la base de datos
en busca de convocatorias recientes que contengan esas palabras, y envía
un correo HTML formateado al destinatario configurado.

Uso:
  python notificar_email.py                    # usa alertas_config.json
  python notificar_email.py --dias 3           # últimos 3 días
  python notificar_email.py --test             # envía aunque no haya nuevas
"""
import argparse
import json
import logging
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from sqlalchemy import create_engine, text
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("notificar_email")

# Ruta al config de alertas (un nivel arriba de etl/)
CONFIG_PATH = Path(__file__).resolve().parent.parent / "alertas_config.json"
ENV_PATH    = Path(__file__).resolve().parent.parent / ".env"


def cargar_config() -> dict:
    if not CONFIG_PATH.exists():
        logger.error("No se encontró %s", CONFIG_PATH)
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def cargar_credenciales_email() -> tuple[str, str]:
    """Lee EMAIL_USER y EMAIL_APP_PASSWORD del .env"""
    usuario = None
    password = None
    if ENV_PATH.exists():
        for linea in ENV_PATH.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea.startswith("EMAIL_USER="):
                usuario = linea.split("=", 1)[1].strip()
            elif linea.startswith("EMAIL_APP_PASSWORD="):
                password = linea.split("=", 1)[1].strip()
    if not usuario or not password:
        logger.error(
            "Faltan EMAIL_USER y EMAIL_APP_PASSWORD en .env\n"
            "Agrega estas líneas al archivo .env:\n"
            "  EMAIL_USER=tu_correo@gmail.com\n"
            "  EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx"
        )
        sys.exit(1)
    return usuario, password


def buscar_convocatorias(palabras: list[str], dias_atras: int) -> list[dict]:
    """Consulta la BD por convocatorias recientes que contengan alguna palabra clave."""
    IS_SQLITE = settings.database_url.startswith("sqlite")
    args = {"check_same_thread": False} if IS_SQLITE else {}
    engine = create_engine(settings.database_url, connect_args=args)

    fecha_desde = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
    resultados = []

    with engine.connect() as conn:
        for palabra in palabras:
            rows = conn.execute(text("""
                SELECT
                    p.codigo_seace,
                    e.nombre        AS entidad,
                    p.objeto_contratacion,
                    p.valor_referencial,
                    p.moneda,
                    p.fecha_convocatoria,
                    p.nivel_gobierno,
                    p.entidad_departamento AS departamento,
                    p.url_seace,
                    est.nombre      AS estado,
                    tip.nombre      AS tipo_proceso
                FROM procesos p
                JOIN entidades e      ON p.entidad_id = e.id
                LEFT JOIN cat_estados est        ON p.estado_id = est.id
                LEFT JOIN cat_tipos_proceso tip  ON p.tipo_proceso_id = tip.id
                WHERE p.objeto_contratacion LIKE :patron
                  AND p.fecha_convocatoria >= :fecha
                ORDER BY p.fecha_convocatoria DESC
                LIMIT 100
            """), {"patron": f"%{palabra}%", "fecha": fecha_desde}).fetchall()

            for r in rows:
                resultados.append({
                    "palabra_clave": palabra,
                    "codigo_seace":  r[0],
                    "entidad":       r[1],
                    "objeto":        r[2],
                    "monto":         r[3],
                    "moneda":        r[4] or "PEN",
                    "fecha":         r[5],
                    "nivel":         r[6] or "—",
                    "departamento":  r[7] or "—",
                    "url_seace":     r[8],
                    "estado":        r[9] or "—",
                    "tipo_proceso":  r[10] or "—",
                })

    # Deduplicar por codigo_seace
    vistos = set()
    unicos = []
    for r in resultados:
        if r["codigo_seace"] not in vistos:
            vistos.add(r["codigo_seace"])
            unicos.append(r)

    return unicos


def fmt_monto(monto, moneda) -> str:
    if not monto:
        return "—"
    try:
        return f"S/ {float(monto):,.0f}" if moneda == "PEN" else f"{moneda} {float(monto):,.0f}"
    except Exception:
        return str(monto)


def construir_html(convocatorias: list[dict], palabras: list[str], dias_atras: int, fecha_envio: str) -> str:
    total = len(convocatorias)
    palabras_str = ", ".join(f'<strong>"{p}"</strong>' for p in palabras)
    periodo = f"últimas {dias_atras} hora{'s' if dias_atras == 1 else 's'}" if dias_atras <= 1 else f"últimos {dias_atras} días"

    # Agrupar por palabra clave
    por_palabra = {}
    for c in convocatorias:
        por_palabra.setdefault(c["palabra_clave"], []).append(c)

    filas_html = ""
    for idx, c in enumerate(convocatorias):
        bg = "#f9fafb" if idx % 2 == 0 else "#ffffff"
        url = c["url_seace"] or "#"
        codigo_link = (
            f'<a href="{url}" style="color:#2563eb;text-decoration:none;font-family:monospace;">{c["codigo_seace"]}</a>'
            if c["url_seace"] else
            f'<span style="font-family:monospace;color:#374151;">{c["codigo_seace"]}</span>'
        )
        nivel_color = {
            "Gobierno Nacional":    "#7c3aed",
            "Gobierno Regional":    "#059669",
            "Municipal Provincial": "#d97706",
            "Municipal Distrital":  "#ca8a04",
        }.get(c["nivel"], "#6b7280")
        nivel_badge = f'<span style="background:{nivel_color};color:white;padding:2px 7px;border-radius:4px;font-size:11px;">{c["nivel"]}</span>'

        filas_html += f"""
        <tr style="background:{bg};">
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">{codigo_link}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:12px;">{c['entidad']}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:12px;">{c['objeto'] or '—'}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:600;color:#065f46;">{fmt_monto(c['monto'], c['moneda'])}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;text-align:center;">{nivel_badge}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:12px;">{c['departamento']}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:12px;">{c['fecha'] or '—'}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:11px;color:#374151;">{c['tipo_proceso']}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:11px;">
            <span style="background:#dbeafe;color:#1d4ed8;padding:2px 6px;border-radius:4px;">{c['estado']}</span>
          </td>
        </tr>"""

    resumen_palabras = ""
    for palabra, items in por_palabra.items():
        resumen_palabras += f'<span style="background:#1e3a5f;color:white;padding:4px 10px;border-radius:20px;margin:4px;display:inline-block;">"{palabra}" — {len(items)} resultado{"s" if len(items)!=1 else ""}</span>'

    sin_resultados = ""
    if total == 0:
        sin_resultados = """
        <div style="text-align:center;padding:40px;color:#6b7280;">
          <div style="font-size:40px;">🔍</div>
          <p style="font-size:16px;margin-top:10px;">No se encontraron convocatorias nuevas para las palabras configuradas.</p>
          <p style="font-size:13px;">Puede que no haya habido publicaciones en este período o que las palabras clave no coincidan.</p>
        </div>"""
        tabla = sin_resultados
    else:
        tabla = f"""
        <div style="overflow-x:auto;">
        <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;font-size:13px;font-family:Arial,sans-serif;">
          <thead>
            <tr style="background:#1e3a5f;color:white;">
              <th style="padding:10px;text-align:left;">Código SEACE</th>
              <th style="padding:10px;text-align:left;">Entidad</th>
              <th style="padding:10px;text-align:left;">Objeto / Descripción</th>
              <th style="padding:10px;text-align:right;">Monto</th>
              <th style="padding:10px;text-align:center;">Nivel</th>
              <th style="padding:10px;text-align:left;">Departamento</th>
              <th style="padding:10px;text-align:left;">Fecha</th>
              <th style="padding:10px;text-align:left;">Tipo</th>
              <th style="padding:10px;text-align:left;">Estado</th>
            </tr>
          </thead>
          <tbody>{filas_html}</tbody>
        </table>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">
<div style="max-width:960px;margin:20px auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.07);">

  <!-- Cabecera -->
  <div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:28px 32px;">
    <div style="color:white;">
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;opacity:0.8;">Alerta Diaria — Dashboard SEACE</div>
      <div style="font-size:26px;font-weight:700;margin:8px 0;">📋 Nuevas Convocatorias</div>
      <div style="font-size:14px;opacity:0.85;">Palabras clave: {palabras_str} &nbsp;|&nbsp; {periodo.capitalize()} &nbsp;|&nbsp; {fecha_envio}</div>
    </div>
  </div>

  <!-- Resumen -->
  <div style="padding:20px 32px;background:#f0f4ff;border-bottom:1px solid #e0e7ff;">
    <div style="font-size:32px;font-weight:800;color:#1e3a5f;">{total}</div>
    <div style="font-size:14px;color:#4b5563;">convocatoria{"s" if total != 1 else ""} encontrada{"s" if total != 1 else ""}</div>
    <div style="margin-top:12px;">{resumen_palabras}</div>
  </div>

  <!-- Tabla -->
  <div style="padding:24px 32px;">
    {tabla}
  </div>

  <!-- Pie -->
  <div style="padding:20px 32px;background:#f9fafb;border-top:1px solid #e5e7eb;text-align:center;">
    <p style="font-size:12px;color:#6b7280;margin:0;">
      Este correo fue generado automáticamente por el Dashboard SEACE.<br>
      Para cambiar las palabras clave, edita el archivo <strong>alertas_config.json</strong>.<br>
      Fuente: <a href="https://contratacionesabiertas.oece.gob.pe" style="color:#2563eb;">contratacionesabiertas.oece.gob.pe</a>
    </p>
  </div>

</div>
</body>
</html>"""


def enviar_email(destinatario: str, asunto: str, html: str, usuario: str, password: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = f"Dashboard SEACE <{usuario}>"
    msg["To"]      = destinatario
    msg.attach(MIMEText(html, "html", "utf-8"))

    logger.info("Conectando con Gmail SMTP...")
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(usuario, password)
        smtp.sendmail(usuario, destinatario, msg.as_string())
    logger.info("Correo enviado a %s", destinatario)


def main():
    parser = argparse.ArgumentParser(description="Alerta diaria de convocatorias SEACE por email")
    parser.add_argument("--dias",  type=int, default=None, help="Días atrás a consultar (default: valor en alertas_config.json)")
    parser.add_argument("--test",  action="store_true",    help="Enviar aunque no haya resultados")
    parser.add_argument("--palabras", nargs="+",           help="Palabras clave a buscar (sobreescribe el config)")
    args = parser.parse_args()

    cfg         = cargar_config()
    palabras    = args.palabras or cfg.get("palabras_clave", ["PUENTE"])
    dias_atras  = args.dias     or cfg.get("dias_atras", 1)
    destinatario = cfg.get("destinatario", "")

    if not destinatario:
        logger.error("Falta 'destinatario' en alertas_config.json")
        sys.exit(1)

    logger.info("Buscando convocatorias con palabras: %s | últimos %d días", palabras, dias_atras)
    convocatorias = buscar_convocatorias(palabras, dias_atras)
    logger.info("Encontradas: %d convocatorias", len(convocatorias))

    if not convocatorias and not args.test:
        logger.info("Sin resultados nuevos — no se envía correo. Usa --test para forzar envío.")
        return

    usuario, password = cargar_credenciales_email()

    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    palabras_asunto = " / ".join(f'"{p}"' for p in palabras)
    asunto = f"[SEACE] {len(convocatorias)} convocatoria{'s' if len(convocatorias)!=1 else ''} — {palabras_asunto} — {datetime.now().strftime('%d/%m/%Y')}"

    html = construir_html(convocatorias, palabras, dias_atras, fecha_hoy)
    enviar_email(destinatario, asunto, html, usuario, password)


if __name__ == "__main__":
    main()
