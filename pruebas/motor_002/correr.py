"""Corre las variantes una por una (cada una en su proceso) y guarda en salida/pruebas/motor_002/<variante>/ (fuera de Git)."""
import os, subprocess, sys, time
from pathlib import Path
AQUI = Path(__file__).resolve().parent; SAL = AQUI.parents[1] / "salida/pruebas/motor_002"
PY = os.environ.get("CINE_PY", "/opt/tools/blendenv/bin/python")
VARS = sys.argv[1:] or ["cycles_prod", "cycles_sinarbol", "cycles_rapido", "eevee_rt0_16", "eevee_rt1_16", "cycles_ref64"]
for v in VARS:
    d = SAL / v
    if (d / "medidas.json").exists(): print("ya hecho", v); continue
    d.mkdir(parents=True, exist_ok=True); t = time.time(); print("===", v, flush=True)
    with open(d / "registro.log", "w") as log: r = subprocess.run([PY, "-I", str(AQUI / "ejecutar_variante.py"), "--variante", v, "--salida", str(d)], stdout=log, stderr=subprocess.STDOUT)
    print(v, "rc", r.returncode, round(time.time() - t), "s", flush=True)
    if r.returncode: print(Path(d / "registro.log").read_text()[-600:])
