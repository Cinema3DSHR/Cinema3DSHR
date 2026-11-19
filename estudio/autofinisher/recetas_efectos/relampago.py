"""Receta RELÁMPAGO (bpy): el destello y el rayo ya viajan animados en el GLB (escala y energía); para Cycles sólo se
refuerza la emisión del material del rayo y se les quita la sombra. No necesita vacío FX."""
from __future__ import annotations

import bpy

from estudio.autofinisher.recetas_efectos import nodos as K

PARAMETROS_POR_DEFECTO = {"material": "rayo", "emision": 60.0, "objetos_sin_sombra": ["Relampago_cielo", "Relampago_rayo"]}


def aplicar(ancla, p: dict, ctx: K.Contexto) -> dict:
    m = bpy.data.materials.get(p["material"])
    if m is None:
        raise KeyError(f"relámpago: no está el material «{p['material']}»")
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Emission Strength"].default_value = p["emision"]
    sin_sombra = []
    for nombre in p["objetos_sin_sombra"]:
        o = bpy.data.objects.get(nombre)
        if o is None:
            raise KeyError(f"relámpago: no está el objeto «{nombre}»")
        for h in [o] + list(o.children_recursive):
            h.visible_shadow = False
            sin_sombra.append(h.name)
    return {"relampago": f"emisión del material «{p['material']}» {p['emision']}, sin sombra: {len(sin_sombra)} objetos"}
