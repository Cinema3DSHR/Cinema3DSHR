"""Componentes de una escena: la receta (escena.json) dividida en piezas con identidad, dependencias y huella, para
reconstruir SÓLO lo que cambió (escena de trabajo, `estudio/blender/trabajo.py`). Sin bpy.

La receta no cambia de formato: cada componente es una porción de ella más el código y los recursos que la arman.

  tiempo           duracion_s, mapa_tiempo, fps                      → si cambia, todo se rehace
  escenario        generador + parámetros (menos los «de después») + eventos del escenario + su código y los audios
                   que leen los eventos                              → reconstrucción completa (es la base)
  vehiculo:<id>    un vehículo de la receta                          → depende del escenario (anclas)
  personaje:<id>   modelo, acciones (clips), cara (expresiones, habla, miradas), perfil + audios y marcas de tiempo
                   de sus líneas + el código de personajes          → se rehace sólo ese personaje
  despues          lo que el escenario arma con los personajes ya hechos (`despues_personajes`, p. ej. la utilería de
                   mano en mano): parámetros listados en PARAMETROS_DESPUES del generador → depende del escenario y de
                   todos los personajes
  pelota           la pelota con física                              → depende de los personajes
  camara:<toma>    una toma (tipo, posición, objetivo, lente, tiempos…) → depende del tiempo, del escenario (anclas) y
                   de los personajes/vehículos que sigue o mira
  render           calidad, vertical, muestras, exposición…          → sólo ajustes de render (no toca la escena)
  sonido           mezcla de audio (fuera de Blender)                → no reconstruye nada en Blender

huella = sha256 de (porción de receta en JSON canónico + bytes del código que la arma + huella de sus recursos).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from estudio import config

FORMATO = "estudio.componentes/1"
CODIGO_PERSONAJES = ("estudio/blender/personajes.py", "estudio/blender/importar.py", "estudio/blender/kit.py")
CODIGO_CAMARAS = ("estudio/blender/camaras.py", "estudio/blender/camara_director.py")
# claves de la receta que no definen la imagen
METADATOS = {"tipo", "id", "produccion", "numero", "version", "titulo", "guion", "estado", "bloqueada", "salidas",
             "historial", "notas", "notas_puesta", "posiciones", "huella_v"}


def _canon(x) -> bytes:
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def _codigo(archivos) -> list[str]:
    """Archivos de código + los módulos del estudio que importan. Los imports del nivel del módulo se siguen
    (recursivo); los que están adentro de una función cuentan como archivo directo, sin seguir lo que importan ellos
    (si no, cualquier escenario «dependía» de todo el estudio a través de stickman → personajes)."""
    vistos, cola = {}, [(a, True) for a in archivos]          # archivo → ya se siguieron sus imports
    while cola:
        rel, seguir = cola.pop()
        p = config.RAIZ / rel
        if not p.exists() or (rel in vistos and (vistos[rel] or not seguir)):
            continue
        vistos[rel] = seguir
        if not rel.endswith(".py") or not seguir:
            continue
        txt = p.read_text()
        for sangria, mod in re.findall(r"^(\s*)from (estudio(?:\.\w+)+) import", txt, re.M) + \
                re.findall(r"^(\s*)import (estudio(?:\.\w+)+)", txt, re.M):
            cola.append((mod.replace(".", "/") + ".py", not sangria))
        for sangria, paquete, nombres in re.findall(r"^(\s*)from (estudio(?:\.\w+)*) import ([^\n(]+)", txt, re.M):
            for n in nombres.split(","):
                n = n.strip().split(" as ")[0]
                cola.append((f"{paquete.replace('.', '/')}/{n}.py", not sangria))
    return sorted(vistos)


def _huella_archivos(rels) -> str:
    h = hashlib.sha256()
    for rel in sorted(set(rels)):
        p = config.RAIZ / rel
        h.update(rel.encode())
        h.update(p.read_bytes() if p.exists() else b"<falta>")
    return h.hexdigest()


def _huella_recurso(ruta: str) -> str:
    """Audios y marcas de tiempo del repo: contenido. Recursos externos («fuente:ruta», FBX/GLB pesados): ruta +
    tamaño (se clonan de nuevo en cada máquina: la fecha no sirve)."""
    if not ruta:
        return ""
    if ":" in ruta.split("/")[0] and not ruta.startswith("/"):
        try:
            p = config.resolver(ruta)
            return f"{ruta}|{p.stat().st_size}"
        except (FileNotFoundError, ValueError):
            return f"{ruta}|<falta>"
    p = config.ruta_recurso(ruta)
    if not p.exists():
        return f"{ruta}|<falta>"
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _audios_de(x) -> list[str]:
    """Rutas de audio / marcas de tiempo que aparezcan en cualquier lugar de x (claves audio, alineacion)."""
    out = []
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ("audio", "alineacion") and isinstance(v, str):
                out.append(v)
            else:
                out += _audios_de(v)
    elif isinstance(x, list):
        for v in x:
            out += _audios_de(v)
    return out


def _moviles_de_toma(t: dict) -> set[str]:
    m = {t.get("movil")} if t.get("movil") else set()
    for k in ("objetivo", "objetivo_final", "desde", "hasta", "centro", "foco"):
        v = t.get(k)
        if isinstance(v, dict) and v.get("movil"):
            m.add(v["movil"])
    return m


def _generador(m: dict) -> tuple[str, tuple]:
    gen = m["escenario"]["generador"]
    rel = f"estudio/escenarios/{gen}.py"
    txt = (config.RAIZ / rel).read_text() if (config.RAIZ / rel).exists() else ""
    desp = ()
    mt = re.search(r"^PARAMETROS_DESPUES\s*=\s*(\([^)]*\)|\[[^\]]*\])", txt, re.M)
    if mt:
        import ast
        desp = tuple(ast.literal_eval(mt.group(1)))
    return rel, desp if "def despues_personajes" in txt else None


def componentes(m: dict) -> dict:
    """{id: {"id", "tipo", "deps": [...], "huella"}} de la receta m."""
    out = {}

    def poner(cid, tipo, porcion, deps=(), codigo=(), recursos=(), codigo_plano=()):
        """codigo: archivos + lo que importan (recursivo); codigo_plano: sólo ese archivo (el director importa todo
        el estudio, pero el escenario usa sólo su fase)."""
        h = hashlib.sha256()
        h.update(_canon(porcion))
        h.update(_huella_archivos(_codigo(codigo) + list(codigo_plano)).encode())
        for r in sorted(set(recursos)):
            h.update(_huella_recurso(r).encode())
        out[cid] = {"id": cid, "tipo": tipo, "deps": sorted(set(deps)), "huella": h.hexdigest()[:16]}

    fps = m.get("render", {}).get("fps", 30)
    poner("tiempo", "tiempo", {"duracion_s": m["duracion_s"], "mapa_tiempo": m.get("mapa_tiempo"), "fps": fps})
    gen_rel, despues = _generador(m)
    params = dict(m["escenario"].get("parametros", {}))
    params_desp = {k: params.pop(k) for k in (despues or ()) if k in params}
    esc = {**m["escenario"], "parametros": params}
    poner("escenario", "escenario", {"escenario": esc, "eventos": m.get("eventos", [])}, ["tiempo"],
          [gen_rel], _audios_de(m.get("eventos", [])), codigo_plano=["estudio/blender/director.py"])
    for v in m.get("vehiculos", []):
        poner(f"vehiculo:{v['id']}", "vehiculo", v, ["tiempo", "escenario"], ["estudio/blender/vehiculos.py"])
    for pj in m.get("personajes", []):
        deps = ["tiempo"] + (["escenario"] if pj.get("sobre") else [])
        clips = [a["clip"] for a in pj.get("acciones", []) if ":" in str(a.get("clip", ""))]
        poner(f"personaje:{pj['id']}", "personaje", pj, deps, CODIGO_PERSONAJES, _audios_de(pj) + clips)
    ids_pj = [f"personaje:{p['id']}" for p in m.get("personajes", [])]
    if despues is not None:
        poner("despues", "despues", params_desp, ["tiempo", "escenario"] + ids_pj, [gen_rel])
    if m.get("pelota"):
        poner("pelota", "pelota", m["pelota"], ["tiempo"] + ids_pj, ["estudio/blender/pelota.py"])
    vehs = {v["id"] for v in m.get("vehiculos", [])}
    pjs = {p["id"] for p in m.get("personajes", [])}
    for t in m.get("tomas", []):
        deps = ["tiempo", "escenario"]
        for mv in _moviles_de_toma(t):
            deps.append(f"personaje:{mv}" if mv in pjs else f"vehiculo:{mv}" if mv in vehs else "escenario")
            if mv in pjs and "despues" in out:
                deps.append("despues")          # el escenario puede mover a un personaje después (subirlo a algo)
        poner(f"camara:{t['id']}", "camara", t, deps, CODIGO_CAMARAS)
    poner("render", "render", {k: v for k, v in m.get("render", {}).items() if k != "fps"}, ["tiempo"])
    son = m.get("sonido", {})
    poner("sonido", "sonido", son, ["tiempo"], ["estudio/audio/__init__.py"], _audios_de(son))
    resto = {k: v for k, v in m.items() if k not in METADATOS and k not in (
        "duracion_s", "mapa_tiempo", "escenario", "eventos", "vehiculos", "personajes", "pelota", "tomas", "render",
        "sonido")}
    if resto:                                   # claves que este módulo no conoce: cuentan como parte del escenario
        poner("otros", "otros", resto, ["tiempo"])
    return out


def codigo_por_componente(m: dict) -> dict:
    """{componente: [archivos de código que lo arman]} (la misma regla que usan las huellas)."""
    gen_rel, despues = _generador(m)
    out = {"escenario": _codigo([gen_rel]) + ["estudio/blender/director.py"]}
    for p in m.get("personajes", []):
        out[f"personaje:{p['id']}"] = _codigo(list(CODIGO_PERSONAJES))
    if despues is not None:
        out["despues"] = _codigo([gen_rel])
    for t in m.get("tomas", []):
        out[f"camara:{t['id']}"] = _codigo(list(CODIGO_CAMARAS))
    return out


def codigo_sha(m: dict) -> dict:
    """sha256 (16) de cada archivo de código que usa la escena: queda en el estado de la escena de trabajo."""
    archivos = sorted({a for v in codigo_por_componente(m).values() for a in v})
    return {a: hashlib.sha256((config.RAIZ / a).read_bytes()).hexdigest()[:16] for a in archivos if (config.RAIZ / a).exists()}


def afectados(previo: dict, actual: dict) -> dict:
    """Qué cambió entre dos juegos de huellas ({id: huella}) y qué depende de eso.
    Devuelve {"cambiados", "nuevos", "quitados", "afectados" (todo lo que hay que rehacer), "completa": bool}."""
    cambiados = {c for c in actual if c in previo and previo[c] != actual[c]["huella"]}
    nuevos = {c for c in actual if c not in previo}
    quitados = {c for c in previo if c not in actual}
    sucios = set(cambiados | nuevos)
    hubo = True
    while hubo:
        hubo = False
        for c, d in actual.items():
            if c not in sucios and any(x in sucios for x in d["deps"]):
                sucios.add(c)
                hubo = True
    base = {"tiempo", "escenario", "otros", "pelota"} | {c for c in actual if c.startswith("vehiculo:")}
    completa = bool(sucios & base) or any(q in base or q.startswith(("personaje:", "vehiculo:")) for q in quitados)
    return {"cambiados": sorted(cambiados), "nuevos": sorted(nuevos), "quitados": sorted(quitados),
            "afectados": sorted(sucios), "completa": completa}


def resumen(m: dict, previo: dict | None = None) -> str:
    comps = componentes(m)
    lin = [f"{len(comps)} componentes de {m['id']} v{m['version']}:"]
    dif = afectados(previo or {}, comps) if previo is not None else None
    for c, d in comps.items():
        marca = ""
        if dif is not None:
            marca = " ← CAMBIÓ" if c in dif["cambiados"] or c in dif["nuevos"] else (" ← afectado" if c in dif["afectados"] else "")
        lin.append(f"  {c:32s} {d['huella']}  deps: {', '.join(d['deps']) or '—'}{marca}")
    if dif is not None:
        lin.append(f"Rehacer: {'TODO (cambió la base: tiempo/escenario/vehículos)' if dif['completa'] else ', '.join(dif['afectados']) or 'nada'}")
    return "\n".join(lin)
