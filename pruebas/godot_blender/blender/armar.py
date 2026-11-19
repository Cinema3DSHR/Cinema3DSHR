"""Arma el .blend editable desde el GLB de Godot, etapa por etapa, midiendo cada una (SIN render).
Uso: /opt/tools/blendenv/bin/python blender/armar.py godot/salida/casa_tormenta.glb blender/casa_tormenta.blend"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
import b6_importar, b7_materiales, b8_efectos, b9_cycles  # noqa: E402

glb, blend = sys.argv[1], sys.argv[2]
informe = {}
for etapa, f in (("6_importacion", lambda: b6_importar.importar(glb)), ("7_materiales_luces", b7_materiales.corregir),
                 ("8_efectos", b8_efectos.crear), ("9_cycles", b9_cycles.preparar)):
    t = time.time()
    r = f()
    informe[etapa] = {"segundos": round(time.time() - t, 2), "resultado": r}
t = time.time()
bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()), compress=True)
informe["guardado"] = {"segundos": round(time.time() - t, 2), "bytes": Path(blend).stat().st_size}
Path(blend).with_suffix(".json").write_text(json.dumps(informe, ensure_ascii=False, indent=1))
print(json.dumps({k: v["segundos"] for k, v in informe.items()}))
