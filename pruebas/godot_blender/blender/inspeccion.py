"""ETAPA 6 — Importa el GLB de Godot en Blender y anota qué llegó (sin tocar nada).
Uso: /opt/tools/blendenv/bin/python blender/inspeccion.py godot/salida/casa_tormenta.glb blender/importado.json"""
import bpy, json, sys, time
glb, salida = sys.argv[1], sys.argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
t = time.time()
bpy.ops.import_scene.gltf(filepath=glb)
dt = time.time() - t
sc = bpy.context.scene
r = {"segundos_importacion": round(dt, 2), "objetos": {}, "fps": sc.render.fps, "frames": [sc.frame_start, sc.frame_end]}
for o in bpy.data.objects:
    r["objetos"].setdefault(o.type, 0)
    r["objetos"][o.type] += 1
r["camaras"] = [{"nombre": o.name, "lente_mm": round(o.data.lens, 2), "sensor_fit": o.data.sensor_fit,
                 "anim": bool(o.animation_data and o.animation_data.action)} for o in bpy.data.objects if o.type == "CAMERA"]
r["luces"] = [{"nombre": o.name, "tipo": o.data.type, "energia": round(o.data.energy, 2),
               "color": [round(c, 3) for c in o.data.color],
               "anim": bool(o.data.animation_data and o.data.animation_data.action)} for o in bpy.data.objects if o.type == "LIGHT"]
r["acciones"] = {}
for a in bpy.data.actions:
    curvas = []
    try:
        for cb in a.layers[0].strips[0].channelbags:
            curvas += [f"{c.data_path}[{c.array_index}]:{len(c.keyframe_points)}" for c in cb.fcurves]
    except Exception:
        curvas = [f"{c.data_path}:{len(c.keyframe_points)}" for c in getattr(a, "fcurves", [])]
    r["acciones"][a.name] = {"rango": list(a.frame_range), "curvas": curvas[:12], "n_curvas": len(curvas)}
r["animados"] = sorted({o.name for o in bpy.data.objects if o.animation_data and o.animation_data.action})
r["materiales"] = {}
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is None:
        r["materiales"][m.name] = "sin Principled"
        continue
    r["materiales"][m.name] = {
        "base": [round(v, 3) for v in b.inputs["Base Color"].default_value],
        "rug": round(b.inputs["Roughness"].default_value, 3), "metal": round(b.inputs["Metallic"].default_value, 3),
        "alfa": round(b.inputs["Alpha"].default_value, 3), "emision": round(b.inputs["Emission Strength"].default_value, 2),
        "transmision": round(b.inputs["Transmission Weight"].default_value, 2),
        "textura": any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes)}
r["vacios_fx"] = [o.name for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith(("FX_", "Colision"))]
r["vacios_otros"] = [o.name for o in bpy.data.objects if o.type == "EMPTY" and o.name in ("Ambiente", "Animacion")]
r["triangulos"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
json.dump(r, open(salida, "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in r.items() if k not in ("materiales",)}, ensure_ascii=False, indent=1)[:5000])
