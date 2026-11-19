"""Receta de terminación (ENTRADA del AutoFinisher): qué escena de Godot, qué cuadros, qué calidad, qué correcciones y
qué efectos. Es un JSON versionado en el repositorio (formato «estudio.receta_autofinisher/1»), uno por producción o
por escena. Este módulo la lee, la valida y completa los valores por defecto del estudio (sin bpy).

Campos (los que tienen valor por defecto pueden omitirse):
  produccion            id de la producción o de la prueba (letras, números, guion bajo)       — obligatorio
  titulo                texto libre
  godot                 {proyecto, script, args[], glb, version, recursos[]}  (para construir en Actions)
  escena                {fps, cuadro_inicial, cuadro_final, camara}   cuadros de BLENDER (los archivos salen 1..N)
  render                calidad de Cycles (ver RENDER_POR_DEFECTO)
  luces                 {perfiles: {perfil: {escala, radio, angulo_sol_grados}}, objetos: {nombre: {perfil|escala}}}
  materiales            {vidrios: {material: {rugosidad, ior, color} | null}, vidrio_por_defecto: {...},
                         emisivos: {material_o_prefijo: factor}}
  mundo                 {color: [r, g, b], fuerza}
  efectos               [{receta, ancla, parametros{}}]   SÓLO los pedidos: no se agrega ninguno por su cuenta
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

FORMATO = "estudio.receta_autofinisher/1"

# Calidad del estudio (la misma de la prueba «Casa moderna en tormenta» y de «A la deriva» E02 a 540p).
RENDER_POR_DEFECTO = {
    "motor": "CYCLES", "dispositivo": "CPU", "resolucion": [540, 960], "muestras": 6,
    "muestreo_adaptativo": 0.05, "denoiser": "OPENIMAGEDENOISE", "pases_denoiser": "RGB_ALBEDO_NORMAL",
    "rebotes": {"total": 6, "difusos": 2, "brillantes": 3, "transmision": 4, "transparencia": 8, "volumen": 0},
    "causticas": False, "limite_indirecto": 8.0, "arbol_de_luces": True,
    "volumen": {"paso": 2.0, "pasos_max": 256},
    "color": {"transformacion": "AgX", "aspecto": "AgX - Medium High Contrast"},
    "formato_cuadros": "PNG", "desenfoque_movimiento": False, "datos_persistentes": True,
}
ESCENA_POR_DEFECTO = {"fps": 30, "cuadro_inicial": 0, "cuadro_final": None, "camara": None}


def _mezclar(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _mezclar(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def errores(r: dict) -> list[str]:
    e = []
    if r.get("formato") != FORMATO:
        e.append(f"formato: se esperaba «{FORMATO}»")
    if not re.fullmatch(r"[a-z0-9_]+", str(r.get("produccion", ""))):
        e.append("produccion: falta o tiene caracteres inválidos (sólo minúsculas, números y _)")
    es = r.get("escena", {})
    if not isinstance(es.get("fps"), int) or es["fps"] <= 0:
        e.append("escena.fps: entero positivo")
    if es.get("cuadro_final") is None or es["cuadro_final"] < es.get("cuadro_inicial", 0):
        e.append("escena.cuadro_final: obligatorio y ≥ cuadro_inicial")
    rd = r.get("render", {})
    res = rd.get("resolucion")
    if not (isinstance(res, list) and len(res) == 2 and all(isinstance(x, int) and x > 0 for x in res)):
        e.append("render.resolucion: [ancho, alto] en píxeles")
    if not isinstance(rd.get("muestras"), int) or rd["muestras"] <= 0:
        e.append("render.muestras: entero positivo")
    for i, ef in enumerate(r.get("efectos", [])):
        if not ef.get("receta") or not ef.get("ancla") and ef.get("receta") != "relampago":
            e.append(f"efectos[{i}]: hace falta «receta» y «ancla» (el vacío FX_* de Godot)")
    return e


def completar(r: dict) -> dict:
    out = copy.deepcopy(r)
    out["escena"] = _mezclar(ESCENA_POR_DEFECTO, r.get("escena", {}))
    out["render"] = _mezclar(RENDER_POR_DEFECTO, r.get("render", {}))
    out.setdefault("luces", {})
    out.setdefault("materiales", {})
    out.setdefault("efectos", [])
    return out


def leer(ruta: str | Path) -> dict:
    r = completar(json.loads(Path(ruta).read_text()))
    e = errores(r)
    if e:
        raise ValueError(f"receta {ruta} inválida: " + "; ".join(e))
    return r


def cuadros(r: dict) -> int:
    return r["escena"]["cuadro_final"] - r["escena"]["cuadro_inicial"] + 1
