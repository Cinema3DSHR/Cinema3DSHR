"""AutoImport (bpy): escena vacía con los fps de la receta ANTES de importar (el importador glTF convierte los segundos
de la animación con los fps de la escena: con los 24 de fábrica una toma de 30 s quedaba en 720 cuadros), importa el
GLB, elige la cámara, fija el rango de cuadros e inspecciona lo que llegó."""
from __future__ import annotations

import bpy

from estudio.autofinisher import convenciones as CV


def _cine_tipo(idb) -> str | None:
    v = idb.get("cine_tipo") if hasattr(idb, "get") else None
    return str(v) if v else None


def importar(glb: str, receta: dict) -> dict:
    es = receta["escena"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps = es["fps"]
    s.render.fps_base = 1.0
    bpy.ops.import_scene.gltf(filepath=str(glb))
    s.frame_start, s.frame_end = es["cuadro_inicial"], es["cuadro_final"]
    camaras = [o for o in bpy.data.objects if o.type == "CAMERA"]
    if es.get("camara"):
        cam = bpy.data.objects.get(es["camara"])
        if cam is None or cam.type != "CAMERA":
            raise ValueError(f"la receta pide la cámara «{es['camara']}» y el GLB no la trae "
                             f"(cámaras: {[c.name for c in camaras]})")
    elif len(camaras) == 1:
        cam = camaras[0]
    else:
        raise ValueError(f"el GLB trae {len(camaras)} cámaras: la receta tiene que decir cuál (escena.camara)")
    s.camera = cam
    return {"fps": s.render.fps, "rango": [s.frame_start, s.frame_end], "camara": cam.name, **inspeccionar()}


def inspeccionar() -> dict:
    """Qué llegó del GLB (para el informe y para detectar lo que hay que reconstruir)."""
    tipos: dict[str, int] = {}
    for o in bpy.data.objects:
        tipos[o.type] = tipos.get(o.type, 0) + 1
    tri = 0
    for me in bpy.data.meshes:
        me.calc_loop_triangles()
        tri += len(me.loop_triangles) * max(1, me.users)
    luces = [{"nombre": o.name, "tipo": o.data.type, "perfil": CV.perfil_luz(o.name, o.data.type, _cine_tipo(o)),
              "energia_importada": round(o.data.energy, 5), "color": [round(c, 3) for c in o.data.color],
              "animada": bool(o.data.animation_data and o.data.animation_data.action)}
             for o in bpy.data.objects if o.type == "LIGHT"]
    vacios_fx = sorted(o.name for o in bpy.data.objects if o.type == "EMPTY" and CV.receta_fx(o.name, _cine_tipo(o)))
    colisiones = sorted(o.name for o in bpy.data.objects if o.name.startswith(CV.PREFIJO_COLISION))
    acciones = {a.name: [round(x, 2) for x in a.frame_range] for a in bpy.data.actions}
    animados = sorted(o.name for o in bpy.data.objects if o.animation_data and o.animation_data.action)
    mats = []
    for m in bpy.data.materials:
        b = next((n for n in (m.node_tree.nodes if m.use_nodes else []) if n.type == "BSDF_PRINCIPLED"), None)
        if b is None:
            continue
        mats.append({"nombre": m.name, "alfa": round(b.inputs["Alpha"].default_value, 3),
                     "emision": round(b.inputs["Emission Strength"].default_value, 3),
                     "vidrio": CV.es_vidrio(m.name, _cine_tipo(m)),
                     "textura": any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes)})
    return {"objetos": tipos, "triangulos": tri, "luces": luces, "vacios_fx": vacios_fx, "colisiones": colisiones,
            "acciones": acciones, "animados": animados, "materiales": mats,
            "imagenes": [{"nombre": i.name, "tam": list(i.size), "empaquetada": bool(i.packed_file)}
                         for i in bpy.data.images if i.source in ("FILE", "SEQUENCE", "MOVIE")]}
