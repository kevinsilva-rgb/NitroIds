"""Cliente mínimo de la API de Redash (redash.rappi.com) para el reporte diario de hielo.

La API key se lee de la variable REDASH_API_KEY o del archivo ~/.config/redash/api_key (fuera del repo).
"""
import json
import os
import time
import urllib.request

REDASH_URL = "https://redash.rappi.com"


def _api_key():
    key = os.environ.get("REDASH_API_KEY")
    if key:
        return key.strip()
    with open(os.path.expanduser("~/.config/redash/api_key")) as f:
        return f.read().strip()


def _req(path, data=None, timeout=120):
    headers = {"Authorization": "Key " + _api_key(), "Content-Type": "application/json"}
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(REDASH_URL + path, body, headers, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _esperar_job(resp, max_espera=300):
    if "job" not in resp:
        return resp
    job = resp["job"]
    inicio = time.time()
    while job["status"] in (1, 2):
        if time.time() - inicio > max_espera:
            raise TimeoutError("Redash no terminó el job %s" % job["id"])
        time.sleep(2)
        job = _req("/api/jobs/" + job["id"])["job"]
    if job["status"] != 3:
        raise RuntimeError("Redash falló: %s" % job.get("error"))
    return _req("/api/query_results/%s" % job["query_result_id"])


def filas_query(query_id, max_age=0):
    """Filas de una query guardada; max_age=0 fuerza re-ejecución."""
    resp = _req("/api/queries/%s/results" % query_id, {"max_age": max_age})
    return _esperar_job(resp)["query_result"]["data"]["rows"]


def filas_sql(data_source_id, sql):
    """Filas de un SQL ad-hoc (sin guardar) en un data source."""
    resp = _req("/api/query_results", {"data_source_id": data_source_id, "query": sql, "max_age": 0})
    return _esperar_job(resp)["query_result"]["data"]["rows"]
