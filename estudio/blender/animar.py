"""Claves en bloque (rápido): una curva por canal, todos los puntos de una vez (foreach_set).

Para trenes y vehículos que se mueven cuadro a cuadro durante miles de fotogramas, `keyframe_insert` uno por uno es
lento; acá se llena la curva entera en una sola llamada.
"""
from __future__ import annotations
import bpy

_INTERP = {}


def _interp(nombre: str) -> int:
    if not _INTERP:
        for it in bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items:
            _INTERP[it.identifier] = it.value
    return _INTERP[nombre]


def curva(obj, ruta: str, indice: int, frames, valores, interp: str = "LINEAR"):
    """Reemplaza la curva `ruta[indice]` de `obj` por los puntos (frames, valores)."""
    ad = obj.animation_data or obj.animation_data_create()
    if ad.action is None:
        ad.action = bpy.data.actions.new(f"AN_{obj.name}")
    fc = ad.action.fcurve_ensure_for_datablock(obj, ruta, index=indice)
    while len(fc.keyframe_points):
        fc.keyframe_points.remove(fc.keyframe_points[0], fast=True)
    n = len(frames)
    fc.keyframe_points.add(n)
    co = [0.0] * (2 * n)
    co[0::2] = [float(f) for f in frames]
    co[1::2] = [float(v) for v in valores]
    fc.keyframe_points.foreach_set("co", co)
    fc.keyframe_points.foreach_set("interpolation", [_interp(interp)] * n)
    fc.update()
    return fc


def transformacion(obj, frames, posiciones=None, rotaciones=None, interp: str = "LINEAR"):
    """posiciones: [(x, y, z)…]; rotaciones: [(rx, ry, rz)…] (Euler XYZ, radianes). None = no se toca ese canal."""
    if posiciones is not None:
        for i in range(3):
            curva(obj, "location", i, frames, [p[i] for p in posiciones], interp)
    if rotaciones is not None:
        obj.rotation_mode = "XYZ"
        for i in range(3):
            curva(obj, "rotation_euler", i, frames, [r[i] for r in rotaciones], interp)


def desenrollar(angulos):
    """Ángulos continuos (sin saltos de 2π) para que la interpolación no dé vueltas de más."""
    import math
    out = []
    for a in angulos:
        if out:
            while a - out[-1] > math.pi:
                a -= 2 * math.pi
            while a - out[-1] < -math.pi:
                a += 2 * math.pi
        out.append(a)
    return out
