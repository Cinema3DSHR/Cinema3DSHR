"""Informe de una corrida de «Episodio · render distribuido»: qué hizo cada trabajo, cuánto tardó (según GitHub y según
el propio render), si los 19 corrieron a la vez, si la configuración y el tamaño de cada fotograma son los pedidos, y la
proyección para el episodio completo (5 400 fotogramas).

    python3 pruebas/episodio/informe.py CARPETA_FOTOGRAMAS jobs.json --salida informe.json
"""
import argparse
import datetime as dt
import json
import re
import statistics as st
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pruebas.episodio.plan import plan  # noqa: E402

ESPERADO = {"motor": "CYCLES", "dispositivo": "CPU", "resolucion": "960x540", "fps": 30, "muestras": 6,
            "muestreo_adaptativo": True, "umbral_adaptativo": 0.05, "denoiser": "OPENIMAGEDENOISE", "rebotes_max": 6,
            "arbol_de_luces": True, "semilla": 0, "semilla_animada": False}


def _t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def _png_tam(p: Path):
    with open(p, "rb") as f:
        cab = f.read(24)
    return struct.unpack(">II", cab[16:24])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("jobs")
    ap.add_argument("--salida")
    ap.add_argument("--produccion", default="p009_duo_cero")
    ap.add_argument("--escenas", default="")
    a = ap.parse_args()
    car = Path(a.carpeta)
    informes = [json.loads(p.read_text()) for p in sorted(car.glob("informe_*.json"))]
    trabajos = {json.loads(p.read_text())["n"]: json.loads(p.read_text()) for p in car.glob("trabajo_*.json")}
    prep = {p.stem.split("_")[1]: int(p.read_text().split("=")[1]) for p in car.glob("preparacion_*.txt")}
    pngs = sorted(car.glob("f_*.png"))
    lineas = []
    P = lineas.append

    # ---- trabajos según GitHub (inicio, fin, a la vez)
    jobs = [j for j in json.load(open(a.jobs))["jobs"] if j["name"].startswith("render ")]
    js = []
    for j in jobs:
        n = re.match(r"render (\d+)", j["name"]).group(1)
        js.append({"n": n, "estado": j["conclusion"] or j["status"], "inicio": _t(j["started_at"]),
                   "fin": _t(j["completed_at"])})
    js.sort(key=lambda x: x["n"])
    ok = [j for j in js if j["estado"] == "success"]
    ini = min(j["inicio"] for j in js) if js else None
    fin = max(j["fin"] for j in js if j["fin"]) if js else None
    # cuántos estuvieron corriendo al mismo tiempo (máximo) y si todos arrancaron antes de que terminara el primero
    eventos = sorted([(j["inicio"], 1) for j in js] + [(j["fin"], -1) for j in js if j["fin"]])
    cur = pico = 0
    for _, d in eventos:
        cur += d
        pico = max(pico, cur)
    primero_fin = min((j["fin"] for j in js if j["fin"]), default=None)
    todos_a_la_vez = bool(js) and all(j["inicio"] <= primero_fin for j in js)
    P(f"## Trabajos: {len(js)} de render, {len(ok)} terminaron bien; simultáneos como máximo: {pico}; "
      f"los {len(js)} arrancaron antes de que terminara el primero: {'sí' if todos_a_la_vez else 'NO'}")
    P(f"- Arranque: el último trabajo empezó {(max(j['inicio'] for j in js) - ini).total_seconds():.0f} s después del primero")

    # ---- por trabajo
    por_n = {}
    for inf in informes:
        g = inf["offset"] + inf["fotogramas"][0]["local"] if inf["fotogramas"] else None
        n = next((nn for nn, t in trabajos.items() if g is not None and t["desde"] <= g <= t["hasta"]), None)
        por_n.setdefault(n, []).append(inf)
    filas = []
    P("")
    P("| trabajo | bloque | fotogramas | escenas | preparación (s) | armado escenas (s) | render (s) | s/fotograma | total trabajo (s) |")
    P("|---|---|---|---|---|---|---|---|---|")
    for j in js:
        n = j["n"]
        infs = por_n.get(n, [])
        t = trabajos.get(n, {})
        nf = sum(len(i["fotogramas"]) for i in infs)
        arm = sum(i["construccion_escena_s"] for i in infs)
        ren = sum(i["render_s"] for i in infs)
        spf = ren / nf if nf else 0
        dur = (j["fin"] - j["inicio"]).total_seconds() if j["fin"] else 0
        filas.append({"n": n, "desde": t.get("desde"), "hasta": t.get("hasta"), "fotogramas": nf,
                      "escenas": [i["escena"].split("-")[-1] for i in infs], "preparacion_s": prep.get(n),
                      "armado_s": round(arm, 1), "render_s": round(ren, 1), "s_por_fotograma": round(spf, 2),
                      "duracion_github_s": round(dur), "estado": j["estado"],
                      "ram_pico_mb": max((i["ram_pico_mb"] for i in infs), default=None),
                      "tiempos": [f["segundos"] for i in infs for f in i["fotogramas"]]})
        P(f"| {n} | {t.get('desde')}–{t.get('hasta')} | {nf} | {' '.join(filas[-1]['escenas'])} | {prep.get(n)} | "
          f"{arm:.0f} | {ren:.0f} | {spf:.1f} | {dur:.0f} |")

    # ---- totales
    todos = [x for f in filas for x in f["tiempos"]]
    primeros = [i["fotogramas"][0]["segundos"] for i in informes if i["fotogramas"]]
    resto = [f["segundos"] for i in informes for f in i["fotogramas"][1:]]
    P("")
    P(f"## Fotogramas: {len(pngs)} PNG; promedio {st.mean(todos):.1f} s/fotograma (mediana {st.median(todos):.1f}, "
      f"mín {min(todos):.1f}, máx {max(todos):.1f}); primer fotograma de cada escena {st.mean(primeros):.1f} s, "
      f"los siguientes {(st.mean(resto) if resto else 0):.1f} s")
    P(f"- Armado de una escena (promedio): {st.mean(i['construccion_escena_s'] for i in informes):.0f} s; "
      f"preparación del trabajo (máquina, Blender, recursos): {st.mean(prep.values()):.0f} s")
    P(f"- RAM pico de un proceso: {max(i['ram_pico_mb'] for i in informes)} MB; CPU: {informes[0]['cpu_modelo']} "
      f"({informes[0]['nucleos']} núcleos)")
    P(f"- Tiempo total de la prueba (primer trabajo de render → último): {(fin - ini).total_seconds() / 60:.1f} min")

    # ---- verificación de calidad
    malos = []
    for i in informes:
        for k, v in ESPERADO.items():
            if i["config_cycles"].get(k) != v:
                malos.append((i["escena"], k, i["config_cycles"].get(k), v))
    tam = {_png_tam(p) for p in pngs}
    globales = [int(p.stem[2:]) for p in pngs]
    P(f"- Configuración en los {len(informes)} tramos: {'igual a la pedida' if not malos else malos}; "
      f"Blender {sorted({i['config_cycles']['blender'] for i in informes})}; tamaños de imagen {sorted(tam)}; "
      f"repetidos: {len(globales) - len(set(globales))}")

    # ---- proyección: 5 400 fotogramas, cada trabajo con su bloque completo
    pl = plan(a.produccion, len(js) or 19, 0, a.escenas.split() or None)
    proy = []
    for f, b in zip(filas, pl["matriz"]):
        nesc = len(json.loads(b["tramos"]))
        arm_esc = (f["armado_s"] / max(1, len(f["escenas"]))) if f["escenas"] else st.mean(i["construccion_escena_s"] for i in informes)
        spf = f["s_por_fotograma"] or st.mean(todos)
        t = (f["preparacion_s"] or st.mean(prep.values())) + nesc * arm_esc + b["cantidad"] * spf + 60  # +60 s: empaquetar y subir
        proy.append(t)
    P("")
    P(f"## Proyección completa de lo elegido ({pl['total']} fotogramas en {len(js)} trabajos): "
      f"el trabajo más lento tardaría ~{max(proy) / 60:.0f} min, el promedio ~{st.mean(proy) / 60:.0f} min → "
      f"render completo en ~{max(proy) / 60:.0f} min de reloj (+ ~1–2 min de planificación y espera de máquinas)")
    print("\n".join(lineas))
    if a.salida:
        Path(a.salida).write_text(json.dumps({"trabajos": [{k: v for k, v in f.items() if k != "tiempos"} for f in filas],
                                              "pico_simultaneos": pico, "todos_a_la_vez": todos_a_la_vez,
                                              "segundos_por_fotograma": round(st.mean(todos), 2),
                                              "prueba_min": round((fin - ini).total_seconds() / 60, 1),
                                              "proyeccion_min": round(max(proy) / 60), "config_ok": not malos,
                                              "tamanos": sorted(tam), "lineas": lineas}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
