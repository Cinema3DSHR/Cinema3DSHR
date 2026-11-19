import bpy, json, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.fps = 30
s.render.fps_base = 1.0
bpy.ops.import_scene.gltf(filepath="/home/user/cls63/cls63_escena.glb")
mallas = [o for o in bpy.data.objects if o.type == "MESH"]
luces = [o for o in bpy.data.objects if o.type == "LIGHT"]
camaras = [o for o in bpy.data.objects if o.type == "CAMERA"]
acciones = [a.name for a in bpy.data.actions]
r = {"mallas": len(mallas), "luces": [(o.name, o.data.type, round(o.data.energy, 2)) for o in luces],
     "camaras": [o.name for o in camaras], "acciones": acciones,
     "materiales": len(bpy.data.materials), "imagenes": len(bpy.data.images),
     "imagenes_sin_empaquetar": sum(1 for i in bpy.data.images if i.source == "FILE" and not i.packed_file)}
print("INFORME", json.dumps(r, ensure_ascii=False))
