"""Publicación y catálogo que lee la app Android.

Dónde vive cada cosa (ver docs/ALMACENAMIENTO.md):
- Recetas, manifiestos, código y documentación → Git (este repo).
- Entregables (videos, GLB del visor, .blend, portadas) → GitHub Releases de este repo:
    release "<produccion>"  assets  <escena>_v<k>_{revision.mp4, revision.ogv, portada.jpg, miniatura.jpg,
                                    visor.glb, proyecto.blend, info.json, previa.glb, previa.json}
    release "escenarios"    assets  <escenario>_{visor.glb, portada.jpg, info.json}
    release "catalogo"      asset   catalogo.json  ← lo único que la app consulta para saber si hay novedades
- Decisiones de revisión (aprobar, rechazar, correcciones, volver a renderizar) → Issues creados por la app
  con el token del dueño. Sólo cuentan los del dueño del repo (author_association OWNER).

El catálogo se puede reconstruir siempre desde: manifiestos del repo + lista de releases + issues.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from estudio import config
from estudio import manifiesto as MF

TIPOS_ARCHIVO = {
    "revision.mp4": "mp4", "revision.ogv": "ogv", "portada.jpg": "portada", "miniatura.jpg": "miniatura",
    "visor.glb": "visor", "proyecto.blend": "proyecto", "info.json": "info", "final.mp4": "mp4_final",
    "audio.wav": "audio", "previa.glb": "previa", "previa.json": "previa_datos",
}
DECISIONES = {"APROBAR": "aprobada", "RECHAZAR": "rechazada", "CORREGIR": "correcciones",
              "RENDERIZAR": "renderizando"}


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def nombre_asset(escena: str, version: int, tipo: str) -> str:
    return f"{escena}_v{version}_{tipo}"


def _indexar_assets(releases: list[dict]) -> dict:
    """{tag: {nombre_asset: {url, bytes, sha256, fecha}}}"""
    out = {}
    for r in releases:
        tag = r.get("tag_name")
        d = out.setdefault(tag, {})
        for a in r.get("assets", []):
            dig = (a.get("digest") or "").replace("sha256:", "")
            d[a["name"]] = {"url": a["browser_download_url"], "bytes": a["size"], "sha256": dig,
                            "fecha": a.get("updated_at", "")}
    return out


_BLOQUE_JSON = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def leer_revisiones(issues: list[dict], dueno: str) -> list[dict]:
    """Eventos de revisión válidos (sólo del dueño), en orden cronológico."""
    evs = []
    for it in issues:
        if "pull_request" in it:
            continue
        autor = (it.get("user") or {}).get("login", "")
        if it.get("author_association") != "OWNER" and autor.lower() != dueno.lower():
            continue
        if not it.get("title", "").startswith("[REVISIÓN]"):
            continue
        m = _BLOQUE_JSON.search(it.get("body") or "")
        if not m:
            continue
        try:
            d = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if d.get("decision") not in DECISIONES:
            continue
        d["issue"] = it.get("number")
        d["fecha"] = it.get("created_at", "")
        d["abierto"] = it.get("state") == "open"
        evs.append(d)
    return sorted(evs, key=lambda e: e["fecha"])


def construir_catalogo(releases: list[dict], issues: list[dict], infos: dict[str, dict] | None = None,
                       dueno: str | None = None) -> dict:
    """Arma catalogo.json. `infos`: {"<tag>/<asset info.json>": contenido} ya descargados (opcional)."""
    infos = infos or {}
    dueno = dueno or config.REPO.split("/")[0]
    assets = _indexar_assets(releases)
    revs = leer_revisiones(issues, dueno)
    estado_rev: dict[tuple, dict] = {}
    notas: dict[tuple, list] = {}
    for e in revs:
        k = (e.get("produccion"), e.get("escena"), int(e.get("version", 0)))
        estado_rev[k] = e
        if e.get("nota"):
            notas.setdefault(k, []).append({"fecha": e["fecha"], "decision": e["decision"], "nota": e["nota"],
                                            "issue": e["issue"]})
    producciones = []
    total_bytes = 0
    pendientes = 0
    for pdir in sorted(config.PRODUCCIONES.glob("*/produccion.json")):
        prod = MF.leer(pdir)
        pid = prod["id"]
        pa = assets.get(pid, {})
        escenas = []
        dur_total = 0.0
        for eid in prod.get("escenas", []):
            vers = []
            for v in MF.versiones(pid, eid):
                m = MF.leer(MF.ruta_escena(pid, eid, v))
                archivos = {}
                for sufijo, tipo in TIPOS_ARCHIVO.items():
                    a = pa.get(nombre_asset(eid, v, sufijo))
                    if a:
                        archivos[tipo] = a
                        total_bytes += a["bytes"]
                info = infos.get(f"{pid}/{nombre_asset(eid, v, 'info.json')}", {})
                if "mp4" in archivos:
                    estado = "en_revision"
                else:
                    estado = m.get("estado", "borrador")
                rev = estado_rev.get((pid, eid, v))
                if rev:
                    estado = DECISIONES[rev["decision"]]
                    if rev["decision"] == "RENDERIZAR" and "mp4" in archivos and archivos["mp4"]["fecha"] > rev["fecha"]:
                        estado = "en_revision"
                if m.get("bloqueada"):
                    estado = "aprobada"
                vers.append({
                    "version": v, "estado": estado, "huella": info.get("huella", ""),
                    "calidad": info.get("calidad", m.get("render", {}).get("calidad", "revision")),
                    "resolucion": info.get("resolucion", ""), "fps": info.get("fps", 30),
                    "duracion_s": info.get("duracion_s", m.get("duracion_s")),
                    "fecha": info.get("fecha", ""), "segundos_render": info.get("segundos_render"),
                    "tomas": [{"id": t["id"], "plano": t.get("plano", t["tipo"]), "inicio_s": t["inicio_s"],
                               "duracion_s": t["duracion_s"]} for t in m["tomas"]],
                    "archivos": archivos, "notas": notas.get((pid, eid, v), []),
                })
            if not vers:
                continue
            actual = vers[-1]
            if actual["estado"] == "en_revision":
                pendientes += 1
            dur_total += actual.get("duracion_s") or 0
            m_act = MF.leer(MF.ruta_escena(pid, eid, actual["version"]))
            escenas.append({"id": eid, "numero": m_act.get("numero"), "titulo": m_act.get("titulo"),
                            "guion": m_act.get("guion", ""), "escenario": m_act["escenario"].get("id"),
                            "version_actual": actual["version"], "versiones": vers})
        estados = [e["versiones"][-1]["estado"] for e in escenas]
        if estados and all(s == "aprobada" for s in estados):
            est_prod = "aprobada"
        elif any(s == "renderizando" for s in estados):
            est_prod = "renderizando"
        elif any(s in ("en_revision", "correcciones") for s in estados):
            est_prod = "en_revision"
        else:
            est_prod = "en_produccion"
        portada = next((e["versiones"][-1]["archivos"].get("portada") for e in escenas
                        if e["versiones"][-1]["archivos"].get("portada")), None)
        producciones.append({
            "id": pid, "titulo": prod["titulo"], "genero": prod.get("genero", ""), "sinopsis": prod.get("sinopsis", ""),
            "clase": prod.get("clase", "pelicula"), "creada": prod.get("creada", ""), "estado": est_prod,
            "duracion_s": round(dur_total, 1), "portada": portada, "escenas": escenas,
            "final": pa.get("pelicula_final.mp4"), "final_ogv": pa.get("pelicula_final.ogv"),
        })
    escenarios = []
    ea = assets.get("escenarios", {})
    for edir in sorted(config.ESCENARIOS.glob("*/escenario.json")):
        e = MF.leer(edir)
        escenarios.append({"id": e["id"], "nombre": e.get("nombre", e["id"]), "descripcion": e.get("descripcion", ""),
                           "etiquetas": e.get("etiquetas", []), "anclas": e.get("anclas", []),
                           "visor": ea.get(f"{e['id']}_visor.glb"), "portada": ea.get(f"{e['id']}_portada.jpg")})
    return {
        "formato": 1,
        "generado": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": config.REPO,
        "producciones": sorted(producciones, key=lambda p: p.get("creada", ""), reverse=True),
        "escenarios": escenarios,
        "resumen": {"producciones": len(producciones), "pendientes_revision": pendientes,
                    "bytes_publicados": total_bytes,
                    "renderizando": sum(1 for p in producciones for e in p["escenas"]
                                        if e["versiones"][-1]["estado"] == "renderizando")},
        "politica_retencion": json.loads((config.RAIZ / "config" / "retencion.json").read_text())
        if (config.RAIZ / "config" / "retencion.json").exists() else {},
    }


def plan_limpieza(catalogo: dict, politica: dict, ahora: dt.datetime | None = None) -> list[dict]:
    """Assets TEMPORALES que se pueden borrar según la política. Nunca incluye proyectos, GLB ni manifiestos.

    - Videos de versiones REEMPLAZADAS (hay una versión más nueva) con más de `dias_versiones_viejas` días.
    - Videos de versiones RECHAZADAS con más de `dias_rechazadas` días.
    - Nunca: la versión actual de cada escena, versiones aprobadas, ni tipos fuera de `tipos_temporales`.
    """
    ahora = ahora or dt.datetime.now(dt.timezone.utc)
    temporales = set(politica.get("tipos_temporales", ["mp4", "ogv"]))
    borrar = []
    for p in catalogo["producciones"]:
        for e in p["escenas"]:
            vers = e["versiones"]
            for v in vers[:-1] + ([vers[-1]] if vers[-1]["estado"] == "rechazada" else []):
                if v["estado"] == "aprobada":
                    continue
                dias = politica.get("dias_rechazadas", 14) if v["estado"] == "rechazada" else \
                    politica.get("dias_versiones_viejas", 30)
                for tipo, a in v["archivos"].items():
                    if tipo not in temporales or not a.get("fecha"):
                        continue
                    f = dt.datetime.fromisoformat(a["fecha"].replace("Z", "+00:00"))
                    if (ahora - f).days >= dias:
                        borrar.append({"produccion": p["id"], "escena": e["id"], "version": v["version"],
                                       "tipo": tipo, "url": a["url"], "bytes": a["bytes"]})
    return borrar
