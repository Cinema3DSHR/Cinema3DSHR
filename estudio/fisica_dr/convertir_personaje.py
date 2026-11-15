"""Convierte un personaje del estudio (FBX/GLB con esqueleto Mixamo) a un GLB en pose de reposo, sin animaciones,
para sentarlo en la cabina de Dream Rally (rig_pilot.gd lo maneja por cinemática inversa).

Uso (con el Python que trae bpy):  python -I convertir_personaje.py <ref o ruta> <salida.glb>
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import bpy
from estudio.blender import importar as I

ref, salida = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = I.importar(ref)
for o in bpy.data.objects:
    o.select_set(o in objs and o.type in ("ARMATURE", "MESH"))
    if o.animation_data:
        o.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
# el FBX trae la escala (centímetros) en el nodo del esqueleto: rig_pilot.gd mide la estatura sobre los huesos sin esa
# escala, así que se aplica todo (huesos y mallas en metros, nodos con escala 1, como el pilot.glb del juego)
sel = [o for o in bpy.data.objects if o.select_get()]
bpy.context.view_layer.objects.active = next((o for o in sel if o.type == "ARMATURE"), sel[0])
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.export_scene.gltf(filepath=salida, export_format="GLB", use_selection=True, export_animations=False,
                          export_skins=True, export_yup=True, export_image_format="JPEG")
print("convertido", salida)
