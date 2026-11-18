"""Arma SÓLO el set de la nave (estudio/escenarios/nave_deriva.py) y lo exporta como la previsualización (GLB) para
mirarlo en el visor de la app (pruebas/nave/vista_nave.gd). No renderiza nada.
Uso: python pruebas/nave/armar_nave.py SALIDA.glb"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import bpy
from estudio.blender import kit as K, previa as PV
from estudio.escenarios import nave_deriva as N

bpy.ops.wm.read_factory_settings(use_empty=True)
K.reiniciar_materiales()
info = N.construir({})
print("anclas", {k: tuple(round(x, 2) for x in v) for k, v in info["anclas"].items()})
PV._aplanar_materiales()
bpy.ops.export_scene.gltf(filepath=sys.argv[1], export_format="GLB", export_apply=True, export_lights=True,
                          export_image_format="WEBP", use_visible=True)
print("OK", sys.argv[1])
