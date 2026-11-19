"""Cambia la cámara (y las cabinas que dependen de ella) de un BLEND ya construido, con el GLB chico de cámara que sale de Godot (--solo_camara).
Uso: python retoque_camara.py -- <entrada.blend> <camara.glb> <camara.json> <salida.blend>"""
import sys, json, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cabinas, camara_cfg
bpy.ops.wm.open_mainfile(filepath=a[0])
s = bpy.context.scene
D = json.load(open(a[2]))
viejo = bpy.data.objects["Camara"]
antes = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=a[1])
nuevo = next(o for o in bpy.data.objects if o.name not in antes and o.type == "CAMERA")
# (la entrada es el BLEND v1: todavía no tiene cabinas ni luces de cabina)
bpy.data.objects.remove(viejo)
nuevo.name = "Camara"
nuevo.data.name = "Camara"
s.camera = nuevo
print("CAMARA curvas", camara_cfg.camara(s, D))
print("CABINAS", cabinas.cabinas(D, s))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=a[3], compress=True)
