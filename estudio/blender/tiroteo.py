"""Efectos del tiroteo (todo por visibilidad y claves por cuadro: barato y reproducible, sin simulación).

Cada tiro {"tirador": id, "t": s (tiempo de la escena), "a": [x, y, z] (adonde pega), "impacto": "chispas"|"sangre"|
"nada", "normal": [nx, ny, nz] opcional}: trazadora de la boca del cañón al blanco (2 cuadros), casquillo que sale
despedido a la derecha del arma, y en el blanco chispas (metal/madera) o una nube chica de sangre estilizada (gotas
rojas que caen, sin gore). La boca del cañón sale del arma real en ese cuadro (el arma sigue la mano del personaje).
"""
from __future__ import annotations
import math
import random

import bpy
from mathutils import Vector

from estudio.blender import kit as K


def _mats():
    return {
        "trazadora": K.material("trazadora", (1.0, 0.75, 0.35), 0.3, emision=(1.0, 0.72, 0.3), fuerza=60.0),
        "chispa": K.material("chispa", (1.0, 0.8, 0.4), 0.3, emision=(1.0, 0.75, 0.35), fuerza=90.0),
        "sangre": K.material("sangre_estilizada", (0.42, 0.015, 0.02), 0.35),
        "casquillo": K.material("casquillo_laton", (0.75, 0.55, 0.18), 0.3, 1.0),
        "polvo": K.material("polvo_impacto", (0.35, 0.32, 0.28), 0.9, alfa=0.55, mezcla="BLENDED"),
    }


def _ocultar_salvo(ob, f0: int, f1: int):
    for f, v in ((0, True), (f0, False), (f1 + 1, True)):
        ob.hide_render = ob.hide_viewport = v
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)
    for fc in K._fcurves(ob.animation_data.action):
        if "hide" in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def _boca_mundo(arma, f: int) -> tuple[Vector, Vector]:
    sc = bpy.context.scene
    sc.frame_set(f)
    bpy.context.view_layer.update()
    mw = arma.matrix_world
    boca = mw @ Vector(arma["boca_local"])
    adelante = (mw.to_3x3() @ Vector((0, -1, 0))).normalized()
    return boca, adelante


def disparo(nombre: str, arma, f: int, blanco: Vector, impacto: str, col, normal=None, semilla=0):
    M = _mats()
    rnd = random.Random(semilla)
    boca, adelante = _boca_mundo(arma, f)
    d = blanco - boca
    largo = d.length
    if largo < 0.2:
        return
    u = d.normalized()
    # trazadora: varilla emisiva de 1,2 m que recorre el camino en 2 cuadros
    tr = K.cilindro(f"{nombre}_trazadora", (0, 0, 0), 0.012, 1.2, M["trazadora"], col, lados=6)
    tr.rotation_mode = "QUATERNION"
    tr.rotation_quaternion = u.to_track_quat("Z", "Y")
    tr.visible_shadow = False
    tr["visor_omitir"] = True
    for k, frac in enumerate((0.35, 0.85)):
        tr.location = boca + d * frac
        tr.keyframe_insert("location", frame=f + k)
    _ocultar_salvo(tr, f, f + 1)
    # casquillo: sale a la derecha del arma, sube y cae girando
    der = adelante.cross(Vector((0, 0, 1))).normalized()
    cq = K.cilindro(f"{nombre}_casquillo", (0, 0, 0), 0.006, 0.022, M["casquillo"], col, lados=6)
    cq["visor_omitir"] = True
    v0 = der * rnd.uniform(1.8, 2.6) + Vector((0, 0, rnd.uniform(1.6, 2.4))) - adelante * 0.4
    p0 = boca - adelante * 0.35
    for k in range(0, 14):
        t = k / 30.0
        cq.location = p0 + v0 * t + Vector((0, 0, -4.9 * t * t))
        cq.rotation_euler = (k * 0.9, k * 0.5, 0)
        cq.keyframe_insert("location", frame=f + k)
        cq.keyframe_insert("rotation_euler", frame=f + k)
    _ocultar_salvo(cq, f, f + 13)
    if impacto == "nada":
        return
    n = Vector(normal) if normal else -u
    if impacto == "chispas":
        for j in range(9):
            ch = K.esfera(f"{nombre}_chispa_{j}", (0, 0, 0), 0.012, M["chispa"], col, subdiv=1, escala=(1, 1, 2.5))
            ch["visor_omitir"] = True
            ch.visible_shadow = False
            dirc = (n + Vector((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), rnd.uniform(-0.2, 1.0)))).normalized()
            vel = dirc * rnd.uniform(3.5, 7.0)
            for k in range(6):
                t = k / 30.0
                ch.location = blanco + vel * t + Vector((0, 0, -4.9 * t * t))
                ch.keyframe_insert("location", frame=f + 1 + k)
            _ocultar_salvo(ch, f + 1, f + 5 + j % 2)
        polvo = K.esfera(f"{nombre}_polvo", tuple(blanco), 0.05, M["polvo"], col, subdiv=2)
        polvo["visor_omitir"] = True
        for k, esc in enumerate((0.4, 1.6, 2.6, 3.2, 3.5)):
            polvo.scale = (esc,) * 3
            polvo.keyframe_insert("scale", frame=f + 1 + k * 2)
        _ocultar_salvo(polvo, f + 1, f + 9)
    elif impacto == "sangre":
        for j in range(7):
            go = K.esfera(f"{nombre}_gota_{j}", (0, 0, 0), rnd.uniform(0.012, 0.022), M["sangre"], col, subdiv=1)
            go["visor_omitir"] = True
            dirc = (u * 0.8 + Vector((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(0.0, 0.8)))).normalized()
            vel = dirc * rnd.uniform(1.2, 2.6)
            for k in range(9):
                t = k / 30.0
                go.location = blanco + vel * t + Vector((0, 0, -4.9 * t * t))
                go.keyframe_insert("location", frame=f + 1 + k)
            _ocultar_salvo(go, f + 1, f + 8)


def preparar(tiros: list, pjs: dict, fps: int, col=None):
    """Crea todos los efectos de la lista de tiros (lo llama el escenario después de crear a los personajes)."""
    col = col or K.coleccion("tiroteo")
    for i, tiro in enumerate(sorted(tiros, key=lambda x: x["t"])):
        pj = pjs[tiro["tirador"]]
        arma = pj.get("arma")
        if arma is None:
            continue
        f = int(round(tiro["t"] * fps)) + 1
        disparo(f"tiro_{i:02d}_{tiro['tirador']}", arma, f, Vector(tiro["a"]), tiro.get("impacto", "chispas"), col,
                tiro.get("normal"), semilla=i)
