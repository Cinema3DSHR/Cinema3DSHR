"""Renderiza el tramo de UNA escena que le toca a un trabajo del episodio (lo llama el flujo «Episodio · render»).

Arma la escena con el camino de producción (director.construir) UNA sola vez y renderiza sus fotogramas uno tras otro
con datos persistentes (la escena, el BVH y las texturas quedan en memoria entre fotogramas). Fija explícitamente la
configuración pedida y la verifica antes de empezar; cualquier diferencia corta el trabajo:
Cycles CPU · 960×540 · 30 fps · 6 muestras · muestreo adaptativo 0,05 · OpenImageDenoise · 6 rebotes · árbol de
luces · semilla fija (0, no animada). Cada fotograma sale como f_GGGG.png con su número GLOBAL en la película.

    python -I pruebas/episodio/render_bloque.py ESCENA.json --offset 979 --locales 1,2,3 --salida out
"""
import argparse
import datetime as dt
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import bpy  # noqa: E402
from estudio import manifiesto as MF  # noqa: E402
from estudio.blender import director as D  # noqa: E402

CONFIG = {"ancho": 960, "alto": 540, "fps": 30, "muestras": 6, "umbral": 0.05, "rebotes": 6}

ap = argparse.ArgumentParser()
ap.add_argument("escena")
ap.add_argument("--offset", type=int, required=True, help="fotogramas de la película antes de esta escena")
ap.add_argument("--locales", required=True, help="fotogramas de la escena a renderizar (base 1), separados por coma")
ap.add_argument("--salida", required=True)
a = ap.parse_args()
locales = [int(x) for x in a.locales.split(",") if x]
out = Path(a.salida)
out.mkdir(parents=True, exist_ok=True)
inicio = dt.datetime.now(dt.timezone.utc)

m = MF.leer(a.escena)
err = MF.validar(m)
assert not err, err
t0 = time.perf_counter()
res = D.construir(m, "revision")
t_build = time.perf_counter() - t0
s = res["escena"]
c = s.cycles
# ---- configuración pedida (explícita; lo demás queda como en producción: AgX, exposición, clamp, rebotes por tipo)
s.render.engine = "CYCLES"
c.device = "CPU"
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = CONFIG["ancho"], CONFIG["alto"], 100
s.render.fps = CONFIG["fps"]
c.samples = CONFIG["muestras"]
c.use_adaptive_sampling = True
c.adaptive_threshold = CONFIG["umbral"]
c.use_denoising = True
c.denoiser = "OPENIMAGEDENOISE"
c.max_bounces = CONFIG["rebotes"]
c.use_light_tree = True
c.seed = 0
c.use_animated_seed = False
s.render.use_persistent_data = True
s.render.image_settings.file_format = "PNG"
s.render.image_settings.color_mode = "RGB"
s.render.image_settings.color_depth = "8"
cfg = {"motor": s.render.engine, "dispositivo": c.device, "resolucion": f"{s.render.resolution_x}x{s.render.resolution_y}",
       "porcentaje": s.render.resolution_percentage, "fps": s.render.fps, "muestras": c.samples,
       "muestreo_adaptativo": c.use_adaptive_sampling, "umbral_adaptativo": round(c.adaptive_threshold, 4),
       "denoise": c.use_denoising, "denoiser": c.denoiser, "rebotes_max": c.max_bounces, "difusos": c.diffuse_bounces,
       "brillantes": c.glossy_bounces, "transmision": c.transmission_bounces,
       "transparentes": c.transparent_max_bounces, "arbol_de_luces": c.use_light_tree, "semilla": c.seed,
       "semilla_animada": c.use_animated_seed, "persistent_data": s.render.use_persistent_data,
       "vista": f"{s.view_settings.view_transform} / {s.view_settings.look}",
       "exposicion": round(s.view_settings.exposure, 2), "blender": bpy.app.version_string}
esperado = {"motor": "CYCLES", "dispositivo": "CPU", "resolucion": "960x540", "porcentaje": 100, "fps": 30, "muestras": 6,
            "muestreo_adaptativo": True, "umbral_adaptativo": 0.05, "denoise": True, "denoiser": "OPENIMAGEDENOISE",
            "rebotes_max": 6, "arbol_de_luces": True, "semilla": 0, "semilla_animada": False}
mal = {k: (cfg[k], v) for k, v in esperado.items() if cfg[k] != v}
assert not mal, f"configuración distinta de la pedida: {mal}"
from estudio import autorizacion as AUT  # noqa: E402  REGLA: sin autorización del dueño no se renderiza
AUT.exigir(m, AUT.config_de(cfg["resolucion"], cfg["fps"], cfg["muestras"]))
nf = res.get("frames_pelicula", s.frame_end)
assert max(locales) <= nf, f"la escena tiene {nf} fotogramas"


def toma_de(f):
    for t in res["tomas"]:
        if t["frame_inicio"] <= f <= t["frame_fin"]:
            return t
    raise SystemExit(f"fotograma {f} sin toma")


cpu0 = sum(os.times()[:2])
filas = []
for f in locales:
    g = a.offset + f
    destino = out / f"f_{g:04d}.png"
    if destino.exists() and destino.stat().st_size > 0:
        continue
    t = toma_de(f)
    s.camera = t["camara"]
    D.ir_a(res, f)
    s.render.filepath = str(destino)
    w = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    dtf = time.perf_counter() - w
    filas.append({"global": g, "local": f, "toma": t["spec"]["id"], "segundos": round(dtf, 3)})
    print(f"f_{g:04d} ({m['id']} {f}) {t['spec']['id']:22} {dtf:6.2f} s", flush=True)
fin = dt.datetime.now(dt.timezone.utc)
cpu_modelo = next((ln.split(":", 1)[1].strip() for ln in open("/proc/cpuinfo") if ln.startswith("model name")),
                  platform.processor())
inf = {"escena": m["id"], "offset": a.offset, "fotogramas_renderizados": len(filas), "inicio_utc": inicio.isoformat(),
       "fin_utc": fin.isoformat(), "segundos_total_proceso": round((fin - inicio).total_seconds(), 1),
       "construccion_escena_s": round(t_build, 1), "render_s": round(sum(x["segundos"] for x in filas), 1),
       "cpu_proceso_s": round(sum(os.times()[:2]) - cpu0, 1),
       "ram_pico_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024), "nucleos": os.cpu_count(),
       "cpu_modelo": cpu_modelo, "huella_receta": MF.huella(m), "config_cycles": cfg, "fotogramas": filas}
(out / f"informe_{m['id']}_{locales[0]:04d}.json").write_text(json.dumps(inf, indent=1, ensure_ascii=False))
print(f"TRAMO {m['id']}: {len(filas)} fotogramas, render {inf['render_s']} s, armado {inf['construccion_escena_s']} s, "
      f"RAM {inf['ram_pico_mb']} MB")
