"""Análisis de la prueba de motor 002: tiempos, memoria, fidelidad (SSIM/PSNR/detalle) y proyección a 10 minutos."""
import json, re, subprocess, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent; SAL = AQUI.parents[1] / "salida/pruebas/motor_002"
MOM = json.loads((AQUI / "momentos.json").read_text())["momentos"]
VARS = [v for v in ("cycles_prod", "cycles_sinarbol", "cycles_rapido", "eevee_rt0_16", "eevee_rt1_16", "cycles_ref64") if (SAL / v / "medidas.json").exists()]
def sh(*a): return subprocess.run([str(x) for x in a], capture_output=True, text=True)
def met(a, b):
    ss = re.search(r"All:([0-9.]+)", sh("ffmpeg", "-hide_banner", "-i", a, "-i", b, "-lavfi", "[0:v][1:v]ssim", "-f", "null", "-").stderr)
    ps = re.search(r"average:([0-9.a-z]+)", sh("ffmpeg", "-hide_banner", "-i", a, "-i", b, "-lavfi", "[0:v][1:v]psnr", "-f", "null", "-").stderr)
    return (float(ss.group(1)) if ss else None, float(ps.group(1)) if ps and ps.group(1) != "inf" else None)
def luma(p):
    import numpy as np
    r = sh_b = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", "format=rgb24", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(r, dtype="uint8").reshape(720, 1280, 3).astype("float64")
def energia_detalle(p):
    import numpy as np
    g = luma(p).mean(2); l = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]; return float(l.var())
def brillo(p):
    return float(luma(p).mean())
R = {"medidas": {v: json.loads((SAL / v / "medidas.json").read_text()) for v in VARS}, "fidelidad": {}}
ref = "cycles_ref64" if "cycles_ref64" in VARS else None
e0 = {m["id"]: energia_detalle(SAL / "cycles_prod" / f"{m['id']}.png") for m in MOM}
for v in VARS:
    f = {"vs_produccion": [], "vs_ref64": [], "detalle_pct": [], "brillo_dif": []}
    for m in MOM:
        a = SAL / v / f"{m['id']}.png"
        f["vs_produccion"].append(met(a, SAL / "cycles_prod" / f"{m['id']}.png"))
        if ref: f["vs_ref64"].append(met(a, SAL / ref / f"{m['id']}.png"))
        f["detalle_pct"].append(100 * energia_detalle(a) / e0[m["id"]])
        f["brillo_dif"].append(brillo(a) - brillo(SAL / ref / f"{m['id']}.png") if ref else 0)
    avg = lambda xs, i=None: round(sum((x[i] if i is not None else x) for x in xs) / len(xs), 4) if xs and all((x[i] if i is not None else x) is not None for x in xs) else None
    R["fidelidad"][v] = {"ssim_vs_produccion": avg(f["vs_produccion"], 0), "ssim_vs_ref64": avg(f["vs_ref64"], 0) if ref else None,
                         "psnr_vs_ref64": avg(f["vs_ref64"], 1) if ref else None, "detalle_pct_vs_prod": round(sum(f["detalle_pct"]) / 5, 1),
                         "brillo_vs_ref64": round(sum(f["brillo_dif"]) / 5, 2), "ssim_por_momento_vs_ref64": [round(x[0], 3) for x in f["vs_ref64"]] if ref else None}
(AQUI / "resultados.json").write_text(json.dumps(R, indent=1, ensure_ascii=False))
print(json.dumps({v: {"s_frame": R["medidas"][v]["media_s"], "rss": R["medidas"][v]["rss_pico_mb"], **R["fidelidad"][v]} for v in VARS}, indent=1, ensure_ascii=False))
