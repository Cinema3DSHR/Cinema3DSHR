"""Prueba comparativa de resolución — EJECUTOR (un proceso = una resolución).

Qué hace: construye la escena de la mansión (p000_prueba_mansion v1) con EL MISMO camino de código de la
producción (`director.construir(manifiesto, "revision")`) y después cambia SÓLO la resolución de salida.
Nada más se toca: cámaras, luces, materiales, muestras (10), denoiser, exposición, animaciones y objetos son los de
producción. No modifica el estudio, la producción ni `config.py` (la resolución se pisa en memoria).

Uso:
  python ejecutar.py --res 960x540 --momentos momentos.json --salida RUTA [--previa]
Cada proceso hace un render de calentamiento (carga de escena y BVH; se descarta y se informa aparte) y después
mide los 5 momentos. Se corre un proceso por resolución para que el pico de memoria sea de esa resolución.
"""
from __future__ import annotations
import argparse
import json
import os
import platform
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import bpy  # noqa: E402
import psutil  # noqa: E402
from estudio.blender import director as D  # noqa: E402
from estudio import manifiesto as MF  # noqa: E402

ESCENA = RAIZ / "producciones/p000_prueba_mansion/escenas/e01/v1/escena.json"


class Muestreador(threading.Thread):
    """Mide memoria (RSS) y CPU del proceso y del sistema mientras se renderiza."""

    def __init__(self, intervalo=0.25):
        super().__init__(daemon=True)
        self.p = psutil.Process(os.getpid())
        self.intervalo = intervalo
        self.activo = True
        self.rss_pico = 0
        self.cpu_sistema = []
        psutil.cpu_percent(interval=None)

    def run(self):
        while self.activo:
            try:
                self.rss_pico = max(self.rss_pico, self.p.memory_info().rss)
                self.cpu_sistema.append(psutil.cpu_percent(interval=None))
            except psutil.Error:
                pass
            time.sleep(self.intervalo)

    def reiniciar(self):
        self.rss_pico = self.p.memory_info().rss
        self.cpu_sistema = []

    def parar(self):
        self.activo = False


def cpu_proceso(p):
    t = p.cpu_times()
    return t.user + t.system


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", required=True, help="ANCHOxALTO, p. ej. 960x540")
    ap.add_argument("--momentos", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--previa", action="store_true", help="sólo previsualizar candidatos a momentos (baja calidad)")
    ap.add_argument("--muestras", type=int, default=None, help="SÓLO para --previa")
    a = ap.parse_args()
    ancho, alto = (int(v) for v in a.res.lower().split("x"))
    momentos = json.loads(Path(a.momentos).read_text())["momentos"]
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)

    manifiesto = MF.leer(ESCENA)
    errs = MF.validar(manifiesto)
    assert not errs, errs
    huella = MF.huella(manifiesto)
    proc = psutil.Process(os.getpid())

    t0 = time.perf_counter()
    res = D.construir(manifiesto, "revision")        # exactamente la ruta de producción
    t_build = time.perf_counter() - t0
    s = res["escena"]
    fps_decl = s.render.fps
    # ---- ÚNICO cambio de la prueba: la resolución de salida ----
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = ancho, alto, 100
    s.render.image_settings.file_format = "PNG"          # sin pérdida, para medir; el JPEG de revisión se hace después
    s.render.image_settings.color_mode = "RGB"
    s.render.image_settings.color_depth = "8"
    if a.previa:
        s.cycles.samples = a.muestras or 6
    tomas = {t["spec"]["id"]: t for t in res["tomas"]}
    cfg = {"motor": s.render.engine, "muestras": s.cycles.samples, "denoiser": s.cycles.denoiser,
           "dispositivo": s.cycles.device, "adaptativo": s.cycles.use_adaptive_sampling,
           "umbral_adaptativo": s.cycles.adaptive_threshold, "rebotes": s.cycles.max_bounces,
           "persistent_data": s.render.use_persistent_data, "exposicion": s.view_settings.exposure,
           "transformacion_vista": s.view_settings.view_transform, "look": s.view_settings.look,
           "fps_declarados": fps_decl, "hilos": s.render.threads_mode, "hilos_n": s.render.threads,
           "objetos": len(bpy.data.objects), "luces": sum(1 for o in bpy.data.objects if o.type == "LIGHT"),
           "materiales": len(bpy.data.materials)}

    mu = Muestreador()
    mu.start()
    # ---- calentamiento (se descarta): carga de escena, BVH, compilación de shaders
    m0 = momentos[0]
    t = tomas[m0["toma"]]
    s.camera = t["camara"]
    s.frame_set(m0["frame"])
    s.render.filepath = str(out / "_calentamiento.png")
    mu.reiniciar()
    c0, w0 = cpu_proceso(proc), time.perf_counter()
    bpy.ops.render.render(write_still=True)
    calent = {"segundos": round(time.perf_counter() - w0, 2), "cpu_s": round(cpu_proceso(proc) - c0, 1),
              "rss_pico_mb": round(mu.rss_pico / 2**20)}
    (out / "_calentamiento.png").unlink(missing_ok=True)

    medidas = []
    n_cpu = psutil.cpu_count(logical=True)
    for m in momentos:
        t = tomas[m["toma"]]
        assert t["frame_inicio"] <= m["frame"] <= t["frame_fin"], (m, t["frame_inicio"], t["frame_fin"])
        s.camera = t["camara"]
        s.frame_set(m["frame"])
        destino = out / f"{m['id']}.png"
        s.render.filepath = str(destino)
        mu.reiniciar()
        c0, w0 = cpu_proceso(proc), time.perf_counter()
        bpy.ops.render.render(write_still=True)
        wall = time.perf_counter() - w0
        cpu = cpu_proceso(proc) - c0
        medidas.append({"id": m["id"], "toma": m["toma"], "frame": m["frame"], "segundos": round(wall, 3),
                        "cpu_s": round(cpu, 2), "uso_cpu_proceso_pct": round(100 * cpu / (wall * n_cpu), 1),
                        "uso_cpu_sistema_pct": round(sum(mu.cpu_sistema) / max(1, len(mu.cpu_sistema)), 1),
                        "rss_pico_mb": round(mu.rss_pico / 2**20), "bytes_png": destino.stat().st_size})
        print(f"[{a.res}] {m['id']}: {wall:.2f} s  cpu {100 * cpu / (wall * n_cpu):.0f}%  rss {mu.rss_pico / 2**20:.0f} MB",
              flush=True)
    mu.parar()
    total = sum(x["segundos"] for x in medidas)
    resumen = {
        "resolucion": a.res, "ancho": ancho, "alto": alto, "pixeles": ancho * alto,
        "huella_receta": huella, "construccion_escena_s": round(t_build, 1), "calentamiento": calent,
        "momentos": medidas, "total_5_s": round(total, 2), "media_s": round(total / len(medidas), 2),
        "fps_reales_render": round(len(medidas) / total, 4),
        "rss_pico_mb": max(x["rss_pico_mb"] for x in medidas),
        "ru_maxrss_mb": round(__import__("resource").getrusage(__import__("resource").RUSAGE_SELF).ru_maxrss / 1024),
        "configuracion": cfg,
        "maquina": {"cpu": platform.processor() or platform.machine(), "nucleos_logicos": n_cpu,
                    "ram_total_mb": round(psutil.virtual_memory().total / 2**20), "gpu": "no disponible (sin GPU)",
                    "blender": bpy.app.version_string, "so": platform.platform()},
    }
    (out / "medidas.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    print(f"[{a.res}] TOTAL 5 momentos: {total:.1f} s  ({resumen['fps_reales_render']:.3f} fotogramas/s reales)", flush=True)


if __name__ == "__main__":
    main()
