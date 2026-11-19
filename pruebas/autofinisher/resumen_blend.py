"""Resumen comparable de un .blend (SIN render): escena, Cycles, luces (energía fija y claves animadas), materiales,
mundo, efectos (nodos de geometría y volúmenes), empaquetado y animación. Sirve para comparar la reconstrucción del
AutoFinisher con la prueba original (comparar.py).

    /opt/tools/blendenv/bin/python pruebas/autofinisher/resumen_blend.py X.blend salida.json
"""
import json
import sys

import bpy
from bpy_extras import anim_utils


def curvas(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return list(cb.fcurves) if cb else []


def r(v, n=4):
    return round(float(v), n)


def _val(x):
    if isinstance(x, bool) or x is None:
        return x
    if isinstance(x, (int, float)):
        return r(x)
    if isinstance(x, str):
        return x
    try:
        return [_val(y) for y in x]
    except TypeError:
        return getattr(x, "name", str(x))


def valor_socket(sk):
    if not hasattr(sk, "default_value"):
        return None
    return _val(sk.default_value)


def nodos(nt):
    out = {}
    for n in nt.nodes:
        clave = n.bl_idname + (":" + n.operation if hasattr(n, "operation") else "")
        ent = {f"{i}:{s.name}": valor_socket(s) for i, s in enumerate(n.inputs) if s.enabled and not s.is_linked and valor_socket(s) is not None}
        out.setdefault(clave, []).append(ent)
    return {k: sorted(v, key=lambda e: json.dumps(e, sort_keys=True)) for k, v in sorted(out.items())}


bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
s = bpy.context.scene
c = s.cycles
res = {
    "escena": {"fps": s.render.fps, "rango": [s.frame_start, s.frame_end], "resolucion": [s.render.resolution_x, s.render.resolution_y],
               "camara": s.camera.name if s.camera else None, "motor": s.render.engine,
               "color": [s.view_settings.view_transform, s.view_settings.look]},
    "cycles": {"muestras": c.samples, "adaptativo": [c.use_adaptive_sampling, r(c.adaptive_threshold)],
               "denoiser": [c.use_denoising, c.denoiser, c.denoising_input_passes],
               "rebotes": [c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces,
                           c.transparent_max_bounces, c.volume_bounces],
               "causticas": [c.caustics_reflective, c.caustics_refractive], "clamp_indirecto": r(c.sample_clamp_indirect),
               "arbol_de_luces": getattr(c, "use_light_tree", None), "volumen": [r(c.volume_step_rate), c.volume_max_steps],
               "datos_persistentes": s.render.use_persistent_data, "dispositivo": c.device},
    "objetos": sorted(f"{o.type}:{o.name}" for o in bpy.data.objects),
    "luces": {}, "materiales": {}, "efectos": {}, "mundo": None,
    "imagenes": sorted(f"{i.name}:{'empaquetada' if i.packed_file else 'EXTERNA'}" for i in bpy.data.images
                       if i.source in ("FILE", "SEQUENCE", "MOVIE")),
    "acciones": {a.name: [r(x, 2) for x in a.frame_range] for a in bpy.data.actions},
}
for o in bpy.data.objects:
    if o.type == "LIGHT":
        L = o.data
        claves = []
        for fc in curvas(L):
            if fc.data_path == "energy":
                ys = [kp.co.y for kp in fc.keyframe_points]
                claves = [len(ys), r(min(ys), 3), r(max(ys), 3)]
        res["luces"][o.name] = {"tipo": L.type, "energia": r(L.energy, 3), "color": [r(x, 3) for x in L.color],
                                "radio": r(L.shadow_soft_size, 3), "angulo": r(getattr(L, "angle", 0), 4), "claves": claves}
    if o.type == "MESH" and o.modifiers:
        for md in o.modifiers:
            if md.type == "NODES" and md.node_group:
                res["efectos"][o.name] = {"modificador": md.name, "nodos": nodos(md.node_group)}
    if o.visible_shadow is False:
        res.setdefault("sin_sombra", []).append(o.name)
res["sin_sombra"] = sorted(res.get("sin_sombra", []))
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    d = {}
    if b is not None:
        d = {k: valor_socket(b.inputs[k]) for k in ("Base Color", "Alpha", "Roughness", "IOR", "Transmission Weight",
                                                      "Emission Strength", "Emission Color")}
        d["metodo"] = m.surface_render_method
    if any(n.type in ("EMISSION", "PRINCIPLED_VOLUME") for n in m.node_tree.nodes) or m.name in ("gota_lluvia",):
        d["nodos"] = nodos(m.node_tree)
    res["materiales"][m.name] = d
if s.world and s.world.use_nodes:
    bg = s.world.node_tree.nodes.get("Background")
    res["mundo"] = {"nombre": s.world.name, "color": valor_socket(bg.inputs["Color"]), "fuerza": valor_socket(bg.inputs["Strength"])}
for o in bpy.data.objects:
    if o.name in ("Fuego_volumen", "Humo_volumen", "Choque_techo_casa", "Gota_lluvia", "Chispa"):
        res["efectos"][o.name] = {"ubicacion": [r(x, 3) for x in o.matrix_world.translation],
                                  "dimensiones": [r(x, 3) for x in o.dimensions],
                                  "colecciones": [c.name for c in o.users_collection]}
json.dump(res, open(sys.argv[2], "w"), ensure_ascii=False, indent=1, sort_keys=True)
print("resumen:", sys.argv[2])
