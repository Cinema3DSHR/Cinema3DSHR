"""Renderiza un trozo de cuadros del .blend de la prueba (lo usa render_prueba_godot_blender.yml, SÓLO por orden del
dueño). Uso: python render_trozo.py <blend> <desde> <hasta> <ancho> <alto> <muestras> <carpeta>
Los cuadros del .blend van de 0 a 899; los archivos salen numerados de 1 a 900 (f_0001.png …), como en el estudio."""
import json
import sys
import time
from pathlib import Path

import bpy

blend, desde, hasta, ancho, alto, muestras, salida = sys.argv[1], *map(int, sys.argv[2:7]), Path(sys.argv[7])
bpy.ops.wm.open_mainfile(filepath=blend)
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = ancho, alto, 100
s.cycles.samples = muestras
s.render.image_settings.file_format = "PNG"
s.render.image_settings.color_mode = "RGB"
salida.mkdir(parents=True, exist_ok=True)
tiempos = {}
for n in range(desde, hasta + 1):
    t = time.time()
    s.frame_set(n - 1)
    s.render.filepath = str((salida / f"f_{n:04d}.png").resolve())
    bpy.ops.render.render(write_still=True)
    tiempos[n] = round(time.time() - t, 2)
    print(f"cuadro {n}: {tiempos[n]} s", flush=True)
(salida / f"informe_{desde:04d}.json").write_text(json.dumps(
    {"desde": desde, "hasta": hasta, "resolucion": f"{ancho}x{alto}", "muestras": muestras, "segundos_por_cuadro": tiempos,
     "media_s": round(sum(tiempos.values()) / len(tiempos), 2), "blender": bpy.app.version_string}, indent=1))
