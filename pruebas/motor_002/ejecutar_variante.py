"""Prueba de motor 002 — ejecuta UNA variante de render sobre los 5 fotogramas de siempre (momentos.json).

Misma escena (p000 v1, armada con director.construir como en producción), mismas cámaras, mismos fotogramas, 1280×720.
Sólo cambia el motor/ajustes de la variante, EN MEMORIA: no se modifica el estudio, la receta ni config.py.
Un proceso por variante (el pico de memoria es de esa variante). Un render de calentamiento se descarta y se informa.
"""
import argparse, json, os, platform, sys, threading, time
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
import bpy, psutil
from estudio.blender import director as D
from estudio import manifiesto as MF

def aplicar(s, v):
    c, e = s.cycles, s.eevee
    if v.startswith("cycles"):
        if v == "cycles_sinarbol": c.use_light_tree = False
        elif v == "cycles_rapido": c.use_light_tree = False; c.samples = 6; c.denoising_prefilter = "FAST"
        elif v == "cycles_ref64": c.samples = 64; c.use_adaptive_sampling = False
        elif v != "cycles_prod": raise SystemExit("variante desconocida " + v)
    elif v.startswith("eevee"):
        s.render.engine = "BLENDER_EEVEE"
        _, rt, ms = v.split("_")            # eevee_rt0_16 / eevee_rt1_16
        e.taa_render_samples = int(ms)
        e.use_raytracing = (rt == "rt1")
        for k, val in (("use_shadows", True), ("use_volumetric_shadows", False)):
            if hasattr(e, k): setattr(e, k, val)
    else: raise SystemExit("variante desconocida " + v)

ap = argparse.ArgumentParser(); ap.add_argument("--variante", required=True); ap.add_argument("--salida", required=True)
a = ap.parse_args(); out = Path(a.salida); out.mkdir(parents=True, exist_ok=True)
MOM = json.loads((Path(__file__).parent / "momentos.json").read_text())["momentos"]
proc = psutil.Process(os.getpid()); pico = [0]; cpu = []; vivo = [True]
def muestrear():
    psutil.cpu_percent(None)
    while vivo[0]:
        pico[0] = max(pico[0], proc.memory_info().rss); cpu.append(psutil.cpu_percent(None)); time.sleep(0.25)
manifiesto = MF.leer(RAIZ / "producciones/p000_prueba_mansion/escenas/e01/v1/escena.json")
t0 = time.perf_counter(); res = D.construir(manifiesto, "revision"); t_build = time.perf_counter() - t0
s = res["escena"]; tomas = {t["spec"]["id"]: t for t in res["tomas"]}
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1280, 720, 100
s.render.image_settings.file_format = "PNG"; s.render.image_settings.color_mode = "RGB"; s.render.image_settings.color_depth = "8"
aplicar(s, a.variante)
cfg = {"motor": s.render.engine, "muestras_cycles": s.cycles.samples, "taa_eevee": s.eevee.taa_render_samples, "raytracing_eevee": getattr(s.eevee, "use_raytracing", None),
       "light_tree": s.cycles.use_light_tree, "prefiltro_denoise": s.cycles.denoising_prefilter}
threading.Thread(target=muestrear, daemon=True).start()
m0 = MOM[0]; s.camera = tomas[m0["toma"]]["camara"]; s.frame_set(m0["frame"]); s.render.filepath = str(out / "_cal.png")
pico[0] = proc.memory_info().rss; w = time.perf_counter(); bpy.ops.render.render(write_still=True); calent = time.perf_counter() - w
(out / "_cal.png").unlink(missing_ok=True)
filas = []; ncpu = psutil.cpu_count()
for m in MOM:
    s.camera = tomas[m["toma"]]["camara"]; s.frame_set(m["frame"]); s.render.filepath = str(out / f"{m['id']}.png")
    pico[0] = proc.memory_info().rss; cpu.clear(); c0 = sum(proc.cpu_times()[:2]); w = time.perf_counter()
    bpy.ops.render.render(write_still=True); dt = time.perf_counter() - w; cs = sum(proc.cpu_times()[:2]) - c0
    filas.append({"id": m["id"], "segundos": round(dt, 2), "cpu_proceso_pct": round(100 * cs / dt / ncpu), "rss_pico_mb": round(pico[0] / 2**20)})
    print(f"[{a.variante}] {m['id']}: {dt:.2f} s  rss {pico[0] / 2**20:.0f} MB", flush=True)
vivo[0] = False
tot = sum(f["segundos"] for f in filas)
(out / "medidas.json").write_text(json.dumps({"variante": a.variante, "config": cfg, "calentamiento_s": round(calent, 1), "construccion_s": round(t_build, 1),
    "fotogramas": filas, "total_5_s": round(tot, 1), "media_s": round(tot / 5, 2), "rss_pico_mb": max(f["rss_pico_mb"] for f in filas),
    "huella": MF.huella(manifiesto), "maquina": {"nucleos": ncpu, "ram_mb": round(psutil.virtual_memory().total / 2**20), "gpu": "no hay", "blender": bpy.app.version_string}}, indent=1))
print(f"[{a.variante}] TOTAL {tot:.1f} s", flush=True)
