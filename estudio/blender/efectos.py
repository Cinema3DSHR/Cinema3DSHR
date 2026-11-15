"""Efectos de acción para las escenas: fogonazo de boca de cañón (malla emisiva + luz puntual que destellan sólo en los
fotogramas de cada disparo). Sin simulación: todo es visibilidad por fotograma, barato y reproducible."""
from __future__ import annotations
import bpy
from mathutils import Vector
from estudio.blender import kit as K


def _visible_en(obj, frames: list[int], duracion_f: int = 1):
    """Invisible salvo durante `duracion_f` fotogramas desde cada fotograma de `frames` (interpolación constante)."""
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=1)
    for f in sorted(set(frames)):
        obj.hide_render = False
        obj.keyframe_insert("hide_render", frame=f)
        obj.hide_render = True
        obj.keyframe_insert("hide_render", frame=f + duracion_f)
    for fc in K._fcurves(obj.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def fogonazos(arma, frames: list[int], col=None, energia: float = 1800.0):
    """Fogonazo en la boca del cañón de `arma` (el vacío soporte de `armas.acoplar`) en cada fotograma de `frames`."""
    boca = Vector(arma["boca_local"])
    mat = K.emisivo("fogonazo", (1.0, 0.72, 0.3), 120.0)
    flash = K.esfera(f"{arma.name}_fogonazo", (0, 0, 0), 0.05, mat, col, subdiv=1, escala=(1.0, 3.2, 1.0))
    for o, desp in ((flash, Vector((0, -0.07, 0))),):
        o.parent = arma
        o.location = boca + desp
    luz = K.luz(f"{arma.name}_luz_fogonazo", "POINT", (0, 0, 0), energia, (1.0, 0.75, 0.4), col, radio=0.03, sombra=True)
    luz.parent = arma
    luz.location = boca + Vector((0, -0.2, 0))
    _visible_en(flash, frames)
    _visible_en(luz, frames)
    return flash, luz
