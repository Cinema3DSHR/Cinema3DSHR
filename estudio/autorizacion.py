"""REGLA PERMANENTE: ningún render sin revisión 3D y autorización explícita del dueño (docs/REVISION_Y_AUTORIZACION.md).

Fuente única de la verdad para:
- el ESTADO de revisión de cada versión de escena (8 estados, en el catálogo y en la app);
- la VERIFICACIÓN que hacen todos los flujos de render de GitHub Actions y todos los comandos que renderizan
  (`python -m estudio render | fijas`, `pruebas/*/render_*.py`, animáticas): si no hay una autorización válida para
  esa versión exacta (misma huella) y esa configuración de render, el render se rechaza.

Los registros son Issues creados desde la app por una cuenta autorizada (config/autorizados.json):
- `[REVISIÓN] <prod> · <escena> v<k> · APROBAR | CORREGIR | RECHAZAR …` (aprobación atada a la huella);
- `[DIRECCIÓN] <prod> · <escena> v<k> · NOTA | MARCADOR | CAMARA | GUARDAR` (revisión y correcciones);
- `[AUTORIZACIÓN] <prod> · <escena> v<k> · RENDER FINAL` (botón AUTORIZAR RENDER FINAL de la app).
Cada uno lleva un bloque ```json``` con produccion, escena, version y huella.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from estudio import config

ESTADOS = ["EN PREPARACIÓN", "LISTA PARA REVISIÓN", "EN REVISIÓN", "CORRECCIONES SOLICITADAS",
           "APROBADA POR EL USUARIO", "RENDER AUTORIZADO", "RENDER EN EJECUCIÓN", "FINALIZADA"]
CAMPOS_CONFIG = ("resolucion", "fps", "muestras")      # lo que tiene que coincidir entre lo autorizado y lo pedido
_JSON = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)
PREFIJOS = {"[REVISIÓN]": "revision", "[DIRECCIÓN]": "direccion", "[AUTORIZACIÓN]": "autorizacion"}


def usuarios_autorizados() -> set[str]:
    p = config.RAIZ / "config" / "autorizados.json"
    us = json.loads(p.read_text()).get("usuarios", []) if p.exists() else []
    extra = os.environ.get("CINE_AUTORIZADOS", "")
    return {u.strip().lower() for u in list(us) + extra.split(",") if u.strip()}


def eventos(issues: list[dict]) -> list[dict]:
    """Registros válidos (sólo de cuentas autorizadas), en orden cronológico."""
    autorizados = usuarios_autorizados()
    out = []
    for it in issues:
        if "pull_request" in it:
            continue
        autor = (it.get("user") or {}).get("login", "")
        if autor.lower() not in autorizados:
            continue
        titulo = it.get("title", "")
        clase = next((c for p, c in PREFIJOS.items() if titulo.startswith(p)), None)
        if not clase:
            continue
        m = _JSON.search(it.get("body") or "")
        if not m:
            continue
        try:
            d = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        d.update({"clase": clase, "issue": it.get("number"), "fecha": it.get("created_at", ""), "autor": autor})
        out.append(d)
    return sorted(out, key=lambda e: e["fecha"])


def _de(evs, pid, eid, v):
    return [e for e in evs if e.get("produccion") == pid and e.get("escena") == eid and int(e.get("version", -1)) == v]


def aprobacion_vigente(evs: list[dict], pid: str, eid: str, v: int, huella: str) -> dict | None:
    """La última aprobación de ESA versión con ESA huella, siempre que después no se hayan pedido correcciones."""
    vigente = None
    for e in _de(evs, pid, eid, v):
        if e["clase"] == "revision" and e.get("decision") == "APROBAR":
            vigente = e if e.get("huella") == huella and huella else None
        elif (e["clase"] == "revision" and e.get("decision") in ("CORREGIR", "RECHAZAR")) or \
                (e["clase"] == "direccion" and e.get("tipo") in ("guardar", "camara")):
            vigente = None
    return vigente


def autorizacion_vigente(evs: list[dict], pid: str, eid: str, v: int, huella: str) -> dict | None:
    ap = aprobacion_vigente(evs, pid, eid, v, huella)
    if not ap:
        return None
    auts = [e for e in _de(evs, pid, eid, v) if e["clase"] == "autorizacion" and e.get("huella") == huella
            and e["fecha"] >= ap["fecha"]]
    return auts[-1] if auts else None


def estado(pid: str, eid: str, v: int, huella: str, evs: list[dict], previa: bool,
           render: str | None = None) -> str:
    """Estado de revisión de una versión. render: None | 'ejecutando' | 'finalizado' (render final publicado con esta
    huella). Sin previsualización publicada no hay revisión posible: EN PREPARACIÓN."""
    if render == "finalizado":
        return "FINALIZADA"
    aut = autorizacion_vigente(evs, pid, eid, v, huella)
    if render == "ejecutando" and aut:
        return "RENDER EN EJECUCIÓN"
    if aut:
        return "RENDER AUTORIZADO"
    if aprobacion_vigente(evs, pid, eid, v, huella):
        return "APROBADA POR EL USUARIO"
    if not previa:
        return "EN PREPARACIÓN"
    # los registros de otra huella (la escena cambió desde entonces) no cuentan para esta revisión
    mios = [e for e in _de(evs, pid, eid, v) if e.get("huella") in (None, "", huella)]
    if any((e["clase"] == "revision" and e.get("decision") in ("CORREGIR", "RECHAZAR"))
           or (e["clase"] == "direccion" and e.get("tipo") in ("guardar", "camara")) for e in mios):
        return "CORRECCIONES SOLICITADAS"
    if mios:
        return "EN REVISIÓN"
    return "LISTA PARA REVISIÓN"


def config_de(resolucion: str, fps, muestras) -> dict:
    return {"resolucion": str(resolucion), "fps": int(fps), "muestras": int(muestras)}


def verificar(m: dict, issues: list[dict], pedida: dict, huella: str | None = None) -> tuple[bool, str, dict | None]:
    """¿Se puede renderizar esta versión con esta configuración? (ok, motivo, autorización)."""
    from estudio import manifiesto as MF
    pid, eid, v = m["produccion"], m["id"].split("-")[-1], int(m["version"])
    h = huella or MF.huella(m)
    evs = eventos(issues)
    if not aprobacion_vigente(evs, pid, eid, v, h):
        otras = [e.get("huella") for e in _de(evs, pid, eid, v) if e.get("decision") == "APROBAR"]
        if h in otras:
            return False, (f"{pid} {eid} v{v}: después de la aprobación se pidieron correcciones; la aprobación ya no "
                           f"vale y la versión corregida tiene que volver a revisarse y aprobarse en la app"), None
        if otras:
            return False, (f"{pid} {eid} v{v}: la aprobación es de otra huella {otras} (actual {h}): la escena cambió "
                           f"después de aprobarla y tiene que volver a revisarse en la app"), None
        return False, f"{pid} {eid} v{v} no está APROBADA por el dueño en la app (huella {h})", None
    aut = autorizacion_vigente(evs, pid, eid, v, h)
    if not aut:
        return False, f"{pid} {eid} v{v} está aprobada pero falta AUTORIZAR RENDER FINAL desde la app (huella {h})", None
    cfg = aut.get("config") or {}
    distintos = {k: (cfg.get(k), pedida.get(k)) for k in CAMPOS_CONFIG if str(cfg.get(k)) != str(pedida.get(k))}
    if distintos:
        return False, f"{pid} {eid} v{v}: la configuración pedida no es la autorizada (autorizada → pedida): {distintos}", None
    return True, (f"{pid} {eid} v{v} AUTORIZADA (pedido #{aut['issue']}, {aut['fecha']}, {aut['autor']}, "
                  f"huella {h}, {cfg})"), aut


def exigir(m: dict, pedida: dict) -> dict:
    """Corta el proceso si no hay autorización válida. Los registros los baja el flujo de GitHub a un archivo
    (variable CINE_ISSUES); sin ese archivo no se renderiza (p. ej. en una máquina local)."""
    ruta = os.environ.get("CINE_ISSUES", "")
    if not ruta or not Path(ruta).exists():
        raise SystemExit("RENDER BLOQUEADO: no hay registros de autorización (CINE_ISSUES). Los renders sólo corren "
                         "en los flujos de GitHub con la autorización del dueño desde la app (docs/REVISION_Y_AUTORIZACION.md).")
    ok, motivo, aut = verificar(m, json.loads(Path(ruta).read_text()), pedida)
    if not ok:
        raise SystemExit(f"RENDER BLOQUEADO: {motivo}")
    print(f"[autorización] {motivo}", flush=True)
    return aut
