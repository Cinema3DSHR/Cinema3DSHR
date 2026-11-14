"""Genera la página de revisión (HTML autocontenido) con las 20 imágenes y las tablas, desde resultados.json.
Uso: python pagina_revision.py SALIDA.html   — la página incrusta las imágenes (≈ 4 MB) y por eso NO se guarda en Git."""
import base64
import json
import math
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
R = json.loads((AQUI / "resultados.json").read_text())
MOM = json.loads((AQUI / "momentos.json").read_text())["momentos"]
RES = ["1280x720", "1024x576", "960x540", "854x480"]
T, F, D, V = R["tiempos"], R["fidelidad"], R["detalle_fino_pct_vs_720p"], R["tamano_video"]
FACT, DUR = V["calibrado_con_archivo_real"]["factor_calibracion"], V["duracion_muestra_s"]
mb10 = lambda r: V["por_resolucion"][r]["crf22"]["bytes_muestra"] * FACT / DUR * 600 / 1e6 + 14.4
amp = lambda p: round(100 * math.sqrt(p / 100))
b64 = lambda p: "data:image/jpeg;base64," + base64.b64encode(Path(p).read_bytes()).decode()

QUE_MIRAR = {
    "m1_plano_general": "Mirá las ventanas de la ciudad de fondo y los listones de madera de la fachada: es donde primero se nota la resolución.",
    "m2_fachada_exterior": "Reflejos sobre el asfalto mojado y la baliza: casi iguales en las cuatro. Sólo los bordes se ablandan un poco.",
    "m3_entrada_garaje": "El moteado fino del vidrio de la baranda se pierde en 960 y 854. La luz y las formas quedan iguales.",
    "m4_piscina_reflejos": "El agua: ondas finas en 720p, más tenues en 576p, casi lisa en 540p y lisa en 480p. Es la diferencia más clara de toda la prueba.",
    "m5_jardin_vegetacion": "Casi no hay diferencia: escena oscura, con poco detalle fino para perder.",
}
datos = {"momentos": [], "res": {}}
for m in MOM:
    datos["momentos"].append({"id": m["id"], "nombre": m["nombre"], "toma": m["toma"], "t": m["tiempo_s"], "frame": m["frame"],
                              "mirar": QUE_MIRAR[m["id"]], "detalle": b64(AQUI / "comparaciones" / f"{m['id']}_detalle_pixeles_2x2.jpg"),
                              "img": {r: b64(AQUI / "imagenes" / r / f"{m['id']}.jpg") for r in RES},
                              "amp_zona": {r: amp(D[r]["zona"][m["id"]]) for r in RES},
                              "t_s": {r: T[r]["momentos"][m["id"]]["media_s"] for r in RES}})
for r in RES:
    datos["res"][r] = {"ancho": int(r.split("x")[0]), "alto": int(r.split("x")[1]), "s": T[r]["media_por_fotograma_s"], "rel": T[r]["tiempo_relativo_a_720p"],
                       "ssim": F[r]["ssim_vista_720p"], "amp": amp(D[r]["cuadro_media_pct"]), "amp_pool": amp(D[r]["zona"]["m4_piscina_reflejos"]),
                       "mb": round(mb10(r)), "ram": T[r]["memoria_pico_mb"], "cpu_h": round(T[r]["media_por_fotograma_s"] * 18000 / 3600),
                       "fps": T[r]["fps_reales_render"]}

HTML = Path(AQUI / "plantilla_pagina.html").read_text(encoding="utf-8").replace("/*DATOS*/", "const DATOS = " + json.dumps(datos, ensure_ascii=False) + ";")
Path(sys.argv[1]).write_text(HTML, encoding="utf-8")
print("página escrita:", sys.argv[1], round(len(HTML) / 1e6, 1), "MB")
