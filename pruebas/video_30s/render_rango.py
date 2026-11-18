"""Renderiza un RANGO de fotogramas de la escena con Cycles (sólo cambia las muestras, en memoria).

Arma la escena con el mismo camino de producción (director.construir(..., "revision")) y fija únicamente
`cycles.samples`. Todo lo demás (denoiser, adaptativo, rebotes, exposición, AgX, semilla…) es el de producción.
Cada fotograma sale como f_NNNN.png (número GLOBAL de fotograma, base 1) y se anota su tiempo. Reanudable.
Uso: python render_rango.py ESCENA.json --desde 1 --hasta 48 --muestras 6 --salida DIR
"""
import argparse, datetime as dt, json, os, platform, resource, sys, time
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
import bpy
from estudio.blender import director as D
from estudio import manifiesto as MF

ap = argparse.ArgumentParser()
ap.add_argument("escena"); ap.add_argument("--desde", type=int, required=True); ap.add_argument("--hasta", type=int, required=True)
ap.add_argument("--muestras", type=int, default=6); ap.add_argument("--salida", required=True)
a = ap.parse_args()
out = Path(a.salida); out.mkdir(parents=True, exist_ok=True)
inicio = dt.datetime.now(dt.timezone.utc)
m = MF.leer(a.escena); err = MF.validar(m); assert not err, err
t0 = time.perf_counter(); res = D.construir(m, "revision"); t_build = time.perf_counter() - t0
s = res["escena"]
s.cycles.samples = a.muestras                       # ÚNICO ajuste de la prueba
s.render.image_settings.file_format = "PNG"; s.render.image_settings.color_mode = "RGB"; s.render.image_settings.color_depth = "8"
ESPERADA = (720, 1280) if m.get("render", {}).get("vertical") else (1280, 720)   # 9:16: el mismo 720p, parado
assert (s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage, s.render.fps) == (*ESPERADA, 100, 30), "resolución/FPS distintos de 720p@30"
assert s.render.engine == "CYCLES"
assert a.hasta <= res.get("frames_pelicula", s.frame_end), f"la escena tiene {res.get('frames_pelicula', s.frame_end)} fotogramas"
from estudio import autorizacion as AUT              # REGLA: sin autorización del dueño no se renderiza
AUT.exigir(m, AUT.config_de("1280x720", 30, a.muestras))
def toma_de(f):
    for t in res["tomas"]:
        if t["frame_inicio"] <= f <= t["frame_fin"]: return t
    raise SystemExit(f"fotograma {f} sin toma")
c = s.cycles
c.seed = 0; c.use_animated_seed = False          # semilla fija: el ruido es idéntico entre ejecuciones
cfg = {"motor": s.render.engine, "dispositivo": c.device, "muestras": c.samples, "muestreo_adaptativo": c.use_adaptive_sampling, "umbral_adaptativo": round(c.adaptive_threshold, 4),
       "denoiser": c.denoiser, "denoise_entradas": c.denoising_input_passes, "denoise_prefiltro": c.denoising_prefilter, "rebotes_max": c.max_bounces, "difusos": c.diffuse_bounces,
       "brillantes": c.glossy_bounces, "transmision": c.transmission_bounces, "transparentes": c.transparent_max_bounces, "caustica_reflectiva": c.caustics_reflective,
       "caustica_refractiva": c.caustics_refractive, "clamp_indirecto": c.sample_clamp_indirect, "arbol_de_luces": c.use_light_tree, "semilla": c.seed, "semilla_animada": c.use_animated_seed,
       "persistent_data": s.render.use_persistent_data, "resolucion": f"{s.render.resolution_x}x{s.render.resolution_y}", "porcentaje": s.render.resolution_percentage, "fps": s.render.fps,
       "vista": f"{s.view_settings.view_transform} / {s.view_settings.look}", "exposicion": round(s.view_settings.exposure, 2), "hilos": s.render.threads, "blender": bpy.app.version_string}
cpu0 = sum(os.times()[:2]); filas = []
for f in range(a.desde, a.hasta + 1):
    destino = out / f"f_{f:04d}.png"
    if destino.exists() and destino.stat().st_size > 0: continue
    t = toma_de(f); s.camera = t["camara"]; D.ir_a(res, f); s.render.filepath = str(destino)
    w = time.perf_counter(); bpy.ops.render.render(write_still=True); dtf = time.perf_counter() - w
    filas.append({"fotograma": f, "toma": t["spec"]["id"], "segundos": round(dtf, 3)})
    print(f"f_{f:04d} {t['spec']['id']:20} {dtf:6.2f} s", flush=True)
fin = dt.datetime.now(dt.timezone.utc)
cpu_modelo = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), platform.processor())
inf = {"desde": a.desde, "hasta": a.hasta, "fotogramas_renderizados": len(filas), "inicio_utc": inicio.isoformat(), "fin_utc": fin.isoformat(),
       "segundos_total_proceso": round((fin - inicio).total_seconds(), 1), "construccion_escena_s": round(t_build, 1),
       "render_s": round(sum(x["segundos"] for x in filas), 1), "cpu_proceso_s": round(sum(os.times()[:2]) - cpu0 + 0.0, 1),
       "ram_pico_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024), "nucleos": os.cpu_count(), "cpu_modelo": cpu_modelo,
       "huella_receta": MF.huella(m), "config_cycles": cfg, "fotogramas": filas}
(out / f"informe_{a.desde:04d}-{a.hasta:04d}.json").write_text(json.dumps(inf, indent=1, ensure_ascii=False))
print(f"RANGO {a.desde}-{a.hasta}: {len(filas)} fotogramas, render {inf['render_s']} s, build {inf['construccion_escena_s']} s, RAM {inf['ram_pico_mb']} MB")
