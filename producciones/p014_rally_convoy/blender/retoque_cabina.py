"""Aplica `cabinas.cabinas()` a un BLEND ya construido (sin rehacer la importación de 20 min).
Uso: python retoque_cabina.py -- <entrada.blend> <datos.json> <salida.blend>"""
import sys, json, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cabinas
bpy.ops.wm.open_mainfile(filepath=a[0])
D = json.load(open(a[1]))
print("CABINAS", cabinas.cabinas(D, bpy.context.scene))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=a[2], compress=True)
