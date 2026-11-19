"""Valida un .blend contra su manifiesto SIN renderizar (bpy): hash y tamaño, que abra, que sea autónomo, cámara,
rango, fps, resolución y calidad iguales a las del manifiesto. Lo usan la construcción antes de publicar y cada
trabajo de render antes de empezar."""
from __future__ import annotations

import time
from pathlib import Path

import bpy

from estudio.autofinisher import auto_pack, manifiesto as MF, medicion as MD


def validar(ruta_blend: str, ruta_manifiesto: str) -> dict:
    m = MF.leer(ruta_manifiesto)
    ok_hash, motivo_hash = MF.verificar_blend(m, ruta_blend)
    problemas = [] if ok_hash else [motivo_hash]
    t = time.time()
    bpy.ops.wm.open_mainfile(filepath=str(Path(ruta_blend).resolve()))
    abrir_s = round(time.time() - t, 2)
    s = bpy.context.scene
    r = m["render"]
    esperado = {"fps": r["fps"], "resolucion": list(r["resolucion"]), "cuadro_inicial": r["cuadro_inicial"],
                "cuadro_final": r["cuadro_final"], "muestras": r["muestras"], "motor": r["motor"]}
    actual = {"fps": s.render.fps, "resolucion": [s.render.resolution_x, s.render.resolution_y],
              "cuadro_inicial": s.frame_start, "cuadro_final": s.frame_end, "muestras": s.cycles.samples,
              "motor": s.render.engine}
    for k, v in esperado.items():
        if actual[k] != v:
            problemas.append(f"{k}: el .blend tiene {actual[k]} y el manifiesto {v}")
    if s.camera is None:
        problemas.append("la escena no tiene cámara activa")
    elif r.get("camara") and s.camera.name != r["camara"]:
        problemas.append(f"cámara activa «{s.camera.name}» ≠ «{r['camara']}» del manifiesto")
    emp = auto_pack.revisar()
    if not emp["autonomo"]:
        problemas.append(f"recursos externos: {emp['externos']}")
    return {"ok": not problemas, "problemas": problemas, "hash": motivo_hash, "abrir_s": abrir_s,
            "ram_max_mb": MD.ram_max_mb(), "actual": actual, "empaquetados": len(emp["empaquetados"]),
            "objetos": len(bpy.data.objects), "id": m["id"]}
