"""Escenario MÍNIMO para las pruebas del sistema de componentes (pruebas/sistema/test_trabajo.py): un piso, una caja,
una luz que titila (evento) y un objeto que el escenario le pone en la mano a un personaje después de crearlo
(`despues_personajes`, como la utilería de «A la deriva»). No se usa en producciones."""
from __future__ import annotations

import bpy
from mathutils import Matrix

from estudio.blender import kit as K

DEPENDENCIAS = []
PARAMETROS = {"color_caja": [0.6, 0.2, 0.2]}
PARAMETROS_DESPUES = ("objeto_mano",)


def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    col = K.coleccion("ESCENARIO_prueba")
    K.caja("piso", (0, 0, -0.05), (12, 12, 0.1), K.material("piso_prueba", (0.3, 0.3, 0.32)), col)
    caja = K.caja("caja", (1.5, 2.0, 0.5), (1, 1, 1), K.material("caja_prueba", tuple(p["color_caja"])), col)
    luz = K.luz("luz_prueba", "POINT", (0, 0, 3), 200, (1, 1, 1), col)
    K.luz("sol_prueba", "SUN", (0, 0, 10), 3, (1, 1, 1), col)
    return {"anclas": {"centro": (0.0, 0.0, 1.0), "caja": (1.5, 2.0, 0.5)}, "animables": {"luz": luz, "caja": caja},
            "personajes": []}


def titilar(animables: dict, frame_inicio: int = 1, **_):
    luz = animables["luz"]
    for f, e in ((1, 200), (frame_inicio, 40), (frame_inicio + 5, 200)):
        luz.data.energy = e
        luz.data.keyframe_insert("energy", frame=f)


def despues_personajes(info, pjs, ctx, manifiesto, fps):
    spec = manifiesto["escenario"].get("parametros", {}).get("objeto_mano")
    if not spec:
        return
    pj = pjs[spec["personaje"]]
    arm = pj["armadura"]
    hueso = next(b.name for b in arm.pose.bones if b.name.endswith("RightHand"))
    ob = K.caja("objeto_mano", (0, 0, 0), (0.05, 0.05, 0.2), K.material("objeto_mano", (0.1, 0.5, 0.9)),
                K.coleccion("UTILERIA_prueba"))
    bpy.context.scene.frame_set(1)
    ob.parent, ob.parent_type, ob.parent_bone = arm, "BONE", hueso
    bpy.context.view_layer.update()
    ob.matrix_world = arm.matrix_world @ arm.pose.bones[hueso].matrix @ Matrix.Translation((0, 0.08, 0))
