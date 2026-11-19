"""AutoEffects (bpy): aplica SÓLO los efectos que pide la receta de terminación, cada uno sobre su vacío FX_* de Godot.
Los vacíos FX que llegaron sin receta se informan (no se inventa un efecto para ellos). Si la receta pide un vacío que
no llegó, la preparación se detiene (no se publica una versión a medias)."""
from __future__ import annotations

import copy

import bpy

from estudio.autofinisher import convenciones as CV
from estudio.autofinisher.recetas_efectos import RECETAS, nodos as K, receta as modulo


def _mezclar(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        out[k] = _mezclar(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def aplicar(receta: dict) -> dict:
    pedidos = receta.get("efectos", [])
    hecho = {"aplicados": [], "vacios_fx_sin_receta": []}
    if not pedidos:
        hecho["nota"] = "la receta no pide efectos"
    ctx = K.Contexto(receta) if pedidos else None
    usados = set()
    for ef in pedidos:
        nombre = ef["receta"]
        if nombre not in RECETAS:
            raise KeyError(f"efecto «{nombre}» no existe en la biblioteca ({', '.join(RECETAS)})")
        ancla = None
        if ef.get("ancla"):
            ancla = bpy.data.objects.get(ef["ancla"])
            if ancla is None:
                raise KeyError(f"efecto «{nombre}»: no llegó el vacío «{ef['ancla']}» en el GLB")
            usados.add(ancla.name)
        mod = modulo(nombre)
        p = _mezclar(mod.PARAMETROS_POR_DEFECTO, ef.get("parametros", {}))
        r = mod.aplicar(ancla, p, ctx)
        hecho["aplicados"].append({"receta": nombre, "ancla": ef.get("ancla"), "resultado": r})
    for o in bpy.data.objects:
        if o.type == "EMPTY" and CV.receta_fx(o.name, o.get("cine_tipo")) and o.name not in usados:
            hecho["vacios_fx_sin_receta"].append(o.name)
    return hecho
