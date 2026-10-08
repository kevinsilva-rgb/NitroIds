"""Paso 1 de la revisión diaria de remitos de hielo: prepara las recepciones del día para que Claude revise sus fotos.

Uso:
    python3 remitos_del_dia.py                  # día anterior (hora CDMX)
    python3 remitos_del_dia.py --fecha 2026-10-07

Saca de Redash (`remitos_hielo.sql`, data source 10271) las recepciones de hielo hechas en Nitro ese día, con lo pedido,
recibido, faltante, averiado y sobrante por producto, y descarga el PDF que arma Nitro con la foto del remito.

Salida: salidas/remitos_<fecha>/
  - po_<ID Nitro>.pdf     (uno por orden)
  - manifest.json         (lista de órdenes con sus datos de Nitro y la ruta de su PDF)
  stdout: JSON {fecha, ordenes, sin_pdf, carpeta, manifest, revision}. `revision` es la ruta donde la tarea de Claude debe
  escribir su revisión (ver PROMPT en la tarea programada y publicar_revision.py).
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request

import redash
from ingresos_sin_foto import CDMX, DATA_SOURCE_TURBO, con_reintentos

AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fecha", help="YYYY-MM-DD (default: ayer en hora CDMX)")
    args = ap.parse_args()
    fecha = args.fecha or (datetime.datetime.now(CDMX).date() - datetime.timedelta(days=1)).isoformat()

    with open(os.path.join(AQUI, "remitos_hielo.sql")) as f:
        sql = f.read().replace("{fecha}", fecha)
    filas = con_reintentos(lambda: redash.filas_sql(DATA_SOURCE_TURBO, sql))

    carpeta = os.path.join(AQUI, "salidas", f"remitos_{fecha}")
    os.makedirs(carpeta, exist_ok=True)
    ordenes = {}
    for r in filas:
        o = ordenes.setdefault(r["po_id"], {
            "po_id": r["po_id"], "external_id": r["external_id"], "tienda": r["tienda"], "proveedor": r["proveedor"],
            "estado_recepcion": r["estado_recepcion"], "ingreso_mx": r["ingreso_mx"],
            "remito_nitro_url": r["remito_nitro_url"], "pdf": None, "recibido_total": 0, "productos": []})
        o["productos"].append({k: r[k] for k in ("producto", "solicitado", "recibido", "faltante", "averiado", "sobrante")})
        o["recibido_total"] += float(r["recibido"] or 0)
    for o in ordenes.values():
        if o["remito_nitro_url"]:
            ruta = os.path.join(carpeta, f"po_{o['po_id']}.pdf")
            con_reintentos(lambda: urllib.request.urlretrieve(o["remito_nitro_url"], ruta))
            o["pdf"] = ruta
    lista = sorted(ordenes.values(), key=lambda o: (o["ingreso_mx"] or "", o["po_id"]))
    manifest = os.path.join(carpeta, "manifest.json")
    with open(manifest, "w") as f:
        json.dump({"fecha": fecha, "ordenes": lista}, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"fecha": fecha, "ordenes": len(lista), "sin_pdf": sum(1 for o in lista if not o["pdf"]),
                      "carpeta": carpeta, "manifest": manifest,
                      "revision": os.path.join(carpeta, "revision.json")}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(json.dumps({"error": str(err)}, ensure_ascii=False))
        sys.exit(1)
