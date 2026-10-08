"""Paso 3 de la revisión diaria de remitos de hielo: publica lo que Claude revisó y arma el correo y el mensaje de Slack.

Uso:
    python3 publicar_revision.py --fecha 2026-10-07

Lee salidas/remitos_<fecha>/manifest.json (de remitos_del_dia.py) y salidas/remitos_<fecha>/revision.json (lo escribe la
tarea de Claude después de abrir cada PDF). Formato de revision.json:
    {"fecha": "YYYY-MM-DD", "revisiones": [
        {"po_id": 326591, "documento": "OC Rappi 4502056843 (otra orden), 'Recibí 40 bolsas'",
         "cantidad_documento": "40", "veredicto": "NO COINCIDE", "detalle": "Nitro 100, documento 40 (+60)"}, ...]}
Veredictos: COINCIDE · NO COINCIDE · DOCUMENTO NO CORRESPONDE (otra orden/fecha/tienda, foto vieja o de pantalla) ·
SIN CANTIDAD EN FOTO (la foto es solo la OC/pedido) · NO LEGIBLE.
"A revisar" (lo que va a Slack) = NO COINCIDE + DOCUMENTO NO CORRESPONDE (Kevin, 2026-10-08).

Hace:
  1. Guarda todas las revisiones en la pestaña "Revisión remitos" del sheet Ticket Hielo vía Control Hielo
     (doPost accion=revisionRemitos, token en ~/.config/hielo/revision_token). El dash de trazabilidad las muestra.
  2. Escribe salidas/remitos_<fecha>/revision.html (correo a Kevin) y revision.slack.md (canal #hielo-ingresos-sin-foto).
  stdout: JSON {fecha, revisados, coinciden, revisar, sin_cantidad, no_legible, asunto, html, slack, guardado}.
"""
import argparse
import datetime
import html
import json
import os
import sys
import urllib.request

from ingresos_sin_foto import (CDMX, CONTROL_HIELO_URL, DASH_URL, SLACK_MAX, con_reintentos, numero)

AQUI = os.path.dirname(os.path.abspath(__file__))
VEREDICTOS = ["COINCIDE", "NO COINCIDE", "DOCUMENTO NO CORRESPONDE", "SIN CANTIDAD EN FOTO", "NO LEGIBLE"]
REVISAR = ("NO COINCIDE", "DOCUMENTO NO CORRESPONDE")


def cargar(fecha):
    carpeta = os.path.join(AQUI, "salidas", f"remitos_{fecha}")
    with open(os.path.join(carpeta, "manifest.json")) as f:
        manifest = json.load(f)["ordenes"]
    with open(os.path.join(carpeta, "revision.json")) as f:
        revision = json.load(f)
    por_po = {str(r["po_id"]): r for r in revision.get("revisiones", [])}
    faltan = [str(o["po_id"]) for o in manifest if str(o["po_id"]) not in por_po]
    if faltan:
        raise ValueError("revision.json no trae veredicto para: " + ", ".join(faltan))
    malos = [k for k, r in por_po.items() if r.get("veredicto") not in VEREDICTOS]
    if malos:
        raise ValueError("Veredicto inválido en: " + ", ".join(malos))
    filas = []
    for o in manifest:
        r = por_po[str(o["po_id"])]
        filas.append(dict(o, documento=r.get("documento", ""), cantidad_documento=r.get("cantidad_documento"),
                          veredicto=r["veredicto"], detalle=r.get("detalle", "")))
    return carpeta, filas


def guardar(fecha, filas):
    with open(os.path.expanduser("~/.config/hielo/revision_token")) as f:
        token = f.read().strip()
    cuerpo = {"accion": "revisionRemitos", "token": token, "fecha": fecha, "revisiones": [
        {"po_id": r["po_id"], "external_id": r["external_id"], "tienda": r["tienda"], "proveedor": r["proveedor"],
         "recibido_nitro": r["recibido_total"], "cantidad_documento": r["cantidad_documento"], "veredicto": r["veredicto"],
         "detalle": ((r["documento"] + " · ") if r["documento"] else "") + (r["detalle"] or ""),
         "remito_url": r["remito_nitro_url"]} for r in filas]}

    def enviar():
        req = urllib.request.Request(CONTROL_HIELO_URL, json.dumps(cuerpo).encode(), {"Content-Type": "text/plain"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            res = json.load(resp)
        if res.get("error"):
            raise RuntimeError("Control Hielo no guardó la revisión: " + str(res.get("mensaje")))
        return res
    return con_reintentos(enviar)


def conteos(filas):
    c = {v: sum(1 for r in filas if r["veredicto"] == v) for v in VEREDICTOS}
    return c, (f"{len(filas)} remitos revisados: {c['COINCIDE']} coinciden · "
               f"{c['NO COINCIDE'] + c['DOCUMENTO NO CORRESPONDE']} a revisar · "
               f"{c['SIN CANTIDAD EN FOTO']} sin cantidad en la foto · {c['NO LEGIBLE']} no legibles")


def armar_slack(fecha, filas):
    fecha_txt = datetime.date.fromisoformat(fecha).strftime("%d/%m/%Y")
    _, resumen = conteos(filas)
    titulo = f"**🧊 Remitos de hielo a revisar · {fecha_txt}**\n{resumen}.\n"
    pie = (f"\n📊 [Ver el dash de trazabilidad]({DASH_URL}) (las órdenes a revisar salen marcadas con ⚠️)\n"
           "_Revisión de la foto del remito que la tienda sube en Nitro al cerrar la recepción, contra lo que registró como "
           "recibido. A revisar = la cantidad no coincide o el documento no corresponde a la orden._")
    revisar = [r for r in filas if r["veredicto"] in REVISAR]
    if not revisar:
        return titulo + ("\n✅ Todos los remitos revisados coinciden o no traen diferencias que revisar.\n" if filas
                         else "\nNo hubo recepciones de hielo en Nitro.\n") + pie
    limpia = lambda v: str(v if v not in (None, "") else "—").replace("|", "/").replace("\n", " ")
    texto = titulo + ("\n| Tienda | Proveedor | ID Nitro | External ID | Nitro | Remito | Motivo | PDF |\n"
                      "|---|---|---|---|---|---|---|---|\n")
    for i, r in enumerate(revisar):
        motivo = limpia(r["detalle"] or r["veredicto"])
        if len(motivo) > 140:
            motivo = motivo[:137] + "…"
        linea = (f"| {limpia(r['tienda'])} | {limpia(r['proveedor'])} | **{r['po_id']}** | {limpia(r['external_id'])} | "
                 f"{numero(r['recibido_total'])} | {limpia(r['cantidad_documento'])} | {motivo} | "
                 + (f"[ver]({r['remito_nitro_url']})" if r["remito_nitro_url"] else "—") + " |\n")
        aviso = f"\n_… y {len(revisar) - i} más (detalle en el dash)._\n"
        if len(texto) + len(linea) + len(aviso) + len(pie) > SLACK_MAX:
            return texto + aviso + pie
        texto += linea
    return texto + pie


def armar_html(fecha, filas):
    e = html.escape
    fecha_txt = datetime.date.fromisoformat(fecha).strftime("%d/%m/%Y")
    _, resumen = conteos(filas)
    th = "text-align:left;padding:6px 8px;background:#0f172a;color:#fff;font-size:12px;"
    td = "padding:6px 8px;border-bottom:1px solid #e2e8f0;font-size:12px;vertical-align:top;"

    def tabla(lista):
        if not lista:
            return "<p style='font-size:13px;color:#64748b'>Ninguna.</p>"
        h = ["<table style='border-collapse:collapse;width:100%;font-family:Arial,sans-serif'><tr>" +
             "".join(f"<th style='{th}'>{c}</th>" for c in ("Tienda", "Proveedor", "ID Nitro", "External ID", "Ingreso",
                                                          "Nitro", "Remito", "Veredicto", "Detalle", "PDF")) + "</tr>"]
        for r in lista:
            pdf = f"<a href='{e(r['remito_nitro_url'])}'>Ver</a>" if r["remito_nitro_url"] else "—"
            h.append("<tr>" + "".join(f"<td style='{td}'>{c}</td>" for c in (
                e(r["tienda"] or ""), e(r["proveedor"] or ""), f"<b>{r['po_id']}</b>", e(str(r["external_id"] or "—")),
                e((r["ingreso_mx"] or "")[11:16]), e(numero(r["recibido_total"])), e(str(r["cantidad_documento"] or "—")),
                e(r["veredicto"]), e(((r["documento"] + " · ") if r["documento"] else "") + (r["detalle"] or "")), pdf)) + "</tr>")
        return "\n".join(h) + "</table>"
    revisar = [r for r in filas if r["veredicto"] in REVISAR]
    otros = [r for r in filas if r["veredicto"] in ("SIN CANTIDAD EN FOTO", "NO LEGIBLE")]
    return f"""<div style="font-family:Arial,sans-serif;color:#0f172a;max-width:1000px">
<h2 style="margin:0 0 8px">🧊 Remitos de hielo a revisar · {fecha_txt}</h2>
<p style="margin:0 0 12px;font-size:14px">{e(resumen)}.</p>
<h3 style="margin:14px 0 6px;font-size:15px;color:#b91c1c">⚠️ A revisar (se mandó a Slack)</h3>
{tabla(revisar)}
<h3 style="margin:18px 0 6px;font-size:15px;color:#64748b">Sin cantidad en la foto / no legibles (no se mandan a Slack)</h3>
{tabla(otros)}
<p style="margin:14px 0 0;font-size:13px">📊 <a href="{DASH_URL}">Ver el dash de trazabilidad</a></p>
<p style="margin:12px 0 0;font-size:11px;color:#64748b">Revisión de la foto del remito (PDF que arma Nitro al cerrar la recepción)
contra lo registrado como recibido en Nitro. Generado {datetime.datetime.now(CDMX).strftime('%d/%m/%Y %H:%M')} CDMX.</p></div>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fecha", required=True, help="YYYY-MM-DD (la misma que usó remitos_del_dia.py)")
    ap.add_argument("--sin-guardar", action="store_true", help="no escribe en el sheet (pruebas)")
    args = ap.parse_args()
    carpeta, filas = cargar(args.fecha)
    guardado = False
    if not args.sin_guardar:
        guardar(args.fecha, filas)
        guardado = True
    ruta_html = os.path.join(carpeta, "revision.html")
    with open(ruta_html, "w") as f:
        f.write(armar_html(args.fecha, filas))
    ruta_slack = os.path.join(carpeta, "revision.slack.md")
    with open(ruta_slack, "w") as f:
        f.write(armar_slack(args.fecha, filas))
    c, _ = conteos(filas)
    revisar = c["NO COINCIDE"] + c["DOCUMENTO NO CORRESPONDE"]
    fecha_txt = datetime.date.fromisoformat(args.fecha).strftime("%d/%m/%Y")
    asunto = (f"🧊 Remitos de hielo {fecha_txt}: {revisar} a revisar de {len(filas)}" if revisar
              else f"🧊 Remitos de hielo {fecha_txt}: sin diferencias ({len(filas)} revisados)")
    print(json.dumps({"fecha": args.fecha, "revisados": len(filas), "coinciden": c["COINCIDE"], "revisar": revisar,
                      "sin_cantidad": c["SIN CANTIDAD EN FOTO"], "no_legible": c["NO LEGIBLE"], "asunto": asunto,
                      "html": ruta_html, "slack": ruta_slack, "guardado": guardado}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(json.dumps({"error": str(err)}, ensure_ascii=False))
        sys.exit(1)
