"""Datos de dirección que manda el EDITOR 3D de la app y su aplicación a la escena de producción (sin Blender).

producciones/<produccion>/director/
    cameras/camera_NNN.json   cámaras colocadas con COLOCAR CÁMARA (coordenadas de Blender, ver blender/camara_director.py)
    markers.json              marcadores de tiempo con notas (instante, cuadro, personaje, clip que estaba reproduciendo)
    director_notes.json       mensajes del director (texto + contexto: tiempo, toma, personaje, cámara en ese momento)

`aplicar_camaras` crea tomas de tipo "director" con los datos EXACTOS del archivo (sin adivinar a partir de capturas)
y recorta las tomas existentes que se superponen en el tiempo. Siempre sobre una versión NUEVA de la escena.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
from estudio import config
from estudio import manifiesto as MF

CAMPOS_CAMARA = ("formato", "camera_id", "name", "position", "rotation", "rotation_mode", "quaternion", "forward", "up",
                 "fov", "fov_v_deg", "fov_h_deg", "lens_mm", "sensor_mm", "aspect", "resolution", "time_start",
                 "time_end", "shot", "transition", "notes", "version_escena", "huella_escena", "created")


def carpeta(prod: str) -> Path:
    return config.PRODUCCIONES / prod / "director"


def leer(prod: str) -> dict:
    d = carpeta(prod)
    cams = [json.loads(p.read_text()) for p in sorted((d / "cameras").glob("camera_*.json"))] if (d / "cameras").exists() else []
    leer_json = lambda n, x: json.loads((d / n).read_text()) if (d / n).exists() else x
    return {"camaras": cams, "marcadores": leer_json("markers.json", []), "notas": leer_json("director_notes.json", [])}


def camara(prod: str, cid: str) -> dict:
    return json.loads((carpeta(prod) / "cameras" / f"{cid}.json").read_text())


def _toma(cam: dict, ini: float, fin: float, previa: dict | None = None) -> dict:
    datos = {k: cam[k] for k in CAMPOS_CAMARA if k in cam}
    t = {"id": f"d_{cam['camera_id']}", "tipo": "director",
         "plano": f"cámara del director «{cam.get('name', cam['camera_id'])}»" + (f": {cam['notes']}" if cam.get("notes") else ""),
         "inicio_s": round(ini, 4), "duracion_s": round(fin - ini, 4), "camara": datos, "luz_relleno": 0}
    if previa is not None:      # transición suave: viaja desde la cámara anterior del director hasta ésta
        t["camara"], t["hasta"] = {k: previa[k] for k in CAMPOS_CAMARA if k in previa}, datos
    return t


def aplicar_camaras(m: dict, camaras: list[dict]) -> dict:
    """Devuelve una copia de la escena con las cámaras del director en sus tramos de tiempo."""
    m = copy.deepcopy(m)
    tomas = sorted(m["tomas"], key=lambda t: t["inicio_s"])
    previa = None
    for cam in sorted(camaras, key=lambda c: float(c["time_start"])):
        ini = max(0.0, float(cam["time_start"]))
        fin = min(float(m["duracion_s"]), float(cam["time_end"]))
        if fin - ini < 1 / 30:
            raise ValueError(f"{cam['camera_id']}: el tramo {ini}–{fin} s es demasiado corto")
        nuevas = []
        for t in tomas:
            a, b = t["inicio_s"], t["inicio_s"] + t["duracion_s"]
            if b <= ini or a >= fin:
                nuevas.append(t)
                continue
            if a < ini:                 # queda la parte de antes
                nuevas.append({**t, "duracion_s": round(ini - a, 4)})
            if b > fin:                 # y la de después (con otro id)
                nuevas.append({**t, "id": t["id"] + "_b", "inicio_s": round(fin, 4), "duracion_s": round(b - fin, 4)})
        suave = str(cam.get("transition", "corte")).startswith("suave") and previa is not None
        nuevas.append(_toma(cam, ini, fin, previa if suave else None))
        tomas = sorted(nuevas, key=lambda t: t["inicio_s"])
        previa = cam
    m["tomas"] = tomas
    return m


def nueva_version_con_camaras(prod: str, escena: str, ids: list[str], motivo: str = "") -> Path:
    """Versión nueva de la escena con las cámaras del director indicadas. No toca las versiones anteriores."""
    ruta = MF.nueva_version(prod, escena, motivo or f"cámaras del director: {', '.join(ids)}")
    m = MF.leer(ruta)
    m2 = aplicar_camaras(m, [camara(prod, i) for i in ids])
    err = MF.validar(m2)
    if err:
        raise ValueError(f"la escena con las cámaras del director no valida: {err}")
    MF.escribir(ruta, m2)
    return ruta


def resumen(prod: str) -> str:
    d = leer(prod)
    out = [f"Dirección de {prod}: {len(d['camaras'])} cámaras, {len(d['marcadores'])} marcadores, {len(d['notas'])} notas"]
    for c in d["camaras"]:
        p = c["position"]
        out.append(f"  {c['camera_id']} «{c.get('name', '')}» toma={c.get('shot') or '-'} {c.get('time_start')}–{c.get('time_end')} s "
                   f"pos=({p['x']:.2f}, {p['y']:.2f}, {p['z']:.2f}) lente={c.get('lens_mm')} mm v{c.get('version_escena')}  {c.get('notes', '')}")
    for mk in d["marcadores"]:
        ctx = mk.get("contexto", {})
        out.append(f"  📍 {mk.get('tiempo_s')} s (f {mk.get('frame')}) {ctx.get('personaje', '')} "
                   f"{(ctx.get('animacion') or {}).get('clip', '')}: {mk.get('nota', '')}")
    for n in d["notas"]:
        ctx = n.get("contexto", {})
        out.append(f"  💬 {ctx.get('tiempo_s', '')} s {ctx.get('personaje', '')}: {n.get('texto', '')}")
    return "\n".join(out)
