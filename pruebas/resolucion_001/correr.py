"""Orquestador: corre las 4 resoluciones en DOS pasadas (orden directo e inverso), cada una en su propio proceso.
Uso: python correr.py [--salida RUTA]   (la salida por defecto es salida/pruebas/resolucion_001, ignorada por Git)"""
import argparse, os, subprocess, sys, time, json
from pathlib import Path
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
PY = os.environ.get("CINE_PY", "/opt/tools/blendenv/bin/python")   # Python con bpy y psutil
RES = ["1280x720", "1024x576", "960x540", "854x480"]
ap = argparse.ArgumentParser(); ap.add_argument("--salida", default=str(RAIZ / "salida/pruebas/resolucion_001"))
a = ap.parse_args()
t0 = time.time()
for pasada, orden in (("A", RES), ("B", RES[::-1])):
    for r in orden:
        dest = Path(a.salida) / f"pasada_{pasada}" / r
        if (dest / "medidas.json").exists():
            print("ya hecho:", pasada, r); continue
        print(f"=== pasada {pasada} · {r} · {time.time() - t0:.0f} s desde el inicio", flush=True)
        dest.mkdir(parents=True, exist_ok=True)
        with open(dest / "registro.log", "w") as log:
            subprocess.run([PY, "-I", str(AQUI / "ejecutar.py"), "--res", r, "--momentos", str(AQUI / "momentos.json"),
                            "--salida", str(dest)], check=True, stdout=log, stderr=subprocess.STDOUT)
        print(Path(dest / "registro.log").read_text().count("\n"), "líneas de registro", flush=True)
print("FIN", round(time.time() - t0), "s")
