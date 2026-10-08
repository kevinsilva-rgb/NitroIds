"""Reporte diario: órdenes de hielo con ingreso en Nitro el día anterior y sus 2 fotos del remito (0/2, 1/2, 2/2).

Uso:
    python3 ingresos_sin_foto.py                  # día anterior (hora CDMX)
    python3 ingresos_sin_foto.py --fecha 2026-10-06

Las 2 fotos que se cuentan por orden (Kevin, 2026-10-08):
  1. Remito en Nitro: el PDF que arma la app de Nitro con la foto del remito al cerrar la recepción
     (turbo_reception_order_ms.reception_order_execution_document.url) — columna `remito_nitro_url` del SQL.
  2. Foto en NitroIds: la que sube la tienda en NitroIds (sheet "Ticket Hielo", vía Control Hielo `?api=idsConFoto`).
Pendiente = orden con menos de 2/2.

Fuentes:
  - Ingresos: SQL ad-hoc `ingresos_hielo.sql` sobre Redash (data source 10271, Turbo). Ingreso = recepción hecha en
    Nitro con hielo recibido > 0; fecha/hora = hora de la foto del remito en Nitro (no el cierre de la recepción).
  - Fotos de NitroIds: sheet "Ticket Hielo" vía el Web App de Control Hielo (`?api=idsConFoto`).

Salida:
  - salidas/ingresos_sin_foto_<fecha>.html      (cuerpo del correo a Kevin)
  - salidas/ingresos_sin_foto_<fecha>.slack.md  (mensaje para el canal privado #hielo-ingresos-sin-foto)
  - stdout: JSON con fecha, ingresos, completas (2/2), sin_foto (= incompletas, < 2/2), faltan_nitro, faltan_nitroids,
    asunto y rutas (lo lee la tarea programada para enviar correo y Slack).
Sale con código != 0 si no pudo armar el reporte (la tarea avisa por correo del error).
"""
import argparse
import datetime
import html
import json
import os
import sys
import time
import urllib.request

import redash

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA_SOURCE_TURBO = 10271
CONTROL_HIELO_URL = ("https://script.google.com/macros/s/"
                     "AKfycbxUy3nlvDOEHp20OzHcYJAH2N7f9El1eRjWl3lfVvNMJDw3EYRyz0E6j0dtKtDhHHjY/exec")
SHEET_TICKETS_URL = "https://docs.google.com/spreadsheets/d/1JB-eKW2W8zcHUeBvBFKmyb873KRWxXspGE0fQMor4C0/edit"
NITROIDS_URL = "https://kevinsilva-rgb.github.io/NitroIds/"
DASH_URL = ("https://script.google.com/macros/s/"
            "AKfycbzrQM4Gzr_SfLHss2pD-MiWXVL_GVFazwIMQn7bm1T0mKf5V5CvQ17lbTQC8vt8mmMp-Q/exec")  # Dash-Hielo-Trazabilidad
CDMX = datetime.timezone(datetime.timedelta(hours=-6))  # México sin horario de verano desde 2022
SLACK_MAX = 4800  # límite de Slack: 5000 caracteres por bloque de texto


def con_reintentos(fn, intentos=3, espera=20):
    for i in range(intentos):
        try:
            return fn()
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(espera)


def ids_con_foto():
    def pedir():
        with urllib.request.urlopen(CONTROL_HIELO_URL + "?api=idsConFoto", timeout=120) as r:
            datos = json.load(r)
        if datos.get("error"):
            raise RuntimeError("Control Hielo respondió error al leer el sheet Ticket Hielo")
        return {str(i).strip() for i in datos.get("idsConFoto", [])}
    return con_reintentos(pedir)


def ingresos(fecha):
    with open(os.path.join(AQUI, "ingresos_hielo.sql")) as f:
        sql = f.read().replace("{fecha}", fecha)
    return con_reintentos(lambda: redash.filas_sql(DATA_SOURCE_TURBO, sql))


def numero(v):
    v = float(v or 0)
    return str(int(v)) if v.is_integer() else str(v)


def con_fotos(filas, fotos_nitroids):
    """Agrega a cada fila: nitro (bool), nitroids (bool), n_fotos (0..2)."""
    for r in filas:
        r["nitro"] = bool(r.get("remito_nitro_url"))
        r["nitroids"] = str(r["po_id"]) in fotos_nitroids
        r["n_fotos"] = int(r["nitro"]) + int(r["nitroids"])
    return filas


def falta_txt(r):
    if r["n_fotos"] == 0:
        return "las 2"
    return "Nitro" if not r["nitro"] else "NitroIds"


def armar_html(fecha, filas, incompletas):
    e = html.escape
    fecha_txt = datetime.date.fromisoformat(fecha).strftime("%d/%m/%Y")
    estilo_th = "text-align:left;padding:6px 8px;background:#0f172a;color:#fff;font-size:12px;"
    estilo_td = "padding:6px 8px;border-bottom:1px solid #e2e8f0;font-size:12px;vertical-align:top;"
    completas = len(filas) - len(incompletas)
    if incompletas:
        resumen = (f"<b>{len(incompletas)} de {len(filas)}</b> órdenes de hielo con ingreso el {fecha_txt} "
                   f"<b style='color:#b91c1c'>no tienen las 2 fotos del remito</b> ({completas} con 2/2).")
        cuerpo = ["<table style='border-collapse:collapse;width:100%;font-family:Arial,sans-serif'>",
                  "<tr>" + "".join(f"<th style='{estilo_th}'>{c}</th>" for c in
                                   ("Tienda", "Proveedor", "ID Nitro", "External ID", "Ingreso", "Unidades",
                                    "Fotos", "Falta", "Remito Nitro")) + "</tr>"]
        for r in incompletas:
            hora = (r.get("ingreso_mx") or "")[11:16]
            remito = (f"<a href='{e(r['remito_nitro_url'])}'>Ver PDF</a>" if r["nitro"] else "—")
            cuerpo.append("<tr>" + "".join(f"<td style='{estilo_td}'>{c}</td>" for c in (
                e(r.get("tienda") or ""), e(r.get("proveedor") or ""), f"<b>{e(str(r['po_id']))}</b>",
                e(str(r.get("external_id") or "—")), e(hora), e(numero(r.get("unidades_hielo_recibidas"))),
                f"<b style='color:#b91c1c'>{r['n_fotos']}/2</b>", e(falta_txt(r)), remito)) + "</tr>")
        cuerpo.append("</table>")
        tabla = "\n".join(cuerpo)
    else:
        resumen = (f"✅ Las <b>{len(filas)}</b> órdenes de hielo con ingreso el {fecha_txt} tienen las 2 fotos (2/2)."
                   if filas else f"No hubo órdenes de hielo con ingreso en Nitro el {fecha_txt}.")
        tabla = ""
    return f"""<div style="font-family:Arial,sans-serif;color:#0f172a;max-width:900px">
<h2 style="margin:0 0 8px">🧊 Ingresos de hielo y fotos del remito · {fecha_txt}</h2>
<p style="margin:0 0 12px;font-size:14px">{resumen}</p>
{tabla}
<p style="margin:14px 0 0;font-size:13px">📊 <a href="{DASH_URL}">Ver el dash de trazabilidad</a> (histórico por día, tienda y orden)</p>
<p style="margin:12px 0 0;font-size:11px;color:#64748b">
Fotos por orden (2): <b>remito en Nitro</b> (PDF que arma Nitro al cerrar la recepción) y <b>foto en NitroIds</b>
(<a href="{SHEET_TICKETS_URL}">sheet Ticket Hielo</a>). Ingreso = recepción en Nitro con hielo recibido &gt; 0,
fecha y hora de la foto del remito en Nitro (hora CDMX), todos los proveedores. ·
<a href="{NITROIDS_URL}">NitroIds</a> · Generado {datetime.datetime.now(CDMX).strftime('%d/%m/%Y %H:%M')} CDMX
</p></div>"""


def armar_slack(fecha, filas, incompletas):
    fecha_txt = datetime.date.fromisoformat(fecha).strftime("%d/%m/%Y")
    pie = (f"\n📊 [Ver el dash de trazabilidad (histórico por día, tienda y orden)]({DASH_URL})\n"
           f"\n_Fotos por orden (2): remito en Nitro (PDF al cerrar la recepción) y foto en NitroIds "
           f"([sheet Ticket Hielo]({SHEET_TICKETS_URL})). Ingreso = recepción en Nitro con hielo recibido, a la hora "
           f"de la foto del remito en Nitro (CDMX), todos los proveedores. · [NitroIds]({NITROIDS_URL})_")
    titulo = f"**🧊 Ingresos de hielo y fotos del remito · {fecha_txt}**\n"
    if not incompletas:
        cuerpo = (f"✅ Las **{len(filas)}** órdenes de hielo con ingreso tienen las 2 fotos (2/2).\n" if filas
                  else "No hubo órdenes de hielo con ingreso en Nitro.\n")
        return titulo + cuerpo + pie
    limpia = lambda v: str(v or "—").replace("|", "/")
    encabezado = (titulo + f"**{len(incompletas)} de {len(filas)}** órdenes con ingreso **no tienen las 2 fotos** "
                  f"({len(filas) - len(incompletas)} con 2/2).\n\n"
                  "| Tienda | Proveedor | ID Nitro | External ID | Hora | Unid. | Fotos | Falta |\n"
                  "|---|---|---|---|---|---|---|---|\n")
    lineas = []
    for r in incompletas:
        lineas.append(f"| {limpia(r.get('tienda'))} | {limpia(r.get('proveedor'))} | **{r['po_id']}** | "
                      f"{limpia(r.get('external_id'))} | {(r.get('ingreso_mx') or '')[11:16]} | "
                      f"{numero(r.get('unidades_hielo_recibidas'))} | **{r['n_fotos']}/2** | {falta_txt(r)} |\n")
    texto = encabezado
    for i, linea in enumerate(lineas):
        resto = len(lineas) - i
        aviso = f"\n_… y {resto} más (detalle completo en el correo del reporte)._\n"
        if len(texto) + len(linea) + len(aviso) + len(pie) > SLACK_MAX:
            return texto + aviso + pie
        texto += linea
    return texto + pie


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fecha", help="YYYY-MM-DD (default: ayer en hora CDMX)")
    args = ap.parse_args()
    fecha = args.fecha or (datetime.datetime.now(CDMX).date() - datetime.timedelta(days=1)).isoformat()

    filas = con_fotos(ingresos(fecha), ids_con_foto())
    incompletas = [r for r in filas if r["n_fotos"] < 2]

    os.makedirs(os.path.join(AQUI, "salidas"), exist_ok=True)
    ruta = os.path.join(AQUI, "salidas", f"ingresos_sin_foto_{fecha}.html")
    with open(ruta, "w") as f:
        f.write(armar_html(fecha, filas, incompletas))
    ruta_slack = os.path.join(AQUI, "salidas", f"ingresos_sin_foto_{fecha}.slack.md")
    with open(ruta_slack, "w") as f:
        f.write(armar_slack(fecha, filas, incompletas))

    fecha_txt = datetime.date.fromisoformat(fecha).strftime("%d/%m/%Y")
    asunto = (f"🧊 Hielo {fecha_txt}: {len(incompletas)} de {len(filas)} ingresos sin las 2 fotos del remito"
              if incompletas else f"🧊 Hielo {fecha_txt}: todos los ingresos con 2/2 fotos ({len(filas)})")
    print(json.dumps({"fecha": fecha, "ingresos": len(filas), "completas": len(filas) - len(incompletas),
                      "sin_foto": len(incompletas),
                      "faltan_nitro": sum(1 for r in filas if not r["nitro"]),
                      "faltan_nitroids": sum(1 for r in filas if not r["nitroids"]),
                      "con_foto": len(filas) - len(incompletas),
                      "asunto": asunto, "html": ruta, "slack": ruta_slack}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(json.dumps({"error": str(err)}, ensure_ascii=False))
        sys.exit(1)
