"""Renderiza los cuadros asignados a UN trabajo, desde el .blend autónomo de una versión (bpy).

    <python de Blender> -m estudio.autofinisher render-trozo --blend X.blend --manifiesto manifest.json \
        (--desde 1 --hasta 15 | --cuadros 12,40-45) --ancho 540 --alto 960 --muestras 6 --salida out \
        [--reintentos 1] [--sin-render]

- Los archivos se numeran 1..N (f_0001.png); el cuadro de Blender es cuadro_inicial + n − 1 (del manifiesto).
- Verifica el SHA-256 del .blend contra el manifiesto ANTES de abrirlo (render de la versión exacta).
- Cada cuadro se reintenta `--reintentos` veces si Blender falla o el archivo sale vacío; un cuadro que no sale queda
  como FALLO en el informe y el proceso termina con error (nunca se inventa ni se copia un cuadro).
- `--sin-render` hace todo menos el render (abre, ubica cada cuadro, mide): para probar el trabajo sin gastar CPU.
- Informe `informe_<desde>.json`: preparación, tiempo y RAM por cuadro, reintentos, fallos, máquina.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import bpy

from estudio.autofinisher import manifiesto as MF, medicion as MD, reparto as RP


def renderizar(blend: str, ruta_manifiesto: str, cuadros: list[int], ancho: int, alto: int, muestras: int,
               salida: str, reintentos: int = 1, sin_render: bool = False) -> dict:
    t0 = time.time()
    m = MF.leer(ruta_manifiesto)
    ok, motivo = MF.verificar_blend(m, blend)
    if not ok:
        raise SystemExit(f"RENDER DETENIDO: el .blend no es el de {m['id']}: {motivo}")
    hash_s = round(time.time() - t0, 2)
    t = time.time()
    bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
    abrir_s = round(time.time() - t, 2)
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = ancho, alto, 100
    s.cycles.samples = muestras
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    out = Path(salida)
    out.mkdir(parents=True, exist_ok=True)
    inicio = m["render"]["cuadro_inicial"]
    total = m["render"]["cuadros"]
    malos = [c for c in cuadros if c < 1 or c > total]
    if malos:
        raise SystemExit(f"cuadros fuera de 1..{total}: {malos[:10]}")
    por_cuadro, fallos, reint = {}, [], 0
    for n in cuadros:
        destino = out / f"f_{n:04d}.png"
        intento = 0
        while True:
            t = time.time()
            try:
                s.frame_set(inicio + n - 1)
                s.render.filepath = str(destino.resolve())
                if not sin_render:
                    bpy.ops.render.render(write_still=True)
                    if not destino.exists() or destino.stat().st_size == 0:
                        raise RuntimeError("el archivo del cuadro salió vacío o no se escribió")
                por_cuadro[n] = {"s": round(time.time() - t, 2), "ram_mb": MD.ram_max_mb(), "intentos": intento + 1}
                print(f"cuadro {n}: {por_cuadro[n]['s']} s", flush=True)
                break
            except Exception as e:
                intento += 1
                if intento > reintentos:
                    fallos.append({"cuadro": n, "error": f"{type(e).__name__}: {e}"[:300], "intentos": intento})
                    print(f"cuadro {n}: FALLO ({e})", flush=True)
                    break
                reint += 1
                print(f"cuadro {n}: reintento {intento} ({e})", flush=True)
    tiempos = [v["s"] for v in por_cuadro.values()]
    inf = {"formato": "estudio.informe_trozo/1", "version": m["id"], "blend_sha256": m["archivos"]["blend"]["sha256"],
           "cuadros_pedidos": RP.comprimir(cuadros), "cantidad": len(cuadros), "procesados": len(por_cuadro),
           "renderizados": 0 if sin_render else len(por_cuadro),
           "fallos": fallos, "reintentos": reint, "sin_render": sin_render,
           "resolucion": f"{ancho}x{alto}", "muestras": muestras,
           "difiere_del_manifiesto": {k: v for k, v in (("resolucion", [ancho, alto] != list(m["render"]["resolucion"])),
                                                         ("muestras", muestras != m["render"]["muestras"])) if v},
           "verificar_hash_s": hash_s, "abrir_blend_s": abrir_s, "por_cuadro": por_cuadro,
           "media_s": round(sum(tiempos) / len(tiempos), 2) if tiempos else None,
           "max_s": max(tiempos) if tiempos else None, "total_s": round(time.time() - t0, 2),
           "ram_max_mb": MD.ram_max_mb(), "blender": bpy.app.version_string, "entorno": MD.entorno()}
    (out / f"informe_{cuadros[0]:04d}.json").write_text(json.dumps(inf, indent=1, ensure_ascii=False))
    return inf
