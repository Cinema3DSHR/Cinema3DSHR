"""Escena de TRABAJO: la escena de Blender editable que se guarda (fuera de Git) y se actualiza por componentes.

  config.TRABAJO/<produccion>/<escena>/v<k>/escena.blend   la escena completa, tal como la arma el director
                                          /estado.json   huellas de sus componentes (estudio/componentes.py), qué
                                                         objetos son de cada uno y el contexto de las cámaras
                                                         (anclas y trayectorias muestreadas)

- `construir(m)`: la arma entera UNA vez (las mismas fases del director) y la guarda.
- `actualizar(m)`: compara las huellas de la receta con las guardadas y rehace SÓLO los componentes afectados:
  cámaras (sin tocar personajes ni escenario), personajes (y la utilería y las cámaras que dependen de ellos),
  ajustes de render. Si cambió la base (tiempo, escenario, vehículos, pelota) avisa y rehace todo (no inventa).
- `exportar_previa(m, salida)`: GLB + JSON del visor desde la escena de trabajo, en una copia en memoria: la
  previsualización aliviana materiales y mallas, y eso NUNCA se guarda en la escena de trabajo.

La receta (escena.json) sigue siendo la fuente: la escena de trabajo es un derivado reconstruible. Nada de esto
renderiza.
"""
from __future__ import annotations

import contextlib
import json
import time
from pathlib import Path

import bpy
from mathutils import Vector

from estudio import componentes as CO
from estudio import config
from estudio.blender import camaras as C
from estudio.blender import director as D
from estudio.blender import kit as K
from estudio.blender import personajes as P

ETIQUETA = "cine_componente"


def carpeta(m: dict) -> Path:
    return config.TRABAJO / m["produccion"] / m["id"].split("-")[-1] / f"v{m['version']}"


def _leer_estado(d: Path) -> dict | None:
    p = d / "estado.json"
    return json.loads(p.read_text()) if p.exists() else None


@contextlib.contextmanager
def _marcar(cid: str, registro: dict):
    """Todo objeto que se cree adentro queda etiquetado como del componente cid."""
    antes = set(bpy.data.objects.keys())
    yield
    nuevos = [o for o in bpy.data.objects if o.name not in antes]
    for o in nuevos:
        o[ETIQUETA] = cid
    registro.setdefault(cid, []).extend(o.name for o in nuevos)


def _borrar_componente(cid: str):
    obs = [o for o in bpy.data.objects if o.get(ETIQUETA) == cid]
    for o in obs:
        bpy.data.objects.remove(o, do_unlink=True)
    for c in [c for c in bpy.data.collections if not c.objects and not c.children and c.get(ETIQUETA) == cid]:
        bpy.data.collections.remove(c)
    return len(obs)


def _reiniciar_caches():
    """Los módulos guardan referencias (materiales, bibliotecas de clips, retargets) que dejan de existir al purgar o
    al abrir otra escena: se vacían antes de rehacer un componente."""
    from estudio.blender import flores as FL
    K.reiniciar_materiales()
    P.reiniciar()
    FL.reiniciar()
    P._RAICES.clear()


def _purgar():
    try:
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except Exception:                                    # noqa: BLE001 (versiones viejas de bpy)
        pass


# ------------------------------------------------------------------------------------------------ contexto ↔ JSON
def _tray_a_json(tray: dict) -> list:
    fs = sorted(tray)
    return [fs[0], [[round(c, 5) for c in tray[f][0]] + [round(float(tray[f][1]), 6), round(float(tray[f][2]), 4)]
                    for f in fs]]


def _tray_de_json(j: list) -> dict:
    f0, filas = j
    return {f0 + i: (Vector(r[:3]), r[3], r[4]) for i, r in enumerate(filas)}


def _ctx_a_json(ctx, nombres_obj: dict) -> dict:
    mov = {}
    for mid, mv in ctx.moviles.items():
        mov[mid] = {"tray": _tray_a_json(mv["tray"]), "anclas": {k: list(v) for k, v in mv["anclas"].items()},
                    "objeto": nombres_obj.get(mid)}
    return {"anclas": {k: list(v) for k, v in ctx.anclas.items()}, "fps": ctx.fps, "mapa": ctx.mapa, "moviles": mov}


def _ctx_de_json(j: dict):
    ctx = C.Contexto({k: tuple(v) for k, v in j["anclas"].items()}, j["fps"])
    ctx.mapa = j.get("mapa")
    for mid, mv in j["moviles"].items():
        ctx.moviles[mid] = {"tray": _tray_de_json(mv["tray"]), "anclas": {k: tuple(v) for k, v in mv["anclas"].items()}}
        if mv.get("objeto") and bpy.data.objects.get(mv["objeto"]):
            ctx.moviles[mid]["objeto"] = bpy.data.objects[mv["objeto"]]
    return ctx


def _pj_a_json(pj: dict) -> dict:
    return {"raiz": pj["raiz"].name, "armadura": pj["armadura"].name, "malla": pj["malla"].name if pj.get("malla") else None,
            "arma": pj["arma"].name if pj.get("arma") else None,
            "info": {k: v for k, v in pj["info"].items() if isinstance(v, (str, int, float, bool, list, tuple))},
            "tramos": [{"f0": t["f0"], "fin": t["fin"], "rumbo": t["rumbo"]} for t in pj["tramos"]], "fin": pj.get("fin")}


def _pj_de_json(j: dict) -> dict:
    ob = bpy.data.objects
    return {"raiz": ob[j["raiz"]], "armadura": ob[j["armadura"]], "malla": ob.get(j["malla"]) if j.get("malla") else None,
            "arma": ob.get(j["arma"]) if j.get("arma") else None, "info": dict(j["info"]), "tramos": j["tramos"],
            "fin": j.get("fin")}


def _tomas_de(estado: dict, m: dict) -> list:
    specs = {t["id"]: t for t in m["tomas"]}
    return [{"camara": bpy.data.objects[t["camara"]], "frame_inicio": t["f0"], "frame_fin": t["f1"], "spec": specs[t["id"]]}
            for t in estado["tomas"]]


def _guardar(d: Path, m: dict, ruta_receta: str, registro: dict, ctx, pjs: dict, tomas: list, frames: int,
             tiempos: dict):
    d.mkdir(parents=True, exist_ok=True)
    comps = CO.componentes(m)
    nombres_obj = {mid: mv["objeto"].name for mid, mv in ctx.moviles.items() if mv.get("objeto") is not None}
    estado = {"formato": "estudio.trabajo/1", "receta": ruta_receta, "huella_receta": None,
              "huellas": {c: v["huella"] for c, v in comps.items()},
              "codigo_sha": CO.codigo_sha(m),
              "objetos": {c: sorted(set(v)) for c, v in registro.items()},
              "contexto": _ctx_a_json(ctx, nombres_obj),
              "personajes": {pid: _pj_a_json(pj) for pid, pj in pjs.items()},
              "tomas": [{"id": t["spec"]["id"], "camara": t["camara"].name, "f0": t["frame_inicio"], "f1": t["frame_fin"]}
                        for t in tomas],
              "frames_pelicula": frames, "tiempos_s": tiempos,
              "guardado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    from estudio import manifiesto as MF
    estado["huella_receta"] = MF.huella(m)
    bpy.ops.wm.save_as_mainfile(filepath=str(d / "escena.blend"), compress=True)
    (d / "estado.json").write_text(json.dumps(estado, ensure_ascii=False) + "\n")
    return estado


# ------------------------------------------------------------------------------------------------ construir
def construir(m: dict, ruta_receta: str = "", calidad: str | None = None) -> dict:
    """Arma la escena entera (fases del director, cada componente etiquetado) y la guarda como escena de trabajo."""
    from estudio import recursos as R
    R.exigir(m)
    calidad = calidad or m.get("render", {}).get("calidad", "revision")
    t, reg = {}, {}
    t0 = time.time()
    with _marcar("escenario", reg):
        s, fps, mod, info, ctx = D.fase_escenario(m)
    for v in m.get("vehiculos", []):
        with _marcar(f"vehiculo:{v['id']}", reg):
            D.fase_vehiculos({**m, "vehiculos": [v]}, ctx, fps)
    t["escenario"] = round(time.time() - t0, 1)
    t0 = time.time()

    def envolver(pid, crear):
        with _marcar(f"personaje:{pid}", reg):
            return crear()
    pjs = D.fase_personajes(m, s, info, fps, al_crear=envolver)
    t["personajes"] = round(time.time() - t0, 1)
    t0 = time.time()
    with _marcar("despues", reg):
        D.fase_despues(mod, info, pjs, ctx, m, fps)
    dur_f = int(round(m["duracion_s"] * fps))
    D.fase_muestreo(m, pjs, ctx, dur_f)
    if m.get("pelota"):
        with _marcar("pelota", reg):
            D._pelota(m["pelota"], pjs, ctx, fps, dur_f)
    t["despues_y_muestreo"] = round(time.time() - t0, 1)
    t0 = time.time()
    tomas = []
    for sp in m["tomas"]:
        with _marcar(f"camara:{sp['id']}", reg):
            tomas.append(C.crear_toma(sp, ctx))
    frames = D.fase_cierre(m, s, tomas, ctx, calidad)
    t["camaras"] = round(time.time() - t0, 1)
    estado = _guardar(carpeta(m), m, ruta_receta, reg, ctx, pjs, tomas, frames, t)
    return {"escena": s, "tomas": tomas, "contexto": ctx, "info": info, "personajes": pjs, "frames_pelicula": frames,
            "manifiesto": m, "estado": estado}


# ------------------------------------------------------------------------------------------------ abrir
def abrir(m: dict) -> dict:
    """Abre la escena de trabajo guardada y reconstruye lo que necesitan las cámaras y el exportador (sin rehacer)."""
    d = carpeta(m)
    estado = _leer_estado(d)
    if not estado:
        raise FileNotFoundError(f"No hay escena de trabajo en {d}: primero `python -m estudio trabajo construir`")
    bpy.ops.wm.open_mainfile(filepath=str(d / "escena.blend"))
    _reiniciar_caches()
    ctx = _ctx_de_json(estado["contexto"])
    pjs = {pid: _pj_de_json(j) for pid, j in estado["personajes"].items()}
    return {"escena": bpy.context.scene, "tomas": _tomas_de(estado, m), "contexto": ctx,
            "info": {"anclas": ctx.anclas}, "personajes": pjs, "frames_pelicula": estado["frames_pelicula"],
            "manifiesto": m, "estado": estado}


# ------------------------------------------------------------------------------------------------ actualizar
def heredar(m: dict) -> Path | None:
    """Versión nueva sin escena de trabajo: copia la de la versión anterior más cercana que tenga una (la v1 no se
    toca: es una copia). Así una corrección de cámara en v2 rehace sólo esa cámara."""
    import shutil
    d = carpeta(m)
    if (d / "estado.json").exists():
        return None
    for k in range(int(m["version"]) - 1, 0, -1):
        prev = d.parent / f"v{k}"
        if (prev / "estado.json").exists() and (prev / "escena.blend").exists():
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy2(prev / "escena.blend", d / "escena.blend")
            shutil.copy2(prev / "estado.json", d / "estado.json")
            (d / "heredada_de.txt").write_text(f"v{k}\n")
            return prev
    return None


def reestampar(m: dict, ids: list[str], motivo: str, archivos_cambiados: list[str]) -> dict:
    """Recalcula las huellas guardadas de `ids` SIN reconstruir, sólo si ninguno de los archivos que cambiaron desde que
    se guardó la escena forma parte del código de esos componentes y su porción de la receta es la misma (p. ej. cambió
    la regla de huellas, no lo que arma el componente). Deja constancia en el estado."""
    d = carpeta(m)
    estado = _leer_estado(d)
    comps = CO.componentes(m)
    usados = CO.codigo_por_componente(m)
    for c in ids:
        toca = sorted(set(archivos_cambiados) & set(usados.get(c, [])))
        if toca:
            raise ValueError(f"{c} usa {toca}, que cambió: hay que reconstruirlo")
    antes = {c: estado["huellas"].get(c) for c in ids}
    for c in ids:
        estado["huellas"][c] = comps[c]["huella"]
    estado.setdefault("reestampados", []).append({"ids": ids, "motivo": motivo, "archivos_cambiados": archivos_cambiados,
                                                  "antes": antes, "fecha": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    (d / "estado.json").write_text(json.dumps(estado, ensure_ascii=False) + "\n")
    return {c: (antes[c], estado["huellas"][c]) for c in ids}


def plan(m: dict) -> dict:
    """Qué habría que rehacer (sin abrir Blender): compara la receta con el estado de la escena de trabajo."""
    heredar(m)
    estado = _leer_estado(carpeta(m))
    if not estado:
        return {"sin_trabajo": True, "completa": True, "afectados": ["(no hay escena de trabajo)"]}
    return CO.afectados(estado["huellas"], CO.componentes(m))


def actualizar(m: dict, ruta_receta: str = "", calidad: str | None = None) -> dict:
    """Rehace sólo lo afectado. Devuelve {"rehecho": [...], "completa": bool, "tiempos_s": {...}}."""
    from estudio import recursos as R
    R.exigir(m)
    calidad = calidad or m.get("render", {}).get("calidad", "revision")
    dif = plan(m)
    if dif.get("completa"):
        t0 = time.time()
        res = construir(m, ruta_receta, calidad)
        return {"rehecho": ["TODO"], "completa": True, "motivo": dif, "tiempos_s": {"total": round(time.time() - t0, 1)},
                "res": res}
    afect = set(dif["afectados"])
    if not afect:
        return {"rehecho": [], "completa": False, "tiempos_s": {}}
    res = abrir(m)
    estado, s, ctx = res["estado"], res["escena"], res["contexto"]
    fps = m.get("render", {}).get("fps", 30)
    s.render.fps = fps                       # antes de importar clips (como el director)
    reg = {c: list(v) for c, v in estado["objetos"].items()}
    t = {}
    pjs = res["personajes"]
    rehacer_pj = sorted(c.split(":", 1)[1] for c in afect if c.startswith("personaje:"))
    mod = D._modulo_escenario(m["escenario"]["generador"])
    t0 = time.time()
    if rehacer_pj or "despues" in afect:
        # lo de «después» (utilería) se apoya en los personajes: se saca antes y se vuelve a armar después
        _borrar_componente("despues")
        reg.pop("despues", None)
    if rehacer_pj:
        for pid in rehacer_pj:
            _borrar_componente(f"personaje:{pid}")
            reg.pop(f"personaje:{pid}", None)
            pjs.pop(pid, None)
        _purgar()
        _reiniciar_caches()

        def envolver(pid, crear):
            with _marcar(f"personaje:{pid}", reg):
                return crear()
        pjs.update(D.fase_personajes(m, s, {"personajes": []}, fps, solo=set(rehacer_pj), al_crear=envolver))
    t["personajes"] = round(time.time() - t0, 1)
    t0 = time.time()
    if (rehacer_pj or "despues" in afect) and hasattr(mod, "despues_personajes"):
        info = {"anclas": ctx.anclas, "animables": {}, "personajes": []}
        with _marcar("despues", reg):
            D.fase_despues(mod, info, pjs, ctx, m, fps)
    sg = D.seguidos(m)
    dur_f = int(round(m["duracion_s"] * fps))
    for pid in rehacer_pj:
        if pid in sg:
            ctx.moviles[pid] = {"tray": D._muestrear_personaje(pjs[pid], dur_f), "anclas": D.ANCLAS_PERSONAJE}
    t["despues_y_muestreo"] = round(time.time() - t0, 1)
    # cámaras: se borran las afectadas y las que ya no están en la receta; se crean las nuevas
    t0 = time.time()
    ids_receta = [sp["id"] for sp in m["tomas"]]
    viejas = {x["id"]: x for x in estado["tomas"]}
    rehacer_cam = [i for i in ids_receta if f"camara:{i}" in afect or i not in viejas]
    for i in list(viejas):
        if i not in ids_receta or i in rehacer_cam:
            _borrar_componente(f"camara:{i}")
            reg.pop(f"camara:{i}", None)
            for mk in [mk for mk in s.timeline_markers if mk.name == i]:
                s.timeline_markers.remove(mk)
    nuevas = {}
    for sp in m["tomas"]:
        if sp["id"] in rehacer_cam:
            with _marcar(f"camara:{sp['id']}", reg):
                nuevas[sp["id"]] = C.crear_toma(sp, ctx)
    tomas = []
    for sp in m["tomas"]:
        if sp["id"] in nuevas:
            tomas.append(nuevas[sp["id"]])
        else:
            v = viejas[sp["id"]]
            tomas.append({"camara": bpy.data.objects[v["camara"]], "frame_inicio": v["f0"], "frame_fin": v["f1"], "spec": sp})
    frames = D.fase_cierre(m, s, tomas, ctx, calidad)        # rango, cámara activa y ajustes de render (barato)
    t["camaras"] = round(time.time() - t0, 1)
    _purgar()
    estado_n = _guardar(carpeta(m), m, ruta_receta or estado.get("receta", ""), reg, ctx, pjs, tomas, frames, t)
    return {"rehecho": sorted(afect), "completa": False, "camaras": rehacer_cam, "personajes": rehacer_pj,
            "tiempos_s": t, "res": {**res, "tomas": tomas, "personajes": pjs, "frames_pelicula": frames,
                                    "estado": estado_n}}


# ------------------------------------------------------------------------------------------------ previsualización
def exportar_previa(m: dict, salida: Path, res: dict | None = None) -> dict:
    """GLB + JSON del visor desde la escena de trabajo. La exportación aliviana materiales y mallas EN MEMORIA: la
    escena de trabajo ya está guardada antes y no se vuelve a guardar después."""
    from estudio import proteccion as PR
    from estudio.blender import previa as PV
    res = res or abrir(m)
    eid = m["id"].split("-")[-1]
    salida = Path(salida)
    glb, js = salida / f"{eid}_v{m['version']}_previa.glb", salida / f"{eid}_v{m['version']}_previa.json"
    reg = PR.registro(Path(config.RAIZ / res["estado"].get("receta", ""))) if res["estado"].get("receta") else None
    for f in (glb, js):
        if reg and f.exists() and any(d["sha256"] == PR.sha256(f) for d in reg.get("derivados", [])):
            raise PermissionError(f"{f} es un archivo ENTREGADO: no se sobrescribe (elegí otra carpeta de salida)")
    return PV.exportar(res, m, glb, js)
